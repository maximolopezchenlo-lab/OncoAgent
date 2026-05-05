import torch
import os
import subprocess

def check_rocm_environment():
    print("=== OncoAgent ROCm 7.2 Diagnostic Tool ===")
    
    # 1. Check PyTorch version and HIP
    print(f"\n[1] PyTorch Version: {torch.__version__}")
    hip_available = torch.cuda.is_available()
    print(f"GPU Available (via HIP): {hip_available}")
    
    if hip_available:
        print(f"GPU Device: {torch.cuda.get_device_name(0)}")
        print(f"HIP Version: {torch.version.hip}")
    
    # 2. Check for ROCm installation
    rocm_path = os.getenv("ROCM_PATH", "/opt/rocm")
    print(f"\n[2] Checking ROCm Path: {rocm_path}")
    if os.path.exists(rocm_path):
        print(f"ROCm found at {rocm_path}")
        try:
            rocminfo = subprocess.check_output(["rocminfo"], stderr=subprocess.STDOUT).decode()
            print("rocminfo: OK")
        except:
            print("rocminfo: Failed or not in PATH")
    else:
        print("ROCm path NOT FOUND")

    # 3. Check for bitsandbytes
    print("\n[3] Checking bitsandbytes...")
    try:
        import bitsandbytes as bnb
        print(f"bitsandbytes version: {bnb.__version__}")
        print("bitsandbytes loaded successfully")
    except ImportError:
        print("bitsandbytes NOT FOUND. Action: Install bitsandbytes-rocm fork.")
    except Exception as e:
        print(f"bitsandbytes error: {e}")

    # 4. Check for vLLM (if applicable)
    print("\n[4] Checking vLLM...")
    try:
        import vllm
        print(f"vLLM version: {vllm.__version__}")
    except ImportError:
        print("vLLM NOT FOUND")

if __name__ == "__main__":
    check_rocm_environment()
