import time
import torch
import numpy as np
from typing import List, Dict
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def benchmark_vllm_throughput(model_name: str, prompts: List[str]):
    """
    Benchmarks token throughput using the vLLM OpenAI-compatible API.
    Designed for AMD Instinct MI300X high-bandwidth performance.
    """
    api_base = os.getenv("VLLM_API_BASE", "http://localhost:8000/v1")
    api_key = os.getenv("VLLM_API_KEY", "EMPTY")
    
    client = OpenAI(api_key=api_key, base_url=api_base)
    
    print(f"\n--- Benchmarking vLLM on MI300X (Model: {model_name}) ---")
    
    total_tokens = 0
    start_time = time.time()
    
    for i, prompt in enumerate(prompts):
        p_start = time.time()
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=256
        )
        p_end = time.time()
        
        tokens = response.usage.completion_tokens
        total_tokens += tokens
        print(f"  [Request {i+1}] {tokens} tokens in {p_end - p_start:.2f}s ({tokens/(p_end-p_start):.2f} tokens/s)")
        
    end_time = time.time()
    total_duration = end_time - start_time
    
    print(f"\n[SUMMARY]")
    print(f"  Total Duration: {total_duration:.2f}s")
    print(f"  Total Tokens: {total_tokens}")
    print(f"  Aggregate Throughput: {total_tokens/total_duration:.2f} tokens/s")
    print(f"  Hardware Target: AMD Instinct™ MI300X (ROCm 7.2)")

def validate_torch_rocm():
    """
    Validates ROCm device detection and HBM3 memory accessibility.
    """
    print("\n--- Validating ROCm Environment ---")
    if not torch.cuda.is_available():
        print("  [ERROR] ROCm/HIP not detected by PyTorch.")
        return
    
    device_name = torch.cuda.get_device_name(0)
    device_count = torch.cuda.device_count()
    free_mem, total_mem = torch.cuda.mem_get_info(0)
    
    print(f"  Device: {device_name}")
    print(f"  GPU Count: {device_count}")
    print(f"  Total HBM3 Memory: {total_mem / (1024**3):.2f} GB")
    print(f"  Free HBM3 Memory: {free_mem / (1024**3):.2f} GB")
    
    # Simple tensor operation to verify compute
    x = torch.randn(1000, 1000).to("cuda")
    y = torch.randn(1000, 1000).to("cuda")
    z = torch.matmul(x, y)
    torch.cuda.synchronize()
    print("  Compute Check (Matrix Mult): SUCCESS")

if __name__ == "__main__":
    validate_torch_rocm()
    
    # Sample clinical prompts for throughput test
    test_prompts = [
        "Explain the standard of care for Metastatic Non-Small Cell Lung Cancer with EGFR T790M mutation.",
        "Summarize the NCCN guidelines for Triple Negative Breast Cancer Stage III.",
        "What are the second-line treatment options for BRAF V600E positive Melanoma?",
        "Compare the efficacy of Pembrolizumab vs Nivolumab in advanced RCC.",
        "List the common adverse effects of Sotorasib in KRAS G12C mutated NSCLC."
    ]
    
    try:
        benchmark_vllm_throughput("meta-llama/Meta-Llama-3.1-8B-Instruct", test_prompts)
    except Exception as e:
        print(f"\n[WARNING] vLLM benchmark skipped: {e}")
        print("Ensure the vLLM server is running on port 8000.")
