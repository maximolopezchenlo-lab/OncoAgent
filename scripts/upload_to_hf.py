import os
from huggingface_hub import HfApi

TOKEN = os.environ.get("HF_TOKEN")
if not TOKEN:
    raise ValueError("HF_TOKEN environment variable is not set. Please provide a token.")
ORG = "lablab-ai-amd-developer-hackathon"
api = HfApi(token=TOKEN)

def get_gitignore_patterns():
    patterns = [".git*"]
    if os.path.exists(".gitignore"):
        with open(".gitignore", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if line.startswith("/"):
                        line = line[1:]
                    if line.endswith("/"):
                        line = line + "*"
                    patterns.append(line)
    return patterns

EXCLUDE_PATTERNS = get_gitignore_patterns()

print("1. Creando y subiendo el Space Repo (OncoAgent)...")
space_repo_id = f"{ORG}/OncoAgent"
try:
    api.create_repo(repo_id=space_repo_id, repo_type="space", space_sdk="gradio", exist_ok=True)
    api.upload_folder(
        folder_path=".",
        repo_id=space_repo_id,
        repo_type="space",
        ignore_patterns=EXCLUDE_PATTERNS,
        delete_patterns="*"
    )
    print("✅ Space subido correctamente.")
except Exception as e:
    print(f"❌ Error con el Space: {e}")

print("\n2. Creando y subiendo el Artículo/Dataset (OncoAgent_Official_Paper)...")
dataset_repo_id = f"{ORG}/OncoAgent_Official_Paper"
try:
    api.create_repo(repo_id=dataset_repo_id, repo_type="dataset", exist_ok=True)
    api.upload_file(
        path_or_fileobj="./docs/OncoAgent_Official_Paper.pdf",
        path_in_repo="OncoAgent_Official_Paper.pdf",
        repo_id=dataset_repo_id,
        repo_type="dataset"
    )
    print("✅ Paper subido correctamente.")
except Exception as e:
    print(f"❌ Error con el Paper: {e}")

print("\n3. Creando y sincronizando el Storage Bucket (OncoAgent)...")
bucket_id = f"{ORG}/OncoAgent"
try:
    api.create_bucket(bucket_id=bucket_id, exist_ok=True)
    api.sync_bucket(
        source=".",
        dest=f"hf://buckets/{bucket_id}",
        exclude=EXCLUDE_PATTERNS,
        delete=True
    )
    print("✅ Bucket sincronizado correctamente.")
except Exception as e:
    print(f"❌ Error con el Bucket: {e}")
