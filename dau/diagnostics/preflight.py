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
# Padding is fabricated data, so any of it earns a label. Not a guessed
# threshold — the strictest honest reading, and FLAG only.
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
        predicate: Callable[[], tuple[bool, str]],
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


def check_seed_derivation(agent_ids: list[str], seeds: list[int]) -> tuple[bool, str]:
    """I0.4 — every planned agent_id yields the seed it is supposed to."""

    from dau.diagnostics.run_protocol_c_prime import _seed_from_agent_id

    if not agent_ids:
        return False, "no agent_ids to verify"
    expected = set(seeds)
    for agent_id in agent_ids:
        derived = _seed_from_agent_id(agent_id)
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
    if problems:
        return False, "; ".join(problems)
    warn_only = bool(torch.is_deterministic_algorithms_warn_only_enabled())
    return True, f"deterministic algorithms on (warn_only={warn_only})"


# ---------------------------------------------------------------------------
# Phase 3 — measurement health (all FLAG: the run continues, labelled)
# ---------------------------------------------------------------------------


def _audited(sections: list[dict[str, Any]]) -> int:
    return sum(int(s.get("n_pe_events_audited", 0)) for s in sections)


def check_pe_event_sufficiency(
    sections: list[dict[str, Any]],
    *,
    expected_per_section: int,
    min_fraction: float,
) -> tuple[bool, str]:
    """I3.1 — enough PE events actually reached the log.

    A stream that stops early leaves a mean dominated by padding rather than
    by measurement (instrument starvation, v1 smoke).
    """

    if not sections:
        return False, "no sections to audit"
    expected = expected_per_section * len(sections)
    actual = _audited(sections)
    fraction = float(actual) / float(expected) if expected else 0.0
    if fraction < min_fraction:
        return False, f"{actual}/{expected} PE events ({fraction:.2f} < {min_fraction})"
    return True, f"{actual}/{expected} PE events ({fraction:.2f})"


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


def check_pad_fraction(
    sections: list[dict[str, Any]],
    *,
    expected_per_section: int,
    max_fraction: float,
) -> tuple[bool, str]:
    """I3.4 — how much of the PE trace was padding rather than measurement.

    Derived from the audit counts rather than from _pad_pe_list: the padded
    values are indistinguishable from real ones once in the list, but the
    number of rows that reached the log is not.
    """

    if not sections:
        return False, "no sections to audit"
    expected = expected_per_section * len(sections)
    padded = max(0, expected - _audited(sections))
    fraction = float(padded) / float(expected) if expected else 0.0
    if fraction > max_fraction:
        return False, f"{padded}/{expected} padded ({fraction:.2f} > {max_fraction})"
    return True, f"{padded}/{expected} padded ({fraction:.2f})"


def check_nli_active() -> tuple[bool, str]:
    """I5.2 — the NLI filter was actually consulted.

    nli_filter returns True when disabled, so a silent no-op looks exactly
    like a clean pass from the caller's side.
    """

    from dau.foundation.lora_update import NLI_FILTER_STATS

    total = int(NLI_FILTER_STATS.get("total_candidates", 0))
    if total <= 0:
        return False, "NLI_FILTER_STATS.total_candidates == 0 — filter never ran"
    return True, (
        f"total_candidates={total} "
        f"rejected={int(NLI_FILTER_STATS.get('rejected', 0))}"
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


def run_phase4_5(
    preflight: Preflight,
    *,
    gen2_sections: list[dict[str, Any]],
    life_stats: list[dict[str, Any]],
) -> Preflight:
    """Record I4.2 (ABORT) and I5.1 / I5.3 / I5.4 (FLAG)."""

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
    """Record I3.1–I3.4 and I5.2. All FLAG — the run continues, labelled."""

    from dau.diagnostics.run_protocol_c_prime import MIN_TRACE_FRACTION

    preflight.check(
        "I3.1",
        lambda: _both_generations(
            check_pe_event_sufficiency,
            gen1_sections,
            gen2_sections,
            expected_gen1,
            expected_gen2,
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
            check_pad_fraction,
            gen1_sections,
            gen2_sections,
            expected_gen1,
            expected_gen2,
            max_fraction=PAD_FRACTION_MAX,
        ),
        mode=MODE_FLAG,
        calibrated=False,
    )
    preflight.check("I5.2", check_nli_active, mode=MODE_FLAG)
    return preflight


# ---------------------------------------------------------------------------
# Phase 0 — before the run starts, before any GPU work
# ---------------------------------------------------------------------------


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
    return preflight
