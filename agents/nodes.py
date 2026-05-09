"""
LangGraph Node implementations for OncoAgent.

This module retains the data ingestion node (PHI cleaning + entity extraction)
and re-exports all other nodes from their dedicated modules for backward
compatibility.

Module organisation (SOTA redesign):
  - agents/router.py       → Router Node (complexity classification)
  - agents/corrective_rag.py → Corrective RAG Node (graded retrieval)
  - agents/specialist.py   → Specialist Node (tier-adaptive reasoning)
  - agents/critic.py       → Critic Node (reflexion validation)
  - agents/formatter.py    → Formatter + Fallback Nodes
  - agents/tools.py        → Shared vLLM client + tier calling
  - agents/memory.py       → Per-patient session memory
"""

from typing import Dict, Any

import re
import logging

from .state import AgentState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# PHI Patterns (Zero-PHI Policy — Rule #39)
# ---------------------------------------------------------------------------

_PHI_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),                 # SSN
    re.compile(r"\b\d{2}/\d{2}/\d{4}\b"),                 # Date of birth
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}"),  # Email
]


# ---------------------------------------------------------------------------
# Node 1: Data Ingestion — PHI cleaning & entity extraction
# ---------------------------------------------------------------------------

def data_ingestion_node(state: AgentState) -> Dict[str, Any]:
    """Clean the input clinical text (Zero-PHI policy) and extract
    key medical entities via rule-based heuristics.

    Enhanced extraction includes:
      - Cancer type identification (20+ types)
      - TNM staging parsing
      - Biomarker/mutation detection (15+ markers)
      - Performance status detection (ECOG)
      - Urgency signals

    Args:
        state: Current LangGraph state with ``clinical_text``.

    Returns:
        State update with ``extracted_entities`` and ``phi_detected``.
    """
    text: str = state.get("clinical_text", "")

    # --- Zero-PHI check and redaction ---
    phi_found = False
    cleaned_text = text
    for pattern in _PHI_PATTERNS:
        if pattern.search(text):
            phi_found = True
            # Redact detected PHI
            cleaned_text = pattern.sub("[REDACTED]", cleaned_text)
    
    if phi_found:
        logger.warning("PHI detected and redacted from clinical input.")

    # Use cleaned text for downstream processing
    text = cleaned_text

    # --- Rule-based entity extraction ---
    extracted: Dict[str, Any] = {
        "cancer_type": "Unknown",
        "stage": "Unknown",
        "mutations": [],
        "ecog_status": "Unknown",
        "urgency": "routine",
    }

    text_lower = text.lower()

    # Cancer type heuristic (Explicit + Symptom-based risk)
    cancer_keywords = {
        "breast": "Breast Cancer",
        "lung": "Lung Cancer",
        "non-small cell": "Non-Small Cell Lung Cancer",
        "small cell lung": "Small Cell Lung Cancer",
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
        "cholangiocarcinoma": "Cholangiocarcinoma",
        "mesothelioma": "Mesothelioma",
        "uterine": "Uterine Cancer",
        "endometrial": "Uterine Cancer",
        # Symptom-based risk mapping (Triage mode) - Multilingual support
        "menstru": "Uterine Cancer",
        "vaginal": "Uterine Cancer",
        "bleeding": "Uterine Cancer",
        "sangrado": "Uterine Cancer",
        "periods": "Uterine Cancer",
        "periodo": "Uterine Cancer",
        "postmenopausal": "Uterine Cancer",
        "postmenopau": "Uterine Cancer",
        "hemorragia": "Uterine Cancer",
    }
    for keyword, label in cancer_keywords.items():
        if keyword in text_lower:
            extracted["cancer_type"] = label
            break

    # Stage heuristic (supports TNM and simple staging)
    stage_match = re.search(
        r"stage\s+(I{1,3}V?|[1-4]|iv|iii|ii|i)\b",
        text,
        re.IGNORECASE,
    )
    if stage_match:
        extracted["stage"] = f"Stage {stage_match.group(1).upper()}"

    # TNM staging
    tnm_match = re.search(
        r"\b(T[0-4x]N[0-3x]M[01x])\b",
        text,
        re.IGNORECASE,
    )
    if tnm_match:
        extracted["tnm"] = tnm_match.group(1).upper()

    # Mutation heuristic (expanded)
    mutations_found = re.findall(
        r"\b(EGFR|ALK|KRAS|BRAF|HER2|TP53|BRCA[12]|PD-?L1|ROS1|MET|RET|"
        r"NTRK|PIK3CA|MSI-?H|dMMR|FGFR[1-4]?|IDH[12]?|ERBB2|CDK[46]|"
        r"PTEN|APC|VEGF|mTOR)\b",
        text,
        re.IGNORECASE,
    )
    if mutations_found:
        extracted["mutations"] = list(set(m.upper() for m in mutations_found))

    # ECOG Performance Status
    ecog_match = re.search(
        r"(?:ECOG|performance\s+status)\s*(?:of\s*)?(\d)",
        text,
        re.IGNORECASE,
    )
    if ecog_match:
        extracted["ecog_status"] = f"ECOG {ecog_match.group(1)}"

    # Urgency detection
    urgency_keywords = [
        "urgent", "emergency", "critical", "immediate",
        "rapidly progressing", "acute", "life-threatening",
    ]
    for kw in urgency_keywords:
        if kw in text_lower:
            extracted["urgency"] = "urgent"
            break

    return {
        "extracted_entities": extracted,
        "phi_detected": phi_found,
    }


# ---------------------------------------------------------------------------
# Re-exports for backward compatibility
# ---------------------------------------------------------------------------

from .corrective_rag import corrective_rag_node as rag_retrieval_node  # noqa: E402, F401
from .specialist import specialist_node as clinical_specialist_node  # noqa: E402, F401
from .critic import critic_node as safety_validator_node  # noqa: E402, F401
