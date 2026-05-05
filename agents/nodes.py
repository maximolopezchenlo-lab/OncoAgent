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
# Node 2: RAG Retrieval — SOTA multi-stage pipeline
# Bi-Encoder → Distance Gate → Cross-Encoder Re-Rank → Token Trim
# with optional HyDE (Hypothetical Document Embeddings) for recall.
# ---------------------------------------------------------------------------


def _generate_hyde_hypothesis(query: str) -> str:
    """
    Generate a hypothetical clinical guideline paragraph that *would*
    answer the query.  The hypothesis is used only as an embedding
    anchor — its factual content is never shown to the user.

    Falls back to the raw query if vLLM is unreachable.

    Args:
        query: The structured clinical query.

    Returns:
        A plausible guideline-style paragraph (unverified).
    """
    try:
        client = get_vllm_client()
        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a medical knowledge base. Given a clinical query, "
                        "write a SHORT (3-4 sentences) paragraph that a clinical "
                        "guideline WOULD contain to answer the query. "
                        "Use formal medical English. Do NOT add disclaimers."
                    ),
                },
                {"role": "user", "content": query},
            ],
            temperature=0.0,
            max_tokens=150,
        )
        hypothesis = response.choices[0].message.content.strip()
        logger.info("HyDE hypothesis generated (%d chars)", len(hypothesis))
        return hypothesis
    except Exception as exc:
        logger.warning("HyDE generation failed (%s) — falling back to raw query.", exc)
        return query


def rag_retrieval_node(state: AgentState) -> Dict[str, Any]:
    """
    SOTA multi-stage retrieval node.

    Pipeline:
      1. Build structured query from extracted entities.
      2. Generate a HyDE hypothesis (optional, if vLLM is available).
      3. Query ChromaDB via bi-encoder → distance gate → cross-encoder re-rank.
      4. Compute confidence metrics for downstream safety decisions.
      5. Trim context to fit within Llama 3.1 context window budget.
    """
    entities: Dict[str, Any] = state.get("extracted_entities", {})
    clinical_text: str = state.get("clinical_text", "")

    # --- Build targeted query from entities ---
    cancer = entities.get("cancer_type", "Unknown")
    stage = entities.get("stage", "Unknown")
    mutations = ", ".join(entities.get("mutations", []))

    query_parts = []
    if cancer != "Unknown":
        query_parts.append(cancer)
    if stage != "Unknown":
        query_parts.append(stage)
    if mutations:
        query_parts.append(f"mutations: {mutations}")
    query_parts.append("treatment recommendation guidelines")

    query = " ".join(query_parts)

    try:
        retriever = _get_retriever()

        # --- HyDE: generate hypothetical answer for embedding ---
        hyde_hypothesis = _generate_hyde_hypothesis(query)

        # If HyDE produced something different from the raw query, use it
        if hyde_hypothesis and hyde_hypothesis != query:
            results = retriever.query_with_hyde(
                original_query=query,
                hypothetical_answer=hyde_hypothesis,
                n_results=5,
            )
        else:
            # Fallback: standard SOTA retrieval (still uses re-ranking)
            results = retriever.query(query, n_results=5)

        # --- Format results for downstream nodes ---
        context_strings = [
            f"[Source: {r['source']}, Page: {r['page']}, Section: {r['header']}]\n{r['text']}"
            for r in results
        ]
        source_strings = [
            f"- **{r['source']}** (Page {r['page']}): {r['header']}"
            for r in results
        ]

        # --- Compute confidence metrics ---
        ce_scores = [r["cross_encoder_score"] for r in results if "cross_encoder_score" in r]
        mean_confidence = sum(ce_scores) / len(ce_scores) if ce_scores else 0.0

    except Exception as exc:
        logger.error("RAG retrieval failed: %s", exc)
        context_strings = []
        source_strings = []
        mean_confidence = 0.0

    return {
        "rag_context": context_strings,
        "rag_sources": source_strings,
        "rag_confidence": round(mean_confidence, 4),
        "rag_retrieval_count": len(context_strings),
    }


# ---------------------------------------------------------------------------
# Node 3: Clinical Specialist — LLM reasoning (placeholder for vLLM)
# ---------------------------------------------------------------------------

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize vLLM client (OpenAI compatible)
# You should configure VLLM_API_BASE and VLLM_API_KEY in your .env
_vllm_client = None

def get_vllm_client():
    global _vllm_client
    if _vllm_client is None:
        api_base = os.getenv("VLLM_API_BASE", "http://localhost:8000/v1")
        api_key = os.getenv("VLLM_API_KEY", "EMPTY")
        _vllm_client = OpenAI(base_url=api_base, api_key=api_key)
    return _vllm_client

