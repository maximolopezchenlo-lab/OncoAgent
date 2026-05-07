"""
OncoAgent — HuggingFace Dataset Acquisition & Oncological Filtering Pipeline.

Downloads 5 SOTA medical datasets, applies strict oncology keyword filtering,
and exports results in Llama 3.1 chat-template JSONL format.

Hardware Target: CPU (data prep phase — no GPU required).
Rule Compliance: #22 (reproducibility seeds), #24 (.env secrets), #26 (type hints).
"""

import json
import os
import re
import random
import logging
from typing import List, Dict, Optional, Set

from datasets import load_dataset, Dataset
from dotenv import load_dotenv

load_dotenv()

# ── Reproducibility (Rule #22) ──────────────────────────────────────────────
random.seed(42)

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Output Directories ──────────────────────────────────────────────────────
RAW_DIR = os.path.join("data", "raw")
FILTERED_DIR = os.path.join("data", "filtered")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(FILTERED_DIR, exist_ok=True)

# ── Oncology Keyword Filter ────────────────────────────────────────────────
ONCOLOGY_KEYWORDS: Set[str] = {
    # General oncology terms
    "cancer", "tumor", "tumour", "neoplasm", "malignant", "malignancy",
    "carcinoma", "sarcoma", "lymphoma", "leukemia", "leukaemia", "myeloma",
    "melanoma", "glioma", "glioblastoma", "mesothelioma", "adenocarcinoma",
    "metastasis", "metastatic", "metastases",
    # Staging & grading
    "staging", "tnm", "ajcc", "figo", "bclc", "ann arbor",
    "gleason", "breslow", "clark level",
    "stage i", "stage ii", "stage iii", "stage iv",
    "grade 1", "grade 2", "grade 3", "grade 4",
    # Treatment
    "chemotherapy", "radiotherapy", "radiation therapy", "immunotherapy",
    "targeted therapy", "hormone therapy", "surgical resection",
    "mastectomy", "lobectomy", "colectomy", "prostatectomy",
    "folfox", "folfiri", "cisplatin", "carboplatin", "pembrolizumab",
    "nivolumab", "atezolizumab", "bevacizumab", "trastuzumab",
    # Diagnostics
    "biopsy", "histopathology", "cytology", "pet-ct", "pet scan",
    "mammography", "colonoscopy", "endoscopy",
    "bi-rads", "pi-rads", "li-rads", "fleischner",
    "ca 19-9", "ca-125", "cea", "afp", "psa",
    # Molecular markers
    "brca", "her2", "egfr", "alk", "kras", "braf", "msi",
    "pd-l1", "microsatellite", "tp53", "rb1",
    # Clinical guidelines
    "nccn", "esmo", "asco", "tumor board",
    # Specific cancers
    "breast cancer", "lung cancer", "colon cancer", "colorectal",
    "prostate cancer", "pancreatic cancer", "liver cancer",
    "hepatocellular", "esophageal", "gastric cancer",
    "ovarian cancer", "cervical cancer", "thyroid cancer",
    "bladder cancer", "renal cell", "testicular cancer",
    "head and neck cancer", "nsclc", "sclc",
}

# Pre-compile a single regex pattern for fast matching
_ONCO_PATTERN = re.compile(
    "|".join(re.escape(kw) for kw in ONCOLOGY_KEYWORDS),
    re.IGNORECASE,
)


def is_oncology_relevant(text: str, min_matches: int = 1) -> bool:
    """Check if text contains oncology-relevant keywords.

    Args:
        text: The input text to check.
        min_matches: Minimum number of keyword matches required.

    Returns:
        True if the text is oncology-relevant.
    """
    if not text:
        return False
    matches = _ONCO_PATTERN.findall(text)
    return len(matches) >= min_matches


# ── Llama 3.1 Chat Templates ───────────────────────────────────────────────

def format_llama3_chat(
    system_msg: str,
    user_msg: str,
    assistant_msg: str,
) -> str:
    """Format a conversation into strict Llama 3.1 chat template.

    Args:
        system_msg: The system prompt defining the assistant's role.
        user_msg: The user's clinical input.
        assistant_msg: The assistant's expert response.

    Returns:
        Formatted string in Llama 3.1 chat template.
    """
    return (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
        f"{system_msg}<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n\n"
        f"{user_msg}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n"
        f"{assistant_msg}<|eot_id|>"
    )


# ── Dataset Processors ─────────────────────────────────────────────────────

SYSTEM_PROMPT_ONCOLOGIST = (
    "You are an expert clinical oncologist specializing in cancer triage. "
    "Analyze the patient's clinical presentation using temporal-causal "
    "reasoning (OncoCoT). Provide: (1) key findings, (2) step-by-step "
    "diagnostic reasoning with staging, and (3) evidence-based recommendations "
    "citing NCCN/ESMO guidelines where applicable."
)


