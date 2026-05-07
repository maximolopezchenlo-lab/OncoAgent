"""
OncoAgent — Dataset Builder / Unifier.

Combines real (HuggingFace-filtered) and synthetic (Qwen generated)
oncology data into a single training-ready JSONL corpus in ChatML
chat template format.

Hardware Target: CPU only.
Rule Compliance: #12 (JSONL + ChatML format), #22 (seeds), #26 (type hints).
"""

import json
import os
import random
import logging
import hashlib
from typing import Dict, List, Tuple

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


def format_synthetic_to_chatml(case: Dict[str, str]) -> str:
    """Convert a synthetic case dict to ChatML template.

    Args:
        case: Dict with 'history', 'reasoning', 'conclusion' keys.

    Returns:
        Formatted ChatML template string.
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
        f"<|im_start|>system\n"
        f"{SYSTEM_PROMPT}<|im_end|>\n"
        f"<|im_start|>user\n"
        f"{user_msg}<|im_end|>\n"
        f"<|im_start|>assistant\n"
        f"{assistant_msg}<|im_end|>"
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
    """Load all synthetic generated data and format to ChatML."""
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
                    formatted = format_synthetic_to_chatml(case)
                    entries.append({
                        "text": formatted,
                        "source": "synthetic_qwen",
                    })
                except (json.JSONDecodeError, KeyError):
                    continue

    logger.info(f"🧬 Loaded {len(entries):,} synthetic oncology samples")
    return entries


def _compute_corpus_hash(entries: List[Dict[str, str]]) -> str:
    """Compute a deterministic hash of the corpus for reproducibility tracking.

    Args:
        entries: List of training entries.

    Returns:
        SHA-256 hex digest (first 12 chars).
    """
    h = hashlib.sha256()
    for e in entries:
        h.update(e.get("text", "").encode("utf-8"))
    return h.hexdigest()[:12]


def build_unified_corpus(
    eval_ratio: float = 0.10,
) -> Tuple[str, str]:
    """Build the final unified training corpus with a train/eval split.

    Args:
        eval_ratio: Fraction of samples reserved for evaluation (default 10%).

    Returns:
        Tuple of (train_path, eval_path).
    """
    logger.info("🚀 Building unified OncoAgent training corpus...")
    logger.info("=" * 60)

    real = load_real_data()
    synthetic = load_synthetic_data()

    combined = real + synthetic
    random.shuffle(combined)

    # Deduplicate by text content
    seen_hashes: set = set()
    deduped: List[Dict[str, str]] = []
    for entry in combined:
        text_hash = hashlib.sha256(entry.get("text", "").encode()).hexdigest()
        if text_hash not in seen_hashes:
            seen_hashes.add(text_hash)
            deduped.append(entry)
    if len(deduped) < len(combined):
        logger.info(f"🧹 Deduplication: removed {len(combined) - len(deduped):,} duplicate samples")
    combined = deduped

    # Train/eval split
    split_idx = max(1, int(len(combined) * (1.0 - eval_ratio)))
    train_set = combined[:split_idx]
    eval_set = combined[split_idx:]

    os.makedirs(os.path.dirname(FINAL_OUTPUT), exist_ok=True)
    eval_output = FINAL_OUTPUT.replace(".jsonl", "_eval.jsonl")

    for path, entries in [(FINAL_OUTPUT, train_set), (eval_output, eval_set)]:
        with open(path, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Statistics
    source_counts: Dict[str, int] = {}
    for e in combined:
        src = e.get("source", "unknown")
        source_counts[src] = source_counts.get(src, 0) + 1

    corpus_hash = _compute_corpus_hash(combined)
    logger.info(f"📊 UNIFIED CORPUS BUILT — {len(combined):,} total samples")
    logger.info(f"   ├── Train: {len(train_set):,} ({100*(1-eval_ratio):.0f}%)")
    logger.info(f"   ├── Eval:  {len(eval_set):,} ({100*eval_ratio:.0f}%)")
    for src, cnt in sorted(source_counts.items(), key=lambda x: -x[1]):
        pct = (cnt / len(combined)) * 100
        logger.info(f"   ├── {src}: {cnt:,} ({pct:.1f}%)")
    logger.info(f"   ├── Corpus hash: {corpus_hash}")
    logger.info(f"   ├── Train output: {FINAL_OUTPUT}")
    logger.info(f"   └── Eval output:  {eval_output}")
    logger.info("=" * 60)

    return FINAL_OUTPUT, eval_output


if __name__ == "__main__":
    build_unified_corpus()
