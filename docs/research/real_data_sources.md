# Fuentes de Datos Reales en Oncología (Open & Registered Access)

Para construir un sistema OncoAgent robusto y libre de alucinaciones, necesitamos datos del mundo real. A continuación, presento la lista más exhaustiva de fuentes de datos oncológicos categorizadas por su utilidad para nuestro pipeline (Fine-Tuning vs. RAG) y su nivel de accesibilidad.

## 1. Datasets de NLP y Resúmenes Clínicos (Ideal para Fine-Tuning)

Estos datasets contienen texto libre clínico, ideal para entrenar a Llama 3.1 en razonamiento oncológico y extracción de entidades.

*   **PMC-Patients V2 (HuggingFace / GitHub)**
    *   **Volumen:** ~250,000 resúmenes de pacientes reales.
    *   **Origen:** Extraídos de reportes de casos médicos en *PubMed Central*.
    *   **Acceso:** 🟢 **Abierto** (HuggingFace Hub).
    *   **Uso en OncoAgent:** Fundamental para generar el formato JSONL de instrucción y entrenar la lógica de "Patient-to-Article" (conectar un paciente con literatura).
*   **PubMedQA / MedQA / MedMCQA (HuggingFace)**
    *   **Volumen:** Cientos de miles de pares de Pregunta/Respuesta biomédica.
    *   **Origen:** Exámenes médicos reales (USMLE) y abstracts de PubMed con respuestas de expertos.
    *   **Acceso:** 🟢 **Abierto** (HuggingFace Hub).
    *   **Uso en OncoAgent:** Validación de razonamiento y fine-tuning de QA clínico.

## 2. Bases de Conocimiento Clínico (Ideal para RAG Engine)

Documentos autoritativos que sirven como fuente de verdad para el sistema de recuperación vectorial.

*   **ESMO Clinical Practice Guidelines**
    *   **Origen:** *European Society for Medical Oncology*, publicados en *Annals of Oncology*.
    *   **Formato:** PDFs de alta calidad (Living Guidelines).
    *   **Acceso:** 🟢 **Abierto** (Free/Open Access directamente en su web).
    *   **Uso en OncoAgent:** Fuente primaria de verdad para el RAG sin fricción de autenticación.
*   **NCCN Clinical Practice Guidelines in Oncology**
    *   **Origen:** *National Comprehensive Cancer Network*.
    *   **Formato:** PDFs detallados estructurados en algoritmos.
    *   **Acceso:** 🟡 **Registro Gratuito Requerido**. Los PDFs deben descargarse manualmente tras iniciar sesión.
    *   **Uso en OncoAgent:** Estándar de oro en EE.UU. Requiere recolección manual previa.

## 3. Registros de Historias Clínicas Electrónicas (EHR / EMR)

Datos crudos de hospitales, ideales para pruebas de estrés de triaje con ruido real (laboratorios, notas de evolución).

*   **MIMIC-IV (PhysioNet)**
    *   **Volumen:** Cientos de miles de admisiones hospitalarias (Beth Israel Deaconess Medical Center). Contiene un subconjunto masivo de pacientes oncológicos con notas clínicas de texto libre, patología y radiología.
    *   **Acceso:** 🔴 **Controlado**. Requiere firmar un *Data Use Agreement (DUA)* y completar el curso de ética CITI.
    *   **Uso en OncoAgent:** La mejor fuente de datos de historias clínicas crudas si logras la acreditación.
*   **Project Data Sphere**
    *   **Volumen:** Datos a nivel de paciente de ensayos clínicos oncológicos históricos donados por farmacéuticas (Sanofi, Pfizer, etc.).
    *   **Acceso:** 🟡 **Registro Requerido**. Abierto a investigadores tras registro básico.
    *   **Uso en OncoAgent:** Excelente para evaluar líneas de tratamiento y toxicidad real.

## 4. Datos Genómicos y Patología (Multimodal)

Si el OncoAgent se expande a analizar perfiles moleculares para terapias dirigidas (Targeted Therapy).

*   **TCGA (The Cancer Genome Atlas) / Genomic Data Commons (GDC)**
    *   **Volumen:** +11,000 pacientes (33 tipos de cáncer).
    *   **Origen:** NIH / NCI.
    *   **Acceso:** 🟢 **Abierto** para datos clínicos y mutaciones simples; 🔴 **Controlado** para genómica cruda.
    *   **Uso en OncoAgent:** Cruce de perfiles moleculares (ej. EGFR, ALK) con guías clínicas.
*   **AACR Project GENIE**
    *   **Volumen:** +130,000 pacientes.
    *   **Origen:** Consorcio internacional. Relaciona secuenciación clínica con resultados del mundo real.
    *   **Acceso:** 🟢 **Abierto** a la comunidad investigadora mediante releases periódicos.

---

> [!TIP]
> **Estrategia para el Hackathon (Viabilidad vs. Tiempo):**
> Dado el límite de tiempo, la mejor relación esfuerzo-beneficio es:
> 1. Descargar **ESMO Guidelines** (sin fricción) para llenar ChromaDB.
> 2. Descargar **PMC-Patients V2** vía el SDK de HuggingFace para los casos de prueba de triaje.
> *(Esto nos da 100% de realidad clínica en 10 minutos de procesamiento, sin esperar certificaciones éticas como las de MIMIC-IV).*
