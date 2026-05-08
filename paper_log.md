# OncoAgent Academic Paper Log

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
