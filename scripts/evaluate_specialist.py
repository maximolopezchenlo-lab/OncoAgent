import argparse
import os
import time
import logging

os.environ["HSA_OVERRIDE_GFX_VERSION"] = "9.4.2"
os.environ["HF_HUB_DISABLE_XET"] = "1"

from dotenv import load_dotenv
load_dotenv()

import torch
from unsloth import FastLanguageModel
from trl import SFTTrainer, SFTConfig

from train_specialist import TIER_CONFIGS, load_jsonl_dataset, EVAL_FILE, SEED

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def evaluate(tier: int):
    """
    Evaluate the fine-tuned OncoAgent model (Tier 1 or 2) on the evaluation dataset.
    Reports cross-entropy loss and perplexity.
    """
    config = TIER_CONFIGS.get(tier)
    if not config:
        raise ValueError(f"Invalid tier: {tier}")

    adapter_path = os.path.join("models", "oncoagent_adapters", f"tier{tier}", "final")
    
    if not os.path.exists(adapter_path):
        logger.error(f"Adapter path not found: {adapter_path}. Please run training first.")
        return
        
    logger.info("=" * 60)
    logger.info(f"🔍 Starting Post-Training Evaluation for Tier {tier}")
    logger.info(f"   Adapter path: {adapter_path}")
    logger.info("=" * 60)

    # Load the model with Unsloth's optimizations
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=adapter_path,
        max_seq_length=config.max_seq_length,
        load_in_4bit=True,
    )
    
    try:
        eval_dataset = load_jsonl_dataset(EVAL_FILE, "evaluation")
    except FileNotFoundError:
        logger.error(f"Eval file not found at {EVAL_FILE}. Cannot perform evaluation.")
        return

    logger.info("Running quantitative evaluation (Loss & Perplexity)...")
    
    actual_tokenizer = tokenizer.tokenizer if hasattr(tokenizer, "tokenizer") else tokenizer
    if actual_tokenizer.pad_token is None:
        actual_tokenizer.pad_token = actual_tokenizer.eos_token

    sft_config = SFTConfig(
        output_dir=os.path.join("models", "oncoagent_adapters", f"tier{tier}", "eval_results"),
        per_device_eval_batch_size=config.batch_size,
        max_length=config.max_seq_length,
        packing=True,
        dataset_text_field="text",
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        report_to="none",
        eos_token=None,
    )
    
    trainer = SFTTrainer(
        model=model,
        processing_class=actual_tokenizer,
        eval_dataset=eval_dataset,
        args=sft_config,
    )
    
    t0 = time.time()
    metrics = trainer.evaluate()
    duration = time.time() - t0
    
    logger.info("=" * 60)
    logger.info(f"✅ EVALUATION COMPLETE FOR TIER {tier}")
    logger.info(f"   Eval duration:    {time.strftime('%Hh %Mm %Ss', time.gmtime(duration))}")
    for k, v in metrics.items():
        if isinstance(v, float):
            logger.info(f"   {k}: {v:.4f}")
        else:
            logger.info(f"   {k}: {v}")
            
    try:
        perplexity = torch.exp(torch.tensor(metrics["eval_loss"])).item()
        logger.info(f"   Perplexity:       {perplexity:.4f}")
    except Exception:
        pass
    logger.info("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Fine-Tuned OncoAgent Models")
    parser.add_argument("--tier", type=int, choices=[1, 2], required=True,
                        help="Select the architectural tier to evaluate (1 = 9B, 2 = 27B)")
    args = parser.parse_args()
    evaluate(args.tier)
