"""Thin LLM backend Protocol — Groq (default) or local frozen+adapter path.

Biology analogy: the organism can sense through one sensory organ at a time —
remote Groq cortex or a local 4-bit body with per-agent LoRA scars.
Default remains Groq; local is opt-in via DAU_LLM_BACKEND=local.
"""

from __future__ import annotations

import os
from typing import Any, Protocol, runtime_checkable

# ---------------------------------------------------------------------------
# Backend selection (no magic numbers in logic)
# ---------------------------------------------------------------------------

LLM_BACKEND_ENV: str = "DAU_LLM_BACKEND"
LLM_BACKEND_DEFAULT: str = "groq"
LLM_BACKEND_GROQ: str = "groq"
LLM_BACKEND_LOCAL: str = "local"


@runtime_checkable
class LLMBackend(Protocol):
    """Minimal completion surface used by agent_node."""

    def complete(self, system: str, user: str) -> str:
        """Return a free-form decision string from system+user prompts."""


class GroqBackend:
    """Remote Groq Llama path — frozen weights, no local adapter."""

    def complete(self, system: str, user: str) -> str:
        from dau.foundation.graph import _build_llm, _decision_text

        llm = _build_llm()
        response = llm.invoke(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
        )
        return _decision_text(response)


class LocalBackend:
    """Local 4-bit model + optional per-agent LoRA adapter."""

    def complete(self, system: str, user: str, agent_id: str = "default") -> str:
        from dau.foundation.local_llm import (
            generate_completion,
            get_loaded_model,
            load_local_model,
            switch_adapter,
        )

        model, tokenizer = load_local_model(agent_id=agent_id)
        loaded = get_loaded_model()
        if loaded is not None:
            switch_adapter(loaded, agent_id)
        return generate_completion(model, tokenizer, system=system, user=user)


def resolve_backend_name() -> str:
    """Return groq|local from DAU_LLM_BACKEND (default groq)."""

    raw = os.environ.get(LLM_BACKEND_ENV, LLM_BACKEND_DEFAULT).strip().lower()
    if raw == LLM_BACKEND_LOCAL:
        return LLM_BACKEND_LOCAL
    return LLM_BACKEND_GROQ


def get_backend() -> Any:
    """Construct the active backend for this process."""

    if resolve_backend_name() == LLM_BACKEND_LOCAL:
        return LocalBackend()
    return GroqBackend()
