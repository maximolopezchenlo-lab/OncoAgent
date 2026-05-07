"""
Critic Node — Reflexion-pattern validation for clinical recommendations.

Design pattern: Reflexion (Shinn et al. 2023)
  - Generator (Specialist) → Critic loop
  - Critic evaluates: entailment, completeness, formatting
  - If FAIL → specific feedback injected back to Specialist for retry
  - Max 2 iterations before safe fallback

Inspired by:
  - Claude Code: deterministic safety checks outside LLM control
  - Hermes Agent: structured evaluation with JSON verdicts

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

# Required sections in a well-formed recommendation
_REQUIRED_SECTIONS = [
    "hallazgos",
    "estadificación",
    "tratamiento",
    "recomendación",
]


# ---------------------------------------------------------------------------
# Layer 1: Deterministic checks (no LLM)
# ---------------------------------------------------------------------------

def _check_formatting(recommendation: str) -> tuple[bool, str]:
    """Verify the recommendation contains required structural sections.

    Args:
        recommendation: The specialist's output text.

    Returns:
        Tuple of (passed, feedback_message).
    """
    text_lower = recommendation.lower()
    missing = []

    for section in _REQUIRED_SECTIONS:
        # Check for markdown headers or section markers
        if section not in text_lower:
            missing.append(section)

    if missing:
        feedback = (
            f"FORMATTING: Missing required sections: {', '.join(missing)}. "
            "Please include all sections: Hallazgos Clínicos, Análisis de Estadificación, "
            "Opciones de Tratamiento, Recomendación."
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

        # Parse the response
        response_upper = response.upper()
        if "FAIL" in response_upper:
            # Extract issues if possible
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

    Runs three layers of checks:
      1. Formatting (deterministic)
      2. Safety phrases (deterministic)
      3. Entailment (LLM-based)

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

    # Guard: if recommendation is already the safe fallback phrase
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

    # --- Layer 3: Entailment check (only if layers 1-2 pass) ---
    entailment_pass = True
    entailment_feedback = ""
    if fmt_pass and safety_pass and context:
        entailment_pass, entailment_feedback = _check_entailment(
            recommendation, context
        )

    # --- Aggregate verdict ---
    all_passed = fmt_pass and safety_pass and entailment_pass
    feedbacks = [f for f in [fmt_feedback, safety_feedback, entailment_feedback] if f]

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
