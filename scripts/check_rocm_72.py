import torch
import subprocess
import sys

def check_rocm():
    print("🔍 Diagnóstico del Entorno OncoAgent (ROCm 7.2.x)")
    print("="*50)
    
    # Check PyTorch version and HIP availability
    print(f"PyTorch Version: {torch.__version__}")
    gpu_available = torch.cuda.is_available()
    print(f"GPU Available (HIP/ROCm): {gpu_available}")
    
    if gpu_available:
        print(f"Current Device: {torch.cuda.get_device_name(0)}")
        print(f"HIP Version: {torch.version.hip}")
    else:
        print("❌ ERROR: No se detectó GPU compatible con HIP/ROCm.")
        print("💡 Sugerencia: Asegúrese de estar ejecutando dentro del contenedor rocm/vllm:rocm7.2")

    # Check for bitsandbytes ROCm
    try:
        import bitsandbytes as bnb
        print(f"✅ bitsandbytes detectado (Versión: {bnb.__version__})")
    except ImportError:
        print("❌ ERROR: bitsandbytes no encontrado. Es vital para la cuantización 4-bit (QLoRA).")

    # Check ROCm runtime info via shell
    try:
        result = subprocess.run(['rocminfo'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ rocminfo ejecutado exitosamente.")
        else:
            print("⚠️ rocminfo falló. Es posible que el entorno host no esté configurado.")
    except FileNotFoundError:
        print("⚠️ rocminfo no encontrado en el PATH.")

    print("="*50)
    print("Estado del Sistema: " + ("OPTIMIZADO para OncoAgent" if gpu_available else "CONFIGURACIÓN INCOMPLETA"))

if __name__ == "__main__":
    check_rocm()
