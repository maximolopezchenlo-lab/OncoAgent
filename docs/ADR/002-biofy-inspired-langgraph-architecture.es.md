# ADR 002: Arquitectura LangGraph Inspirada en Biofy

**Fecha:** 2026-05-04
**Estado:** Aceptado

## Contexto
OncoAgent requiere un sistema multi-agente altamente confiable para procesar datos clínicos no estructurados y cruzarlos con guías NCCN/ESMO. Los prompts lineales tradicionales de LLM sufren de saturación de contexto y son propensos a alucinaciones, lo cual es inaceptable en oncología.

Durante nuestra investigación, analizamos arquitecturas de plataformas HealthTech de alto rendimiento como Biofy, que utilizan pipelines de agentes especializados (Extracción de ADN -> Búsqueda Vectorial -> Síntesis) para lograr alta precisión y eliminar la prescripción a ciegas.

## Decisión
Hemos decidido adoptar una **Arquitectura Multi-Agente Desacoplada utilizando LangGraph**.
1. **Estado Inmutable:** Definimos un `AgentState` usando `TypedDict` donde el texto clínico original es inmutable.
2. **Nodos Especializados:** El flujo se divide estrictamente en cuatro roles distintos:
   - `data_ingestion_node`: Extrae entidades y aplica Zero-PHI.
   - `rag_retrieval_node`: Realiza la búsqueda semántica contra ChromaDB/FAISS.
   - `clinical_specialist_node`: Formula la recomendación.
   - `safety_validator_node`: Ejecuta controles anti-alucinación.
3. **Ruteo Estricto:** El grafo se compila con un `recursion_limit` fijo para evitar bucles infinitos durante los controles de seguridad.

## Consecuencias
- **Positivo:** Máxima trazabilidad. Podemos registrar exactamente qué contexto se recuperó y cómo lo usó el especialista, haciendo transparente la auditoría clínica.
- **Positivo:** Previene alucinaciones forzando estructuralmente al especialista a ver únicamente el contexto curado por el RAG.
- **Negativo:** Ligero aumento de latencia comparado con un prompt de una sola vez debido a múltiples invocaciones al LLM. Sin embargo, ejecutar localmente en AMD MI300X a través de vLLM con PagedAttention mitigará este costo.
