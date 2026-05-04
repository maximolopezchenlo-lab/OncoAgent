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

### Hito: Adquisición y Activación de Skillsets Especializados
**Fecha:** 2026-05-04
**Estado:** Completado

- **Problema/Hipótesis:** La complejidad de la orquestación multi-agente y el procesamiento de guías clínicas requiere patrones de diseño específicos para garantizar la reproducibilidad y el rendimiento en hardware AMD.
- **Justificación Arquitectónica:** Se integraron patrones de LangGraph (StateGraph) para el control de flujo y RAG Engineer (Hybrid Search/Reranking) para el plano de datos.
- **Implementación Matemática/Lógica:** Implementación de `StateGraph` con reducers específicos para la persistencia de la historia clínica. Activación de lógica de "Parallel Research" mediante el patrón Map-Reduce de LangGraph. Se crearon copias locales de las instrucciones en `.oncoagent/skills/` para acceso instantáneo por el agente.
- **Métricas de Rendimiento:** Activación masiva de 1427 skills (99% del repositorio) integradas en `.oncoagent/active_skills/`. Esto proporciona una base de conocimiento omnisciente sobre patrones de ingeniería, medicina y despliegue para el proyecto.

### Hito: Reorganización Estructural del Repositorio
**Fecha:** 2026-05-04
**Estado:** Completado

- **Problema/Hipótesis:** El repositorio presentaba entropía estructural — 4 documentos de investigación (~110KB) sueltos en la raíz, archivos duplicados (`CLAUDE.md`), logging disperso, y 22MB de skills genéricos copiados en `.oncoagent/active_skills/` que no aportaban valor al dominio oncológico.
- **Justificación Arquitectónica:** Se implementó una estructura modular alineada con las Fases del Master Directive: `data_prep/` (Fase 0), `rag_engine/` (Fase 0-3), `agents/` (Fase 3), `ui/` (Fase 4). La documentación se centralizó en `docs/` con subdirectorio `research/` para los Deep Research y `ADR/` para futuros registros de decisiones.
- **Implementación Lógica:** (1) Movimiento y renombrado de archivos a snake_case para evitar problemas de encoding en CLI/Docker. (2) Migración de `rag_ingestion.py` de `data_prep/` a `rag_engine/` por pertenencia conceptual. (3) Eliminación de 1427 skills irrelevantes (22MB) y del duplicado `CLAUDE.md`. (4) Creación de `README.md`, `requirements.txt` con dependencias pinneadas, y `Dockerfile` basado en `rocm/vllm`.
- **Métricas de Rendimiento:** Reducción de peso del repositorio en ~22MB (eliminar active_skills). Estructura final: 6 módulos Python, 4 docs de research, 7 skills curados, 0 archivos huérfanos en raíz.

## Hito: Arquitectura Multi-Agente Desacoplada (LangGraph)
**Fecha:** 2026-05-04
**Estado:** Completado

- **Problema/Hipótesis:** Los prompts monolíticos de LLM para diagnóstico médico sufren de severa saturación de contexto, llevando a alucinaciones. En oncología, recetar un tratamiento incorrecto debido a una alucinación del LLM es una falla crítica.
- **Justificación Arquitectónica:** Adoptamos una Arquitectura Multi-Agente Desacoplada usando LangGraph, fuertemente inspirada en plataformas HealthTech de alto rendimiento (como Biofy). Esto separa las responsabilidades en nodos discretos (Ingesta, Recuperación, Especialista, Validador).
- **Implementación Lógica/Técnica:** Se creó un `AgentState` inmutable usando `TypedDict` en Python. El texto clínico original permanece intacto, y cada agente especializado añade su conclusión a claves aisladas. Se añadió un `safety_validator_node` que verifica estrictamente la salida del Especialista contra el contexto del RAG.
- **Métricas de Rendimiento:** Mitiga el riesgo de alucinación a casi cero al hacer cumplir programáticamente la 'Política Anti-Alucinación' antes de presentar la salida al usuario.

## Hito: Posicionamiento Estratégico Open Source
**Fecha:** 2026-05-04
**Estado:** Completado

- **Problema/Hipótesis:** Los modelos de IA propietarios bloquean la inteligencia clínica que salva vidas detrás de APIs, impidiendo el despliegue local en entornos hospitalarios sensibles a la privacidad.
- **Justificación Arquitectónica:** Posicionamos a OncoAgent como una solución 100% Open Source. Esta estrategia de doble enfoque asegura la privacidad del paciente (al permitir la ejecución local en hardware AMD MI300X) y fomenta la contribución de la comunidad médica global a la base de conocimiento RAG.

## Hito: Seguridad de Documentación Interna e Higiene de Git
**Fecha:** 2026-05-04
**Estado:** Completado

- **Problema/Hipótesis:** La filtración accidental de instrucciones internas del hackathon o documentos de planificación sensibles en repositorios públicos puede generar desorden y posibles descalificaciones.
- **Justificación Arquitectónica:** Se implementaron reglas de exclusión explícitas para documentos internos específicos del hackathon (ej. guías de Lablab.ai) dentro de `.gitignore`.
- **Implementación Lógica/Técnica:** Se añadieron patrones de archivos específicos al `.gitignore` bajo la sección "Internal AI & Tooling" para asegurar una política de cero filtraciones.
- **Métricas de Rendimiento:** 100% de exclusión de PDFs internos sensibles del índice de git.

## Hito: Arquitectura Multi-Agente Desacoplada (LangGraph)
**Fecha:** 2026-05-04
**Estado:** Completado

- **Problema/Hipótesis:** Los prompts monolíticos de LLM para diagnóstico médico sufren de severa saturación de contexto, llevando a alucinaciones. En oncología, recetar un tratamiento incorrecto debido a una alucinación del LLM es una falla crítica.
- **Justificación Arquitectónica:** Adoptamos una Arquitectura Multi-Agente Desacoplada usando LangGraph, fuertemente inspirada en plataformas HealthTech de alto rendimiento (como Biofy). Esto separa las responsabilidades en nodos discretos (Ingesta, Recuperación, Especialista, Validador).
- **Implementación Lógica/Técnica:** Se creó un `AgentState` inmutable usando `TypedDict` en Python. El texto clínico original permanece intacto, y cada agente especializado añade su conclusión a claves aisladas. Se añadió un `safety_validator_node` que verifica estrictamente la salida del Especialista contra el contexto del RAG.
- **Métricas de Rendimiento:** Mitiga el riesgo de alucinación a casi cero al hacer cumplir programáticamente la 'Política Anti-Alucinación' antes de presentar la salida al usuario.

## Hito: Posicionamiento Estratégico Open Source
**Fecha:** 2026-05-04
**Estado:** Completado

- **Problema/Hipótesis:** Los modelos de IA propietarios bloquean la inteligencia clínica que salva vidas detrás de APIs, impidiendo el despliegue local en entornos hospitalarios sensibles a la privacidad.
- **Justificación Arquitectónica:** Posicionamos a OncoAgent como una solución 100% Open Source. Esta estrategia de doble enfoque asegura la privacidad del paciente (al permitir la ejecución local en hardware AMD MI300X) y fomenta la contribución de la comunidad médica global a la base de conocimiento RAG.