def process_pmc_patients(max_samples: Optional[int] = None) -> List[Dict[str, str]]:
    """Download and filter PMC-Patients for oncology cases.

    Args:
        max_samples: Optional limit on number of samples to process.

    Returns:
        List of formatted JSONL entries.
    """
    logger.info("📥 Downloading PMC-Patients (zhengyun21/PMC-Patients)...")
    try:
        dataset = load_dataset("zhengyun21/PMC-Patients", split="train")
    except Exception as e:
        logger.error(f"Failed to download PMC-Patients: {e}")
        return []

    results: List[Dict[str, str]] = []
    total = len(dataset)
    filtered = 0

    for i, item in enumerate(dataset):
        patient_text = item.get("patient", "")
        if not is_oncology_relevant(patient_text, min_matches=2):
            continue

        formatted = format_llama3_chat(
            system_msg=SYSTEM_PROMPT_ONCOLOGIST,
            user_msg=f"Patient Summary:\n{patient_text}",
            assistant_msg=(
                f"Patient UID: {item.get('patient_uid', 'N/A')}.\n\n"
                f"Clinical Analysis: This patient presents with findings "
                f"requiring oncological evaluation. A systematic review of "
                f"the clinical presentation, imaging, and laboratory findings "
                f"is necessary for proper staging and treatment planning."
            ),
        )
        results.append({"text": formatted, "source": "pmc_patients"})
        filtered += 1

        if max_samples and filtered >= max_samples:
            break

    logger.info(f"✅ PMC-Patients: {filtered}/{total} oncology-relevant cases extracted.")
    return results


def process_asclepius_notes(max_samples: Optional[int] = None) -> List[Dict[str, str]]:
    """Download and filter Asclepius Synthetic Clinical Notes.

    Args:
        max_samples: Optional limit on number of samples.

    Returns:
        List of formatted JSONL entries.
    """
    logger.info("📥 Downloading Asclepius Clinical Notes (starmpcc/Asclepius-Synthetic-Clinical-Notes)...")
    try:
        dataset = load_dataset(
            "starmpcc/Asclepius-Synthetic-Clinical-Notes", split="train"
        )
    except Exception as e:
        logger.error(f"Failed to download Asclepius: {e}")
        return []

    results: List[Dict[str, str]] = []
    total = len(dataset)
    filtered = 0

    for item in dataset:
        # Asclepius has 'note' or 'text' field depending on version
        note_text = item.get("note", item.get("text", ""))
        if not is_oncology_relevant(note_text, min_matches=2):
            continue

        formatted = format_llama3_chat(
            system_msg=SYSTEM_PROMPT_ONCOLOGIST,
            user_msg=f"Clinical Note:\n{note_text}",
            assistant_msg=(
                "Oncological Assessment: The clinical note describes findings "
                "consistent with a potential oncological process. Further "
                "evaluation with appropriate imaging, biopsy, and molecular "
                "profiling is recommended for definitive diagnosis and staging."
            ),
        )
        results.append({"text": formatted, "source": "asclepius"})
        filtered += 1

        if max_samples and filtered >= max_samples:
            break

    logger.info(f"✅ Asclepius: {filtered}/{total} oncology-relevant notes extracted.")
    return results


def process_clinical_trial_cancer() -> List[Dict[str, str]]:
    """Download Clinical Trial Cancer v4 dataset (already oncology-focused).

    Returns:
        List of formatted JSONL entries.
    """
    logger.info("📥 Downloading Clinical Trial Cancer v4 (ravistech/clinical-trial-llm-cancer-v4)...")
    try:
        dataset = load_dataset(
            "ravistech/clinical-trial-llm-cancer-v4", split="train"
        )
    except Exception as e:
        logger.error(f"Failed to download Clinical Trial Cancer: {e}")
        return []

    results: List[Dict[str, str]] = []

    for item in dataset:
        # Build context from available fields
        context_parts = []
        for field in ["input", "instruction", "context", "text"]:
            val = item.get(field, "")
            if val:
                context_parts.append(val)

        context = "\n".join(context_parts)
        output = item.get("output", item.get("response", ""))

        if not context or not output:
            continue

        formatted = format_llama3_chat(
            system_msg=SYSTEM_PROMPT_ONCOLOGIST,
            user_msg=context,
            assistant_msg=output,
        )
        results.append({"text": formatted, "source": "clinical_trial_cancer"})

    logger.info(f"✅ Clinical Trial Cancer: {len(results)} entries processed.")
    return results


