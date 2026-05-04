# ============================================================
# OncoAgent - Dockerfile for Hugging Face Spaces (ROCm/vLLM)
# Hardware Target: AMD Instinct MI300X
# ============================================================
FROM rocm/vllm:latest

WORKDIR /app

# Copy dependency manifest first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Expose Gradio default port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Launch UI (Gradio binds to 0.0.0.0:7860)
CMD ["python", "-m", "ui.app"]
