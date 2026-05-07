"""
OncoAgent — GPU-Accelerated Synthetic Oncology Data Generator (MI300X Edition).

Generates 100,000+ SOTA clinical oncology cases using Qwen3.6-27B served
locally via vLLM on AMD Instinct MI300X. Zero API cost, zero concurrency
limits, ~100x faster than cloud API generation.

Architecture:
  - Same combinatorial diversity matrices (129,600 unique profiles)
  - 50 rotating system prompt templates
  - Dynamic few-shot exemplar selection from real data
  - Inline quality validation (schema, length, staging, dedup)
  - Checkpoint/resume support
  - 64 async workers with continuous batching via vLLM

Hardware: AMD Instinct MI300X (192GB HBM3) via local vLLM server.
Rule Compliance: #22 (seeds), #24 (.env), #26 (type hints), #28 (anti-hallucination).
"""

import asyncio
import hashlib
import json
import logging
import os
import random
import time
from itertools import product
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

# ── Reproducibility ─────────────────────────────────────────────────────────
random.seed(42)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Configuration ───────────────────────────────────────────────────────────
MODEL: str = "Qwen/Qwen3.6-27B"
VLLM_BASE_URL: str = os.getenv("VLLM_BASE_URL", "http://localhost:8001/v1")
VLLM_API_KEY: str = os.getenv("VLLM_API_KEY", "not-needed")  # vLLM local needs no key
NUM_WORKERS: int = int(os.getenv("NUM_WORKERS", "64"))
CASES_PER_BATCH: int = 5
TARGET_TOTAL: int = int(os.getenv("TARGET_TOTAL", "100000"))
OUTPUT_DIR: str = os.path.join("data", "synthetic")
CHECKPOINT_FILE: str = os.path.join(OUTPUT_DIR, "generation_checkpoint.json")
MAX_RETRIES: int = 5
RETRY_BACKOFF: float = 1.5
CHECKPOINT_INTERVAL: int = 50  # batches between checkpoints
PROGRESS_INTERVAL: int = 20   # batches between progress logs

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Diversity Matrices ──────────────────────────────────────────────────────
CANCER_TYPES: List[str] = [
    "Non-small cell lung cancer (NSCLC)", "Small cell lung cancer (SCLC)",
    "Breast cancer", "Colorectal cancer", "Prostate cancer",
    "Esophageal cancer", "Hepatocellular carcinoma",
    "Pancreatic adenocarcinoma", "Thyroid cancer", "Gastric cancer",
    "Melanoma", "Bladder cancer", "Renal cell carcinoma",
    "Ovarian cancer", "Endometrial cancer", "Cervical cancer",
    "Testicular cancer", "Glioblastoma multiforme",
    "Diffuse large B-cell lymphoma", "Hodgkin lymphoma",
    "Acute myeloid leukemia", "Multiple myeloma",
    "Soft tissue sarcoma", "Mesothelioma", "Head and neck squamous cell carcinoma",
]

RISK_LEVELS: List[str] = ["High", "Medium", "Low"]

AGE_RANGES: List[str] = ["18-30", "31-45", "46-55", "56-65", "66-75", "76+"]

SEXES: List[str] = ["Male", "Female", "Non-specified"]

STAGING_SYSTEMS: List[str] = [
    "AJCC/TNM 8th Edition", "BCLC (Barcelona Clinic Liver Cancer)",
    "FIGO (gynecologic)", "Ann Arbor (lymphoma)", "Rai/Binet (leukemia)",
]

PRESENTATION_MODES: List[str] = [
    "Primary symptom presentation", "Incidental finding on imaging",
    "Screening program detection", "Post-treatment follow-up recurrence",
]

COMORBIDITIES: List[str] = [
    "None", "Type 2 Diabetes Mellitus", "Hypertension",
    "COPD", "HIV/AIDS", "Chronic Hepatitis B/C",
    "Chronic kidney disease Stage III", "Systemic lupus erythematosus",
]

IMAGING_MODALITIES: List[str] = [
    "CT with contrast", "MRI", "PET-CT (18F-FDG)",
    "Ultrasound", "Mammography", "Endoscopy/EUS",
]

# ── System Prompt Templates (50 variations) ─────────────────────────────────

