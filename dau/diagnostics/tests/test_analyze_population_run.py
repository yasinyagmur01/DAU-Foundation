"""The population report reader — and mostly, what it must REFUSE to say.

Every test here is about a way the report could look healthy while saying
nothing, because that is this project's actual failure mode: D-102 reported
`price={}` for every transition and looked fine, and D-090 / D-092 / D-059 were
all confident sentences written over a single measurement.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from dau.diagnostics.analyze_population_run import (
    NOT_EVALUABLE,
    arm_views,
    distinct_z,
    format_report,
    l2,
    level0_gate,
    level1_selection,
    level2_persistence,
    level3_arm_contrast,
    load_run,
    main,
    mean_z,
)

RESOURCE: str = "resource"
SOCIAL: str = "social"


def _agent(agent_id: str, z: dict[str, float] | None, events: int = 20) -> dict[str, Any]:
    return {
        "agent_id": agent_id,
        "f_agent": 0.4,
        "events_lived": events,
        "landmark": {
            "landmark_reached": z is not None,
            "landmark_drift_magnitudes": z,
        },
    }


def _generation(
    generation: int,
    agents: list[dict[str, Any]],
    *,
    price: dict[str, dict[str, float]] | None = None,
    w_variance: float | None = 0.25,
    w_distinct: int = 2,
    digest: str = "d0",
) -> dict[str, Any]:
    report = (
        None
        if w_variance is None
        else {
            "w_variance": w_variance,
            "w_n_distinct": w_distinct,
            "f_agent_spread": 0.3,
            "selection_measurable": w_distinct > 1,
        }
    )
    return {
        "generation": generation,
        "arm_digest": digest,
        "agents": agents,
        "reproduction_report": report,
        "price_for_previous_transition": price,
    }


def _run(arms: list[dict[str, Any]], **overrides: Any) -> dict[str, Any]:
    run = {
        "note": "exploratory, not pre-registered",
        "seeds": [9901],
        "n_agents": 2,
        "n_generations": 3,
        "events_budget": 30,
        "run_quality": "clean",
        "invariants": {"I0.3": True, "I4.1": True},
        "generations_informative": True,
        "replay": {
            "recorded_digest": "abc",
            "replay_digest": "abc",
            "n_generations": 2,
        },
        "arms": arms,
    }
    run.update(overrides)
    return run


def _three_arms(price: dict[str, dict[str, float]] | None = None) -> list[dict[str, Any]]:
    arms = []
    for index, name in enumerate(("lived", "null", "shuffle")):
        arms.append(
            {
                "arm": name,
                "seed": 9901,
                "generations": [
                    _generation(
                        1,
                        [
                            _agent(f"{name}-a0", {RESOURCE: 1.0 + index}),
                            _agent(f"{name}-a1", {RESOURCE: 2.0 + index}),
                        ],
                        digest=f"{name}-g1",
                    ),
                    _generation(
                        2,
                        [
                            _agent(f"{name}-h0", {RESOURCE: 1.5 + index}),
                            _agent(f"{name}-h1", {RESOURCE: 2.5 + index}),
                        ],
                        price=price,
                        digest=f"{name}-g2",
                    ),
                ],
            }
        )
    return arms


PRICE = {
    RESOURCE: {"selection": -0.201, "transmission": 0.05, "delta_zbar": -0.151}
}


def test_a_single_seed_can_never_produce_a_level_one_claim() -> None:
    """⭐ The rule that would have killed three dead findings.

    A level-1 claim asks for the SIGN to hold across seeds. One seed cannot
    answer that, and the report has to say so next to the number — not leave it
    to the reader, who by then has already seen a large covariance.
    """

    lines = "\n".join(level1_selection(_run(_three_arms(PRICE)), arm_views(_run(_three_arms(PRICE)))))

    assert "-0.201" in lines.replace("−", "-")
    assert NOT_EVALUABLE in lines
    assert "no level-1 claim is available" in lines


def test_two_seeds_stop_refusing_but_still_do_not_test() -> None:
    """The other side: the refusal has to be about the seed count, not blanket."""

    run = _run(_three_arms(PRICE), seeds=[9901, 9902])
    lines = "\n".join(level1_selection(run, arm_views(run)))

    assert "does not test" in lines
    assert "no level-1 claim is available" not in lines


def test_an_empty_price_partition_is_named_not_skipped() -> None:
    """⛔ D-102's exact failure: price={} everywhere and the run looked healthy.

    An empty partition must produce a LINE saying it is empty. Skipping it
    leaves a report whose level-1 section is simply absent, which reads as
    "nothing to report" rather than "the measurement did not land".
    """

    run = _run(_three_arms({}))
    lines = "\n".join(level1_selection(run, arm_views(run)))

    assert "empty" in lines


def test_var_w_zero_closes_the_gate_visibly() -> None:
    """Level 0 claims nothing, but it must SHOW when levels 1-2 are undefined."""

    arms = _three_arms(PRICE)
    for arm in arms:
        arm["generations"][0]["reproduction_report"]["w_variance"] = 0.0
        arm["generations"][0]["reproduction_report"]["w_n_distinct"] = 1
        arm["generations"][0]["reproduction_report"]["selection_measurable"] = False
    run = _run(arms)

    lines = "\n".join(level0_gate(run, arm_views(run)))

    assert "CLOSED" in lines


def test_g_less_than_three_is_called_out_in_level_zero() -> None:
    """A3/D-107 arriving from the reader's side."""

    run = _run(_three_arms(PRICE), generations_informative=False, n_generations=2)
    lines = "\n".join(level0_gate(run, arm_views(run)))

    assert "zero BY CONSTRUCTION" in lines


