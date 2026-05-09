
import logging
from agents.nodes import data_ingestion_node
from agents.state import AgentState

def test_phi_redaction():
    state: AgentState = {
        "clinical_text": "Patient John Doe, born on 12/12/1980, email test@example.com, SSN 123-45-6789. Reported irregular periods.",
        "extracted_entities": {}
    }
    
    result = data_ingestion_node(state)
    
    print(f"Original: {state['clinical_text']}")
    print(f"Redacted: {result['clinical_text']}")
    print(f"PHI Detected: {result['phi_detected']}")
    
if __name__ == "__main__":
    test_phi_redaction()
