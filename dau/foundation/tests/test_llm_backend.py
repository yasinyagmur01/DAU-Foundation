"""Unit tests for pluggable LLM backend factory (Faz 1)."""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from dau.foundation import llm_backend as backend_mod
from dau.foundation.llm_backend import (
    BACKEND_GROQ,
    BACKEND_LOCAL,
    DEFAULT_BACKEND,
    LLM_BACKEND_ENV,
    GroqBackend,
    LocalBackend,
    get_llm_backend,
    resolve_backend_name,
)


@pytest.fixture(autouse=True)
def _clear_backend_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate DAU_LLM_BACKEND across tests."""

    monkeypatch.delenv(LLM_BACKEND_ENV, raising=False)


def test_resolve_backend_default_is_groq() -> None:
    assert resolve_backend_name() == DEFAULT_BACKEND
    assert resolve_backend_name() == BACKEND_GROQ


def test_resolve_backend_env_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(LLM_BACKEND_ENV, "local")
    assert resolve_backend_name() == BACKEND_LOCAL


def test_resolve_backend_rejects_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(LLM_BACKEND_ENV, "openai")
    with pytest.raises(ValueError, match="Unsupported"):
        resolve_backend_name()


def test_factory_default_returns_groq(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(backend_mod.GROQ_API_KEY_ENV, "test-key-not-real")
    backend = get_llm_backend()
    assert isinstance(backend, GroqBackend)


def test_factory_local_returns_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(LLM_BACKEND_ENV, BACKEND_LOCAL)
    backend = get_llm_backend()
    assert isinstance(backend, LocalBackend)


def test_local_complete_raises_not_implemented(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "dau.foundation.local_llm.cuda_is_available",
        lambda: False,
    )
    backend = LocalBackend()
    with pytest.raises(NotImplementedError, match="CUDA"):
        backend.complete(
            [{"role": "user", "content": "hello"}],
            seed=42,
            temperature=0.2,
        )


def test_local_invoke_raises_without_cuda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "dau.foundation.local_llm.cuda_is_available",
        lambda: False,
    )
    backend = LocalBackend()
    with pytest.raises(NotImplementedError, match="CUDA"):
        backend.invoke([{"role": "user", "content": "hello"}])


def test_groq_complete_uses_chatgroq_invoke(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(backend_mod.GROQ_API_KEY_ENV, "test-key-not-real")

    fake_response = MagicMock()
    fake_response.content = "  take resources  "

    fake_client = MagicMock()
    fake_client.invoke.return_value = fake_response

    with patch.object(GroqBackend, "_make_client", return_value=fake_client):
        backend = GroqBackend(api_key="test-key-not-real")
        text = backend.complete(
            [
                {"role": "system", "content": "sys"},
                {"role": "user", "content": "usr"},
            ],
            seed=1001,
            temperature=0.2,
            max_tokens=150,
        )

    assert text == "take resources"
    fake_client.invoke.assert_called_once()
    messages = fake_client.invoke.call_args[0][0]
    assert messages[0]["role"] == "system"
    assert messages[1]["content"] == "usr"


def test_groq_make_client_passes_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(backend_mod.GROQ_API_KEY_ENV, "test-key-not-real")
    captured: dict[str, Any] = {}

    def _fake_chatgroq(**kwargs: Any) -> MagicMock:
        captured.update(kwargs)
        return MagicMock()

    with patch("dau.foundation.llm_backend.ChatGroq", side_effect=_fake_chatgroq):
        backend = GroqBackend(api_key="test-key-not-real")
        backend._make_client(temperature=0.2, seed=42, max_tokens=150)

    assert captured["model"] == backend_mod.GROQ_MODEL_NAME
    assert captured["temperature"] == 0.2
    assert captured["max_tokens"] == 150
    assert captured["model_kwargs"]["seed"] == 42


def test_get_llm_backend_explicit_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(backend_mod.GROQ_API_KEY_ENV, "test-key-not-real")
    assert isinstance(get_llm_backend(BACKEND_LOCAL), LocalBackend)
    assert isinstance(get_llm_backend(BACKEND_GROQ), GroqBackend)
