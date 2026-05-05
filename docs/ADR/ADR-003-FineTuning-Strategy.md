# ADR-003: Fine-Tuning Strategy for Oncological Guideline Alignment

## Status
Proposed

## Date
2026-05-05

## Context
To achieve state-of-the-art (SOTA) performance in clinical oncology triage, the base model (meta-llama/Meta-Llama-3.1-8B-Instruct) requires supervised fine-tuning (SFT) on structured medical knowledge. The challenge is to maintain high accuracy while operating within the memory constraints and architectural specificities of the AMD Instinct MI300X hardware.

## Decision
We will implement a QLoRA (Quantized Low-Rank Adaptation) strategy using 4-bit NormalFloat4 (NF4) quantization.

### Technical Details:
1. **Precision:** 4-bit NF4 using a ROCm-compatible fork of `bitsandbytes`.
2. **Compute Dtype:** `torch.float16` to leverage MI300X Matrix Core performance.
3. **PEFT Configuration:**
   - Rank (r): 64
   - Alpha: 16
   - Target Modules: All linear layers (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`) to maximize adaptation capacity.
4. **Dataset:** Instruction-tuning dataset generated from NCCN/ESMO guideline chunks, formatted in Llama 3 chat template.
5. **Optimizer:** `paged_adamw_32bit` for memory efficiency.

## Consequences
- **Pros:**
  - Significant reduction in VRAM usage (allowing for larger batch sizes or context windows).
  - Maintains near-full precision performance of the adapted layers.
  - High reproducibility via fixed seeds and standardized hyperparameters.
- **Cons:**
  - Quantization overhead might slightly increase latency during the initial loading phase.
  - Requires specific ROCm environment setup for `bitsandbytes`.
