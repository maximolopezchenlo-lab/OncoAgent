# ADR 006: Inferencia Nativa BF16 para Triaje Local

## Estado
Aprobado

## Contexto
La implementación inicial del especialista local (Tier 1) utilizaba Unsloth con cuantización de 4 bits (bitsandbytes) para minimizar el uso de memoria. Sin embargo, durante la validación en el hardware AMD MI300X, observamos "colapso semántico" y generación repetitiva de tokens (ej. repetición indefinida de signos de puntuación o frases).

Las investigaciones iniciales sugirieron que los artefactos de la cuantización de 4 bits, combinados con el manejo de ciertos kernels de menos de 8 bits por parte de la arquitectura CDNA3, estaban degradando la calidad de la inferencia para tareas clínicas que requieren alta precisión.

## Decisión
Migraremos el \`LocalModelManager\` de Unsloth/4-bit a precisión nativa **BFloat16 (BF16)** utilizando las librerías estándar \`transformers\` y \`peft\`.

Dada la masiva VRAM de 192GB de la AMD MI300X, el aumento en el requerimiento de memoria de BF16 (~14GB para un modelo 7B) está muy por debajo de las capacidades del hardware, incluso con múltiples agentes concurrentes.

## Consecuencias
- **Positivo:** Mejora de la estabilidad semántica y eliminación de los artefactos de salida repetitiva.
- **Positivo:** Compatibilidad total con los kernels bfloat16 nativos de ROCm.
- **Positivo:** Razonamiento clínico de mayor fidelidad en comparación con las versiones cuantizadas de 4 bits.
- **Neutral:** Mayor consumo de VRAM (aprox. 2.5x en comparación con 4 bits), lo cual es insignificante en la MI300X.
- **Neutral:** Tiempo de inicialización ligeramente superior ya que se cargan pesos más grandes en la memoria HBM3.