def process_medical_o1_reasoning(max_samples: Optional[int] = None) -> List[Dict[str, str]]:
    """Download and filter Medical O1 Reasoning SFT dataset.

    Args:
        max_samples: Optional limit on number of samples.

    Returns:
        List of formatted JSONL entries.
    """
    logger.info("📥 Downloading Medical O1 Reasoning (FreedomIntelligence/medical-o1-reasoning-SFT)...")
    try:
        dataset = load_dataset(
            "FreedomIntelligence/medical-o1-reasoning-SFT",
            split="train",
        )
    except Exception as e:
        logger.error(f"Failed to download Medical O1: {e}")
        return []

    results: List[Dict[str, str]] = []
    total = len(dataset)
    filtered = 0

    for item in dataset:
        # This dataset typically has 'question'/'input' and 'response'/'output'
        question = item.get("question", item.get("input", item.get("instruction", "")))
        response = item.get("response", item.get("output", ""))

        combined_text = f"{question} {response}"
        if not is_oncology_relevant(combined_text, min_matches=2):
            continue

        formatted = format_llama3_chat(
            system_msg=(
                "You are an expert clinical oncologist. Use chain-of-thought "
                "reasoning to analyze the following medical scenario step by step. "
                "Consider differential diagnoses, staging criteria, and "
                "evidence-based treatment guidelines."
            ),
            user_msg=question,
            assistant_msg=response,
        )
        results.append({"text": formatted, "source": "medical_o1_reasoning"})
        filtered += 1

        if max_samples and filtered >= max_samples:
            break

    logger.info(f"✅ Medical O1 Reasoning: {filtered}/{total} oncology-relevant entries extracted.")
    return results


def process_pubmed_qa() -> List[Dict[str, str]]:
    """Download PubMedQA labeled split and filter for oncology.

    Returns:
        List of formatted JSONL entries.
    """
    logger.info("📥 Downloading PubMedQA (pubmed_qa, pqa_labeled)...")
    try:
        dataset = load_dataset("pubmed_qa", "pqa_labeled", split="train")
    except Exception as e:
        logger.error(f"Failed to download PubMedQA: {e}")
        return []

    results: List[Dict[str, str]] = []
    total = len(dataset)
    filtered = 0

    for item in dataset:
        question = item.get("question", "")
        context_data = item.get("context", {})
        contexts_list = context_data.get("contexts", [])
        context_str = " ".join(contexts_list) if isinstance(contexts_list, list) else str(contexts_list)
        long_answer = item.get("long_answer", "")
        final_decision = item.get("final_decision", "")

        combined = f"{question} {context_str} {long_answer}"
        if not is_oncology_relevant(combined, min_matches=1):
            continue

        formatted = format_llama3_chat(
            system_msg=SYSTEM_PROMPT_ONCOLOGIST,
            user_msg=f"Context:\n{context_str}\n\nQuestion: {question}",
            assistant_msg=f"{long_answer}\n\nConclusion: {final_decision}",
        )
        results.append({"text": formatted, "source": "pubmed_qa"})
        filtered += 1

    logger.info(f"✅ PubMedQA: {filtered}/{total} oncology-relevant QA pairs extracted.")
    return results


# ── Main Pipeline ───────────────────────────────────────────────────────────

def run_pipeline() -> str:
    """Execute the full dataset acquisition and filtering pipeline.

    Returns:
        Path to the final filtered JSONL file.
    """
    logger.info("🚀 Starting OncoAgent Data Acquisition Pipeline...")
    logger.info("=" * 60)

    all_results: List[Dict[str, str]] = []

    # 1. PMC-Patients (filtered)
    all_results.extend(process_pmc_patients())

    # 2. Asclepius Clinical Notes (filtered)
    all_results.extend(process_asclepius_notes())

    # 3. Clinical Trial Cancer (already oncology)
    all_results.extend(process_clinical_trial_cancer())

    # 4. Medical O1 Reasoning (filtered)
    all_results.extend(process_medical_o1_reasoning())

    # 5. PubMedQA (filtered)
    all_results.extend(process_pubmed_qa())

    # Shuffle for training diversity
    random.shuffle(all_results)

    # Write final filtered output
    output_path = os.path.join(FILTERED_DIR, "onco_real_filtered.jsonl")
    with open(output_path, "w", encoding="utf-8") as f:
        for entry in all_results:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Print statistics
    logger.info("=" * 60)
    logger.info(f"📊 PIPELINE COMPLETE — Total oncology samples: {len(all_results)}")

    source_counts: Dict[str, int] = {}
    for entry in all_results:
        src = entry.get("source", "unknown")
        source_counts[src] = source_counts.get(src, 0) + 1

    for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        logger.info(f"   ├── {src}: {count:,} samples")

    logger.info(f"   └── Output: {output_path}")
    logger.info("=" * 60)

    return output_path


if __name__ == "__main__":
    run_pipeline()
