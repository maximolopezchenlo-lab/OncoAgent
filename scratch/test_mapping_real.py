import sys
import os
sys.path.append(os.getcwd())

from agents.nodes import data_ingestion_node

clinical_history = """
Concurro al médico porque tenía períodos irregulares de los cuales venía la menstruación más cantidad de lo habitual, duraba más de lo habitual y al ser irregular tenía períodos en el cual duraban 10 días, no venían por 2 meses, o venía 2 meses seguidos y un mes no menstruaba.
"""

state = {
    "clinical_text": clinical_history,
    "messages": [],
    "manual_override": None,
    "errors": []
}

result = data_ingestion_node(state)
print(f"Extracted Entities: {result.get('extracted_entities')}")
