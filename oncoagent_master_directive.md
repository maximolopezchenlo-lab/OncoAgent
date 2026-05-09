DIRECTIVA PRINCIPAL DE EJECUCIÓN: ONCOAGENT

Proyecto: OncoAgent - Sistema Multi-Agente para Triaje Oncológico
Hardware Target: AMD Instinct™ MI300X (Entorno ROCm 7.2)
Frameworks Base: LangGraph, vLLM, PyTorch (optimum-amd), PEFT

1. Contexto y Misión para Antigravity

Antigravity, tu misión como Ingeniero de Software Principal es ejecutar el desarrollo del proyecto "OncoAgent" para el AMD Developer Hackathon. El objetivo es construir un sistema de triaje oncológico que solucione la "ceguera de datos no estructurados" en atención primaria.

2. Organización del Conocimiento (Estructura de Planos)

Para evitar la saturación de contexto y duplicidad, utilizaremos una estructura de planos:

**Plano de Datos (Fuentes de Evidencia):**
- **Notebook 1 (Clinical Evidence):** Casos clínicos, síntomas y diagnósticos reales.
- **Notebook 2 (Clinical Guidelines):** Guías NCCN/ESMO. Fuente principal para el RAG.
- **Notebook 3 (Market Data):** Benchmarks y soluciones actuales.
- **Notebook 4 (Strategic Vision):** Documentación del hackathon y visión a largo plazo.

**Plano de Control (Cerebro Estratégico):**
- **Documentos MD (Deep Research):** Sintetizan la información de los Notebooks en decisiones técnicas y estratégicas.
- **OncoAgent Master Directive:** Este archivo. Orquestador de la ejecución.
- **Notebook Maestro:** Centraliza los logs y ADRs para consulta rápida por el agente.

**Regla de Oro de Relación:** Los documentos MD **no deben repetir** datos crudos de los Notebooks. Deben **decidir** qué hacer con esos datos (ej. "Basado en la Guía NCCN del Notebook 2, implementaremos el chunking semántico en la Fase 0").

3. Roadmap de Desarrollo (Fases)

Fase 0: Preparación de Datos (Data Prep)
Objetivo: Transformar guías PDF y datasets crudos en conocimiento estructurado.
- Script rag_ingestion.py: Extracción semántica con PyMuPDF.
- Script dataset_builder.py: Conversión de PMC-Patients/OncoCoT a JSONL (Llama 3 template).

Fase 1: Validación de Infraestructura (AMD/ROCm)
Objetivo: Asegurar que el entorno MI300X esté listo (ROCm 7.2).
- Comandos de diagnóstico (amdsmi, rocm-smi).
- Validación de vLLM con PagedAttention.

Fase 2: Fine-Tuning de Especialista (SFT/QLoRA)
Objetivo: Adaptar Qwen 2.5 7B/32B a la lógica OncoCoT.
- Uso de QLoRA 4-bit (bitsandbytes-rocm).
- Entrenamiento con checkpoints intermedios.

Fase 3: Orquestación de Agentes (LangGraph)
Objetivo: Definir el flujo de razonamiento (CRAG, Reflexion).
- Nodo Router: Limpieza de PHI y clasificación inicial.
- Nodo RAG: Recuperación de guías médicas basadas en síntomas.
- Nodo Especialista: Análisis clínico y generación de OncoCoT.

Fase 4: Interfaz de Usuario y Empaquetado
Objetivo: Desplegar en Hugging Face Spaces con Docker (rocm/vllm). UI en Gradio 6.

4. Reglas de Engagement

- Prioridad AMD: Todo código debe ser compatible con ROCm 7.2. Prohibido usar librerías exclusivas de CUDA.
- Logging Estricto: Mantener paper_log.md y social_media_log.txt (y versiones .es) al día.
- Seguridad PHI: Cero exposición de datos privados.
- Anti-Alucinación: Basar respuestas estrictamente en el RAG.
- Rigor Diagnóstico: Prohibido recomendar tratamientos oncológicos (cirugía, quimio, radio) si no existe confirmación histológica/biopsia en el input. Priorizar siempre la obtención del diagnóstico definitivo.

Antigravity, analiza este documento y confírmame que has integrado esta directiva en tu memoria operativa. Procederemos con la Fase 0.
