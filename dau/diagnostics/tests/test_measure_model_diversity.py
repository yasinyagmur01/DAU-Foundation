"""U3b gates: the measurement refuses rather than producing a wrong number."""

from __future__ import annotations

import json

import pytest

from dau.diagnostics import measure_model_diversity as u3
from dau.foundation import local_llm
from dau.foundation.local_llm import LLM_DO_SAMPLE_ENV, LOCAL_MODEL_ENV

AGENT_ID: str = "u3-unit-agent"
BACKEND_ENV: str = "DAU_LLM_BACKEND"


@pytest.fixture(autouse=True)
def _clean_env(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Local backend, nothing resident, adapters under tmp."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(BACKEND_ENV, "local")
    monkeypatch.delenv(LOCAL_MODEL_ENV, raising=False)
    monkeypatch.delenv(LLM_DO_SAMPLE_ENV, raising=False)
    local_llm.reset_local_llm_singletons_for_tests()


def test_remote_backend_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """A remote endpoint would measure someone else's model."""

    monkeypatch.setenv(BACKEND_ENV, "groq")
    with pytest.raises(SystemExit) as excinfo:
        u3._check_preconditions(AGENT_ID)
    assert "local" in str(excinfo.value)


def test_second_model_in_same_process_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One model per process — otherwise the VRAM peak mixes two checkpoints."""

    monkeypatch.setattr(local_llm, "_loaded_model_name", "meta-llama/already-here")
    with pytest.raises(SystemExit) as excinfo:
        u3._check_preconditions(AGENT_ID)
    assert "meta-llama/already-here" in str(excinfo.value)


def test_sampling_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """D-019 pre-registered greedy; sampling makes n_unique a temperature knob."""

    monkeypatch.setenv(LLM_DO_SAMPLE_ENV, "1")
    with pytest.raises(SystemExit) as excinfo:
        u3._check_preconditions(AGENT_ID)
    assert LLM_DO_SAMPLE_ENV in str(excinfo.value)


def test_existing_adapter_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """A leftover adapter would make this describe trained weights, not the base."""

    monkeypatch.setattr(local_llm, "adapter_exists", lambda _agent_id: True)
    monkeypatch.setattr(u3, "adapter_exists", lambda _agent_id: True)
    with pytest.raises(SystemExit) as excinfo:
        u3._check_preconditions(AGENT_ID)
    assert AGENT_ID in str(excinfo.value)


def test_preconditions_return_resolved_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Clean state resolves to the checkpoint the env names (D-025 arm B)."""

    monkeypatch.setenv(LOCAL_MODEL_ENV, "Qwen/Qwen2.5-7B-Instruct")
    assert u3._check_preconditions(AGENT_ID) == "Qwen/Qwen2.5-7B-Instruct"


def test_templateless_tokenizer_invalidates_the_arm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D-025: silent plain-text fallback must abort, not produce a comparison.

    A model run outside its own chat format continues the prompt instead of
    deciding, and distinct continuations inflate n_unique for the wrong reason.
    """

    monkeypatch.setattr(u3, "load_local_model", lambda agent_id: (object(), object()))
    monkeypatch.setattr(u3, "_build_prompt", lambda *_a, **_k: ("plain text", False))

    with pytest.raises(SystemExit) as excinfo:
        u3.measure_one_model(seeds=(2001,), n_events=1)
    assert "chat template" in str(excinfo.value)


def test_arms_write_to_separate_files(tmp_path) -> None:
    """Two checkpoints must not overwrite each other's numbers."""

    first = u3.write_results_json(
        {"model_loaded": "meta-llama/Meta-Llama-3.1-8B-Instruct", "n_unique_values": [3]}
    )
    second = u3.write_results_json(
        {"model_loaded": "Qwen/Qwen2.5-7B-Instruct", "n_unique_values": [6]}
    )

    assert first != second
    assert json.loads(first.read_text())["n_unique_values"] == [3]
    assert json.loads(second.read_text())["n_unique_values"] == [6]


def test_script_never_names_a_winner() -> None:
    """The criterion lives in D-019/D-025; code that ranks is code that drifts."""

    source = u3.__file__
    with open(source, encoding="utf-8") as handle:
        text = handle.read()

    for banned in ("winner", "adopt", "better_model", "is_qwen_better"):
        assert f"{banned} =" not in text
        assert f"def {banned}" not in text
    assert "DIVERSITY_MIN_UNIQUE" in text  # reported for reference only
