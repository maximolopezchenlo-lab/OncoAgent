
import os
import sys
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.tools import call_tier_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("=== OncoAgent Local Adapter Validation ===")
    
    # Force local adapters
    os.environ["USE_LOCAL_ADAPTERS"] = "true"
    
    system_prompt = "You are an expert oncologist triage agent. Provide brief, clinical assessment."
    user_prompt = "Female patient with heavy menstrual bleeding for 10 days and cycles of amenorrhea. No diagnostic tests performed yet."
    
    print("\n[Test 1] Tier 1 - Speed Triage (Expected: Local Adapters)")
    try:
        response = call_tier_model(
            tier=1,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=256
        )
        print(f"\nResponse:\n{response}")
        print("\n[SUCCESS] Tier 1 inference completed.")
    except Exception as e:
        print(f"\n[FAILURE] Tier 1 inference failed: {e}")

    print("\n[Test 2] Tier 2 - Deep Reasoning (Expected: Featherless API Fallback)")
    try:
        response = call_tier_model(
            tier=2,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=256
        )
        print(f"\nResponse:\n{response}")
        print("\n[SUCCESS] Tier 2 inference completed via API.")
    except Exception as e:
        print(f"\n[FAILURE] Tier 2 inference failed: {e}")

if __name__ == "__main__":
    main()
