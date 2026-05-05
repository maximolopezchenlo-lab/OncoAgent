# 🧬 OncoAgent — Sistema Multi-Agente de Triaje Oncológico

> **AMD Developer Hackathon 2026** · Potenciado por AMD Instinct™ MI300X · ROCm 7.2

## 🌍 100% Código Abierto: Democratizando la Oncología
OncoAgent es orgullosamente 100% de código abierto. Creemos que la inteligencia clínica que salva vidas no debe estar bloqueada tras APIs propietarias. Nuestra solución está diseñada para:
- **Garantizar la Privacidad del Paciente:** Ejecutándose localmente en hardware AMD MI300X o nubes privadas, asegurando que ningún dato del paciente salga del hospital (Zero-PHI).
- **Fomentar la Contribución Global:** Permitiendo a las comunidades médicas de todo el mundo auditar, modificar y contribuir fácilmente a la base de conocimientos RAG.

OncoAgent es un sistema de triaje clínico multi-agente diseñado para combatir la **ceguera de datos no estructurados** en oncología de atención primaria. Aprovecha un modelo Llama 3.1 8B ajustado (fine-tuned) y orquestado mediante LangGraph para proporcionar razonamiento oncológico basado en evidencia, fundamentado en las guías clínicas de NCCN/ESMO.

---

## 🏗️ Arquitectura

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Enrutador  │───▶│ Motor RAG    │───▶│ Especialista │───▶│ Validador de │
│(Limpieza PHI)│    │(ChromaDB +   │    │  Clínico     │    │  Seguridad   │
│              │    │ PubMedBERT)  │    │ (Llama 3.1)  │    │ (Anti-Aluci) │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
        │                                                           │
        └─────────────── LangGraph StateGraph ──────────────────────┘
```

**Componentes Clave:**

| Módulo | Descripción |
|--------|-------------|
| `data_prep/` | Generador de datasets: PMC-Patients/OncoCoT → JSONL |
| `rag_engine/` | Fragmentación semántica de PDFs NCCN/ESMO + Vectorización ChromaDB |
| `agents/` | Orquestación multi-agente en LangGraph (Enrutador → RAG → Especialista → Validador) |
| `ui/` | Interfaz bilingüe en Gradio para el ingreso de notas clínicas, justificación de fuentes y resultados |

---

## ⚡ Objetivo de Hardware

- **GPU:** AMD Instinct™ MI300X (192GB HBM3)
- **Software Stack:** ROCm 7.2.x, PyTorch (HIP), vLLM con PagedAttention
- **Modelo Base:** `meta-llama/Meta-Llama-3.1-8B-Instruct`
- **Inferencia:** Optimizada a través del servidor vLLM local.

---

## 🚀 Inicio Rápido (Despliegue)

### Requisitos Previos
- Instancia AMD MI300X (Ej. servidor bare-metal o nube con soporte ROCm 7.2)
- Docker y Docker Compose instalados.

### Instalación y Ejecución

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd OncoAgent

# 2. Iniciar el entorno virtual y dependencias
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Iniciar el Servidor de Inferencia vLLM (Docker)
# Esto iniciará Llama 3.1 8B optimizado para hardware AMD
docker run --device /dev/kfd --device /dev/dri -p 8000:8000 rocm/vllm:latest \
    --model meta-llama/Meta-Llama-3.1-8B-Instruct --tensor-parallel-size 1

# 4. Configurar entorno e Iniciar la Interfaz de Usuario
cp .env.example .env
# Asegúrate de configurar VLLM_API_BASE=http://localhost:8000/v1 en .env
python -m ui.app
```

---

## 🩺 Garantías de Seguridad Médica

- **Verificación Anti-Alucinaciones:** Un nodo "Validador de Seguridad" revisa obligatoriamente la salida del Especialista contra el contexto RAG recuperado. Si no hay concordancia, rechaza la respuesta.
- **Zero-PHI:** Eliminación de PII basada en Regex antes de cualquier procesamiento RAG o LLM para proteger la identidad del paciente.
- **Trazabilidad (Fuentes RAG):** La interfaz muestra las fuentes exactas de la guía médica (Página y Sección) en la recomendación final.
- **Reproducibilidad:** Semillas fijas (`torch.manual_seed(42)`) en todos los scripts de Machine Learning.

---

## 📄 Licencia

Este proyecto fue construido para el AMD Developer Hackathon 2026.
Abierto para la comunidad de salud, por la comunidad.
