# ADR 006: BF16 Native Inference for Local Triage

## Status
Approved

## Context
The initial implementation of the local specialist (Tier 1) used Unsloth with 4-bit quantization (bitsandbytes) to minimize memory footprint. However, during validation on AMD MI300X hardware, we observed "semantic collapse" and repetitive token generation (e.g., repeating punctuation or phrases indefinitely).

Initial investigations suggested that 4-bit quantization artifacts, combined with the CDNA3 architecture's handling of certain sub-8bit kernels, were degrading inference quality for clinical tasks requiring high precision.

## Decision
We will migrate the `LocalModelManager` from Unsloth/4-bit to native **BFloat16 (BF16)** precision using the standard `transformers` and `peft` libraries.

Given the AMD MI300X's massive 192GB of VRAM, the increased memory requirement of BF16 (~14GB for a 7B model) is well within the hardware's capabilities, even with multiple concurrent agents.

## Consequences
- **Positive:** Improved semantic stability and elimination of repetitive output artifacts.
- **Positive:** Full compatibility with ROCm native bfloat16 kernels.
- **Positive:** Higher fidelity clinical reasoning compared to 4-bit quantized versions.
- **Neutral:** Higher VRAM consumption (approx. 2.5x compared to 4-bit), which is negligible on MI300X.
- **Neutral:** Slightly slower initialization time as larger weights are loaded into HBM3.
