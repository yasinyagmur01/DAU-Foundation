"""Tests for System 2→1 nuance-loss micro-pilot."""

from __future__ import annotations

from dau.foundation.lod import CognitiveMode, NPC_ACTION_EXTRACT_MODERATE
from dau.society.run_convention_pilot import SENSOR_LABEL
from dau.society.run_nuance_loss_pilot import (
    demonstrate_lod_deescalation,
    pilot_summary_dict,
    run_nuance_loss_pilot,
)


def test_nuance_loss_detected_scripted_vs_npc() -> None:
    """Heterogeneous System-2 scripts collapse to one NPC action under System 1."""

    result = run_nuance_loss_pilot()
    assert result.sensor_label == SENSOR_LABEL
    assert result.nuance_loss_detected is True
    assert result.pre_unique_decisions > 1
    assert result.post_unique_decisions == 1
    assert result.post_decisions[0] == NPC_ACTION_EXTRACT_MODERATE


def test_lod_deescalation_after_cooldown() -> None:
    """update_lod reaches System 1 after sustained low T_cognitive."""

    lod = demonstrate_lod_deescalation()
    assert lod.mode == CognitiveMode.SYSTEM_1


def test_nuance_summary_keys() -> None:
    """Summary dict exposes the core comparison fields."""

    summary = pilot_summary_dict(run_nuance_loss_pilot())
    assert summary["nuance_loss_detected"] is True
    assert "pre_unique_decisions" in summary
    assert "post_unique_decisions" in summary
