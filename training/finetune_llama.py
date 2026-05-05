import torch
import os
from datetime import datetime
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    set_seed
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer

# Reproducibility
set_seed(42)

def finetune():
    """
    OncoAgent Llama 3.1 Fine-Tuning Script optimized for AMD MI300X (ROCm 7.2).
    Implements QLoRA 4-bit (NF4) for clinical guideline alignment.
    """
    print(f"[{datetime.now()}] Starting OncoAgent Fine-Tuning...")

    model_id = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    dataset_path = "data/finetuning/onco_dataset.jsonl"
    output_dir = "models/oncoagent-llama-3.1-v1"

    # 1. Loading Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 2. BitsAndBytes Configuration (NF4 for MI300X)
    # Using ROCm-compatible settings
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16, # Optimized for MI300X
        bnb_4bit_use_double_quant=True,
    )

    # 3. Loading Model
    print(f"Loading model: {model_id}...")
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    
    # 4. Prepare model for k-bit training
    model = prepare_model_for_kbit_training(model)

    # 5. LoRA Configuration
    peft_config = LoraConfig(
        lora_alpha=16,
        lora_dropout=0.1,
        r=64,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    )
    
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # 6. Loading Dataset
    dataset = load_dataset("json", data_files=dataset_path, split="train")

    # 7. Training Arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=1,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        optim="paged_adamw_32bit", # ROCm optimized
        save_steps=100,
        logging_steps=10,
        learning_rate=2e-4,
        weight_decay=0.001,
        fp16=True, # Standard for ROCm training
        bf16=False,
        max_grad_norm=0.3,
        max_steps=-1,
        warmup_ratio=0.03,
        group_by_length=True,
        lr_scheduler_type="constant",
        report_to="none",
        push_to_hub=False,
    )

    # 8. Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        dataset_text_field="text",
        max_seq_length=2048,
        tokenizer=tokenizer,
        args=training_args,
        packing=False,
    )

    # 9. Execute Training
    print("Executing training...")
    trainer.train()

    # 10. Save Model
    print(f"Saving final model to {output_dir}")
    trainer.model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    print("Fine-tuning completed successfully.")

if __name__ == "__main__":
    finetune()
