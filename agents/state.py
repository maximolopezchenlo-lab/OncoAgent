from typing import TypedDict, Annotated, List, Dict, Any
import operator

class AgentState(TypedDict):
    """
    Represents the state of the LangGraph execution for OncoAgent.
    Inspired by high-performance decoupled architectures (e.g., Biofy).
    Ensures the original clinical text remains immutable while adding
    specialized outputs in isolated keys to prevent hallucinations and data pollution.
    """
    
    # 1. Input (Immutable)
    clinical_text: str
    
    # 2. Extracted Data (Data Ingestion Node)
    extracted_entities: Dict[str, Any]
    phi_detected: bool
    
    # 3. RAG Context (Retrieval Node)
    rag_context: List[str]
    
    # 4. Clinical Reasoning (Specialist Node)
    clinical_recommendation: str
    
    # 5. Safety & Verification (Validator Node)
    safety_status: str
    is_safe: bool
    
    # 6. Routing/Control
    routing_decision: str
    # Use operator.add to allow appending errors without overwriting
    errors: Annotated[List[str], operator.add]
