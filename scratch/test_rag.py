from rag_engine.retriever import OncoRAGRetriever
import logging

logging.basicConfig(level=logging.INFO)

retriever = OncoRAGRetriever()
results = retriever.query("Uterine Cancer", n_results=5)

print(f"Results for 'Uterine Cancer': {len(results)}")
for i, r in enumerate(results):
    print(f"[{i}] {r['source']} - {r['header']} (Score: {r.get('cross_encoder_score', 'N/A')})")

results2 = retriever.query("Uterine Neoplasms", n_results=5)
print(f"\nResults for 'Uterine Neoplasms': {len(results2)}")
for i, r in enumerate(results2):
    print(f"[{i}] {r['source']} - {r['header']} (Score: {r.get('cross_encoder_score', 'N/A')})")
