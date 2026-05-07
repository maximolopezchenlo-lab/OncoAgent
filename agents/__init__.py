"""
OncoAgent Multi-Agent System — SOTA Architecture.

This package implements a production-grade clinical oncology triage system
using LangGraph for orchestration, incorporating:

  - Router: complexity classification + model tier selection
  - Corrective RAG: graded retrieval with query rewriting
  - Specialist: tier-adaptive clinical reasoning (9B/27B)
  - Critic: reflexion-pattern validation loop
  - HITL Gate: clinician approval for high-acuity cases
  - Formatter: structured output with confidence metrics

Architecture inspired by Claude Code, Hermes Agent, Corrective RAG,
and Reflexion patterns.
"""

from .graph import build_oncoagent_graph
from .state import AgentState
from .memory import get_memory_store, PatientMemoryStore
from .tools import get_vllm_client, call_tier_model, get_tier_spec, TIER_SPECS

__all__ = [
    "build_oncoagent_graph",
    "AgentState",
    "get_memory_store",
    "PatientMemoryStore",
    "get_vllm_client",
    "call_tier_model",
    "get_tier_spec",
    "TIER_SPECS",
]
