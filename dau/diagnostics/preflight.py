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
        if self.failures(MODE_ABORT):
            return RUN_QUALITY_ABORTED
        if self.mock:
            return RUN_QUALITY_MOCK
        if self.failures(MODE_FLAG):
            return RUN_QUALITY_FLAGGED
        return RUN_QUALITY_CLEAN

    def block(self) -> dict[str, Any]:
        return {
            "invariants": self.invariants(),
            "invariant_details": self.details(),
            "run_quality": self.run_quality(),
            "mock": self.mock,
        }


# ---------------------------------------------------------------------------
# Phase 0 — before the run starts, before any GPU work
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
