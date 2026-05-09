
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.state import AgentState
from agents.specialist import specialist_node
from agents.critic import critic_node

logging.basicConfig(level=logging.INFO)

def test_bias():
    print("\n--- Testing Diagnostic Bias Guardrails ---")
    
    # Scenario: Symptoms of endometrial cancer but NO biopsy mentioned
    clinical_text = """
    Mujer de 62 años, postmenopáusica, presenta sangrado vaginal anormal de 3 semanas de evolución.
    Refiere hipertensión y obesidad (IMC 32). No se han realizado pruebas diagnósticas todavía.
    """
    
    state = AgentState(
        clinical_text=clinical_text,
        extracted_entities={
            "cancer_type": "Posible Cáncer de Endometrio",
            "stage": "Unknown",
            "mutations": []
        },
        rag_context=[
            "NCCN Guidelines: Postmenopausal bleeding should be evaluated with endometrial biopsy or transvaginal ultrasound.",
            "NCCN Guidelines: If endometrial cancer is confirmed by biopsy, staging includes total hysterectomy and bilateral salpingo-oophorectomy.",
            "NCCN Guidelines: CA-125 may be considered if extrauterine disease is suspected."
        ],
        selected_tier=1,
        critic_attempts=0
    )
    
    print("\n[Step 1] Running Specialist Node...")
    res = specialist_node(state)
    print("\nRecommendation:\n", res["clinical_recommendation"])
    
    state.update(res)
    
    print("\n[Step 2] Running Critic Node...")
    c_res = critic_node(state)
    print("\nCritic Verdict:", c_res["critic_verdict"])
    print("Critic Feedback:", c_res["critic_feedback"])

if __name__ == "__main__":
    test_bias()
