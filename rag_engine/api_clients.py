import requests
import logging
import json
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class CivicAPIClient:
    """
    Client for CIViC (Clinical Interpretations of Variants in Cancer).
    Uses GraphQL (API v2) to fetch evidence for molecular profiles.
    """
    BASE_URL = "https://civicdb.org/api/graphql"

    def search_variant_evidence(self, gene: str, variant: str) -> List[Dict]:
        """
        Searches for evidence related to a specific gene and variant using GraphQL.
        """
        logger.info(f"Searching CIViC GraphQL for {gene} {variant}...")
        
        # Try different naming conventions for the Molecular Profile
        mp_names = [f"{gene} {variant}", f"{gene}-{variant}", f"{gene}_{variant}"]
        
        query = """
        query GetEvidenceByMolecularProfile($name: String!) {
          molecularProfiles(name: $name, first: 1) {
            nodes {
              id
              name
              evidenceItems(first: 5) {
                nodes {
                  id
                  status
                  description
                  evidenceType
                  evidenceDirection
                  evidenceLevel
                  clinicalSignificance
                }
              }
            }
          }
        }
        """
        
        for name in mp_names:
            variables = {"name": name.upper()}
            try:
                response = requests.post(
                    self.BASE_URL, 
                    json={'query': query, 'variables': variables},
                    timeout=15
                )
                response.raise_for_status()
                data = response.json()
                
                profiles = data.get("data", {}).get("molecularProfiles", {}).get("nodes", [])
                if profiles:
                    evidence_items = profiles[0].get("evidenceItems", {}).get("nodes", [])
                    if evidence_items:
                        return evidence_items
            except Exception as e:
                logger.error(f"Error querying CIViC for {name}: {e}")
                continue
                
        return []

class ClinicalTrialsClient:
    """
    Client for ClinicalTrials.gov API v2.
    Fetches active Phase II/III trials for specific conditions.
    """
    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

    def search_trials(self, condition: str, phases: List[str] = ["Phase 2", "Phase 3"]) -> List[Dict]:
        """
        Searches for recruiting/active trials for a condition.
        Uses query.term for phases to be more flexible.
        """
        logger.info(f"Searching ClinicalTrials.gov for {condition} trials...")
        
        processed_trials = []
        
        for phase in phases:
            # Using query.term instead of filter.phase to avoid 400 errors
            params = {
                "format": "json",
                "query.cond": condition,
                "query.term": phase,
                "filter.overallStatus": "RECRUITING",
                "pageSize": 3
            }
            try:
                resp = requests.get(self.BASE_URL, params=params, timeout=10)
                resp.raise_for_status()
                studies = resp.json().get("studies", [])
                
                for study in studies:
                    info = study.get("protocolSection", {})
                    processed_trials.append({
                        "nctId": info.get("identificationModule", {}).get("nctId"),
                        "title": info.get("identificationModule", {}).get("briefTitle"),
                        "status": info.get("statusModule", {}).get("overallStatus"),
                        "phase": phase,
                        "briefSummary": info.get("descriptionModule", {}).get("briefSummary", ""),
                        "eligibility": info.get("eligibilityModule", {}).get("eligibilityCriteria", "")
                    })
                
                if len(processed_trials) >= 5:
                    break
                    
            except Exception as e:
                logger.error(f"Error querying ClinicalTrials API for phase {phase}: {e}")
                continue
        
        return processed_trials

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    civic = CivicAPIClient()
    trials = ClinicalTrialsClient()
    
    print("\n--- Testing CIViC (BRAF V600E) ---")
    results = civic.search_variant_evidence("BRAF", "V600E")
    print(f"Found {len(results)} evidence items.")
    for res in results:
        print(f"- [{res['evidenceLevel']}] {res['clinicalSignificance']}: {res['description'][:100]}...")
    
    print("\n--- Testing ClinicalTrials.gov (Lung Cancer) ---")
    results_trials = trials.search_trials("Non-Small Cell Lung Cancer")
    print(f"Found {len(results_trials)} recruiting trials.")
    for t in results_trials:
        print(f"- {t['nctId']} ({t['phase']}): {t['title']}")
