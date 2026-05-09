"""
Router Node — Complexity classification and model tier selection.

Design pattern: Supervisor Routing (LangGraph SOTA)
Inspired by:
  - Claude Code: deterministic routing via structured logic, not free text
  - Hermes Agent: structured JSON output for decisions

The router classifies each clinical case into one of three categories:
  - ``simple``:  Well-known cancer + standard staging → Tier 1 (9B)
  - ``complex``: Rare cancer / multi-mutation / ambiguous staging → Tier 2 (27B)
  - ``insufficient``: Input too short or unintelligible → direct fallback

Supports manual tier override from the UI (user can force Tier 1 or 2).
"""

import logging
import json
from typing import Dict, Any, Optional

from .state import AgentState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Complexity heuristics
# ---------------------------------------------------------------------------

# Cancer types considered "well-documented" with standard NCCN guidelines
_COMMON_CANCERS = frozenset({
    "breast cancer", "lung cancer", "colon cancer", "colorectal cancer",
    "prostate cancer", "melanoma", "bladder cancer", "thyroid cancer",
    "cervical cancer", "ovarian cancer", "gastric cancer", "uterine cancer",
})

# Cancer types considered rare or requiring deeper reasoning
_RARE_CANCERS = frozenset({
    "pancreatic cancer", "hepatocellular carcinoma", "sarcoma",
    "glioma", "glioblastoma", "multiple myeloma", "renal cell carcinoma",
    "esophageal cancer", "cholangiocarcinoma", "mesothelioma",
    "neuroendocrine tumor", "adrenocortical carcinoma",
})

# Mutations that indicate multi-pathway complexity
_COMPLEX_MUTATIONS = frozenset({
    "EGFR", "ALK", "KRAS", "NTRK", "RET", "MET", "ROS1",
    "PIK3CA", "MSI-H", "DMMR", "BRAF V600E",
})

# Minimum character count for a clinically meaningful input
_MIN_INPUT_LENGTH = 30


def _classify_complexity(
    clinical_text: str,
    entities: Dict[str, Any],
) -> tuple[str, float, int]:
    """Classify case complexity using rule-based heuristics.

    Args:
        clinical_text: Raw clinical text.
        entities: Extracted entities from the ingestion node.

    Returns:
        Tuple of (routing_decision, complexity_score, recommended_tier).
    """
    # Gate: insufficient input
    if len(clinical_text.strip()) < _MIN_INPUT_LENGTH:
        logger.info("Input too short (%d chars) — routing to insufficient.", len(clinical_text))
        return "insufficient", 0.0, 1

    score = 0.0
    cancer_type = entities.get("cancer_type", "Unknown").lower()
    stage = entities.get("stage", "Unknown")
    mutations = entities.get("mutations", [])

    # --- Cancer type scoring ---
    if cancer_type in _RARE_CANCERS:
        score += 0.4
    elif cancer_type == "unknown":
        score += 0.3  # Unidentified cancer is inherently complex
    # Common cancers add no complexity

    # --- Stage scoring ---
    if "IV" in stage.upper():
        score += 0.25
    elif "III" in stage.upper():
        score += 0.15

    # --- Mutation complexity ---
    complex_muts = [m for m in mutations if m.upper() in _COMPLEX_MUTATIONS]
    if len(complex_muts) >= 2:
        score += 0.3  # Multi-mutation = high complexity
    elif len(complex_muts) == 1:
        score += 0.15

    # --- Prior treatment mentions (heuristic) ---
    prior_treatment_keywords = [
        "prior treatment", "previously treated", "relapsed",
        "refractory", "second-line", "third-line", "progression",
        "resistance", "failed", "recurrent",
    ]
    text_lower = clinical_text.lower()
    for kw in prior_treatment_keywords:
        if kw in text_lower:
            score += 0.1
            break

    # Clamp to [0, 1]
    score = min(score, 1.0)

    # Decision boundary
    if score >= 0.5:
        return "complex", score, 2
    else:
        return "simple", score, 1


# ---------------------------------------------------------------------------
# Router Node
# ---------------------------------------------------------------------------

def router_node(state: AgentState) -> Dict[str, Any]:
    """Classify case complexity and select the appropriate model tier.

    If the user has set ``user_tier_override`` in the state, that
    takes precedence over the automatic classification.

    Args:
        state: Current LangGraph state.

    Returns:
        State update with routing_decision, complexity_score, selected_tier.
    """
    clinical_text: str = state.get("clinical_text", "")
    entities: Dict[str, Any] = state.get("extracted_entities", {})
    user_override: Optional[int] = state.get("user_tier_override")

    # Run automatic classification
    decision, score, auto_tier = _classify_complexity(clinical_text, entities)

    # Apply manual override if present
    if user_override in (1, 2):
        selected_tier = user_override
        logger.info(
            "Manual tier override applied: Tier %d (auto would be Tier %d, score=%.2f)",
            user_override, auto_tier, score,
        )
    else:
        selected_tier = auto_tier
        logger.info(
            "Auto-routing: decision=%s, score=%.2f → Tier %d",
            decision, score, selected_tier,
        )

    return {
        "routing_decision": decision,
        "complexity_score": round(score, 4),
        "selected_tier": selected_tier,
    }
