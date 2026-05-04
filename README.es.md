# 🧬 OncoAgent — Sistema Multi-Agente de Triage Oncológico

> **AMD Developer Hackathon 2026** · Potenciado por AMD Instinct™ MI300X · ROCm 6.2

OncoAgent es un sistema de triage clínico multi-agente diseñado para combatir la **ceguera de datos no estructurados** en la oncología de atención primaria. Aprovecha un modelo Llama 3.1 8B con fine-tuning, orquestado a través de LangGraph para proporcionar razonamiento oncológico basado en evidencia y fundamentado en las guías clínicas de NCCN/ESMO.

---

## 🏗️ Arquitectura

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Enrutador  │───▶│ Motor RAG    │───▶│ Especialista │
│  (Limpieza   │    │ (ChromaDB +  │    │  (Razonamiento│
│   PHI)       │    │  BioBERT)    │    │   OncoCoT)   │
└──────────────┘    └──────────────┘    └──────────────┘
        │                                       │
        └──── LangGraph StateGraph ─────────────┘
```

**Componentes Clave:**

| Módulo | Descripción |
|--------|-------------|
| `data_prep/` | Generador de datasets: PMC-Patients/OncoCoT → JSONL (plantilla Llama 3) |
| `rag_engine/` | Chunking semántico de PDFs NCCN/ESMO + vectorización en ChromaDB |
| `agents/` | Orquestación multi-agente en LangGraph (Enrutador → RAG → Especialista) |
| `ui/` | Interfaz en Gradio para el ingreso de notas clínicas y salida de razonamiento |

---

## ⚡ Hardware Objetivo

- **GPU:** AMD Instinct™ MI300X (192GB HBM3)
- **Software Stack:** ROCm 6.2.x, PyTorch (HIP), vLLM con PagedAttention
- **Modelo:** `meta-llama/Meta-Llama-3.1-8B-Instruct` (QLoRA 4-bit fine-tuned)

---

## 🚀 Inicio Rápido

```bash
# 1. Clonar y preparar
git clone <repo-url>
cd OncoAgent

# 2. Instalar dependencias
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configurar entorno
cp .env.example .env
# Edita .env con tu HF_TOKEN

# 4. Iniciar la UI
python -m ui.app
```

---

## 📁 Estructura del Proyecto

```
├── docs/                   # Documentación e investigación
│   ├── research/           # Documentos de análisis (Deep Research)
│   ├── ADR/                # Registros de Decisiones Arquitectónicas
│   ├── oncoagent_master_directive.md
│   └── antigravity_rules.md
├── data_prep/              # Preparación del dataset (Fase 0)
├── rag_engine/             # Ingesta y recuperación RAG (Fase 0-3)
├── agents/                 # Orquestación LangGraph (Fase 3)
├── ui/                     # Frontend en Gradio (Fase 4)
├── tests/                  # Pruebas unitarias y de integración
├── scripts/                # Scripts de utilidad
├── logs/                   # Logs de papers y de redes sociales
├── requirements.txt        # Dependencias fijadas (pinned)
└── Dockerfile              # Despliegue en HF Spaces
```

---

## 🩺 Garantías de Seguridad

- **Anti-Alucinación:** El agente Especialista responde *"Evidencia insuficiente"* cuando el contexto del RAG no basta.
- **Cero-PHI:** Eliminación de PII (Información Personal Identificable) basada en expresiones regulares antes de cualquier procesamiento.
- **Reproducibilidad:** Semillas fijas (`torch.manual_seed(42)`) en todos los scripts de Machine Learning.

---

## 📄 Licencia

Este proyecto fue construido para el AMD Developer Hackathon 2026.

---

## 👥 Equipo

Construido con ❤️ y AMD Instinct MI300X.
