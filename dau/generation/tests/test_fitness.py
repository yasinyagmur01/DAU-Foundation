"""Unit tests for F_agent fitness and fitness-based transfer selection."""

from __future__ import annotations

import math

import pytest

from dau.foundation.delta import DELTA_THRESHOLD_DEEP
from dau.foundation.drift import DriftState
from dau.foundation.generation import (
    DRIFT_TRANSFER_MIN,
    GENERATION_MIN_RECALL,
    GENERATION_TRANSFER_THRESHOLD,
    INHERITED_WARNING_KEY,
    RECORD_ID_KEY,
    SOMATIC_SCALE_KEY,
    TRANSFER_KIND_INHERITED_WARNING,
    TRANSFER_KIND_STANDARD,
    W_TRANSFER_UNSCORED,
    GenerationRecord,
    TransferCandidate,
    apply_generation,
    select_for_transfer,
)
from dau.foundation.constraints import build_default_constraints
from dau.foundation.state import DAUAgentState, DeltaRecord
from dau.generation.fitness import (
    ENERGY_MAX,
    FITNESS_HIGH_THRESHOLD,
    FITNESS_LABEL_HIGH,
    FITNESS_LABEL_LOW,
    FITNESS_LABEL_NORMAL,
    FITNESS_LOW_THRESHOLD,
    FITNESS_W_ENERGY,
    FITNESS_W_POOL,
    FITNESS_W_SURVIVAL,
    WARNING_SOMATIC_SCALE,
    W_TRANSFER_VALENCE_BASE,
    classify_fitness,
    compute_fitness,
    compute_w_transfer,
)
from dau.society.environment import POOL_MAX
from dau.society.extraction import EXTRACTION_DEFECT

# K4-b (D-070): the pool term is a per-event rate. These two lives took the
# same 6.88 units per event of life — the pilot's two lineages, whose raw
# ledgers (130.8 vs 62.2) spread 110% while their intensity spread 10.7%.
RATE_SHORT_LIFE_EVENTS: int = 10
RATE_LONG_LIFE_EVENTS: int = 20
RATE_PER_EVENT: float = 6.88
# Budgets set to twice each lifespan so the SURVIVAL term is equal (0.5) in
# both, leaving the pool term as the only thing that could differ.
RATE_SURVIVAL_MULTIPLE: int = 2
# A separate pair for the survival term: same intensity, same budget, and a
# lifespan that differs by design.
SPAN_BUDGET_EVENTS: int = 50
SPAN_SHORT_EVENTS: int = 10
SPAN_LONG_EVENTS: int = 40
SPAN_PER_EVENT: float = 2.0
NO_ENERGY_LEFT: float = 0.0


def _delta(magnitude: float, domain: str = "resource", timestamp: int = 1) -> DeltaRecord:
    snap = {
        "energy": 1.0,
        "resource_load": 0.0,
        "uncertainty_load": 0.0,
        "social_load": 0.0,
    }
    return DeltaRecord(
        timestamp=timestamp,
        magnitude=magnitude,
        affected_domain=domain,  # type: ignore[arg-type]
        snapshot_before=snap,
        snapshot_after=dict(snap),
    )


def _candidate(
    magnitude: float,
    *,
    memory_score: float,
    recall_count: int,
    domain: str = "resource",
    record_id: str = "mem-0",
) -> TransferCandidate:
    return TransferCandidate(
        record=_delta(magnitude, domain=domain),
        record_id=record_id,
        memory_score=memory_score,
        recall_count=recall_count,
    )


def test_compute_fitness_formula() -> None:
    """F matches weighted energy / pool / survival terms and clamps to [0, 1]."""

    energy_lived = 0.8
    delta_pool = 20.0
    t_survived = 40
    t_generation = 50

    expected = (
        FITNESS_W_ENERGY * (energy_lived / ENERGY_MAX)
        + FITNESS_W_POOL
        * (1.0 - (abs(delta_pool) / t_survived) / EXTRACTION_DEFECT)
        + FITNESS_W_SURVIVAL * (t_survived / t_generation)
    )
    assert compute_fitness(
        energy_lived, delta_pool, t_survived, t_generation
    ) == pytest.approx(expected)

    assert compute_fitness(2.0, 0.0, 10, 10) == 1.0
    assert compute_fitness(0.0, POOL_MAX, 0, 0) == 0.0


