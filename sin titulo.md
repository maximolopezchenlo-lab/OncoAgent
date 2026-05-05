DIRECTIVA PRINCIPAL DE EJECUCIÓN: ONCOAGENT

Proyecto: OncoAgent - Sistema Multi-Agente para Triaje Oncológico
Hardware Target: AMD Instinct™ MI300X (Entorno ROCm 6.2.x)
Frameworks Base: LangGraph, vLLM, PyTorch (optimum-amd), PEFT

1. Contexto y Misión para Antigravity

Antigravity, tu misión como Ingeniero de Software Principal es ejecutar el desarrollo del proyecto "OncoAgent" para el AMD Developer Hackathon. El objetivo es construir un sistema de triaje oncológico que solucione la "ceguera de datos no estructurados" en atención primaria.

📄 Fundamentación Estratégica: Toda la justificación clínica y de negocio de este proyecto se basa en los reportes de investigación de NotebookLM: "Deep Research problematica-dolor a resolver.md" y "Deep Research soluciones existentes a la problemática.md".

Deberás construir el proyecto respetando estrictamente las 30 reglas definidas en antigravity_rules.md, priorizando en todo momento la compatibilidad con el ecosistema AMD (ROCm), la estabilidad del código y el registro meticuloso para la redacción del Whitepaper (paper_log.md) y el contenido de redes (social_media_log.txt).

2. Topología del Sistema (Lo que vamos a construir)

El sistema se compone de tres pilares que deberás desarrollar de forma modular:

Pilar A: El Motor RAG (Base de Conocimiento)

Fuentes: Guías de práctica clínica (NCCN/ESMO) en formato PDF.

Procesamiento: Usarás PyMuPDF (fitz) para extraer el texto. Implementarás una lógica de particionamiento inteligente (Adaptive Semantic Chunking) que respete la jerarquía médica.

Almacenamiento: Vectorización con BioBERT (o equivalente médico open-source) y almacenamiento local en ChromaDB.

Pilar B: El Modelo Especialista (Fine-Tuning / Track 2)

Modelo Base: meta-llama/Meta-Llama-3.1-8B-Instruct.

Técnica: QLoRA a 4-bits (NormalFloat4) vía bitsandbytes y PEFT.

Datos de Entrenamiento: Unificación de PMC-Patients y OncoCoT en un archivo .jsonl para enseñar al modelo a razonar de forma temporal-causal.

Pilar C: Orquestación Multi-Agente (LangGraph / Track 1)

Estado (State): Un TypedDict que transporte la historia_clinica cruda, la especialidad decidida, el contexto_rag y la justificacion final.

Nodos: Router (Triaje zero-shot), RAG (Recuperación), Especialista (Evaluación de riesgo).

3. Plan de Ejecución (Roadmap de Desarrollo y Enlaces a Research)

Antigravity, deberás planificar tu ejecución siguiendo estrictamente este orden.

Fase 0: Preparación de Datos (Local/CPU)

Objetivo: Crear los cimientos de datos (RAG y Fine-Tuning) sin gastar cómputo GPU en la nube.

📄 Documento Base: Referenciar el reporte de NotebookLM: "Strategic Framework for Oncological Intelligence: Data Acquisition and Curation for the OncoAgent Triage System".

Script 1 (rag_ingestion.py): * Detalle Técnico: No usarás OCR. Usa PyMuPDF para leer el texto crudo. El "Adaptive Semantic Chunking" debe identificar palabras clave como "Recomendación" y "Nivel de evidencia" para no cortar el texto por la mitad de un tratamiento vital. Vectoriza los chunks usando un modelo de embeddings ligero de HuggingFace y persiste la base en una carpeta local ./chroma_db.

Script 2 (dataset_builder.py): * Detalle Técnico: Este script descarga o procesa localmente los casos médicos de PMC-Patients y OncoCoT. El entregable crítico es un archivo train_oncoagent.jsonl. Cada línea del JSONL debe respetar el chat template de Llama 3 (<|start_header_id|>system<|end_header_id|>...), donde el sistema define al médico, el usuario da los síntomas desordenados, y el asistente responde con el razonamiento cronológico y el diagnóstico.

Fase 1: Setup de Infraestructura AMD

Objetivo: Validar el entorno MI300X y el stack ROCm 6.2.x para asegurar que no haya cuellos de botella de hardware.

