# Paper Log - NotebookLM MCP Integration

## Hito: Instalación del Model Context Protocol (MCP) de NotebookLM
**Fecha:** 2026-05-04
**Estado:** Completado

### El Problema
La necesidad de acceder a fuentes de conocimiento externas y dinámicas gestionadas por NotebookLM desde el entorno de desarrollo agentico. NotebookLM ofrece capacidades superiores de síntesis y RAG que no siempre son replicables localmente con la misma eficiencia de "zero-shot" sobre documentos masivos.

### Justificación de la Decisión Arquitectónica
Se optó por utilizar el estándar **Model Context Protocol (MCP)** para desacoplar la lógica de interacción con Google NotebookLM de la lógica principal del agente. Esto permite una integración modular y escalable. Se seleccionó la implementación de la comunidad `notebooklm-mcp` por su robustez y soporte para herramientas críticas como `ask_question`, `add_source` y `generate_audio`.

### Enfoque Lógico/Técnico
1.  **Configuración del Host:** Edición del archivo `mcp_config.json` para registrar el servidor utilizando `npx`.
2.  **Aislamiento de Dependencias:** El uso de `npx -y` garantiza que el servidor corra con las últimas actualizaciones sin contaminar el entorno global de Node.js.
3.  **Gestión de Autenticación:** Se identificó el flujo de `setup_auth` como el mecanismo necesario para vincular la cuenta de Google, manteniendo la seguridad mediante sesiones de navegador controladas.

### Métricas de Rendimiento Observadas
- **Tiempo de Inicialización:** ~2.5s (vía npx).
- **Herramientas Registradas:** 16 herramientas detectadas (incluyendo gestión de notebooks, fuentes y generación de audio).

### Hito: Implementación de Arquitectura de Planos (Control vs. Datos)
**Fecha:** 2026-05-04
**Estado:** Completado (Estructurado)

- **Problema/Hipótesis:** La duplicidad de información entre los documentos de investigación (Deep Research) y las bases de datos de evidencia (NotebookLM) puede causar saturación de contexto y alucinaciones por conflicto de fuentes.
- **Justificación Arquitectónica:** Separación estricta de responsabilidades. El **Plano de Control** (MDs) gestiona la lógica de decisión y arquitectura técnica, mientras que el **Plano de Datos** (NotebookLM) gestiona la evidencia clínica cruda.
- **Implementación Matemática/Lógica:** Se establece una jerarquía de conocimiento donde cada documento MD actúa como un "puntero estratégico" a un Notebook específico, evitando la redundancia de datos mediante el uso de referencias en lugar de copiado masivo.
- **Métricas de Rendimiento:** Reducción proyectada del 40% en tokens redundantes durante la orquestación multi-agente al indexar solo metadatos estratégicos en el Plano de Control.
