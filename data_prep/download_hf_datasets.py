import os
import json
import logging
from datasets import load_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = "data/samples"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Plantillas compatibles con Llama 3.1 (Formato estricto)
LLAMA3_TEMPLATE_PATIENT = (
    "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
    "You are an expert clinical oncologist.\n<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n"
    "Analyze the following patient summary.\n\nPatient Summary:\n{patient}\n<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
    "Patient UID: {patient_uid}. Case analyzed and ready for triage.\n<|eot_id|>"
)

LLAMA3_TEMPLATE_QA = (
    "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
    "You are an expert clinical oncologist.\n<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n"
    "Context:\n{context}\n\nQuestion: {question}\n<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
    "{long_answer}\n\nConclusion: {final_decision}\n<|eot_id|>"
)

def process_pmc_patients():
    logger.info("Descargando dataset PMC-Patients (zhengyun21/PMC-Patients)...")
    dataset = load_dataset("zhengyun21/PMC-Patients", split="train")
    
    output_file = os.path.join(OUTPUT_DIR, "pmc_patients.jsonl")
    logger.info(f"Guardando {len(dataset)} registros en formato estricto Llama 3.1 JSONL en {output_file}...")
    
    with open(output_file, "w", encoding="utf-8") as f:
        for item in dataset:
            prompt = LLAMA3_TEMPLATE_PATIENT.format(
                patient=item.get("patient", ""),
                patient_uid=item.get("patient_uid", "")
            )
            f.write(json.dumps({"text": prompt}) + "\n")
            
    logger.info("PMC-Patients finalizado.")

def process_pubmed_qa():
    logger.info("Descargando dataset PubMedQA (pubmed_qa, pqa_labeled)...")
    dataset = load_dataset("pubmed_qa", "pqa_labeled", split="train")
    
    output_file = os.path.join(OUTPUT_DIR, "pubmed_qa.jsonl")
    logger.info(f"Guardando {len(dataset)} registros en formato estricto Llama 3.1 JSONL en {output_file}...")
    
    with open(output_file, "w", encoding="utf-8") as f:
        for item in dataset:
            context_data = item.get("context", {})
            contexts_list = context_data.get("contexts", [])
            context_str = " ".join(contexts_list) if isinstance(contexts_list, list) else str(contexts_list)
            
            prompt = LLAMA3_TEMPLATE_QA.format(
                context=context_str,
                question=item.get("question", ""),
                long_answer=item.get("long_answer", ""),
                final_decision=item.get("final_decision", "")
            )
            f.write(json.dumps({"text": prompt}) + "\n")
            
    logger.info("PubMedQA finalizado.")

def main():
    logger.info("Iniciando adquisición de datos para Fine-Tuning (JSONL)...")
    process_pmc_patients()
    process_pubmed_qa()
    logger.info("Todos los datasets fueron procesados y guardados exitosamente.")

if __name__ == "__main__":
    main()
