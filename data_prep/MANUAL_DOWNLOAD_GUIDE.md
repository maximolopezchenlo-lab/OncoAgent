# Guía de Descarga Manual de Datos Clínicos Restringidos

Para asegurar la máxima calidad médica en OncoAgent, necesitamos ciertos datos que requieren registro manual por motivos de copyright o privacidad. Sigue estos pasos para descargar los datos fundacionales:

## Prioridad 1: Guías NCCN (NCCN Clinical Practice Guidelines in Oncology)
*Es el "Gold Standard" en EE.UU. Su inclusión hace que el RAG sea inmensamente valioso.*

**Paso a paso:**
1. Ve a **[NCCN.org](https://www.nccn.org/login)** y haz clic en "Register".
2. Completa el registro gratuito (puedes elegir el perfil de estudiante/investigador si te lo preguntan).
3. Una vez iniciada la sesión, ve a la sección **"Guidelines" -> "Treatment by Cancer Type"**.
4. Descarga los PDFs de los tipos de cáncer más críticos para nuestro MVP. Sugiero fuertemente:
   - **Non-Small Cell Lung Cancer (NSCLC)**
   - **Breast Cancer**
   - **Colon Cancer**
5. **Dónde guardar:** Mueve todos los PDFs descargados a la carpeta del proyecto:
   `data/clinical_guides/nccn/`
   *(Si la carpeta no existe, créala).*

---

## Prioridad 2 (Opcional pero Recomendada): Project Data Sphere
*Datos de ensayos clínicos reales. Excelente para probar el razonamiento sobre toxicidad y líneas previas de tratamiento.*

**Paso a paso:**
1. Ve a **[ProjectDataSphere.org](https://www.projectdatasphere.org/)** y haz clic en "Register" o "Access Data".
2. Completa el registro como investigador. Generalmente aprueban rápido ya que los datos están desidentificados.
3. Busca datasets de ensayos de Fase III en cáncer de pulmón o mama.
4. Descarga los archivos CSV de datos de pacientes (Patient-level data).
5. **Dónde guardar:** Crea la carpeta y guárdalos en:
   `data/samples/clinical_trials/`

---

## Prioridad 3 (Para el futuro): MIMIC-IV (PhysioNet)
*Notas clínicas crudas. El proceso de acceso toma días, por lo que te recomiendo iniciarlo ahora pero no bloquear el hackathon por esto.*

**Paso a paso:**
1. Ve a **[PhysioNet (MIMIC-IV)](https://physionet.org/content/mimiciv/2.2/)**.
2. Regístrate en PhysioNet.
3. Completa el curso obligatorio de ética en investigación con sujetos humanos (**CITI Program** - toma un par de horas).
4. Firma el *Data Use Agreement (DUA)* online.
5. Una vez aprobado, podrás descargar los archivos masivos en CSV (especialmente la tabla `noteevents` o similares en MIMIC-IV-Note).
6. **Dónde guardar:**
   `data/samples/mimic_iv/`

---

### Siguiente paso para el agente:
Una vez que me confirmes que has colocado los PDFs de NCCN en `data/clinical_guides/nccn/` (o si decides saltarlo por ahora), me encargaré de descargar automáticamente mediante scripts:
- Guías ESMO (Open Access)
- Dataset PMC-Patients V2 (HuggingFace)
- PubMedQA (HuggingFace)
