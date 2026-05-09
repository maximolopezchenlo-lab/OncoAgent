# OncoAgent: High-Performance Oncology Triage on AMD MI300X

## Project Overview
OncoAgent is a multi-agent clinical decision support system designed to automate oncological triage following NCCN and ESMO guidelines. The system is optimized for **AMD Instinct MI300X** hardware, leveraging ROCm 7.2 and high-precision inference.

## Technical Milestones Accomplished
- **Stable BF16 Inference:** Successfully migrated the local inference engine from 4-bit quantization to native **bfloat16** precision, eliminating semantic collapse and repetitive output artifacts.
- **MI300X Optimization:** Leveraged the 192GB HBM3 memory of the MI300X to load full-fidelity models (Qwen 2.5 7B) and LoRA adapters.
- **LangGraph Orchestration:** Implemented a robust multi-agent state machine that handles clinical safety checks, RAG retrieval, and specialist reasoning.
- **Bilingual Documentation:** Maintained a dual-language (English/Spanish) workflow for all technical documentation, logs, and ADRs.

## Validation Results
- **Hardware Compatibility:** Confirmed native support for `bfloat16` and HIP kernels on MI300X.
- **Inference Quality:** Validated with complex clinical cases (e.g., uterine bleeding/menstrual irregularities), achieving coherent and clinically sound reasoning.
- **System Integrity:** All core components (RAG, Tools, Agents) are integrated and operational in the local droplet environment.

## Deployment Ready
The system is fully configured for a final demo and submission to Hugging Face Spaces.
