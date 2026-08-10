"""Unit tests for per-agent QLoRA adapter paths (Punica pattern)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from dau.foundation.constraints import ADAPTER_BASE_DIR
from dau.foundation import local_llm
from dau.foundation.local_llm import (
    adapter_exists,
    get_adapter_path,
    save_agent_adapter,
    switch_adapter,
)
from dau.foundation.lora_update import (
    LORA_ENABLED_ENV,
    PreferencePair,
    run_micro_train_preference_step,
)


@pytest.fixture(autouse=True)
def _isolate_adapter_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep adapter writes inside tmp; LoRA off by default."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(LORA_ENABLED_ENV, "0")
    local_llm.reset_local_llm_singletons_for_tests()


def test_get_adapter_path_creates_directory() -> None:
    path = get_adapter_path("test-agent-001")
    assert path.exists()
    assert path.is_dir()
    assert path == Path(ADAPTER_BASE_DIR) / "test-agent-001"


def test_adapter_exists_false_when_no_adapter() -> None:
    agent_id = "fresh-never-saved-agent-xyz"
    get_adapter_path(agent_id)  # directory may exist empty
    assert adapter_exists(agent_id) is False


def test_adapter_exists_true_after_save() -> None:
    agent_id = "saved-agent-002"
    path = get_adapter_path(agent_id)
    (path / "adapter_config.json").write_text('{"peft_type":"LORA"}\n', encoding="utf-8")
    assert adapter_exists(agent_id) is True


def test_switch_adapter_no_crash_when_no_adapter() -> None:
    mock_model = SimpleNamespace()
    switch_adapter(mock_model, "nonexistent-agent-999")  # must not raise


def test_run_micro_train_preference_step_saves_per_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(LORA_ENABLED_ENV, "1")
    agent_id = "train-agent-003"
    saved: list[str] = []

    class _FakePeftModel:
        peft_config = {"default": object()}

        def save_pretrained(self, directory: str) -> None:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            (path / "adapter_config.json").write_text(
                '{"peft_type":"LORA","r":8}\n',
                encoding="utf-8",
            )
            (path / "adapter_model.safetensors").write_bytes(b"fake")
            saved.append(str(path))

    fake_model = _FakePeftModel()
    pairs = [
        PreferencePair(
            prompt="ctx",
            chosen="cooperate",
            rejected="defect",
            pe_chosen=0.2,
            pe_rejected=0.8,
            event_counter=1,
        )
    ]

    def _fake_local_train(*, pairs=None, agent_id="default", model=None):
        assert agent_id == "train-agent-003"
        save_agent_adapter(model, agent_id)
        return {
            "trained": True,
            "skipped": False,
            "reason": "ok",
            "agent_id": agent_id,
            "pair_count": len(pairs or []),
            "adapter_dir": str(get_adapter_path(agent_id)),
        }

    monkeypatch.setattr(
        "dau.foundation.local_llm.run_micro_train_preference_step",
        _fake_local_train,
    )
    monkeypatch.setattr(
        "dau.foundation.local_llm.get_loaded_model",
        lambda: fake_model,
    )

    result = run_micro_train_preference_step(
        pairs=pairs,
        agent_id=agent_id,
        model=fake_model,
    )
    assert result["skipped"] is False
    assert result["trained"] is True
    assert adapter_exists(agent_id) is True
    assert (get_adapter_path(agent_id) / "adapter_config.json").exists()
    assert result.get("adapter_dir") == str(get_adapter_path(agent_id))


def test_lora_disabled_skips_train_and_save(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(LORA_ENABLED_ENV, "0")
    agent_id = "disabled-agent"
    result = run_micro_train_preference_step(
        pairs=[
            PreferencePair(
                prompt="p",
                chosen="a",
                rejected="b",
                pe_chosen=0.1,
                pe_rejected=0.9,
            )
        ],
        agent_id=agent_id,
        model=SimpleNamespace(peft_config={}),
    )
    assert result["skipped"] is True
    assert result["trained"] is False
    assert adapter_exists(agent_id) is False


def test_save_agent_adapter_warns_without_lora() -> None:
    agent_id = "no-lora-model"
    save_agent_adapter(SimpleNamespace(), agent_id)
    assert adapter_exists(agent_id) is False


DEAD_ADAPTER_ROOT_NAME: str = "dau_lora_adapters"
DEAD_ADAPTER_ROOT_CONSTANT: str = "ADAPTER_ROOT_DIR"


def test_no_dead_adapter_root_reference() -> None:
    """Runtime adapter I/O must not reference the dead dau_lora_adapters root."""

    from dau.foundation import constraints, lora_update

    runtime_sources = (
        Path(local_llm.__file__),
        Path(constraints.__file__),
        Path(lora_update.__file__),
    )
    for source in runtime_sources:
        text = source.read_text(encoding="utf-8")
        assert DEAD_ADAPTER_ROOT_NAME not in text, source.name
        assert DEAD_ADAPTER_ROOT_CONSTANT not in text, source.name

    assert ADAPTER_BASE_DIR == "dau_runs/adapters"
    assert "dau_lora_adapters" not in get_adapter_path("probe-agent").as_posix()
    assert get_adapter_path.__code__.co_filename == local_llm.__file__
    assert save_agent_adapter.__code__.co_filename == local_llm.__file__
    assert switch_adapter.__code__.co_filename == local_llm.__file__


def test_quantization_flags_are_pinned_not_inherited() -> None:
    """D-020: nf4 + double_quant are written out, not left to the library.

    The neighbouring tool-identity test asserts that the report matches the
    loader, which holds whatever the values are — it would still pass if the
    flags were dropped and transformers' fp4 default came back. This one
    pins the values, so that regression has somewhere to break.
    """

    pytest.importorskip("torch")
    pytest.importorskip("bitsandbytes")

    config = local_llm.build_load_kwargs().get("quantization_config")
    if config is None:  # CPU-only build — 4-bit path not taken at all
        pytest.skip("bitsandbytes unavailable in this build")

    assert config.bnb_4bit_quant_type == local_llm.QUANT_TYPE_NF4
    assert config.bnb_4bit_use_double_quant is local_llm.DOUBLE_QUANT_ENABLED
    assert local_llm.QUANT_TYPE_NF4 == "nf4"
    assert local_llm.DOUBLE_QUANT_ENABLED is True

    reported = local_llm.describe_quantization()
    assert reported["quant_type"] == "nf4"
    assert reported["double_quant"] is True
