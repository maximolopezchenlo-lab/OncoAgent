import logging
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from rag_engine.retriever import OncoRAGRetriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sota_retrieval():
    # Note: We assume the graph and chroma_db are initialized
    # If the graph doesn't exist, it will just log a warning and return [] for graph search
    retriever = OncoRAGRetriever(
        db_path="data/chroma_db",
        collection_name="clinical_guidelines",
        distance_threshold=0.5 # Relaxed for testing
    )
    
    # Test 1: Genomic Query (Should trigger CIViC)
    logger.info("\n--- TEST 1: Genomic Query ---")
    results_genomic = retriever.query("Patient has BRAF V600E mutation. What are the evidence-based treatments?")
    for i, res in enumerate(results_genomic):
        print(f"[{i+1}] Source: {res['source']} | Type: {res.get('type', 'Standard')}")
        print(f"Content: {res['text'][:200]}...")
    
    # Test 2: Clinical Trial Query (Should trigger ClinicalTrials.gov)
    logger.info("\n--- TEST 2: Clinical Trial Query ---")
    results_trials = retriever.query("Search for recruiting trials for Non-Small Cell Lung Cancer.")
    for i, res in enumerate(results_trials):
        print(f"[{i+1}] Source: {res['source']} | Type: {res.get('type', 'Standard')}")
        print(f"Content: {res['text'][:200]}...")

    # Test 3: Graph Search (Should trigger if keywords match)
    logger.info("\n--- TEST 3: Graph Search Query ---")
    # Using keywords from advanced_ingestion.py: osimertinib, egfr, nsclc
    results_graph = retriever.query("Explain the relation between osimertinib and egfr in nsclc.")
    for i, res in enumerate(results_graph):
        print(f"[{i+1}] Source: {res['source']} | Type: {res.get('type', 'Standard')}")
        print(f"Content: {res['text'][:200]}...")

if __name__ == "__main__":
    test_sota_retrieval()
