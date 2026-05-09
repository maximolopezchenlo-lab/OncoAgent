"""
Shared vLLM client and tier-aware model calling utilities.

All LLM inference across OncoAgent flows through this module,
ensuring consistent model selection, error handling, and
environment variable management.

Design inspired by:
  - Hermes Agent: structured tool calling with JSON output
  - Claude Code: deterministic harness separating LLM from execution
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from openai import OpenAI
from dotenv import load_dotenv

# Conditional imports for local adapter inference
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    import torch
    HAS_LOCAL_INFERENCE = True
except ImportError:
    HAS_LOCAL_INFERENCE = False

load_dotenv()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tier Configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TierSpec:
    """Immutable specification for a model tier."""

    tier_id: int
    name: str
    model_id: str
    description: str
    max_tokens: int
    temperature: float

    def __str__(self) -> str:
        return f"Tier {self.tier_id}: {self.name} ({self.model_id})"


# Production tier definitions
TIER_SPECS: Dict[int, TierSpec] = {
    1: TierSpec(
        tier_id=1,
        name="Speed Triage",
        model_id=os.getenv("BASE_MODEL_ID", "Qwen/Qwen3.5-9B"),
        description="Fast local model for initial triage and low-complexity cases.",
        max_tokens=2048,
        temperature=0.1,
    ),
    2: TierSpec(
        tier_id=2,
        name="Deep Reasoning",
        model_id=os.getenv("TIER2_MODEL_ID", "Qwen/Qwen3.6-27B-Instruct"),
        description="High-reasoning model for complex oncology cases and validation.",
        max_tokens=4096,
        temperature=0.0,
    ),
}


# ---------------------------------------------------------------------------
# vLLM Client Singleton
# ---------------------------------------------------------------------------

_vllm_client: Optional[OpenAI] = None


def get_vllm_client() -> OpenAI:
    """Return a cached OpenAI-compatible client pointing at vLLM.

    Reads ``VLLM_API_BASE`` and ``VLLM_API_KEY`` from environment.

    Returns:
        OpenAI client configured for the local vLLM server.
    """
    global _vllm_client
    if _vllm_client is None:
        api_base = os.getenv("VLLM_API_BASE", "http://localhost:8000/v1")
        api_key = os.getenv("VLLM_API_KEY", "EMPTY")
        _vllm_client = OpenAI(base_url=api_base, api_key=api_key)
        logger.info("vLLM client initialised → %s", api_base)
    return _vllm_client


# ---------------------------------------------------------------------------
# Local Adapter Manager (PEFT/Unsloth)
# ---------------------------------------------------------------------------

class LocalModelManager:
    """Singleton to manage local LoRA model loading and inference."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalModelManager, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.tokenizer = None
            cls._instance.initialized = False
        return cls._instance

    def initialize(self):
        """Load the base model and LoRA adapters."""
        if self.initialized:
            return

        if not HAS_LOCAL_INFERENCE:
            logger.warning("Transformers/Torch not found. Local inference disabled.")
            return

        adapter_path = os.getenv("LOCAL_ADAPTER_PATH")
        base_model_id = os.getenv("BASE_MODEL_ID", "Qwen/Qwen3.5-9B")

        if not adapter_path or not os.path.exists(adapter_path):
            logger.error("Local adapter path not found: %s", adapter_path)
            return

        logger.info("Loading local base model %s and adapters from %s...", base_model_id, adapter_path)
        try:
            # 1. Load Tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(base_model_id, trust_remote_code=True)
            
            # 2. Load Base Model in BF16
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_id,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                trust_remote_code=True,
            )
            
            # 3. Load LoRA Adapters
            self.model = PeftModel.from_pretrained(base_model, adapter_path)
            self.model.eval()
            
            self.initialized = True
            logger.info("Local BF16 model initialized successfully on %s", os.getenv("DEVICE", "cuda"))
        except Exception as e:
            logger.error("Failed to load local model: %s", e)

    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float) -> str:
        """Run inference using the loaded local model."""
        if not self.initialized:
            self.initialize()
        
        if not self.initialized:
            raise RuntimeError("Local model manager requested but not initialized.")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        prompt_str = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        logger.debug("Local prompt: %s", prompt_str)

        inputs = self.tokenizer(text=prompt_str, return_tensors="pt").to("cuda")

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                use_cache=True,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        
        # Extract only the generated part
        generated_ids = outputs[:, inputs.input_ids.shape[1]:]
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return response.strip()


_local_manager = LocalModelManager()


# ---------------------------------------------------------------------------
# Tier-Aware Model Calling
# ---------------------------------------------------------------------------

def call_tier_model(
    tier: int,
    system_prompt: str,
    user_prompt: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    json_mode: bool = False,
) -> str:
    """Call the appropriate model based on the selected tier.

    This is the *single entry point* for all LLM inference in OncoAgent.
    Every node must call this function instead of instantiating clients.

    Args:
        tier: Model tier (1 = fast 9B, 2 = deep 27B).
        system_prompt: System-level instructions.
        user_prompt: User-level content / query.
        max_tokens: Override the tier's default max_tokens.
        temperature: Override the tier's default temperature.
        json_mode: If True, request JSON response format.

    Returns:
        The model's text response (stripped).

    Raises:
        ValueError: If the tier is not 1 or 2.
        RuntimeError: If the vLLM server is unreachable.
    """
    spec = TIER_SPECS.get(tier)
    if spec is None:
        raise ValueError(f"Invalid tier {tier}. Must be 1 or 2.")

    effective_max_tokens = max_tokens or spec.max_tokens
    effective_temperature = temperature if temperature is not None else spec.temperature

    logger.info(
        "Calling %s (max_tokens=%d, temp=%.2f, json=%s)",
        spec, effective_max_tokens, effective_temperature, json_mode,
    )

    # Check if we should use local adapters for Tier 1
    use_local = os.getenv("USE_LOCAL_ADAPTERS", "false").lower() == "true"
    if tier == 1 and use_local and HAS_LOCAL_INFERENCE:
        try:
            logger.info("Routing Tier 1 call to local LoRA adapters...")
            return _local_manager.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=effective_max_tokens,
                temperature=effective_temperature
            )
        except Exception as local_exc:
            logger.warning("Local inference failed, falling back to API: %s", local_exc)

    try:
        client = get_vllm_client()

        kwargs: Dict[str, Any] = {
            "model": spec.model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": effective_temperature,
            "max_tokens": effective_max_tokens,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**kwargs)
        text = response.choices[0].message.content.strip()
        logger.debug("Response length: %d chars", len(text))
        return text

    except Exception as exc:
        logger.error("vLLM call failed for %s: %s", spec, exc)
        raise RuntimeError(
            f"Error connecting to vLLM ({spec.model_id}): {exc}"
        ) from exc


def get_tier_spec(tier: int) -> TierSpec:
    """Retrieve the TierSpec for the given tier number.

    Args:
        tier: 1 or 2.

    Returns:
        The corresponding TierSpec.
    """
    spec = TIER_SPECS.get(tier)
    if spec is None:
        raise ValueError(f"Invalid tier {tier}. Available: {list(TIER_SPECS.keys())}")
    return spec