_BASE_TEMPLATES: List[str] = [
    "You are a senior oncologist writing a detailed clinical case report. Generate a realistic oncology case with: (1) patient history, (2) temporal-causal diagnostic reasoning with explicit staging, (3) evidence-based treatment recommendations.",
    "You are an oncology fellow presenting a case at tumor board. Create a structured clinical case with presenting symptoms, workup findings, pathology results, staging assessment, and multidisciplinary treatment plan.",
    "You are a radiation oncology consultant documenting a referral case. Write a clinical case including the patient's cancer history, current imaging findings, molecular markers, staging, and your treatment recommendation.",
    "You are an oncology surgeon writing a preoperative assessment. Document a cancer case with surgical candidacy evaluation, staging workup results, and operative plan with alternatives.",
    "You are an emergency medicine physician identifying a potential cancer case. Write an ED encounter note with red-flag symptoms, initial workup, and urgent oncology referral reasoning.",
    "Generate a complex oncology case with multiple differential diagnoses that must be systematically ruled out before arriving at the final cancer diagnosis and staging.",
    "Create an oncology case where initial imaging is ambiguous and requires a stepwise diagnostic approach (biopsy, molecular testing, repeat imaging) before definitive staging.",
    "Generate a straightforward oncology case with classic textbook presentation, clear imaging findings, and unambiguous staging per AJCC/TNM criteria.",
    "Create a challenging oncology case with contradictory findings (e.g., low tumor markers but suspicious imaging) requiring clinical judgment for staging.",
    "Generate an oncology case involving a rare cancer presentation in an atypical demographic, emphasizing the importance of maintaining a broad differential.",
]


def _build_prompt_templates() -> List[str]:
    """Generate 50 unique system prompt templates by combining styles."""
    templates: List[str] = list(_BASE_TEMPLATES)
    suffixes = [
        " Cite NCCN guidelines where applicable.",
        " Reference ESMO clinical practice guidelines.",
        " Include relevant biomarker and molecular profiling results.",
        " Emphasize the role of imaging in the diagnostic workup.",
        " Discuss the patient's performance status and treatment tolerance.",
    ]
    for base in _BASE_TEMPLATES[:8]:
        for suffix in suffixes:
            candidate = base + suffix
            if candidate not in templates:
                templates.append(candidate)
            if len(templates) >= 50:
                return templates
    return templates


PROMPT_TEMPLATES: List[str] = _build_prompt_templates()


def _build_combination_pool() -> List[Dict[str, str]]:
    """Build the full combinatorial pool of unique clinical profiles."""
    combos = list(product(
        CANCER_TYPES, RISK_LEVELS, AGE_RANGES, SEXES,
        PRESENTATION_MODES, COMORBIDITIES, IMAGING_MODALITIES,
    ))
    random.shuffle(combos)
    pool: List[Dict[str, str]] = []
    for c in combos:
        pool.append({
            "cancer_type": c[0], "risk_level": c[1],
            "age_range": c[2], "sex": c[3],
            "presentation": c[4], "comorbidity": c[5],
            "imaging": c[6],
        })
    return pool


# ── Few-Shot Exemplar Loading ───────────────────────────────────────────────

