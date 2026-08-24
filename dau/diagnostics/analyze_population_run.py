"""Read a population run and report it against the reading rules — nothing else.

Written because the alternative is reading the JSON by eye, and this project has
a documented history of that going wrong in one specific way: a number is seen,
it looks like a result, and the sentence written about it claims more than the
measurement can carry. D-090's drift threshold, D-092's band narrowing and
D-059's clipping lever were all read that way and all three died.

⭐ The reading rules are NOT invented here. They were fixed in CLAUDE.md BEFORE
any population run, and this module implements them literally:

    level 0 — gate       Var(w) > 0                  claim: NOTHING, it is a
                                                     precondition
    level 1 — selection  Cov(w, z) != 0, sign        claim: "selection acted on
                         consistent across seeds     landmark drift"
    level 2 — accumulation  the term does not decay  claim: "the effect is
                         across generations          cumulative"
    level 3 — arm contrast  lived != shuffle != null claim: the Lamarckian
                                                     channel

⚠ The most likely mistake, named in CLAUDE.md: Price gives SELECTION, the arm
comparison gives INHERITANCE. Level 1 can be full while level 3 is empty — in
B2 the three arms came out equidistant. This module therefore never merges the
two, and prints level 3 even when level 1 is empty.

⛔ NO HYPOTHESIS TEST IS PERFORMED, deliberately (P7-b / D-096): the first run
is an ESTIMATION run. No p-value is computed here, so no report produced by
this module can say "significant". The forbidden claims are printed alongside
the numbers rather than left to the reader's memory.

⚠ Exploratory. This reads a run that is itself exploratory; it changes no
constant, and it is not on the pre-registered analysis path.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dau.generation.reproduction import (
    CONTROL_KEY_COVARIANCE,
    CONTROL_KEY_ESTIMABLE,
    CONTROL_KEY_VARIANCE,
    DRIFT_ABSENT_MAGNITUDE,
    PRICE_KEY_DELTA_ZBAR,
    PRICE_KEY_ESTIMABLE,
    PRICE_KEY_SELECTION,
    PRICE_KEY_TRANSMISSION,
    REPORT_KEY_F_AGENT_SPREAD,
    REPORT_KEY_SELECTION_MEASURABLE,
    REPORT_KEY_W_DISTINCT,
    REPORT_KEY_W_VARIANCE,
)

# Keys the runner writes. Imported where they already exist (above) and named
# here where they do not: reading the wrong one is silent — the section comes
# back empty and the report looks like a measured zero (§2.8, and the exact
# failure D-102 shipped with `landmark_drift_magnitudes`).
RUN_KEY_ARMS: str = "arms"
RUN_KEY_REPLAY: str = "replay"
RUN_KEY_SEEDS: str = "seeds"
RUN_KEY_QUALITY: str = "run_quality"
RUN_KEY_INVARIANTS: str = "invariants"
RUN_KEY_INFORMATIVE: str = "generations_informative"
# D-111. False on a checkpoint file, True only on a run that reached the end
# with every gate run. ABSENT on runs written before checkpointing existed,
# which is why "not False" is the test rather than "is True": those files are
# complete, they just predate the flag.
RUN_KEY_COMPLETE: str = "complete"
# D-176/B3. Present only on a merged run; its presence is what tells the
# report to stop speaking as if there were one file behind it.
MERGE_KEY_SOURCES: str = "merged_from"
# ── D-179/L9. The forbidden readings, and where the permission comes from ────
#
# ⛔ CLAUDE.md §5 lists what may NOT be read from a run before the third
# pre-registration is locked: the covariance VALUE, its SIGN, the
# lived↔shuffle DIFFERENCE, the effect size, and ΔP_active. The rule existed;
# nothing enforced it, and on 2026-08-24 it was broken (D-179) — P_active was
# computed per arm and differenced, straight off the pilot.
#
# ⚠ AND THE LIMIT IS DECLARED HERE, because a gate that oversells itself is
# worse than none: the D-179 violation was an ad-hoc script, which this cannot
# see. What this removes is the CONVENIENT path — reading a forbidden number
# now takes a deliberate act instead of running the obvious tool.
#
# The permission is NOT a hand-flipped flag. It is read from the
# pre-registration itself, so it cannot drift from the document it describes:
# the status line carries 🔒 and a commit hash once the lock is taken.
PREREGISTRATION_PATH: Path = Path("docs/PREREGISTRATION_3.md")
LOCK_MARK: str = "🔒"
LOCK_COMMIT_PATTERN: str = r"commit\s+`([0-9a-f]{6,40})`"
L9_REFUSAL: str = (
    "⛔ WITHHELD (L9, D-179) — the third pre-registration is not locked, and "
    "this section reports a quantity CLAUDE.md §5 forbids reading before the "
    "lock: the covariance value or sign, the lived↔shuffle difference, the "
    "effect size, ΔP_active. Reading it now would make the endpoint choice "
    "post-hoc. Lock the pre-registration and this section returns by itself."
)


def preregistration_locked(path: Path | None = None) -> bool:
    """True once the pre-registration's status line declares a lock.

    Read from the document rather than from a constant in this file, so the
    two cannot disagree: a lock that was never written down does not open the
    report, and a report that opens is evidence the lock was written.
    """

    import re

    target = PREREGISTRATION_PATH if path is None else path
    try:
        text = target.read_text(encoding="utf-8")
    except OSError:
        # ⚠ Missing document means NOT locked. The direction matters: the
        # failure mode of a wrong guess here is either "refused a legitimate
        # reading" or "published a forbidden one", and only one of those is
        # recoverable.
        return False
    head = text.split("\n---", 1)[0]
    return LOCK_MARK in head and re.search(LOCK_COMMIT_PATTERN, head) is not None
GEN_KEY_PRICE: str = "price_for_previous_transition"
GEN_KEY_REPRODUCTION: str = "reproduction_report"
GEN_KEY_AGENTS: str = "agents"
GEN_KEY_DIGEST: str = "arm_digest"
AGENT_KEY_LANDMARK: str = "landmark"
LANDMARK_KEY_DRIFT: str = "landmark_drift_magnitudes"
LANDMARK_KEY_REACHED: str = "landmark_reached"

AGENT_KEY_DELTA_PROFILE: str = "delta_profile"
# D-121: where the runner writes the positive control, and how the report
# labels it. The label names the QUANTITY so a reader never has to guess which
# trait was declared.
GEN_KEY_CONTROL: str = "positive_control_for_previous_transition"
CONTROL_TRAIT_LABEL: str = "energy_mean_over_life"
# Printed next to a term that exists but cannot carry information.
UNDEFINED_MARK: str = "⛔ UNDEFINED (Var=0)"
# The commons-crisis sub-block D-117 added to the profile. Absent in every
# run before it, which the report says out loud rather than reading as zero.
PROFILE_KEY_CRISIS: str = "crisis"

NOT_EVALUABLE: str = "not evaluable"
# D-113. Dienes (2014) lists three ways to read a non-significant result:
# power, INTERVAL ESTIMATES, and Bayes factors. Only the middle one needs no
# threshold to be named, which is why it is the one adopted here: an estimation
# run (P7-b) should report an interval, and equivalence testing would first
# require fixing a smallest meaningful effect — the question DR #1 left open.
# ⚠ This is NOT a hypothesis test and produces no p-value.
CONFIDENCE_Z: float = 1.96  # two-sided 95%
CONFIDENCE_LABEL: str = "95%"
# A level-1 claim asks for the sign to hold across seeds. One seed cannot
# answer that, and saying so is the point: a single-seed run is where this
# project's dead findings came from.
MIN_SEEDS_FOR_SIGN_CONSISTENCY: int = 2
# Level 2 asks whether the term decays across generations, which needs at least
# two transitions to compare — i.e. G >= 3, which is A3/D-107's floor arriving
# from the other direction.
MIN_TRANSITIONS_FOR_PERSISTENCE: int = 2


@dataclass
class ArmGenerationView:
    """One arm's one generation, in the shape the reading rules ask for."""

    arm: str
    seed: int
    generation: int
    digest: str
    w_variance: float | None
    w_n_distinct: int | None
    f_agent_spread: float | None
    selection_measurable: bool | None
    price: dict[str, dict[str, float]] | None
    # D-121. Reported beside the price row, never merged into it: the control
    # answers "could this run have measured selection at all", which is a
    # different question from "did selection act on z".
    control: dict[str, Any] | None = None
    z_by_agent: dict[str, dict[str, float]] = field(default_factory=dict)
    landmark_reached: int = 0
    n_agents: int = 0
    events_lived: list[int] = field(default_factory=list)


