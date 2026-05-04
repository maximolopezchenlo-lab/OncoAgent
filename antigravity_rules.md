# Antigravity Rules: OncoAgent Development Standards v2.0

Este documento centraliza las reglas de oro para el desarrollo de OncoAgent en hardware AMD MI300X.

---

## 📝 BLOQUE 1: LOGGING, DOCUMENTACIÓN Y MARKETING (PRIORIDAD ALTA)

### 1. Academic Paper Logging (`paper_log.md`)
Por cada hito técnico, módulo o bug crítico resuelto, redactar una entrada en tono académico.

**Formato requerido:** `[Problema/Hipótesis]` → `[Justificación Arquitectónica]` → `[Implementación Matemática/Lógica]` → `[Métricas de Rendimiento]`.

**Objetivo:** Este archivo debe poder copiarse y pegarse casi directamente para formar las secciones de Metodología y Resultados del Whitepaper del proyecto.

### 2. Social Media "Build in Public" Logging (`social_media_log.txt`)
Actuar como un Social Media Manager técnico. Al final de cada sesión, generar **2 posts** (uno formato "Hilo de X/Twitter" y otro para "LinkedIn").

**Qué registrar para el usuario:**
- **Métricas "Sexys":** Velocidad de inferencia (tokens/s) de vLLM, cómo el Loss bajó durante el fine-tuning con QLoRA, o el tamaño de la base de datos ChromaDB.
- **El "Fracaso del Día":** Registrar un bug o error de hardware/librería crítico que nos haya detenido. Explicar por qué falló y cómo se superó. Esto humaniza el proceso y genera engagement orgánico.
- **Sugerencia de Imágenes (Prompts visuales):** Indicar qué capturar. Ej: "Toma un screenshot de la terminal con el error de bitsandbytes y otro con la solución", o "Graba un video corto del log de vLLM".
- **Tono:** Entusiasta, técnico pero accesible, usando viñetas.
- **Hashtags obligatorios:** `#AMDHackathon` `#HealthTech` `#ROCm` `#MI300X` `#LangGraph` `#Llama31`

### 3. Architectural Decision Records (ADR)
Nunca cambiar un framework principal sin documentarlo. Si se cambia ChromaDB por FAISS, o PyMuPDF por otra cosa, crear un mini-registro en `/docs/ADR` explicando el **"Por qué"** técnico.

---

## ⚙️ BLOQUE 2: ECOSISTEMA AMD Y HARDWARE (ROCm)

### 4. AMD First, No CUDA
Asumir siempre hardware **AMD Instinct MI300X**. Reemplazar mentalmente `nvcc` por `hipcc`. **NUNCA** sugerir instalar paquetes exclusivos de NVIDIA o comandos como `nvidia-smi` (usar `rocm-smi`).

### 5. PyTorch Device Translation
En PyTorch, `device="cuda"` funciona para AMD porque ROCm lo traduce a HIP bajo el capó. Usarlo sin miedo, pero evitar librerías de terceros que dependan de binarios de NVIDIA.

### 6. Aceleración vLLM
Configurar el motor vLLM aprovechando **PagedAttention**. Optimizar los parámetros de concurrencia sabiendo que tenemos **192GB de HBM3** en la MI300X.

### 7. QLoRA y Cuantización
Para el Fine-Tuning, usar estrictamente la versión de `bitsandbytes` **compilada para ROCm**. Usar el tipo de dato **NormalFloat4 (nf4)** para los pesos base, y `float16` o `bfloat16` para el cómputo.

### 8. Contenedores Nativos
Asumir que el código correrá en la imagen Docker oficial `rocm/vllm`. No intentar compilar desde cero a menos que sea estrictamente necesario.

---

## 🧠 BLOQUE 3: MODELOS Y FINE-TUNING

### 9. Inmutabilidad del Modelo Base
El modelo a usar es **EXCLUSIVAMENTE** `meta-llama/Meta-Llama-3.1-8B-Instruct`. No sugerir otros modelos.

### 10. Formato Estricto JSONL
Los scripts de preparación de datos deben exportar a `.jsonl`. Deben inyectar los roles (`system`, `user`, `assistant`) respetando **EXACTAMENTE** la sintaxis de chat template de Llama 3.1.

### 11. Determinismo y Reproducibilidad
Fijar las semillas aleatorias (`torch.manual_seed(42)`, `random.seed(42)`) en **todos** los scripts de Machine Learning para garantizar resultados consistentes.

