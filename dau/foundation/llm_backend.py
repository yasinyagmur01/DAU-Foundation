"""Thin LLM backend Protocol — local frozen+adapter path (default) or Groq.

Biology analogy: the organism can sense through one sensory organ at a time —
a local 4-bit body with per-agent LoRA scars, or a remote Groq cortex.
Default is local since D-018; groq is the legacy/exploration path, opt-in
via DAU_LLM_BACKEND=groq.
"""

from __future__ import annotations

import os
from typing import Any, Protocol, runtime_checkable

# ---------------------------------------------------------------------------
# Backend selection (no magic numbers in logic)
# ---------------------------------------------------------------------------

LLM_BACKEND_ENV: str = "DAU_LLM_BACKEND"
LLM_BACKEND_GROQ: str = "groq"
LLM_BACKEND_LOCAL: str = "local"
# D-018: the experiment default is local. Channel 2 (per-agent adapter + DPO)
# needs weight access a remote endpoint cannot give, so the configuration in
# which the central claim is untestable cannot be the default. groq is kept as
# the legacy/exploration path, opt-in via DAU_LLM_BACKEND=groq.
LLM_BACKEND_DEFAULT: str = LLM_BACKEND_LOCAL
LLM_BACKEND_VALID: tuple[str, ...] = (LLM_BACKEND_LOCAL, LLM_BACKEND_GROQ)
LLM_BACKEND_UNKNOWN_MESSAGE: str = (
    "Unknown {env}={value!r}. Valid values: {valid}. Refusing to fall back to "
    "the default: since D-018 that default is '{default}', so a typo would "
    "silently load the local model for a run that asked for something else."
)


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
    """Return local|groq from DAU_LLM_BACKEND (default local, D-018).

    Unset or blank counts as "not set" and yields the default, matching
    graph._resolve_llm_temperature (GAP-15). Any other value raises instead of
    falling back: with the default flipped to local, a silent fallback
    would load the local model for a run that asked for something else
    (D-023). graph._resolve_llm_backend is a thin wrapper over this.
    """

    raw = os.environ.get(LLM_BACKEND_ENV, "").strip().lower()
    if not raw:
        return LLM_BACKEND_DEFAULT
    if raw not in LLM_BACKEND_VALID:
        raise ValueError(
            LLM_BACKEND_UNKNOWN_MESSAGE.format(
                env=LLM_BACKEND_ENV,
                value=raw,
                valid=", ".join(LLM_BACKEND_VALID),
                default=LLM_BACKEND_DEFAULT,
            )
        )
    return raw


def get_backend() -> Any:
    """Construct the active backend for this process."""

    if resolve_backend_name() == LLM_BACKEND_LOCAL:
        return LocalBackend()
    return GroqBackend()