def test_a_diverged_replay_is_reported_as_diverged() -> None:
    """The report must not launder a failed determinism check."""

    run = _run(
        _three_arms(PRICE),
        replay={"recorded_digest": "abc", "replay_digest": "xyz", "n_generations": 2},
    )
    lines = "\n".join(level0_gate(run, arm_views(run)))

    assert "DIVERGED" in lines


def test_persistence_refuses_a_single_transition() -> None:
    """Level 2 compares transitions; one transition is not a comparison."""

    run = _run(_three_arms(PRICE))
    lines = "\n".join(level2_persistence(arm_views(run)))

    assert NOT_EVALUABLE in lines
    assert "at least 2" in lines


def test_persistence_prints_the_sequence_when_there_are_two() -> None:
    """And when it CAN be read, it is a sequence — never a fitted trend."""

    arms = _three_arms(PRICE)
    for arm in arms:
        arm["generations"].append(
            _generation(
                3,
                [_agent("h2", {RESOURCE: 3.0}), _agent("h3", {RESOURCE: 3.5})],
                price={
                    RESOURCE: {
                        "selection": -0.180,
                        "transmission": 0.0,
                        "delta_zbar": -0.180,
                    }
                },
                w_variance=None,
            )
        )
    lines = "\n".join(level2_persistence(arm_views(_run(arms))))

    assert "gen2:-0.201000" in lines.replace("−", "-").replace("+", "")
    assert "gen3:-0.180000" in lines.replace("−", "-").replace("+", "")
    assert "no slope is fitted" in lines


def test_identical_arm_digests_are_flagged() -> None:
    """Identical arms cannot differ in any endpoint — the reader must be told.

    This is not hypothetical: gen1 of the A2 verification run came out
    identical across all four arms, which is CORRECT there (arms only diverge
    once Channel 2 is in play) and would be fatal in gen2.
    """

    arms = _three_arms(PRICE)
    for arm in arms:
        arm["generations"][1]["arm_digest"] = "same"
    lines = "\n".join(level3_arm_contrast(arm_views(_run(arms))))

    assert "identical arms cannot differ" in lines


def test_arm_contrast_reports_all_three_pairwise_distances() -> None:
    """⭐ The equidistance pattern is the one that must be visible.

    B2's null looked like 0.3852 / 0.3812 / 0.3814. If the report only showed
    lived-vs-shuffle, that null would read as a signal.
    """

    lines = "\n".join(level3_arm_contrast(arm_views(_run(_three_arms(PRICE)))))

    assert "‖lived − null‖" in lines
    assert "‖lived − shuffle‖" in lines
    assert "‖null − shuffle‖" in lines
    assert "Equal distances" in lines


def test_missing_landmark_readings_are_not_imputed() -> None:
    """D-073 removed LOCF; averaging a fabricated zero would put it back."""

    view = arm_views(
        _run(
            [
                {
                    "arm": "lived",
                    "seed": 9901,
                    "generations": [
                        _generation(
                            1,
                            [
                                _agent("a0", {RESOURCE: 2.0}),
                                _agent("a1", None),
                            ],
                        )
                    ],
                }
            ]
        )
    )[0]

    # Mean over the ONE agent that has a reading, not over two with a zero.
    assert mean_z(view, [RESOURCE])[RESOURCE] == pytest.approx(2.0)
    assert view.landmark_reached == 1


def test_an_arm_without_any_reading_is_not_silently_distance_zero() -> None:
    """Two empty vectors are 0.0 apart, which would read as 'identical arms'."""

    arms = _three_arms(PRICE)
    for agent in arms[0]["generations"][0]["agents"]:
        agent["landmark"] = {
            "landmark_reached": False,
            "landmark_drift_magnitudes": None,
        }
    lines = "\n".join(level3_arm_contrast(arm_views(_run(arms))))

    assert NOT_EVALUABLE in lines


