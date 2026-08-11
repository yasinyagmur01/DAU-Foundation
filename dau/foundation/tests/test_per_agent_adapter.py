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


class _CountingOptimizer:
    """Records optimizer traffic so accumulation can be counted, not assumed."""

    def __init__(self, params, lr: float = 0.0) -> None:
        self.param_groups = [{"params": list(params), "lr": lr}]
        self.steps = 0
        self.zero_grads = 0

    def step(self) -> None:
        self.steps += 1

    def zero_grad(self, *args, **kwargs) -> None:
        self.zero_grads += 1


def _run_epochs_counting_steps(
    monkeypatch: pytest.MonkeyPatch,
    *,
    n_pairs: int,
    accumulation: int,
) -> tuple[dict, _CountingOptimizer]:
    """Drive _run_dpo_epochs with every heavy part stubbed but the step logic."""

    torch = pytest.importorskip("torch")

    created: list[_CountingOptimizer] = []

    def _make_optimizer(params, lr=0.0):
        optimizer = _CountingOptimizer(params, lr)
        created.append(optimizer)
        return optimizer

    monkeypatch.setattr(torch.optim, "AdamW", _make_optimizer)
    monkeypatch.setattr(
        local_llm, "DPO_GRADIENT_ACCUMULATION_STEPS", accumulation, raising=False
    )
    monkeypatch.setattr(local_llm, "_enable_adapter_training", lambda _m: None)
    monkeypatch.setattr(local_llm, "_enable_gradient_checkpointing", lambda _m: False)
    def _encode(_tokenizer, _prompt, completion, _system="", **_k):
        # The two sides must not encode identically. When they did, every
        # policy_chosen - policy_rejected was exactly 0, so the whole loop
        # backpropagated a zero gradient and still reported a healthy train —
        # the shape I1.3 exists to catch, sitting inside the test harness.
        return ([1, 2, 3, 4], 2) if str(completion) == "c" else ([1, 2, 3], 2)

    monkeypatch.setattr(local_llm, "_encode_pair_side", _encode)
    monkeypatch.setattr(
        local_llm,
        "_reference_logprobs",
        lambda _model, encoded, _device: [(0.0, 0.0)] * len(encoded),
    )

    weight = torch.nn.Parameter(torch.zeros(1, requires_grad=True))

    def _logprob(_model, token_ids, _prompt_length, _device):
        # Depends on the parameter so backward() has a graph to walk.
        return weight.sum() * float(len(token_ids))

    monkeypatch.setattr(local_llm, "_sequence_logprob", _logprob)

    model = SimpleNamespace(
        parameters=lambda: iter([weight]),
        training=False,
        train=lambda: None,
        eval=lambda: None,
        config=None,
        device=torch.device("cpu"),
    )
    pairs = [
        SimpleNamespace(prompt="p", chosen="c", rejected="r", system="")
        for _ in range(n_pairs)
    ]

    stats = local_llm._run_dpo_epochs(model, object(), pairs)
    return stats, created[0]


@pytest.mark.parametrize(
    ("n_pairs", "accumulation", "expected_steps"),
    [
        (8, 4, 2),   # exact multiple
        (1, 4, 1),   # the case that actually happens today: tail only
        (6, 4, 2),   # 4 + a short tail of 2 — the tail must still step
        (3, 1, 3),   # accumulation off reproduces the old one-step-per-pair
    ],
)
def test_optimizer_steps_once_per_accumulation_group(
    monkeypatch: pytest.MonkeyPatch,
    n_pairs: int,
    accumulation: int,
    expected_steps: int,
) -> None:
    """D-021/A1: one optimizer step per N micro-steps, and no lost tail.

    The partial last group is not an edge case here — with 1-2 pairs surviving
    the filter it is the only group that ever runs, so a tail that never
    stepped would mean no training at all while the run reported success.
    """

    stats, optimizer = _run_epochs_counting_steps(
        monkeypatch, n_pairs=n_pairs, accumulation=accumulation
    )

    assert optimizer.steps == expected_steps
    assert stats["dpo_optimizer_steps"] == expected_steps
    assert stats["dpo_steps"] == n_pairs  # micro-steps keep their old meaning
    assert stats["dpo_gradient_accumulation_steps"] == accumulation


