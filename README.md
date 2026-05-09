---
title: OncoAgent
emoji: 🧬
colorFrom: red
colorTo: blue
sdk: docker
pinned: false
license: apache-2.0
short_description: Multi-Agent Oncology Triage powered by AMD MI300X
---

# 🧬 OncoAgent — Multi-Agent Oncology Triage System

![ROCm](https://img.shields.io/badge/AMD-ROCm_7.2-ed1c24?logo=amd&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![vLLM](https://img.shields.io/badge/vLLM-PagedAttention-000000?logo=vllm&logoColor=white)
![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-FF4F00?logo=langchain&logoColor=white)
![Gradio](https://img.shields.io/badge/UI-Gradio_6-FF7C00?logo=gradio&logoColor=white)

> **AMD Developer Hackathon 2026** · Powered by AMD Instinct™ MI300X · ROCm 7.2

## 🌍 100% Open-Source: Democratizing Oncology
OncoAgent is proudly 100% open-source. We believe that life-saving clinical intelligence should not be locked behind proprietary APIs. Our solution is designed to:
- **Guarantee Patient Privacy:** Run locally on AMD MI300X hardware or private clouds, ensuring zero patient data leaves the hospital.
- **Foster Global Contribution:** Allow medical communities worldwide to easily audit, modify, and contribute to the RAG knowledge base.

OncoAgent is a state-of-the-art multi-agent clinical triage system designed to combat **unstructured data blindness** in primary care oncology. It leverages a tier-adaptive architecture featuring **Qwen 3.5-9B** (Speed Triage) and **Qwen 3.6-27B** (Deep Reasoning) models. Orchestrated via a sophisticated LangGraph state machine, it provides evidence-based oncological reasoning strictly grounded in NCCN/ESMO clinical guidelines, with built-in human-in-the-loop (HITL) safety gates and a Reflexion-based critic loop.

---

## 🏗️ Architecture

```
┌────────┐   ┌─────────┐   ┌─────────┐   ┌────────────┐      ┌────────────┐   ┌─────────┐
│ Router │──▶│Ingestion│──▶│Corrective│──▶│ Specialist │◀────│ Critic     │   │ Formatter│
│(Triage)│   │ (PHI)   │   │  RAG    │   │ (Qwen 9B/  │     │(Reflexion  │   │(Output)  │
└────────┘   └─────────┘   └─────────┘   │    27B)    │────▶│ Validation)│   └─────────┘
    │           │             │          └────────────┘      └────────────┘        ▲
    │           │             │                 │                   │              │
    ▼           ▼             ▼                 ▼                   ▼              │
  ┌───────────────────────────────────────────────────────────────────┐      ┌────────────┐
  │                           Fallback Node                           │      │ HITL Gate  │
  └───────────────────────────────────────────────────────────────────┘      │(Acuity Chk)│
                                                                             └────────────┘
```

**Key Components:**

| Module | Description |
|--------|-------------|
| `data_prep/` | Dataset builder: PMC-Patients/OncoCoT → Strict JSONL (Llama 3 chat template) |
| `rag_engine/` | The "Brain": PyMuPDF extraction, Adaptive Semantic Chunking of NCCN/ESMO PDFs, & ChromaDB + PubMedBERT vectorization. |
| `agents/` | The "Reasoning": LangGraph multi-agent orchestration (Router → Corrective RAG → Specialist ↔ Critic → HITL Gate). |
| `ui/` | The "Face": Gradio 6 UI with Glassmorphism for clinical note input, real-time source citations, and reasoning output. |

---

## 🧠 Dual-Tier Model Strategy (Qwen)

To maximize the compute capabilities of the **AMD MI300X**, OncoAgent implements a dynamic **Dual-Tier** routing strategy using the Qwen model family. **Both tiers have been fine-tuned on +200,000 real-world oncological cases covering all major cancer types** (derived from PMC-Patients and OncoCoT datasets) to ensure hyper-specialized medical reasoning:

- **Tier 1: Qwen 3.5-9B (Speed Triage):** A lightweight, extremely fast model used by the `Router` to assess initial complexity, perform simple triage, and handle low-risk queries.
- **Tier 2: Qwen 3.6-27B (Deep Reasoning):** The heavy-lifter. Activated for high-complexity clinical cases (e.g., metastasis, multi-mutations). It performs deep reasoning and entailment checks, avoiding confirmation bias through rigorous Reflexion loops.

---

## ⚡ Hardware Target

- **GPU:** AMD Instinct™ MI300X (192GB HBM3)
- **Software Stack:** ROCm 7.2.x, PyTorch (HIP), vLLM with PagedAttention
- **Models:** `Qwen/Qwen3.5-9B` (Speed Triage) & `Qwen/Qwen3.6-27B-Instruct` (Deep Reasoning)
- **Precision:** QLoRA 4-bit NormalFloat4 via `bitsandbytes` (ROCm compatible)

---

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone <repo-url>
cd OncoAgent

# 2. Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Start Inference Server (vLLM on Docker)
# This spins up the Qwen models optimized for AMD MI300X via ROCm PagedAttention
docker run --device /dev/kfd --device /dev/dri -p 8000:8000 rocm/vllm:latest \
    --model Qwen/Qwen3.6-27B-Instruct --tensor-parallel-size 1

# 4. Configure environment & Run UI
cp .env.example .env
# Set VLLM_API_BASE=http://localhost:8000/v1 in .env
python -m ui.app
```

---

## 📁 Project Structure

```
├── docs/                   # Documentation & research
│   ├── research/           # Deep Research analysis documents
│   ├── ADR/                # Architectural Decision Records
│   ├── oncoagent_master_directive.md
│   └── antigravity_rules.md
├── data_prep/              # Dataset preparation (Fase 0)
├── rag_engine/             # RAG ingestion & retrieval (Fase 0-3)
├── agents/                 # LangGraph orchestration (Fase 3)
├── ui/                     # Gradio frontend (Fase 4)
├── tests/                  # Unit & integration tests
├── scripts/                # Utility scripts
├── logs/                   # Paper log & social media log
├── requirements.txt        # Pinned dependencies
└── Dockerfile              # HF Spaces deployment
```

---

## 🩺 Safety Guarantees

- **Reflexion-based Critic Loop:** A dedicated safety node audits the Specialist's output against the RAG context (entailment verification). It forces the Specialist to regenerate its output if it detects ungrounded claims or invented dosages.
- **Human-In-The-Loop (HITL) Gate:** An acuity-based checkpoint that stops the pipeline for human clinician approval on high-risk cases (e.g., Stage IV + complex mutations).
- **Corrective RAG:** The system grades retrieved context relevance. If insufficient evidence is found, it safely falls back instead of guessing.
- **Zero-PHI:** Regex-based PII redaction before any processing
- **Reproducibility:** Fixed seeds (`torch.manual_seed(42)`) across all ML scripts

---

## 📄 License

This project was built for the AMD Developer Hackathon 2026.

---

## 👥 Team

Built with ❤️ and AMD Instinct MI300X.
