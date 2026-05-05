import json
import os
import glob

def format_llama3_chat(system: str, user: str, assistant: str) -> str:
    """Formats a conversation for Llama 3.1 chat template."""
    return (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n\n{user}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n{assistant}<|eot_id|>"
    )

def convert_chunks_to_jsonl(input_dir: str, output_file: str):
    """Converts medical guideline chunks into JSONL for fine-tuning."""
    print(f"Reading chunks from {input_dir}...")
    
    chunk_files = glob.glob(os.path.join(input_dir, "*.json"))
    dataset = []
    
    system_message = (
        "You are OncoAgent, a professional oncology clinical specialist. "
        "Your goal is to provide evidence-based recommendations grounded strictly in clinical guidelines. "
        "Always follow the OncoCoT (Oncology Chain-of-Thought) reasoning process."
    )
    
    for file_path in chunk_files:
        with open(file_path, "r") as f:
            data = json.load(f)
            # data is a list of chunks: {"header": ..., "content": ...}
            for chunk in data:
                header = chunk.get("header", "General Guideline")
                content = chunk.get("content", "")
                
                if len(content.strip()) < 50:
                    continue
                
                # Synthetic instruction generation
                user_message = f"Based on the clinical guidelines for {header}, what are the key recommendations?"
                assistant_message = f"According to the guidelines for {header}:\n\n{content}"
                
                formatted_text = format_llama3_chat(system_message, user_message, assistant_message)
                dataset.append({"text": formatted_text})
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        for entry in dataset:
            f.write(json.dumps(entry) + "\n")
            
    print(f"Successfully created {output_file} with {len(dataset)} examples.")

if __name__ == "__main__":
    INPUT_DIR = "data/processed/chunks"
    OUTPUT_FILE = "data/finetuning/onco_dataset.jsonl"
    convert_chunks_to_jsonl(INPUT_DIR, OUTPUT_FILE)