def load_run(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _comparability_fingerprint(run: dict[str, Any]) -> dict[str, Any]:
    """The part of a run that decides whether two files may be read together.

    Two fields are dropped, and neither is dropped for convenience:

    * ``tool_identity.lora.adapter`` is a census of the adapter directory,
      which every run adds to — so two nights of the same experiment differ
      here by construction.
    * ``tool_identity.argv`` carries the seed list and the output path, which
      are exactly what a partitioned run varies on purpose.

    Everything else is compared verbatim: model, quantization, DPO settings,
    metabolism, fitness, endpoints, sampling, reproduction rule, versions,
    N, G, events. Two files that disagree on any of those are two experiments,
    and averaging across them would be the reporting drift §2.8 keeps catching.
    """

    keep = {
        key: run.get(key)
        for key in ("protocol", "n_agents", "n_generations", "events_budget",
                    "tool_identity")
    }
    fingerprint = json.loads(json.dumps(keep))
    identity = fingerprint.get("tool_identity")
    if isinstance(identity, dict):
        identity.pop("argv", None)
        lora = identity.get("lora")
        if isinstance(lora, dict):
            lora.pop("adapter", None)
    return fingerprint


def merge_runs(runs: list[dict[str, Any]], paths: list[Path]) -> dict[str, Any]:
    """Read several result files as one study (D-176/B3).

    The verifying run is planned as 70 GPU-hours, which cannot be one
    invocation, so it lands as one file per night. Until now this module took
    a single ``--results`` path and there was nothing to read them together
    with — a partitioned run would have finished with no way to report it.

    ⛔ Three refusals, none of them best-effort:

    * a CHECKPOINT is refused, by the same rule a single file is (D-111);
    * files that disagree on the instrument or the design are refused, because
      pooling them would silently average two experiments;
    * OVERLAPPING SEEDS are refused. The repetition unit is the seed
      (Lazic 2010, adopted in D-140), so the same seed counted twice is
      pseudoreplication — and it is the failure mode a partitioned run invites,
      because re-running a night that looked wrong is the natural thing to do.

    ⚠ The gate verdicts are NOT flattened into one healthy-looking stamp. A
    merged run is `clean` only if every file was, an invariant passes only if
    it passed everywhere, and the per-file ledger travels in the result so the
    report can name which night flagged what.
    """

    if not runs:
        raise ValueError("merge_runs needs at least one run")
    for run, path in zip(runs, paths):
        refuse_if_incomplete(run, path)
    first = _comparability_fingerprint(runs[0])
    for run, path in zip(runs[1:], paths[1:]):
        theirs = _comparability_fingerprint(run)
        if theirs != first:
            differing = sorted(k for k in first if theirs.get(k) != first.get(k))
            raise ValueError(
                f"{path.name} was produced by a different instrument or design "
                f"than {paths[0].name} ({differing} differ) — these are two "
                "experiments, not two nights of one."
            )
    seen: dict[int, str] = {}
    for run, path in zip(runs, paths):
        for seed in run.get(RUN_KEY_SEEDS, []):
            if int(seed) in seen:
                raise ValueError(
                    f"seed {seed} appears in both {seen[int(seed)]} and "
                    f"{path.name}. The repetition unit is the seed (D-140), so "
                    "counting one twice is pseudoreplication — drop a file or "
                    "re-run one of them on fresh seeds."
                )
            seen[int(seed)] = path.name

    names: set[str] = set()
    for run in runs:
        names.update((run.get(RUN_KEY_INVARIANTS) or {}).keys())
    invariants: dict[str, Any] = {}
    for name in sorted(names):
        verdicts = [
            (run.get(RUN_KEY_INVARIANTS) or {}).get(name) for run in runs
        ]
        # ⛔ Three outcomes, not two, and the third one is the point. Written
        # this way after a mutation run: the first version fell through to
        # `all(v is True)`, which turned a {passed one night, NOT EVALUATED the
        # other} pair into FAILED — inverting the exact distinction D-121 spent
        # a decision on. None is not False and it is not True either.
        if any(verdict is False for verdict in verdicts):
            invariants[name] = False
        elif all(verdict is True for verdict in verdicts):
            invariants[name] = True
        else:
            # Some night did not evaluate it, so the STUDY was not fully
            # checked — reporting a pass would claim coverage the merge does
            # not have. The per-file ledger says which night saw what.
            invariants[name] = None
    qualities = [run.get(RUN_KEY_QUALITY) for run in runs]
    merged: dict[str, Any] = {
        **runs[0],
        RUN_KEY_SEEDS: [seed for run in runs for seed in run.get(RUN_KEY_SEEDS, [])],
        RUN_KEY_ARMS: [arm for run in runs for arm in run.get(RUN_KEY_ARMS, [])],
        RUN_KEY_INVARIANTS: invariants,
        # ⚠ No category is invented when the files disagree. Collapsing
        # {clean, mock} or {clean, aborted} onto "flagged" would name a state
        # no run was in; "mixed:…" cannot be mistaken for any single verdict,
        # and `== "clean"` stays false, which is the direction that matters.
        RUN_KEY_QUALITY: (
            qualities[0]
            if len(set(map(str, qualities))) == 1
            else "mixed:" + "+".join(sorted({str(q) for q in qualities}))
        ),
        RUN_KEY_INFORMATIVE: all(
            bool(run.get(RUN_KEY_INFORMATIVE)) for run in runs
        ),
        MERGE_KEY_SOURCES: [
            {
                "file": path.name,
                "seeds": run.get(RUN_KEY_SEEDS),
                RUN_KEY_QUALITY: run.get(RUN_KEY_QUALITY),
                "failed": sorted(
                    name
                    for name, ok in (run.get(RUN_KEY_INVARIANTS) or {}).items()
                    if ok is False
                ),
                "replay": _replay_verdict(run),
            }
            for run, path in zip(runs, paths)
        ],
    }
    # Belongs to one file and cannot be pooled: each night replayed its own
    # first seed. The per-file ledger above carries every verdict; leaving the
    # single-run key behind would let a reader take one night's determinism
    # for the study's.
    merged.pop(RUN_KEY_REPLAY, None)
    return merged


def _replay_verdict(run: dict[str, Any]) -> str:
    replay = run.get(RUN_KEY_REPLAY)
    if replay is None:
        return "not run"
    return (
        "identical"
        if replay.get("recorded_digest") == replay.get("replay_digest")
        else "DIVERGED"
    )


def arm_views(run: dict[str, Any]) -> list[ArmGenerationView]:
    """Flatten the run into one row per arm per generation."""

    views: list[ArmGenerationView] = []
    for arm in run.get(RUN_KEY_ARMS, []):
        for row in arm.get("generations", []):
            report = row.get(GEN_KEY_REPRODUCTION) or {}
            agents = row.get(GEN_KEY_AGENTS, [])
            # ⚠ Only agents that REACHED the landmark go in, and an empty dict
            # from one that did is kept as an all-zero vector rather than
            # dropped. The two look identical in the JSON — `{}` — and they are
            # opposites: a reached landmark with no flags is a real reading of
            # zero drift (D-002's "an unflagged domain counts as 0"), while a
            # life that ended at event 6 has NO reading and must never be
            # imputed (D-073 removed LOCF for exactly this).
            # Measured: conflating them made the first version of this module
            # report "not evaluable" for every arm contrast of a run in which
            # all 12 agents had a perfectly good reading.
            z_by_agent: dict[str, dict[str, float]] = {}
            reached = 0
            for agent in agents:
                landmark = agent.get(AGENT_KEY_LANDMARK) or {}
                if not landmark.get(LANDMARK_KEY_REACHED):
                    continue
                reached += 1
                z_by_agent[agent["agent_id"]] = dict(
                    landmark.get(LANDMARK_KEY_DRIFT) or {}
                )
            views.append(
                ArmGenerationView(
                    arm=str(arm.get("arm")),
                    seed=int(arm.get("seed", -1)),
                    generation=int(row.get("generation", -1)),
                    digest=str(row.get(GEN_KEY_DIGEST, "")),
                    w_variance=report.get(REPORT_KEY_W_VARIANCE),
                    w_n_distinct=report.get(REPORT_KEY_W_DISTINCT),
                    f_agent_spread=report.get(REPORT_KEY_F_AGENT_SPREAD),
                    selection_measurable=report.get(REPORT_KEY_SELECTION_MEASURABLE),
                    price=row.get(GEN_KEY_PRICE),
                    control=row.get(GEN_KEY_CONTROL),
                    z_by_agent=z_by_agent,
                    landmark_reached=reached,
                    n_agents=len(agents),
                    events_lived=[int(a.get("events_lived", 0)) for a in agents],
                )
            )
    return views


def z_signature(z: dict[str, float]) -> tuple[tuple[str, float], ...]:
    """A hashable form of one agent's z, for counting distinct outcomes.

    Rounded nowhere: two agents whose drift differs in the twelfth decimal
    ARE different, and D-103's finding was precisely that eight agents came out
    bit-identical. Rounding here would have hidden it.
    """

    return tuple(sorted((str(k), float(v)) for k, v in z.items()))


def distinct_z(view: ArmGenerationView) -> int:
    return len({z_signature(z) for z in view.z_by_agent.values()})


def mean_z(view: ArmGenerationView, domains: list[str]) -> dict[str, float]:
    """Arm-level z, over the agents that HAVE a reading.

    Agents whose life ended before the landmark are already absent from
    ``z_by_agent`` and so contribute nothing rather than a zero: the landmark
    reader refuses to impute (D-073 removed LOCF), and averaging in a
    fabricated zero here would put it back. An agent that DID reach the
    landmark with no drift flags contributes its zeros, because that is a
    measurement.
    """

    rows = list(view.z_by_agent.values())
    if not rows:
        return {}
    return {
        domain: statistics.fmean(
            float(z.get(domain, DRIFT_ABSENT_MAGNITUDE)) for z in rows
        )
        for domain in domains
    }


def all_domains(views: list[ArmGenerationView]) -> list[str]:
    domains: set[str] = set()
    for view in views:
        for z in view.z_by_agent.values():
            domains.update(z)
        for domain in (view.price or {}):
            domains.add(domain)
    return sorted(domains)


def one_sided_share(
    a: dict[str, float], b: dict[str, float], domains: list[str]
) -> tuple[int, int, float]:
    """How much of the squared distance comes from axes only ONE arm entered.

    ⚠ D-147/AV-2. ``l2`` is arithmetically right and stays untouched: an
    unflagged domain really has no accumulated magnitude, so absent IS zero.
    What the number cannot say on its own is whether a distance is a
    DIFFERENCE — two arms that both entered an axis and landed apart — or a
    PRESENCE — one arm entered an axis the other never reached at all.

    Measured on C2 (s9912, gen2): ‖lived − null‖ = 0.087899, and 100% of it
    came from `energy`, an axis `null` never entered. RECONCILIATION §G.2 named
    this reading in 2026-08-11 for the single-lineage design; it survived into
    the population reader because nothing reported the decomposition.

    Returns (n_shared_axes, n_one_sided_axes, one_sided_fraction_of_squared).
    Fraction is 0.0 when the arms coincide everywhere — no distance, nothing
    to attribute.
    """

    shared = one_sided = 0
    total_sq = one_sided_sq = 0.0
    for domain in domains:
        first = float(a.get(domain, DRIFT_ABSENT_MAGNITUDE))
        second = float(b.get(domain, DRIFT_ABSENT_MAGNITUDE))
        gap = (first - second) ** 2
        total_sq += gap
        entered_first = first > DRIFT_ABSENT_MAGNITUDE
        entered_second = second > DRIFT_ABSENT_MAGNITUDE
        if entered_first and entered_second:
            shared += 1
        elif entered_first or entered_second:
            one_sided += 1
            one_sided_sq += gap
    fraction = 0.0 if total_sq <= 0.0 else one_sided_sq / total_sq
    return shared, one_sided, fraction


def l2(a: dict[str, float], b: dict[str, float], domains: list[str]) -> float:
    """Distance over the union of domains, absent = 0.

    The absent-is-zero rule is the endpoint's own definition (an unflagged
    domain really has no accumulated magnitude), not a convenience.
    """

    return math.sqrt(
        sum(
            (
                float(a.get(d, DRIFT_ABSENT_MAGNITUDE))
                - float(b.get(d, DRIFT_ABSENT_MAGNITUDE))
            )
            ** 2
            for d in domains
        )
    )


# ---------------------------------------------------------------------------
# The four levels
# ---------------------------------------------------------------------------


def wilson_interval(successes: int, trials: int) -> tuple[float, float, float]:
    """Point estimate and Wilson score interval for a proportion.

    Wilson rather than Wald, deliberately: the quantity we are estimating is
    rare (B1 measured 3/72) and the Wald interval misbehaves exactly there —
    it can run below zero and its coverage collapses for small p, which is the
    subject of McGrath & Burke (arXiv:2109.02516). Wilson stays inside [0, 1]
    and keeps its coverage at small p, and it costs one extra line.
    """

    if trials <= 0:
        return (float("nan"), float("nan"), float("nan"))
    p = successes / trials
    z2 = CONFIDENCE_Z * CONFIDENCE_Z
    denom = 1.0 + z2 / trials
    centre = (p + z2 / (2 * trials)) / denom
    half = (
        CONFIDENCE_Z
        * math.sqrt(p * (1 - p) / trials + z2 / (4 * trials * trials))
    ) / denom
    return (p, max(0.0, centre - half), min(1.0, centre + half))


def trauma_headroom(run: dict[str, Any]) -> list[str]:
    """How close the universe came to the endpoint's own trigger (D-112).

    ⚠ This section exists because a run can report an all-zero endpoint for two
    opposite reasons — the universe never came near the trigger, or it came
    within a hair of it — and the endpoint decision goes the other way in each
    case. Before D-112 the results file could not tell them apart.
    """

    peaks: list[float] = []
    crossings = 0
    lives = 0
    # The SECOND writer of z (D-115/D-117): a famine scars every agent of an
    # arm at the same event, so it fills z while leaving the individual channel
    # empty. Counted apart and never pooled — pooled, the two are exactly as
    # indistinguishable as they were before D-117.
    crisis_lives = 0
    crisis_crossings = 0
    crisis_channel_present = False
    for arm in run.get(RUN_KEY_ARMS, []):
        for row in arm.get("generations", []):
            for agent in row.get(GEN_KEY_AGENTS, []):
                profile = agent.get(AGENT_KEY_DELTA_PROFILE) or {}
                if not profile:
                    continue
                crisis = profile.get(PROFILE_KEY_CRISIS)
                if crisis is not None:
                    crisis_channel_present = True
                    if int(crisis.get("n_crisis_events", 0)) > 0:
                        crisis_lives += 1
                    if int(crisis.get("n_at_or_above_trauma", 0)) > 0:
                        crisis_crossings += 1
                if profile.get("max") is None:
                    continue
                lives += 1
                peaks.append(float(profile["max"]))
                if int(profile.get("n_at_or_above_trauma", 0)) > 0:
                    crossings += 1
    if not lives and not crisis_channel_present:
        return [
            "  no delta profile in this run — it predates D-112, so how close "
            "the universe came to the trigger cannot be read from it"
        ]
    if not lives:
        return [
            "  no individual-channel reading in this run",
            *_crisis_lines(crisis_channel_present, crisis_lives, crisis_crossings),
        ]
    peaks.sort()
    point, low, high = wilson_interval(crossings, lives)
    return [
        "  individual channel — the agent's OWN surprise (graph, PE path):",
        f"  lives with a reading: {lives}",
        f"  peak delta magnitude: min={peaks[0]:.4f} "
        f"median={peaks[len(peaks) // 2]:.4f} max={peaks[-1]:.4f}",
        f"  lives that crossed the trauma threshold: {crossings}/{lives}",
        f"  crossing rate = {point:.4f}, {CONFIDENCE_LABEL} Wilson interval "
        f"[{low:.4f}, {high:.4f}]",
        "",
        # ⚠ Worded WITHOUT the token "p-value" on purpose: the guard that
        # keeps this module test-free searches the rendered report for that
        # token, and a disclaimer containing it would trip its own guard —
        # which it did, the first time this line was written.
        "⚠ An interval, not a test: no significance test is computed here and "
        "none may be quoted. This says how precisely the RATE is known, and "
        "nothing about whether the arms differ.",
        "",
        *_crisis_lines(crisis_channel_present, crisis_lives, crisis_crossings),
    ]


def _crisis_lines(present: bool, lives: int, crossings: int) -> list[str]:
    """The commons-crisis channel, reported beside the individual one (D-117)."""

    if not present:
        return [
            "  commons-crisis channel: ABSENT — this run predates D-117, so a "
            "life scarred by famine is indistinguishable in it from a life "
            "nothing happened to (that is the D-115 reading error itself)"
        ]
    return [
        "  commons channel — a famine that scars EVERY agent at once:",
        f"  lives that saw a crisis event: {lives}",
        f"  lives the crisis scarred at or above the trauma threshold: "
        f"{crossings}",
        "",
        "⚠ A crisis hits the whole arm simultaneously, so its contribution to "
        "z carries NO between-agent information: it can fill z and leave "
        "Cov(w, z) at zero. Read the two channels apart — a run whose z came "
        "only from here has an endpoint the arms cannot differ on (D-115).",
    ]


def level0_gate(run: dict[str, Any], views: list[ArmGenerationView]) -> list[str]:
    """Var(w) > 0, and the run-health facts a reader needs before anything else.

    ⚠ Claims NOTHING. Every line here is a precondition: if this section fails
    the sections below are not weak evidence, they are undefined.
    """

    lines = [
        f"run_quality = {run.get(RUN_KEY_QUALITY)}",
        f"invariants  = {run.get(RUN_KEY_INVARIANTS)}",
    ]
    informative = run.get(RUN_KEY_INFORMATIVE)
    if informative is None:
        lines.append(
            "generations_informative: ABSENT — this run predates A3/D-107; "
            "check G by hand"
        )
    elif not informative:
        lines.append(
            "⛔ generations_informative = false — G < 3, so the only transition "
            "this run has is the one whose selection term is zero BY "
            "CONSTRUCTION (D-107). Levels 1-2 below cannot mean anything."
        )
    sources = run.get(MERGE_KEY_SOURCES)
    if sources:
        # D-176/B3. One line per file, because the study's health is not a
        # single fact: a night that flagged I4.2 and a night that did not are
        # different measurements, and a merged stamp would hide which was
        # which. Printed INSTEAD of the single-run replay line — each night
        # replayed its own first seed, so there is no study-level replay.
        lines.append("")
        lines.append(f"merged from {len(sources)} files:")
        for source in sources:
            failed = ", ".join(source.get("failed") or []) or "none"
            lines.append(
                f"  {source.get('file')}: seeds={source.get('seeds')} "
                f"quality={source.get(RUN_KEY_QUALITY)} "
                f"failed={failed} I4.1 replay={source.get('replay')}"
            )
    else:
        replay = run.get(RUN_KEY_REPLAY)
        if replay is None:
            lines.append("I4.1 replay: not run — determinism is not demonstrated")
        else:
            same = replay.get("recorded_digest") == replay.get("replay_digest")
            lines.append(
                f"I4.1 replay: {'identical' if same else 'DIVERGED'} over "
                f"{replay.get('n_generations')} generation(s)"
            )

    lines.append("")
    lines.append("Var(w) per arm per transition — the gate itself:")
    for view in views:
        if view.w_variance is None:
            lines.append(
                f"  s{view.seed} {view.arm:<8} gen{view.generation}: no transition "
                "(final generation produces no heirs)"
            )
            continue
        verdict = "OPEN" if view.selection_measurable else "⛔ CLOSED"
        lines.append(
            f"  s{view.seed} {view.arm:<8} gen{view.generation}: Var(w)={view.w_variance:.4f} "
            f"distinct(w)={view.w_n_distinct} "
            f"F_agent spread={view.f_agent_spread:.4f} → {verdict}"
        )
    lines.append("")
    lines.append("Distinct z per generation (D-104 compared 1/8 vs 4/8):")
    for view in views:
        lines.append(
            f"  s{view.seed} {view.arm:<8} gen{view.generation}: {distinct_z(view)} distinct "
            f"among {len(view.z_by_agent)} reading(s), landmark reached "
            f"{view.landmark_reached}/{view.n_agents}"
        )
    return lines


def level1_selection(
    run: dict[str, Any], views: list[ArmGenerationView]
) -> list[str]:
    """Cov(w, z) per domain, and whether the sign question is even askable."""

    n_seeds = len(run.get(RUN_KEY_SEEDS, []))
    lines: list[str] = []
    for view in views:
        if view.price is None:
            continue
        lines.append(
            f"  s{view.seed} {view.arm:<8} gen{view.generation} "
            "closes the previous transition:"
        )
        for domain in sorted(view.price):
            part = view.price[domain]
            # D-121. Var(z) = 0 within a cell makes the selection term zero BY
            # CONSTRUCTION, and printing that zero like any other is the single
            # most likely misreading of this whole report: it looks exactly
            # like "selection acted and came out flat". Measured: 14 of 27
            # cells of the headroom run were degenerate. So the term is
            # labelled, not hidden — the number stays visible and the label
            # says what it can carry (Rothenberg 1971, 10.2307/1913267).
            estimable = part.get(PRICE_KEY_ESTIMABLE)
            mark = "" if estimable is not False else f"  {UNDEFINED_MARK}"
            lines.append(
                f"    {domain:<14} selection={part[PRICE_KEY_SELECTION]:+.6f}  "
                f"transmission={part[PRICE_KEY_TRANSMISSION]:+.6f}  "
                f"Δz̄={part[PRICE_KEY_DELTA_ZBAR]:+.6f}{mark}"
            )
        degenerate = sum(
            1 for part in view.price.values()
            if part.get(PRICE_KEY_ESTIMABLE) is False
        )
        if degenerate:
            lines.append(
                f"    ⛔ {degenerate} of {len(view.price)} domains: every parent "
                "of this cell carried the SAME z, so Var(z) = 0 and the "
                "selection term is zero by construction. This is NOT 'no "
                "selection was measured' — nothing could have been measured."
            )
        # Only a NON-empty partition can be missing the flag. An empty one
        # carries no domains at all, which the line below already says — and
        # calling that "predates D-121" was simply false on a run that has the
        # field everywhere it applies (D-127).
        if view.price and PRICE_KEY_ESTIMABLE not in _any_part(view.price):
            lines.append(
                "    ⚠ estimability ABSENT — this run predates D-121 and cannot "
                "say whether its zeros were measurable"
            )
        if not view.price:
            lines.append(
                "    (empty — z carried no domains; the partition says nothing)"
            )
    if not lines:
        lines.append("  no transition was closed at all")
    lines.extend(positive_control(views))
    lines.append("")
    if n_seeds < MIN_SEEDS_FOR_SIGN_CONSISTENCY:
        lines.append(
            f"⚠ sign consistency across seeds: {NOT_EVALUABLE} — this run has "
            f"{n_seeds} seed. A level-1 claim REQUIRES the sign to hold across "
            "seeds, so no level-1 claim is available from this run however "
            "large the term is."
        )
    else:
        lines.append(
            f"sign consistency across seeds: {n_seeds} seeds present — compare "
            "the per-seed signs above by hand; this module does not test."
        )
    return lines


def _any_part(price: dict[str, Any]) -> dict[str, Any]:
    """One domain's partition, or an empty dict when there are none."""

    for part in price.values():
        return part
    return {}


def positive_control(views: list[ArmGenerationView]) -> list[str]:
    """The pre-declared control trait — D-121, and it answers a different question.

    ⛔ Not an endpoint and not evidence of inheritance. It exists to separate
    "selection acted and we measured none" from "this run could not have
    measured any selection at all": the SAME w is covaried with a quantity
    that does vary, so a flat z next to a moving control means the machinery
    worked and z was the flat thing.
    """

    rows = [(v, v.control) for v in views if getattr(v, "control", None)]
    if not rows:
        return [
            "",
            "  positive control: ABSENT — this run predates D-121, so a null "
            "here cannot be told apart from a broken selection engine",
        ]
    lines = ["", f"  positive control ({CONTROL_TRAIT_LABEL}) — NOT an endpoint:"]
    for view, control in rows:
        mark = "" if control.get(CONTROL_KEY_ESTIMABLE) else f"  {UNDEFINED_MARK}"
        lines.append(
            f"    s{view.seed} {view.arm:<8} gen{view.generation}  "
            f"Cov(w, control)={float(control[CONTROL_KEY_COVARIANCE]):+.6f}  "
            f"Var(control)={float(control[CONTROL_KEY_VARIANCE]):.6f}{mark}"
        )
    return lines


def level2_persistence(views: list[ArmGenerationView]) -> list[str]:
    """Does the term survive across transitions? Reported, never tested."""

    lines: list[str] = []
    # ⛔ Keyed by (arm, SEED), not by arm alone (D-127). With the seed left out,
    # three seeds' transitions were appended into one list and printed as a
    # single arrow sequence — "gen2 → gen3 → gen2 → gen3 → …" reads as one
    # lineage's trajectory and was in fact three unrelated ones. Persistence is
    # a statement about a lineage over time, so mixing seeds into the sequence
    # answers a different question than the one the section asks.
    by_arm_seed: dict[tuple[str, int], list[ArmGenerationView]] = {}
    for view in views:
        if view.price is not None:
            by_arm_seed.setdefault((view.arm, view.seed), []).append(view)

    for (arm, seed), rows in sorted(by_arm_seed.items()):
        rows = sorted(rows, key=lambda v: v.generation)
        if len(rows) < MIN_TRANSITIONS_FOR_PERSISTENCE:
            lines.append(
                f"  {arm:<8} s{seed}: {len(rows)} closed transition — "
                f"{NOT_EVALUABLE}, persistence needs at least "
                f"{MIN_TRANSITIONS_FOR_PERSISTENCE}"
            )
            continue
        domains = sorted({d for row in rows for d in (row.price or {})})
        for domain in domains:
            series = [
                (row.generation, (row.price or {}).get(domain, {}).get(
                    PRICE_KEY_SELECTION, 0.0))
                for row in rows
            ]
            shown = " → ".join(f"gen{g}:{v:+.6f}" for g, v in series)
            lines.append(f"  {arm:<8} s{seed} {domain:<14} {shown}")
    if not lines:
        lines.append("  nothing to compare")
    lines.append("")
    lines.append(
        "⚠ Read as a sequence, not a trend: no slope is fitted and none may be "
        "claimed. 'Does not decay' is a description of these numbers only."
    )
    return lines


def level3_arm_contrast(views: list[ArmGenerationView]) -> list[str]:
    """lived vs shuffle vs null, per generation. The INHERITANCE question.

    ⚠ Kept separate from level 1 on purpose. Price measures selection inside an
    arm; only this section can speak about the channel, and in B2 all three
    arms came out equidistant while the machinery looked healthy.
    """

    domains = all_domains(views)
    # ⛔ Keyed by (SEED, generation), not by generation alone (D-127). Without
    # the seed, `[arm] = view` let the LAST seed overwrite the others and three
    # seeds' arm contrasts were reported as one — silently, and the section
    # looked healthy. The arm contrast is the inheritance question, so a
    # collapsed one is the most expensive wrong number this report can print.
    by_cell: dict[tuple[int, int], dict[str, ArmGenerationView]] = {}
    for view in views:
        by_cell.setdefault((view.seed, view.generation), {})[view.arm] = view

    lines: list[str] = []
    for (seed, generation) in sorted(by_cell):
        arms = by_cell[(seed, generation)]
        lines.append(f"  s{seed} gen{generation}:")
        digests = {arm: view.digest[:12] for arm, view in sorted(arms.items())}
        distinct = len(set(digests.values()))
        lines.append(
            f"    digests {digests} → "
            f"{distinct}/{len(digests)} distinct"
            + (
                "  ⚠ identical arms cannot differ in ANY endpoint"
                if distinct == 1
                else ""
            )
        )
        means = {arm: mean_z(view, domains) for arm, view in arms.items()}
        names = sorted(means)
        for i, first in enumerate(names):
            for second in names[i + 1:]:
                if not means[first] or not means[second]:
                    lines.append(
                        f"    ‖{first} − {second}‖ = {NOT_EVALUABLE} "
                        "(an arm has no landmark reading)"
                    )
                    continue
                shared, one_sided, share = one_sided_share(
                    means[first], means[second], domains
                )
                note = ""
                if one_sided:
                    note = (
                        f"  ⚠ {share:.0%} of it from {one_sided} axis/axes only "
                        f"one arm entered ({shared} shared)"
                    )
                lines.append(
                    f"    ‖{first} − {second}‖ = "
                    f"{l2(means[first], means[second], domains):.6f}{note}"
                )
    lines.append("")
    lines.append(
        "⚠ Equal distances are the outcome to watch for: B2 measured "
        "0.3852 / 0.3812 / 0.3814 and that pattern is a NULL, not a signal."
    )
    return lines


def health(views: list[ArmGenerationView]) -> list[str]:
    """Descriptive only — the facts that decide whether the above is readable."""

    lines: list[str] = []
    for view in views:
        lived = view.events_lived
        if not lived:
            continue
        lines.append(
            f"  {view.arm:<8} gen{view.generation}: lifespans "
            f"min={min(lived)} max={max(lived)} mean={statistics.fmean(lived):.1f} "
            f"n={len(lived)}"
        )
    return lines


FORBIDDEN: tuple[str, ...] = (
    '"significant" — no test was run (P7-b: this is an estimation run, D-096)',
    "anything at the individual level — P1 makes this a GROUP-level design "
    "(Chevin 2011)",
    '"LLM agents inherit Lamarckian traits" — one model, one niche family, '
    "n = 1 experiment",
    "anything via delta_pe — P6 removed that endpoint",
    '"inheritance flowed" from level 1 — Price gives SELECTION; inheritance is '
    "level 3",
)


class IncompleteRun(ValueError):
    """Raised when asked to report on a checkpoint rather than a result."""


def refuse_if_incomplete(run: dict[str, Any], path: Path) -> None:
    """A checkpoint is not a result and must not be reported as one (D-111).

    The two files differ by one boolean and by the absence of a gate block, and
    the partial one is missing arms — so a report built from it would look
    exactly like a smaller, healthy run. Refusing is the only reading that
    cannot be mistaken.
    """

    if run.get(RUN_KEY_COMPLETE) is False:
        raise IncompleteRun(
            f"{path.name} is a CHECKPOINT, not a result: it was written while "
            f"the run was still going and no preflight gate has run on it. "
            f"Refusing to report it. Use it for diagnosis by hand."
        )


def format_report(
    run: dict[str, Any], path: Path, *, unlocked: bool | None = None
) -> str:
    """The report. ``unlocked`` defaults to asking the pre-registration itself.

    ⚠ The parameter exists so tests can drive both states, NOT so a caller can
    grant itself permission: nothing in the codebase passes it, and a caller
    that did would be writing the violation down in its own source.
    """

    refuse_if_incomplete(run, path)
    if unlocked is None:
        unlocked = preregistration_locked()
    views = arm_views(run)
    sources = run.get(MERGE_KEY_SOURCES)
    title = (
        path.name
        if not sources
        else " + ".join(str(source.get("file")) for source in sources)
    )
    out: list[str] = [
        f"# Population run report — {title}",
        "",
        f"note: {run.get('note')}",
        f"seeds={run.get(RUN_KEY_SEEDS)} N={run.get('n_agents')} "
        f"G={run.get('n_generations')} events={run.get('events_budget')}",
        "",
        (
            "pre-registration: 🔒 LOCKED — levels 1-3 readable"
            if unlocked
            else "pre-registration: 📝 NOT LOCKED — levels 1-3 WITHHELD (L9)"
        ),
        "",
        "## Level 0 — gate (claims NOTHING; this is a precondition)",
        *level0_gate(run, views),
        "",
        "## Trauma headroom — can the universe even reach the endpoint? (D-112)",
        *trauma_headroom(run),
        "",
        "## Level 1 — selection: Cov(w, z)",
        # D-179/L9. Levels 1-3 are exactly the forbidden readings: 1 prints the
        # covariance and its sign, 2 prints how that term moves, 3 prints the
        # lived↔shuffle distance. Level 0, health and headroom stay open —
        # those are DEFINEDNESS, which CLAUDE.md permits in the same breath as
        # it forbids these ("kol farkına değil, dağılımın var olup olmadığına").
        *(level1_selection(run, views) if unlocked else [f"  {L9_REFUSAL}"]),
        "",
        "## Level 2 — accumulation across generations",
        *(level2_persistence(views) if unlocked else [f"  {L9_REFUSAL}"]),
        "",
        "## Level 3 — arm contrast (the INHERITANCE question)",
        *(level3_arm_contrast(views) if unlocked else [f"  {L9_REFUSAL}"]),
        "",
        "## Health (descriptive)",
        *health(views),
        "",
        "## ⛔ May NOT be claimed from this report",
    ]
    out.extend(f"  - {item}" for item in FORBIDDEN)
    return "\n".join(out)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    # D-176/B3. nargs="+" so a partitioned run can be reported: pass every
    # night's file and they are merged, with the refusals merge_runs documents.
    parser.add_argument("--results", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    paths = list(args.results)
    runs = [load_run(path) for path in paths]
    run = runs[0] if len(runs) == 1 else merge_runs(runs, paths)
    report = format_report(run, paths[0])
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    print(report)


if __name__ == "__main__":
    main()
