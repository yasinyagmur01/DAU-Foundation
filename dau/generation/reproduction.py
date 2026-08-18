"""Reproduction layer — tournament selection, the `w` counter, Price partition.

E4 of the population design (`docs/POPULATION_DESIGN_PROPOSAL.md`). This is the
lynchpin: until a parent can have a number of heirs OTHER than exactly one, `w`
is constant, Var(w) = 0, and Cov(w, z) — the selection term of the Price
equation — is undefined. No amount of instrument cleanliness fixes that; it is
a missing layer, not a defect (D-076, D-093).

Three decisions were locked by Yasin on 2026-08-17 and this module implements
exactly those, nothing more:

  P2 — tournament, k = 2. Pressure is tunable through k and small populations
       keep their diversity (Goldberg & Deb 1991, verified). The reason is
       MEASURABILITY, not diversity for its own sake: fitness-proportional
       selection produces no pressure inside the narrow F_agent band we
       actually measured (0.279-0.518 over twelve lineages, D-093), and
       truncation collapses N=8 to a single lineage in two generations.
  P3 — fixed population size. Every agent that dies frees one slot, and each
       slot is filled by one heir of a tournament winner. A parent may win
       several tournaments or none, so w ∈ {0, 1, 2, ...} and Var(w) > 0
       becomes possible. Death-birth balance was rejected: with eight of
       twelve lineages still draining the commons (D-093) a drifting
       population can reach zero, and the run budget stops being predictable.
  P4 — three layers stay separate. F_agent is the selection INPUT (reported,
       never the outcome), w is demographic success, and z is the landmark
       drift vector (K5) read as the outcome. Feeding F_agent straight in as w
       would rebuild the Mills & Beatty tautology D-075 warned about, because
       30% of F_agent has been realized survival since D-071.

⚠ NOT WIRED YET. Nothing in `run_cprime_multigen` calls this module: E1/E5
(shared pool outside the flows) and E2 (the outer loop over N agents) come
first, and both wait on P1/P6 which are undecided. The module is written and
tested on its own so that the reproduction rule is reviewable before it is
entangled with orchestration.
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Reproduction parameters (P2 / P3, no magic numbers)
# ---------------------------------------------------------------------------

TOURNAMENT_K: int = 2  # P2 — Goldberg & Deb 1991
HEIRS_PER_TOURNAMENT_WIN: int = 1  # P3 — one slot, one heir
MIN_TOURNAMENT_CANDIDATES: int = 1  # below this there is nobody to select from

# A parent whose drift never flagged a domain has no drift in that domain. The
# absence is data, not a missing value, so it enters the Price sums as zero
# rather than dropping the parent out of that domain's covariance.
DRIFT_ABSENT_MAGNITUDE: float = 0.0

# Price terms are POPULATION moments (divide by N, not N-1). That is not a
# stylistic choice: the partition below is an algebraic identity only under
# population moments. Rice (2008) — flagged in D-082/§P — warns separately that
# the ESTIMATOR is biased at small N; that is a claim-side limit for the second
# pre-registration, not a reason to change the divisor here.
PRICE_KEY_SELECTION: str = "selection"
PRICE_KEY_TRANSMISSION: str = "transmission"
PRICE_KEY_DELTA_ZBAR: str = "delta_zbar"
# D-121. Cov(w, z) is zero BY CONSTRUCTION when every parent of a cell carries
# the same z, and a run that prints that zero next to a real one is reporting
# two different things with one number. Measured: 14 of 27 cells of the
# headroom run were degenerate this way. So the partition also says whether the
# selection term was estimable at all — the identification check Rothenberg
# 1971 (10.2307/1913267) names, applied before the number is read rather than
# after (Yasin's decision A, 2026-08-18).
PRICE_KEY_Z_VARIANCE: str = "z_variance"
PRICE_KEY_ESTIMABLE: str = "selection_estimable"
# Below this the within-cell spread is numerical noise, not variation. Named
# rather than testing == 0.0 because z is a sum of floats and an exact zero is
# not the only way to have nothing to select on.
Z_VARIANCE_EPSILON: float = 1e-12
# The pre-declared positive control (D-121). NOT an endpoint and never claimed
# as one: it exists so that a run reporting "no selection" can be told apart
# from a run whose selection machinery never worked. Declared before the run,
# per Q4's boundary conditions.
CONTROL_KEY_COVARIANCE: str = "control_selection"
CONTROL_KEY_VARIANCE: str = "control_variance"
CONTROL_KEY_ESTIMABLE: str = "control_estimable"

REPORT_KEY_F_AGENT_SPREAD: str = "f_agent_spread"
REPORT_KEY_W_VARIANCE: str = "w_variance"
REPORT_KEY_W_DISTINCT: str = "w_n_distinct"
REPORT_KEY_W_VALUES: str = "w_values"
REPORT_KEY_SELECTION_MEASURABLE: str = "selection_measurable"


@dataclass(frozen=True)
class Candidate:
    """One agent at the end of its generation — a possible parent.

    `f_agent` is the selection input (P4). `z` is the landmark drift vector as
    `run_cprime_multigen` writes it: domain → magnitude, flagged domains only.
    """

    agent_id: str
    f_agent: float
    z: dict[str, float]
    # D-121: the pre-declared positive-control trait, or None when the caller
    # does not carry one. Optional so every existing construction stays valid,
    # and never folded into z — it is a diagnostic, not an endpoint.
    control: float | None = None


def _sorted_unique(candidates: list[Candidate]) -> list[Candidate]:
    """Candidates in a deterministic order, rejecting duplicate ids.

    Two parents with one id would make w ambiguous, so this is an error rather
    than a silent merge (§2.9: no silent fallback).
    """

    seen: set[str] = set()
    for candidate in candidates:
        if candidate.agent_id in seen:
            raise ValueError(f"duplicate candidate agent_id: {candidate.agent_id}")
        seen.add(candidate.agent_id)
    return sorted(candidates, key=lambda c: c.agent_id)


def tournament_winner(
    candidates: list[Candidate],
    rng: random.Random,
    k: int = TOURNAMENT_K,
) -> str:
    """Draw k candidates without replacement and return the fittest one's id.

    Ties break on `agent_id`, declared rather than left to whatever order the
    caller happened to build the list in — the same discipline D-042 had to
    apply to adapter grafting after position turned out to matter.
    """

    ordered = _sorted_unique(candidates)
    if len(ordered) < MIN_TOURNAMENT_CANDIDATES:
        raise ValueError("tournament needs at least one candidate")
    if k < 1:
        raise ValueError(f"tournament k must be >= 1, got {k}")
    drawn = rng.sample(ordered, min(k, len(ordered)))
    best = drawn[0]
    for challenger in drawn[1:]:
        fitter = challenger.f_agent > best.f_agent
        tied_and_earlier = (
            challenger.f_agent == best.f_agent
            and challenger.agent_id < best.agent_id
        )
        if fitter or tied_and_earlier:
            best = challenger
    return best.agent_id


def allocate_heirs(
    candidates: list[Candidate],
    n_slots: int,
    rng: random.Random,
    k: int = TOURNAMENT_K,
) -> dict[str, int]:
    """Fill n_slots open slots by tournament and return w per parent (P3).

    Every candidate appears in the result, including the ones that won nothing:
    a `w` of zero is the informative half of the covariance, so dropping those
    rows would bias Cov(w, z) toward the winners.
    """

    if n_slots < 0:
        raise ValueError(f"n_slots must be >= 0, got {n_slots}")
    ordered = _sorted_unique(candidates)
    w_by_parent: dict[str, int] = {c.agent_id: 0 for c in ordered}
    for _ in range(n_slots):
        winner = tournament_winner(ordered, rng, k=k)
        w_by_parent[winner] += HEIRS_PER_TOURNAMENT_WIN
    return w_by_parent


def _domains(
    parents: list[Candidate],
    heir_z_by_parent: dict[str, list[dict[str, float]]],
) -> list[str]:
    """Every drift domain any parent or heir reported, in a stable order."""

    names: set[str] = set()
    for parent in parents:
        names.update(parent.z)
    for heir_rows in heir_z_by_parent.values():
        for row in heir_rows:
            names.update(row)
    return sorted(names)


def price_partition(
    parents: list[Candidate],
    w_by_parent: dict[str, int],
    heir_z_by_parent: dict[str, list[dict[str, float]]],
) -> dict[str, dict[str, float]]:
    """Partition Δz̄ into selection and transmission, per drift domain.

        Δz̄ = (1/w̄)·Cov(wᵢ, zᵢ) + (1/w̄)·E(wᵢ·Δzᵢ)

    Returned per domain because z is a VECTOR (K5) and collapsing it to a norm
    would be choosing an endpoint after seeing the data — exactly what L9
    forbids. The caller reports every domain; nobody picks one later.

    `heir_z_by_parent` maps a parent id to its heirs' z vectors. A parent with
    w > 0 must have that many heir rows, otherwise Δzᵢ is not defined and the
    identity silently stops holding — so that mismatch raises.
    """

    ordered = _sorted_unique(parents)
    if not ordered:
        raise ValueError("price_partition needs at least one parent")
    w_values = [float(w_by_parent[c.agent_id]) for c in ordered]
    w_mean = statistics.fmean(w_values)
    if w_mean <= 0.0:
        raise ValueError("no heirs were produced — Price partition is undefined")
    for candidate in ordered:
        expected = int(w_by_parent[candidate.agent_id])
        rows = heir_z_by_parent.get(candidate.agent_id, [])
        if len(rows) != expected:
            raise ValueError(
                f"{candidate.agent_id}: w={expected} but {len(rows)} heir z rows"
            )

    out: dict[str, dict[str, float]] = {}
    for domain in _domains(ordered, heir_z_by_parent):
        z_values = [
            float(c.z.get(domain, DRIFT_ABSENT_MAGNITUDE)) for c in ordered
        ]
        z_mean = statistics.fmean(z_values)
        delta_z: list[float] = []
        for candidate, z_parent in zip(ordered, z_values):
            rows = heir_z_by_parent.get(candidate.agent_id, [])
            if not rows:
                delta_z.append(0.0)  # no heirs ⇒ w·Δz is zero either way
                continue
            heir_mean = statistics.fmean(
                float(r.get(domain, DRIFT_ABSENT_MAGNITUDE)) for r in rows
            )
            delta_z.append(heir_mean - z_parent)
        cov = statistics.fmean(
            (w - w_mean) * (z - z_mean) for w, z in zip(w_values, z_values)
        )
        transmission = statistics.fmean(
            w * dz for w, dz in zip(w_values, delta_z)
        )
        z_variance = statistics.fmean((z - z_mean) ** 2 for z in z_values)
        out[domain] = {
            PRICE_KEY_SELECTION: cov / w_mean,
            PRICE_KEY_TRANSMISSION: transmission / w_mean,
            PRICE_KEY_DELTA_ZBAR: (cov + transmission) / w_mean,
            # Reported beside the term, not instead of it: the number stays
            # readable, and the flag says whether it carries information.
            PRICE_KEY_Z_VARIANCE: z_variance,
            PRICE_KEY_ESTIMABLE: z_variance > Z_VARIANCE_EPSILON,
        }
    return out


def positive_control_partition(
    parents: list[Candidate],
    w_by_parent: dict[str, int],
) -> dict[str, float | bool] | None:
    """Cov(w, control) for the pre-declared control trait — D-121, Yasin's A.

    Returns None when the trait was not carried, rather than a zero: a run
    without the control must not look like a run whose control came out flat.

    ⚠ This is NOT a second endpoint and no inheritance claim may be built on
    it. Its only job is to separate two readings that look identical in the
    results file — "selection acted and we measured none" from "the selection
    machinery could not have measured anything" — by showing the same w
    covarying with a quantity that DOES vary. Chosen and written down before
    the run (Q4/Eldridge 2016), and reported whatever it says.
    """

    ordered = _sorted_unique(parents)
    if not ordered or any(c.control is None for c in ordered):
        return None
    w_values = [float(w_by_parent[c.agent_id]) for c in ordered]
    w_mean = statistics.fmean(w_values)
    if w_mean <= 0.0:
        raise ValueError("no heirs were produced — Price partition is undefined")
    values = [float(c.control) for c in ordered]  # type: ignore[arg-type]
    mean = statistics.fmean(values)
    variance = statistics.fmean((v - mean) ** 2 for v in values)
    cov = statistics.fmean(
        (w - w_mean) * (v - mean) for w, v in zip(w_values, values)
    )
    return {
        CONTROL_KEY_COVARIANCE: cov / w_mean,
        CONTROL_KEY_VARIANCE: variance,
        CONTROL_KEY_ESTIMABLE: variance > Z_VARIANCE_EPSILON,
    }


def reproduction_report(
    candidates: list[Candidate],
    w_by_parent: dict[str, int],
) -> dict[str, object]:
    """Validity gate inputs: is there anything for selection to act on?

    Reports the spread of the selection input and the variance of w, and flags
    the one structurally degenerate case — Var(w) = 0, where every parent has
    the same number of heirs and Cov(w, z) is zero BY CONSTRUCTION rather than
    by measurement. That flag needs no calibrated threshold, so §2.7 is not in
    play: the rule is a definition, and it is written before any run.
    """

    ordered = _sorted_unique(candidates)
    f_values = [float(c.f_agent) for c in ordered]
    w_values = [int(w_by_parent[c.agent_id]) for c in ordered]
    return {
        REPORT_KEY_F_AGENT_SPREAD: max(f_values) - min(f_values),
        REPORT_KEY_W_VARIANCE: statistics.pvariance(
            [float(w) for w in w_values]
        ),
        REPORT_KEY_W_DISTINCT: len(set(w_values)),
        REPORT_KEY_W_VALUES: w_values,
        REPORT_KEY_SELECTION_MEASURABLE: len(set(w_values)) > 1,
    }
