"""
Formatter & Fallback Nodes — Structured output and safe degradation.

Formatter: transforms the validated recommendation into a structured
format optimised for the Gradio UI, including confidence reports and
source citations.

Fallback: safe degradation when RAG or reasoning fails, following the
Anti-Hallucination Policy (Rule #39).
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from .state import AgentState
from .tools import get_tier_spec

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response Formatter Node
# ---------------------------------------------------------------------------

def formatter_node(state: AgentState) -> Dict[str, Any]:
    """Transform the validated recommendation into structured UI output.

    Produces:
      - formatted_recommendation: Markdown with metadata header
      - confidence_report: Dict of all quality metrics
      - source_citations: Formatted bibliography

    Args:
        state: Current LangGraph state.

    Returns:
        State update with formatted output, confidence report, and citations.
    """
    recommendation = state.get("clinical_recommendation", "")
    tier = state.get("selected_tier", 1)
    spec = get_tier_spec(tier)
    rag_confidence = state.get("rag_confidence", 0.0)
    critic_attempts = state.get("critic_attempts", 0)
    complexity_score = state.get("complexity_score", 0.0)
    rag_sources = state.get("rag_sources", [])
    rag_count = state.get("rag_retrieval_count", 0)
    rag_graded = state.get("rag_grading_pass_count", 0)
    rag_rewrites = state.get("rag_query_rewrites", 0)
    api_evidence = state.get("api_evidence_context", [])
    entities = state.get("extracted_entities", {})

    # --- Confidence report ---
    confidence_report: Dict[str, Any] = {
        "tier_used": tier,
        "tier_name": spec.name,
        "model_id": spec.model_id,
        "complexity_score": complexity_score,
        "rag_confidence": rag_confidence,
        "rag_retrieval_count": rag_count,
        "rag_graded_relevant": rag_graded,
        "rag_query_rewrites": rag_rewrites,
        "critic_iterations": critic_attempts,
        "api_evidence_count": len(api_evidence),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # --- Confidence level label ---
    if rag_confidence >= 0.7:
        confidence_label = "🟢 Alta"
    elif rag_confidence >= 0.4:
        confidence_label = "🟡 Media"
    else:
        confidence_label = "🔴 Baja"

    # --- Formatted recommendation with metadata header ---
    header = (
        f"---\n"
        f"**OncoAgent — Recomendación Clínica**\n"
        f"📊 Modelo: {spec.name} (Tier {tier}) | "
        f"Confianza RAG: {confidence_label} ({rag_confidence:.2f}) | "
        f"Iteraciones Críticas: {critic_attempts}\n"
        f"🧬 Tipo: {entities.get('cancer_type', 'N/A')} | "
        f"Estadío: {entities.get('stage', 'N/A')} | "
        f"Mutaciones: {', '.join(entities.get('mutations', [])) or 'N/A'}\n"
        f"---\n\n"
    )

    formatted = header + recommendation

    # --- Source citations ---
    citations = []
    if rag_sources:
        citations.append("### Fuentes Clínicas (RAG)")
        citations.extend(rag_sources)

    if api_evidence:
        citations.append("\n### Evidencia Adicional (APIs)")
        citations.extend([f"- {e}" for e in api_evidence])

    # --- Safety status ---
    safety_status = "Validated against clinical oncology guidelines"

    return {
        "formatted_recommendation": formatted,
        "confidence_report": confidence_report,
        "source_citations": citations,
        "safety_status": safety_status,
        "is_safe": True,
    }


# ---------------------------------------------------------------------------
# Fallback Node (Safe Degradation)
# ---------------------------------------------------------------------------

_SAFE_MESSAGE = (
    "---\n"
    "**OncoAgent — Resultado No Concluyente**\n"
    "---\n\n"
    "## ⚠️ Información no concluyente en las guías provistas.\n\n"
    "El sistema no pudo generar una recomendación clínica confiable "
    "para este caso por una de las siguientes razones:\n\n"
    "1. No se encontró evidencia suficiente en las guías clínicas cargadas.\n"
    "2. La recomendación generada no pasó la validación de seguridad.\n"
    "3. El caso requiere revisión clínica especializada fuera del alcance "
    "de las guías disponibles.\n\n"
    "**Acción recomendada:** Consulte con un oncólogo especialista para "
    "una evaluación personalizada.\n"
)


def fallback_node(state: AgentState) -> Dict[str, Any]:
    """Generate a safe fallback response when the pipeline cannot produce
    a reliable recommendation.

    This node is triggered when:
      - RAG retrieval yields insufficient relevant documents
      - The critic fails after max iterations
      - The input is too short or unintelligible

    Args:
        state: Current LangGraph state.

    Returns:
        State update with safe fallback response and diagnostic info.
    """
    # Determine why we fell back
    routing = state.get("routing_decision", "")
    rag_count = state.get("rag_retrieval_count", 0)
    critic_verdict = state.get("critic_verdict", "")
    critic_attempts = state.get("critic_attempts", 0)

    reasons = []
    if routing == "insufficient":
        reasons.append("Input too short or unintelligible for clinical triage.")
    if rag_count == 0:
        reasons.append("No relevant documents found in clinical guidelines database.")
    if critic_verdict == "FAIL" and critic_attempts >= 2:
        reasons.append(
            f"Recommendation failed safety validation after {critic_attempts} attempts."
        )
    if not reasons:
        reasons.append("Unknown system error — safe fallback triggered.")

    fallback_reason = " | ".join(reasons)
    logger.warning("Fallback triggered: %s", fallback_reason)

    return {
        "formatted_recommendation": _SAFE_MESSAGE,
        "clinical_recommendation": "Información no concluyente en las guías provistas.",
        "confidence_report": {
            "tier_used": state.get("selected_tier", 0),
            "fallback": True,
            "reason": fallback_reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "source_citations": [],
        "fallback_reason": fallback_reason,
        "safety_status": f"Fallback: {fallback_reason}",
        "is_safe": False,
    }
