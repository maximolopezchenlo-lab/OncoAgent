# ADR 002: Pivot a Arquitectura Qwen de Doble Nivel (Dual-Tier)

## Fecha
2026-05-06

## Estado
Aceptado

## Contexto
Inicialmente, el proyecto apuntaba a utilizar `meta-llama/Meta-Llama-3.1-8B-Instruct` como el modelo base exclusivo para fine-tuning. Sin embargo, para maximizar la utilización de las capacidades del AMD Instinct MI300X (192GB de VRAM) y ofrecer una solución más versátil, el usuario exigió explícitamente un pivot hacia la familia de modelos Qwen. Específicamente, la propuesta implica una arquitectura de "Doble Nivel" (Dual-Tier): ofrecer un modelo rápido y ligero (Qwen 9B) y un modelo pesado de alta precisión (Qwen 27B) para el triaje clínico.

Ambos modelos cuentan con soporte de "Día Cero" en ROCm y sus arquitecturas híbridas optimizadas (Gated Delta Networks) tienen soporte upstream en vLLM.

## Decisión
Pivotearemos la arquitectura del modelo base de un único Llama 3.1 8B a un ecosistema Qwen de Doble Nivel:
1.  **Nivel 1 (Velocidad y Eficiencia):** Qwen 9B. Utilizado para un triaje inicial rápido y de baja latencia.
2.  **Nivel 2 (Razonamiento Profundo):** Qwen 27B. Utilizado para casos complejos que requieren un razonamiento clínico más profundo.

Ambos modelos serán ajustados (fine-tuned) utilizando QLoRA (cuantización a 4 bits vía `bitsandbytes`) en el AMD MI300X, el cual tiene VRAM de sobra (192GB) para entrenar cómodamente un modelo de 27B (requiere ~30GB de VRAM bajo QLoRA).

## Consecuencias
*   **Positivo:** Podemos ofrecer opciones de despliegue flexibles a los proveedores de salud (velocidad vs. precisión máxima). Aprovechamos al máximo el masivo búfer de memoria del MI300X.
*   **Negativo:** Entrenar dos modelos requerirá ejecutar el pipeline de fine-tuning dos veces (o en paralelo, dependiendo de la asignación de GPUs), aumentando el tiempo total de cómputo.
*   **Adaptación Técnica:** El pipeline de preprocesamiento de datos debe asegurar que las salidas JSONL utilicen el formato ChatML de Qwen (`<|im_start|>` / `<|im_end|>`) en lugar de los tokens `<|start_header_id|>` de Llama, o bien depender de los templates nativos del tokenizador de Qwen.
