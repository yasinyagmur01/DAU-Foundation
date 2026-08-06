"""Tests for Protocol C′ harness (dry-run; no GPU required)."""

from __future__ import annotations

import json
from pathlib import Path

from dau.diagnostics.run_protocol_c_prime import (
    ADAPTER_NULL,
    ADAPTER_SHARED,
    ADAPTER_SHUFFLE,
    STATUS_DEFERRED,
    build_shared_adapter,
    run_protocol_c_prime,
    write_report,
)
from dau.foundation.lora_update import LivedTraceExample


def _example(pe: float = 0.3) -> LivedTraceExample:
    return LivedTraceExample(
        event_counter=1,
        prediction_error=pe,
        delta_magnitude=0.4,
        delta_class="NORMAL",
        trauma_flag=False,
        drift_sum=0.0,
        loss_weight=0.7,
        prompt=f"Lived scalars: pe={pe:.3f} magnitude=0.400 class=NORMAL trauma=False drift_sum=0.000",
        completion="extract",
    )


def test_shared_adapter_meta_marks_train_then_ab(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    spec = build_shared_adapter(2001, kind=ADAPTER_SHARED, examples=[_example()])
    meta = json.loads((Path(spec.path) / "adapter_meta.json").read_text(encoding="utf-8"))
    assert meta["shared_for_ab"] is True
    assert meta["train_then_ab"] is True
    assert spec.adapter_id == ADAPTER_SHARED


def test_null_adapter_has_no_traces(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    spec = build_shared_adapter(2001, kind=ADAPTER_NULL, examples=[_example()])
    assert spec.example_count == 0
    assert not (Path(spec.path) / "lived_traces.jsonl").exists()


def test_shuffle_permutes_pe(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    examples = [_example(0.1), _example(0.9), _example(0.5)]
    spec = build_shared_adapter(2001, kind=ADAPTER_SHUFFLE, examples=examples)
    lines = (Path(spec.path) / "lived_traces.jsonl").read_text(encoding="utf-8").strip().splitlines()
    pes = [json.loads(line)["prediction_error"] for line in lines]
    assert sorted(pes) == sorted([0.1, 0.9, 0.5])


def test_protocol_c_prime_dry_run_report(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    report = run_protocol_c_prime(seeds=[2001, 2002, 2003], dry_run=True)
    assert report.status == STATUS_DEFERRED
    assert report.n_pairs == 3
    assert report.wall_clock_total_s >= 0.0
    kinds = {c["condition"] for c in report.conditions}
    assert kinds == {ADAPTER_SHARED, ADAPTER_NULL, ADAPTER_SHUFFLE}
    # Each seed × 3 conditions
    assert len(report.conditions) == 9
    path = write_report(report)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["status"] == STATUS_DEFERRED
    assert "DEFER" in payload["decision"]
