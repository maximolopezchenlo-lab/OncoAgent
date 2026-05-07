"""
Corrective RAG Node — Graded retrieval with query rewriting.

Design pattern: Corrective RAG (CRAG) from Yan et al. 2024
  1. Retrieve top-K documents from ChromaDB
  2. Grade each document for relevance (binary: RELEVANT / IRRELEVANT)
  3. If insufficient relevant docs → rewrite query and re-retrieve
  4. If still insufficient after max retries → route to fallback

Also implements parallelised evidence gathering:
  - ChromaDB (clinical guidelines)
  - CIViC API (genomic evidence)
  - ClinicalTrials.gov (active trials)
"""

import logging
import re
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .state import AgentState
from .tools import call_tier_model

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lazy-loaded retriever singleton
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
# Document Grading (CRAG core)
# ---------------------------------------------------------------------------

def _grade_document(document_text: str, query: str, tier: int = 1) -> bool:
    """Grade a single retrieved document for relevance.

    Uses the Tier 1 (fast) model for binary classification.

    Args:
        document_text: The document text to evaluate.
        query: The clinical query.
        tier: Model tier to use for grading (default: 1 for speed).

    Returns:
        True if the document is RELEVANT, False otherwise.
    """
    system_prompt = (
        "You are a medical document relevance evaluator. "
        "Given a clinical query and a retrieved document, determine if the document "
        "is RELEVANT to answering the query. "
        "Output ONLY the word 'RELEVANT' or 'IRRELEVANT', nothing else."
    )
    user_prompt = (
        f"Clinical Query: {query}\n\n"
        f"Retrieved Document:\n{document_text[:1500]}\n\n"
        f"Is this document relevant to the clinical query? (RELEVANT/IRRELEVANT):"
    )

    try:
        response = call_tier_model(
            tier=tier,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=10,
            temperature=0.0,
        )
        return "RELEVANT" in response.upper()
    except Exception as exc:
        logger.warning("Document grading failed: %s — defaulting to RELEVANT.", exc)
        return True  # Fail open: include document if grading fails


def _rewrite_query(
    original_query: str,
    entities: Dict[str, Any],
    attempt: int,
) -> str:
    """Broaden the query for a retry attempt.

    Uses deterministic broadening rather than LLM-based rewriting
    for speed and predictability.

    Args:
        original_query: The query that yielded insufficient results.
        entities: Extracted clinical entities.
        attempt: The retry attempt number (1-indexed).

    Returns:
        A broadened query string.
    """
    cancer = entities.get("cancer_type", "Unknown")
    stage = entities.get("stage", "Unknown")
    mutations = entities.get("mutations", [])

    if attempt == 1:
        # Broadening strategy: remove stage specificity, keep cancer + mutations
        parts = [cancer]
        if mutations:
            parts.append(f"mutations {' '.join(mutations)}")
        parts.append("treatment guidelines evidence-based recommendations")
        rewritten = " ".join(parts)
        logger.info("Query rewrite attempt %d: %s → %s", attempt, original_query, rewritten)
        return rewritten

    # Attempt 2+: maximally broad
    rewritten = f"{cancer} oncology clinical guidelines management"
    logger.info("Query rewrite attempt %d (maximal broadening): %s", attempt, rewritten)
    return rewritten


# ---------------------------------------------------------------------------
# Parallel Evidence Gathering
# ---------------------------------------------------------------------------

def _fetch_api_evidence(entities: Dict[str, Any]) -> Dict[str, List[str]]:
    """Fetch genomic and clinical trial evidence in parallel.

    Calls CIViC API and ClinicalTrials.gov concurrently for MI300X
    throughput optimisation.

    Args:
        entities: Extracted clinical entities.

    Returns:
        Dict with "genomic_evidence" and "clinical_trials" lists.
    """
    results: Dict[str, List[str]] = {
        "genomic_evidence": [],
        "clinical_trials": [],
    }

    mutations = entities.get("mutations", [])
    cancer = entities.get("cancer_type", "Unknown")

    def fetch_civic():
        """Fetch genomic evidence from CIViC."""
        try:
            from rag_engine.api_clients import CivicAPIClient
            client = CivicAPIClient()
            evidence = []
            for mutation in mutations:
                civic_results = client.query_variant(mutation, cancer)
                for r in civic_results:
                    evidence.append(
                        f"[CIViC] {mutation}: {r.get('summary', 'No summary available')}"
                    )
            return evidence
        except Exception as exc:
            logger.warning("CIViC API failed: %s", exc)
            return []

    def fetch_trials():
        """Fetch active clinical trials."""
        try:
            from rag_engine.api_clients import ClinicalTrialsClient
            client = ClinicalTrialsClient()
            trial_results = client.search_trials(cancer, mutations)
            return [
                f"[ClinicalTrials.gov] {t.get('title', 'Unknown')}: {t.get('status', '?')}"
                for t in trial_results
            ]
        except Exception as exc:
            logger.warning("ClinicalTrials.gov API failed: %s", exc)
            return []

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(fetch_civic): "genomic_evidence",
            executor.submit(fetch_trials): "clinical_trials",
        }
        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as exc:
                logger.error("Parallel fetch error (%s): %s", key, exc)

    return results


