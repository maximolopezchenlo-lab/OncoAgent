import json
import os
import re
import random
import torch
from typing import List, Dict

# Reproducibilidad: Semilla fija según reglas
def set_seed(seed: int = 42):
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

class OncoDatasetBuilder:
    """
    Transformador de datasets médicos a formato JSONL (Llama 3.1).
    Incluye limpieza de PHI (Private Health Information).
    """
    
    def __init__(self, output_file: str = "oncoagent_finetuning.jsonl"):
        self.output_file = output_file
        set_seed(42)
        
        # Patrones para Zero-PHI (Básico)
        self.phi_patterns = [
            r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",  # Nombres Propios
            r"\d{2}/\d{2}/\d{4}",             # Fechas DD/MM/YYYY
            r"\b\d{9,}\b",                    # Posibles IDs numéricos
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b" # Emails
        ]

    def redact_phi(self, text: str) -> str:
        """Aplica filtros de redacción para asegurar Zero-PHI."""
        redacted = text
        for pattern in self.phi_patterns:
            redacted = re.sub(pattern, "[REDACTED]", redacted)
        return redacted

    def format_llama3_chat(self, system_msg: str, user_msg: str, assistant_msg: str) -> str:
        """Aplica el template de chat estricto de Llama 3."""
        template = (
            f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_msg}<|eot_id|>"
            f"<|start_header_id|>user<|end_header_id|>\n\n{user_msg}<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>\n\n{assistant_msg}<|eot_id|>"
        )
        return template

    def process_oncocot_sample(self, sample: Dict) -> str:
        """
        Procesa una muestra del dataset OncoCoT.
        Asume campos: 'history', 'reasoning', 'conclusion'
        """
        system = "Eres un oncólogo especialista. Analiza la historia clínica y proporciona un razonamiento cronológico (OncoCoT)."
        user = self.redact_phi(sample.get("history", ""))
        assistant = self.redact_phi(f"Razonamiento: {sample.get('reasoning', '')}\nConclusión: {sample.get('conclusion', '')}")
        
        return self.format_llama3_chat(system, user, assistant)

    def build(self, raw_data_path: str):
        """Lee datos crudos y genera el archivo JSONL."""
        if not os.path.exists(raw_data_path):
            print(f"⚠️ No se encontró el archivo: {raw_data_path}")
            return

        processed_count = 0
        with open(self.output_file, 'w', encoding='utf-8') as outfile:
            with open(raw_data_path, 'r', encoding='utf-8') as infile:
                # Asumiendo que el raw data es una lista de JSONs o JSONL
                try:
                    data = json.load(infile) if raw_data_path.endswith(".json") else [json.loads(line) for line in infile]
                    for entry in data:
                        formatted = self.process_oncocot_sample(entry)
                        outfile.write(json.dumps({"text": formatted}, ensure_ascii=False) + "\n")
                        processed_count += 1
                except Exception as e:
                    print(f"❌ Error procesando {raw_data_path}: {e}")

        print(f"✅ Dataset completado: {processed_count} muestras guardadas en {self.output_file}")

if __name__ == "__main__":
    builder = OncoDatasetBuilder()
    # builder.build("raw_data/oncocot_samples.json")
    print("🚀 Dataset Builder listo. Ejecuta builder.build(path) con tus datos crudos.")
