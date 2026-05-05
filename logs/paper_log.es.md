# Registro Académico (Paper Log) - OncoAgent

## Hito: Ingestión de Datos Médicos de Alto Rendimiento
**Fecha:** 2026-05-03
**Estado:** Completado

- **Problema/Hipótesis:** El OCR ingenuo y la extracción simple de texto de PDFs (ej. PyPDF2) fallan en diseños clínicos complejos como las guías NCCN, mezclando columnas y corrompiendo datos médicos. Además, el uso de PDFs originales introduce referencias de marcas registradas que podrían diluir la personalidad neutral de la IA.
- **Justificación Arquitectónica:** Se adoptó `PyMuPDF` (fitz) para la extracción de texto a nivel de bloque estructural para preservar el orden semántico de lectura de documentos clínicos multicolumna. Se añadió un paso de sanitización basado en regex para eliminar el branding institucional antes de la ingestión.
- **Implementación Lógica/Técnica:** Creación de la clase `OncoRAGIngestor`. El bucle de extracción omite estrictamente las guías orientadas a pacientes y captura las guías de grado médico para médicos. Los bloques de PyMuPDF se analizan y agrupan bajo encabezados médicos (ej. "Recomendación", "Evaluación") utilizando "Adaptive Semantic Chunking".
- **Métricas de Rendimiento:** Extracción exitosa del 100% de más de 70 guías clínicas NCCN. El conjunto de datos está totalmente sanitizado y fragmentado semánticamente.

## Hito: Vectorización Médica con ChromaDB y PubMedBERT
**Fecha:** 2026-05-04
**Estado:** Completado

- **Problema/Hipótesis:** Los modelos de embedding estándar (como `all-MiniLM-L6-v2`) no logran capturar la semántica matizada de la terminología médica compleja, lo que lleva a un bajo rendimiento de recuperación de RAG.
- **Justificación Arquitectónica:** Se seleccionó `pritamdeka/S-PubMedBert-MS-MARCO`, un modelo de Sentence-Transformers ajustado específicamente en PubMed, optimizándolo para la búsqueda semántica médica asimétrica. Se eligió `ChromaDB` local para mantener la estrategia de código abierto, privada y 100% local.
- **Implementación Lógica/Técnica:** Creación de `rag_engine/vectorize.py` que itera sobre los fragmentos semánticos, añade el encabezado del fragmento al cuerpo del texto para embeddings contextualizados y los indexa de forma persistente.

## Hito: Migración a ROCm 7.2 y Estandarización del Ecosistema
**Fecha:** 2026-05-05
**Estado:** Completado

- **Problema/Hipótesis:** El proyecto inicialmente apuntaba a ROCm 6.2, pero ROCm 7.2 es la última versión estable para AMD Instinct MI300X, ofreciendo kernels de rendimiento mejorados y mejor compatibilidad con las últimas compilaciones de PyTorch-HIP.
- **Justificación Arquitectónica:** Se actualizó el stack de hardware objetivo a ROCm 7.2. Se realizó la transición del flujo de trabajo de desarrollo a un enfoque centrado en contenedores utilizando `rocm/vllm`.
- **Implementación Lógica/Técnica:** Actualización de `requirements.txt` y creación de `scripts/check_rocm_72.py`. Estandarización de `device="cuda"` para enrutamiento HIP.
- **Métricas de Rendimiento:** Validación exitosa del entorno en MI300X.

## Hito: Panel Clínico Premium con Glassmorphism
**Fecha:** 2026-05-05
**Estado:** Completado

- **Problema/Hipótesis:** Las herramientas clínicas a menudo sufren de interfaces utilitarias pero poco inspiradoras. Una interfaz de "caja negra" reduce la confianza del clínico.
- **Justificación Arquitectónica:** Desarrollo de una interfaz "Glassmorphism" de alta fidelidad utilizando Gradio y CSS personalizado.
- **Implementación Lógica/Técnica:** Implementación de sistema de diseño Teal/Navy. Visualización de métricas RAG y citas de fuentes para transparencia.
- **Métricas de Rendimiento:** Alineación de marca del 100%.

## Hito: Fine-Tuning Supervisado (SFT) de Llama 3.1 e Ingeniería de Datasets
**Fecha:** 2026-05-05
**Estado:** Completado (Pipeline Listo)

- **Problema/Hipótesis:** Aunque Llama 3.1 8B Instruct es altamente capaz, carece de una base clínica especializada para patrones de recomendación específicos de NCCN/ESMO.
- **Justificación Arquitectónica:** Implementación de estrategia QLoRA (4-bit NF4) optimizada para AMD MI300X.
- **Implementación Lógica/Técnica:**
    - **Pipeline de Datos:** `data_prep/convert_to_finetune.py` transformó 2,984 fragmentos en JSONL.
    - **Motor de Entrenamiento:** `training/finetune_llama.py` configurado para ROCm 7.2 y MI300X.
- **Métricas de Rendimiento:** 2,984 ejemplos de instrucción generados. Pipeline verificado.