def test_pool_term_is_a_rate_not_a_lifetime_sum() -> None:
    """Two lives that used the commons equally hard score equally (K4-b).

    The long life took twice as much in total simply by living twice as long.
    Summing the ledger made that look like twice the greed, which is how
    nine tenths of the pilot's "commons" signal turned out to be longevity
    counted a second time (D-070) — the double counting Stearns (1989) warns
    about. Budgets are set so the survival terms match, leaving the pool term
    as the only free variable.
    """

    short = compute_fitness(
        energy_lived=NO_ENERGY_LEFT,
        delta_pool=RATE_PER_EVENT * RATE_SHORT_LIFE_EVENTS,
        t_survived=RATE_SHORT_LIFE_EVENTS,
        t_generation=RATE_SHORT_LIFE_EVENTS * RATE_SURVIVAL_MULTIPLE,
    )
    long_life = compute_fitness(
        energy_lived=NO_ENERGY_LEFT,
        delta_pool=RATE_PER_EVENT * RATE_LONG_LIFE_EVENTS,
        t_survived=RATE_LONG_LIFE_EVENTS,
        t_generation=RATE_LONG_LIFE_EVENTS * RATE_SURVIVAL_MULTIPLE,
    )

    assert short == pytest.approx(long_life)
    # Not vacuous in the other direction: taking more per event still costs.
    greedier = compute_fitness(
        energy_lived=NO_ENERGY_LEFT,
        delta_pool=RATE_PER_EVENT * RATE_SHORT_LIFE_EVENTS * 2.0,
        t_survived=RATE_SHORT_LIFE_EVENTS,
        t_generation=RATE_SHORT_LIFE_EVENTS * RATE_SURVIVAL_MULTIPLE,
    )
    assert greedier < short


def test_survival_term_measures_the_budget_not_the_agents_own_span() -> None:
    """Living 40 of 50 events beats living 10 of 50 (K4-b, D-070).

    f_agent_inputs used to hand t_generation the agent's own lifespan, making
    this term t_survived/t_survived ≡ 1.0 — a constant 0.3 added to every
    lineage the harness has ever scored, which is why the pilot's F_agent
    spread reproduced exactly from the pool term alone. Since D-066 a life can
    end early, so the fraction of the span endured is a real measurement.
    """

    short = compute_fitness(
        energy_lived=NO_ENERGY_LEFT,
        delta_pool=SPAN_PER_EVENT * SPAN_SHORT_EVENTS,
        t_survived=SPAN_SHORT_EVENTS,
        t_generation=SPAN_BUDGET_EVENTS,
    )
    long_life = compute_fitness(
        energy_lived=NO_ENERGY_LEFT,
        delta_pool=SPAN_PER_EVENT * SPAN_LONG_EVENTS,
        t_survived=SPAN_LONG_EVENTS,
        t_generation=SPAN_BUDGET_EVENTS,
    )

    assert long_life > short
    expected_gap = FITNESS_W_SURVIVAL * (
        (SPAN_LONG_EVENTS - SPAN_SHORT_EVENTS) / SPAN_BUDGET_EVENTS
    )
    assert long_life - short == pytest.approx(expected_gap)


def test_classify_fitness_thresholds() -> None:
    """Low / high thresholds map onto policy labels; mid-band is normal."""

    assert classify_fitness(FITNESS_LOW_THRESHOLD - 0.01) == FITNESS_LABEL_LOW
    assert classify_fitness(FITNESS_LOW_THRESHOLD) == FITNESS_LABEL_NORMAL
    assert classify_fitness(FITNESS_HIGH_THRESHOLD - 0.01) == FITNESS_LABEL_NORMAL
    assert classify_fitness(FITNESS_HIGH_THRESHOLD) == FITNESS_LABEL_HIGH


def test_compute_w_transfer_formula() -> None:
    """W matches memory_score · F · (1 + tanh(reward − threat)) and clamps."""

    memory_score = 0.8
    f_agent = 0.5
    reward_marker = 0.6
    threat_marker = 0.2
    expected = memory_score * f_agent * (
        W_TRANSFER_VALENCE_BASE + math.tanh(reward_marker - threat_marker)
    )
    assert compute_w_transfer(
        memory_score, f_agent, reward_marker, threat_marker
    ) == pytest.approx(expected)
    assert compute_w_transfer(1.0, 1.0, 10.0, 0.0) == 1.0


