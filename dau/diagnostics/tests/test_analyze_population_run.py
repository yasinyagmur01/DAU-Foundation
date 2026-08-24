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


def _multi_seed(
    price: dict[str, dict[str, float]] | None = None,
    seeds: tuple[int, ...] = (9901, 9902, 9903),
) -> list[dict[str, Any]]:
    """⭐ K2's fixture: three seeds AND three arms, one block each (D-127).

    Every fixture in this module used to carry a single seed, and that is
    precisely why two seed-collapsing defects lived here unseen: with one seed
    there is no second value to collapse. Two reporting sections keyed their
    aggregates by arm or by generation alone, and the last seed silently
    overwrote (level 3) or was concatenated into (level 2) the others.

    ⛔ Any section that aggregates over a dimension must be tested with at
    least two values in that dimension, or the test cannot see the collapse.
    """

    arms: list[dict[str, Any]] = []
    for seed in seeds:
        arms.extend(_three_arms(price, seed=seed))
    return arms


def _three_arms(
    price: dict[str, dict[str, float]] | None = None, seed: int = 9901
) -> list[dict[str, Any]]:
    arms = []
    for index, name in enumerate(("lived", "null", "shuffle")):
        arms.append(
            {
                "arm": name,
                "seed": seed,
                "generations": [
                    _generation(
                        1,
                        [
                            _agent(f"{name}-a0", {RESOURCE: 1.0 + index}),
                            _agent(f"{name}-a1", {RESOURCE: 2.0 + index}),
                        ],
                        digest=f"{name}-s{seed}-g1",
                    ),
                    _generation(
                        2,
                        [
                            _agent(f"{name}-h0", {RESOURCE: 1.5 + index}),
                            _agent(f"{name}-h1", {RESOURCE: 2.5 + index}),
                        ],
                        price=price,
                        digest=f"{name}-s{seed}-g2",
                    ),
                    # A THIRD generation, so each (arm, seed) lineage really
                    # has two closed transitions (D-127). Without it the
                    # persistence section could only reach its minimum by
                    # pooling seeds — which is exactly the defect: the old code
                    # printed a "persistence" sequence for a run where no
                    # lineage had two transitions at all.
                    _generation(
                        3,
                        [
                            _agent(f"{name}-h0h0", {RESOURCE: 1.7 + index}),
                            _agent(f"{name}-h1h0", {RESOURCE: 2.7 + index}),
                        ],
                        price=price,
                        digest=f"{name}-s{seed}-g3",
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

    # Trimmed to two generations on purpose: the shared fixture now carries
    # three, because a lineage needs two closed transitions for the section to
    # be readable at all (D-127). This test is about the OTHER side — one
    # transition must be refused — so it builds that case explicitly instead of
    # depending on how many generations the fixture happens to have.
    arms = _three_arms(PRICE)
    for arm in arms:
        arm["generations"] = arm["generations"][:2]
    run = _run(arms)
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


# ---------------------------------------------------------------------------
# D-113 — interval estimates (Dienes' second solution), never a test
# ---------------------------------------------------------------------------


def _with_profiles(arms, peak: float, crossings: int):
    """Give every agent a delta profile; the first `crossings` of them cross."""

    from dau.foundation.delta import DELTA_THRESHOLD_DEEP

    left = crossings
    for arm in arms:
        for gen in arm["generations"]:
            for agent in gen["agents"]:
                crossed = left > 0
                left -= 1 if crossed else 0
                top = DELTA_THRESHOLD_DEEP + 0.1 if crossed else peak
                agent["delta_profile"] = {
                    "n_events": 5,
                    "max": top,
                    "mean": top / 2,
                    "n_at_or_above_trauma": 1 if crossed else 0,
                    "headroom_to_trauma": DELTA_THRESHOLD_DEEP - top,
                }
    return arms


def test_wilson_interval_stays_inside_zero_and_one_at_a_rare_rate() -> None:
    """⭐ Why Wilson and not Wald: the quantity we estimate IS rare.

    Wald's interval runs below zero for small p and its coverage collapses
    exactly there (McGrath & Burke, arXiv:2109.02516). A lower bound of -0.005
    would be nonsense printed next to a real measurement.
    """

    from dau.diagnostics.analyze_population_run import wilson_interval

    point, low, high = wilson_interval(3, 72)

    assert point == pytest.approx(3 / 72)
    assert 0.0 <= low < point < high <= 1.0
    # The Wald lower bound for this case is negative; Wilson's is not.
    wald_low = 3 / 72 - 1.96 * ((3 / 72) * (1 - 3 / 72) / 72) ** 0.5
    assert wald_low < 0.0 < low


def test_zero_crossings_still_produce_an_upper_bound() -> None:
    """⭐ "It never happened" is not "it cannot happen".

    A run with no crossings must still say how rare the event could be and
    still be consistent with the data — that upper bound is the whole reason
    an interval is reported instead of a bare zero.
    """

    from dau.diagnostics.analyze_population_run import wilson_interval

    point, low, high = wilson_interval(0, 72)

    assert point == 0.0
    assert low == 0.0
    assert high > 0.0, "a bare zero would claim impossibility"


def test_the_report_shows_headroom_and_never_a_p_value() -> None:
    """The section must carry the interval AND the refusal to test."""

    from dau.diagnostics.analyze_population_run import trauma_headroom

    run = _run(_with_profiles(_three_arms(PRICE), peak=0.68, crossings=1))
    lines = "\n".join(trauma_headroom(run))

    assert "Wilson interval" in lines
    assert "0.6800" in lines, "the near-miss peak has to be visible"
    assert "An interval, not a test" in lines
    assert "p =" not in lines and "p-value" not in lines


def test_a_run_without_delta_profiles_says_so_instead_of_reporting_zero() -> None:
    """B1 predates D-112. Silence there would read as "nothing came close"."""

    from dau.diagnostics.analyze_population_run import trauma_headroom

    lines = "\n".join(trauma_headroom(_run(_three_arms(PRICE))))

    assert "predates D-112" in lines
    assert "0/0" not in lines


# ---------------------------------------------------------------------------
# D-117 — the commons channel in the report
# ---------------------------------------------------------------------------


def _with_crisis(arms, n_crisis_lives: int):
    """Give the first ``n_crisis_lives`` agents a famine and nothing else.

    Deliberately the shape of seed 9904: the individual channel says nothing
    came close, while every one of those lives carries drift.
    """

    from dau.foundation.delta import DELTA_THRESHOLD_DEEP

    left = n_crisis_lives
    for arm in arms:
        for gen in arm["generations"]:
            for agent in gen["agents"]:
                scarred = left > 0
                left -= 1 if scarred else 0
                agent["delta_profile"] = {
                    "n_events": 5,
                    "max": 0.10,
                    "mean": 0.05,
                    "n_at_or_above_trauma": 0,
                    "headroom_to_trauma": DELTA_THRESHOLD_DEEP - 0.10,
                    "channel": "individual",
                    "crisis": {
                        "n_events": 1 if scarred else 0,
                        "n_crisis_events": 1 if scarred else 0,
                        "max": 1.0 if scarred else None,
                        "mean": 1.0 if scarred else None,
                        "n_at_or_above_trauma": 1 if scarred else 0,
                        "headroom_to_trauma": (
                            DELTA_THRESHOLD_DEEP - 1.0 if scarred else None
                        ),
                    },
                    "n_at_or_above_trauma_either_channel": 1 if scarred else 0,
                }
    return arms


def test_the_report_names_the_channel_that_filled_z() -> None:
    """⭐ D-115's blind spot, closed in the reader as well as the log.

    Individual crossings are zero here and lives are still scarred. A report
    that showed only the first channel would say "nothing came close" about a
    universe that rewrote every agent's drift map — which is exactly what it
    said about seed 9904.
    """

    from dau.diagnostics.analyze_population_run import trauma_headroom

    lines = "\n".join(trauma_headroom(_run(_with_crisis(_three_arms(PRICE), 4))))

    assert "lives that saw a crisis event: 4" in lines
    assert "lives the crisis scarred at or above the trauma threshold: 4" in lines
    assert "individual channel" in lines and "commons channel" in lines
    assert "NO between-agent information" in lines
    assert "p =" not in lines and "p-value" not in lines


def test_a_run_without_the_crisis_block_says_so_instead_of_reporting_zero() -> None:
    """The headroom runs predate D-117; silence would repeat the same error."""

    from dau.diagnostics.analyze_population_run import trauma_headroom

    run = _run(_with_profiles(_three_arms(PRICE), peak=0.68, crossings=1))
    lines = "\n".join(trauma_headroom(run))

    assert "predates D-117" in lines
    assert "lives that saw a crisis event" not in lines


def test_a_degenerate_cell_is_labelled_not_printed_as_a_plain_zero() -> None:
    """⭐ D-121: the single most likely misreading of this whole report.

    An unlabelled 0.000000 looks exactly like "selection acted and came out
    flat". The report must say the term could not have been measured.
    """

    from dau.diagnostics.analyze_population_run import level1_selection
    from dau.generation.reproduction import PRICE_KEY_ESTIMABLE

    flat = {
        "resource": {
            "selection": 0.0,
            "transmission": 0.2,
            "delta_zbar": 0.2,
            "z_variance": 0.0,
            PRICE_KEY_ESTIMABLE: False,
        }
    }
    from dau.diagnostics.analyze_population_run import arm_views

    run = _run(_three_arms(flat))
    lines = "\n".join(level1_selection(run, arm_views(run)))

    assert "UNDEFINED" in lines
    assert "NOT 'no selection was measured'" in lines


def test_an_estimable_cell_is_not_labelled() -> None:
    """The label must discriminate, or it is decoration."""

    from dau.diagnostics.analyze_population_run import level1_selection
    from dau.generation.reproduction import PRICE_KEY_ESTIMABLE

    varied = {
        "resource": {
            "selection": 0.0,
            "transmission": 0.2,
            "delta_zbar": 0.2,
            "z_variance": 0.25,
            PRICE_KEY_ESTIMABLE: True,
        }
    }
    from dau.diagnostics.analyze_population_run import arm_views

    run = _run(_three_arms(varied))
    lines = "\n".join(level1_selection(run, arm_views(run)))

    assert "UNDEFINED" not in lines


def test_a_run_without_the_control_says_so_instead_of_reporting_a_null() -> None:
    """Old runs have no control; silence would read as a control that came out flat."""

    from dau.diagnostics.analyze_population_run import positive_control

    from dau.diagnostics.analyze_population_run import arm_views

    run = _run(_three_arms(PRICE))
    lines = "\n".join(positive_control(arm_views(run)))

    assert "predates D-121" in lines


# ---------------------------------------------------------------------------
# D-127 / K2 — the seed dimension must survive every aggregation
# ---------------------------------------------------------------------------


def test_level3_reports_every_seed_not_just_the_last() -> None:
    """⛔ The defect that cost the most: three seeds reported as one.

    `by_generation[generation][arm] = view` let the last seed overwrite the
    others. The section looked healthy and printed one arm contrast per
    generation — and the arm contrast IS the inheritance question, so a
    collapsed one is the most expensive wrong number this report can print.
    """

    from dau.diagnostics.analyze_population_run import arm_views, level3_arm_contrast

    run = _run(_multi_seed(PRICE), seeds=[9901, 9902, 9903])
    lines = "\n".join(level3_arm_contrast(arm_views(run)))

    for seed in (9901, 9902, 9903):
        assert f"s{seed}" in lines, f"seed {seed} vanished from the arm contrast"


def test_level2_keeps_each_seed_its_own_sequence() -> None:
    """A persistence sequence is about ONE lineage over time.

    Three seeds appended into one list printed "gen2 → gen3 → gen2 → gen3 → …",
    which reads as a single trajectory and was three unrelated ones.
    """

    from dau.diagnostics.analyze_population_run import arm_views, level2_persistence

    run = _run(_multi_seed(PRICE), seeds=[9901, 9902, 9903])
    rows = [ln for ln in level2_persistence(arm_views(run)) if "→" in ln]

    assert rows, "no sequence rows produced"
    for row in rows:
        # One row per (arm, seed): a row may not carry more transitions than
        # a single lineage has.
        assert row.count("gen") <= 2, f"a row mixed seeds: {row}"
    for seed in (9901, 9902, 9903):
        assert any(f"s{seed}" in row for row in rows), f"seed {seed} unlabelled"


def test_an_empty_partition_is_not_called_a_pre_D121_run() -> None:
    """The label must fire on a missing FIELD, never on a missing DOMAIN.

    A cell whose z carried no domains has an empty partition; calling that
    "predates D-121" was false on a run that has the field everywhere it
    applies.
    """

    from dau.diagnostics.analyze_population_run import arm_views, level1_selection

    run = _run(_multi_seed({}), seeds=[9901, 9902, 9903])
    lines = "\n".join(level1_selection(run, arm_views(run)))

    # Narrow on purpose: the positive-control section legitimately says
    # "predates D-121" for a fixture that carries no control, and that message
    # is correct. What must never appear is the ESTIMABILITY one.
    assert "estimability ABSENT" not in lines
    assert "empty" in lines, "an empty partition must still be reported as empty"


# ---------------------------------------------------------------------------
# D-148 — what the report could not say about ITSELF (D-147's hunt)
# ---------------------------------------------------------------------------


def test_every_listing_says_which_seed_the_row_belongs_to() -> None:
    """⭐ AV-1: three seeds printed the same label with different numbers.

    D-127 fixed the COLLAPSE in levels 2 and 3, where an arm-keyed dict let the
    last seed overwrite the others. The listings in levels 0 and 1 never
    collapsed — every row was printed — but they carried no seed, so `lived
    gen1` appeared three times with three different Var(w) values and a reader
    could not attribute any of them. A half-applied fix.

    Measured on the real C2 output before this change: 27 Var(w) rows, 9 of
    them labelled `lived gen…`, none of them attributable.
    """

    # ⚠ price=... on purpose: with the default None every level-1 row is
    # skipped and the section produces no lines at all, so a seedless heading
    # there would sail through. Measured — the first version of this test did
    # exactly that and the mutation "drop the seed from level 1" survived it.
    run = _run(_multi_seed(price={RESOURCE: {"selection": 0.1,
                                             "transmission": 0.0,
                                             "delta_zbar": 0.1,
                                             "z_variance": 0.5,
                                             "selection_estimable": True}}))
    views = arm_views(run)
    level1 = level1_selection(run, views)
    assert level1, "level 1 produced no rows — the test cannot see its labels"
    text = "\n".join(level0_gate(run, views) + level1)

    for seed in (9901, 9902, 9903):
        assert f"s{seed}" in text, f"seed {seed} is not attributable anywhere"
    # And the ambiguous form must be gone: a row that starts with the arm name
    # is a row whose seed the reader has to guess.
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("lived", "null", "shuffle")):
            raise AssertionError(f"row without a seed label: {line!r}")


def test_a_distance_made_only_of_one_sided_axes_is_marked_as_such() -> None:
    """⭐⭐ AV-2: is this distance a DIFFERENCE, or one arm's own magnitude?

    ⚠ The arithmetic is right and stays right: an unflagged domain really has
    no accumulated magnitude, so absent IS zero. What `l2` alone cannot say is
    whether both arms entered the axis. Measured on C2 (s9912, gen2):
    ‖lived − null‖ = 0.087899 and 100% of it came from `energy`, an axis `null`
    never entered — a distance that reads like a contrast and is a presence.

    RECONCILIATION §G.2 named this reading on 2026-08-11 for the single-lineage
    design. It survived into the population reader because nothing reported the
    decomposition, which is what this pins.
    """

    from dau.diagnostics.analyze_population_run import one_sided_share

    domains = ["energy", "resource"]
    only_one_entered = ({"energy": 0.0879, "resource": 0.0},
                        {"energy": 0.0, "resource": 0.0})
    both_entered = ({"energy": 0.4, "resource": 0.0},
                    {"energy": 0.1, "resource": 0.0})

    shared, one_sided, share = one_sided_share(*only_one_entered, domains)
    assert (shared, one_sided) == (0, 1)
    assert share == pytest.approx(1.0), "a pure presence read as a difference"

    shared, one_sided, share = one_sided_share(*both_entered, domains)
    assert (shared, one_sided) == (1, 0)
    assert share == pytest.approx(0.0), "a real difference marked as one-sided"

    # ⭐ The mixed case is the one that pins share as a FRACTION rather than a
    # count. With a single one-sided axis both readings equal 1.0 and the two
    # are indistinguishable — measured: the mutation "return the count instead
    # of the fraction" survived a test that only had that case.
    mixed = (
        {"energy": 0.5, "resource": 0.3, "social": 0.0},
        {"energy": 0.1, "resource": 0.0, "social": 0.0},
    )
    shared, one_sided, share = one_sided_share(*mixed, ["energy", "resource", "social"])
    assert (shared, one_sided) == (1, 1)
    expected = 0.3 ** 2 / (0.4 ** 2 + 0.3 ** 2)
    assert share == pytest.approx(expected)
    assert 0.0 < share < 1.0, "a fraction collapsed to a count"


def test_identical_arms_attribute_nothing_rather_than_dividing_by_zero() -> None:
    """Two arms that coincide have no distance, so nothing to attribute."""

    from dau.diagnostics.analyze_population_run import one_sided_share

    same = {"energy": 0.3, "resource": 0.0}
    shared, one_sided, share = one_sided_share(same, dict(same), ["energy", "resource"])

    assert one_sided == 0
    assert share == 0.0, "an attribution was invented where there is no distance"


def test_the_one_sided_warning_reaches_the_report(monkeypatch) -> None:
    """K3 — the decomposition is worthless if level 3 never prints it."""

    lopsided = [
        {
            "arm": "lived", "seed": 9901,
            "generations": [_generation(1, [_agent("l0", {"energy": 0.4}),
                                            _agent("l1", {"energy": 0.4})])],
        },
        {
            "arm": "null", "seed": 9901,
            "generations": [_generation(1, [_agent("n0", {RESOURCE: 0.0}),
                                            _agent("n1", {RESOURCE: 0.0})])],
        },
    ]
    text = "\n".join(level3_arm_contrast(arm_views(_run(lopsided))))

    assert "only one arm entered" in text
    assert "100%" in text


# ── D-176/B3: reading a partitioned run ──────────────────────────────────────
# The verifying run is 70 GPU-hours and lands as one file per night. Until B3
# this module took a single --results path, so a partitioned run would have
# finished with nothing able to read it.


def _night(seeds: tuple[int, ...], **overrides: Any) -> dict[str, Any]:
    arms: list[dict[str, Any]] = []
    for seed in seeds:
        arms.extend(_three_arms(seed=seed))
    return _run(arms, seeds=list(seeds), complete=True, **overrides)


def test_two_nights_merge_into_one_study(tmp_path) -> None:
    """K2: two files AND two seeds each, or a collapse could not be seen."""

    from pathlib import Path

    from dau.diagnostics.analyze_population_run import merge_runs

    first = _night((9901, 9902))
    second = _night((9903, 9904))

    merged = merge_runs([first, second], [Path("a.json"), Path("b.json")])

    assert merged["seeds"] == [9901, 9902, 9903, 9904]
    assert len(merged["arms"]) == len(first["arms"]) + len(second["arms"])
    # Every seed still reaches the reader as its own row: pooling must not
    # aggregate the repetition unit away (D-140 / Lazic 2010).
    assert {view.seed for view in arm_views(merged)} == {9901, 9902, 9903, 9904}


def test_a_repeated_seed_is_refused_as_pseudoreplication() -> None:
    """The failure a partitioned run invites: re-running a night that looked off.

    The repetition unit is the seed, so counting one twice inflates N without
    adding information — and nothing in the report would show it.
    """

    from pathlib import Path

    from dau.diagnostics.analyze_population_run import merge_runs

    with pytest.raises(ValueError, match="pseudoreplication"):
        merge_runs(
            [_night((9901, 9902)), _night((9902, 9903))],
            [Path("a.json"), Path("b.json")],
        )


def test_files_from_different_instruments_are_refused() -> None:
    """Pooling two designs would silently average two experiments."""

    from pathlib import Path

    from dau.diagnostics.analyze_population_run import merge_runs

    with pytest.raises(ValueError, match="different instrument or design"):
        merge_runs(
            [_night((9901,)), _night((9902,), n_generations=4)],
            [Path("a.json"), Path("b.json")],
        )


def test_a_checkpoint_cannot_be_merged_in() -> None:
    """The single-file refusal (D-111) must not have a back door."""

    from pathlib import Path

    from dau.diagnostics.analyze_population_run import IncompleteRun, merge_runs

    partial = _night((9902,))
    partial["complete"] = False

    with pytest.raises(IncompleteRun):
        merge_runs([_night((9901,)), partial], [Path("a.json"), Path("b.json")])


def test_one_flagged_night_cannot_be_averaged_into_a_clean_study() -> None:
    """⛔ The merged stamp is the conservative one, and the ledger survives.

    A night that flagged and a night that did not are different measurements.
    Reporting the pair as `clean` is exactly the silent fake result the whole
    preflight system exists to prevent.
    """

    from pathlib import Path

    from dau.diagnostics.analyze_population_run import merge_runs

    clean = _night((9901,))
    flagged = _night(
        (9902,),
        run_quality="flagged",
        invariants={"I0.3": True, "I4.1": True, "I4.2": False},
    )

    merged = merge_runs([clean, flagged], [Path("a.json"), Path("b.json")])

    assert merged["run_quality"] != "clean"
    assert merged["invariants"]["I4.2"] is False
    assert merged["invariants"]["I0.3"] is True
    report = "\n".join(level0_gate(merged, arm_views(merged)))
    assert "merged from 2 files" in report
    assert "b.json" in report and "I4.2" in report


def test_a_never_evaluated_invariant_does_not_become_a_pass() -> None:
    """None is not True — the distinction D-121 spent a decision on."""

    from pathlib import Path

    from dau.diagnostics.analyze_population_run import merge_runs

    merged = merge_runs(
        [
            _night((9901,), invariants={"I5.4": None}),
            _night((9902,), invariants={"I5.4": None}),
        ],
        [Path("a.json"), Path("b.json")],
    )

    assert merged["invariants"]["I5.4"] is None


def test_a_gate_that_only_one_night_evaluated_is_not_reported_as_failed() -> None:
    """⛔ Found by a surviving mutant, not by design.

    The first version of the merge fell through to `all(v is True)`, so an
    invariant that PASSED one night and was never evaluated the other came out
    FAILED — the D-121 distinction inverted. None is the honest answer: the
    study was not fully checked, and the per-file ledger says by whom.
    """

    from pathlib import Path

    from dau.diagnostics.analyze_population_run import merge_runs

    merged = merge_runs(
        [
            _night((9901,), invariants={"I5.4": True}),
            _night((9902,), invariants={"I5.4": None}),
        ],
        [Path("a.json"), Path("b.json")],
    )

    assert merged["invariants"]["I5.4"] is None, "not evaluated is not failed"


def test_the_merged_report_never_claims_one_nights_replay_for_the_study() -> None:
    """Each night replayed its own first seed; there is no study-level replay."""

    from pathlib import Path

    from dau.diagnostics.analyze_population_run import (
        RUN_KEY_REPLAY,
        merge_runs,
    )

    merged = merge_runs(
        [_night((9901,)), _night((9902,))], [Path("a.json"), Path("b.json")]
    )

    assert RUN_KEY_REPLAY not in merged
    report = "\n".join(level0_gate(merged, arm_views(merged)))
    assert "I4.1 replay=identical" in report
    assert "determinism is not demonstrated" not in report


def test_cli_reports_several_files_at_once(tmp_path) -> None:
    """K3 — the wiring, not just merge_runs (the whole point of B3)."""

    first = tmp_path / "night1.json"
    second = tmp_path / "night2.json"
    first.write_text(json.dumps(_night((9901, 9902))), encoding="utf-8")
    second.write_text(json.dumps(_night((9903, 9904))), encoding="utf-8")
    out = tmp_path / "report.md"

    main(["--results", str(first), str(second), "--out", str(out)])

    report = out.read_text(encoding="utf-8")
    assert "night1.json + night2.json" in report
    assert "merged from 2 files" in report
    for seed in (9901, 9902, 9903, 9904):
        assert f"s{seed}" in report
