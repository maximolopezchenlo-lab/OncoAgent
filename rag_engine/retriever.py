"""
OncoRAG SOTA Retriever — State-of-the-Art Medical Retrieval Pipeline.

Implements a multi-stage retrieval architecture:
  1. Bi-Encoder (PubMedBERT) → fast top-K candidates from ChromaDB
  2. Cross-Encoder Re-Ranking → precision-optimised ordering
  3. Distance Threshold Gate → anti-hallucination confidence filter
  4. HyDE Query Expansion → hypothetical document embedding for recall
  5. Token Trimming → context window budget control for Llama 3.1

Architecture inspired by:
  - Nogueira et al. (2019) "Multi-Stage Document Ranking with BERT"
  - Gao et al. (2023) "Precise Zero-Shot Dense Retrieval without Relevance Labels" (HyDE)
"""

import logging
import os
from typing import List, Dict, Optional, Tuple

import chromadb
import chromadb.utils.embedding_functions as embedding_functions

logger = logging.getLogger(__name__)


class OncoRAGRetriever:
    """
    SOTA Retriever connecting LangGraph agents to ChromaDB.

    Pipeline: Query → (optional HyDE) → Bi-Encoder → Cross-Encoder Re-Rank
              → Distance Gate → Token Trim → LLM-ready context.

    Args:
        db_path: Path to the persistent ChromaDB directory.
        collection_name: Name of the ChromaDB collection to query.
        bi_encoder_model: Sentence-Transformer model for embedding queries.
        cross_encoder_model: Cross-Encoder model for re-ranking candidates.
        n_candidates: Number of candidates fetched by the bi-encoder (wide net).
        n_results: Number of final results returned after re-ranking.
        distance_threshold: Maximum cosine distance to accept a result.
            Results above this threshold are considered irrelevant.
        max_context_chars: Maximum total character budget for LLM context.
    """

    # ------------------------------------------------------------------ init
    def __init__(
        self,
        db_path: str = "data/chroma_db",
        collection_name: str = "clinical_guidelines",
        bi_encoder_model: str = "pritamdeka/S-PubMedBert-MS-MARCO",
        cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        n_candidates: int = 15,
        n_results: int = 5,
        distance_threshold: float = 0.10,
        max_context_chars: int = 6000,
    ):
        self.db_path = db_path
        self.n_candidates = n_candidates
        self.n_results = n_results
        self.distance_threshold = distance_threshold
        self.max_context_chars = max_context_chars

        # --- Bi-Encoder (Stage 1: recall) ---
        self._client = chromadb.PersistentClient(path=db_path)
        self._emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=bi_encoder_model
        )
        self._collection = self._client.get_collection(
            name=collection_name,
            embedding_function=self._emb_fn,
        )
        logger.info(
            "Bi-Encoder loaded: %s | Collection: %s (%d docs)",
            bi_encoder_model,
            collection_name,
            self._collection.count(),
        )

        # --- Cross-Encoder (Stage 2: precision) ---
        self._cross_encoder = None
        self._cross_encoder_model_name = cross_encoder_model

    # Lazy-load the cross encoder to avoid blocking import time
    def _get_cross_encoder(self):
        """Return a cached CrossEncoder instance (lazy init)."""
        if self._cross_encoder is None:
            try:
                from sentence_transformers import CrossEncoder
                self._cross_encoder = CrossEncoder(
                    self._cross_encoder_model_name
                )
                logger.info(
                    "Cross-Encoder loaded: %s",
                    self._cross_encoder_model_name,
                )
            except ImportError:
                logger.warning(
                    "sentence-transformers CrossEncoder not available. "
                    "Falling back to bi-encoder ordering only."
                )
            except Exception as exc:
                logger.error("Failed to load Cross-Encoder: %s", exc)
        return self._cross_encoder

    # ------------------------------------------------- stage 1: bi-encoder
    def _bi_encoder_retrieve(
        self,
        query_text: str,
        n: int,
        cancer_type_filter: Optional[str] = None,
    ) -> Tuple[List[Dict], List[float]]:
        """
        Fetch top-N candidates from ChromaDB using PubMedBERT bi-encoder.

        Args:
            query_text: The natural-language clinical question.
            n: Number of candidate documents to retrieve.
            cancer_type_filter: Optional source filename filter.

        Returns:
            Tuple of (list of result dicts, list of distances).
        """
        where_filter = None
        if cancer_type_filter:
            where_filter = {"source": cancer_type_filter}

        results = self._collection.query(
            query_texts=[query_text],
            n_results=n,
            where=where_filter,
        )

        candidates: List[Dict] = []
        distances: List[float] = []

        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                dist = results["distances"][0][i] if results["distances"] else 999.0
                candidates.append({
                    "text": doc,
                    "source": meta.get("source", "Unknown"),
                    "page": str(meta.get("page", "?")),
                    "header": meta.get("header", "Unknown"),
                })
                distances.append(dist)

        return candidates, distances

    # ------------------------------------------------- stage 2: cross-encoder
    def _cross_encoder_rerank(
        self,
        query_text: str,
        candidates: List[Dict],
    ) -> List[Tuple[Dict, float]]:
        """
        Re-rank candidates using a Cross-Encoder for precise relevance scoring.

        The Cross-Encoder reads (query, document) pairs jointly, producing
        far more accurate relevance scores than bi-encoder cosine distance.

        Args:
            query_text: The original query string.
            candidates: List of candidate result dicts from bi-encoder.

        Returns:
            List of (result_dict, cross_encoder_score) sorted by relevance desc.
        """
        cross_enc = self._get_cross_encoder()
        if cross_enc is None or not candidates:
            # Fallback: return candidates in original order with dummy scores
            return [(c, 0.0) for c in candidates]

        pairs = [(query_text, c["text"]) for c in candidates]
        try:
            scores = cross_enc.predict(pairs)
        except Exception as exc:
            logger.error("Cross-Encoder scoring failed: %s", exc)
            return [(c, 0.0) for c in candidates]

        scored = list(zip(candidates, scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    # ------------------------------------------------- stage 3: distance gate
    def _apply_distance_gate(
        self,
        candidates: List[Dict],
        distances: List[float],
    ) -> List[Dict]:
        """
        Filter out candidates whose bi-encoder distance exceeds the threshold.

        This implements the Anti-Hallucination Distance Gate (Rule #8):
        if all results are too far from the query embedding, it is safer
        to return nothing than to hallucinate from irrelevant context.

        Args:
            candidates: List of result dicts.
            distances: Corresponding distances from bi-encoder.

        Returns:
            Filtered list of candidates that pass the gate.
        """
        passed: List[Dict] = []
        for cand, dist in zip(candidates, distances):
            if dist <= self.distance_threshold:
                cand["bi_encoder_distance"] = round(dist, 4)
                passed.append(cand)
            else:
                logger.debug(
                    "Distance gate rejected (%.4f > %.4f): %s",
                    dist,
                    self.distance_threshold,
                    cand.get("header", "?"),
                )
        return passed

    # ------------------------------------------------- stage 4: token trim
    def _trim_to_budget(self, results: List[Dict]) -> List[Dict]:
        """
        Trim the final result list so the total text stays within the
        character budget for the LLM context window.

        This prevents overflowing Llama 3.1 8B's context when many
        long guideline sections are retrieved.

        Args:
            results: Ordered list of result dicts (best first).

        Returns:
            Subset of results fitting within max_context_chars.
        """
        trimmed: List[Dict] = []
        char_count = 0
        for r in results:
            text_len = len(r["text"])
            if char_count + text_len > self.max_context_chars:
                # Try to include a truncated version of the next result
                remaining = self.max_context_chars - char_count
                if remaining > 200:  # Only include if meaningful
                    truncated = r.copy()
                    truncated["text"] = r["text"][:remaining] + "… [truncated]"
                    trimmed.append(truncated)
                break
            trimmed.append(r)
            char_count += text_len
        return trimmed

    # ------------------------------------------------- public: main query
    def query(
        self,
        query_text: str,
        n_results: Optional[int] = None,
        cancer_type_filter: Optional[str] = None,
        use_reranking: bool = True,
    ) -> List[Dict[str, str]]:
        """
        Full SOTA retrieval pipeline.

        Stage 1 — Bi-Encoder: Cast a wide net (n_candidates) via PubMedBERT.
        Stage 2 — Distance Gate: Reject low-confidence results.
        Stage 3 — Cross-Encoder: Re-rank survivors for precision.
        Stage 4 — Token Trim: Fit within LLM context budget.

        Args:
            query_text: The natural-language clinical question.
            n_results: Override the default number of final results.
            cancer_type_filter: Optional source filename filter.
            use_reranking: Whether to apply cross-encoder re-ranking.

        Returns:
            A list of dicts with 'text', 'source', 'page', 'header',
            and optionally 'cross_encoder_score' / 'bi_encoder_distance'.
        """
        k = n_results or self.n_results

        # Stage 1: Bi-Encoder wide recall
        candidates, distances = self._bi_encoder_retrieve(
            query_text, self.n_candidates, cancer_type_filter
        )
        logger.info(
            "Bi-Encoder returned %d candidates for query: '%s'",
            len(candidates),
            query_text[:80],
        )

        if not candidates:
            return []

        # Stage 2: Distance Gate (anti-hallucination)
        gated = self._apply_distance_gate(candidates, distances)
        logger.info(
            "Distance gate passed: %d / %d (threshold=%.2f)",
            len(gated),
            len(candidates),
            self.distance_threshold,
        )

        if not gated:
            logger.warning(
                "All candidates rejected by distance gate — "
                "query likely outside guideline coverage."
            )
            return []

        # Stage 3: Cross-Encoder Re-ranking
        if use_reranking and len(gated) > 1:
            scored = self._cross_encoder_rerank(query_text, gated)
            # Take top-k after re-ranking
            final = []
            for cand, score in scored[:k]:
                cand["cross_encoder_score"] = round(float(score), 4)
                final.append(cand)
        else:
            final = gated[:k]

        # Stage 4: Token trimming for LLM context budget
        final = self._trim_to_budget(final)

        logger.info(
            "Final retrieval: %d results (total chars: %d / %d budget)",
            len(final),
            sum(len(r["text"]) for r in final),
            self.max_context_chars,
        )
        return final

    # ------------------------------------------------- public: HyDE query
    def query_with_hyde(
        self,
        original_query: str,
        hypothetical_answer: str,
        n_results: Optional[int] = None,
        cancer_type_filter: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        HyDE (Hypothetical Document Embeddings) retrieval.

        Instead of embedding the user's question, we embed a hypothetical
        answer generated by the LLM. This dramatically improves recall
        for medical synonym matching (e.g. "neoplasia pulmonar" vs
        "lung carcinoma").

        The LLM generates a plausible (but unverified) answer, which is
        then used as the query for bi-encoder search. The Cross-Encoder
        then re-ranks against the ORIGINAL query for precision.

        Args:
            original_query: The actual clinical question (used for re-ranking).
            hypothetical_answer: LLM-generated hypothetical answer (used for embedding).
            n_results: Override the default number of final results.
            cancer_type_filter: Optional source filename filter.

        Returns:
            A list of result dicts, same format as query().
        """
        k = n_results or self.n_results

        # Stage 1: Bi-Encoder using the hypothetical answer as query
        candidates, distances = self._bi_encoder_retrieve(
            hypothetical_answer, self.n_candidates, cancer_type_filter
        )

        if not candidates:
            return []

        # Stage 2: Distance gate
        gated = self._apply_distance_gate(candidates, distances)
        if not gated:
            return []

        # Stage 3: Cross-Encoder re-rank against ORIGINAL query (not HyDE)
        if len(gated) > 1:
            scored = self._cross_encoder_rerank(original_query, gated)
            final = []
            for cand, score in scored[:k]:
                cand["cross_encoder_score"] = round(float(score), 4)
                final.append(cand)
        else:
            final = gated[:k]

        # Stage 4: Token trim
        final = self._trim_to_budget(final)
        return final

    # ------------------------------------------------- public: format for LLM
    def format_context_for_llm(self, results: List[Dict[str, str]]) -> str:
        """
        Format retrieval results into a single string suitable for
        injection into an LLM prompt as grounding context.

        Includes confidence metadata when available.

        Args:
            results: The list of dicts returned by self.query().

        Returns:
            A formatted multi-section string ready for LLM consumption.
        """
        if not results:
            return "No relevant clinical guidelines found for this query."

        sections: List[str] = []
        for i, r in enumerate(results, 1):
            header_line = (
                f"[Source {i}] {r['source']} — Page {r['page']} "
                f"— Section: {r['header']}"
            )
            # Add confidence metadata if present
            meta_parts: List[str] = []
            if "cross_encoder_score" in r:
                meta_parts.append(f"Relevance: {r['cross_encoder_score']:.2f}")
            if "bi_encoder_distance" in r:
                meta_parts.append(f"Distance: {r['bi_encoder_distance']:.4f}")
            if meta_parts:
                header_line += f" | {' | '.join(meta_parts)}"

            sections.append(f"{header_line}\n{r['text']}")

        return "\n\n---\n\n".join(sections)

    # ------------------------------------------------- public: diagnostics
    def get_collection_stats(self) -> Dict:
        """
        Return basic stats about the underlying ChromaDB collection.

        Returns:
            Dict with 'count', 'name', and 'db_path'.
        """
        return {
            "count": self._collection.count(),
            "name": self._collection.name,
            "db_path": self.db_path,
            "distance_threshold": self.distance_threshold,
            "max_context_chars": self.max_context_chars,
        }
