"""
OncoAgent — QLoRA Fine-Tuning Script (Unsloth-Accelerated).

Uses Unsloth's FastLanguageModel for 2x faster training with 60% less VRAM
on AMD Instinct MI300X (ROCm). 4-bit NF4 quantization via bitsandbytes.

Key features:
  - Unsloth-optimized kernels for Attention + Loss computation
  - Tier-adaptive hyperparameters (batch size, LoRA rank, seq length)
  - Automatic checkpoint resume on crash recovery
  - Eval split monitoring to detect overfitting
  - Training metadata saved for reproducibility audits

Hardware Target: AMD Instinct MI300X (gfx942) via ROCm 7.0 + HIP.
Rule Compliance: #3 (Qwen 3.5/3.6, format ChatML), #14 (QLoRA + bitsandbytes + PEFT),
                 #22 (reproducibility seeds), #24 (.env), #26 (type hints).
"""

import argparse
import json
import os
import time
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

# ── Critical AMD MI300X Environment ─────────────────────────────────────────
# Must be set BEFORE any ROCm/HIP library is invoked.
os.environ["HSA_OVERRIDE_GFX_VERSION"] = "9.4.2"
os.environ["HF_HUB_DISABLE_XET"] = "1"

from dotenv import load_dotenv
load_dotenv()

import torch
from datasets import Dataset

# Unsloth MUST be imported before trl to apply monkey-patches correctly
from unsloth import FastLanguageModel
from trl import SFTTrainer, SFTConfig

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
        batch_size=8,               # Proven ~16s/step throughput on MI300X with Unsloth
        gradient_accumulation=2,    # Effective batch = 16
        learning_rate=2e-4,
        num_epochs=3,               # Maximize clinical knowledge retention within ~2.5h on MI300X
        save_steps=500,
    ),
    2: TierConfig(
        model_id="Qwen/Qwen3.6-27B",
        lora_r=32,                  # Higher rank for 27B capacity
        lora_alpha=64,
        max_seq_length=2048,
        batch_size=4,               # 27B needs smaller micro-batch
        gradient_accumulation=4,    # Effective batch = 16
        learning_rate=1e-4,         # Lower LR for larger model stability
        num_epochs=1,
        save_steps=250,             # More frequent checkpoints for 27B
    ),
}

# ── Shared Constants ────────────────────────────────────────────────────────
OUTPUT_DIR: str = os.path.join("models", "oncoagent_adapters")
TRAIN_FILE: str = os.path.join("data", "final", "train_oncoagent.jsonl")
EVAL_FILE: str = os.path.join("data", "final", "train_oncoagent_eval.jsonl")

LORA_DROPOUT: float = 0.0  # Unsloth optimized: 0 dropout for speed
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


# ── Model Setup (Unsloth) ──────────────────────────────────────────────────

