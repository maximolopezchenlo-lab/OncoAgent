"""
Shared vLLM client and tier-aware model calling utilities.

All LLM inference across OncoAgent flows through this module,
ensuring consistent model selection, error handling, and
environment variable management.

Design inspired by:
  - Hermes Agent: structured tool calling with JSON output
  - Claude Code: deterministic harness separating LLM from execution

Production target: AMD Instinct MI300X via ROCm 7.2 + vLLM
Development fallback: Featherless.ai OpenAI-compatible API
"""

import os
import re
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from openai import OpenAI
from dotenv import load_dotenv

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


# Production tier definitions — Qwen 3.5 / 3.6 as per project rules
TIER_SPECS: Dict[int, TierSpec] = {
    1: TierSpec(
        tier_id=1,
        name="Speed Triage",
        model_id=os.getenv("TIER1_MODEL_ID", "Qwen/Qwen3.5-9B"),
        description="Fast model for initial triage and low-complexity cases.",
        max_tokens=2048,
        temperature=0.1,
    ),
    2: TierSpec(
        tier_id=2,
        name="Deep Reasoning",
        model_id=os.getenv("TIER2_MODEL_ID", "Qwen/Qwen3.6-27B"),
        description="High-reasoning model for complex oncology cases and validation.",
        max_tokens=4096,
        temperature=0.0,
    ),
}


# ---------------------------------------------------------------------------
# Qwen3 Thinking-Mode Handler
# ---------------------------------------------------------------------------

_THINK_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL)


def _strip_thinking_tokens(text: str) -> str:
    """Remove Qwen3 <think>...</think> blocks from model output.

    Qwen3 models use an internal reasoning mode that wraps chain-of-thought
    in <think> tags. We preserve only the final answer for the pipeline.

    Args:
        text: Raw model output potentially containing <think> blocks.

    Returns:
        Cleaned text with thinking blocks removed.
    """
    cleaned = _THINK_PATTERN.sub("", text).strip()
    # If everything was inside <think> tags, return the original
    return cleaned if cleaned else text.strip()


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
# Model ID Resolution (handles Featherless fallback for dev)
# ---------------------------------------------------------------------------

def _resolve_model_id(spec: TierSpec) -> str:
    """Resolve the actual model ID to use for API calls.

    In production (local vLLM), we use the exact model ID.
    In development (Featherless.ai), some models may not be available,
    so we check for configured fallbacks.

    Args:
        spec: The TierSpec for the requested tier.

    Returns:
        The model ID string to pass to the API.
    """
    api_base = os.getenv("VLLM_API_BASE", "http://localhost:8000/v1")
    is_featherless = "featherless" in api_base.lower()

    if is_featherless and spec.tier_id == 2:
        # Qwen3.6-27B is not available on Featherless — use fallback
        fallback = os.getenv("TIER2_FEATHERLESS_FALLBACK", "Qwen/Qwen3.5-27B")
        logger.info(
            "Featherless detected: Tier 2 fallback %s → %s",
            spec.model_id, fallback,
        )
        return fallback

    return spec.model_id


# ---------------------------------------------------------------------------
# Local Adapter Manager (PEFT — AMD MI300X only)
# ---------------------------------------------------------------------------

class LocalModelManager:
    """Singleton to manage local LoRA model loading and inference.

    Only used on the AMD droplet with working ROCm/GPU drivers.
    In development without GPU, this is skipped entirely.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalModelManager, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.tokenizer = None
            cls._instance.initialized = False
        return cls._instance

    def initialize(self) -> None:
        """Load the base model and LoRA adapters."""
        if self.initialized:
            return

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from peft import PeftModel
            import torch
        except ImportError:
            logger.warning("Transformers/PEFT/Torch not installed. Local inference disabled.")
            return

        adapter_path = os.getenv("LOCAL_ADAPTER_PATH")
        base_model_id = os.getenv("BASE_MODEL_ID", "Qwen/Qwen3.5-9B")

        if not adapter_path or not os.path.exists(adapter_path):
            logger.error("Local adapter path not found: %s", adapter_path)
            return

        logger.info("Loading base model %s + adapters %s...", base_model_id, adapter_path)
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                base_model_id, trust_remote_code=True,
            )
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_id,
                dtype=torch.bfloat16,
                device_map="auto",
                trust_remote_code=True,
            )
            self.model = PeftModel.from_pretrained(base_model, adapter_path)
            self.model.eval()
            self.initialized = True
            logger.info("Local BF16 model ready on %s", os.getenv("DEVICE", "cuda"))
        except Exception as exc:
            logger.error("Failed to load local model: %s", exc)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Run inference using the loaded local model."""
        if not self.initialized:
            self.initialize()
        if not self.initialized:
            raise RuntimeError("Local model manager not initialized.")

        import torch

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        prompt_str = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
        )
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
        generated_ids = outputs[:, inputs.input_ids.shape[1]:]
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return _strip_thinking_tokens(response)


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

    Flow:
      1. If USE_LOCAL_ADAPTERS=true AND tier=1 → try local PEFT inference
      2. If local fails or not enabled → route through vLLM/Featherless API

    Args:
        tier: Model tier (1 = fast 9B, 2 = deep 27B).
        system_prompt: System-level instructions.
        user_prompt: User-level content / query.
        max_tokens: Override the tier's default max_tokens.
        temperature: Override the tier's default temperature.
        json_mode: If True, request JSON response format.

    Returns:
        The model's text response (stripped of thinking tokens).

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

    # --- Path 1: Local LoRA adapters (MI300X only) ---
    use_local = os.getenv("USE_LOCAL_ADAPTERS", "false").lower() == "true"
    if tier == 1 and use_local:
        try:
            logger.info("Routing Tier 1 to local LoRA adapters...")
            return _local_manager.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=effective_max_tokens,
                temperature=effective_temperature,
            )
        except Exception as local_exc:
            logger.warning("Local inference failed, falling back to API: %s", local_exc)

    # --- Path 2: vLLM / Featherless API ---
    model_id = _resolve_model_id(spec)

    try:
        client = get_vllm_client()

        kwargs: Dict[str, Any] = {
            "model": model_id,
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
        raw_text = response.choices[0].message.content or ""
        text = _strip_thinking_tokens(raw_text)

        if not text:
            logger.warning(
                "Model returned empty response (raw_len=%d). "
                "May be all <think> tokens. Returning raw.",
                len(raw_text),
            )
            text = raw_text.strip() if raw_text else ""

        logger.debug("Response length: %d chars", len(text))
        return text

    except Exception as exc:
        logger.error("vLLM call failed for %s: %s", spec, exc)
        raise RuntimeError(
            f"Error connecting to vLLM ({model_id}): {exc}"
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
