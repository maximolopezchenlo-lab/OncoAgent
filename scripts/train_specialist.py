"""
OncoAgent — QLoRA Fine-Tuning Script for Dual-Tier Qwen Architecture.

Trains a LoRA adapter on the combined real + synthetic oncology corpus
using 4-bit NormalFloat4 quantization (bitsandbytes) on AMD MI300X (ROCm).
Supports Dual-Tier: Tier 1 (Qwen 3.5 9B) and Tier 2 (Qwen 3.6 27B).

Key features:
  - Tier-adaptive hyperparameters (batch size, LoRA rank, seq length)
  - Automatic checkpoint resume on crash recovery
  - Eval split monitoring to detect overfitting
  - Training metadata saved for reproducibility audits

Hardware Target: AMD Instinct MI300X via ROCm 7.2.
Rule Compliance: #3 (Qwen 3.5/3.6, format ChatML), #14 (QLoRA + bitsandbytes + PEFT),
                 #22 (reproducibility seeds), #24 (.env), #26 (type hints).
"""

import argparse
import json
import os
import time
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

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
    EarlyStoppingCallback,
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


# ── Tier-Adaptive Configuration ─────────────────────────────────────────────

@dataclass
class TierConfig:
    """Tier-specific hyperparameters tuned for MI300X 192GB HBM3."""

    model_id: str
    lora_r: int
    lora_alpha: int
    max_seq_length: int
    batch_size: int
    gradient_accumulation: int
    learning_rate: float
    num_epochs: int
    save_steps: int


TIER_CONFIGS: Dict[int, TierConfig] = {
    1: TierConfig(
        model_id="Qwen/Qwen3.5-9B",
        lora_r=16,
        lora_alpha=32,
        max_seq_length=2048,
        batch_size=4,               # 9B fits larger batches in 192GB
        gradient_accumulation=4,    # Effective batch = 16
        learning_rate=2e-4,
        num_epochs=3,
        save_steps=500,
    ),
    2: TierConfig(
        model_id="Qwen/Qwen3.6-27B",
        lora_r=32,                  # Higher rank for 27B capacity
        lora_alpha=64,
        max_seq_length=2048,
        batch_size=2,               # 27B needs smaller micro-batch
        gradient_accumulation=8,    # Effective batch = 16
        learning_rate=1e-4,         # Lower LR for larger model stability
        num_epochs=3,
        save_steps=250,             # More frequent checkpoints for 27B
    ),
}

# ── Shared Constants ────────────────────────────────────────────────────────
OUTPUT_DIR: str = os.path.join("models", "oncoagent_adapters")
TRAIN_FILE: str = os.path.join("data", "final", "train_oncoagent.jsonl")
EVAL_FILE: str = os.path.join("data", "final", "train_oncoagent_eval.jsonl")

LORA_DROPOUT: float = 0.05
LORA_TARGET_MODULES: List[str] = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]

WARMUP_RATIO: float = 0.03
WEIGHT_DECAY: float = 0.01
MAX_GRAD_NORM: float = 1.0

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join("data", "final"), exist_ok=True)


# ── Data Loading ────────────────────────────────────────────────────────────