# ---------------------------------------------------------------------------
# Corrective RAG Node
# ---------------------------------------------------------------------------

# Minimum relevant documents required to proceed
_MIN_RELEVANT_DOCS = 2
# Maximum query rewrite attempts
_MAX_REWRITES = 1


def corrective_rag_node(state: AgentState) -> Dict[str, Any]:
    """Execute the Corrective RAG pipeline.

    Pipeline:
      1. Build structured query from extracted entities.
      2. Retrieve top-K candidates from ChromaDB.
      3. Grade each document for relevance.
      4. If insufficient relevant docs → rewrite query and retry.
      5. Fetch API evidence in parallel (CIViC + ClinicalTrials).
      6. Compute confidence metrics.

    Args:
        state: Current LangGraph state.

    Returns:
        State update with rag_context, sources, confidence, and metrics.
    """
    entities: Dict[str, Any] = state.get("extracted_entities", {})
    clinical_text: str = state.get("clinical_text", "")
    selected_tier: int = state.get("selected_tier", 1)

    # --- Build initial query ---
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

    rewrite_count = 0
    relevant_docs: List[Dict[str, Any]] = []

    try:
        retriever = _get_retriever()

        # --- Retrieve + Grade loop ---
        for attempt in range(1 + _MAX_REWRITES):
            if attempt > 0:
                query = _rewrite_query(query, entities, attempt)
                rewrite_count += 1

            # Retrieve candidates
            raw_results = retriever.query(query, n_results=8)

            # Grade each document
            graded = []
            for r in raw_results:
                doc_text = r.get("text", "")
                is_relevant = _grade_document(doc_text, query, tier=1)
                if is_relevant:
                    graded.append(r)

            logger.info(
                "CRAG attempt %d: %d/%d documents graded RELEVANT.",
                attempt + 1, len(graded), len(raw_results),
            )

            if len(graded) >= _MIN_RELEVANT_DOCS:
                relevant_docs = graded
                break

        # --- Format results ---
        context_strings = []
        source_strings = []
        for r in relevant_docs:
            context_strings.append(
                f"[Source: {r['source']}, Page: {r.get('page', '?')}, "
                f"Section: {r.get('header', 'Unknown')}]\n{r['text']}"
            )
            source_strings.append(
                f"- **{r['source']}** (Page {r.get('page', '?')}): "
                f"{r.get('header', 'Unknown')}"
            )

        # --- Confidence metrics ---
        ce_scores = [
            r["cross_encoder_score"]
            for r in relevant_docs
            if "cross_encoder_score" in r
        ]
        mean_confidence = sum(ce_scores) / len(ce_scores) if ce_scores else 0.0

    except Exception as exc:
        logger.error("RAG retrieval failed: %s", exc)
        context_strings = []
        source_strings = []
        relevant_docs = []
        mean_confidence = 0.0
        rewrite_count = 0

    # --- Parallel API evidence ---
    api_results = _fetch_api_evidence(entities)

    return {
        "rag_context": context_strings,
        "rag_sources": source_strings,
        "graph_rag_context": [],  # Future: knowledge graph integration
        "api_evidence_context": (
            api_results.get("genomic_evidence", [])
            + api_results.get("clinical_trials", [])
        ),
        "rag_confidence": round(mean_confidence, 4),
        "rag_retrieval_count": len(context_strings),
        "rag_grading_pass_count": len(relevant_docs),
        "rag_query_rewrites": rewrite_count,
    }
