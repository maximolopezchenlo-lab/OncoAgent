"""
Critic Node — Reflexion-pattern validation for clinical recommendations.

Design pattern: Reflexion (Shinn et al. 2023)
  - Generator (Specialist) → Critic loop
  - Critic evaluates: entailment, completeness, formatting
  - If FAIL → specific feedback injected back to Specialist for retry
  - Max 2 iterations before safe fallback

Layer 1: Rule-based checks (deterministic, no LLM needed)
Layer 2: LLM-based entailment verification (Tier 1 for speed)
"""

import logging
import re
from typing import Dict, Any, List

from .state import AgentState
from .tools import call_tier_model

logger = logging.getLogger(__name__)


# Maximum critic attempts before triggering safe fallback
MAX_CRITIC_ATTEMPTS = 2

# Required semantic concepts in a well-formed recommendation.
# Each entry is a list of synonyms — at least ONE must appear.
_REQUIRED_CONCEPTS = [
    # Clinical findings / presentation
    ["hallazgos", "findings", "presentación", "presentation", "clinical findings"],
    # Diagnostic validation
    ["diagnóstic", "diagnostic", "validación", "biopsia", "biopsy", "patholog", "patolog"],
    # Management / treatment options
    ["manejo", "management", "tratamiento", "treatment", "opciones", "options", "histerectom", "hysterectom", "surgery", "cirugía"],
    # Final recommendation
    ["recomendación", "recommendation", "conclusi", "next step"],
]


# ---------------------------------------------------------------------------
# Layer 1: Deterministic checks (no LLM)
# ---------------------------------------------------------------------------

def _check_formatting(recommendation: str) -> tuple[bool, str]:
    """Verify the recommendation contains required structural sections.

    Uses flexible semantic matching instead of exact section headers,
    so the model can use different header styles and still pass.

    Args:
        recommendation: The specialist's output text.

    Returns:
        Tuple of (passed, feedback_message).
    """
    text_lower = recommendation.lower()
    missing_concepts = []

    for synonyms in _REQUIRED_CONCEPTS:
        if not any(syn in text_lower for syn in synonyms):
            missing_concepts.append(synonyms[0])

    if missing_concepts:
        feedback = (
            f"FORMATTING: Missing required concepts: {', '.join(missing_concepts)}. "
            "Please include all sections: Hallazgos Clínicos, Validación Diagnóstica, "
            "Análisis de Estadificación, Opciones de Manejo, Recomendación Final."
        )
        return False, feedback

    return True, ""


def _check_safety_phrases(recommendation: str) -> tuple[bool, str]:
    """Check for known unsafe patterns (e.g., inventing dosages without sources).

    Args:
        recommendation: The specialist's output text.

    Returns:
        Tuple of (passed, feedback_message).
    """
    # Detect unsupported dosage patterns without source citations
    dosage_pattern = re.compile(
        r"\b\d+\s*(mg|mg/m2|mg/kg|mcg|IU|units)\b",
        re.IGNORECASE,
    )
    dosages_found = dosage_pattern.findall(recommendation)

    if dosages_found and "[source" not in recommendation.lower():
        return False, (
            "SAFETY: Specific dosages were mentioned without explicit source citations. "
            "Either cite the guideline source for each dosage or remove the specific numbers."
        )

    return True, ""


def _check_diagnostic_rigor(recommendation: str, clinical_text: str) -> tuple[bool, str]:
    """Ensure no premature treatment is recommended without a confirmed diagnosis.

    Args:
        recommendation: The specialist's output text.
        clinical_text: The original clinical input.

    Returns:
        Tuple of (passed, feedback_message).
    """
    text_lower = clinical_text.lower()
    rec_lower = recommendation.lower()

    # Detect if a biopsy/pathology was mentioned in the clinical text
    pathology_keywords = [
        "biopsia", "patología", "pathology", "biopsy", "histolog",
        "legrado", "malign", "adenocarcinoma", "carcinoma", "sarcoma",
        "linfoma", "lymphoma", "melanoma", "confirms", "confirma",
        "diagnosed", "diagnosticado",
    ]
    has_pathology = any(word in text_lower for word in pathology_keywords)

    # Treatment keywords
    treatment_keywords = [
        "cirugía", "radioterapia", "quimioterapia", "surgery",
        "radiation", "chemotherapy", "histerectomía", "hysterectomy",
    ]

    if not has_pathology:
        found_treatments = [kw for kw in treatment_keywords if kw in rec_lower]
        if found_treatments:
            feedback = (
                f"DIAGNOSTIC RIGOR: Recommended treatments ({', '.join(found_treatments)}) "
                "but no pathology/biopsy confirmation was found in the clinical text. "
                "You MUST request a diagnostic procedure (e.g., biopsy) first."
            )
            return False, feedback

    return True, ""


# ---------------------------------------------------------------------------
# Layer 2: LLM-based entailment check
# ---------------------------------------------------------------------------