📄 Documento Base: Referenciar el reporte de NotebookLM: "Technical Design Document for OncoAgent: A Multi-Agent System for Early Oncology Detection on AMD Instinct MI300X Infrastructure".

Script 3 (test_rocm_vllm.py): * Detalle Técnico: Un smoke test de inferencia. Debe importar vllm, instanciar el modelo Llama-3.1-8B-Instruct Base en la GPU MI300X (device="cuda") y ejecutar un prompt médico básico. El script debe registrar en consola la latencia de respuesta y confirmar explícitamente que no se están produciendo fallas de memoria (memory access faults) o caídas a CPU.

Fase 2: Fine-Tuning QLoRA (El "Quirófano")

Objetivo: Adaptar el modelo generalista para el razonamiento oncológico experto.

📄 Documento Base: Referenciar el reporte de NotebookLM: "Technical Design Document for OncoAgent: A Multi-Agent System for Early Oncology Detection on AMD Instinct MI300X Infrastructure".

Script 4 (train_specialist.py): * Detalle Técnico: Implementación de Supervised Fine-Tuning (SFT) usando la librería transformers.

Parámetros estrictos: Carga el modelo en 4-bits (BitsAndBytesConfig con NormalFloat4). Configura los adaptadores LoRA (apuntando a los módulos de atención q_proj, v_proj).

Training Arguments: Usa un learning rate muy bajo (ej. 2e-4 o 1e-4) para evitar el olvido catastrófico de la jerga médica general. Activa gradient_checkpointing si es necesario y configura la frecuencia de guardado de checkpoints en la carpeta ./models/oncoagent_adapters.

Fase 3: Orquestación LangGraph (El "Cerebro")

Objetivo: Construir el grafo de decisión y conectar la memoria a largo plazo.

📄 Documento Base: Referenciar el reporte de NotebookLM: "Technical Design Document for OncoAgent: A Multi-Agent System for Early Oncology Detection on AMD Instinct MI300X Infrastructure".

Script 5 (agents/state.py): * Detalle Técnico: Declarar el TypedDict. Las claves mínimas son: clinical_note (str), triage_route (str), retrieved_guidelines (list), expert_analysis (str).

Script 6 (agents/workflow.py): * Detalle Técnico: Es el núcleo lógico.

Nodo Router: Usa el modelo Llama base. Le pasamos el clinical_note. Su prompt debe forzar un output JSON estricto ({"route": "oncology"} o {"route": "standard"}).

Conditional Edge: Si route == "oncology", ir al Nodo RAG. Si no, fin del proceso.

Nodo RAG: Toma el clinical_note, extrae entidades clave, busca en ChromaDB y actualiza la clave retrieved_guidelines.

Nodo Especialista: Usa el modelo fine-tuneado (vLLM apuntando a los adaptadores LoRA). Ingiere clinical_note + retrieved_guidelines y devuelve el OncoCoT (el análisis cronológico).

Fase 4: Interfaz de Usuario y Empaquetado

Objetivo: Desplegar el sistema para la evaluación de los jueces en Hugging Face Spaces.

📄 Documento Base: Referenciar el reporte de NotebookLM: "Technical Design Document for OncoAgent: A Multi-Agent System for Early Oncology Detection on AMD Instinct MI300X Infrastructure".

Script 7 (app.py): * Detalle Técnico: Un dashboard en Gradio o Streamlit. Debe mostrar a la izquierda el input de la nota clínica, y a la derecha una interfaz tipo chat o registro paso a paso donde se vea: "Router analizando...", "Buscando guías ESMO...", "Análisis Especialista: Alto Riesgo".

Script 8 (Dockerfile): * Detalle Técnico: El contenedor. Usa como base rocm/vllm para garantizar aceleración de hardware. Instala las dependencias de requirements.txt (incluyendo LangGraph, Gradio/Streamlit, PyMuPDF). Expone el puerto 7860 (estándar para Gradio en HF Spaces) y define el ENTRYPOINT para ejecutar app.py.

4. Protocolo de Inicio para Antigravity

Al recibir este documento y comenzar a trabajar, Antigravity debe:

Confirmar la lectura y comprensión de esta Directiva y de las reglas en antigravity_rules.md.

Reconocer los documentos de investigación (Deep Research y TDD) que respaldan las fases.

Preguntar al usuario: "¿Procedemos a crear los scripts de la Fase 0 (Preparación de Datos) en Python?"

Iniciar el registro en paper_log.md con la entrada inicial de diseño arquitectónico.