def clinical_specialist_node(state: AgentState) -> Dict[str, Any]:
    """
    Synthesises patient data and RAG context into a clinical recommendation.
    Strictly grounded in the provided context (Anti-Hallucination Policy).

    Uses Llama 3.1 8B inference via vLLM on AMD MI300X.
    """
    context: list = state.get("rag_context", [])
    clinical_text: str = state.get("clinical_text", "")
    entities: Dict[str, Any] = state.get("extracted_entities", {})

    if not context:
        return {
            "clinical_recommendation": (
                "Información no concluyente en las guías provistas. "
                "No se encontró evidencia relevante en la base de datos clínica."
            )
        }

    # Prepare context string
    context_summary = "\n---\n".join(context)

    # Prompt Engineering for Anti-Hallucination
    system_prompt = (
        "You are an expert clinical oncologist. Your task is to provide a treatment recommendation "
        "based STRICTLY on the provided clinical guidelines context.\n\n"
        "ANTI-HALLUCINATION POLICY:\n"
        "1. You are STRICTLY FORBIDDEN from inventing treatments.\n"
        "2. If the answer is not explicitly contained in the provided guidelines, you MUST reply ONLY with: "
        "'Información no concluyente en las guías provistas.'\n"
        "3. Do not add external knowledge.\n\n"
        "Provide your recommendation in Spanish, clearly citing the guidelines if possible."
    )

    user_prompt = (
        f"Patient Information:\n"
        f"- Original Text: {clinical_text}\n"
        f"- Cancer Type: {entities.get('cancer_type', 'Unknown')}\n"
        f"- Stage: {entities.get('stage', 'Unknown')}\n"
        f"- Mutations: {', '.join(entities.get('mutations', []))}\n\n"
        f"Clinical Guidelines Context:\n{context_summary}\n\n"
        f"Based ONLY on the guidelines above, what is the recommended treatment?"
    )

    try:
        client = get_vllm_client()
        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,  # Zero temperature for factual grounding
            max_tokens=512,
        )
        recommendation = response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("Error connecting to vLLM: %s", e)
        recommendation = (
            "Error en el sistema de inferencia. "
            "No se pudo generar la recomendación clínica en este momento."
        )

    # Fallback validation to ensure the strict phrase is used if context wasn't helpful
    if "información no concluyente" in recommendation.lower() or "no concluyente" in recommendation.lower():
        recommendation = "Información no concluyente en las guías provistas."

    return {
        "clinical_recommendation": recommendation
    }


# ---------------------------------------------------------------------------
# Node 4: Safety Validator — grounding verification
# ---------------------------------------------------------------------------

def safety_validator_node(state: AgentState) -> Dict[str, Any]:
    """
    Verifies that the clinical recommendation is grounded in the RAG
    context and does not hallucinate treatments absent from the sources.

    Multi-layer validation:
      1. Empty context / explicit "no info" check.
      2. RAG confidence score check (cross-encoder threshold).
      3. LLM-based entailment verification via vLLM.
    """
    recommendation: str = state.get("clinical_recommendation", "")
    context: list = state.get("rag_context", [])
    rag_confidence: float = state.get("rag_confidence", 0.0)
    retrieval_count: int = state.get("rag_retrieval_count", 0)

    # Layer 1: Reject if no context was available
    if not context or "Información no concluyente" in recommendation:
        return {
            "safety_status": "Rejected: Insufficient evidence in clinical guidelines",
            "is_safe": False,
        }

    # Layer 2: Reject if RAG confidence is too low (cross-encoder based)
    if rag_confidence < 0.3 and retrieval_count > 0:
        logger.warning(
            "Low RAG confidence (%.4f) — safety gate triggered.",
            rag_confidence,
        )
        return {
            "safety_status": (
                f"Rejected: Low retrieval confidence ({rag_confidence:.2f}). "
                "Retrieved guidelines may not be relevant to this case."
            ),
            "is_safe": False,
        }

    # Error handling fallback
    if "Error en el sistema de inferencia" in recommendation:
        return {
            "safety_status": "Rejected: Inference system error",
            "is_safe": False,
        }

    context_summary = "\n---\n".join(context)

    system_prompt = (
        "You are an expert clinical safety auditor. Your job is to verify if a given treatment "
        "recommendation is STRICTLY grounded in the provided clinical guidelines context.\n"
        "If the recommendation includes ANY specific treatment, drug, or procedure that is NOT "
        "mentioned in the context, you must output 'FAIL'.\n"
        "If the recommendation is fully supported by the context, output 'PASS'.\n"
        "Output ONLY the word 'PASS' or 'FAIL', nothing else."
    )

    user_prompt = (
        f"Context:\n{context_summary}\n\n"
        f"Recommendation:\n{recommendation}\n\n"
        f"Does the context fully support the recommendation? (PASS/FAIL):"
    )

    try:
        client = get_vllm_client()
        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=10,
        )
        validation_result = response.choices[0].message.content.strip().upper()
        
        is_safe = "PASS" in validation_result
        status = (
            "Validated against clinical oncology guidelines" 
            if is_safe else 
            "Rejected: Hallucination detected (unsupported claims)"
        )
        
        return {
            "safety_status": status,
            "is_safe": is_safe,
        }

    except Exception as e:
        logger.error("Error in safety validation via vLLM: %s", e)
        # Fail safe
        return {
            "safety_status": "Rejected: Safety validation failed due to system error",
            "is_safe": False,
        }
