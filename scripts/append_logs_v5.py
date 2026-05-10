import os
from datetime import datetime

BASE_DIR = "/mnt/36270add-d8d7-4990-b2b6-c9c5f803b31b/Hackatones/AMD Developer Hackathon/Repo v2"
PAPER_LOG_EN = os.path.join(BASE_DIR, "logs/paper_log.md")
PAPER_LOG_ES = os.path.join(BASE_DIR, "logs/paper_log.es.md")
SOCIAL_LOG_EN = os.path.join(BASE_DIR, "logs/social_media_log.txt")
SOCIAL_LOG_ES = os.path.join(BASE_DIR, "logs/social_media_log.es.txt")

PAPER_EN_ENTRY = """
## Hardware Breakthrough: Extreme Throughput via Sequence Packing
**Date:** 2026-05-08
**Context:** Full dataset fine-tuning of Tier 1 (Qwen 3.5 9B).
**Observation:** Training on the entire 266k synthetic clinical dataset completed in approximately 50 minutes, vastly under the 5-hour estimation.
**Architectural Reason:** The combination of `unsloth` kernels on the AMD Instinct MI300X and sequence packing (`packing=True` in SFTTrainer) allowed multiple short medical cases to be concatenated into single 2048-token sequences. This effectively minimized the padding token overhead and drastically reduced the total number of training steps without losing data points.
**Impact:** We can now iterate on full-dataset fine-tuning runs multiple times a day or increase the number of epochs to 3+ while staying within the hackathon time constraints.
"""

PAPER_ES_ENTRY = """
## Descubrimiento de Hardware: Throughput Extremo vía Sequence Packing
**Fecha:** 2026-05-08
**Contexto:** Fine-tuning con el dataset completo del Tier 1 (Qwen 3.5 9B).
**Observación:** El entrenamiento con los 266k casos clínicos sintéticos se completó en aproximadamente 50 minutos, muy por debajo de la estimación de 5 horas.
**Razón Arquitectónica:** La combinación de los kernels de `unsloth` en el AMD Instinct MI300X y el "sequence packing" (`packing=True` en SFTTrainer) permitió concatenar múltiples casos médicos cortos en secuencias únicas de 2048 tokens. Esto minimizó la sobrecarga de tokens de relleno (padding) y redujo drásticamente la cantidad de pasos de entrenamiento sin perder puntos de datos.
**Impacto:** Ahora podemos iterar sobre entrenamientos con el dataset completo múltiples veces al día, o incrementar la cantidad de épocas a 3+ manteniéndonos dentro de los límites de tiempo del hackathon.
"""

SOCIAL_EN_ENTRY = """
---
DATE: 2026-05-08 (Session 25)

### POST 1: X/TWITTER THREAD (Tone: Build in Public / Technical)
1/ 🤯 We over-estimated how long AI training takes when you use the right hardware. 

We budgeted 5 hours to fine-tune our 9B medical model on 266,000 clinical cases. The AMD Instinct MI300X chewed through it in ~50 MINUTES. ⏱️🔥

#AMDHackathon #ROCm #Unsloth

2/ 🛠️ The secret? Sequence Packing + Unsloth.
Instead of feeding short medical texts one by one and wasting compute on padding tokens, we packed them perfectly into 2048-token sequences. The MI300X memory bandwidth handled the dense tensors flawlessly.

3/ 🚀 This changes our entire iteration speed. We can now run multi-epoch training on massive datasets multiple times a day. Next up: pushing the Tier 2 27B model to see how hard we can stress this GPU!

#OpenSource #AI #HealthTech #MachineLearning #BuildInPublic

---
"""

SOCIAL_ES_ENTRY = """
---
FECHA: 2026-05-08 (Sesión 25)

### POST 1: HILO EN X/TWITTER (Tono: Build in Public / Técnico)
1/ 🤯 Sobreestimamos cuánto tarda el entrenamiento de IA cuando usas el hardware correcto.

Presupuestamos 5 horas para hacer fine-tuning a nuestro modelo médico de 9B con 266,000 casos clínicos. La AMD Instinct MI300X lo devoró en ~50 MINUTOS. ⏱️🔥

#AMDHackathon #ROCm #Unsloth

2/ 🛠️ ¿El secreto? Sequence Packing + Unsloth.
En lugar de procesar textos médicos cortos uno a uno y desperdiciar cómputo en tokens de relleno (padding), los empaquetamos perfectamente en secuencias de 2048 tokens. El ancho de banda de memoria de la MI300X manejó los tensores densos de forma impecable.

3/ 🚀 Esto cambia toda nuestra velocidad de iteración. Ahora podemos correr entrenamientos de múltiples épocas en datasets masivos varias veces al día. Siguiente paso: ¡probar el modelo Tier 2 de 27B para ver cuánto podemos estresar esta GPU!

#OpenSource #AI #HealthTech #MachineLearning #BuildInPublic

---
"""

def append_to_file(filepath, content):
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(content + "\n")
    print(f"✅ Appended to {filepath}")

def main():
    append_to_file(PAPER_LOG_EN, PAPER_EN_ENTRY)
    append_to_file(PAPER_LOG_ES, PAPER_ES_ENTRY)
    append_to_file(SOCIAL_LOG_EN, SOCIAL_EN_ENTRY)
    append_to_file(SOCIAL_LOG_ES, SOCIAL_ES_ENTRY)
    print("All logs updated successfully with hardware breakthrough metrics.")

if __name__ == "__main__":
    main()
