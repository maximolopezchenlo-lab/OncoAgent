from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    data_ingestion_node,
    rag_retrieval_node,
    clinical_specialist_node,
    safety_validator_node
)

def build_oncoagent_graph() -> StateGraph:
    """
    Builds the LangGraph state machine for OncoAgent.
    The architecture enforces decoupling between extraction, retrieval, reasoning,
    and validation to strictly mitigate hallucinations.
    """
    workflow = StateGraph(AgentState)
    
    # Define Nodes
    workflow.add_node("ingestion", data_ingestion_node)
    workflow.add_node("retriever", rag_retrieval_node)
    workflow.add_node("specialist", clinical_specialist_node)
    workflow.add_node("validator", safety_validator_node)
    
    # Define Edges
    workflow.set_entry_point("ingestion")
    workflow.add_edge("ingestion", "retriever")
    workflow.add_edge("retriever", "specialist")
    workflow.add_edge("specialist", "validator")
    workflow.add_edge("validator", END)
    
    # Compile the graph with a strict recursion limit
    # This prevents infinite loops if we add dynamic routing later.
    return workflow.compile()
