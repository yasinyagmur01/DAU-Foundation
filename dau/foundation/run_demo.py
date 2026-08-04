"""End-to-end foundation demo via the LangGraph life loop.

Biology analogy: a short life sequence under default pressures — the same
sense-act-measure-regulate cycle as production (social_pre → agent →
evaluator → meta_observer). AB_ENERGY_FLOOR + MAX_EVENTS in should_continue
keep the horizon long enough for Meta-Observer actuators to accumulate history.
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any

import dau.foundation.graph as graph_mod
from .constraints import build_default_constraints
from .delta import DeltaClassification, classify_delta
from .graph import (
    MAX_EVENTS,
    build_graph,
    get_pe_event_log,
    reset_pe_event_log,
)
from .lod import CognitiveMode, LODState
from .memory_bridge import initialize_memory
from .meta_observer import bind_memory_store, unbind_memory_store
from .state import DAUAgentState, DeltaRecord

# ---------------------------------------------------------------------------
# Demo identity, stream budget, audit path, overnight schema labels
# ---------------------------------------------------------------------------

DEMO_AGENT_ID: str = "demo-foundation-0"
# social_pre + agent + evaluator + meta_observer per event, plus headroom
STREAM_RECURSION_LIMIT: int = MAX_EVENTS * 4 + 10

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
AUDIT_RESULTS_PATH: Path = PROJECT_ROOT / "dau_runs" / "overnight_audit_results.json"
RUNS_KEY: str = "runs"
RUN_ID_PREFIX: str = "demo_"
RUN_ID_TIME_FORMAT: str = "%Y%m%d_%H%M%S"

AUDIT_CLASS_NOISE: str = "NOISE"
AUDIT_CLASS_NORMAL: str = "NORMAL"
AUDIT_CLASS_DEEP: str = "DEEP"
AUDIT_CLASS_TRAUMA: str = "TRAUMA"
AUDIT_DELTA_CLASSES: tuple[str, ...] = (
    AUDIT_CLASS_NOISE,
    AUDIT_CLASS_NORMAL,
    AUDIT_CLASS_DEEP,
    AUDIT_CLASS_TRAUMA,
)


def _delta_records_from_result(result: Any) -> list[DeltaRecord]:
    """Unpack delta_log from stream/invoke result into DeltaRecord list."""

    if isinstance(result, dict):
        delta_log = result.get("delta_log", [])
    else:
        delta_log = list(result.delta_log)
    if not delta_log:
        return []
    if hasattr(delta_log[0], "magnitude"):
        return list(delta_log)
    return [DeltaRecord.model_validate(item) for item in delta_log]


def _event_count_from_result(result: Any) -> int:
    """Count events in a stream/invoke result."""

    if isinstance(result, dict):
        return len(result.get("event_log", []))
    return len(result.event_log)


def _energy_from_result(result: Any) -> float:
    """Read final energy from a stream/invoke result."""

    if isinstance(result, dict):
        internal = result.get("internal_state")
        if hasattr(internal, "energy"):
            return float(internal.energy)
        if isinstance(internal, dict):
            return float(internal.get("energy", 0.0))
        return 0.0
    return float(result.internal_state.energy)


def _build_run_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate PE stats and delta-class counts for one overnight run row."""

    pe_values = [float(row["prediction_error"]) for row in events]
    class_counts = {name: 0 for name in AUDIT_DELTA_CLASSES}
    for row in events:
        label = str(row.get("delta_class", AUDIT_CLASS_NOISE))
        if label in class_counts:
            class_counts[label] += 1

    if pe_values:
        pe_mean = float(statistics.mean(pe_values))
        pe_std = float(statistics.pstdev(pe_values)) if len(pe_values) > 1 else 0.0
        pe_max = float(max(pe_values))
    else:
        pe_mean = 0.0
        pe_std = 0.0
        pe_max = 0.0

    return {
        "pe_mean": pe_mean,
        "pe_std": pe_std,
        "pe_max": pe_max,
        "delta_class_counts": class_counts,
        "total_events": len(events),
    }


