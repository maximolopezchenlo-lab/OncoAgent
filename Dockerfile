# OncoAgent - Dockerfile for AMD Instinct MI300X & Hugging Face Spaces
# Hardware Target: AMD ROCm 7.2.x Ecosystem

# Base image: vLLM optimized for ROCm
FROM rocm/vllm:latest

# Set Environment Variables for Gradio and PyTorch
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT=7860
# Required for PyTorch to map 'cuda' calls to 'hip' correctly
ENV HSA_OVERRIDE_GFX_VERSION=9.4.2

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt /app/

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Expose the standard Hugging Face Spaces port for Gradio
EXPOSE 7860

# Start the application
ENTRYPOINT ["python", "ui/app.py"]