def test_low_fitness_excludes_trauma() -> None:
    """Below FITNESS_LOW_THRESHOLD: trauma kept as cautionary inherited_warning."""

    f_low = FITNESS_LOW_THRESHOLD - 0.01
    trauma = _candidate(
        DELTA_THRESHOLD_DEEP,
        memory_score=0.95,
        recall_count=GENERATION_MIN_RECALL,
        record_id="trauma-low-f",
    )
    # W = 0.95 * f_low * 1 ≈ 0.32 < 0.60 with neutral markers — boost valence.
    normal = _candidate(
        0.55,
        memory_score=0.95,
        recall_count=GENERATION_MIN_RECALL,
        record_id="keep-normal",
    )
    high_drift = DriftState(
        flags={"resource": True},
        magnitudes={"resource": DRIFT_TRANSFER_MIN},
    )
    selected = select_for_transfer(
        [trauma, normal],
        high_drift,
        f_agent=f_low,
        reward_marker=5.0,
        threat_marker=0.0,
    )
    ids = [c.record_id for c in selected]
    assert "trauma-low-f" in ids
    assert "keep-normal" in ids
    caution = next(c for c in selected if c.record_id == "trauma-low-f")
    assert caution.inherited_warning is True
    assert caution.somatic_scale == -WARNING_SOMATIC_SCALE
    normal_sel = next(c for c in selected if c.record_id == "keep-normal")
    assert normal_sel.transfer_kind == TRANSFER_KIND_STANDARD
    assert normal_sel.inherited_warning is False


def test_high_fitness_trauma_becomes_inherited_warning() -> None:
    """High F + trauma → inherited_warning; apply_generation scales somatic."""

    f_high = FITNESS_HIGH_THRESHOLD
    trauma = _candidate(
        DELTA_THRESHOLD_DEEP,
        memory_score=0.95,
        recall_count=GENERATION_MIN_RECALL,
        record_id="warn-me",
    )
    # No drift required for high-fitness inherited warnings.
    selected = select_for_transfer(
        [trauma],
        DriftState(),
        f_agent=f_high,
        reward_marker=5.0,
        threat_marker=0.0,
    )
    assert len(selected) == 1
    assert selected[0].transfer_kind == TRANSFER_KIND_INHERITED_WARNING

    record = GenerationRecord(
        agent_id="parent-0",
        generation=1,
        inherited_memories=["warn-me"],
        inherited_warning_ids=["warn-me"],
        transfer_timestamp=3,
    )
    heir = apply_generation(
        DAUAgentState(
            agent_id="heir-0",
            environment=build_default_constraints(),
        ),
        record,
        memory_store=None,
    )
    assert heir.retrieval_context == [
        {
            RECORD_ID_KEY: "warn-me",
            "generation_inherited": True,
            INHERITED_WARNING_KEY: True,
            SOMATIC_SCALE_KEY: WARNING_SOMATIC_SCALE,
        }
    ]


def test_normal_fitness_uses_salience_and_drift_gate() -> None:
    """Normal F: the salience bar + trauma still needs high drift.

    D-088 renamed this from ..._uses_w_transfer_...: it never tested the
    w_transfer gate. Both of its candidates put memory_score and w_transfer on
    the SAME side of the threshold (0.95 clears both, 0.1 fails both), so it
    passed identically whichever quantity was being gated and could not have
    caught the transplanted-constant defect. The case that discriminates is
    below, in test_salience_bar_is_tested_on_memory_score_not_the_product.
    """

    f_normal = (FITNESS_LOW_THRESHOLD + FITNESS_HIGH_THRESHOLD) / 2.0
    trauma = _candidate(
        DELTA_THRESHOLD_DEEP,
        memory_score=0.95,
        recall_count=GENERATION_MIN_RECALL,
        record_id="trauma-normal",
    )
    low_drift = DriftState(
        flags={"resource": True},
        magnitudes={"resource": DRIFT_TRANSFER_MIN - 0.1},
    )
    assert (
        select_for_transfer(
            [trauma],
            low_drift,
            f_agent=f_normal,
            reward_marker=5.0,
            threat_marker=0.0,
        )
        == []
    )

    high_drift = DriftState(
        flags={"resource": True},
        magnitudes={"resource": DRIFT_TRANSFER_MIN},
    )
    selected = select_for_transfer(
        [trauma],
        high_drift,
        f_agent=f_normal,
        reward_marker=5.0,
        threat_marker=0.0,
    )
    assert len(selected) == 1
    assert selected[0].transfer_kind == TRANSFER_KIND_STANDARD

    # Below the salience bar even with high drift.
    weak = _candidate(
        0.55,
        memory_score=0.1,
        recall_count=GENERATION_MIN_RECALL,
        record_id="weak",
    )
    assert (
        select_for_transfer(
            [weak],
            DriftState(),
            f_agent=f_normal,
            reward_marker=0.0,
            threat_marker=0.0,
        )
        == []
    )
    assert compute_w_transfer(0.1, f_normal, 0.0, 0.0) < GENERATION_TRANSFER_THRESHOLD


