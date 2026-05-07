"""
OncoAgent — QLoRA Fine-Tuning Script for Llama 3.1 8B Instruct.

Trains a LoRA adapter on the combined real + synthetic oncology corpus
using 4-bit NormalFloat4 quantization (bitsandbytes) on AMD MI300X (ROCm).

Hardware Target: AMD Instinct MI300X via ROCm 7.2.
Rule Compliance: #11 (Llama 3.1), #14 (QLoRA + bitsandbytes + PEFT),
                 #22 (reproducibility seeds), #24 (.env), #26 (type hints).
"""

import json
import os
import logging
from typing import Dict, List, Optional

import torch
from datasets import Dataset
from dotenv import load_dotenv
from peft import LoraConfig, get_peft_model, TaskType
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)

load_dotenv()

# ── Reproducibility (Rule #22) ──────────────────────────────────────────────
SEED: int = 42
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Configuration ───────────────────────────────────────────────────────────
MODEL_ID: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"
OUTPUT_DIR: str = os.path.join("models", "oncoagent_adapters")
TRAIN_FILE: str = os.path.join("data", "final", "train_oncoagent.jsonl")

LORA_R: int = 16
LORA_ALPHA: int = 32
LORA_DROPOUT: float = 0.05
LORA_TARGET_MODULES: List[str] = ["q_proj", "v_proj"]

MAX_SEQ_LENGTH: int = 2048
LEARNING_RATE: float = 2e-4
NUM_EPOCHS: int = 3
BATCH_SIZE: int = 2
GRADIENT_ACCUMULATION: int = 8  # Effective batch = 16
SAVE_STEPS: int = 500
WARMUP_RATIO: float = 0.03
WEIGHT_DECAY: float = 0.01

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join("data", "final"), exist_ok=True)


# ── Data Loading ────────────────────────────────────────────────────────────

def load_training_data(path: str = TRAIN_FILE) -> Dataset:
    """Load the unified JSONL training corpus into a HuggingFace Dataset.

    Args:
        path: Path to the JSONL training file.

    Returns:
        HuggingFace Dataset object.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Training file not found: {path}. "
            "Run download_hf_datasets.py and synthetic_generator.py first, "
            "then unify with dataset_builder.py."
        )

    texts: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                text = entry.get("text", "")
                if text:
                    texts.append(text)
            except json.JSONDecodeError:
                continue

    logger.info(f"📊 Loaded {len(texts):,} training samples from {path}")
    return Dataset.from_dict({"text": texts})


# ── Tokenization ────────────────────────────────────────────────────────────

def tokenize_dataset(
    dataset: Dataset,
    tokenizer: AutoTokenizer,
    max_length: int = MAX_SEQ_LENGTH,
) -> Dataset:
    """Tokenize the dataset for causal language modeling.

    Args:
        dataset: Raw text dataset.
        tokenizer: The model tokenizer.
        max_length: Maximum sequence length.

    Returns:
        Tokenized dataset.
    """
    def _tokenize(examples: Dict) -> Dict:
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=max_length,
            padding=False,
        )

    tokenized = dataset.map(
        _tokenize,
        batched=True,
        remove_columns=dataset.column_names,
        desc="Tokenizing",
    )
    logger.info(f"✅ Tokenized {len(tokenized):,} samples (max_length={max_length})")
    return tokenized


# ── Model Setup ─────────────────────────────────────────────────────────────

def setup_model_and_tokenizer() -> tuple:
    """Load the base model with 4-bit quantization and apply LoRA.

    Returns:
        Tuple of (model, tokenizer, peft_config).
    """
    hf_token = os.getenv("HF_TOKEN")

    # 4-bit quantization config (Rule #14)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    logger.info(f"📦 Loading base model: {MODEL_ID}")
    logger.info(f"   Device: {os.getenv('DEVICE', 'cuda')} (ROCm maps cuda→hip)")
    logger.info(f"   Quantization: 4-bit NormalFloat4")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID,
        token=hf_token,
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        token=hf_token,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )
    model.config.use_cache = False

    # LoRA config
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGET_MODULES,
        bias="none",
    )
    model = get_peft_model(model, peft_config)

    trainable, total = model.get_nb_trainable_parameters()
    logger.info(f"🧠 LoRA applied: {trainable:,} trainable / {total:,} total "
                f"({100 * trainable / total:.2f}%)")

    return model, tokenizer, peft_config


# ── Training ────────────────────────────────────────────────────────────────

def train() -> str:
    """Execute the full QLoRA training pipeline.

    Returns:
        Path to the saved adapter directory.
    """
    logger.info("🚀 Starting OncoAgent QLoRA Training Pipeline")
    logger.info("=" * 60)

    # Setup
    model, tokenizer, peft_config = setup_model_and_tokenizer()
    dataset = load_training_data()
    tokenized_dataset = tokenize_dataset(dataset, tokenizer)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
        warmup_ratio=WARMUP_RATIO,
        lr_scheduler_type="cosine",
        logging_steps=10,
        save_steps=SAVE_STEPS,
        save_total_limit=3,
        bf16=True,
        gradient_checkpointing=True,
        seed=SEED,
        report_to="none",
        remove_unused_columns=False,
        optim="paged_adamw_8bit",
    )

    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
    )

    logger.info("🏋️ Training started...")
    trainer.train()

    # Save final adapter
    final_path = os.path.join(OUTPUT_DIR, "final")
    model.save_pretrained(final_path)
    tokenizer.save_pretrained(final_path)

    logger.info("=" * 60)
    logger.info(f"🏁 TRAINING COMPLETE")
    logger.info(f"   Adapter saved to: {final_path}")
    logger.info(f"   Epochs: {NUM_EPOCHS}")
    logger.info(f"   Effective batch size: {BATCH_SIZE * GRADIENT_ACCUMULATION}")
    logger.info("=" * 60)

    return final_path


if __name__ == "__main__":
    train()
