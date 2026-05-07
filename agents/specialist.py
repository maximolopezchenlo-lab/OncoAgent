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
Your task is to provide a treatment recommendation based STRICTLY on the provided
clinical guidelines context.

MODEL TIER: {tier_name} ({tier_description})

ANTI-HALLUCINATION POLICY:
1. You are STRICTLY FORBIDDEN from inventing treatments, drugs, or procedures.
2. If the answer is NOT explicitly contained in the provided guidelines, you MUST
   reply ONLY with: "Información no concluyente en las guías provistas."
3. Do NOT add external knowledge beyond what is provided in the context.
4. Every drug, procedure, or protocol you mention MUST be traceable to the context.

OUTPUT FORMAT (use this exact structure):
## Hallazgos Clínicos
[Summarise the patient's condition based on input]

## Análisis de Estadificación
[Map findings to the cancer staging system mentioned in guidelines]

## Opciones de Tratamiento
[List treatment options from the guidelines with supporting evidence]

## Recomendación
[Provide the final recommendation with confidence level]

## Biomarcadores Relevantes
[List relevant biomarkers and their implications]

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

Based ONLY on the guidelines above, what is the recommended treatment?"""


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
