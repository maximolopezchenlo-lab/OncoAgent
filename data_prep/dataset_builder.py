"""
OncoAgent — Dataset Builder / Unifier.

Combines real (HuggingFace-filtered) and synthetic (Qwen3.5-9B generated)
oncology data into a single training-ready JSONL corpus in Llama 3.1
chat template format.

Hardware Target: CPU only.
Rule Compliance: #12 (JSONL + Llama 3 format), #22 (seeds), #26 (type hints).
"""

import json
import os
import random
import logging
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()

random.seed(42)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Paths ───────────────────────────────────────────────────────────────────
FILTERED_REAL: str = os.path.join("data", "filtered", "onco_real_filtered.jsonl")
SYNTHETIC_DIR: str = os.path.join("data", "synthetic")
FINAL_OUTPUT: str = os.path.join("data", "final", "train_oncoagent.jsonl")

SYSTEM_PROMPT: str = (
    "You are an expert clinical oncologist specializing in cancer triage. "
    "Analyze the patient's clinical presentation using temporal-causal "
    "reasoning (OncoCoT). Provide: (1) key findings, (2) step-by-step "
    "diagnostic reasoning with staging, and (3) evidence-based recommendations "
    "citing NCCN/ESMO guidelines where applicable."
)


def format_synthetic_to_llama3(case: Dict[str, str]) -> str:
    """Convert a synthetic case dict to Llama 3.1 chat template.

    Args:
        case: Dict with 'history', 'reasoning', 'conclusion' keys.

    Returns:
        Formatted Llama 3 chat template string.
    """
    history = case.get("history", "")
    reasoning = case.get("reasoning", "")
    conclusion = case.get("conclusion", "")

    user_msg = f"Clinical Presentation:\n{history}"
    assistant_msg = (
        f"Diagnostic Reasoning:\n{reasoning}\n\n"
        f"Assessment & Plan:\n{conclusion}"
    )

    return (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
        f"{SYSTEM_PROMPT}<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n\n"
        f"{user_msg}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n"
        f"{assistant_msg}<|eot_id|>"
    )


def load_real_data() -> List[Dict[str, str]]:
    """Load real filtered oncology data."""
    if not os.path.exists(FILTERED_REAL):
        logger.warning(f"⚠️  Real data not found: {FILTERED_REAL}")
        return []

    entries: List[Dict[str, str]] = []
    with open(FILTERED_REAL, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entries.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue

    logger.info(f"📚 Loaded {len(entries):,} real oncology samples")
    return entries


def load_synthetic_data() -> List[Dict[str, str]]:
    """Load all synthetic generated data and format to Llama 3."""
    if not os.path.exists(SYNTHETIC_DIR):
        logger.warning(f"⚠️  Synthetic dir not found: {SYNTHETIC_DIR}")
        return []

    # Look for the final consolidated file first
    final = os.path.join(SYNTHETIC_DIR, "onco_synthetic_final.jsonl")
    files_to_read = []

    if os.path.exists(final):
        files_to_read = [final]
    else:
        files_to_read = sorted([
            os.path.join(SYNTHETIC_DIR, f)
            for f in os.listdir(SYNTHETIC_DIR)
            if f.endswith(".jsonl") and f.startswith("generated_")
        ])

    entries: List[Dict[str, str]] = []
    for fpath in files_to_read:
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    case = json.loads(line.strip())
                    formatted = format_synthetic_to_llama3(case)
                    entries.append({
                        "text": formatted,
                        "source": "synthetic_qwen35",
                    })
                except (json.JSONDecodeError, KeyError):
                    continue

    logger.info(f"🧬 Loaded {len(entries):,} synthetic oncology samples")
    return entries


def build_unified_corpus() -> str:
    """Build the final unified training corpus.

    Returns:
        Path to the output JSONL file.
    """
    logger.info("🚀 Building unified OncoAgent training corpus...")
    logger.info("=" * 60)

    real = load_real_data()
    synthetic = load_synthetic_data()

    combined = real + synthetic
    random.shuffle(combined)

    os.makedirs(os.path.dirname(FINAL_OUTPUT), exist_ok=True)

    with open(FINAL_OUTPUT, "w", encoding="utf-8") as f:
        for entry in combined:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Statistics
    source_counts: Dict[str, int] = {}
    for e in combined:
        src = e.get("source", "unknown")
        source_counts[src] = source_counts.get(src, 0) + 1

    logger.info(f"📊 UNIFIED CORPUS BUILT — {len(combined):,} total samples")
    for src, cnt in sorted(source_counts.items(), key=lambda x: -x[1]):
        pct = (cnt / len(combined)) * 100
        logger.info(f"   ├── {src}: {cnt:,} ({pct:.1f}%)")
    logger.info(f"   └── Output: {FINAL_OUTPUT}")
    logger.info("=" * 60)

    return FINAL_OUTPUT


if __name__ == "__main__":
    build_unified_corpus()
