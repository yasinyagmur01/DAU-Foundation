"""Report prediction_error distribution from overnight audit results.

Reads dau_runs/overnight_audit_results.json, collects every non-None
prediction_error value (nested under run → events or any top-level key),
and prints bucket counts plus summary statistics.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths & PE bucket thresholds (no magic numbers)
# ---------------------------------------------------------------------------

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
AUDIT_RESULTS_PATH: Path = PROJECT_ROOT / "dau_runs" / "overnight_audit_results.json"

PREDICTION_ERROR_KEY: str = "prediction_error"
EVENTS_KEY: str = "events"

BUCKET_NOISE_MAX: float = 0.1
BUCKET_SOFT_MAX: float = 0.4
BUCKET_NORMAL_MAX: float = 0.7
BUCKET_DEEP_MAX: float = 1.0

BUCKET_NOISE: str = "NOISE"
BUCKET_SOFT: str = "SOFT"
BUCKET_NORMAL: str = "NORMAL"
BUCKET_DEEP: str = "DEEP"
BUCKET_TRAUMA: str = "TRAUMA"

BUCKET_ORDER: tuple[str, ...] = (
    BUCKET_NOISE,
    BUCKET_SOFT,
    BUCKET_NORMAL,
    BUCKET_DEEP,
    BUCKET_TRAUMA,
)

PERCENT_SCALE: float = 100.0
EMPTY_COUNT: int = 0


def _as_float(value: Any) -> float | None:
    """Coerce a JSON leaf to float; skip None and non-numeric values."""

    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _collect_prediction_errors(node: Any) -> list[float]:
    """Recursively gather prediction_error floats from any JSON subtree.

    Preferred shapes (all handled by the same walk):
    - run → events → [{prediction_error: ...}, ...]
    - top-level / nested objects with a prediction_error field
    """

    collected: list[float] = []

    if isinstance(node, dict):
        if PREDICTION_ERROR_KEY in node:
            pe = _as_float(node[PREDICTION_ERROR_KEY])
            if pe is not None:
                collected.append(pe)

        events = node.get(EVENTS_KEY)
        if isinstance(events, list):
            for event in events:
                collected.extend(_collect_prediction_errors(event))

        for key, child in node.items():
            if key in (PREDICTION_ERROR_KEY, EVENTS_KEY):
                continue
            collected.extend(_collect_prediction_errors(child))
        return collected

    if isinstance(node, list):
        for item in node:
            collected.extend(_collect_prediction_errors(item))
        return collected

    return collected


def _bucket_name(pe: float) -> str:
    """Map a prediction_error value onto the diagnostic histogram bucket."""

    if pe < BUCKET_NOISE_MAX:
        return BUCKET_NOISE
    if pe < BUCKET_SOFT_MAX:
        return BUCKET_SOFT
    if pe < BUCKET_NORMAL_MAX:
        return BUCKET_NORMAL
    if pe < BUCKET_DEEP_MAX:
        return BUCKET_DEEP
    return BUCKET_TRAUMA


def _count_buckets(values: list[float]) -> dict[str, int]:
    """Tally PE values into NOISE/SOFT/NORMAL/DEEP/TRAUMA buckets."""

    counts: dict[str, int] = {name: EMPTY_COUNT for name in BUCKET_ORDER}
    for pe in values:
        counts[_bucket_name(pe)] += 1
    return counts


def _format_pct(count: int, total: int) -> str:
    """Render a percentage with one decimal place; 0.0% when total is empty."""

    if total == EMPTY_COUNT:
        return "0.0%"
    return f"{(count / total) * PERCENT_SCALE:.1f}%"


def report_histogram(values: list[float]) -> None:
    """Print bucket distribution and mean/std/max for collected PE values."""

    total = len(values)
    counts = _count_buckets(values)

    print(f"Total PE values found: {total}")
    for name in BUCKET_ORDER:
        n = counts[name]
        print(f"{name:<8}: {n} ({_format_pct(n, total)})")

    if total == EMPTY_COUNT:
        print("Mean PE : n/a")
        print("Std PE  : n/a")
        print("Max PE  : n/a")
        return

    print(f"Mean PE : {statistics.mean(values):.3f}")
    print(f"Std PE  : {statistics.pstdev(values):.3f}")
    print(f"Max PE  : {max(values):.3f}")


def main() -> int:
    """Load overnight audit JSON and print the PE histogram."""

    if not AUDIT_RESULTS_PATH.is_file():
        print(
            f"Error: audit results file not found: {AUDIT_RESULTS_PATH}",
            file=sys.stderr,
        )
        return 1

    try:
        with AUDIT_RESULTS_PATH.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"Error: could not read audit results at {AUDIT_RESULTS_PATH}: {exc}",
            file=sys.stderr,
        )
        return 1

    values = _collect_prediction_errors(payload)
    report_histogram(values)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
