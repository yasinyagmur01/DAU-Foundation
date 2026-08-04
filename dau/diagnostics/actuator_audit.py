"""Monkey-patch Meta-Observer actuators and audit call/trigger counts.

Wraps lod_override, context_prune, trigger_drift_healing, and
trigger_retrieval without modifying meta_observer.py, then runs
foundation run_demo once and prints actuator statistics.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

from dau.foundation.lod import CognitiveMode
from dau.foundation import meta_observer as meta_observer_mod
from dau.foundation.meta_observer import (
    context_prune,
    lod_override,
    trigger_drift_healing,
    trigger_retrieval,
)

# ---------------------------------------------------------------------------
# Actuator audit counters (no magic numbers)
# ---------------------------------------------------------------------------

ACTUATOR_LOD_OVERRIDE: str = "lod_override"
ACTUATOR_CONTEXT_PRUNE: str = "context_prune"
ACTUATOR_DRIFT_HEALING: str = "trigger_drift_healing"
ACTUATOR_RETRIEVAL: str = "trigger_retrieval"

ACTUATOR_NAMES: tuple[str, ...] = (
    ACTUATOR_LOD_OVERRIDE,
    ACTUATOR_CONTEXT_PRUNE,
    ACTUATOR_DRIFT_HEALING,
    ACTUATOR_RETRIEVAL,
)

RUN_DEMO_MODULE: str = "dau.foundation.run_demo"
RUN_DEMO_ATTR: str = "run_demo"

# name -> {"called": int, "triggered": int}
_AUDIT: dict[str, dict[str, int]] = {
    name: {"called": 0, "triggered": 0} for name in ACTUATOR_NAMES
}


def _record(name: str, triggered: bool) -> None:
    """Increment call count; optionally increment trigger count."""

    _AUDIT[name]["called"] += 1
    if triggered:
        _AUDIT[name]["triggered"] += 1


def _drift_changed(before: Any, after: Any) -> bool:
    """True when drift flags or magnitudes differ between before and after."""

    return dict(before.flags) != dict(after.flags) or dict(before.magnitudes) != dict(
        after.magnitudes
    )


def _wrap_lod_override(original: Callable[..., Any]) -> Callable[..., Any]:
    """Count lod_override; triggered when returned mode is SYSTEM_2."""

    def wrapper(self_model: Any, lod_state: Any) -> Any:
        result = original(self_model, lod_state)
        triggered = result.mode == CognitiveMode.SYSTEM_2
        _record(ACTUATOR_LOD_OVERRIDE, triggered)
        return result

    return wrapper


def _wrap_context_prune(original: Callable[..., Any]) -> Callable[..., Any]:
    """Count context_prune; triggered when output list is shorter than input."""

    def wrapper(retrieval_context: list[dict[str, Any]], self_model: Any) -> Any:
        input_len = len(retrieval_context)
        result = original(retrieval_context, self_model)
        triggered = len(result) < input_len
        _record(ACTUATOR_CONTEXT_PRUNE, triggered)
        return result

    return wrapper


def _wrap_trigger_drift_healing(original: Callable[..., Any]) -> Callable[..., Any]:
    """Count trigger_drift_healing; triggered when drift_state content changes."""

    def wrapper(drift_state: Any, self_model: Any) -> Any:
        result = original(drift_state, self_model)
        triggered = _drift_changed(drift_state, result)
        _record(ACTUATOR_DRIFT_HEALING, triggered)
        return result

    return wrapper


def _wrap_trigger_retrieval(original: Callable[..., Any]) -> Callable[..., Any]:
    """Count trigger_retrieval; triggered when return list is non-empty."""

    def wrapper(state: Any, self_model: Any) -> Any:
        result = original(state, self_model)
        triggered = len(result) > 0
        _record(ACTUATOR_RETRIEVAL, triggered)
        return result

    return wrapper


def install_actuator_patches() -> None:
    """Replace the four actuators on the meta_observer module with wrappers."""

    meta_observer_mod.lod_override = _wrap_lod_override(lod_override)
    meta_observer_mod.context_prune = _wrap_context_prune(context_prune)
    meta_observer_mod.trigger_drift_healing = _wrap_trigger_drift_healing(
        trigger_drift_healing
    )
    meta_observer_mod.trigger_retrieval = _wrap_trigger_retrieval(trigger_retrieval)


def run_foundation_demo() -> None:
    """Import and execute run_demo exactly once."""

    demo_mod = importlib.import_module(RUN_DEMO_MODULE)
    getattr(demo_mod, RUN_DEMO_ATTR)()


def print_audit_report() -> None:
    """Print called/triggered counts for each actuator."""

    print("=== ACTUATOR AUDIT ===")
    print(
        f"{ACTUATOR_LOD_OVERRIDE:<20}: "
        f"called={_AUDIT[ACTUATOR_LOD_OVERRIDE]['called']}, "
        f"triggered={_AUDIT[ACTUATOR_LOD_OVERRIDE]['triggered']}"
    )
    print(
        f"{ACTUATOR_CONTEXT_PRUNE:<20}: "
        f"called={_AUDIT[ACTUATOR_CONTEXT_PRUNE]['called']}, "
        f"triggered={_AUDIT[ACTUATOR_CONTEXT_PRUNE]['triggered']}"
    )
    print(
        f"{ACTUATOR_DRIFT_HEALING}: "
        f"called={_AUDIT[ACTUATOR_DRIFT_HEALING]['called']}, "
        f"triggered={_AUDIT[ACTUATOR_DRIFT_HEALING]['triggered']}"
    )
    print(
        f"{ACTUATOR_RETRIEVAL:<20}: "
        f"called={_AUDIT[ACTUATOR_RETRIEVAL]['called']}, "
        f"triggered={_AUDIT[ACTUATOR_RETRIEVAL]['triggered']}"
    )


def main() -> int:
    """Patch actuators, run demo once, print audit summary."""

    install_actuator_patches()
    run_foundation_demo()
    print()
    print_audit_report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
