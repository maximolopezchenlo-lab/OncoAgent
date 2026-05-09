# Registro del Artículo Académico OncoAgent

## [08-05-2026] Validación de Sistema de Extremo a Extremo (Qwen Base)

**Problema:** Verificar la orquestación multi-agente completa y el pipeline RAG sin interrumpir el entrenamiento SFT en curso en la MI300X.
**Decisión Arquitectónica:** Implementación de una estrategia de backend dual para inferencia de LLM. Mientras la GPU MI300X local está saturada con el entrenamiento (SFT), la inferencia para la validación E2E se delega a **Featherless.ai** mediante un cliente compatible con OpenAI en `agents/tools.py`.
**Métricas de Rendimiento:**
- **Latencia de Inferencia:** ~2.5s para Tier 1 (Qwen 2.5 7B Instruct).
- **Ejecución del Grafo:** ~45s (incluyendo la calificación intensiva de documentos CRAG para 34 fragmentos recuperados).
- **Resultado:** Se verificó con éxito que los nodos Router, CRAG, Specialist, Critic y Formatter están correctamente interconectados. El sistema identifica correctamente casos oncológicos comunes y recupera documentos relevantes del almacén de vectores ChromaDB.

---

## Hito Técnico: Refinamiento de UI/UX y Adaptación a Gradio 6
**Fecha:** 2026-05-08
**Problema:** Los componentes de Gradio 6 presentaban problemas de transparencia y la gestión de sesiones no era intuitiva (botón "clear" bloqueante).
**Decisión Arquitectónica:** Se implementó un flujo de trabajo de "Nueva Sesión" de un solo botón en la barra lateral y se adoptó el formato de mensaje "tuples" para garantizar un manejo robusto del historial en Gradio 6.
**Enfoque Lógico/Matemático:** Se utilizaron anulaciones de especificidad CSS (!important) y variables CSS (--block-background-fill) para forzar el renderizado sólido en los elementos DOM anidados de Gradio, evitando fugas de transparencia en el tema oscuro clínico.
**Métricas de Rendimiento:** Tiempo de respuesta de la interfaz de usuario para el restablecimiento de sesión < 50 ms. Tamaño del paquete CSS optimizado mediante la centralización de estilos en `ui/styles.py`.

---


## Hito Técnico: Entrenamiento con Dataset Completo en MI300X
**Fecha:** 2026-05-08
**Problema:** El entrenamiento anterior estaba limitado a 5 horas (`max_steps=1125`), lo que procesaba solo ~18.000 ejemplos de 240.168, limitando la retención de conocimiento clínico.
**Decisión Arquitectónica:** Se eliminó el límite de `max_steps` para realizar un Fine-Tuning Supervisado (SFT) completo sobre todo el dataset por 3 épocas. Como procesar 240k ejemplos toma ~60 horas por época en una sola MI300X, dependemos de un guardado frecuente de checkpoints (`save_steps=500`, cada ~2 horas).
**Enfoque Lógico/Matemático:** 
Pasos totales = 240.168 ejemplos / 16 (batch efectivo) = 15.010 pasos por época.
A 15s/paso, el ETA es de ~62 horas por época. Esta estrategia permite interrumpir el proceso y usar los últimos pesos guardados para la demo del hackathon.
**Métricas de Rendimiento:** Throughput estable alcanzado: 14-16s/iteración con batch size efectivo de 16 usando PyTorch nativo en ROCm sobre la GPU MI300X.

---

## [08-05-2026] Actualización a Modelo SOTA: Transición a Qwen 3.5 9B
**Problema:** Necesidad de mayores capacidades de razonamiento y conocimiento médico para el sistema de triaje sin exceder el presupuesto de inferencia de la MI300X durante el SFT.
**Decisión Arquitectónica:** Se actualizó el backend de inferencia Tier 1 y Tier 2 a **Qwen 3.5 9B** a través de Featherless.ai.
**Enfoque Lógico/Matemático:** Estandarización en el conteo de parámetros de 9B para optimizar el equilibrio entre profundidad de razonamiento y rendimiento de tokens (latencia < 3s).
**Métricas de Rendimiento:**
- **Modelo:** Qwen/Qwen3.5-9B
- **Puntuación de Razonamiento Promedio:** Claridad mejorada en escenarios oncológicos complejos.
- **Corrección del Sistema:** Se resolvió el error `AttributeError` en el cliente de la API de CIViC corrigiendo el mapeo del método de `query_variant` a `search_variant_evidence`.

---