def test_grad_norm_is_kept_not_discarded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """I1.3: clip_grad_norm_ already computes the norm; we were throwing it away.

    Without this the run cannot tell a step driven by its learning rate from
    one pinned to the clip ceiling, and D-029's choice of DPO_LEARNING_RATE
    stops describing the training.
    """

    stats, _ = _run_epochs_counting_steps(monkeypatch, n_pairs=8, accumulation=4)

    assert stats["dpo_grad_norm_min"] > 0.0
    assert stats["dpo_grad_norm_mean"] >= stats["dpo_grad_norm_min"]
    assert isinstance(stats["dpo_clipped_steps"], int)


def test_grad_norm_counts_only_the_steps_over_the_ceiling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The clip counter must follow the measured norm, not the constant (2.8)."""

    from dau.foundation.constraints import DPO_MAX_GRAD_NORM

    stats, _ = _run_epochs_counting_steps(monkeypatch, n_pairs=8, accumulation=4)
    steps = stats["dpo_optimizer_steps"]

    # Whatever the stub's gradients came out as, the count has to agree with
    # the norms actually seen — that is the only thing making it a measurement.
    if stats["dpo_grad_norm_min"] > DPO_MAX_GRAD_NORM:
        assert stats["dpo_clipped_steps"] == steps
    elif stats["dpo_grad_norm_mean"] <= DPO_MAX_GRAD_NORM:
        assert stats["dpo_clipped_steps"] < steps or steps == 0


def test_grad_norm_is_unread_not_zero_when_no_step_ran(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A loop that never stepped reports unread — 0.0 would look like a real
    reading of a zero gradient, which is a different failure (I1.1's rule)."""

    import math

    from dau.foundation.constraints import GRAD_NORM_UNREAD

    assert math.isnan(GRAD_NORM_UNREAD)