def load_real_exemplars(path: str = "data/filtered/onco_real_filtered.jsonl",
                        max_exemplars: int = 200) -> List[str]:
    """Load real oncology cases to use as few-shot references."""
    exemplars: List[str] = []
    fallback = os.path.join("data", "samples", "oncocot_synthetic.json")

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= max_exemplars:
                    break
                try:
                    entry = json.loads(line)
                    exemplars.append(entry.get("text", "")[:800])
                except json.JSONDecodeError:
                    continue
    elif os.path.exists(fallback):
        with open(fallback, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data[:max_exemplars]:
                exemplars.append(json.dumps(item, ensure_ascii=False)[:800])

    if not exemplars:
        exemplars = [
            '{"history":"62yo female, dry cough 3mo, weight loss 8kg, hemoptysis. CT: 2.5cm spiculated mass LUL.","reasoning":"Spiculated mass + hemoptysis + smoking = high suspicion NSCLC. T2aN2M0 Stage IIIA.","conclusion":"Urgent biopsy + PET-CT. MDT referral."}',
            '{"history":"55yo male, 3.5cm right breast mass, skin dimpling, axillary LAD. Mammo: BI-RADS 5.","reasoning":"Male breast mass + BRCA2 family hx. T2N1M0 Stage IIB.","conclusion":"Core biopsy with ER/PR/HER2. BRCA testing."}',
        ]

    logger.info(f"📚 Loaded {len(exemplars)} real exemplars for few-shot prompting.")
    return exemplars


# ── Prompt Construction ─────────────────────────────────────────────────────

def build_generation_prompt(
    profiles: List[Dict[str, str]],
    exemplars: List[str],
) -> Tuple[str, str]:
    """Build system + user prompt for a batch of cases."""
    system = random.choice(PROMPT_TEMPLATES)

    selected = random.sample(exemplars, min(2, len(exemplars)))
    exemplar_block = "\n---\n".join(selected)

    profile_descriptions = []
    for i, p in enumerate(profiles, 1):
        desc = (
            f"Case {i}: {p['cancer_type']}, {p['risk_level']} risk, "
            f"{p['sex']} patient aged {p['age_range']}, "
            f"presenting via {p['presentation'].lower()}, "
            f"comorbidity: {p['comorbidity']}, "
            f"primary imaging: {p['imaging']}."
        )
        profile_descriptions.append(desc)

    user_prompt = f"""Generate {len(profiles)} unique oncology clinical cases based on these profiles.

REFERENCE STYLE (use similar depth and medical rigor):
{exemplar_block}

PROFILES TO GENERATE:
{chr(10).join(profile_descriptions)}

OUTPUT FORMAT — Return a JSON array with exactly {len(profiles)} objects. Each object MUST have:
- "history": Patient presentation (symptoms, imaging findings, labs, risk factors). 150-300 words.
- "reasoning": Step-by-step temporal-causal diagnostic reasoning with explicit staging (TNM/AJCC or appropriate system). 150-250 words. Number each step.
- "conclusion": Final assessment with risk level, recommended workup, and treatment plan citing guidelines. 50-100 words.

CRITICAL RULES:
- Each case MUST include explicit cancer staging (e.g., T2N1M0, Stage IIIA).
- Use real medical terminology, imaging criteria (BI-RADS, PI-RADS, LI-RADS, Fleischner), and biomarkers.
- If information is insufficient for staging, explicitly state "staging pending further workup".
- NEVER invent drug names or staging systems. Use only real, published guidelines.
- Return ONLY the JSON array, no markdown fences or additional text."""

    return system, user_prompt


# ── Quality Validation ──────────────────────────────────────────────────────

_STAGING_KEYWORDS = [
    "stage", "tnm", "t1", "t2", "t3", "t4", "n0", "n1", "n2", "n3",
    "m0", "m1", "ajcc", "figo", "bclc", "ann arbor", "rai", "binet",
    "gleason", "breslow", "staging pending",
]
_STAGING_PATTERN = "|".join(_STAGING_KEYWORDS)

# Thread-safe dedup set for async context
_seen_hashes: set = set()
_hash_lock = asyncio.Lock()


async def validate_case(case: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate a single generated case for SOTA quality."""
    for field in ("history", "reasoning", "conclusion"):
        if field not in case or not isinstance(case[field], str):
            return False, f"missing_field:{field}"

    if len(case["reasoning"].split()) < 40:
        return False, "reasoning_too_short"

    if len(case["history"].split()) < 30:
        return False, "history_too_short"

    combined = f"{case['reasoning']} {case['conclusion']}".lower()
    import re
    if not re.search(_STAGING_PATTERN, combined, re.IGNORECASE):
        return False, "no_staging_reference"

    hash_input = case["history"][:200].lower().strip()
    h = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    async with _hash_lock:
        if h in _seen_hashes:
            return False, "duplicate"
        _seen_hashes.add(h)

    return True, "ok"


# ── API Call with Retry ─────────────────────────────────────────────────────

async def generate_batch(
    client: AsyncOpenAI,
    system: str,
    user_prompt: str,
    worker_id: int,
) -> Optional[List[Dict[str, Any]]]:
    """Call the local vLLM server and parse the JSON response."""
    for attempt in range(MAX_RETRIES):
        try:
            response = await client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.85,
                max_tokens=6000,
                top_p=0.95,
                extra_body={
                    "chat_template_kwargs": {"enable_thinking": False},
                },
            )
            content = response.choices[0].message.content.strip()

            # Strip markdown fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # Handle think tags from Qwen3.6
            if "<think>" in content:
                import re as _re
                content = _re.sub(r"<think>.*?</think>", "", content, flags=_re.DOTALL).strip()

            cases = json.loads(content)
            if isinstance(cases, list):
                return cases
            elif isinstance(cases, dict):
                return [cases]

        except json.JSONDecodeError:
            logger.warning(f"[W{worker_id}] JSON parse error (attempt {attempt+1})")
        except Exception as e:
            wait = RETRY_BACKOFF ** (attempt + 1)
            logger.warning(f"[W{worker_id}] API error: {e}. Retrying in {wait:.0f}s...")
            await asyncio.sleep(wait)

    return None


# ── Worker Coroutine ────────────────────────────────────────────────────────

async def worker(
    worker_id: int,
    client: AsyncOpenAI,
    semaphore: asyncio.Semaphore,
    task_queue: asyncio.Queue,
    results: List[Dict[str, Any]],
    stats: Dict[str, int],
    exemplars: List[str],
    results_lock: asyncio.Lock,
    stats_lock: asyncio.Lock,
):
    """Async worker that pulls profile batches from the queue and generates cases."""
    while True:
        try:
            batch_profiles = task_queue.get_nowait()
        except asyncio.QueueEmpty:
            break

        async with semaphore:
            system, user_prompt = build_generation_prompt(batch_profiles, exemplars)
            cases = await generate_batch(client, system, user_prompt, worker_id)

        if cases:
            valid_count = 0
            for case in cases:
                is_valid, reason = await validate_case(case)
                if is_valid:
                    async with results_lock:
                        results.append(case)
                    valid_count += 1
                else:
                    async with stats_lock:
                        stats["rejected"] = stats.get("rejected", 0) + 1
                        stats[f"reject_{reason}"] = stats.get(f"reject_{reason}", 0) + 1

            async with stats_lock:
                stats["generated"] = stats.get("generated", 0) + valid_count
        else:
            async with stats_lock:
                stats["api_failures"] = stats.get("api_failures", 0) + 1

        async with stats_lock:
            stats["batches_done"] = stats.get("batches_done", 0) + 1
            batches_done = stats["batches_done"]

        # Progress log
        if batches_done % PROGRESS_INTERVAL == 0:
            async with stats_lock:
                total_gen = stats.get("generated", 0)
                total_rej = stats.get("rejected", 0)
            pct = (total_gen / TARGET_TOTAL) * 100
            elapsed = time.time() - stats.get("_start_time", time.time())
            rate = total_gen / max(elapsed, 1) * 3600
            logger.info(
                f"[W{worker_id}] Progress: {total_gen:,}/{TARGET_TOTAL:,} "
                f"({pct:.1f}%) | Rejected: {total_rej:,} | "
                f"Batches: {batches_done:,} | Rate: {rate:,.0f} cases/hr"
            )

        # Checkpoint
        if batches_done % CHECKPOINT_INTERVAL == 0:
            async with results_lock:
                save_checkpoint(list(results), stats)

        task_queue.task_done()


# ── Checkpoint ──────────────────────────────────────────────────────────────

def save_checkpoint(results: List[Dict[str, Any]], stats: Dict[str, int]) -> None:
    """Save progress to disk."""
    batch_file = os.path.join(OUTPUT_DIR, f"generated_{len(results):06d}.jsonl")
    with open(batch_file, "w", encoding="utf-8") as f:
        for case in results:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    clean_stats = {k: v for k, v in stats.items() if not k.startswith("_")}
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({
            "total_generated": len(results),
            "stats": clean_stats,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }, f, indent=2)

    logger.info(f"💾 Checkpoint: {len(results):,} cases saved.")


def load_checkpoint() -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Load previous checkpoint if it exists."""
    results: List[Dict[str, Any]] = []
    stats: Dict[str, int] = {"generated": 0, "rejected": 0, "batches_done": 0}

    if not os.path.exists(CHECKPOINT_FILE):
        return results, stats

    with open(CHECKPOINT_FILE, "r") as f:
        cp = json.load(f)

    stats = cp.get("stats", stats)
    total = cp.get("total_generated", 0)

    gen_files = sorted(
        [f for f in os.listdir(OUTPUT_DIR) if f.startswith("generated_")],
        reverse=True,
    )
    if gen_files:
        latest = os.path.join(OUTPUT_DIR, gen_files[0])
        with open(latest, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        for case in results:
            h_input = case.get("history", "")[:200].lower().strip()
            _seen_hashes.add(hashlib.sha256(h_input.encode()).hexdigest()[:16])

    logger.info(f"🔄 Resumed from checkpoint: {len(results):,} cases loaded.")
    return results, stats


# ── Main Orchestrator ───────────────────────────────────────────────────────

async def run_generation(target: int = TARGET_TOTAL) -> str:
    """Orchestrate parallel generation via local vLLM on MI300X."""

    logger.info("=" * 60)
    logger.info("🔥 OncoAgent GPU-Accelerated Synthetic Generator")
    logger.info(f"   Hardware: AMD Instinct MI300X (192GB HBM3)")
    logger.info(f"   Engine:   vLLM with PagedAttention")
    logger.info(f"   Model:    {MODEL}")
    logger.info(f"   Workers:  {NUM_WORKERS}")
    logger.info(f"   Target:   {target:,} cases")
    logger.info(f"   Server:   {VLLM_BASE_URL}")
    logger.info("=" * 60)

    # Single client pointing to local vLLM
    client = AsyncOpenAI(
        api_key=VLLM_API_KEY,
        base_url=VLLM_BASE_URL,
    )

    # Verify vLLM is up
    try:
        models = await client.models.list()
        available = [m.id for m in models.data]
        logger.info(f"✅ vLLM server online. Available models: {available}")
    except Exception as e:
        logger.error(f"❌ Cannot reach vLLM server at {VLLM_BASE_URL}: {e}")
        logger.error("   Make sure vLLM Docker container is running.")
        raise SystemExit(1)

    semaphore = asyncio.Semaphore(NUM_WORKERS)

    # Load exemplars and checkpoint
    exemplars = load_real_exemplars()
    results, stats = load_checkpoint()
    already_generated = len(results)
    remaining = max(0, target - already_generated)

    if remaining == 0:
        logger.info(f"✅ Target already reached ({already_generated:,} cases).")
        return os.path.join(OUTPUT_DIR, f"generated_{already_generated:06d}.jsonl")

    # Build combination pool and task queue
    combo_pool = _build_combination_pool()
    num_batches = (remaining // CASES_PER_BATCH) + 1

    task_queue: asyncio.Queue = asyncio.Queue()
    for i in range(num_batches):
        batch_profiles = []
        for j in range(CASES_PER_BATCH):
            idx = (i * CASES_PER_BATCH + j) % len(combo_pool)
            batch_profiles.append(combo_pool[idx])
        task_queue.put_nowait(batch_profiles)

    logger.info(f"🚀 Starting generation: {remaining:,} cases in {num_batches:,} batches")
    logger.info(f"   Batches per worker: ~{num_batches // NUM_WORKERS:,}")

    start_time = time.time()
    stats["_start_time"] = start_time

    results_lock = asyncio.Lock()
    stats_lock = asyncio.Lock()

    # Launch workers
    tasks = []
    for w_id in range(NUM_WORKERS):
        tasks.append(
            asyncio.create_task(
                worker(w_id, client, semaphore, task_queue,
                       results, stats, exemplars, results_lock, stats_lock)
            )
        )

    await asyncio.gather(*tasks)

    elapsed = time.time() - start_time
    hours = elapsed / 3600

    # Final save
    save_checkpoint(results, stats)

    # Final consolidated output
    final_path = os.path.join(OUTPUT_DIR, "onco_synthetic_final.jsonl")
    with open(final_path, "w", encoding="utf-8") as f:
        for case in results:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    rate = len(results) / max(hours, 0.001)

    logger.info("=" * 60)
    logger.info(f"🏁 GENERATION COMPLETE")
    logger.info(f"   Total valid cases: {len(results):,}")
    logger.info(f"   Rejected: {stats.get('rejected', 0):,}")
    logger.info(f"   API failures: {stats.get('api_failures', 0):,}")
    logger.info(f"   Time: {hours:.1f} hours")
    logger.info(f"   Effective rate: {rate:,.0f} cases/hour")
    logger.info(f"   Output: {final_path}")
    logger.info("=" * 60)

    return final_path


def main() -> None:
    """Entry point."""
    asyncio.run(run_generation())


if __name__ == "__main__":
    main()