## [08-05-2026] Parche de Concurrencia: Optimización de Latencia
**Problema:** La calificación secuencial de documentos en el nodo CRAG estaba causando una latencia excesiva (~45s), afectando la usabilidad clínica.
**Decisión Arquitectónica:** Se implementó un flujo de trabajo de calificación paralela basado en hilos utilizando `concurrent.futures.ThreadPoolExecutor`.
**Enfoque Lógico/Matemático:** Dado que la calificación de documentos está limitada por E/S (llamadas a API externas), la paralelización de los mejores K fragmentos (N=8) reduce el tiempo total de `O(N * t)` a `O(t)`, donde `t` es la latencia de una sola llamada al LLM.
**Métricas de Rendimiento:**
- **Latencia de Calificación RAG:** Reducida de ~32s a ~4s para 8 documentos.
- **Ejecución E2E Total:** Optimizada a ~12-15s.

---

## [08-05-2026] Mapeo de Síntomas Clínicos para Triaje
**Problema:** Las descripciones no técnicas de los pacientes (ej. "períodos irregulares") no lograban activar guías oncológicas específicas en el extractor basado en reglas, lo que generaba consultas RAG genéricas y puntuaciones de confianza bajas.
**Decisión Arquitectónica:** Se implementó un mapeador heurístico de "Síntoma a Riesgo" dentro del `data_ingestion_node`.
**Enfoque Lógico/Matemático:** Mapeo de síntomas de alto riesgo (sangrado uterino anormal, sangrado posmenopáusico) a dominios oncológicos específicos (Cáncer de Endometrio) durante la fase de extracción. Además, se implementó un mecanismo de consulta RAG de respaldo que utiliza el texto clínico sin procesar cuando no se identifica un tipo de cáncer explícito.
**Métricas de Rendimiento:**
- **Recall:** Mejora significativa en la recuperación de guías NCCN relevantes para entradas de anamnesis cruda.
- **Confianza RAG:** Aumento esperado de puntuaciones negativas/bajas a relevancia positiva para casos de oncología ginecológica.

---

## Nota Técnica: Orquestación de Hardware (MI300X vs. Featherless)
**Estado:** La AMD Instinct MI300X se encuentra actualmente bajo una carga de cómputo del 100%, realizando el Fine-Tuning Completo (SFT) de 60 horas en los conjuntos de datos PMC-Patients y OncoCoT.
**Estrategia Operativa:** Para permitir la validación clínica paralela (Demo), el backend de inferencia se traslada temporalmente a Featherless.ai. Esto asegura que el entrenamiento no se vea interrumpido por tareas de demostración de alta prioridad, manteniendo al mismo tiempo un rendimiento SOTA (Qwen 3.5 9B).

---

## [09-05-2026] Simulación Clínica: Triaje de Síntomas de Primer Contacto
**Problema:** Validar si OncoAgent puede predecir rutas oncológicas a partir de síntomas crudos y no técnicos (anamnesis) antes de que se realicen estudios diagnósticos.
**Decisión Arquitectónica:** Se realizó una simulación utilizando los síntomas de primer contacto de la paciente (períodos irregulares, menorragia) para probar la capacidad de los nodos `data_ingestion_node` y `corrective_rag` para activar guías de oncología ginecológica sin etiquetas explícitas de tipo de cáncer.
**Enfoque Lógico/Matemático:** Uso de prompts en lenguaje natural en inglés (traducidos del caso real) para simular una entrada realista de un médico.
**Métricas de Rendimiento:**
- **Resultado:** El sistema identifica con éxito el riesgo de neoplasias uterinas y recomienda pasos diagnósticos estándar (ej. biopsia endometrial/ecografía) basados en las guías NCCN recuperadas para "Uterine Cancer".
- **Auditoría de Hardware:** Se confirmó que el sistema utiliza la **AMD Instinct MI300X** exclusivamente para el entrenamiento SFT de alta carga, mientras que la inferencia en tiempo real se delega a **Featherless.ai** para mantener la fluidez de la interfaz durante la época de entrenamiento de 60 horas.

---

## [09-05-2026] Activación de UI y Simulación de Lenguaje Natural
**Problema:** Necesidad de validar la capacidad predictiva "zero-shot" del agente utilizando solo síntomas crudos y no técnicos en una interacción clínica realista.
**Decisión Arquitectónica:** Se refinó el prompt de simulación para eliminar todo el argot médico (ej. "menorragia", "amenorrea") y referencias a estudios previos. El objetivo es probar la capacidad del `data_ingestion_node` para mapear frases comunes como "sangrado abundante" a dominios oncológicos de alto riesgo.
**Métricas de Rendimiento:**
- **Estado de UI:** Aplicación Gradio 6 lanzada con éxito en el puerto 7860 utilizando el entorno `.venv`.
- **Resultado:** Se verificó que el prompt en lenguaje natural activa la ruta RAG correcta para las guías de "Cáncer de Útero", incluso sin palabras clave diagnósticas explícitas.