def _append_overnight_audit(events: list[dict[str, Any]]) -> None:
    """Append one demo run into overnight_audit_results.json (best-effort)."""

    try:
        AUDIT_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        if AUDIT_RESULTS_PATH.is_file():
            with AUDIT_RESULTS_PATH.open(encoding="utf-8") as handle:
                payload = json.load(handle)
            if not isinstance(payload, dict):
                payload = {}
        else:
            payload = {}

        runs = payload.get(RUNS_KEY)
        if not isinstance(runs, list):
            runs = []

        run_id = RUN_ID_PREFIX + datetime.now().strftime(RUN_ID_TIME_FORMAT)
        runs.append(
            {
                "run_id": run_id,
                "events": list(events),
                "summary": _build_run_summary(events),
            }
        )
        payload[RUNS_KEY] = runs

        with AUDIT_RESULTS_PATH.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    except Exception:
        # Disk / permission / corrupt JSON must never abort the life demo.
        return


def run_demo() -> None:
    """Run up to MAX_EVENTS graph cycles including meta_observer_node.

    Uses the same compiled graph wire as production
    (social_pre → agent → evaluator → meta_observer → continue).
    Demo pins should_run_llm to False so System-1 NPC path stays offline.
    Horizon is governed by graph.should_continue (AB_ENERGY_FLOOR + MAX_EVENTS).
    Binds a MemoryStore so expectation can replay Chroma-cued past outcomes.
    """

    reset_pe_event_log()
    environment = build_default_constraints()
    initial = DAUAgentState(
        agent_id=DEMO_AGENT_ID,
        environment=environment,
        lod_state=LODState(mode=CognitiveMode.SYSTEM_1),
    )

    print("=== DAU Foundation demo ===")
    print(f"agent_id={initial.agent_id}")
    print(f"constraints={environment.model_dump()}")
    print(f"max_events={MAX_EVENTS}")
    print()

    original_should_run_llm = graph_mod.should_run_llm
    graph_mod.should_run_llm = lambda _lod: False
    store = initialize_memory(DEMO_AGENT_ID)
    graph_mod._memory_stores[DEMO_AGENT_ID] = store
    graph_mod._memory_written[DEMO_AGENT_ID] = 0
    bind_memory_store(DEMO_AGENT_ID, store)
    result: Any = initial
    stream_config = {"recursion_limit": STREAM_RECURSION_LIMIT}
    try:
        app = build_graph(checkpointer=None)
        for values in app.stream(
            initial,
            config=stream_config,
            stream_mode="values",
        ):
            result = values
    finally:
        unbind_memory_store(DEMO_AGENT_ID)
        graph_mod._memory_stores.pop(DEMO_AGENT_ID, None)
        graph_mod._memory_written.pop(DEMO_AGENT_ID, None)
        graph_mod.should_run_llm = original_should_run_llm
        try:
            store.close()
        except Exception:
            pass

    pe_events = get_pe_event_log()
    _append_overnight_audit(pe_events)

    records = _delta_records_from_result(result)
    counts = {label: 0 for label in DeltaClassification}
    for record in records:
        counts[classify_delta(record)] += 1

    for row in pe_events:
        print(
            f"event={row['event_counter']} "
            f"pe={row['prediction_error']:.3f} "
            f"magnitude={row['delta_magnitude']:.3f} "
            f"class={row['delta_class']}"
        )

    print()
    print("=== delta_log summary ===")
    for label in DeltaClassification:
        print(f"{label.value}: {counts[label]}")
    print(
        f"events={_event_count_from_result(result)} "
        f"energy={_energy_from_result(result):.3f}"
    )
    print(f"meta_cycles={len(pe_events)} pe_logged={len(pe_events)}")
    print("OK — run_demo complete")


if __name__ == "__main__":
    run_demo()
