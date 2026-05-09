import sys
import os
sys.path.append(os.getcwd())

from agents.nodes import data_ingestion_node

state = {
    "clinical_text": "The patient has irregular menstrual periods and heavy bleeding.",
    "messages": [],
    "manual_override": None,
    "errors": []
}

result = data_ingestion_node(state)
print(f"Extracted Entities: {result.get('extracted_entities')}")
print(f"Confidence Score: {result.get('initial_confidence_score')}")