def load_jsonl_dataset(path: str, label: str = "data") -> Dataset:
    """Load a JSONL file into a HuggingFace Dataset.

    Args:
        path: Path to the JSONL file.
        label: Human-readable label for logging.

    Returns:
        HuggingFace Dataset object.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{label} file not found: {path}. "
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

    logger.info(f"📊 Loaded {len(texts):,} {label} samples from {path}")
    return Dataset.from_dict({"text": texts})


# ── Tokenization ────────────────────────────────────────────────────────────

def tokenize_dataset(
    dataset: Dataset,
    tokenizer: AutoTokenizer,
    max_length: int,
) -> Dataset:
    """Tokenize the dataset for causal language modeling.

    Args:
        dataset: Raw text dataset.
        tokenizer: The model tokenizer.
        max_length: Maximum sequence length.

    Returns:
        Tokenized dataset with input_ids, attention_mask, and labels.
    """
    def _tokenize(examples: Dict) -> Dict:
        tokenized = tokenizer(
            examples["text"],
            truncation=True,
            max_length=max_length,
            padding="max_length",
        )
        # DataCollatorForLanguageModeling automatically handles creating labels
        # padded with -100, so we don't need to manually copy input_ids here.
        return tokenized

    result = dataset.map(
        _tokenize,
        batched=True,
        remove_columns=dataset.column_names,
        desc="Tokenizing",
    )

    # Log token length distribution
    lengths = [len(ids) for ids in result["input_ids"]]
    avg_len = sum(lengths) / len(lengths) if lengths else 0
    max_len = max(lengths) if lengths else 0
    logger.info(
        f"✅ Tokenized {len(result):,} samples "
        f"(avg={avg_len:.0f}, max={max_len}, cap={max_length})"
    )
    return result


# ── Model Setup ─────────────────────────────────────────────────────────────

def setup_model_and_tokenizer(
    config: TierConfig,
) -> tuple:
    """Load the base model with 4-bit quantization and apply LoRA.

    Args:
        config: The tier-specific configuration.

    Returns:
        Tuple of (model, tokenizer, peft_config).
    """
    hf_token: Optional[str] = os.getenv("HF_TOKEN")

    # 4-bit quantization config (Rule #14)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    logger.info(f"📦 Loading base model: {config.model_id}")
    logger.info(f"   Device: {os.getenv('DEVICE', 'cuda')} (ROCm maps cuda→hip)")
    logger.info(f"   Quantization: 4-bit NormalFloat4 (double quant)")
    logger.info(f"   LoRA rank: {config.lora_r}, alpha: {config.lora_alpha}")

    tokenizer = AutoTokenizer.from_pretrained(
        config.model_id,
        token=hf_token,
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        config.model_id,
        quantization_config=bnb_config,
        device_map="auto",
        token=hf_token,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )
    model.config.use_cache = False

    # LoRA config — tier-adaptive rank
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGET_MODULES,
        bias="none",
    )
    model = get_peft_model(model, peft_config)

    trainable, total = model.get_nb_trainable_parameters()
    logger.info(
        f"🧠 LoRA applied: {trainable:,} trainable / {total:,} total "
        f"({100 * trainable / total:.2f}%)"
    )

    return model, tokenizer, peft_config


# ── Training Metadata ───────────────────────────────────────────────────────

def _save_training_metadata(
    output_dir: str,
    config: TierConfig,
    train_samples: int,
    eval_samples: int,
    duration_seconds: float,
    final_metrics: Optional[Dict[str, Any]] = None,
) -> None:
    """Save a JSON metadata file alongside the adapter for audit trails.

    Args:
        output_dir: Directory to save to.
        config: The tier config used.
        train_samples: Number of training samples.
        eval_samples: Number of eval samples.
        duration_seconds: Wall-clock training time.
        final_metrics: Optional metrics from trainer.
    """
    meta: Dict[str, Any] = {
        "project": "OncoAgent",
        "model_id": config.model_id,
        "tier": 1 if "9B" in config.model_id else 2,
        "lora_r": config.lora_r,
        "lora_alpha": config.lora_alpha,
        "max_seq_length": config.max_seq_length,
        "effective_batch_size": config.batch_size * config.gradient_accumulation,
        "learning_rate": config.learning_rate,
        "num_epochs": config.num_epochs,
        "train_samples": train_samples,
        "eval_samples": eval_samples,
        "duration_seconds": round(duration_seconds, 1),
        "duration_human": time.strftime("%Hh %Mm %Ss", time.gmtime(duration_seconds)),
        "hardware": "AMD Instinct MI300X (192GB HBM3)",
        "framework": "ROCm 7.2 + bitsandbytes (NF4) + PEFT/LoRA",
        "seed": SEED,
    }
    if final_metrics:
        meta["final_metrics"] = {
            k: round(v, 6) if isinstance(v, float) else v
            for k, v in final_metrics.items()
        }

    path = os.path.join(output_dir, "training_metadata.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    logger.info(f"📝 Training metadata saved to {path}")


# ── Training ────────────────────────────────────────────────────────────────

def train(
    tier: int,
    max_steps: int = -1,
    resume: bool = False,
) -> str:
    """Execute the full QLoRA training pipeline.

    Args:
        tier: The architectural tier to train (1 for 9B, 2 for 27B).
        max_steps: If > 0, stop training after this many steps (useful for dry runs).
        resume: If True, resume from the last checkpoint in the output directory.

    Returns:
        Path to the saved adapter directory.
    """
    config = TIER_CONFIGS.get(tier)
    if not config:
        raise ValueError(f"Invalid tier: {tier}. Must be 1 or 2.")

    logger.info(f"🚀 Starting OncoAgent QLoRA Training Pipeline (Tier {tier})")
    logger.info("=" * 60)
    logger.info(f"   Model:          {config.model_id}")
    logger.info(f"   LoRA rank:      {config.lora_r}")
    logger.info(f"   Batch size:     {config.batch_size} × {config.gradient_accumulation} = {config.batch_size * config.gradient_accumulation}")
    logger.info(f"   Learning rate:  {config.learning_rate}")
    logger.info(f"   Epochs:         {config.num_epochs}")
    logger.info(f"   Seq length:     {config.max_seq_length}")
    logger.info("=" * 60)

    # Setup
    model, tokenizer, peft_config = setup_model_and_tokenizer(config)
    train_dataset = load_jsonl_dataset(TRAIN_FILE, "training")
    tokenized_train = tokenize_dataset(train_dataset, tokenizer, config.max_seq_length)

    # Eval dataset (optional — graceful degradation if missing)
    tokenized_eval: Optional[Dataset] = None
    eval_samples: int = 0
    try:
        eval_dataset = load_jsonl_dataset(EVAL_FILE, "evaluation")
        tokenized_eval = tokenize_dataset(eval_dataset, tokenizer, config.max_seq_length)
        eval_samples = len(tokenized_eval)
    except FileNotFoundError:
        logger.warning("⚠️  Eval file not found — training without evaluation metrics")

    # Output directory
    tier_output_dir: str = os.path.join(OUTPUT_DIR, f"tier{tier}")
    os.makedirs(tier_output_dir, exist_ok=True)

    # Detect checkpoint for resume
    resume_checkpoint: Optional[str] = None
    if resume:
        checkpoints = sorted([
            os.path.join(tier_output_dir, d)
            for d in os.listdir(tier_output_dir)
            if d.startswith("checkpoint-")
        ])
        if checkpoints:
            resume_checkpoint = checkpoints[-1]
            logger.info(f"♻️  Resuming from checkpoint: {resume_checkpoint}")
        else:
            logger.warning("⚠️  --resume requested but no checkpoint found, starting fresh")

    # Training arguments
    training_args = TrainingArguments(
        output_dir=tier_output_dir,
        num_train_epochs=config.num_epochs,
        per_device_train_batch_size=config.batch_size,
        gradient_accumulation_steps=config.gradient_accumulation,
        learning_rate=config.learning_rate,
        weight_decay=WEIGHT_DECAY,
        warmup_ratio=WARMUP_RATIO,
        lr_scheduler_type="cosine",
        logging_steps=10,
        max_steps=max_steps,
        save_steps=config.save_steps,
        save_total_limit=3,
        fp16=True,
        gradient_checkpointing=True,
        max_grad_norm=MAX_GRAD_NORM,
        seed=SEED,
        report_to="none",
        remove_unused_columns=False,
        optim="paged_adamw_8bit",
        # Eval integration
        eval_strategy="steps" if tokenized_eval else "no",
        eval_steps=config.save_steps if tokenized_eval else None,
        load_best_model_at_end=True if tokenized_eval else False,
        metric_for_best_model="eval_loss" if tokenized_eval else None,
        greater_is_better=False if tokenized_eval else None,
    )

    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    # Callbacks
    callbacks = []
    if tokenized_eval:
        callbacks.append(EarlyStoppingCallback(early_stopping_patience=3))

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_eval,
        data_collator=data_collator,
        callbacks=callbacks,
    )

    # Train
    t0 = time.time()
    logger.info("🏋️ Training started...")
    train_result = trainer.train(resume_from_checkpoint=resume_checkpoint)
    duration = time.time() - t0

    # Save final adapter
    final_path: str = os.path.join(tier_output_dir, "final")
    model.save_pretrained(final_path)
    tokenizer.save_pretrained(final_path)

    # Save training metadata
    _save_training_metadata(
        output_dir=final_path,
        config=config,
        train_samples=len(tokenized_train),
        eval_samples=eval_samples,
        duration_seconds=duration,
        final_metrics=train_result.metrics if train_result else None,
    )

    # Final report
    logger.info("=" * 60)
    logger.info(f"🏁 TRAINING COMPLETE FOR TIER {tier} ({config.model_id})")
    logger.info(f"   Adapter saved to: {final_path}")
    logger.info(f"   Train samples:    {len(tokenized_train):,}")
    logger.info(f"   Eval samples:     {eval_samples:,}")
    logger.info(f"   Duration:         {time.strftime('%Hh %Mm %Ss', time.gmtime(duration))}")
    logger.info(f"   Final train loss: {train_result.metrics.get('train_loss', 'N/A')}")
    if tokenized_eval:
        eval_results = trainer.evaluate()
        logger.info(f"   Final eval loss:  {eval_results.get('eval_loss', 'N/A')}")
    logger.info("=" * 60)

    # Cleanup VRAM
    del model, trainer
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return final_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="OncoAgent QLoRA Fine-Tuning (Dual-Tier Qwen Architecture)"
    )
    parser.add_argument(
        "--tier",
        type=int,
        choices=[1, 2],
        required=True,
        help="Select the architectural tier to train (1 = Qwen 3.5 9B Speed, 2 = Qwen 3.6 27B Reasoning)",
    )
    parser.add_argument(
        "--max_steps",
        type=int,
        default=-1,
        help="Maximum number of training steps (useful for validation/dry-runs)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from the last checkpoint (critical for crash recovery on cloud instances)",
    )
    args = parser.parse_args()

    train(args.tier, max_steps=args.max_steps, resume=args.resume)
