# 🧬 OncoAgent — Sistema Multi-Agente de Triaje Oncológico

> **AMD Developer Hackathon 2026** · Potenciado por AMD Instinct™ MI300X · ROCm 7.2

## 🌍 100% Código Abierto: Democratizando la Oncología
OncoAgent es orgullosamente 100% de código abierto. Creemos que la inteligencia clínica capaz de salvar vidas no debería estar bloqueada tras APIs propietarias. Nuestra solución está diseñada para:
- **Garantizar la Privacidad del Paciente:** Ejecutarse localmente en hardware AMD MI300X o nubes privadas, asegurando que ningún dato del paciente abandone el hospital.
- **Fomentar la Contribución Global:** Permitir a las comunidades médicas de todo el mundo auditar, modificar y contribuir fácilmente a la base de conocimiento RAG.

OncoAgent es un sistema de triaje clínico multi-agente de última generación diseñado para combatir la **ceguera por datos no estructurados** en la oncología de atención primaria. Aprovecha una arquitectura adaptativa por niveles con modelos **Qwen 3.5-9B** (Triaje Rápido) y **Qwen 3.6-27B** (Razonamiento Profundo). Orquestado a través de una sofisticada máquina de estados de LangGraph, proporciona razonamiento oncológico basado en evidencia estrictamente fundamentado en las guías clínicas de NCCN/ESMO, con puertas de seguridad de validación humana (HITL) integradas y un bucle de crítica basado en Reflexion.

---

## 🏗️ Arquitectura

```
┌────────┐   ┌─────────┐   ┌─────────┐   ┌────────────┐      ┌────────────┐   ┌─────────┐
│ Router │──▶│Ingestión│──▶│   RAG   │──▶│Especialista│◀────│  Crítico   │   │Formateo │
│(Triaje)│   │ (PHI)   │   │Correctiv│   │ (Qwen 9B/  │     │(Validación │   │(Salida) │
└────────┘   └─────────┘   └─────────┘   │    27B)    │────▶│ Reflexion) │   └─────────┘
    │           │             │          └────────────┘      └────────────┘        ▲
    │           │             │                 │                   │              │
    ▼           ▼             ▼                 ▼                   ▼              │
  ┌───────────────────────────────────────────────────────────────────┐      ┌────────────┐
  │                        Nodo de Respaldo (Fallback)                │      │Puerta HITL │
  └───────────────────────────────────────────────────────────────────┘      │(Agudeza)   │
                                                                             └────────────┘
```

**Componentes Principales:**

| Módulo | Descripción |
|--------|-------------|
| `data_prep/` | Creador de datasets: PMC-Patients/OncoCoT → JSONL (Formato Llama 3) |
| `rag_engine/` | División semántica de PDFs de NCCN/ESMO + vectorización en ChromaDB |
| `agents/` | Orquestación multi-agente en LangGraph (Router → Ingestión → RAG Correctivo → Especialista ↔ Crítico → Puerta HITL → Formateo) |
| `ui/` | Interfaz Gradio para ingreso de notas clínicas, citas de fuentes y salida de razonamiento |

---

## ⚡ Objetivo de Hardware

- **GPU:** AMD Instinct™ MI300X (192GB HBM3)
- **Pila de Software:** ROCm 7.2.x, PyTorch (HIP), vLLM con PagedAttention
- **Modelos:** `Qwen/Qwen3.5-9B` (Triaje Rápido) y `Qwen/Qwen3.6-27B-Instruct` (Razonamiento Profundo) (QLoRA 4-bit vía bitsandbytes)

---

## 🚀 Inicio Rápido

```bash
# 1. Clonar y configurar
git clone <repo-url>
cd OncoAgent

# 2. Instalar dependencias
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Iniciar Servidor de Inferencia (vLLM en Docker)
# Esto levanta los modelos Qwen optimizados para AMD MI300X vía ROCm PagedAttention
docker run --device /dev/kfd --device /dev/dri -p 8000:8000 rocm/vllm:latest \
    --model Qwen/Qwen3.6-27B-Instruct --tensor-parallel-size 1

# 4. Configurar entorno y ejecutar interfaz
cp .env.example .env
# Configurar VLLM_API_BASE=http://localhost:8000/v1 en .env
python -m ui.app
```

---

## 📁 Estructura del Proyecto

```
├── docs/                   # Documentación e investigación
│   ├── research/           # Documentos de análisis de investigación profunda
│   ├── ADR/                # Registros de Decisiones Arquitectónicas (ADRs)
│   ├── oncoagent_master_directive.md
│   └── antigravity_rules.md
├── data_prep/              # Preparación de conjuntos de datos (Fase 0)
├── rag_engine/             # Ingestión y recuperación de RAG (Fase 0-3)
├── agents/                 # Orquestación LangGraph (Fase 3)
├── ui/                     # Frontend en Gradio (Fase 4)
├── tests/                  # Pruebas unitarias e integración
├── scripts/                # Scripts de utilidad
├── logs/                   # Bitácora (Paper log) y de redes sociales
├── requirements.txt        # Dependencias fijadas
└── Dockerfile              # Despliegue en HF Spaces
```

---

## 🩺 Garantías de Seguridad

- **Bucle Crítico basado en Reflexion:** Un nodo de seguridad dedicado audita la salida del Especialista contra el contexto RAG (verificación de implicación). Obliga al Especialista a regenerar su salida si detecta afirmaciones sin fundamento o dosis inventadas.
- **Puerta de Aprobación Humana (HITL):** Un punto de control basado en la agudeza clínica que detiene el flujo para la aprobación de un médico humano en casos de alto riesgo (ej. Estadio IV + mutaciones complejas).
- **RAG Correctivo:** El sistema evalúa la relevancia del contexto recuperado. Si no se encuentra evidencia suficiente, se activa un respaldo seguro en lugar de intentar adivinar.
- **Cero-PHI (Cero Información Médica Privada):** Redacción de PII basada en expresiones regulares antes de cualquier procesamiento.
- **Reproducibilidad:** Semillas fijas (`torch.manual_seed(42)`) en todos los scripts de ML.

---

## 📄 Licencia

Este proyecto fue construido para el AMD Developer Hackathon 2026.

---

## 👥 Equipo

Construido con ❤️ y AMD Instinct MI300X.