### 12. Tolerancia a Fallos (Checkpoints)
El script de entrenamiento PEFT/LoRA debe guardar checkpoints de los adaptadores cada X steps. Si la nube se reinicia, no debemos perder el progreso.

---

## 📚 BLOQUE 4: PROCESAMIENTO DE DATOS Y RAG (EL CEREBRO)

### 13. Extracción de PDF
Usar estrictamente la librería `PyMuPDF` (`fitz`) para leer las guías NCCN/ESMO. Está **prohibido** usar OCR (Tesseract) ya que los documentos son nacidos digitales.

### 14. Adaptive Semantic Chunking
**Prohibido** usar `RecursiveCharacterTextSplitter` con cortes arbitrarios (ej. 500 chars). Implementar lógica que corte por encabezados ("Recomendación:", "Evidencia:") para no destruir el contexto médico.

### 15. Base de Datos Vectorial
Usar **ChromaDB** en memoria local (`./chroma_db`). No integrar bases de datos Cloud que requieran keys o setups complejos.

### 16. Embeddings Especializados
Para vectorizar, usar modelos de la familia **BioBERT** o **ClinicalBERT** desde HuggingFace, no usar embeddings generalistas como los de OpenAI.

---

## 🕸️ BLOQUE 5: ORQUESTACIÓN MULTI-AGENTE (LANGGRAPH)

### 17. Exclusividad de Framework
Toda la lógica multi-agente se hará con **LangGraph**. Prohibido sugerir CrewAI o AutoGen.

### 18. Definición de Estado (State)
Usar `TypedDict` de Python para definir el estado del grafo de manera robusta.

### 19. Límite de Recursión
Establecer siempre un `recursion_limit` (ej. 5 o 10) al compilar el grafo para evitar que el Enrutador y el Especialista entren en bucles infinitos discutiendo un diagnóstico.

### 20. Handoff Estructurado
El Nodo Enrutador debe forzarse a devolver un **JSON validado** (ej. `{"route": "oncology"}`) para que los Conditional Edges (Bordes Condicionales) dirijan el flujo sin fallos de parseo.

### 21. Preservación del Input
El flujo de estado **NUNCA** debe sobrescribir la nota clínica original del paciente. Las observaciones de los agentes se añaden a nuevas variables en el estado.

---

## 🐍 BLOQUE 6: ESTÁNDARES DE CÓDIGO PYTHON

### 22. Type Hinting Obligatorio
Todas las funciones deben tener tipado estricto: `def process(text: str) -> Dict[str, Any]:`.

### 23. Arquitectura Modular
Nada de scripts de 1000 líneas. Dividir en `/data`, `/rag`, `/agents`, `/ui`.

### 24. Manejo de Secretos
Usar `python-dotenv`. Los tokens de HuggingFace (`HF_TOKEN`) se leen de variables de entorno. **Prohibido** hardcodear llaves en el código.

### 25. Degradación Elegante (Graceful Degradation)
Usar bloques `try/except` en llamadas a modelos o base de datos. Si ChromaDB falla, el Agente debe saber responder "Error al consultar guías" en lugar de crashear la app.

### 26. Docstrings Claros
Añadir descripciones cortas a las clases y funciones principales para mantener el código legible.

---

## 🩺 BLOQUE 7: SEGURIDAD CLÍNICA

### 27. Política Anti-Alucinación
En el System Prompt del Agente Especialista, incluir la regla estricta: *"Si la información no se encuentra en el contexto provisto, responde 'Evidencia insuficiente para emitir recomendación'. No inventes tratamientos."*

### 28. Zero-PHI (Protección de Datos)
Asegurar que el código elimine identificadores obvios (Nombres reales, Fechas de nacimiento reales) de los logs y prompts mediante regex o sustitución simple antes de procesar.

---

## 🚀 BLOQUE 8: FRONTEND Y DESPLIEGUE

### 29. Interfaz Minimalista
Usar **Gradio** o **Streamlit** para la UI. Debe tener dos columnas: Izquierda (Input de Historia Clínica) y Derecha (Log de razonamiento de los Agentes y conclusión).

### 30. Preparación para HF Spaces
Mantener el `requirements.txt` pulcro, con las versiones exactas ancladas (`paquete==1.2.3`). El proyecto debe ser empaquetable en un Dockerfile simple listo para subir a la organización del hackathon en Hugging Face.
