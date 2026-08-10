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


def test_local_model_name_defaults_when_env_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unset or blank means "not set" — the GAP-15 / D-023 reading."""

    monkeypatch.delenv(local_llm.LOCAL_MODEL_ENV, raising=False)
    assert local_llm.resolve_local_model_name() == local_llm.LOCAL_MODEL_NAME

    for blank in ("", "   ", "\t"):
        monkeypatch.setenv(local_llm.LOCAL_MODEL_ENV, blank)
        assert local_llm.resolve_local_model_name() == local_llm.LOCAL_MODEL_NAME


def test_local_model_name_follows_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """U3 points the same harness at a second checkpoint (D-019/D-025)."""

    monkeypatch.setenv(local_llm.LOCAL_MODEL_ENV, "  Qwen/Qwen2.5-7B-Instruct ")
    assert local_llm.resolve_local_model_name() == "Qwen/Qwen2.5-7B-Instruct"


def test_loaded_model_name_is_none_before_any_load() -> None:
    """Nothing in VRAM yet — the autouse fixture resets the singletons."""

    assert local_llm.get_loaded_model_name() is None


def test_switching_model_env_after_load_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The singleton cannot swap weights; serving the old ones silently is worse.

    Without this, a second measurement in the same process would generate
    with the first model while tool_identity reported the second.
    """

    monkeypatch.setattr(local_llm, "_model", SimpleNamespace())
    monkeypatch.setattr(local_llm, "_tokenizer", SimpleNamespace())
    monkeypatch.setattr(local_llm, "_loaded_model_name", "meta-llama/first")
    monkeypatch.setenv(local_llm.LOCAL_MODEL_ENV, "Qwen/second")

    with pytest.raises(RuntimeError) as excinfo:
        local_llm.load_local_model(agent_id="probe-agent")

    message = str(excinfo.value)
    assert "meta-llama/first" in message
    assert "Qwen/second" in message
    assert local_llm.LOCAL_MODEL_ENV in message


def test_tool_identity_reports_loaded_weights_not_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """model_id must name what is in VRAM, never what the env now asks for.

    The trap this guards: point DAU_LOCAL_MODEL at a second checkpoint and a
    report that read the constant (or the env) would label Qwen numbers with
    a Llama name, or the reverse.
    """

    from dau.diagnostics.tool_identity import BACKEND_LOCAL, _model_id

    monkeypatch.setenv(local_llm.LOCAL_MODEL_ENV, "Qwen/env-says-this")

    monkeypatch.setattr(local_llm, "_loaded_model_name", None)
    assert _model_id(BACKEND_LOCAL) == "Qwen/env-says-this"

    monkeypatch.setattr(local_llm, "_loaded_model_name", "meta-llama/vram-has-this")
    assert _model_id(BACKEND_LOCAL) == "meta-llama/vram-has-this"


def test_dpo_window_holds_a_real_prompt_with_full_memory_recall() -> None:
    """D-027: the DPO window must fit what inference actually sends.

    _encode_pair_side drops the prompt HEAD on overflow — the chat template
    header and SYSTEM_PROMPT — while generate_completion never truncates. Any
    overflow therefore trains on an instruction the agent never decided under.

    The assertion is that no truncation happened, not that the returned
    sequence is short: the encoder truncates to fit, so its output is within
    the window by construction and measuring it would prove nothing. It
    compares the prompt length the encoder kept against the full prompt.
    """

    pytest.importorskip("transformers")
    from transformers import AutoTokenizer

    from dau.foundation import graph as graph_mod
    from dau.foundation.constraints import DPO_MAX_SEQUENCE_TOKENS
    from dau.foundation.memory_bridge import MAX_RETRIEVED_MEMORIES

    try:
        tokenizer = AutoTokenizer.from_pretrained(local_llm.LOCAL_MODEL_NAME)
    except Exception:  # noqa: BLE001 — no cached checkpoint in this environment
        pytest.skip("base tokenizer not available locally")

    from dau.diagnostics.run_protocol_c_prime import _initial_state

    state = _initial_state("dpo-window-probe", 2001)
    user = graph_mod.build_agent_view(state).model_dump_json()

    # Worst realistic case: a full memory block plus the drift warning.
    memory = {"domain": "resource_load", "magnitude": 0.42, "classification": "DEEP"}
    block = graph_mod._format_memory_context([memory] * MAX_RETRIEVED_MEMORIES)
    system = (
        f"{graph_mod.SYSTEM_PROMPT}\n\n{block}\n"
        + graph_mod.DRIFT_WARNING_TEMPLATE.format(domain="resource_load", bias=0.42)
    )
    completion = "I cooperate and share resources carefully with others."

    prompt_text, used_template = local_llm._build_prompt(tokenizer, system, user)
    full_prompt_tokens = len(
        tokenizer(prompt_text, add_special_tokens=not used_template)["input_ids"]
    )

    sequence, kept_prompt_tokens = local_llm._encode_pair_side(
        tokenizer,
        system=system,
        prompt=user,
        completion=completion,
    )

    assert kept_prompt_tokens == full_prompt_tokens, (
        f"the encoder kept {kept_prompt_tokens} of {full_prompt_tokens} prompt "
        f"tokens: {full_prompt_tokens - kept_prompt_tokens} were cut off the "
        f"head (SYSTEM_PROMPT) because the sequence needs "
        f"{len(sequence) + full_prompt_tokens - kept_prompt_tokens} tokens and "
        f"DPO_MAX_SEQUENCE_TOKENS is {DPO_MAX_SEQUENCE_TOKENS}. Training would "
        "learn from an instruction inference never truncates (D-027)."
    )
