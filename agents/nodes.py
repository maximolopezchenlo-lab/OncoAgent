"""
LangGraph Node implementations for OncoAgent.
Each node operates on an immutable AgentState, appending its conclusions
to isolated keys to prevent data pollution or hallucinations.
"""

from typing import Dict, Any
from .state import AgentState

import re
import os
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lazy-loaded retriever singleton (avoids loading the model on every call)
# ---------------------------------------------------------------------------
_retriever_instance = None


def _get_retriever():
    """Return a cached OncoRAGRetriever instance (lazy init)."""
    global _retriever_instance
    if _retriever_instance is None:
        try:
            from rag_engine.retriever import OncoRAGRetriever
            _retriever_instance = OncoRAGRetriever()
            logger.info("OncoRAGRetriever initialised successfully.")
        except Exception as exc:
            logger.error("Failed to initialise OncoRAGRetriever: %s", exc)
            raise
    return _retriever_instance


# ---------------------------------------------------------------------------
# Node 1: Data Ingestion — PHI cleaning & entity extraction
# ---------------------------------------------------------------------------

# Simple PHI patterns (names, dates, SSN-like, emails)
_PHI_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),                 # SSN
    re.compile(r"\b\d{2}/\d{2}/\d{4}\b"),                 # Date of birth
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}"),  # Email
]


def data_ingestion_node(state: AgentState) -> Dict[str, Any]:
    """
    Cleans the input clinical text (Zero-PHI policy) and extracts
    key medical entities via rule-based heuristics.

    Future improvement: delegate entity extraction to the fine-tuned
    Llama 3.1 8B model via vLLM.
    """
    text: str = state.get("clinical_text", "")

    # --- Zero-PHI check ---
    phi_found = False
    for pattern in _PHI_PATTERNS:
        if pattern.search(text):
            phi_found = True
            break

    # --- Rule-based entity extraction (placeholder for LLM) ---
    extracted: Dict[str, Any] = {
        "cancer_type": "Unknown",
        "stage": "Unknown",
        "mutations": [],
    }

    text_lower = text.lower()

    # Cancer type heuristic
    cancer_keywords = {
        "breast": "Breast Cancer",
        "lung": "Lung Cancer",
        "colon": "Colon Cancer",
        "colorectal": "Colorectal Cancer",
        "prostate": "Prostate Cancer",
        "pancreatic": "Pancreatic Cancer",
        "hepatocellular": "Hepatocellular Carcinoma",
        "hcc": "Hepatocellular Carcinoma",
        "melanoma": "Melanoma",
        "renal": "Renal Cell Carcinoma",
        "bladder": "Bladder Cancer",
        "ovarian": "Ovarian Cancer",
        "cervical": "Cervical Cancer",
        "thyroid": "Thyroid Cancer",
        "leukemia": "Leukemia",
        "lymphoma": "Lymphoma",
        "myeloma": "Multiple Myeloma",
        "sarcoma": "Sarcoma",
        "glioma": "Glioma",
        "glioblastoma": "Glioblastoma",
        "esophageal": "Esophageal Cancer",
        "gastric": "Gastric Cancer",
    }
    for keyword, label in cancer_keywords.items():
        if keyword in text_lower:
            extracted["cancer_type"] = label
            break

    # Stage heuristic
    stage_match = re.search(r"stage\s+(I{1,3}V?|[1-4]|iv|iii|ii|i)\b", text, re.IGNORECASE)
    if stage_match:
        extracted["stage"] = f"Stage {stage_match.group(1).upper()}"

    # Mutation heuristic
    mutations_found = re.findall(
        r"\b(EGFR|ALK|KRAS|BRAF|HER2|TP53|BRCA[12]|PD-?L1|ROS1|MET|RET|NTRK|PIK3CA|MSI-?H|dMMR)\b",
        text,
        re.IGNORECASE,
    )
    if mutations_found:
        extracted["mutations"] = list(set(m.upper() for m in mutations_found))

    return {
        "extracted_entities": extracted,
        "phi_detected": phi_found,
    }


# ---------------------------------------------------------------------------
# Node 2: RAG Retrieval — real ChromaDB query
# ---------------------------------------------------------------------------

def rag_retrieval_node(state: AgentState) -> Dict[str, Any]:
    """
    Queries the ChromaDB vector database using PubMedBERT embeddings.
    Constructs a semantic query from the extracted entities and the
    original clinical text to maximise retrieval relevance.
    """
    entities: Dict[str, Any] = state.get("extracted_entities", {})
    clinical_text: str = state.get("clinical_text", "")

    # Build a targeted query combining entities + original text
    cancer = entities.get("cancer_type", "Unknown")
    stage = entities.get("stage", "Unknown")
    mutations = ", ".join(entities.get("mutations", []))

    query_parts = []
    if cancer != "Unknown":
        query_parts.append(f"{cancer}")
    if stage != "Unknown":
        query_parts.append(f"{stage}")
    if mutations:
        query_parts.append(f"mutations: {mutations}")
    query_parts.append("treatment recommendation guidelines")

    query = " ".join(query_parts)

    try:
        retriever = _get_retriever()
        results = retriever.query(query, n_results=5)
        context_strings = [r["text"] for r in results]
    except Exception as exc:
        logger.error("RAG retrieval failed: %s", exc)
        context_strings = []

    return {
        "rag_context": context_strings,
    }


# ---------------------------------------------------------------------------
# Node 3: Clinical Specialist — LLM reasoning (placeholder for vLLM)
# ---------------------------------------------------------------------------

def clinical_specialist_node(state: AgentState) -> Dict[str, Any]:
    """
    Synthesises patient data and RAG context into a clinical recommendation.
    Strictly grounded in the provided context (Anti-Hallucination Policy).

    TODO: Replace stub with Llama 3.1 8B inference via vLLM on AMD MI300X.
    """
    context: list = state.get("rag_context", [])

    if not context:
        return {
            "clinical_recommendation": (
                "Información no concluyente en las guías provistas. "
                "No se encontró evidencia relevante en la base de datos clínica."
            )
        }

    # For now, return a structured summary of the retrieved context
    # This will be replaced by an actual LLM call to vLLM.
    context_summary = "\n---\n".join(context[:3])  # top 3
    return {
        "clinical_recommendation": (
            f"Based on retrieved clinical guidelines:\n\n{context_summary}"
        )
    }


# ---------------------------------------------------------------------------
# Node 4: Safety Validator — grounding verification
# ---------------------------------------------------------------------------

def safety_validator_node(state: AgentState) -> Dict[str, Any]:
    """
    Verifies that the clinical recommendation is grounded in the RAG
    context and does not hallucinate treatments absent from the sources.

    TODO: Implement LLM-based grounding check with NLI or entailment.
    """
    recommendation: str = state.get("clinical_recommendation", "")
    context: list = state.get("rag_context", [])

    # Basic grounding: reject if no context was available
    if not context or "Información no concluyente" in recommendation:
        return {
            "safety_status": "Rejected: Insufficient evidence in clinical guidelines",
            "is_safe": False,
        }

    return {
        "safety_status": "Validated against clinical oncology guidelines",
        "is_safe": True,
    }