# D-086: F_agent's energy term reads the LIFE, not the ending. Death is by
# energy exhaustion, so the final reading is pinned near zero by the death rule
# itself — 10 of 12 lineages reported exactly 0.000 in the D-085 validation run
# while the same lives spread 0.59-0.86 on the lifetime mean.
ENERGY_TRACE_STARVED: tuple[float, ...] = (0.9, 0.7, 0.5, 0.3, 0.0)
ENERGY_TRACE_LEAN: tuple[float, ...] = (0.2, 0.2, 0.1, 0.1, 0.0)
ENERGY_DEATH_READING: float = 0.0
ENERGY_TRACE_EVENT_TYPE: str = "agent_decision"
ENERGY_TRACE_POOL: float = 10.0
ENERGY_TRACE_BUDGET: int = 20


def _state_with_energy_trace(
    agent_id: str,
    trace: tuple[float, ...],
) -> DAUAgentState:
    """A life whose logged energies are ``trace`` and whose LAST reading is 0."""

    from dau.foundation.state import Event, InternalState

    return DAUAgentState(
        agent_id=agent_id,
        environment=build_default_constraints(),
        internal_state=InternalState(energy=ENERGY_DEATH_READING),
        event_log=[
            Event(event_type=ENERGY_TRACE_EVENT_TYPE, payload={"energy": value})
            for value in trace
        ],
    )


def test_energy_term_reads_the_life_not_the_ending() -> None:
    """Two lives with the SAME final energy but different traces score apart.

    Mutation control (§2.4): revert f_agent_inputs to
    state.internal_state.energy and this must fail — both states end at exactly
    ENERGY_DEATH_READING, so the old read cannot tell them apart. That
    indistinguishability is the defect D-086 fixes, not a hypothetical.
    """

    from dau.foundation.self_model import f_agent_inputs

    well_fuelled = _state_with_energy_trace("f-lived-rich", ENERGY_TRACE_STARVED)
    lean = _state_with_energy_trace("f-lived-lean", ENERGY_TRACE_LEAN)

    # The old reading is identical for both — this is what used to be scored.
    assert well_fuelled.internal_state.energy == lean.internal_state.energy

    rich_inputs = f_agent_inputs(well_fuelled, ENERGY_TRACE_BUDGET)
    lean_inputs = f_agent_inputs(lean, ENERGY_TRACE_BUDGET)
    assert rich_inputs["energy_lived"] > lean_inputs["energy_lived"]

    rich_f = compute_fitness(
        energy_lived=rich_inputs["energy_lived"],
        delta_pool=ENERGY_TRACE_POOL,
        t_survived=int(rich_inputs["t_survived"]),
        t_generation=ENERGY_TRACE_BUDGET,
    )
    lean_f = compute_fitness(
        energy_lived=lean_inputs["energy_lived"],
        delta_pool=ENERGY_TRACE_POOL,
        t_survived=int(lean_inputs["t_survived"]),
        t_generation=ENERGY_TRACE_BUDGET,
    )
    assert rich_f > lean_f
    expected_gap = FITNESS_W_ENERGY * (
        (sum(ENERGY_TRACE_STARVED) - sum(ENERGY_TRACE_LEAN))
        / len(ENERGY_TRACE_STARVED)
        / ENERGY_MAX
    )
    assert rich_f - lean_f == pytest.approx(expected_gap)


