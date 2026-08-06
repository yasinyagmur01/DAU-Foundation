"""Pluggable LLM inference backends for DAU agent decisions.

Biology analogy: the same organism can breathe through different media —
cloud API (Groq) or local tissue (HF 4-bit) — without rewriting the nervous
system (Layer 0–5 spine). Feature flag selects the medium; default keeps
today's Groq path.

LoRA plasticity is a leading testable path, not a guaranteed fix.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from langchain_groq import ChatGroq

# ---------------------------------------------------------------------------
# Backend selection and model constants (no magic numbers in logic)
# ---------------------------------------------------------------------------

LLM_BACKEND_ENV: str = "DAU_LLM_BACKEND"
BACKEND_GROQ: str = "groq"
BACKEND_LOCAL: str = "local"
DEFAULT_BACKEND: str = BACKEND_GROQ

GROQ_API_KEY_ENV: str = "GROQ_API_KEY"
ENV_FILE_NAME: str = ".env"

GROQ_MODEL_NAME: str = "llama-3.1-8b-instant"
DEFAULT_TEMPERATURE: float = 0.2
DEFAULT_MAX_TOKENS: int = 150

LOCAL_STUB_MESSAGE: str = (
    "LocalBackend: local_llm complete failed. "
    "Set DAU_LLM_BACKEND=groq, or ensure CUDA + peft/bitsandbytes and a GO VRAM spike."
)


def _project_root() -> Path:
    """Return the repository root (parent of the dau package)."""

    return Path(__file__).resolve().parents[2]


def load_env_file(env_path: Path | None = None) -> None:
    """Load KEY=VALUE pairs from .env into os.environ if not already set."""

    path = env_path if env_path is not None else _project_root() / ENV_FILE_NAME
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def resolve_backend_name() -> str:
    """Return groq|local from DAU_LLM_BACKEND; default groq."""

    raw = os.environ.get(LLM_BACKEND_ENV, "").strip().lower()
    if not raw:
        return DEFAULT_BACKEND
    if raw in (BACKEND_GROQ, BACKEND_LOCAL):
        return raw
    raise ValueError(
        f"Unsupported {LLM_BACKEND_ENV}={raw!r}; "
        f"expected {BACKEND_GROQ!r} or {BACKEND_LOCAL!r}."
    )


def _decision_text(response: Any) -> str:
    """Extract plain text from an LLM message response."""

    content = getattr(response, "content", None)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(str(block["text"]))
            else:
                text = getattr(block, "text", None)
                if text is not None:
                    parts.append(str(text))
        return "".join(parts).strip()
    return str(response).strip()


class LLMBackend(ABC):
    """Unified completion interface for System-2 decisions."""

    @abstractmethod
    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        seed: int | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        """Return assistant text for the given chat messages."""

    @abstractmethod
    def get_invoke_client(self) -> Any:
        """Return an object with .invoke(messages) for graph / diagnostics."""


class GroqBackend(LLMBackend):
    """Cloud Groq path — preserves today's ChatGroq behaviour."""

    def __init__(
        self,
        *,
        model_name: str = GROQ_MODEL_NAME,
        api_key: str | None = None,
    ) -> None:
        load_env_file()
        key = (api_key if api_key is not None else os.environ.get(GROQ_API_KEY_ENV, "")).strip()
        if not key:
            raise RuntimeError(
                f"{GROQ_API_KEY_ENV} is missing. Put it in "
                f"{_project_root() / ENV_FILE_NAME} or export {GROQ_API_KEY_ENV}=..."
            )
        self._model_name = model_name
        self._api_key = key

    def _make_client(
        self,
        *,
        temperature: float,
        seed: int | None,
        max_tokens: int,
    ) -> ChatGroq:
        model_kwargs: dict[str, Any] = {}
        if seed is not None:
            model_kwargs["seed"] = seed
        return ChatGroq(
            model=self._model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=self._api_key,
            model_kwargs=model_kwargs,
        )

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        seed: int | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        client = self._make_client(
            temperature=temperature,
            seed=seed,
            max_tokens=max_tokens,
        )
        response = client.invoke(messages)
        return _decision_text(response)

    def get_invoke_client(self) -> Any:
        """Default client using env temperature/seed resolved by the caller.

        Graph still constructs temperature/seed via its own resolvers and may
        monkeypatch _build_llm; this returns a ChatGroq at default T without
        seed so graph._build_llm can keep its prior construction path.
        """

        return self._make_client(
            temperature=DEFAULT_TEMPERATURE,
            seed=None,
            max_tokens=DEFAULT_MAX_TOKENS,
        )


class LocalBackend(LLMBackend):
    """Local 4-bit Llama path — delegates to local_llm when CUDA/deps ready."""

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        seed: int | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        from dau.foundation.local_llm import complete_local, cuda_is_available

        if not cuda_is_available():
            raise NotImplementedError(
                "LocalBackend requires CUDA. "
                f"Rollback: export {LLM_BACKEND_ENV}={BACKEND_GROQ}."
            )
        try:
            return complete_local(
                messages,
                seed=seed,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:  # noqa: BLE001 — surface as NotImplemented for callers
            raise NotImplementedError(f"{LOCAL_STUB_MESSAGE} ({exc})") from exc

    def get_invoke_client(self) -> Any:
        return self

    def invoke(self, messages: list[dict[str, str]]) -> Any:
        """Duck-type ChatGroq.invoke for graph wiring."""

        text = self.complete(messages)
        return type("LocalMessage", (), {"content": text})()


def get_llm_backend(name: str | None = None) -> LLMBackend:
    """Factory: DAU_LLM_BACKEND selects groq (default) or local stub."""

    backend_name = name if name is not None else resolve_backend_name()
    if backend_name == BACKEND_GROQ:
        return GroqBackend()
    if backend_name == BACKEND_LOCAL:
        return LocalBackend()
    raise ValueError(
        f"Unsupported backend {backend_name!r}; "
        f"expected {BACKEND_GROQ!r} or {BACKEND_LOCAL!r}."
    )
