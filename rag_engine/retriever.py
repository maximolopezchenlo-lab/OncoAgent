"""
OncoRAG Retriever: Bridge between LangGraph agents and ChromaDB.
Provides a clean interface for querying the medical vector database.
"""

import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from typing import List, Dict, Optional


class OncoRAGRetriever:
    """
    Retriever class that connects LangGraph agent nodes to the
    ChromaDB clinical guidelines vector database.

    Uses PubMedBERT-based embeddings for medical semantic search.

    Args:
        db_path: Path to the persistent ChromaDB directory.
        collection_name: Name of the ChromaDB collection to query.
        model_name: Sentence-Transformer model for embedding queries.
        n_results: Default number of results to return per query.
    """

    def __init__(
        self,
        db_path: str = "data/chroma_db",
        collection_name: str = "clinical_guidelines",
        model_name: str = "pritamdeka/S-PubMedBert-MS-MARCO",
        n_results: int = 5,
    ):
        self.db_path = db_path
        self.n_results = n_results

        self._client = chromadb.PersistentClient(path=db_path)
        self._emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )
        self._collection = self._client.get_collection(
            name=collection_name,
            embedding_function=self._emb_fn,
        )

    def query(
        self,
        query_text: str,
        n_results: Optional[int] = None,
        cancer_type_filter: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Perform a semantic search against the clinical guidelines database.

        Args:
            query_text: The natural-language clinical question.
            n_results: Override the default number of results.
            cancer_type_filter: Optional source filename filter (e.g. 'breast.pdf').

        Returns:
            A list of dicts, each containing 'text', 'source', 'page', and 'header'.
        """
        k = n_results or self.n_results
        where_filter = None
        if cancer_type_filter:
            where_filter = {"source": cancer_type_filter}

        results = self._collection.query(
            query_texts=[query_text],
            n_results=k,
            where=where_filter,
        )

        formatted: List[Dict[str, str]] = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                formatted.append({
                    "text": doc,
                    "source": meta.get("source", "Unknown"),
                    "page": str(meta.get("page", "?")),
                    "header": meta.get("header", "Unknown"),
                })

        return formatted

    def format_context_for_llm(self, results: List[Dict[str, str]]) -> str:
        """
        Formats retrieval results into a single string suitable for
        injection into an LLM prompt as grounding context.

        Args:
            results: The list of dicts returned by self.query().

        Returns:
            A formatted multi-section string ready for LLM consumption.
        """
        if not results:
            return "No relevant clinical guidelines found for this query."

        sections: List[str] = []
        for i, r in enumerate(results, 1):
            sections.append(
                f"[Source {i}] {r['source']} — Page {r['page']} — Section: {r['header']}\n"
                f"{r['text']}"
            )
        return "\n\n---\n\n".join(sections)
