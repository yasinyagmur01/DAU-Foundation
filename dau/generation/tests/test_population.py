"""Generation bookkeeping (E2-4a): parentage plans and closing the Price partition."""

from __future__ import annotations

import random
import statistics

import pytest

from dau.generation.population import (
    FIRST_GENERATION,
    Candidate,
    close_transition,
    heir_id,
    plan_next_generation,
)
from dau.generation.reproduction import (
    PRICE_KEY_DELTA_ZBAR,
    PRICE_KEY_SELECTION,
    PRICE_KEY_TRANSMISSION,
    REPORT_KEY_SELECTION_MEASURABLE,
)

DOMAIN = "resource"
N_SLOTS = 4
NEXT_GEN = FIRST_GENERATION + 1


def _parents() -> list[Candidate]:
    """Four parents spanning the F_agent band measured in D-093."""

    return [
        Candidate("a", 0.279, {DOMAIN: 1.26}),
        Candidate("b", 0.421, {DOMAIN: 1.42}),
        Candidate("c", 0.445, {}),
        Candidate("d", 0.518, {DOMAIN: 1.82}),
    ]


def test_plan_fills_every_slot_and_names_heirs_uniquely() -> None:
    """w sums to the population and a double winner gets two distinct heirs."""

    plan = plan_next_generation(NEXT_GEN, _parents(), random.Random(5), N_SLOTS)

    assert sum(plan.w_by_parent.values()) == N_SLOTS
    assert len(plan.heirs) == N_SLOTS
    assert len({heir.heir_id for heir in plan.heirs}) == N_SLOTS


def test_plan_heir_count_per_parent_equals_w() -> None:
    """The pedigree and the w counter cannot disagree — Price reads both."""

    plan = plan_next_generation(NEXT_GEN, _parents(), random.Random(11), N_SLOTS)

    for parent_id, w in plan.w_by_parent.items():
        assert sum(1 for h in plan.heirs if h.parent_id == parent_id) == w


def test_plan_is_deterministic_for_a_seed() -> None:
    """Same seed, same pedigree — I0.6 / D-037 discipline."""

    first = plan_next_generation(NEXT_GEN, _parents(), random.Random(77), N_SLOTS)
    second = plan_next_generation(NEXT_GEN, _parents(), random.Random(77), N_SLOTS)

    assert first.w_by_parent == second.w_by_parent
    assert first.heirs == second.heirs


def test_plan_reports_whether_selection_is_measurable() -> None:
    """The validity gate travels with the plan, not with a later reader."""

    plan = plan_next_generation(NEXT_GEN, _parents(), random.Random(3), N_SLOTS)
    measurable = plan.report[REPORT_KEY_SELECTION_MEASURABLE]

    assert measurable is (len(set(plan.w_by_parent.values())) > 1)


def test_heir_id_carries_parent_generation_and_ordinal() -> None:
    """Two heirs of one parent must not collapse into one id (Var(w) → 0)."""

    assert heir_id("a", NEXT_GEN, 1) != heir_id("a", NEXT_GEN, 2)
    assert "a" in heir_id("a", NEXT_GEN, 1)
    assert str(NEXT_GEN) in heir_id("a", NEXT_GEN, 1)


def test_close_transition_holds_the_price_identity() -> None:
    """⭐ selection + transmission must reproduce Δz̄ read straight from heirs.

    Asymmetric w on purpose: with one heir each, grouping heirs by the wrong
    parent would still balance out, and the test would pass against a broken
    pedigree.
    """

    parents = _parents()
    plan = plan_next_generation(NEXT_GEN, parents, random.Random(5), N_SLOTS)
    assert len(set(plan.w_by_parent.values())) > 1, "seed gave a flat w; pick another"

    heir_z = {
        heir.heir_id: {DOMAIN: 0.5 + 0.25 * index}
        for index, heir in enumerate(plan.heirs)
    }
    part = close_transition(plan, heir_z)[DOMAIN]

    z_parent_mean = statistics.fmean(p.z.get(DOMAIN, 0.0) for p in plan.parents)
    z_heir_mean = statistics.fmean(row[DOMAIN] for row in heir_z.values())
    delta_zbar = z_heir_mean - z_parent_mean

    assert part[PRICE_KEY_DELTA_ZBAR] == pytest.approx(delta_zbar)
    assert part[PRICE_KEY_SELECTION] + part[PRICE_KEY_TRANSMISSION] == pytest.approx(
        delta_zbar
    )


def test_close_transition_refuses_a_missing_heir() -> None:
    """A heir with no z would average Δzᵢ over fewer offspring than w claims."""

    plan = plan_next_generation(NEXT_GEN, _parents(), random.Random(5), N_SLOTS)
    partial = {
        heir.heir_id: {DOMAIN: 1.0} for heir in plan.heirs[:-1]
    }

    with pytest.raises(ValueError, match="no z recorded"):
        close_transition(plan, partial)


def test_plan_rejects_a_generation_below_the_first() -> None:
    """Generation 0 has no parents, so it cannot be planned (§2.9)."""

    with pytest.raises(ValueError, match="generation must be"):
        plan_next_generation(0, _parents(), random.Random(1), N_SLOTS)