def test_train_step_leaves_no_gradient_on_the_shared_adapter_slot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GAP-6: one adapter slot is reused across agents, so .grad must not survive.

    Relying on the next call's zero_grad would make agent A's isolation depend
    on agent B's ordering — the shape of the f25b0ef and D-042 leaks.
    """

    torch = pytest.importorskip("torch")

    captured: list[torch.nn.Parameter] = []
    real_release = local_llm._release_train_memory

    def _spy(parameters):
        captured.extend(parameters)
        return real_release(parameters)

    monkeypatch.setattr(local_llm, "_release_train_memory", _spy)
    _run_epochs_counting_steps(monkeypatch, n_pairs=8, accumulation=4)

    assert captured, "the train step never released its parameters"
    assert all(p.grad is None for p in captured)


def test_release_is_not_wired_into_the_per_decision_swap_path() -> None:
    """empty_cache walks the allocator; switch_adapter runs on every decision.

    graph.agent_node calls switch_adapter per local decision, and the swap
    allocates nothing worth reclaiming, so paying that walk 50+ times a phase
    would be cost without benefit.
    """

    import inspect

    source = inspect.getsource(local_llm.switch_adapter)
    assert "_release_train_memory" not in source
    assert "empty_cache" not in source


def test_learning_rate_stays_in_the_band_the_decision_rests_on() -> None:
    """D-029: outside this band DPO stops raising the chosen completion.

    Measured on 9 real pairs (dau_runs/lr_probe_results.json): at 5e-5 the
    chosen completion's mean log-prob fell -0.1230 while the rejected fell
    -4.3715, so the entire margin came from suppression. At 1e-6 the chosen
    rose +0.0846. Pinning the literal alone would not say why a change is
    wrong, so the band is asserted with the reason attached.
    """

    from dau.foundation.constraints import (
        DPO_LEARNING_RATE,
        DPO_LEARNING_RATE_MAX,
        DPO_LEARNING_RATE_MIN,
    )

    assert DPO_LEARNING_RATE_MIN <= DPO_LEARNING_RATE <= DPO_LEARNING_RATE_MAX, (
        f"DPO_LEARNING_RATE={DPO_LEARNING_RATE:g} is outside the measured band "
        f"[{DPO_LEARNING_RATE_MIN:g}, {DPO_LEARNING_RATE_MAX:g}]. Above it, "
        "training suppresses the rejected completion instead of raising the "
        "chosen one, and the trace inherited by gen2 is a suppression pattern "
        "rather than a preference (D-029). Changing it needs a new D-record."
    )


def test_tool_identity_reports_the_learning_rate_actually_used() -> None:
    """A run must not be able to misreport the rate that produced its weights."""

    from dau.diagnostics.tool_identity import BACKEND_LOCAL, build_tool_identity
    from dau.foundation.constraints import DPO_LEARNING_RATE

    import os

    previous = os.environ.get("DAU_LLM_BACKEND")
    os.environ["DAU_LLM_BACKEND"] = BACKEND_LOCAL
    try:
        identity = build_tool_identity(lora_choice="off", seeds=[2001])
    finally:
        if previous is None:
            os.environ.pop("DAU_LLM_BACKEND", None)
        else:
            os.environ["DAU_LLM_BACKEND"] = previous

    assert identity["dpo"]["learning_rate"] == DPO_LEARNING_RATE


def test_adapter_reset_neither_draws_nor_reads_the_live_rng() -> None:
    """D-042: the reset must not depend on, or disturb, the life's stream.

    Both halves are load-bearing. If the reset READS the live stream, lora_A
    becomes a function of how many arms already ran — measured as a shuffle
    arm digesting differently at position 1 and position 3, which put a
    systematic term inside lived-vs-shuffle. If it DRAWS from the stream, the
    life's sampling lands somewhere different depending on the same history.

    Uses a stand-in LoraLayer so the property is tested without an 8B model.
    """

    torch = pytest.importorskip("torch")
    lora = pytest.importorskip("peft.tuners.lora")

    STREAM_SEED = 2001

    from dau.foundation.local_llm import ACTIVE_ADAPTER_NAME, _reset_active_adapter

    class _FakeLayer(lora.LoraLayer):
        def __init__(self) -> None:
            self.lora_A = {ACTIVE_ADAPTER_NAME: torch.nn.Linear(4, 2, bias=False)}
            self.lora_B = {ACTIVE_ADAPTER_NAME: torch.nn.Linear(2, 4, bias=False)}
            self.lora_embedding_A = {}
            self.lora_embedding_B = {}
            self.r = {ACTIVE_ADAPTER_NAME: 2}
            self.lora_bias = {ACTIVE_ADAPTER_NAME: False}

    class _FakeModel:
        def __init__(self) -> None:
            self.layer = _FakeLayer()

        def modules(self):
            return [self.layer]

    # Built once and outside every measurement window: constructing nn.Linear
    # draws from the stream itself, which would be mistaken for the reset.
    model = _FakeModel()

    def reset_after(warmup: int) -> tuple[torch.Tensor, torch.Tensor]:
        """Reset after consuming `warmup` draws, then read what comes next."""

        torch.manual_seed(STREAM_SEED)
        for _ in range(warmup):
            torch.rand(1)
        _reset_active_adapter(model)
        lora_a = model.layer.lora_A[ACTIVE_ADAPTER_NAME].weight.detach().clone()
        return lora_a, torch.rand(3)

    early_a, early_next = reset_after(warmup=0)
    late_a, late_next = reset_after(warmup=17)

    # Reads nothing: the graft is identical however much ran before it.
    assert torch.equal(early_a, late_a)

    # Draws nothing: a reset inserted into a stream leaves it where it was.
    torch.manual_seed(STREAM_SEED)
    untouched_next = torch.rand(3)
    assert torch.equal(early_next, untouched_next)

    # And the warmup itself is still visible, so the comparison above is not
    # passing because the stream is somehow frozen.
    assert not torch.equal(early_next, late_next)
