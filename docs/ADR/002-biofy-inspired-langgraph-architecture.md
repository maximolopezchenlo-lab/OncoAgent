# ADR 002: Biofy-Inspired LangGraph Architecture

**Date:** 2026-05-04
**Status:** Accepted

## Context
OncoAgent requires a highly reliable multi-agent system to process unstructured clinical data and match it against NCCN/ESMO guidelines. Traditional linear LLM prompts suffer from context saturation and are prone to hallucinations, which is unacceptable in oncology.

During research, we analyzed architectures from high-performance HealthTech platforms like Biofy, which utilize specialized agent pipelines (DNA extraction -> Vector Search -> Synthesis) to achieve high accuracy and eliminate broad-spectrum guesswork.

## Decision
We decided to adopt a **Decoupled Multi-Agent Architecture using LangGraph**.
1. **Immutable State:** We defined an `AgentState` using `TypedDict` where the original clinical text is immutable.
2. **Specialized Nodes:** The workflow is strictly divided into four distinct roles:
   - `data_ingestion_node`: Extracts entities and enforces Zero-PHI.
   - `rag_retrieval_node`: Performs the semantic search against ChromaDB/FAISS.
   - `clinical_specialist_node`: Formulates the recommendation.
   - `safety_validator_node`: Enforces anti-hallucination checks.
3. **Strict Routing:** The graph is compiled with a fixed `recursion_limit` to prevent infinite loops during safety checks.

## Consequences
- **Positive:** Maximum traceability. We can log exactly what context was retrieved and how the specialist used it, making clinical auditing transparent.
- **Positive:** Prevents hallucinations by structurally forcing the specialist to only see the curated RAG context.
- **Negative:** Slightly increased latency compared to a single-shot prompt due to multiple LLM node invocations. However, running locally on AMD MI300X via vLLM PagedAttention will mitigate this overhead.