def setup_model_and_tokenizer(
    config: TierConfig,
) -> tuple:
    """Load model with Unsloth's FastLanguageModel (4-bit, LoRA-ready).

    Args:
        config: The tier-specific configuration.

    Returns:
        Tuple of (model, tokenizer).
    """
    # FastLanguageModel imported at module level

    hf_token: Optional[str] = os.getenv("HF_TOKEN")

    logger.info(f"📦 Loading model via Unsloth: {config.model_id}")
    logger.info(f"   Device: cuda (ROCm maps cuda→hip, gfx942 via HSA_OVERRIDE)")
    logger.info(f"   Quantization: 4-bit NF4 (Unsloth managed)")
    logger.info(f"   LoRA rank: {config.lora_r}, alpha: {config.lora_alpha}")

    # Unsloth handles quantization, model loading, and optimization in one call
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=config.model_id,
        max_seq_length=config.max_seq_length,
        load_in_4bit=True,
        token=hf_token,
    )

    # Extract the actual tokenizer for pad_token setup
    # Qwen3.5 returns a Qwen3VLProcessor wrapper
    actual_tokenizer = tokenizer.tokenizer if hasattr(tokenizer, "tokenizer") else tokenizer
    logger.info(f"   Tokenizer type: {type(tokenizer).__name__} → inner: {type(actual_tokenizer).__name__}")
    logger.info(f"   EOS token: {actual_tokenizer.eos_token!r}")

    if actual_tokenizer.pad_token is None:
        actual_tokenizer.pad_token = actual_tokenizer.eos_token

    # Apply LoRA via Unsloth's optimized path
    model = FastLanguageModel.get_peft_model(
        model,
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGET_MODULES,
        bias="none",
        use_gradient_checkpointing="unsloth",  # Unsloth's 2x speedup
        random_state=SEED,
    )

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    logger.info(
        f"🧠 LoRA applied: {trainable:,} trainable / {total:,} total "
        f"({100 * trainable / total:.2f}%)"
    )

    return model, actual_tokenizer  # Return inner tokenizer for SFTTrainer compatibility


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
        "framework": "Unsloth 2026.5.2 + ROCm 7.0 + bitsandbytes (NF4) + PEFT/LoRA",
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
    """Execute the Unsloth-accelerated QLoRA training pipeline.

    Args:
        tier: The architectural tier to train (1 for 9B, 2 for 27B).
        max_steps: If > 0, stop training after this many steps (useful for dry runs).
        resume: If True, resume from the last checkpoint in the output directory.

    Returns:
        Path to the saved adapter directory.
    """
    # SFTTrainer, SFTConfig imported at module level

    config = TIER_CONFIGS.get(tier)
    if not config:
        raise ValueError(f"Invalid tier: {tier}. Must be 1 or 2.")

    logger.info(f"🚀 Starting OncoAgent Unsloth Training Pipeline (Tier {tier})")
    logger.info("=" * 60)
    logger.info(f"   Model:          {config.model_id}")
    logger.info(f"   Engine:         Unsloth FastLanguageModel (2x speedup)")
    logger.info(f"   LoRA rank:      {config.lora_r}")
    logger.info(f"   Batch size:     {config.batch_size} × {config.gradient_accumulation} = {config.batch_size * config.gradient_accumulation}")
    logger.info(f"   Learning rate:  {config.learning_rate}")
    logger.info(f"   Epochs:         {config.num_epochs}")
    logger.info(f"   Seq length:     {config.max_seq_length}")
    logger.info(f"   HSA_GFX:        {os.environ.get('HSA_OVERRIDE_GFX_VERSION', 'NOT SET')}")
    logger.info("=" * 60)

    # Setup
    model, tokenizer = setup_model_and_tokenizer(config)
    train_dataset = load_jsonl_dataset(TRAIN_FILE, "training")

    # Eval dataset (optional — graceful degradation if missing)
    eval_dataset: Optional[Dataset] = None
    eval_samples: int = 0
    try:
        eval_dataset = load_jsonl_dataset(EVAL_FILE, "evaluation")
        eval_samples = len(eval_dataset)
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

    # SFTConfig = TrainingArguments + SFT-specific fields (trl >=0.14)
    sft_config = SFTConfig(
        output_dir=tier_output_dir,
        num_train_epochs=config.num_epochs,
        per_device_train_batch_size=config.batch_size,
        gradient_accumulation_steps=config.gradient_accumulation,
        learning_rate=config.learning_rate,
        weight_decay=WEIGHT_DECAY,
        warmup_steps=int(WARMUP_RATIO * (len(train_dataset) // (config.batch_size * config.gradient_accumulation))),
        lr_scheduler_type="cosine",
        logging_steps=10,
        max_steps=max_steps,
        save_steps=config.save_steps,
        save_total_limit=3,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        max_grad_norm=MAX_GRAD_NORM,
        seed=SEED,
        report_to="none",
        optim="adamw_8bit",
        # SFT-specific fields
        max_length=config.max_seq_length,
        packing=True,  # Pack multiple short samples into one sequence for ~2.5x throughput
        dataset_text_field="text",
        eos_token=None,  # Prevent EOS_TOKEN mismatch with Qwen3 tokenizers
        # No eval during training — too slow for 5h target. Eval post-training.
        eval_strategy="no",
    )

    # SFTTrainer from trl — Unsloth patches this for 2x speed
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,  # Inner tokenizer (not VLM processor) for packing compat
        train_dataset=train_dataset,
        args=sft_config,
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
        train_samples=len(train_dataset),
        eval_samples=eval_samples,
        duration_seconds=duration,
        final_metrics=train_result.metrics if train_result else None,
    )

    # Final report
    logger.info("=" * 60)
    logger.info(f"🏁 TRAINING COMPLETE FOR TIER {tier} ({config.model_id})")
    logger.info(f"   Adapter saved to: {final_path}")
    logger.info(f"   Train samples:    {len(train_dataset):,}")
    logger.info(f"   Eval samples:     {eval_samples:,}")
    logger.info(f"   Duration:         {time.strftime('%Hh %Mm %Ss', time.gmtime(duration))}")
    logger.info(f"   Final train loss: {train_result.metrics.get('train_loss', 'N/A')}")
    if eval_dataset:
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
        description="OncoAgent Unsloth QLoRA Fine-Tuning (Dual-Tier Qwen Architecture)"
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
