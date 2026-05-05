"""
End-to-End integration test for the OncoAgent LangGraph pipeline.
Tests the full flow: ingestion -> RAG retrieval -> specialist -> validator.
"""

import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.graph import build_oncoagent_graph


def run_e2e_test():
    """Run a sample clinical case through the full OncoAgent pipeline."""
    
    print("=" * 70)
    print("  OncoAgent — End-to-End Pipeline Test")
    print("=" * 70)
    
    # Simulated clinical case (no real PHI)
    clinical_case = (
        "Patient is a 62-year-old male presenting with hepatocellular carcinoma "
        "(HCC), Stage III. Imaging reveals a 5.2 cm lesion in the right hepatic "
        "lobe with portal vein invasion. AFP elevated at 1200 ng/mL. "
        "No extrahepatic disease identified. Child-Pugh score B7. "
        "ECOG performance status 1. Prior treatment: none."
    )
    
    print(f"\n📋 Input Clinical Text:\n{clinical_case}\n")
    print("-" * 70)
    
    # Build and invoke the graph
    print("\n⏳ Building LangGraph pipeline...")
    graph = build_oncoagent_graph()
    
    print("🚀 Invoking pipeline...\n")
    result = graph.invoke({
        "clinical_text": clinical_case,
        "extracted_entities": {},
        "phi_detected": False,
        "rag_context": [],
        "clinical_recommendation": "",
        "safety_status": "",
        "is_safe": False,
        "routing_decision": "",
        "errors": [],
    })
    
    # Display results
    print("=" * 70)
    print("  PIPELINE RESULTS")
    print("=" * 70)
    
    print(f"\n🏷️  Extracted Entities:")
    entities = result.get("extracted_entities", {})
    print(f"   Cancer Type : {entities.get('cancer_type', 'N/A')}")
    print(f"   Stage       : {entities.get('stage', 'N/A')}")
    print(f"   Mutations   : {entities.get('mutations', [])}")
    
    print(f"\n🔒 PHI Detected: {result.get('phi_detected', 'N/A')}")
    
    rag_context = result.get("rag_context", [])
    print(f"\n📚 RAG Context Retrieved: {len(rag_context)} documents")
    for i, ctx in enumerate(rag_context[:2], 1):
        print(f"\n   --- Document {i} (first 200 chars) ---")
        print(f"   {ctx[:200]}...")
    
    print(f"\n💊 Clinical Recommendation:")
    rec = result.get("clinical_recommendation", "N/A")
    print(f"   {rec[:500]}...")
    
    print(f"\n✅ Safety Status: {result.get('safety_status', 'N/A')}")
    print(f"   Is Safe: {result.get('is_safe', 'N/A')}")
    
    print("\n" + "=" * 70)
    if result.get("is_safe"):
        print("  ✅ PIPELINE TEST PASSED — Safe recommendation generated.")
    else:
        print("  ⚠️  PIPELINE TEST — Recommendation flagged as unsafe.")
    print("=" * 70)


if __name__ == "__main__":
    run_e2e_test()
