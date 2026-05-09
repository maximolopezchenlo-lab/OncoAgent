# OncoAgent: Triaje Oncológico de Alto Rendimiento en AMD MI300X

## Descripción General del Proyecto
OncoAgent es un sistema de soporte de decisiones clínicas multi-agente diseñado para automatizar el triaje oncológico siguiendo las guías NCCN y ESMO. El sistema está optimizado para el hardware **AMD Instinct MI300X**, aprovechando ROCm 7.2 e inferencia de alta precisión.

## Hitos Técnicos Logrados
- **Inferencia BF16 Estable:** Migración exitosa del motor de inferencia local de cuantización de 4 bits a precisión **bfloat16** nativa, eliminando el colapso semántico y los artefactos de salida repetitiva.
- **Optimización MI300X:** Aprovechamiento de los 192GB de memoria HBM3 de la MI300X para cargar modelos de alta fidelidad (Qwen 2.5 7B) y adaptadores LoRA.
- **Orquestación LangGraph:** Implementación de una máquina de estados multi-agente robusta que maneja chequeos de seguridad clínica, recuperación RAG y razonamiento de especialistas.
- **Documentación Bilingüe:** Mantenimiento de un flujo de trabajo bilingüe (Inglés/Español) para toda la documentación técnica, logs y ADRs.

## Resultados de Validación
- **Compatibilidad de Hardware:** Confirmación del soporte nativo para \`bfloat16\` y kernels HIP en MI300X.
- **Calidad de Inferencia:** Validación con casos clínicos complejos (ej. sangrado uterino/irregularidades menstruales), logrando razonamientos coherentes y clínicamente sólidos.
- **Integridad del Sistema:** Todos los componentes principales (RAG, Herramientas, Agentes) están integrados y operativos en el entorno local del droplet.

## Listo para Despliegue
El sistema está completamente configurado para una demo final y su envío a Hugging Face Spaces.
