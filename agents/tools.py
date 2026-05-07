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
        model_id=os.getenv("TIER1_MODEL_ID", "Qwen/Qwen3-8B"),
        description="Fast triage for well-documented cancers. Optimised for throughput.",
        max_tokens=512,
        temperature=0.0,
    ),
    2: TierSpec(
        tier_id=2,
        name="Deep Reasoning",
        model_id=os.getenv("TIER2_MODEL_ID", "Qwen/Qwen3-32B"),
        description="Deep reasoning for rare/complex/multi-mutation cases.",
        max_tokens=1024,
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
