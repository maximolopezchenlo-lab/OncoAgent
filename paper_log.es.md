# Registro del Artículo Académico OncoAgent

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
