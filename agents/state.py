"""
AgentState — Shared state schema for the OncoAgent LangGraph execution.

Design principles (inspired by Claude Code + Hermes Agent):
  - Immutable input: ``clinical_text`` is never mutated.
  - Additive outputs: each node writes to its own isolated keys.
  - Deterministic routing: ``routing_decision`` and ``selected_tier``
    are set by the Router node using structured logic, never free text.
  - Per-patient memory: ``patient_id`` isolates session history.
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
import operator
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Represents the state of the LangGraph execution for OncoAgent.

    Sections are ordered by the pipeline stage that writes them.
    Keys prefixed with ``#`` comments indicate which node owns each group.
    """

    # ------------------------------------------------------------------ #
    # 0. Session & Patient Context                                       #
    # ------------------------------------------------------------------ #
    patient_id: str                  # Unique patient profile ID
    session_id: str                  # Current session identifier
    user_tier_override: Optional[int]  # Manual tier override (1 or 2, None = auto)
    messages: Annotated[List[BaseMessage], add_messages]  # Chat history

    # ------------------------------------------------------------------ #
    # 1. Input (Immutable — set once at invocation)                      #
    # ------------------------------------------------------------------ #
    clinical_text: str

    # ------------------------------------------------------------------ #
    # 2. Router Node                                                     #
    # ------------------------------------------------------------------ #
    routing_decision: str            # "simple" | "complex" | "insufficient"
    selected_tier: int               # 1 (Qwen 3.5 9B) or 2 (Qwen 3.6 27B)
    complexity_score: float          # 0.0–1.0 complexity estimate

    # ------------------------------------------------------------------ #
    # 3. Ingestion Node (PHI clean + entity extraction)                  #
    # ------------------------------------------------------------------ #
    extracted_entities: Dict[str, Any]
    phi_detected: bool

    # ------------------------------------------------------------------ #
    # 4. Corrective RAG Node                                             #
    # ------------------------------------------------------------------ #
    rag_context: List[str]
    rag_sources: List[str]
    graph_rag_context: List[str]       # Clinical Knowledge Graph results
    api_evidence_context: List[str]    # CIViC / ClinicalTrials.gov results
    rag_confidence: float              # Mean cross-encoder score (0–1)
    rag_retrieval_count: int           # Results that passed the distance gate
    rag_grading_pass_count: int        # Documents graded RELEVANT by CRAG
    rag_query_rewrites: int            # Number of query rewrites performed

    # ------------------------------------------------------------------ #
    # 5. Specialist Node (Tier-adaptive reasoning)                       #
    # ------------------------------------------------------------------ #
    clinical_recommendation: str
    reasoning_trace: str               # Chain-of-thought breakdown

    # ------------------------------------------------------------------ #
    # 6. Critic Node (Reflexion loop)                                    #
    # ------------------------------------------------------------------ #
    critic_verdict: str                # "PASS" | "FAIL"
    critic_feedback: str               # Specific issues for specialist retry
    critic_attempts: int               # Current iteration count (max 2)

    # ------------------------------------------------------------------ #
    # 7. HITL Gate                                                       #
    # ------------------------------------------------------------------ #
    acuity_level: str                  # "low" | "medium" | "high"
    hitl_required: bool                # True if clinician approval needed
    hitl_approved: bool                # Set by clinician via UI interrupt

    # ------------------------------------------------------------------ #
    # 8. Formatter Node (final output)                                   #
    # ------------------------------------------------------------------ #
    formatted_recommendation: str      # Markdown-formatted for Gradio
    confidence_report: Dict[str, Any]  # Full metrics (tier, RAG, critic iters)
    source_citations: List[str]        # Formatted bibliography

    # ------------------------------------------------------------------ #
    # 9. Fallback Node                                                   #
    # ------------------------------------------------------------------ #
    fallback_reason: str               # Why the system fell back to safe mode

    # ------------------------------------------------------------------ #
    # 10. Safety (legacy compat + validator output)                      #
    # ------------------------------------------------------------------ #
    safety_status: str
    is_safe: bool

    # ------------------------------------------------------------------ #
    # 11. Error accumulator (append-only via operator.add)               #
    # ------------------------------------------------------------------ #
    errors: Annotated[List[str], operator.add]