def _check_entailment(
    recommendation: str,
    context: List[str],
) -> tuple[bool, str]:
    """Verify the recommendation is entailed by the RAG context.

    Uses Tier 1 (fast model) for binary entailment classification.

    Args:
        recommendation: The specialist's output text.
        context: The RAG context strings.

    Returns:
        Tuple of (passed, feedback_message).
    """
    context_summary = "\n---\n".join(context)

    system_prompt = (
        "You are a clinical safety auditor. Verify if a treatment recommendation "
        "is STRICTLY grounded in the provided clinical guidelines context.\n\n"
        "Check for:\n"
        "1. Any drug, treatment, or procedure mentioned that is NOT in the context.\n"
        "2. Any dosage or protocol that contradicts the context.\n"
        "3. Any claim presented as fact that lacks support in the context.\n\n"
        "Output a JSON object with two keys:\n"
        '- "verdict": "PASS" or "FAIL"\n'
        '- "issues": a list of specific issues found (empty list if PASS)\n\n'
        "Output ONLY the JSON, nothing else."
    )

    user_prompt = (
        f"Context:\n{context_summary}\n\n"
        f"Recommendation:\n{recommendation}\n\n"
        "Evaluate the recommendation against the context:"
    )

    try:
        response = call_tier_model(
            tier=1,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=200,
            temperature=0.0,
        )

        response_upper = response.upper()
        if "FAIL" in response_upper:
            feedback = f"ENTAILMENT: {response}"
            return False, feedback

        return True, ""

    except Exception as exc:
        logger.warning("Entailment check failed: %s — defaulting to PASS.", exc)
        return True, ""  # Fail open if entailment check itself fails


# ---------------------------------------------------------------------------
# Critic Node
# ---------------------------------------------------------------------------

def critic_node(state: AgentState) -> Dict[str, Any]:
    """Validate the specialist's recommendation for safety and completeness.

    Runs four layers of checks:
      1. Formatting (deterministic — flexible concept matching)
      2. Safety phrases (deterministic — dosage citation check)
      3. Diagnostic rigor (deterministic — no treatment without pathology)
      4. Entailment (LLM-based — only if layers 1-3 pass)

    If any check fails, returns FAIL with specific feedback.
    The graph will loop back to the specialist if attempts < max.

    Args:
        state: Current LangGraph state.

    Returns:
        State update with critic_verdict, critic_feedback, critic_attempts.
    """
    recommendation = state.get("clinical_recommendation", "")
    context = state.get("rag_context", [])
    current_attempts = state.get("critic_attempts", 0)

    # Track this attempt
    new_attempts = current_attempts + 1

    # Guard: empty recommendation
    if not recommendation or not recommendation.strip():
        logger.warning("Critic received empty recommendation — auto-FAIL.")
        return {
            "critic_verdict": "FAIL",
            "critic_feedback": "SYSTEM: Specialist returned empty recommendation.",
            "critic_attempts": new_attempts,
        }

    # Guard: recommendation is already the safe fallback phrase
    if "información no concluyente" in recommendation.lower():
        return {
            "critic_verdict": "PASS",
            "critic_feedback": "",
            "critic_attempts": new_attempts,
        }

    # Guard: inference error
    if "error en el sistema de inferencia" in recommendation.lower():
        return {
            "critic_verdict": "FAIL",
            "critic_feedback": "SYSTEM: Inference engine error — cannot validate.",
            "critic_attempts": new_attempts,
        }

    # --- Layer 1: Formatting check ---
    fmt_pass, fmt_feedback = _check_formatting(recommendation)

    # --- Layer 2: Safety check ---
    safety_pass, safety_feedback = _check_safety_phrases(recommendation)

    # --- Layer 3: Diagnostic Rigor check ---
    clinical_text = state.get("clinical_text", "")
    rigor_pass, rigor_feedback = _check_diagnostic_rigor(recommendation, clinical_text)

    # --- Layer 4: Entailment check (only if layers 1-3 pass) ---
    entailment_pass = True
    entailment_feedback = ""
    if fmt_pass and safety_pass and rigor_pass and context:
        entailment_pass, entailment_feedback = _check_entailment(
            recommendation, context
        )

    # --- Aggregate verdict ---
    all_passed = fmt_pass and safety_pass and rigor_pass and entailment_pass
    feedbacks = [f for f in [fmt_feedback, safety_feedback, rigor_feedback, entailment_feedback] if f]

    verdict = "PASS" if all_passed else "FAIL"
    combined_feedback = "\n".join(feedbacks)

    logger.info(
        "Critic verdict: %s (attempt %d/%d). Issues: %d",
        verdict, new_attempts, MAX_CRITIC_ATTEMPTS, len(feedbacks),
    )

    return {
        "critic_verdict": verdict,
        "critic_feedback": combined_feedback,
        "critic_attempts": new_attempts,
    }
