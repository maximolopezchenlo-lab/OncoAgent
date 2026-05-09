"""
Specialist Node — Tier-adaptive clinical reasoning with Chain-of-Thought.

Design patterns:
  - Model Tiering: routes to Qwen 3.5 9B (fast) or Qwen 3.6 27B (deep)
  - Reflexion: accepts critic feedback for iterative refinement
  - Anti-Hallucination: system prompt strictly forbids inventing treatments

The specialist produces a structured recommendation with explicit
reasoning sections (Findings → Staging → Treatment → Recommendation).
"""

import logging
from typing import Dict, Any

from .state import AgentState
from .tools import call_tier_model, get_tier_spec

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt Engineering
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT_TEMPLATE = """\
You are an expert clinical oncologist operating as part of the OncoAgent system.
Your task is to analyze the patient case and provide the most appropriate clinical
next steps based STRICTLY on the provided guidelines.

MODEL TIER: {tier_name} ({tier_description})

DIAGNOSTIC RIGOR POLICY:
1. You MUST verify if a definitive diagnosis (e.g., pathology report, biopsy) exists.
2. If diagnostic evidence is missing or inconclusive, your PRIMARY recommendation 
   MUST be the specific diagnostic procedure needed (e.g., "Esperar informe de biopsia", 
   "Realizar legrado diagnóstico").
3. You are STRICTLY FORBIDDEN from assuming cancer exists or jumping to treatment 
   protocols (surgery, chemo, radiation) if the pathology is not confirmed in the input.

ANTI-HALLUCINATION POLICY:
1. If the information is NOT explicitly in the guidelines, reply ONLY with: 
   "Información no concluyente en las guías provistas."
2. Do NOT invent dosages or protocols.

OUTPUT FORMAT (use this exact structure):
## Hallazgos Clínicos
[Summary of current patient presentation]

## Validación Diagnóstica
[State if pathology/biopsy is present and confirmed. If missing, specify what is needed.]

## Análisis de Estadificación
[Map findings to staging ONLY if diagnosis is confirmed. Otherwise, state why it's not possible.]

## Opciones de Manejo
[List clinical next steps or treatment options ONLY if appropriate for the diagnostic stage.]

## Recomendación Final
[The absolute next step for the clinician with confidence level]

Provide your recommendation in Spanish, clearly citing the guidelines."""


_USER_PROMPT_TEMPLATE = """\
Patient Information:
- Original Text: {clinical_text}
- Cancer Type: {cancer_type}
- Stage: {stage}
- Mutations: {mutations}

Clinical Guidelines Context:
{context}

{api_evidence}

{critic_feedback_section}

Based ONLY on the guidelines above, what are the recommended clinical next steps?"""


def _build_specialist_prompt(
    state: AgentState,
) -> tuple[str, str]:
    """Build the system and user prompts for the specialist.

    Incorporates critic feedback if this is a retry iteration.

    Args:
        state: Current LangGraph state.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    tier = state.get("selected_tier", 1)
    spec = get_tier_spec(tier)

    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        tier_name=spec.name,
        tier_description=spec.description,
    )

    entities = state.get("extracted_entities", {})
    context = "\n---\n".join(state.get("rag_context", []))
    api_evidence = state.get("api_evidence_context", [])

    # Format API evidence if available
    api_section = ""
    if api_evidence:
        api_section = "Additional Evidence (Genomic/Trials):\n" + "\n".join(api_evidence)

    # Inject critic feedback for retry iterations
    critic_feedback = state.get("critic_feedback", "")
    critic_attempts = state.get("critic_attempts", 0)
    feedback_section = ""
    if critic_attempts > 0 and critic_feedback:
        feedback_section = (
            f"\n⚠️ PREVIOUS ATTEMPT FEEDBACK (attempt {critic_attempts}):\n"
            f"The following issues were identified in your previous recommendation. "
            f"Please address them in this revision:\n{critic_feedback}\n"
        )

    user_prompt = _USER_PROMPT_TEMPLATE.format(
        clinical_text=state.get("clinical_text", ""),
        cancer_type=entities.get("cancer_type", "Unknown"),
        stage=entities.get("stage", "Unknown"),
        mutations=", ".join(entities.get("mutations", [])),
        context=context,
        api_evidence=api_section,
        critic_feedback_section=feedback_section,
    )

    return system_prompt, user_prompt


# ---------------------------------------------------------------------------
# Specialist Node
# ---------------------------------------------------------------------------

def specialist_node(state: AgentState) -> Dict[str, Any]:
    """Generate a clinical recommendation using the tier-adaptive model.

    If critic feedback exists in the state (retry iteration), the feedback
    is injected into the prompt so the model can self-correct.

    Args:
        state: Current LangGraph state.

    Returns:
        State update with clinical_recommendation and reasoning_trace.
    """
    context = state.get("rag_context", [])
    tier = state.get("selected_tier", 1)
    attempt = state.get("critic_attempts", 0)

    # Guard: no context available
    if not context:
        return {
            "clinical_recommendation": (
                "Información no concluyente en las guías provistas. "
                "No se encontró evidencia relevante en la base de datos clínica."
            ),
            "reasoning_trace": "No RAG context available — safe fallback triggered.",
        }

    system_prompt, user_prompt = _build_specialist_prompt(state)

    spec = get_tier_spec(tier)
    logger.info(
        "Specialist invoking %s (attempt %d, context chunks: %d)",
        spec, attempt + 1, len(context),
    )

    try:
        recommendation = call_tier_model(
            tier=tier,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        # Build reasoning trace for the critic
        reasoning_trace = (
            f"Tier: {spec.name} ({spec.model_id})\n"
            f"Attempt: {attempt + 1}\n"
            f"Context chunks: {len(context)}\n"
            f"API evidence items: {len(state.get('api_evidence_context', []))}\n"
            f"Recommendation length: {len(recommendation)} chars"
        )

    except RuntimeError as exc:
        logger.error("Specialist inference failed: %s", exc)
        recommendation = (
            "Error en el sistema de inferencia. "
            "No se pudo generar la recomendación clínica en este momento."
        )
        reasoning_trace = f"INFERENCE ERROR: {exc}"

    # Detect if model returned the safe phrase
    if "información no concluyente" in recommendation.lower():
        recommendation = "Información no concluyente en las guías provistas."

    return {
        "clinical_recommendation": recommendation,
        "reasoning_trace": reasoning_trace,
    }
