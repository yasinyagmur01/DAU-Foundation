"""Backend resolution: default local (D-018), loud on unknown (D-023)."""

from __future__ import annotations

import pytest

from dau.foundation import graph as graph_mod
from dau.foundation import llm_backend as backend_mod
from dau.foundation.graph import (
    LLM_BACKEND_ENV,
    LLM_BACKEND_GROQ,
    LLM_BACKEND_LOCAL,
    _resolve_llm_backend,
)

BLANK_VALUES: tuple[str, ...] = ("", "   ", "\t")
UNKNOWN_VALUES: tuple[str, ...] = ("grok", "openai", "Local ish", "none")


@pytest.fixture(autouse=True)
def _clear_backend_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Start every case from an unset variable, whatever the shell had."""

    monkeypatch.delenv(LLM_BACKEND_ENV, raising=False)


def test_unset_backend_resolves_local() -> None:
    """D-018: the experiment default is the local backend, not groq."""

    assert _resolve_llm_backend() == LLM_BACKEND_LOCAL


@pytest.mark.parametrize("blank", BLANK_VALUES)
def test_blank_backend_counts_as_unset(
    blank: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Blank means "not set" — same reading as _resolve_llm_temperature."""

    monkeypatch.setenv(LLM_BACKEND_ENV, blank)
    assert _resolve_llm_backend() == LLM_BACKEND_LOCAL


def test_groq_stays_reachable(monkeypatch: pytest.MonkeyPatch) -> None:
    """D-018 keeps groq as the legacy path — opt-in, not deleted."""

    monkeypatch.setenv(LLM_BACKEND_ENV, LLM_BACKEND_GROQ)
    assert _resolve_llm_backend() == LLM_BACKEND_GROQ


def test_local_is_accepted_explicitly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(LLM_BACKEND_ENV, LLM_BACKEND_LOCAL)
    assert _resolve_llm_backend() == LLM_BACKEND_LOCAL


def test_case_and_whitespace_are_tolerated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Leniency that predates D-023 stays: only unknown words are fatal."""

    monkeypatch.setenv(LLM_BACKEND_ENV, "  GROQ ")
    assert _resolve_llm_backend() == LLM_BACKEND_GROQ


@pytest.mark.parametrize("unknown", UNKNOWN_VALUES)
def test_unknown_backend_raises_instead_of_defaulting(
    unknown: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D-023: a typo must not silently become the local backend."""

    monkeypatch.setenv(LLM_BACKEND_ENV, unknown)
    with pytest.raises(ValueError) as excinfo:
        _resolve_llm_backend()

    message = str(excinfo.value)
    assert LLM_BACKEND_ENV in message
    assert LLM_BACKEND_LOCAL in message
    assert LLM_BACKEND_GROQ in message


def test_llm_backend_module_mirrors_graph_constants() -> None:
    """graph re-exports the same objects — tekilleştirme is identity, not equality."""

    assert backend_mod.LLM_BACKEND_VALID is graph_mod.LLM_BACKEND_VALID


def test_llm_backend_module_resolver_agrees_with_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """resolve_backend_name has no caller today; it must not answer differently."""

    assert backend_mod.resolve_backend_name() == _resolve_llm_backend()

    monkeypatch.setenv(LLM_BACKEND_ENV, LLM_BACKEND_GROQ)
    assert backend_mod.resolve_backend_name() == _resolve_llm_backend()

    monkeypatch.setenv(LLM_BACKEND_ENV, UNKNOWN_VALUES[0])
    with pytest.raises(ValueError):
        backend_mod.resolve_backend_name()
