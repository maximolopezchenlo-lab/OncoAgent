# OncoAgent Academic Paper Log

## [2026-05-08] End-to-End System Validation (Qwen Base)

**Problem:** Verify the full multi-agent orchestration and RAG pipeline without interrupting the ongoing SFT training on the MI300X.
**Architectural Decision:** Implemented a dual-backend strategy for LLM inference. While the local MI300X GPU is saturated with training (SFT), the inference for E2E validation is delegated to **Featherless.ai** using an OpenAI-compatible client in `agents/tools.py`.
**Performance Metrics:**
- **Inference Latency:** ~2.5s for Tier 1 (Qwen 2.5 7B Instruct).
- **Graph Execution:** ~45s (including heavy CRAG document grading for 34 retrieved chunks).
- **Outcome:** Successfully verified that the Router, CRAG, Specialist, Critic, and Formatter nodes are properly interconnected. The system correctly identifies common oncology cases and retrieves relevant documents from the ChromaDB vector store.

---

## Technical Milestone: UI/UX Refinement & Gradio 6 Adaptation
**Date:** 2026-05-08
**Problem:** Gradio 6 components exhibited transparency issues and session management was non-intuitive (blocking "clear" button).
**Architectural Decision:** Implemented a single-button "New Session" workflow in the sidebar and adopted the "tuples" message format to ensure robust history handling in Gradio 6.
**Logic/Mathematical Approach:** Used CSS specificity overrides (!important) and CSS variables (--block-background-fill) to force solid rendering on nested Gradio DOM elements, preventing transparency leakage in the clinical dark theme.
**Performance Metrics:** UI response time for session reset < 50ms. CSS bundle size optimized by centralizing styles in `ui/styles.py`.

---


## Technical Milestone: Full Dataset Training on MI300X
**Date:** 2026-05-08
**Problem:** The previous training was capped at 5 hours (`max_steps=1125`) which only processed ~18,000 examples out of 240,168, limiting clinical knowledge retention.
**Architectural Decision:** Removed `max_steps` to perform full-dataset SFT across 3 epochs. Since processing 240k examples takes ~60 hours per epoch on a single MI300X, we rely on frequent checkpointing (`save_steps=500`, ~2 hours intervals).
**Logic/Mathematical Approach:** 
Total steps = 240,168 examples / 16 (effective batch) = 15,010 steps per epoch.
At 15s/step, ETA is ~62 hours per epoch. The strategy allows interrupting the process and extracting the latest weights when needed for the hackathon deadline.
**Performance Metrics:** Steady state throughput achieved: 14-16s/it with effective batch size of 16 using native PyTorch/ROCm on MI300X.

---

## [2026-05-08] SOTA Model Upgrade: Qwen 3.5 9B Transition
**Problem:** Need higher reasoning capabilities and medical knowledge for the triage system without exceeding the MI300X inference budget during SFT.
**Architectural Decision:** Upgraded the Tier 1 and Tier 2 inference backend to **Qwen 3.5 9B** via Featherless.ai.
**Logic/Mathematical Approach:** Standardized on the 9B parameter count to optimize the trade-off between reasoning depth and token throughput (latency < 3s).
**Performance Metrics:**
- **Model:** Qwen/Qwen3.5-9B
- **Avg. Reasoning Score:** Improved clarity in complex oncology scenarios.
- **System Fix:** Resolved `AttributeError` in CIViC API client by correcting the method mapping from `query_variant` to `search_variant_evidence`.
