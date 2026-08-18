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
                f"  {view.arm:<8} gen{view.generation}: no transition "
                "(final generation produces no heirs)"
            )
            continue
        verdict = "OPEN" if view.selection_measurable else "⛔ CLOSED"
        lines.append(
            f"  {view.arm:<8} gen{view.generation}: Var(w)={view.w_variance:.4f} "
            f"distinct(w)={view.w_n_distinct} "
            f"F_agent spread={view.f_agent_spread:.4f} → {verdict}"
        )
    lines.append("")
    lines.append("Distinct z per generation (D-104 compared 1/8 vs 4/8):")
    for view in views:
        lines.append(
            f"  {view.arm:<8} gen{view.generation}: {distinct_z(view)} distinct "
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
        lines.append(f"  {view.arm:<8} gen{view.generation} closes the previous transition:")
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
        if PRICE_KEY_ESTIMABLE not in _any_part(view.price):
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
            f"    {view.arm:<8} gen{view.generation}  "
            f"Cov(w, control)={float(control[CONTROL_KEY_COVARIANCE]):+.6f}  "
            f"Var(control)={float(control[CONTROL_KEY_VARIANCE]):.6f}{mark}"
        )
    return lines


def level2_persistence(views: list[ArmGenerationView]) -> list[str]:
    """Does the term survive across transitions? Reported, never tested."""

    lines: list[str] = []
    by_arm: dict[str, list[ArmGenerationView]] = {}
    for view in views:
        if view.price is not None:
            by_arm.setdefault(view.arm, []).append(view)

    for arm, rows in sorted(by_arm.items()):
        if len(rows) < MIN_TRANSITIONS_FOR_PERSISTENCE:
            lines.append(
                f"  {arm:<8}: {len(rows)} closed transition — {NOT_EVALUABLE}, "
                f"persistence needs at least {MIN_TRANSITIONS_FOR_PERSISTENCE}"
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
            lines.append(f"  {arm:<8} {domain:<14} {shown}")
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
    by_generation: dict[int, dict[str, ArmGenerationView]] = {}
    for view in views:
        by_generation.setdefault(view.generation, {})[view.arm] = view

    lines: list[str] = []
    for generation in sorted(by_generation):
        arms = by_generation[generation]
        lines.append(f"  gen{generation}:")
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
                lines.append(
                    f"    ‖{first} − {second}‖ = "
                    f"{l2(means[first], means[second], domains):.6f}"
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


def format_report(run: dict[str, Any], path: Path) -> str:
    refuse_if_incomplete(run, path)
    views = arm_views(run)
    out: list[str] = [
        f"# Population run report — {path.name}",
        "",
        f"note: {run.get('note')}",
        f"seeds={run.get(RUN_KEY_SEEDS)} N={run.get('n_agents')} "
        f"G={run.get('n_generations')} events={run.get('events_budget')}",
        "",
        "## Level 0 — gate (claims NOTHING; this is a precondition)",
        *level0_gate(run, views),
        "",
        "## Trauma headroom — can the universe even reach the endpoint? (D-112)",
        *trauma_headroom(run),
        "",
        "## Level 1 — selection: Cov(w, z)",
        *level1_selection(run, views),
        "",
        "## Level 2 — accumulation across generations",
        *level2_persistence(views),
        "",
        "## Level 3 — arm contrast (the INHERITANCE question)",
        *level3_arm_contrast(views),
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
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    report = format_report(load_run(args.results), args.results)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    print(report)


if __name__ == "__main__":
    main()