def test_distinct_z_does_not_round_away_a_difference() -> None:
    """D-103 found eight bit-identical agents; rounding would have hidden it."""

    view = arm_views(
        _run(
            [
                {
                    "arm": "lived",
                    "seed": 9901,
                    "generations": [
                        _generation(
                            1,
                            [
                                _agent("a0", {RESOURCE: 1.0}),
                                _agent("a1", {RESOURCE: 1.000000000001}),
                            ],
                        )
                    ],
                }
            ]
        )
    )[0]

    assert distinct_z(view) == 2


def test_the_forbidden_claims_travel_with_the_numbers() -> None:
    """A report read a month later has no memory of what it may not say."""

    report = format_report(_run(_three_arms(PRICE)), __import__("pathlib").Path("x.json"))

    assert "May NOT be claimed" in report
    assert "significant" in report
    assert "Price gives SELECTION" in report


def test_no_p_value_is_produced_anywhere() -> None:
    """P7-b: the first run is an estimation run, so there is nothing to test.

    Guards the whole module, not one function: a p-value appearing in this
    report is how "estimation run" quietly becomes "hypothesis test".
    """

    report = format_report(_run(_three_arms(PRICE)), __import__("pathlib").Path("x.json"))

    assert "p =" not in report
    assert "p-value" not in report
    assert "p<" not in report.replace(" ", "")


def test_l2_treats_an_absent_domain_as_zero_not_as_missing() -> None:
    """The endpoint's own rule: an unflagged domain has no accumulated drift."""

    assert l2({RESOURCE: 3.0}, {}, [RESOURCE, SOCIAL]) == pytest.approx(3.0)


def test_cli_writes_the_report(tmp_path) -> None:
    """End-to-end: a file in, a file out."""

    results = tmp_path / "run.json"
    results.write_text(json.dumps(_run(_three_arms(PRICE))), encoding="utf-8")
    out = tmp_path / "report.md"

    main(["--results", str(results), "--out", str(out)])

    assert "Level 3" in out.read_text(encoding="utf-8")
    assert load_run(results)["run_quality"] == "clean"


def test_reached_landmark_with_no_flags_is_a_zero_reading_not_a_missing_one() -> None:
    """⭐ The two cases the JSON writes identically as `{}` — and they are opposites.

    A reached landmark with no drift flags is a MEASUREMENT of zero drift
    (D-002: an unflagged domain counts as 0). A life that ended before the
    landmark has NO reading at all, and imputing one would reinstate the LOCF
    that D-073 removed.

    Measured, not hypothetical: the first version of this module dropped both,
    and reported "not evaluable" for every arm contrast of a run in which all
    twelve agents had a perfectly good reading of zero.
    """

    arms = _three_arms(PRICE)
    for arm in arms:
        for agent in arm["generations"][0]["agents"]:
            agent["landmark"] = {
                "landmark_reached": True,
                "landmark_drift_magnitudes": {},
            }
    # lived's gen-1 heirs did move; the others did not.
    arms[0]["generations"][1]["agents"][0]["landmark"] = {
        "landmark_reached": True,
        "landmark_drift_magnitudes": {RESOURCE: 2.0},
    }
    views = arm_views(_run(arms))
    gen1 = [v for v in views if v.generation == 1]

    for view in gen1:
        assert len(view.z_by_agent) == 2, "a zero reading was dropped"
        assert mean_z(view, [RESOURCE]) == {RESOURCE: 0.0}
    lines = "\n".join(level3_arm_contrast(views))
    assert "‖lived − null‖ = 0.000000" in lines, (
        "three arms of measured zeros are 0.0 apart — that is a finding, "
        "not an absence"
    )
    assert NOT_EVALUABLE not in lines.split("gen2:")[0]


# ---------------------------------------------------------------------------
# D-111 — a checkpoint is not a result
# ---------------------------------------------------------------------------


def test_a_checkpoint_file_is_refused_not_reported() -> None:
    """A partial run differs from a result by one boolean and some missing arms.

    A report built from it would look exactly like a smaller, healthy run --
    fewer arms, fewer generations, everything else in place. Refusing is the
    only reading that cannot be mistaken for a finding.
    """

    from dau.diagnostics.analyze_population_run import IncompleteRun

    import pathlib

    run = _run(_three_arms(PRICE), complete=False)
    del run["run_quality"]
    del run["invariants"]

    with pytest.raises(IncompleteRun, match="CHECKPOINT"):
        format_report(run, pathlib.Path("run.json.partial.json"))


def test_a_run_from_before_checkpointing_is_still_reportable() -> None:
    """Absent is not False: files written before D-111 are complete.

    B1's results have no `complete` key at all. Testing "is True" instead of
    "is not False" would refuse every run this project has already made.
    """

    import pathlib

    run = _run(_three_arms(PRICE))
    assert "complete" not in run

    assert "Level 3" in format_report(run, pathlib.Path("old.json"))
