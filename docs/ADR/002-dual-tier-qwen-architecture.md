# ADR 002: Pivot to Dual-Tier Qwen Architecture

## Date
2026-05-06

## Status
Accepted

## Context
The project initially targeted `meta-llama/Meta-Llama-3.1-8B-Instruct` as the exclusive base model for fine-tuning. However, to maximize the utilization of the AMD Instinct MI300X capabilities (192GB VRAM) and offer a more versatile solution, the user explicitly requested a pivot to the Qwen model family. Specifically, the proposal involves a "Dual-Tier" architecture: offering a fast, lightweight model (Qwen 9B) and a high-accuracy, heavy model (Qwen 27B) for clinical triage.

Both models boast "Day 0" ROCm compatibility and their optimized hybrid architectures (Gated Delta Networks) have upstream support in vLLM.

## Decision
We will pivot the base model architecture from a single Llama 3.1 8B model to a Dual-Tier Qwen ecosystem:
1.  **Tier 1 (Speed & Efficiency):** Qwen 9B. Used for fast, low-latency initial triage.
2.  **Tier 2 (Deep Reasoning):** Qwen 27B. Used for complex cases requiring deeper clinical reasoning.

Both models will be fine-tuned using QLoRA (4-bit quantization via `bitsandbytes`) on the AMD MI300X, which has ample VRAM (192GB) to comfortably train a 27B model (~30GB VRAM requirement under QLoRA).

## Consequences
*   **Positive:** We can offer flexible deployment options to healthcare providers (speed vs. maximum accuracy). We fully leverage the MI300X's massive memory buffer.
*   **Negative:** Training two models will require running the fine-tuning pipeline twice (or in parallel, depending on GPU allocation), increasing total compute time.
*   **Technical Adaptation:** The data preprocessing pipeline must ensure that the JSONL outputs use Qwen's ChatML format (`<|im_start|>` / `<|im_end|>`) instead of Llama's `<|start_header_id|>` tokens, or rely on the native Qwen tokenizer templates.
