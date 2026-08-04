"""Unit tests for convention micro-pilot harness (NPC baseline)."""

from __future__ import annotations

import pytest

from dau.foundation.lod import (
    NPC_ACTION_CONSERVE,
    NPC_ACTION_COOPERATE,
    NPC_ACTION_EXTRACT_MODERATE,
    NPC_POOL_RATIO_CONSERVE,
)
from dau.foundation.social import (
    OUTCOME_COORDINATE,
    OUTCOME_COOPERATE,
    OUTCOME_DEADLOCK,
    OUTCOME_DEFECT,
)
from dau.society.environment import EnvironmentState
from dau.society.run_convention_pilot import (
    CONVENTION_MODAL_SHARE_MIN,
    CONVENTION_STREAK_MIN,
    EXTRACTION_COOPERATE,
    EXTRACTION_DEFECT,
    N_AGENTS,
    SENSOR_LABEL,
    RoundRecord,
    agent_ids,
    decide_npc,
    decision_to_extraction,
    decision_to_outcome,
    detect_convention,
    domain_for_agent,
    pilot_summary_dict,
    run_convention_pilot,
)


def test_decision_to_outcome_npc_tokens() -> None:
    """NPC action tokens map to the expected OUTCOME_* labels."""

    assert decision_to_outcome(NPC_ACTION_COOPERATE) == OUTCOME_COOPERATE
    assert decision_to_outcome(NPC_ACTION_EXTRACT_MODERATE) == OUTCOME_DEFECT
    assert decision_to_outcome(NPC_ACTION_CONSERVE) == OUTCOME_COORDINATE


def test_decision_to_outcome_keyword_and_unknown() -> None:
    """Free-text keywords map deterministically; unknown → deadlock."""

    assert decision_to_outcome("I will extract and take more") == OUTCOME_DEFECT
    assert decision_to_outcome("I announce harvest of 27%") == OUTCOME_DEFECT
    assert decision_to_outcome("I choose to cooperate and share") == OUTCOME_COOPERATE
    assert decision_to_outcome("xyz unexplained mutter") == OUTCOME_DEADLOCK


def test_decision_to_extraction_amounts() -> None:
    """Cooperate restrains harvest; defect over-extracts; parsed units win."""

    assert decision_to_extraction(NPC_ACTION_COOPERATE) == EXTRACTION_COOPERATE
    assert decision_to_extraction(NPC_ACTION_EXTRACT_MODERATE) == EXTRACTION_DEFECT
    assert EXTRACTION_DEFECT > EXTRACTION_COOPERATE
    assert decision_to_extraction(
        "I announce my intention to harvest 0.5 units of the resource."
    ) == pytest.approx(0.5)
    assert decision_to_extraction("harvest 10%") == pytest.approx(10.0)


def test_agent_ids_and_heterogeneous_domains() -> None:
    """Three agents get distinct domain assignments (not identical clones)."""

    ids = agent_ids(N_AGENTS)
    assert len(ids) == N_AGENTS
    domains = [domain_for_agent(agent_id) for agent_id in ids]
    assert len(set(domains)) == N_AGENTS


def test_scarcity_forces_all_conserve() -> None:
    """Below NPC_POOL_RATIO_CONSERVE every agent conserves — scarcity rule, not social.

    Characterizes the NPC 'fake convention' path so LLM results are not
    confused with pool-threshold collapse to conserve.
    """

    scarce_ratio = NPC_POOL_RATIO_CONSERVE - 0.01
    for agent_id in agent_ids(N_AGENTS):
        assert decide_npc(agent_id, scarce_ratio) == NPC_ACTION_CONSERVE


def test_detect_convention_streak() -> None:
    """Convention requires CONVENTION_STREAK_MIN high-share rounds in a row."""

    def _round(index: int, share: float) -> RoundRecord:
        return RoundRecord(
            round_index=index,
            decisions={},
            outcomes={},
            extractions={},
            outcome_entropy=0.0,
            modal_outcome=OUTCOME_COORDINATE,
            modal_share=share,
            format_share=0.0,
            restraint_share=0.0,
            pool_after=50.0,
            pool_ratio_after=0.5,
            collapsed=False,
        )

    low = CONVENTION_MODAL_SHARE_MIN - 0.1
    high = CONVENTION_MODAL_SHARE_MIN
    short = [_round(i, high) for i in range(1, CONVENTION_STREAK_MIN)]
    assert detect_convention(short) == (False, None)

    broken = [_round(1, high), _round(2, low), _round(3, high)]
    assert detect_convention(broken)[0] is False

    long_enough = [_round(i, high) for i in range(1, CONVENTION_STREAK_MIN + 1)]
    detected, onset = detect_convention(long_enough)
    assert detected is True
    assert onset == 1


def test_format_share_ignores_numeric_quantities() -> None:
    """Same announcement skeleton with different numbers → format_share=1."""

    from dau.society.run_convention_pilot import format_share, format_template

    assert format_template("collect 0.5 units") == format_template("collect 0.9 units")
    share = format_share(
        {
            "a": "I announce collect 0.5 units from the pool.",
            "b": "I announce collect 0.9 units from the pool.",
            "c": "I announce collect 0.2 units from the pool.",
        }
    )
    assert share == pytest.approx(1.0)


def test_restraint_share_separates_defect_lock() -> None:
    """All-defect is not restraint sync; cooperate/coordinate is."""

    from dau.society.run_convention_pilot import restraint_share

    assert restraint_share(
        {"a": OUTCOME_DEFECT, "b": OUTCOME_DEFECT, "c": OUTCOME_DEFECT}
    ) == pytest.approx(0.0)
    assert restraint_share(
        {
            "a": OUTCOME_COOPERATE,
            "b": OUTCOME_COORDINATE,
            "c": OUTCOME_COOPERATE,
        }
    ) == pytest.approx(1.0)


def test_npc_pilot_reports_split_convention_fields() -> None:
    """Summary exposes format vs restraint flags (overnight misread fix)."""

    result = run_convention_pilot(n_agents=3, n_rounds=10)
    summary = pilot_summary_dict(result)
    assert "format_convention_detected" in summary
    assert "restraint_convention_detected" in summary
    assert "mean_format_share" in summary
    assert "mean_restraint_share" in summary


def test_run_convention_pilot_labels_and_closes_loop() -> None:
    """Full NPC pilot returns labeled metrics and advances the shared pool."""

    result = run_convention_pilot(n_agents=3, n_rounds=10)
    summary = pilot_summary_dict(result)
    assert summary["sensor_label"] == SENSOR_LABEL
    assert summary["mode"] == "npc_baseline"
    assert result.n_rounds >= 1
    assert len(result.transcript) == result.n_rounds * 3
    assert result.rounds[0].extractions
    assert EnvironmentState().event_counter == 0
    assert sum(result.rounds[0].extractions.values()) > 0.0


def test_run_convention_pilot_early_entropy_then_possible_scarcity_lock() -> None:
    """Early rounds are heterogeneous; late scarcity may lock coordinate.

    Documents NPC baseline dynamics without claiming spontaneous social convention.
    """

    result = run_convention_pilot(n_agents=3, n_rounds=50)
    assert result.rounds[0].outcome_entropy > 0.0
    if result.collapsed or result.rounds[-1].pool_ratio_after < NPC_POOL_RATIO_CONSERVE:
        assert result.rounds[-1].modal_outcome == OUTCOME_COORDINATE
        assert result.rounds[-1].modal_share == pytest.approx(1.0)
