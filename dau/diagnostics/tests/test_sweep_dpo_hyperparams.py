"""Tests for the exploratory DPO hyperparameter sweep.

The sweep runs outside the pre-registered harness, so two properties carry the
whole safety argument: it must not leave weights on disk, and it must not
leave a changed threshold behind. Both are asserted here rather than trusted
to the code reading correctly.
"""

from __future__ import annotations

import pytest

import dau.foundation.local_llm as local_llm
from dau.diagnostics.sweep_dpo_hyperparams import (
    SWEEP_AGENT_PREFIX,
    _rehydrate,
    _train_once,
)
from dau.foundation.lora_update import PreferencePair


class _FakeModel:
    pass


def _patch_training(monkeypatch: pytest.MonkeyPatch, calls: dict) -> None:
    monkeypatch.setattr(local_llm, "switch_adapter", lambda m, a: calls.setdefault("switched", []).append(a))
    monkeypatch.setattr(local_llm, "lora_b_abs_sum", lambda m: 1.0)
    monkeypatch.setattr(
        local_llm,
        "_run_dpo_epochs",
        lambda m, t, p: {
            "dpo_loss": 0.5,
            "seen_lr": local_llm.DPO_LEARNING_RATE,
            "seen_clip": local_llm.DPO_MAX_GRAD_NORM,
        },
    )
    monkeypatch.setattr(
        local_llm,
        "save_agent_adapter",
        lambda m, a: calls.setdefault("saved", []).append(a),
    )


def test_sweep_never_saves_an_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    # An exploratory run that wrote weights would trip I0.7 on the next real
    # run — and would do so a whole run later, when the cause is hardest to
    # find (CLAUDE.md 2.7).
    calls: dict = {}
    _patch_training(monkeypatch, calls)

    _train_once(
        model=_FakeModel(),
        tokenizer=object(),
        pairs=[_pair()],
        learning_rate=5e-6,
        max_grad_norm=3.0,
        config_tag="t1",
    )

    assert "saved" not in calls
    assert calls["switched"] == [f"{SWEEP_AGENT_PREFIX}t1"]


def test_overrides_reach_training_and_are_restored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict = {}
    _patch_training(monkeypatch, calls)
    original_lr = local_llm.DPO_LEARNING_RATE
    original_clip = local_llm.DPO_MAX_GRAD_NORM

    stats = _train_once(
        model=_FakeModel(),
        tokenizer=object(),
        pairs=[_pair()],
        learning_rate=2e-5,
        max_grad_norm=10.0,
        config_tag="t2",
    )

    # The override must actually be visible to the training call, not merely
    # assigned somewhere the trainer does not read.
    assert stats["seen_lr"] == 2e-5
    assert stats["seen_clip"] == 10.0
    assert local_llm.DPO_LEARNING_RATE == original_lr
    assert local_llm.DPO_MAX_GRAD_NORM == original_clip


def test_constants_restored_even_when_training_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Without the finally, one crashed config would leave every later run in
    # the process training under a threshold nobody chose.
    calls: dict = {}
    _patch_training(monkeypatch, calls)
    monkeypatch.setattr(
        local_llm,
        "_run_dpo_epochs",
        lambda m, t, p: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    original_lr = local_llm.DPO_LEARNING_RATE
    original_clip = local_llm.DPO_MAX_GRAD_NORM

    with pytest.raises(RuntimeError, match="boom"):
        _train_once(
            model=_FakeModel(),
            tokenizer=object(),
            pairs=[_pair()],
            learning_rate=1e-4,
            max_grad_norm=99.0,
            config_tag="t3",
        )

    assert local_llm.DPO_LEARNING_RATE == original_lr
    assert local_llm.DPO_MAX_GRAD_NORM == original_clip


def test_resume_reads_finished_cells_and_survives_a_truncated_line(tmp_path) -> None:
    # The sweep runs for hours on a machine that gets shut down. The file it
    # resumes from is written incrementally, so the normal way it ends is a
    # process killed mid-write — refusing to start on a half-written last line
    # would throw away the very progress the file exists to protect.
    import json

    from dau.diagnostics.sweep_dpo_hyperparams import cell_key, load_completed_cells

    path = tmp_path / "progress.jsonl"
    path.write_text(
        json.dumps({"learning_rate": 1e-6, "max_grad_norm": 1.0, "agent_id": "a"})
        + "\n"
        + json.dumps({"learning_rate": 5e-6, "max_grad_norm": 3.0, "agent_id": "b"})
        + "\n"
        + '{"learning_rate": 1e-05, "max_gr',  # killed mid-write
        encoding="utf-8",
    )

    done = load_completed_cells(path)

    assert set(done) == {cell_key(1e-6, 1.0, "a"), cell_key(5e-6, 3.0, "b")}


def test_rehydrate_round_trips_a_dumped_pair() -> None:
    from dataclasses import asdict

    original = _pair()
    assert _rehydrate([asdict(original)]) == [original]


def _pair() -> PreferencePair:
    return PreferencePair(
        prompt="p",
        chosen="c",
        rejected="r",
        pe_chosen=0.2,
        pe_rejected=0.8,
        event_counter=3,
        system="s",
    )
