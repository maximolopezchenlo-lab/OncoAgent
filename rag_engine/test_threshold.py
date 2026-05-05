import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rag_engine.retriever import OncoRAGRetriever

def main():
    queries = [
        "Patient with Stage III colon cancer, KRAS mutated",
        "Paciente masculino de 65 años con cáncer de colon en Estadio III, mutación KRAS",
        "Tratamiento para glioblastoma recurrente en adultos mayores",
        "How to treat a common cold with vitamin C",
        "Melanoma metastásico con mutación BRAF V600E, progresión tras ipilimumab",
        "Receta para hacer una torta de chocolate",
        "Non-small cell lung cancer stage IV with EGFR exon 19 deletion",
        "Dolor de cabeza leve y fiebre baja en niño de 8 años"
    ]
    
    retriever = OncoRAGRetriever()
    
    for q in queries:
        print(f"\n{'='*60}\nQuery: {q}")
        candidates, distances = retriever._bi_encoder_retrieve(q, 5)
        for i, (cand, dist) in enumerate(zip(candidates, distances)):
            pass_gate = "PASS" if dist <= retriever.distance_threshold else "FAIL"
            print(f"  [{i}] Dist: {dist:.4f} [{pass_gate}] | Source: {cand['source']} - {cand['header']}")

if __name__ == '__main__':
    main()
