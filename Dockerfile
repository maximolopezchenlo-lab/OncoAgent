# ============================================================
# OncoAgent — Production Dockerfile
# Hardware: AMD Instinct MI300X / ROCm 7.2
# Serves: vLLM (Qwen3.5-9B + Qwen3.6-27B) + Gradio UI
# ============================================================

# Base image: vLLM optimized for ROCm
FROM rocm/vllm:latest

# System environment
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT=7860

# ROCm / PyTorch environment
ENV HSA_OVERRIDE_GFX_VERSION=9.4.2
ENV PYTORCH_ROCM_ARCH="gfx942"

# OncoAgent model configuration
ENV TIER1_MODEL_ID="Qwen/Qwen3.5-9B"
ENV TIER2_MODEL_ID="Qwen/Qwen3.6-27B"
ENV BASE_MODEL_ID="Qwen/Qwen3.5-9B"
ENV VLLM_API_BASE="http://localhost:8000/v1"
ENV VLLM_API_KEY="EMPTY"
ENV USE_LOCAL_ADAPTERS="false"
ENV DEVICE="cuda"
ENV TENSOR_PARALLEL_SIZE=1

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . /app/

# Make deploy scripts executable
RUN chmod +x deploy/start_vllm.sh

# Supervisor config to run vLLM + Gradio simultaneously
RUN cat > /etc/supervisor/conf.d/oncoagent.conf <<'EOF'
[supervisord]
nodaemon=true
logfile=/var/log/supervisord.log

[program:vllm]
command=bash /app/deploy/start_vllm.sh tier1
directory=/app
autostart=true
autorestart=true
stdout_logfile=/var/log/vllm.log
stderr_logfile=/var/log/vllm_err.log
priority=10

[program:gradio]
command=python /app/ui/app.py
directory=/app
autostart=true
autorestart=true
stdout_logfile=/var/log/gradio.log
stderr_logfile=/var/log/gradio_err.log
priority=20
startsecs=30
EOF

# Expose ports: Gradio (7860) + vLLM API (8000)
EXPOSE 7860 8000

# Start both services via supervisor
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/oncoagent.conf"]
