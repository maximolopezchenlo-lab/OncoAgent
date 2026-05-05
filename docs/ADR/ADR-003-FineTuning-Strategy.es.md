# ADR-003: Estrategia de Fine-Tuning para el Alineamiento con Guías Oncológicas

## Estado
Propuesto

## Fecha
2026-05-05

## Contexto
Para lograr un rendimiento de vanguardia (SOTA) en el triaje oncológico clínico, el modelo base (meta-llama/Meta-Llama-3.1-8B-Instruct) requiere un ajuste fino supervisado (SFT) sobre conocimiento médico estructurado. El desafío es mantener una alta precisión operando dentro de las limitaciones de memoria y las especificidades arquitectónicas del hardware AMD Instinct MI300X.

## Decisión
Implementaremos una estrategia QLoRA (Adaptación de Bajo Rango Cuantizada) utilizando cuantización de 4 bits NormalFloat4 (NF4).

### Detalles Técnicos:
1. **Precisión:** 4 bits NF4 utilizando un fork de `bitsandbytes` compatible con ROCm.
2. **Compute Dtype:** `torch.float16` para aprovechar el rendimiento de los Matrix Cores de la MI300X.
3. **Configuración de PEFT:**
   - Rango (r): 64
   - Alpha: 16
   - Módulos Objetivo: Todas las capas lineales (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`) para maximizar la capacidad de adaptación.
4. **Conjunto de Datos:** Dataset de ajuste de instrucciones generado a partir de fragmentos de guías NCCN/ESMO, formateado en la plantilla de chat de Llama 3.
5. **Optimizador:** `paged_adamw_32bit` para eficiencia de memoria.

## Consecuencias
- **Pros:**
  - Reducción significativa en el uso de VRAM (permitiendo mayores tamaños de lote o ventanas de contexto).
  - Mantiene un rendimiento cercano a la precisión completa de las capas adaptadas.
  - Alta reproducibilidad mediante semillas fijas e hiperparámetros estandarizados.
- **Contras:**
  - La sobrecarga de cuantización podría aumentar ligeramente la latencia durante la fase de carga inicial.
  - Requiere una configuración específica del entorno ROCm para `bitsandbytes`.