def test_energy_trace_with_a_hole_raises_instead_of_averaging_around_it() -> None:
    """A logged event without the energy key is loud, not skipped (§2.9)."""

    from dau.foundation.self_model import f_agent_inputs
    from dau.foundation.state import Event

    holed = _state_with_energy_trace("f-lived-hole", ENERGY_TRACE_STARVED)
    holed = holed.model_copy(
        update={
            "event_log": [
                *holed.event_log,
                Event(event_type=ENERGY_TRACE_EVENT_TYPE, payload={}),
            ]
        }
    )
    with pytest.raises(ValueError, match="energy"):
        f_agent_inputs(holed, ENERGY_TRACE_BUDGET)


def test_life_of_zero_events_scores_its_present_energy() -> None:
    """An empty log is not a hole: one reading exists, the current one."""

    from dau.foundation.self_model import f_agent_inputs
    from dau.foundation.state import InternalState

    newborn = DAUAgentState(
        agent_id="f-lived-newborn",
        environment=build_default_constraints(),
        internal_state=InternalState(energy=ENERGY_MAX),
    )
    inputs = f_agent_inputs(newborn, ENERGY_TRACE_BUDGET)
    assert inputs["energy_lived"] == pytest.approx(ENERGY_MAX)
    assert inputs["t_survived"] == 0.0


# D-088: the discriminating case the old test could not reach — a memory that
# clears the salience bar while the fitness-weighted product does not. Every
# memory that failed to transfer in the D-085 validation run was of this shape.
SALIENT_SCORE: float = 0.9
NEUTRAL_MARKER: float = 0.0


def test_salience_bar_is_tested_on_memory_score_not_the_product() -> None:
    """A salient memory from a normal-fitness life transfers.

    Mutation control (§2.4): restore `if w_transfer < THRESHOLD: continue` and
    this must fail. The candidate is built so the two readings DISAGREE —
    memory_score 0.9 clears 0.6, while w_transfer = 0.9·F·1.0 does not — which
    is exactly the region the transplanted constant was silently rejecting, and
    exactly what the old test's candidates could not express.
    """

    f_normal = (FITNESS_LOW_THRESHOLD + FITNESS_HIGH_THRESHOLD) / 2.0
    salient = _candidate(
        DELTA_THRESHOLD_DEEP - 0.1,  # below trauma: no drift gate in the way
        memory_score=SALIENT_SCORE,
        recall_count=GENERATION_MIN_RECALL,
        record_id="salient-normal",
    )

    # The premise: the two readings disagree about this candidate.
    assert salient.memory_score >= GENERATION_TRANSFER_THRESHOLD
    product = compute_w_transfer(
        SALIENT_SCORE, f_normal, NEUTRAL_MARKER, NEUTRAL_MARKER
    )
    assert product < GENERATION_TRANSFER_THRESHOLD

    selected = select_for_transfer(
        [salient],
        DriftState(),
        f_agent=f_normal,
        reward_marker=NEUTRAL_MARKER,
        threat_marker=NEUTRAL_MARKER,
    )
    assert len(selected) == 1
    assert selected[0].transfer_kind == TRANSFER_KIND_STANDARD
    # F_agent did not vanish from the decision — it rode along as the
    # fitness-weighted salience, so a reader can still see it.
    assert selected[0].w_transfer == pytest.approx(product)


def test_legacy_and_fitness_paths_agree_on_the_salience_bar() -> None:
    """The same memory is judged the same by both paths (D-088).

    Before D-088 the F_agent path was strictly stricter than the legacy path by
    a factor of F_agent·valence, without that ever being declared.
    """

    salient = _candidate(
        DELTA_THRESHOLD_DEEP - 0.1,
        memory_score=SALIENT_SCORE,
        recall_count=GENERATION_MIN_RECALL,
        record_id="salient-both",
    )
    legacy = select_for_transfer([salient], DriftState(), f_agent=None)
    fitness = select_for_transfer(
        [salient],
        DriftState(),
        f_agent=(FITNESS_LOW_THRESHOLD + FITNESS_HIGH_THRESHOLD) / 2.0,
        reward_marker=NEUTRAL_MARKER,
        threat_marker=NEUTRAL_MARKER,
    )
    assert len(legacy) == len(fitness) == 1
    # Only the legacy path leaves w_transfer unscored — it was never asked.
    assert legacy[0].w_transfer == W_TRANSFER_UNSCORED
    assert fitness[0].w_transfer > W_TRANSFER_UNSCORED
