
### Hito: Mejora del Motor RAG a SOTA (Markdown, Grafos y Evidencia en Vivo)
**Fecha:** 2026-05-06
**Problema:** Las guías clínicas contienen datos tabulares complejos (ej. estadificación TNM, esquemas de dosificación) que la extracción de texto plano suele corromper. Además, el RAG estático está limitado por la fecha de corte del entrenamiento, perdiendo actualizaciones de ensayos clínicos y evidencia genómica en tiempo real.
**Decisión Arquitectónica:** 
1. **Transición a Markdown:** Cambio de texto plano a extracción Markdown usando `pymupdf4llm` para preservar la integridad estructural de las tablas clínicas.
2. **Grafo de Conocimiento (GraphRAG):** Implementación de una capa de relaciones usando `networkx` para mapear entidades como `Mutación Accionable <-> Terapia Dirigida <-> Condición`.
3. **Conectividad con APIs en Vivo:** Integración de consultas en tiempo real a CIViC (genómica) y ClinicalTrials.gov v2 (ensayos Fase II/III).
**Resultados:** Mayor precisión en el análisis mutacional y provisión de evidencia actualizada al minuto para el triaje de pacientes.

### Hito: Fase 2 — UI Premium y Validación de Hardware (MI300X)
**Fecha:** 2026-05-06
**Problema:** Una interfaz de línea de comandos o de texto básica es insuficiente para la adopción clínica. Los médicos necesitan transparencia en las fuentes RAG, métricas de confianza y visibilidad de la evidencia en tiempo real. Además, el rendimiento del sistema en los aceleradores AMD debe cuantificarse para su validación técnica.
**Decisión Arquitectónica:** 
1. **UI Glassmorphism:** Desarrollo de un tablero Gradio de alta fidelidad utilizando CSS personalizado (Glassmorphism) para crear una experiencia de usuario premium de grado médico.
2. **Pipeline Transparente:** Implementación de resultados en pestañas múltiples para mostrar explícitamente los hallazgos de GraphRAG, evidencia de APIs y fuentes originales de las guías, cumpliendo con el requisito de "IA Explicable".
3. **Validación Específica de Hardware:** Creación de `scripts/validate_mi300x.py` para medir el rendimiento de tokens de vLLM y la utilización de memoria HBM3 en la plataforma MI300X.
**Resultados:** Interfaz de alto rendimiento integrada exitosamente con el backend de LangGraph. Listo para demostración de grado clínico en hardware AMD Instinct.
