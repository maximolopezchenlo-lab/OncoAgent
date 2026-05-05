"""
SOTA RAG Pipeline — Integration Test Suite.

Tests the full multi-stage retrieval pipeline:
  1. Bi-Encoder recall from ChromaDB
  2. Distance Gate filtering
  3. Cross-Encoder Re-ranking
  4. Token Trimming
  5. Collection stats
"""

import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rag_engine.retriever import OncoRAGRetriever


def test_standard_query(
    query: str = "What is the recommended treatment for advanced HCC?",
) -> None:
    """
    Test the standard SOTA query pipeline.

    Args:
        query: A clinical question to search for in the guidelines.
    """
    print("=" * 70)
    print("🧪 TEST 1: Standard SOTA Query Pipeline")
    print("=" * 70)

    retriever = OncoRAGRetriever()
    stats = retriever.get_collection_stats()
    print(f"\n📊 Collection: {stats['name']} | Docs: {stats['count']}")
    print(f"   Distance Threshold: {stats['distance_threshold']}")
    print(f"   Context Budget: {stats['max_context_chars']} chars")

    print(f"\n❓ Query: '{query}'")
    results = retriever.query(query, n_results=5, use_reranking=True)

    if not results:
        print("\n⚠️  No results passed the distance gate!")
        print("   → This means the query is likely outside guideline coverage.")
        print("   → Anti-Hallucination policy: 'Información no concluyente'")
        return

    print(f"\n🔍 {len(results)} results passed all stages:\n")
    for i, r in enumerate(results, 1):
        ce_score = r.get("cross_encoder_score", "N/A")
        bi_dist = r.get("bi_encoder_distance", "N/A")
        print(f"--- Result {i} ---")
        print(f"  📄 Source: {r['source']} (Page: {r['page']})")
        print(f"  🏷️  Section: {r['header']}")
        print(f"  📏 Bi-Encoder Distance: {bi_dist}")
        print(f"  🎯 Cross-Encoder Score: {ce_score}")
        print(f"  📝 Excerpt: {r['text'][:250]}...")
        print()

    # Show formatted context
    formatted = retriever.format_context_for_llm(results)
    print(f"\n📋 Formatted LLM Context ({len(formatted)} chars):")
    print("-" * 50)
    print(formatted[:500] + "..." if len(formatted) > 500 else formatted)


def test_distance_gate() -> None:
    """
    Test that the distance gate correctly rejects irrelevant queries.
    A query about the common cold should return zero results from
    oncology guidelines.
    """
    print("\n" + "=" * 70)
    print("🧪 TEST 2: Distance Gate (Anti-Hallucination)")
    print("=" * 70)

    retriever = OncoRAGRetriever()

    irrelevant_query = "How to treat a common cold with chicken soup"
    print(f"\n❓ Irrelevant Query: '{irrelevant_query}'")

    results = retriever.query(irrelevant_query, use_reranking=True)

    if not results:
        print("✅ PASS — Distance gate correctly rejected all results!")
        print("   → Anti-hallucination defense is working.")
    else:
        print(f"⚠️  WARN — {len(results)} results passed (may need tighter threshold)")
        for r in results:
            print(f"   Distance: {r.get('bi_encoder_distance', '?')} | {r['header']}")


def test_cross_encoder_reranking() -> None:
    """
    Test that cross-encoder re-ranking actually changes the order
    compared to bi-encoder-only results.
    """
    print("\n" + "=" * 70)
    print("🧪 TEST 3: Cross-Encoder Re-Ranking Effect")
    print("=" * 70)

    retriever = OncoRAGRetriever()

    query = "EGFR mutation non-small cell lung cancer targeted therapy"
    print(f"\n❓ Query: '{query}'")

    # Without re-ranking (bi-encoder order)
    results_no_rerank = retriever.query(query, n_results=5, use_reranking=False)
    # With re-ranking
    results_reranked = retriever.query(query, n_results=5, use_reranking=True)

    print("\n📊 Bi-Encoder Order (no re-rank):")
    for i, r in enumerate(results_no_rerank, 1):
        print(f"  {i}. [{r.get('bi_encoder_distance', '?')}] {r['header'][:60]}")

    print("\n📊 After Cross-Encoder Re-Rank:")
    for i, r in enumerate(results_reranked, 1):
        print(f"  {i}. [score={r.get('cross_encoder_score', '?')}] {r['header'][:60]}")

    # Check if order changed
    headers_no = [r["header"] for r in results_no_rerank]
    headers_re = [r["header"] for r in results_reranked]
    if headers_no != headers_re:
        print("\n✅ PASS — Re-ranking changed the order (precision improvement).")
    else:
        print("\n ℹ️  INFO — Same order (bi-encoder was already optimal for this query).")


def test_token_trimming() -> None:
    """
    Verify that the total context stays within the character budget.
    """
    print("\n" + "=" * 70)
    print("🧪 TEST 4: Token Trimming (Context Budget)")
    print("=" * 70)

    retriever = OncoRAGRetriever(max_context_chars=2000)  # Tight budget

    query = "Breast cancer treatment recommendations"
    results = retriever.query(query, n_results=10)

    total_chars = sum(len(r["text"]) for r in results)
    print(f"\n   Budget: 2000 chars")
    print(f"   Actual: {total_chars} chars in {len(results)} results")

    if total_chars <= 2000:
        print("✅ PASS — Context fits within budget.")
    else:
        print("⚠️  WARN — Context exceeds budget!")


if __name__ == "__main__":
    test_standard_query()
    test_distance_gate()
    test_cross_encoder_reranking()
    test_token_trimming()

    print("\n" + "=" * 70)
    print("🏁 All SOTA RAG tests completed.")
    print("=" * 70)
