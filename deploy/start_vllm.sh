#!/usr/bin/env bash
# ============================================================
# OncoAgent — vLLM Startup Script for AMD Instinct MI300X
# Serves both Tier 1 (Qwen3.5-9B) and Tier 2 (Qwen3.6-27B)
# using the OpenAI-compatible API on port 8000.
#
# Usage:
#   chmod +x deploy/start_vllm.sh
#   ./deploy/start_vllm.sh [tier1|tier2|both]
#
# Default: tier1 (single-model mode for demos)
# ============================================================

set -euo pipefail

# --- Configuration ---
TIER1_MODEL="${TIER1_MODEL_ID:-Qwen/Qwen3.5-9B}"
TIER2_MODEL="${TIER2_MODEL_ID:-Qwen/Qwen3.6-27B}"
VLLM_PORT="${VLLM_PORT:-8000}"
TENSOR_PARALLEL="${TENSOR_PARALLEL_SIZE:-1}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}"
GPU_MEMORY_UTIL="${GPU_MEMORY_UTILIZATION:-0.90}"
ADAPTER_PATH="${LOCAL_ADAPTER_PATH:-}"

# ROCm environment
export HSA_OVERRIDE_GFX_VERSION="${HSA_OVERRIDE_GFX_VERSION:-9.4.2}"
export PYTORCH_ROCM_ARCH="gfx942"

MODE="${1:-tier1}"

echo "============================================"
echo "  OncoAgent vLLM Server — AMD MI300X"
echo "  Mode: ${MODE}"
echo "============================================"

case "${MODE}" in
    tier1)
        echo "Starting Tier 1: ${TIER1_MODEL}"
        SERVE_MODEL="${TIER1_MODEL}"

        # Build command
        CMD="python -m vllm.entrypoints.openai.api_server \
            --model ${SERVE_MODEL} \
            --port ${VLLM_PORT} \
            --tensor-parallel-size ${TENSOR_PARALLEL} \
            --max-model-len ${MAX_MODEL_LEN} \
            --gpu-memory-utilization ${GPU_MEMORY_UTIL} \
            --dtype bfloat16 \
            --trust-remote-code \
            --enable-auto-tool-choice"

        # Add LoRA adapters if configured
        if [ -n "${ADAPTER_PATH}" ] && [ -d "${ADAPTER_PATH}" ]; then
            echo "Loading LoRA adapters from: ${ADAPTER_PATH}"
            CMD="${CMD} --enable-lora --lora-modules oncoagent-tier1=${ADAPTER_PATH}"
        fi

        eval ${CMD}
        ;;

    tier2)
        echo "Starting Tier 2: ${TIER2_MODEL}"
        python -m vllm.entrypoints.openai.api_server \
            --model "${TIER2_MODEL}" \
            --port "${VLLM_PORT}" \
            --tensor-parallel-size "${TENSOR_PARALLEL}" \
            --max-model-len "${MAX_MODEL_LEN}" \
            --gpu-memory-utilization "${GPU_MEMORY_UTIL}" \
            --dtype bfloat16 \
            --trust-remote-code \
            --enable-auto-tool-choice
        ;;

    both)
        echo "Multi-model mode: serving both tiers"
        echo "  Tier 1 (port ${VLLM_PORT}): ${TIER1_MODEL}"
        echo "  Tier 2 (port $((VLLM_PORT + 1))): ${TIER2_MODEL}"
        echo ""
        echo "Starting Tier 1..."

        CMD_T1="python -m vllm.entrypoints.openai.api_server \
            --model ${TIER1_MODEL} \
            --port ${VLLM_PORT} \
            --tensor-parallel-size ${TENSOR_PARALLEL} \
            --max-model-len ${MAX_MODEL_LEN} \
            --gpu-memory-utilization 0.45 \
            --dtype bfloat16 \
            --trust-remote-code"

        if [ -n "${ADAPTER_PATH}" ] && [ -d "${ADAPTER_PATH}" ]; then
            CMD_T1="${CMD_T1} --enable-lora --lora-modules oncoagent-tier1=${ADAPTER_PATH}"
        fi

        eval ${CMD_T1} &
        T1_PID=$!
        sleep 10

        echo "Starting Tier 2..."
        python -m vllm.entrypoints.openai.api_server \
            --model "${TIER2_MODEL}" \
            --port "$((VLLM_PORT + 1))" \
            --tensor-parallel-size "${TENSOR_PARALLEL}" \
            --max-model-len "${MAX_MODEL_LEN}" \
            --gpu-memory-utilization 0.45 \
            --dtype bfloat16 \
            --trust-remote-code &
        T2_PID=$!

        echo "Both models running. PIDs: Tier1=${T1_PID} Tier2=${T2_PID}"
        wait
        ;;

    *)
        echo "Usage: $0 [tier1|tier2|both]"
        exit 1
        ;;
esac
