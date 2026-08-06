"""Unit tests for local_llm VRAM spike harness (no GPU required)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from dau.foundation.local_llm import (
    MICRO_TRAIN_COMPLETION,
    MICRO_TRAIN_PROMPT,
    STATUS_CUDA_UNAVAILABLE,
    STATUS_DEPS_MISSING,
    STATUS_GO,
    STATUS_MODEL_ACCESS,
    STATUS_NOGO,
    VRAM_GO_BUDGET_BYTES,
    VramSpikeReport,
    format_micro_train_texts,
    lora_plasticity_allowed,
    run_vram_spike,
    write_vram_spike_report,
)
from dau.foundation.lora_update import LivedTraceExample


def test_vram_spike_reports_cuda_unavailable_without_gpu() -> None:
    with patch("dau.foundation.local_llm._missing_optional_deps", return_value=[]):
        with patch("dau.foundation.local_llm.cuda_is_available", return_value=False):
            report = run_vram_spike()
    assert report.status == STATUS_CUDA_UNAVAILABLE
    assert report.cuda_available is False
    assert "DAU_LORA_ENABLED=0" in report.detail


def test_vram_spike_reports_model_access_separately_from_oom() -> None:
    with patch("dau.foundation.local_llm._missing_optional_deps", return_value=[]):
        with patch("dau.foundation.local_llm.cuda_is_available", return_value=True):
            with patch(
                "dau.foundation.local_llm.ensure_minilm_loaded",
                return_value=True,
            ):
                with patch(
                    "dau.foundation.local_llm.load_base_model_4bit",
                    side_effect=OSError("gated repo 401 Client Error"),
                ):
                    with patch("dau.foundation.local_llm.reset_vram_peak_stats"):
                        report = run_vram_spike()
    assert report.status == STATUS_MODEL_ACCESS
    assert report.oom is False
    assert report.base_model_loaded is False



def test_vram_spike_reports_missing_deps() -> None:
    with patch(
        "dau.foundation.local_llm._missing_optional_deps",
        return_value=["peft", "bitsandbytes"],
    ):
        report = run_vram_spike()
    assert report.status == STATUS_DEPS_MISSING
    assert "peft" in report.missing_deps


def test_write_and_read_go_report(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    report = VramSpikeReport(
        status=STATUS_GO,
        cuda_available=True,
        peak_allocated_bytes=VRAM_GO_BUDGET_BYTES // 2,
        peak_allocated_mib=1000.0,
        minilm_loaded=True,
        base_model_loaded=True,
        micro_train_ran=True,
        detail="ok",
    )
    path = write_vram_spike_report(report)
    assert path.is_file()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["status"] == STATUS_GO
    assert lora_plasticity_allowed() is True


def test_lora_plasticity_denied_without_report(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert lora_plasticity_allowed() is False
    assert lora_plasticity_allowed(
        VramSpikeReport(status=STATUS_NOGO, cuda_available=True)
    ) is False


def test_format_micro_train_texts_uses_lived_examples() -> None:
    example = LivedTraceExample(
        event_counter=1,
        prediction_error=0.2,
        delta_magnitude=0.1,
        delta_class="NORMAL",
        trauma_flag=False,
        drift_sum=0.0,
        loss_weight=0.8,
        prompt="Lived scalars: pe=0.200",
        completion="share resources with the pool",
    )
    texts = format_micro_train_texts([example])
    assert len(texts) == 1
    assert "Lived scalars: pe=0.200" in texts[0]
    assert "share resources with the pool" in texts[0]
    assert MICRO_TRAIN_PROMPT not in texts[0]


def test_format_micro_train_texts_falls_back_without_examples() -> None:
    texts = format_micro_train_texts(None)
    assert texts == [f"{MICRO_TRAIN_PROMPT}\n{MICRO_TRAIN_COMPLETION}"]
    assert format_micro_train_texts([]) == texts


def test_local_backend_requires_cuda(monkeypatch) -> None:
    from dau.foundation.llm_backend import LocalBackend

    monkeypatch.setattr(
        "dau.foundation.local_llm.cuda_is_available",
        lambda: False,
    )
    backend = LocalBackend()
    try:
        backend.complete([{"role": "user", "content": "hi"}])
        raised = False
    except NotImplementedError as exc:
        raised = True
        assert "CUDA" in str(exc)
    assert raised
