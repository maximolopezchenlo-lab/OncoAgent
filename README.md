# 🧬 OncoAgent — Multi-Agent Oncology Triage System

> **AMD Developer Hackathon 2026** · Powered by AMD Instinct™ MI300X · ROCm 6.2

## 🌍 100% Open-Source: Democratizing Oncology
OncoAgent is proudly 100% open-source. We believe that life-saving clinical intelligence should not be locked behind proprietary APIs. Our solution is designed to:
- **Guarantee Patient Privacy:** Run locally on AMD MI300X hardware or private clouds, ensuring zero patient data leaves the hospital.
- **Foster Global Contribution:** Allow medical communities worldwide to easily audit, modify, and contribute to the RAG knowledge base.

OncoAgent is a multi-agent clinical triage system designed to combat **unstructured data blindness** in primary care oncology. It leverages a fine-tuned Llama 3.1 8B model orchestrated via LangGraph to provide evidence-based oncological reasoning grounded in NCCN/ESMO clinical guidelines.

---

## 🏗️ Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Router     │───▶│   RAG Engine │───▶│  Specialist  │
│  (PHI Clean) │    │ (ChromaDB +  │    │  (OncoCoT    │
│              │    │  BioBERT)    │    │   Reasoning) │
└──────────────┘    └──────────────┘    └──────────────┘
        │                                       │
        └──── LangGraph StateGraph ─────────────┘
```

**Key Components:**

| Module | Description |
|--------|-------------|
| `data_prep/` | Dataset builder: PMC-Patients/OncoCoT → JSONL (Llama 3 template) |
| `rag_engine/` | Semantic chunking of NCCN/ESMO PDFs + ChromaDB vectorization |
| `agents/` | LangGraph multi-agent orchestration (Router → RAG → Specialist) |
| `ui/` | Gradio interface for clinical note input and reasoning output |

---

## ⚡ Hardware Target

- **GPU:** AMD Instinct™ MI300X (192GB HBM3)
- **Software Stack:** ROCm 6.2.x, PyTorch (HIP), vLLM with PagedAttention
- **Model:** `meta-llama/Meta-Llama-3.1-8B-Instruct` (QLoRA 4-bit fine-tuned)

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

# 3. Configure environment
cp .env.example .env
# Edit .env with your HF_TOKEN

# 4. Run the UI
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

- **Anti-Hallucination:** Specialist agent responds *"Evidencia insuficiente"* when RAG context is insufficient
- **Zero-PHI:** Regex-based PII redaction before any processing
- **Reproducibility:** Fixed seeds (`torch.manual_seed(42)`) across all ML scripts

---

## 📄 License

This project was built for the AMD Developer Hackathon 2026.

---

## 👥 Team

Built with ❤️ and AMD Instinct MI300X.
