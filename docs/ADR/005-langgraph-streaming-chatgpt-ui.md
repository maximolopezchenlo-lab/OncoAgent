# ADR-005: LangGraph Streaming Migration & ChatGPT-style UI

**Date:** 2026-05-08
**Status:** Accepted
**Deciders:** Máximo López Chenlo

## Context

The OncoAgent UI was a static, one-shot dashboard using `agent_graph.invoke()` which blocked the Gradio event loop for the entire multi-agent pipeline duration (Router → RAG → Specialist ↔ Critic → Formatter). This caused:

1. **UI freezing** during inference (10-60s depending on model tier and RAG complexity)
2. **No conversational iteration** — oncologists could not ask follow-up questions
3. **Dropdown transparency bug** in Gradio's dark theme making model selection unreadable
4. **Monolithic CSS** embedded in `app.py` hurting maintainability

## Decision

1. **Replace `invoke()` with `stream(stream_mode="updates")`**: LangGraph's streaming API emits `{node_name: output_dict}` events as each node completes, enabling real-time progress display.

2. **ChatGPT-style layout**: Sidebar (session controls, KPIs, evidence tabs) + main chat area, following modern AI assistant conventions.

3. **CSS module extraction**: Moved all styling to `ui/styles.py` for separation of concerns.

4. **Dropdown fix**: Added 30+ explicit CSS selectors targeting Gradio's internal dropdown classes with solid backgrounds.

## Consequences

### Positive
- Zero perceived latency — UI updates node-by-node
- Conversational memory enables iterative clinical dialogue
- Cleaner code architecture (styles separated from logic)
- Fixed visual accessibility bug in model selector

### Negative
- Streaming requires generator functions, slightly more complex handler logic
- More CSS selectors to maintain for Gradio version upgrades

## Alternatives Considered

- **WebSocket-based streaming**: Too complex for Gradio's architecture
- **Polling-based progress**: Higher latency, more server load
- **Streamlit migration**: Would require full rewrite of all UI logic
