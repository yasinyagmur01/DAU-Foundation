"""Unit tests for the reproduction layer (E4): tournament, w, Price partition."""

from __future__ import annotations

import random
import statistics

import pytest

from dau.generation.reproduction import (
    PRICE_KEY_DELTA_ZBAR,
    PRICE_KEY_SELECTION,
    PRICE_KEY_TRANSMISSION,
    REPORT_KEY_SELECTION_MEASURABLE,
    REPORT_KEY_W_DISTINCT,
    REPORT_KEY_W_VARIANCE,
    TOURNAMENT_K,
    Candidate,
    allocate_heirs,
    price_partition,
    reproduction_report,
    tournament_winner,
)

DOMAIN = "resource"


def _population() -> list[Candidate]:
    """Four parents spanning the F_agent band actually measured in D-093."""

    return [
        Candidate("a", 0.279, {DOMAIN: 1.26}),
        Candidate("b", 0.421, {DOMAIN: 1.42}),
        Candidate("c", 0.445, {}),
        Candidate("d", 0.518, {DOMAIN: 1.82}),
    ]


def test_tournament_picks_the_fitter_candidate() -> None:
    """With k = 2 the higher F_agent of the drawn pair wins."""

    pair = [Candidate("low", 0.30, {}), Candidate("high", 0.50, {})]
    assert tournament_winner(pair, random.Random(1), k=2) == "high"
    assert tournament_winner(pair, random.Random(99), k=2) == "high"


def test_tournament_tie_breaks_on_agent_id_not_list_order() -> None:
    """Equal fitness must not let the caller's ordering decide (D-042)."""

    forward = [Candidate("x", 0.40, {}), Candidate("b", 0.40, {})]
    backward = [Candidate("b", 0.40, {}), Candidate("x", 0.40, {})]
    assert tournament_winner(forward, random.Random(7), k=2) == "b"
    assert tournament_winner(backward, random.Random(7), k=2) == "b"


def test_tournament_is_deterministic_for_a_given_seed() -> None:
    """Same seed, same winner sequence — I0.6 / D-037 discipline."""

    pop = _population()
    first = [tournament_winner(pop, random.Random(4242), k=TOURNAMENT_K)]
    rng = random.Random(4242)
    second = [tournament_winner(pop, rng, k=TOURNAMENT_K)]
    assert first == second


def test_allocate_heirs_conserves_slots_and_makes_w_variable() -> None:
    """P3: w sums to the open slots and stops being constant."""

    pop = _population()
    w = allocate_heirs(pop, n_slots=4, rng=random.Random(11), k=TOURNAMENT_K)
    assert sum(w.values()) == 4
    assert len(set(w.values())) > 1, "w must vary or Cov(w, z) is undefined"


def test_allocate_heirs_keeps_the_losers() -> None:
    """A parent with w = 0 is the informative half of the covariance."""

    pop = _population()
    w = allocate_heirs(pop, n_slots=2, rng=random.Random(3), k=TOURNAMENT_K)
    assert set(w) == {c.agent_id for c in pop}
    assert 0 in set(w.values())


def test_price_identity_holds_exactly() -> None:
    """selection + transmission must reproduce Δz̄ computed straight from heirs.

    This is the load-bearing test: the partition is an algebraic identity under
    population moments, so any drift in divisor, weighting, or the treatment of
    w = 0 parents shows up here as a mismatch rather than as a plausible number.
    """

    parents = _population()
    w = {"a": 0, "b": 1, "c": 2, "d": 1}
    heirs = {
        "a": [],
        "b": [{DOMAIN: 1.50}],
        "c": [{DOMAIN: 0.10}, {DOMAIN: 0.30}],
        "d": [{DOMAIN: 2.05}],
    }
    part = price_partition(parents, w, heirs)[DOMAIN]

    z_parent_mean = statistics.fmean(
        p.z.get(DOMAIN, 0.0) for p in sorted(parents, key=lambda c: c.agent_id)
    )
    heir_rows = [row for rows in heirs.values() for row in rows]
    z_heir_mean = statistics.fmean(r.get(DOMAIN, 0.0) for r in heir_rows)
    delta_zbar = z_heir_mean - z_parent_mean

    assert part[PRICE_KEY_DELTA_ZBAR] == pytest.approx(delta_zbar)
    assert part[PRICE_KEY_SELECTION] + part[PRICE_KEY_TRANSMISSION] == pytest.approx(
        delta_zbar
    )


def test_price_selection_term_vanishes_when_w_is_constant() -> None:
    """Today's evolution: one heir each ⇒ Cov(w, z) = 0 BY CONSTRUCTION."""

    parents = _population()
    w = {c.agent_id: 1 for c in parents}
    heirs = {c.agent_id: [{DOMAIN: c.z.get(DOMAIN, 0.0) + 0.1}] for c in parents}
    part = price_partition(parents, w, heirs)[DOMAIN]
    assert part[PRICE_KEY_SELECTION] == pytest.approx(0.0)
    assert part[PRICE_KEY_TRANSMISSION] == pytest.approx(0.1)


def test_price_reports_every_domain_never_a_norm() -> None:
    """z is a vector (K5); collapsing it to one number would be an L9 choice."""

    parents = [
        Candidate("a", 0.3, {"resource": 1.0}),
        Candidate("b", 0.5, {"energy": 0.8}),
    ]
    w = {"a": 1, "b": 1}
    heirs = {"a": [{"resource": 1.2}], "b": [{"energy": 0.9}]}
    assert sorted(price_partition(parents, w, heirs)) == ["energy", "resource"]


def test_price_rejects_heir_count_mismatch() -> None:
    """w and the heir rows must agree or Δzᵢ is not defined (§2.9)."""

    parents = [Candidate("a", 0.3, {DOMAIN: 1.0})]
    with pytest.raises(ValueError, match="heir z rows"):
        price_partition(parents, {"a": 2}, {"a": [{DOMAIN: 1.1}]})


def test_price_rejects_a_generation_with_no_heirs() -> None:
    """w̄ = 0 makes the partition undefined — loud, not zero."""

    parents = [Candidate("a", 0.3, {DOMAIN: 1.0})]
    with pytest.raises(ValueError, match="undefined"):
        price_partition(parents, {"a": 0}, {"a": []})


def test_duplicate_agent_id_is_an_error() -> None:
    """Two parents sharing an id would make w ambiguous."""

    with pytest.raises(ValueError, match="duplicate"):
        allocate_heirs(
            [Candidate("a", 0.3, {}), Candidate("a", 0.4, {})],
            n_slots=1,
            rng=random.Random(0),
        )


def test_report_flags_the_degenerate_case() -> None:
    """The validity gate must say when selection is unmeasurable."""

    parents = _population()
    flat = reproduction_report(parents, {c.agent_id: 1 for c in parents})
    assert flat[REPORT_KEY_W_VARIANCE] == pytest.approx(0.0)
    assert flat[REPORT_KEY_W_DISTINCT] == 1
    assert flat[REPORT_KEY_SELECTION_MEASURABLE] is False

    varied = reproduction_report(parents, {"a": 0, "b": 1, "c": 2, "d": 1})
    assert varied[REPORT_KEY_W_VARIANCE] > 0.0
    assert varied[REPORT_KEY_SELECTION_MEASURABLE] is True
