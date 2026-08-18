"""Preflight invariants (D-012) — a run must prove itself before it reports.

Seven instrument failures in this project all produced numbers: lora_B=0 fake
training, adapter leakage, greedy plateau, precision saturation, GAP-1 (three
identical arms), GAP-11 (random shuffle seed), GAP-14 (inert PPR). None
crashed. The disease is not "we missed bugs" — it is that the system emits
output independently of whether the output means anything.

Invariants invert that: before results are written, the run has to prove a
list about itself.

Failure modes
-------------
ABORT  the run stops and no JSON is written — a silent fake result becomes
       impossible.
FLAG   the run continues; the result carries invariants.<id> = false and a
       run_quality stamp. Usable in analysis, but labelled.

Rule from D-012: no invariant whose threshold is still uncalibrated may
ABORT. Killing a run on an invented constant is worse than labelling it.

Ids here match docs/PREFLIGHT_INVARIANTS.md exactly. Phase 0 lives in this
module; later phases are added as their instrumentation lands.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable

MODE_ABORT: str = "abort"
MODE_FLAG: str = "flag"
# D-073. Measured and written into the results file, but never reaches
# run_quality. For quantities that are a FINDING about the universe rather
# than a fact about instrument health — flagging those would stamp every run
# from here on and leave the stamp meaning nothing.
MODE_REPORT: str = "report"

RUN_QUALITY_CLEAN: str = "clean"
RUN_QUALITY_FLAGGED: str = "flagged"
RUN_QUALITY_ABORTED: str = "aborted"
# A mock run can never be clean: it uses a canned LLM, so its arms are
# identical by construction and its training invariants cannot even run.
RUN_QUALITY_MOCK: str = "mock"

PYTHONHASHSEED_ENV: str = "PYTHONHASHSEED"
CUBLAS_WORKSPACE_CONFIG_ENV: str = "CUBLAS_WORKSPACE_CONFIG"

# --- phase 3 thresholds ----------------------------------------------------
# Sources are in docs/PREFLIGHT_INVARIANTS.md. Uncalibrated ones stay FLAG:
# killing a run on an invented constant is worse than labelling it.
#
# Note these are deliberately stricter than run_protocol_c_prime's
# SMOKE_SATURATION_MAX_RATE=0.30 / SMOKE_PI_MIN_DISTINCT=3. The smoke gate is
# left alone; D-012 derived these from the v3 smoke measurement (saturation
# 0.0025, π distinct 14) with a 20x margin, and the two gates answer
# different questions.
SATURATION_MAX: float = 0.05  # D-012; uncalibrated (proposal, not locked)
PI_N_DISTINCT_MIN: int = 8  # D-012; uncalibrated
GATED_FRACTION_MAX: float = 0.20  # last run measured 3/15; uncalibrated
# Any shortfall against the budget is reported. Not a guessed threshold: it
# used to mean "any fabricated data earns a label", and with LOCF gone (D-073)
# nothing is fabricated — the same 0.0 now means "report every event the
# cohort did not reach", which is a finding, so MODE_REPORT and not FLAG.
PAD_FRACTION_MAX: float = 0.0

NOT_APPLICABLE_MOCK: str = "not applicable under mock LLM"


class PreflightAbort(RuntimeError):
    """Raised when an ABORT-mode invariant fails. No results are written."""


@dataclass
class InvariantResult:
    """One invariant's verdict.

    ``passed=None`` means *not applicable* — deliberately distinct from True.
    A check that could not run must never read as a check that succeeded.
    """

    id: str
    passed: bool | None
    mode: str
    detail: str
    calibrated: bool = True

    @property
    def failed(self) -> bool:
        return self.passed is False


@dataclass
class Preflight:
    """Collects invariant results for one run and renders the JSON blocks."""

    mock: bool = False
    results: list[InvariantResult] = field(default_factory=list)

    def record(
        self,
        invariant_id: str,
        passed: bool | None,
        *,
        mode: str,
        detail: str = "",
        calibrated: bool = True,
    ) -> InvariantResult:
        result = InvariantResult(
            id=invariant_id,
            passed=passed,
            mode=mode,
            detail=detail,
            calibrated=calibrated,
        )
        self.results.append(result)
        return result

    def check(
        self,
        invariant_id: str,
        # bool | None: a predicate may report "not applicable", which record()
        # keeps distinct from True and enforce() does not treat as a failure.
        predicate: Callable[[], tuple[bool | None, str]],
        *,
        mode: str,
        calibrated: bool = True,
    ) -> InvariantResult:
        """Run one predicate, recording the failure rather than raising it.

        A check that blows up is a failed check: an exception here would
        otherwise abort with a traceback instead of a named invariant.
        """

        try:
            passed, detail = predicate()
        except Exception as exc:  # noqa: BLE001 — a broken check is a failure
            passed, detail = False, f"check raised {exc!r}"
        return self.record(
            invariant_id,
            passed,
            mode=mode,
            detail=detail,
            calibrated=calibrated,
        )

    # -- reporting ---------------------------------------------------------

    def failures(self, mode: str) -> list[InvariantResult]:
        return [r for r in self.results if r.failed and r.mode == mode]

    def enforce(self) -> None:
        """Stop the run if any ABORT-mode invariant failed."""

        failed = self.failures(MODE_ABORT)
        if not failed:
            return
        lines = [f"  {r.id}: {r.detail}" for r in failed]
        raise PreflightAbort(
            "Preflight ABORT — results will not be written:\n" + "\n".join(lines)
        )

    def invariants(self) -> dict[str, bool | None]:
        return {r.id: r.passed for r in self.results}

    def details(self) -> dict[str, dict[str, Any]]:
        return {
            r.id: {
                "passed": r.passed,
                "mode": r.mode,
                "calibrated": r.calibrated,
                "detail": r.detail,
            }
            for r in self.results
        }

    def run_quality(self) -> str:
        """Worst-first, so the stamp never hides a live problem.

        A flagged mock reports "flagged" rather than "mock": both are true and
        the flag is the one that matters. Mock still outranks clean, so a
        canned-LLM run can never be stamped clean.
        """

        if self.failures(MODE_ABORT):
            return RUN_QUALITY_ABORTED
        if self.failures(MODE_FLAG):
            return RUN_QUALITY_FLAGGED
        if self.mock:
            return RUN_QUALITY_MOCK
        return RUN_QUALITY_CLEAN

    def block(self) -> dict[str, Any]:
        return {
            "invariants": self.invariants(),
            "invariant_details": self.details(),
            "run_quality": self.run_quality(),
            "mock": self.mock,
        }


# ---------------------------------------------------------------------------
# Phase 0 checks — before the run starts, before any GPU work
# ---------------------------------------------------------------------------


def _walk_for_none(node: Any, path: str) -> str:
    """First path holding None, or empty string when every leaf is set."""

    if isinstance(node, dict):
        for key, value in node.items():
            found = _walk_for_none(value, f"{path}.{key}")
            if found:
                return found
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found = _walk_for_none(value, f"{path}[{index}]")
            if found:
                return found
    elif node is None:
        return path
    return ""


def check_tool_identity(tool_identity: dict[str, Any]) -> tuple[bool, str]:
    """I0.1 — every field of the instrument record is determinable."""

    missing = _walk_for_none(tool_identity, "tool_identity")
    if missing:
        return False, f"undeterminable field: {missing}"
    return True, (
        f"backend={tool_identity.get('backend')} "
        f"model={tool_identity.get('model_id')}"
    )


def check_lora_choice(tool_identity: dict[str, Any]) -> tuple[bool, str]:
    """I0.2 — the LoRA gate was a stated choice and the env agrees with it."""

    from dau.diagnostics.tool_identity import (
        LORA_CHOICE_OFF,
        LORA_CHOICE_ON,
        LORA_ENABLED_OFF,
        LORA_ENABLED_ON,
    )

    lora = tool_identity.get("lora", {})
    choice = lora.get("choice")
    env = str(lora.get("enabled_env", ""))
    if choice not in {LORA_CHOICE_ON, LORA_CHOICE_OFF}:
        return False, f"lora choice not stated: {choice!r}"
    expected = LORA_ENABLED_ON if choice == LORA_CHOICE_ON else LORA_ENABLED_OFF
    if env != expected:
        return False, f"choice={choice} but {env=} (expected {expected})"
    return True, f"choice={choice} env={env}"


def check_pythonhashseed() -> tuple[bool, str]:
    """I0.3 — PYTHONHASHSEED pinned.

    GAP-11's seed parser no longer falls back to hash(), so this is a belt
    rather than the only strap: set ordering and any future hash use stay
    reproducible across processes. Only the interpreter can honour it, so
    the runner refuses rather than setting it and re-executing itself —
    a re-exec would be a hidden mechanism where an explicit one will do.
    """

    raw = os.environ.get(PYTHONHASHSEED_ENV, "").strip()
    if not raw:
        return False, (
            f"{PYTHONHASHSEED_ENV} is unset — re-run as "
            f"`{PYTHONHASHSEED_ENV}=0 python -m ...`"
        )
    if raw == "random":
        return False, f"{PYTHONHASHSEED_ENV}=random defeats replay"
    return True, f"{PYTHONHASHSEED_ENV}={raw}"


def check_seed_derivation(
    agent_ids: list[str],
    seeds: list[int],
    derive: Callable[[str], int] | None = None,
) -> tuple[bool, str]:
    """I0.4 — every planned agent_id yields the seed it is supposed to.

    ``derive`` is the parser the CALLER's ids are built for, because id
    formats differ per runner and the seed segment sits in a different place
    in each: Protocol C′ ends in the seed, the population wrapper carries it
    mid-string as ``-s{seed}-a{index}``. Defaulting to the C′ parser keeps the
    multigen path exactly as it was; the population runner passes its own and
    stops being the runner without this gate (D-105's declared debt).
    """

    if derive is None:
        from dau.diagnostics.run_protocol_c_prime import _seed_from_agent_id

        derive = _seed_from_agent_id
    if not agent_ids:
        return False, "no agent_ids to verify"
    expected = set(seeds)
    for agent_id in agent_ids:
        derived = derive(agent_id)
        if derived not in expected:
            return False, f"{agent_id} → {derived}, not in planned seeds"
    return True, f"{len(agent_ids)} agent_ids verified"


def check_import_time_env(
    bindings: list[tuple[str, Any, str, Callable[[str], Any]]],
) -> tuple[bool, str]:
    """I0.5 — values captured at import still match the environment.

    ``bindings`` are (name, value_bound_at_import, env_var, parser). An env
    var changed after import is silently ignored by the module that read it,
    so the run would use one setting and could report another (GAP-15).
    """

    stale: list[str] = []
    for name, bound, env_var, parse in bindings:
        raw = os.environ.get(env_var, "").strip()
        if not raw:
            continue
        if parse(raw) != bound:
            stale.append(f"{name}={bound!r} but {env_var}={raw!r}")
    if stale:
        return False, "; ".join(stale)
    return True, f"{len(bindings)} import-time bindings match env"


def check_determinism_settings() -> tuple[bool, str]:
    """I0.6 — determinism is actually switched on, not merely intended.

    Checks state rather than setting it: the runner locks seeds first and
    this reports what that produced. Without torch there is no CUDA
    nondeterminism to guard against, which is recorded as not applicable.
    """

    try:
        import torch
    except ImportError:
        return True, "torch not installed — no CUDA nondeterminism to guard"

    problems: list[str] = []
    if not os.environ.get(CUBLAS_WORKSPACE_CONFIG_ENV, "").strip():
        problems.append(f"{CUBLAS_WORKSPACE_CONFIG_ENV} unset")
    if not torch.are_deterministic_algorithms_enabled():
        problems.append("torch deterministic algorithms off")
    try:
        if not torch.backends.cudnn.deterministic:
            problems.append("cudnn.deterministic off")
    except Exception:  # noqa: BLE001 — CPU-only builds have no cudnn
        pass
    # D-037. warn_only used to be reported and tolerated. Measured: under it,
    # two runs of the same seed and code produced different adapter weights and
    # flipped 21 of 50 phase-2 decisions, while the untrained arm stayed
    # bit-exact. A run that merely reports the setting cannot tell afterwards
    # whether its trained arms were reproducible, so this is now a failure
    # rather than a note.
    if bool(torch.is_deterministic_algorithms_warn_only_enabled()):
        problems.append(
            "deterministic algorithms in warn_only mode — trained arms drift "
            "between runs (D-037)"
        )
    if problems:
        return False, "; ".join(problems)
    return True, "deterministic algorithms on (warn_only=False)"


# ---------------------------------------------------------------------------
# Phase 3 — measurement health (all FLAG: the run continues, labelled)
# ---------------------------------------------------------------------------


def _audited(sections: list[dict[str, Any]]) -> int:
    return sum(int(s.get("n_pe_events_audited", 0)) for s in sections)


def _lived(sections: list[dict[str, Any]]) -> int:
    """Events the lives in these sections actually got through (D-073).

    Gen1 sections hold two phases and their PE audit merges both, so both are
    summed; a gen2 section holds one life. A section written before D-073 has
    neither key and contributes zero, which the caller sees as an unmeasurable
    denominator rather than as a pass.
    """

    return sum(
        int(section.get("events_lived", 0))
        + int(section.get("events_lived_phase1", 0))
        + int(section.get("events_lived_phase2", 0))
        for section in sections
    )


def check_pe_event_sufficiency(
    sections: list[dict[str, Any]],
    *,
    min_fraction: float,
) -> tuple[bool, str]:
    """I3.1 — enough PE events actually reached the log.

    Instrument starvation: the PE log should hold a row for every event the
    agent lived, so a shortfall means the sensor stopped, not that the agent
    did.

    D-073 changed the denominator from the event BUDGET to events LIVED.
    Against the budget this check could not tell a broken sensor from a short
    life, and since D-066 short lives are the norm — so it would have reported
    the universe working as designed as an instrument fault. 12 rows from a
    12-event life is healthy; 12 rows from a 50-event life is not, and only
    the lived count separates them.
    """

    if not sections:
        return False, "no sections to audit"
    lived = _lived(sections)
    if lived <= 0:
        return False, "no lived events recorded — sufficiency cannot be assessed"
    actual = _audited(sections)
    fraction = float(actual) / float(lived)
    if fraction < min_fraction:
        return False, f"{actual}/{lived} PE events ({fraction:.2f} < {min_fraction})"
    return True, f"{actual}/{lived} PE events ({fraction:.2f})"


def check_precision_saturation(
    audit: dict[str, Any],
    *,
    max_rate: float,
    min_distinct: int,
) -> tuple[bool, str]:
    """I3.2 — the precision sensor still discriminates.

    A saturated sensor reads "no difference between arms" exactly like a real
    null, so this is what keeps a dead instrument from looking like a result.
    """

    n_events = int(audit.get("n_pe_events_audited", 0))
    if n_events <= 0:
        return False, "no PE events audited — saturation cannot be assessed"
    rate = float(audit.get("saturation_rate", 0.0))
    distinct = int(audit.get("pi_n_distinct", 0))
    problems: list[str] = []
    if rate > max_rate:
        problems.append(f"saturation_rate={rate:.4f} > {max_rate}")
    if distinct < min_distinct:
        problems.append(f"pi_n_distinct={distinct} < {min_distinct}")
    if problems:
        return False, "; ".join(problems)
    return True, f"saturation_rate={rate:.4f} pi_n_distinct={distinct}"


def check_gated_fraction(
    sections: list[dict[str, Any]],
    *,
    max_fraction: float,
) -> tuple[bool, str]:
    """I3.3 — too many gated arms means n_eff < N and the run is thin."""

    if not sections:
        return False, "no sections to audit"
    n_gated = sum(1 for s in sections if bool(s.get("gated", False)))
    fraction = float(n_gated) / float(len(sections))
    if fraction > max_fraction:
        return False, f"{n_gated}/{len(sections)} gated ({fraction:.2f} > {max_fraction})"
    return True, f"{n_gated}/{len(sections)} gated ({fraction:.2f})"


def check_early_termination_fraction(
    sections: list[dict[str, Any]],
    *,
    expected_per_section: int,
    max_fraction: float,
) -> tuple[bool, str]:
    """I3.4 — how much of the event budget the cohort never got through.

    D-073 renamed this from "pad fraction" and moved it to MODE_REPORT. The
    arithmetic is unchanged, and it never touched _pad_pe_list in the first
    place: it has always been budget minus the rows that reached the log.

    What changed is what that number means. It used to say "this much of the
    endpoint is LOCF output", which was an instrument fault worth flagging.
    LOCF is gone, and with the endpoints read at a fixed age a short life is
    still fully measurable — so the same number is now a finding about the
    universe: how many lineages the metabolic cost killed before the budget
    ran out. D-070/K7 already decided such collapse is reported, not
    intervened on, and MAX is 0.0, so leaving it a flag would stamp every run
    from here on and leave run_quality meaning nothing.

    Still measured, and deliberately so: the fraction is a candidate validity
    criterion for the second pre-registration, and dropping the measurement
    would make recovering it cost a new run.
    """

    if not sections:
        return False, "no sections to audit"
    expected = expected_per_section * len(sections)
    unreached = max(0, expected - _audited(sections))
    fraction = float(unreached) / float(expected) if expected else 0.0
    if fraction > max_fraction:
        return (
            False,
            f"{unreached}/{expected} events not reached ({fraction:.2f} > "
            f"{max_fraction})",
        )
    return True, f"{unreached}/{expected} events not reached ({fraction:.2f})"


def check_nli_active() -> tuple[bool, str]:
    """I5.2 — the polarity filter was actually consulted.

    The gate returns True when disabled, so a silent no-op looks exactly like
    a clean pass from the caller's side. D-032 swapped the instrument from NLI
    contradiction to cosine distance; the invariant is unchanged, so the
    message names whichever gate resolved rather than assuming NLI.
    """

    from dau.foundation.lora_update import POLARITY_FILTER_STATS
    from dau.foundation.polarity_filter import describe_polarity_filter

    active = describe_polarity_filter()["polarity_filter"]
    total = int(POLARITY_FILTER_STATS.get("total_candidates", 0))
    if total <= 0:
        return False, (
            f"POLARITY_FILTER_STATS.total_candidates == 0 — "
            f"{active} filter never ran"
        )
    return True, (
        f"filter={active} total_candidates={total} "
        f"rejected={int(POLARITY_FILTER_STATS.get('rejected', 0))}"
    )


def _both_generations(
    check: Callable[..., tuple[bool, str]],
    gen1: list[dict[str, Any]],
    gen2: list[dict[str, Any]],
    expected_gen1: int,
    expected_gen2: int,
    **kwargs: Any,
) -> tuple[bool, str]:
    """Apply a per-section check to gen1 and gen2, which have different Ns.

    Both must pass. Reported together so a healthy gen1 cannot hide a starved
    gen2 — the generation where the inheritance claim is actually read.
    """

    gen1_passed, gen1_detail = check(
        gen1, expected_per_section=expected_gen1, **kwargs
    )
    gen2_passed, gen2_detail = check(
        gen2, expected_per_section=expected_gen2, **kwargs
    )
    return (
        bool(gen1_passed and gen2_passed),
        f"gen1: {gen1_detail} | gen2: {gen2_detail}",
    )


def _both_generations_self_scaled(
    check: Callable[..., tuple[bool, str]],
    gen1: list[dict[str, Any]],
    gen2: list[dict[str, Any]],
    **kwargs: Any,
) -> tuple[bool, str]:
    """Same combine, for a check that carries its own denominator (D-073).

    I3.1 divides by events lived, which is in the sections themselves, so it
    takes no per-section budget. Kept separate rather than making the budget
    optional: an ignored argument is how a check ends up silently measuring
    something other than what its caller thinks.
    """

    gen1_passed, gen1_detail = check(gen1, **kwargs)
    gen2_passed, gen2_detail = check(gen2, **kwargs)
    return (
        bool(gen1_passed and gen2_passed),
        f"gen1: {gen1_detail} | gen2: {gen2_detail}",
    )


# ---------------------------------------------------------------------------
# Phase 4 — determinism evidence · Phase 5 — component liveness
# ---------------------------------------------------------------------------


def rng_state_digest() -> str:
    """Fingerprint of every RNG _lock_seeds pins (torch optional)."""

    import hashlib
    import random

    import numpy as np

    digest = hashlib.sha256()
    digest.update(repr(random.getstate()).encode("utf-8"))
    digest.update(repr(np.random.get_state()).encode("utf-8"))
    try:
        import torch
    except ImportError:
        pass
    else:
        digest.update(torch.random.get_rng_state().numpy().tobytes())
    return digest.hexdigest()


def check_gen2_rng_uniform(gen2_sections: list[dict[str, Any]]) -> tuple[bool, str]:
    """I4.2 — every heir of a seed enters gen2 from the same RNG state.

    lived/shuffle run DPO before gen2 and consume torch RNG; null does not.
    Unlocked, the arm contrast would carry an RNG contrast inside it (GAP-12).
    """

    if not gen2_sections:
        return False, "no gen2 sections to compare"
    by_seed: dict[Any, dict[str, str]] = {}
    for section in gen2_sections:
        digest = str(section.get("rng_digest", ""))
        if not digest:
            return False, f"seed={section.get('seed')} has no rng_digest recorded"
        by_seed.setdefault(section.get("seed"), {})[
            str(section.get("gen1_arm"))
        ] = digest
    for seed, digests in by_seed.items():
        if len(set(digests.values())) > 1:
            return False, f"seed={seed} entered gen2 from {len(set(digests.values()))} RNG states"
    return True, f"{len(by_seed)} seeds, one RNG state per seed"


def arm_digest(decisions: list[str], pe_values: list[float]) -> str:
    """sha256(decision sequence ++ PE sequence) for one arm.

    Final agent state is deliberately excluded (D-012): it is a function of
    decisions and PE, so it adds no information while contributing float
    noise that would produce false separations. Decisions alone are not
    enough either — identical decisions can carry different PE, and that is
    a real divergence.
    """

    import hashlib

    digest = hashlib.sha256()
    for decision in decisions:
        digest.update(str(decision).encode("utf-8"))
        digest.update(b"\x00")
    for value in pe_values:
        digest.update(f"{float(value):.12g}".encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()


def check_arms_differ(gen1_sections: list[dict[str, Any]]) -> tuple[bool, str]:
    """I2.1 — no two arms of a seed are byte-identical.

    The most valuable invariant on the list: it removes the ambiguity of
    "null ΔPE = 0.000 clean", which reads the same whether the tool is
    deterministic or no arm was ever trained (GAP-1).
    """

    if not gen1_sections:
        return False, "no arms to compare"
    by_seed: dict[Any, dict[str, str]] = {}
    for section in gen1_sections:
        digest = str(section.get("arm_digest", ""))
        if not digest:
            return False, f"seed={section.get('seed')} arm has no digest recorded"
        by_seed.setdefault(section.get("seed"), {})[str(section.get("arm"))] = digest
    for seed, digests in by_seed.items():
        if len(set(digests.values())) < len(digests):
            collisions = [
                arm
                for arm, value in digests.items()
                if list(digests.values()).count(value) > 1
            ]
            return False, f"seed={seed}: identical arms {sorted(collisions)}"
    return True, f"{len(by_seed)} seeds, all arms distinct"


def check_training_moved_weights(
    gen1_sections: list[dict[str, Any]],
    *,
    lora_enabled: bool = True,
) -> tuple[bool | None, str]:
    """I1.1 — a train arm's lora_B actually moved; a null arm's was never read.

    Every other signal a trained arm emits is produced upstream of the gradient
    step: the pair counts come from the polarity filter, the adapter file is
    written unconditionally after the loop, and dpo_loss is whatever the last
    forward pass returned. The pre-e4c026b bug rode through all of them —
    lora_B stayed at its zero init and nothing in the run said so. This reads
    the weights themselves, which is the only place that bug was visible.

    A diversity-gated arm skipped training on purpose, so it is exempt: it is
    identified by gated=True, not by its counts, because a gated arm and a
    silently-failed one both report zero pairs. A whole run with LoRA off is
    exempt the same way, via lora_enabled — otherwise this gate would abort
    the deliberate --no-lora arm of the design.
    """

    from dau.diagnostics.tool_identity import ARM_NULL_NAME

    if not lora_enabled:
        # --no-lora is a deliberate run mode, recorded in the results JSON.
        # There is no train step to verify, so this reports not-applicable
        # rather than failing — and never True, which would read as proof
        # that training happened.
        return None, "LoRA off by choice — no train step to verify"
    if not gen1_sections:
        return False, "no arms to check"

    unmoved: list[str] = []
    unread: list[str] = []
    contaminated: list[str] = []
    checked = 0
    for section in gen1_sections:
        arm = str(section.get("arm"))
        label = f"seed={section.get('seed')}/{arm}"
        delta = section.get("lora_b_abs_sum_delta")
        delta = float("nan") if delta is None else float(delta)

        if arm == ARM_NULL_NAME:
            # Not "must be zero" — null never calls train, so a real reading
            # here means something trained on the control's weights.
            if delta == delta:  # NaN is the only value that fails this
                contaminated.append(f"{label} delta={delta:.6g}")
            continue
        if bool(section.get("gated", False)):
            continue

        checked += 1
        if delta != delta:
            unread.append(label)
        elif delta <= 0.0:
            unmoved.append(f"{label} delta={delta:.6g}")

    if contaminated:
        return False, f"null arm reports a train-step weight read: {contaminated}"
    if unread:
        return False, (
            f"{len(unread)} train arm(s) never had lora_B read: {unread} — "
            f"the run cannot show training happened"
        )
    if unmoved:
        return False, f"train arm(s) whose lora_B did not move: {unmoved}"
    if not checked:
        return False, "no ungated train arm to check"
    return True, f"{checked} train arms moved lora_B; null arms unread"


def check_gradient_step_taken(
    gen1_sections: list[dict[str, Any]],
    *,
    lora_enabled: bool = True,
) -> tuple[bool | None, str]:
    """I1.3 — the optimizer ran, on a finite loss, with a gradient behind it.

    I1.1 already proves a step landed, so this deliberately does not re-ask
    that. It covers the three ways a step can land and still be worthless,
    none of which move Σ|lora_B| in a way I1.1 could tell apart from a healthy
    run: a non-finite loss (the weights change, into NaN), a loop that
    accumulates gradient but never calls optimizer.step (the run then trains on
    whatever the previous group left), and an optimizer step taken on an
    exactly-zero gradient.

    Clipping is NOT failed here — see check_gradient_clipping. A clipped step
    is a real step; the question it raises is about effective step size, which
    is a labelling matter, not an abort.
    """

    from dau.diagnostics.tool_identity import ARM_NULL_NAME

    if not lora_enabled:
        return None, "LoRA off by choice — no train step to verify"
    if not gen1_sections:
        return False, "no arms to check"

    problems: list[str] = []
    checked = 0
    for section in gen1_sections:
        arm = str(section.get("arm"))
        if arm == ARM_NULL_NAME or bool(section.get("gated", False)):
            continue
        checked += 1
        label = f"seed={section.get('seed')}/{arm}"

        loss = section.get("dpo_loss")
        loss = float("nan") if loss is None else float(loss)
        steps = int(section.get("dpo_optimizer_steps", 0) or 0)
        norm_min = section.get("dpo_grad_norm_min")
        norm_min = float("nan") if norm_min is None else float(norm_min)

        if steps <= 0:
            problems.append(f"{label} optimizer never stepped")
            continue
        if loss != loss or loss in (float("inf"), float("-inf")):
            problems.append(f"{label} dpo_loss={loss}")
        # NaN here means the field was never written by the train path, which
        # is a reporting failure, not a healthy run — same rule as I1.1.
        if norm_min != norm_min:
            problems.append(f"{label} grad norm never read")
        elif norm_min <= 0.0:
            problems.append(f"{label} stepped on a zero gradient")

    if problems:
        return False, f"train step not verifiable: {problems}"
    if not checked:
        return False, "no ungated train arm to check"
    return True, f"{checked} train arms stepped on a finite loss and real gradient"


def check_gradient_clipping(
    gen1_sections: list[dict[str, Any]],
    *,
    lora_enabled: bool = True,
) -> tuple[bool | None, str]:
    """I1.3b — how much of the training ran against DPO_MAX_GRAD_NORM.

    Not a correctness check. D-029 chose DPO_LEARNING_RATE from the literature
    to avoid the unlikelihood push that lr=5e-5 produced, and that choice only
    means what it says while the gradient is what sets the step size. If every
    step is clipped, the ceiling sets it instead and the locked learning rate
    describes the run less than the clip does.

    FLAG, and the threshold is the strictest honest reading rather than a
    guessed one: any clipping at all earns the label, like PAD_FRACTION_MAX.
    Calibrating it into an ABORT needs a pilot, which is why it is not one.
    """

    from dau.diagnostics.tool_identity import ARM_NULL_NAME

    if not lora_enabled:
        return None, "LoRA off by choice — no train step to verify"

    clipped_total = 0
    step_total = 0
    per_arm: list[str] = []
    for section in gen1_sections:
        arm = str(section.get("arm"))
        if arm == ARM_NULL_NAME or bool(section.get("gated", False)):
            continue
        steps = int(section.get("dpo_optimizer_steps", 0) or 0)
        clipped = int(section.get("dpo_clipped_steps", 0) or 0)
        step_total += steps
        clipped_total += clipped
        if clipped:
            per_arm.append(f"seed={section.get('seed')}/{arm} {clipped}/{steps}")

    if step_total == 0:
        return None, "no optimizer steps to judge"
    fraction = clipped_total / step_total
    if clipped_total:
        return False, (
            f"{clipped_total}/{step_total} optimizer steps ({fraction:.1%}) hit "
            f"the grad-norm ceiling: {per_arm} — effective step size is set by "
            f"the clip, not only by DPO_LEARNING_RATE"
        )
    return True, f"no step of {step_total} was clipped"


def check_pairs_survived_filter(
    pair_filter: dict[str, Any] | None,
) -> tuple[bool | None, str]:
    """I1.4 — the surviving pairs are not the last scraps of a starving filter.

    ⚠ This is NOT what docs/PREFLIGHT_INVARIANTS.md originally specified. That
    text asks for "the share of pairs with PE >= SNR_FLOOR", written when the
    floor was applied after pair construction. D-030 moved the margin test into
    build_pe_ranked_pairs, so every pair that reaches training already clears
    it by construction and the specified ratio is 1.0 in all cases — a gate
    that cannot fail. The measurable question that survives D-030 is the one
    below: how much of the candidate pool the filter had to throw away.

    FLAG only, and no threshold is invented. The rejection rate is recorded
    and it fails only in the degenerate case where nothing survived, which is
    the one reading that needs no calibration to interpret.
    """

    if not pair_filter or not pair_filter.get("available", False):
        return None, "pair filter did not report — nothing to judge"

    candidates = int(pair_filter.get("snr_candidates", 0) or 0)
    rejected = int(pair_filter.get("snr_rejected_below_margin", 0) or 0)
    passed = int(pair_filter.get("pairs_passed", 0) or 0)
    if candidates == 0:
        return False, "filter saw no candidate pairs at all"

    rate = rejected / candidates
    if passed == 0:
        return False, (
            f"every candidate was filtered out ({rejected}/{candidates} below "
            f"the margin) — training had nothing to learn from"
        )
    return True, (
        f"{rejected}/{candidates} candidates ({rate:.1%}) below the margin, "
        f"{passed} pairs survived"
    )


def check_pair_count_sufficient(
    gen1_sections: list[dict[str, Any]],
) -> tuple[bool | None, str]:
    """I1.5 — each train arm had at least one full accumulation group.

    MIN_PAIRS is DPO_BATCH_SIZE * DPO_GRADIENT_ACCUMULATION_STEPS, derived
    from the configuration rather than from any pair count we have observed:
    choosing it from our own runs would be the post-hoc tuning §2.7 forbids.
    Below it the arm still trains, but the optimizer only ever sees a short
    tail group, so the effective batch is not the one tool identity reports.

    FLAG: this is a structural floor, not a calibrated sufficiency level.
    MIN_PAIRS_CALIBRATED stays False and is reported alongside it, so the
    number cannot read as more settled than it is (§2.8).
    """

    from dau.foundation.constraints import MIN_PAIRS
    from dau.diagnostics.tool_identity import ARM_NULL_NAME

    short: list[str] = []
    checked = 0
    for section in gen1_sections:
        arm = str(section.get("arm"))
        if arm == ARM_NULL_NAME or bool(section.get("gated", False)):
            continue
        checked += 1
        n_pairs = int(section.get("n_pairs_trained", 0) or 0)
        if n_pairs < MIN_PAIRS:
            short.append(f"seed={section.get('seed')}/{arm} n_pairs={n_pairs}")

    if not checked:
        return None, "no ungated train arm to check"
    if short:
        return False, (
            f"{len(short)} arm(s) under MIN_PAIRS={MIN_PAIRS} "
            f"(uncalibrated structural floor): {short}"
        )
    return True, f"{checked} train arms at or above MIN_PAIRS={MIN_PAIRS}"


def check_null_untrained(gen1_sections: list[dict[str, Any]]) -> tuple[bool, str]:
    """I2.2 — the null arm has no adapter of its own.

    A null that trained is not a control, and the arm contrast built on it
    means nothing (the pre-f25b0ef leak did exactly this).
    """

    from dau.diagnostics.tool_identity import ARM_NULL_NAME

    nulls = [s for s in gen1_sections if str(s.get("arm")) == ARM_NULL_NAME]
    if not nulls:
        return False, "no null arm found"
    trained = [s for s in nulls if int(s.get("n_pairs_trained", 0)) > 0]
    if trained:
        return False, f"{len(trained)} null arms report trained pairs"
    contaminated = [s for s in nulls if bool(s.get("adapter_present", False))]
    if contaminated:
        return False, (
            f"{len(contaminated)} null arms have an adapter on disk — "
            f"stale state from an earlier run counts as contamination"
        )
    return True, f"{len(nulls)} null arms untrained, no adapter on disk"


def run_phase2(
    preflight: Preflight,
    *,
    gen1_sections: list[dict[str, Any]],
    lora_enabled: bool = True,
    pair_filter: dict[str, Any] | None = None,
) -> Preflight:
    """Record I1.1, I1.3, I1.3b, I1.4, I1.5, I2.1 and I2.2.

    Mock exception (D-012): under a canned LLM the arms are identical by
    design, so I2.1 drops to FLAG rather than aborting a smoke run.
    """

    preflight.check(
        "I1.1",
        lambda: check_training_moved_weights(
            gen1_sections, lora_enabled=lora_enabled
        ),
        # A mocked LLM has no LoRA layers to read, so the delta is unread by
        # construction and aborting would only punish smoke runs (D-012).
        mode=MODE_FLAG if preflight.mock else MODE_ABORT,
    )
    preflight.check(
        "I1.3",
        lambda: check_gradient_step_taken(gen1_sections, lora_enabled=lora_enabled),
        # Same mock reasoning as I1.1: a canned LLM runs no optimizer.
        mode=MODE_FLAG if preflight.mock else MODE_ABORT,
    )
    preflight.check(
        "I1.3b",
        lambda: check_gradient_clipping(gen1_sections, lora_enabled=lora_enabled),
        mode=MODE_FLAG,
    )
    preflight.check(
        "I1.4",
        lambda: check_pairs_survived_filter(pair_filter),
        mode=MODE_FLAG,
    )
    preflight.check(
        "I1.5",
        lambda: check_pair_count_sufficient(gen1_sections),
        mode=MODE_FLAG,
    )
    preflight.check(
        "I2.1",
        lambda: check_arms_differ(gen1_sections),
        mode=MODE_FLAG if preflight.mock else MODE_ABORT,
    )
    preflight.check(
        "I2.2",
        lambda: check_null_untrained(gen1_sections),
        mode=MODE_ABORT,
    )
    return preflight


def check_ppr_active(life_stats: list[dict[str, Any]]) -> tuple[bool, str]:
    """I5.1 — the association graph has edges at all.

    compute_ppr_scores returns {seed_domain: 1.0} on an empty graph without
    complaining, so PPR reads as a working component while contributing a
    constant (GAP-14).
    """

    if not life_stats:
        return False, "no lives sampled"
    total = sum(int(s.get("memory_edges", 0)) for s in life_stats if
                int(s.get("memory_edges", -1)) >= 0)
    unreadable = sum(1 for s in life_stats if int(s.get("memory_edges", -1)) < 0)
    if unreadable:
        return False, f"{unreadable} lives had an unreadable store"
    if total <= 0:
        return False, "memory_edges is empty in every life — PPR is inert"
    return True, f"{total} edges across {len(life_stats)} lives"


def check_memory_written(life_stats: list[dict[str, Any]]) -> tuple[bool, str]:
    """I5.3 — each life actually wrote to its vault."""

    if not life_stats:
        return False, "no lives sampled"
    empty = [s["agent_id"] for s in life_stats if int(s.get("memory_written", 0)) <= 0]
    if empty:
        return False, f"{len(empty)} lives wrote nothing, e.g. {empty[0]}"
    total = sum(int(s.get("memory_written", 0)) for s in life_stats)
    return True, f"{total} writes across {len(life_stats)} lives"


def check_somatic_scale_applied() -> tuple[bool, str]:
    """I5.4 — an inherited somatic scale was applied at least once.

    The function returns its input unchanged when nothing was inherited, so
    a lineage that never applied one is indistinguishable from scaling that
    silently never fired (GAP-3).
    """

    from dau.foundation.emotional_weight import SOMATIC_SCALE_STATS

    applied = int(SOMATIC_SCALE_STATS.get("applied", 0))
    if applied <= 0:
        return False, (
            f"never applied (skipped={int(SOMATIC_SCALE_STATS.get('skipped', 0))})"
        )
    return True, f"applied {applied}x"


def check_replay_identical(replay: dict[str, Any] | None) -> tuple[bool | None, str]:
    """I4.1 — one arm re-run in-process lands on the same digest.

    This is the only invariant that costs wall time, and it earned it: under
    TORCH_DETERMINISTIC_WARN_ONLY the same seed and code produced different
    adapters and a 21/50 phase-2 decision split between two runs, while every
    other gate stayed green (D-037). Nothing in a single pass can see that —
    each arm trains once, so there is nothing to compare it against.

    Why the digest and not a file diff: the results JSON also carries per-run
    memory UUIDs, which differ by construction. Comparing whole payloads would
    fail on a deterministic run (D-038).

    Deliberately replays a TRAINED arm. The null arm was already deterministic
    under warn_only — it runs no adapter matmul — so replaying it would have
    passed straight through the failure this exists to catch.
    """

    if replay is None:
        return None, "replay not run"
    recorded = str(replay.get("recorded_digest", ""))
    replayed = str(replay.get("replay_digest", ""))
    label = f"seed={replay.get('seed')}/{replay.get('arm')}"
    if not recorded or not replayed:
        return False, f"{label}: a digest is missing, replay proves nothing"
    if recorded != replayed:
        return False, (
            f"{label}: replay diverged — {recorded[:12]} vs {replayed[:12]}. "
            f"Same seed, same code, different run: the arm contrast is noise"
        )
    return True, f"{label}: replay bit-identical ({recorded[:12]})"


def run_phase4_5(
    preflight: Preflight,
    *,
    gen2_sections: list[dict[str, Any]],
    life_stats: list[dict[str, Any]],
    replay: dict[str, Any] | None = None,
) -> Preflight:
    """Record I4.1 / I4.2 (ABORT) and I5.1 / I5.3 / I5.4 (FLAG)."""

    preflight.check(
        "I4.1",
        lambda: check_replay_identical(replay),
        # A canned LLM replays trivially, so the check would assert nothing.
        mode=MODE_FLAG if preflight.mock else MODE_ABORT,
    )
    preflight.check(
        "I4.2",
        lambda: check_gen2_rng_uniform(gen2_sections),
        mode=MODE_ABORT,
    )
    # I5.1 stays FLAG until the GAP-14 decision: whether PPR should be wired
    # into the run path or documented as inert is not the gate's call.
    preflight.check("I5.1", lambda: check_ppr_active(life_stats), mode=MODE_FLAG)
    preflight.check("I5.3", lambda: check_memory_written(life_stats), mode=MODE_FLAG)
    preflight.check("I5.4", check_somatic_scale_applied, mode=MODE_FLAG)
    return preflight


def _both_audits(
    gen1_audit: dict[str, Any],
    gen2_audit: dict[str, Any],
) -> tuple[bool, str]:
    gen1_passed, gen1_detail = check_precision_saturation(
        gen1_audit, max_rate=SATURATION_MAX, min_distinct=PI_N_DISTINCT_MIN
    )
    gen2_passed, gen2_detail = check_precision_saturation(
        gen2_audit, max_rate=SATURATION_MAX, min_distinct=PI_N_DISTINCT_MIN
    )
    return (
        bool(gen1_passed and gen2_passed),
        f"gen1: {gen1_detail} | gen2: {gen2_detail}",
    )


def run_phase3(
    preflight: Preflight,
    *,
    gen1_sections: list[dict[str, Any]],
    gen2_sections: list[dict[str, Any]],
    expected_gen1: int,
    expected_gen2: int,
    gen1_audit: dict[str, Any],
    gen2_audit: dict[str, Any],
) -> Preflight:
    """Record I3.1–I3.4 and I5.2. The run continues either way — I3.1/I3.2/
    I3.3 and I5.2 label it, I3.4 only reports (D-073)."""

    from dau.diagnostics.run_protocol_c_prime import MIN_TRACE_FRACTION

    preflight.check(
        "I3.1",
        lambda: _both_generations_self_scaled(
            check_pe_event_sufficiency,
            gen1_sections,
            gen2_sections,
            min_fraction=MIN_TRACE_FRACTION,
        ),
        mode=MODE_FLAG,
    )
    preflight.check(
        "I3.2",
        lambda: _both_audits(gen1_audit, gen2_audit),
        mode=MODE_FLAG,
        calibrated=False,
    )
    preflight.check(
        "I3.3",
        lambda: check_gated_fraction(
            gen1_sections + gen2_sections,
            max_fraction=GATED_FRACTION_MAX,
        ),
        mode=MODE_FLAG,
        calibrated=False,
    )
    preflight.check(
        "I3.4",
        lambda: _both_generations(
            check_early_termination_fraction,
            gen1_sections,
            gen2_sections,
            expected_gen1,
            expected_gen2,
            max_fraction=PAD_FRACTION_MAX,
        ),
        mode=MODE_REPORT,
        calibrated=False,
    )
    preflight.check("I5.2", check_nli_active, mode=MODE_FLAG)
    return preflight


# ---------------------------------------------------------------------------
# Phase 0 — before the run starts, before any GPU work
# ---------------------------------------------------------------------------


def check_no_stale_adapters(agent_ids: list[str]) -> tuple[bool | None, str]:
    """I0.7 — no agent starts its life on a previous run's trained adapter.

    graph.agent_node calls switch_adapter on every local-backend decision, and
    switch_adapter loads from disk whenever adapter_exists(agent_id) — which
    only asks whether adapter_config.json is there. Adapter directories are
    keyed by agent_id alone, so re-running the same seeds re-uses them:
    phase 1 then begins on weights an earlier run trained.

    Measured 2026-08-10: dau_runs/adapters held 35 populated directories, some
    from 08-07, including cprime-lived-2003-g1 from the 08-09 pilot. In that
    day's smoke the arms' phase-1 lives diverged (n_unique 6/7/6, 8 vs 6
    pairs) because lived and shuffle loaded 08-09 weights while null — which
    never trains, so its directory was empty — started from the base policy.

    The bias has a direction: LIVED accumulates training across runs and NULL
    never does, so the leak favours the hypothesis. This is the across-run twin
    of the within-run leak closed in f25b0ef.

    ABORT rather than delete: removing a previous run's artefacts is the
    operator's call, not the gate's.

    Not applicable off the local backend — switch_adapter's disk path is
    local-only, and None is deliberately distinct from True here.
    """

    from dau.diagnostics.tool_identity import BACKEND_LOCAL, resolve_backend

    if resolve_backend() != BACKEND_LOCAL:
        return None, f"backend is not {BACKEND_LOCAL} — adapters are never loaded"

    from dau.foundation.constraints import ADAPTER_BASE_DIR
    from dau.foundation.local_llm import adapter_exists

    stale = [agent_id for agent_id in agent_ids if adapter_exists(agent_id)]
    if stale:
        shown = ", ".join(stale[:5])
        more = f" (+{len(stale) - 5} more)" if len(stale) > 5 else ""
        return False, (
            f"{len(stale)}/{len(agent_ids)} agent(s) already have a saved "
            f"adapter: {shown}{more} — delete them under "
            f"{ADAPTER_BASE_DIR}/ or use fresh seeds; this run would start "
            f"phase 1 on a previous run's weights"
        )
    return True, f"{len(agent_ids)} agent(s) start from the base policy"


def run_phase0(
    preflight: Preflight,
    *,
    tool_identity: dict[str, Any],
    agent_ids: list[str],
    seeds: list[int],
    import_time_bindings: list[tuple[str, Any, str, Callable[[str], Any]]],
) -> Preflight:
    """Record I0.1–I0.6. Caller decides when to enforce()."""

    preflight.check(
        "I0.1",
        lambda: check_tool_identity(tool_identity),
        mode=MODE_ABORT,
    )
    preflight.check(
        "I0.2",
        lambda: check_lora_choice(tool_identity),
        mode=MODE_ABORT,
    )
    preflight.check("I0.3", check_pythonhashseed, mode=MODE_ABORT)
    preflight.check(
        "I0.4",
        lambda: check_seed_derivation(agent_ids, seeds),
        mode=MODE_ABORT,
    )
    preflight.check(
        "I0.5",
        lambda: check_import_time_env(import_time_bindings),
        mode=MODE_ABORT,
    )
    preflight.check("I0.6", check_determinism_settings, mode=MODE_ABORT)
    preflight.check(
        "I0.7",
        lambda: check_no_stale_adapters(agent_ids),
        mode=MODE_ABORT,
    )
    return preflight
