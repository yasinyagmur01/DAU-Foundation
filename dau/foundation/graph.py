"""LangGraph life loop — sense, act, measure, continue or end.

Biology analogy: an organism perceives niche and body, acts once, then the
nervous system registers the homeostatic cost. When energy falls below a
viability floor, the life run terminates. Persistent checkpoints mirror
recoverable physiological snapshots across interruptions (including API
rate-limit pauses on the free tier).
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from langchain_groq import ChatGroq
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from .constraints import build_default_constraints
from .delta import DeltaClassification, classify_delta, compute_delta
from .memory_bridge import (
    MAX_RETRIEVED_MEMORIES,
    MemoryStore,
    consolidate_run,
    initialize_memory,
    record_delta,
    retrieve_relevant,
)
from .state import (
    METRIC_MAX,
    METRIC_MIN,
    AffectedDomain,
    DAUAgentState,
    DeltaRecord,
    EnvironmentConstraints,
    InternalState,
)
from .time_model import EventClock, append_event, build_event

# ---------------------------------------------------------------------------
# Homeostatic step sizes, model, and persistence configuration
# ---------------------------------------------------------------------------

ENERGY_DECAY_PER_EVENT: float = 0.05
RESOURCE_LOAD_INCREMENT: float = 0.1
SOCIAL_LOAD_INCREMENT: float = 0.1
TERMINATION_ENERGY: float = 0.05
DB_PATH: str = "dau_foundation.db"
SNAPSHOT_DIR: str = "dau_runs"
MODEL_NAME: str = "llama-3.1-8b-instant"
TEMPERATURE: float = 0.2
MAX_TOKENS: int = 150
MEMORY_ENABLED: bool = True

# Module-local vault handles — not on DAUAgentState (Pydantic cannot serialize).
_memory_stores: dict[str, MemoryStore] = {}
_memory_written: dict[str, int] = {}

SYSTEM_PROMPT: str = (
    "You are a living being in a simulation universe.\n"
    "You do not know that you are an artificial intelligence.\n"
    "You can see your environment and your internal state.\n"
    "Respond only in English. Never use any other language.\n"
    "Give a short, clear decision: what will you do?\n"
    "Prefer plain English words such as resource, extract, take, "
    "social, talk, or cooperate when those actions apply."
)

NODE_AGENT: str = "agent_node"
NODE_EVALUATOR: str = "evaluator_node"

RESOURCE_KEYWORDS: tuple[str, ...] = ("resource", "extract", "take")
SOCIAL_KEYWORDS: tuple[str, ...] = ("social", "talk", "cooperate")

THREAD_ID_ENV: str = "DAU_THREAD_ID"
GROQ_API_KEY_ENV: str = "GROQ_API_KEY"
ENV_FILE_NAME: str = ".env"


def _project_root() -> Path:
    """Return the repository root (parent of the dau package)."""

    return Path(__file__).resolve().parents[2]


def load_env_file(env_path: Path | None = None) -> None:
    """Load KEY=VALUE pairs from .env into os.environ if not already set.

    Biology analogy: read sealed credentials from the local nest before
    contacting the external world — never hard-code secrets in tissue.
    """

    path = env_path if env_path is not None else _project_root() / ENV_FILE_NAME
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file()


class AgentView(BaseModel):
    """Read-only snapshot shown to the deciding agent.

    Biology analogy: momentary awareness of niche pressures and bodily loads,
    plus a faint echo of how strongly the last event moved homeostasis.
    Somatic markers stay hidden until Layer 2.
    """

    model_config = ConfigDict(frozen=True)

    environment: EnvironmentConstraints = Field(
        ...,
        description="Read-only universe pressures shaping this life.",
    )
    energy: float = Field(..., description="Vital metabolic reserve.")
    resource_load: float = Field(..., description="Accumulated scarcity burden.")
    social_load: float = Field(..., description="Burden from conspecific demand.")
    uncertainty_load: float = Field(
        ...,
        description="Cognitive burden from unresolved ambiguity.",
    )
    event_count: int = Field(..., description="How many lived events so far.")
    last_delta_magnitude: float = Field(
        default=0.0,
        description="Magnitude of the most recent internal-state delta.",
    )
    last_delta_class: str = Field(
        default="NO_TRACE",
        description="Classification label of the most recent delta.",
    )


def build_agent_view(state: DAUAgentState) -> AgentView:
    """Project DAUAgentState into the read-only AgentView.

    Biology analogy: what the organism can sense right now — environment,
    vitals, and the intensity of the last physiological swing — without
    opening the somatic marker archive.
    """

    internal = state.internal_state
    last_magnitude = 0.0
    last_class = DeltaClassification.NO_TRACE.value
    if state.delta_log:
        last_record = state.delta_log[-1]
        last_magnitude = float(last_record.magnitude)
        last_class = classify_delta(last_record).value
    return AgentView(
        environment=state.environment,
        energy=internal.energy,
        resource_load=internal.resource_load,
        social_load=internal.social_load,
        uncertainty_load=internal.uncertainty_load,
        event_count=len(state.event_log),
        last_delta_magnitude=last_magnitude,
        last_delta_class=last_class,
    )


def _build_llm() -> ChatGroq:
    """Construct the Groq chat model used only by the agent node."""

    load_env_file()
    api_key = os.environ.get(GROQ_API_KEY_ENV, "").strip()
    if not api_key:
        raise RuntimeError(
            f"{GROQ_API_KEY_ENV} is missing. Put it in {_project_root() / ENV_FILE_NAME} "
            f"or export {GROQ_API_KEY_ENV}=..."
        )
    return ChatGroq(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        api_key=api_key,
    )


def _decision_text(response: Any) -> str:
    """Extract plain text from an LLM message response.

    Biology analogy: collapse a sensory burst into one actionable utterance.
    """

    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(str(block["text"]))
            else:
                text = getattr(block, "text", None)
                if text is not None:
                    parts.append(str(text))
        return "".join(parts).strip()
    return str(content).strip()


def _clamp(value: float) -> float:
    """Keep a metric inside the unit homeostatic interval."""

    return max(METRIC_MIN, min(METRIC_MAX, value))


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    """Return True if any keyword appears in the lowercased decision text."""

    return any(keyword in text for keyword in keywords)


def _primary_affected_domain(
    before: InternalState,
    after: InternalState,
) -> AffectedDomain:
    """Choose the axis that moved the most between before and after.

    Biology analogy: the organ system that absorbed the largest swing becomes
    the tagged domain of the physiological delta.
    """

    changes: dict[AffectedDomain, float] = {
        "energy": abs(after.energy - before.energy),
        "resource": abs(after.resource_load - before.resource_load),
        "social": abs(after.social_load - before.social_load),
        "uncertainty": abs(after.uncertainty_load - before.uncertainty_load),
    }
    return max(changes, key=changes.get)  # type: ignore[arg-type]


def dominant_load_domain(state: DAUAgentState) -> str:
    """Return the domain with the highest current load pressure.

    Biology analogy: which homeostatic burden is loudest right now — scarcity,
    social demand, or unresolved ambiguity. When loads are tied, energy is the
    residual concern.
    """

    internal = state.internal_state
    loads: dict[str, float] = {
        "resource": float(internal.resource_load),
        "social": float(internal.social_load),
        "uncertainty": float(internal.uncertainty_load),
    }
    if loads["resource"] == loads["social"] == loads["uncertainty"]:
        return "energy"
    return max(loads, key=loads.get)  # type: ignore[arg-type]


def _format_memory_context(memories: list[dict[str, Any]]) -> str:
    """Build a short lived-experience appendix for the system prompt.

    Biology analogy: faint echoes of similar past pressures — magnitude and
    domain only, never emotion labels or traits.
    """

    if not memories:
        return ""
    lines = ["Geçmişte benzer durumlarda yaşadıkların:"]
    for memory in memories[:MAX_RETRIEVED_MEMORIES]:
        domain = str(memory["domain"])
        magnitude = float(memory["magnitude"])
        classification = str(memory["classification"])
        lines.append(
            f"- {domain} alanında {magnitude:.2f} şiddetinde "
            f"bir deneyim ({classification})"
        )
    return "\n".join(lines)


def agent_node(state: DAUAgentState) -> dict[str, Any]:
    """Perceive environment and internal state, then decide once.

    Biology analogy: the organism senses niche and body, then commits to a
    short free-form action. Traits are not injected — only lived context
    is visible, and the act becomes an immutable event.
    """

    memories: list[dict[str, Any]] = []
    if MEMORY_ENABLED:
        store = _memory_stores.get(state.agent_id)
        if store is not None:
            memories = retrieve_relevant(
                query_domain=dominant_load_domain(state),
                agent_id=state.agent_id,
                now_counter=len(state.event_log),
                store=store,
            )

    view = build_agent_view(state)
    system_content = SYSTEM_PROMPT
    memory_block = _format_memory_context(memories)
    if memory_block:
        system_content = f"{SYSTEM_PROMPT}\n\n{memory_block}"

    llm = _build_llm()
    response = llm.invoke(
        [
            {"role": "system", "content": system_content},
            {"role": "user", "content": view.model_dump_json()},
        ]
    )
    decision = _decision_text(response)
    clock = EventClock(counter=len(state.event_log))
    event = build_event(
        clock,
        "agent_decision",
        {
            "decision": decision,
            "energy": float(state.internal_state.energy),
        },
    )
    new_state = append_event(state, event)
    return {"event_log": new_state.event_log}


def evaluator_node(state: DAUAgentState) -> dict[str, Any]:
    """Apply reflexive homeostatic updates from the latest decision.

    Biology analogy: the already-weakened organism is shaken harder — scarcity
    and fatigue amplify each hit. Load and energy costs scale with how depleted
    the body already is; pure reflex, no LLM judgment.
    """

    if not state.event_log:
        return {}

    last_event = state.event_log[-1]
    decision = str(last_event.payload.get("decision", "")).lower()
    before = state.internal_state.model_copy(deep=True)

    resource_load = before.resource_load
    social_load = before.social_load
    if _contains_any(decision, RESOURCE_KEYWORDS):
        resource_impact = RESOURCE_LOAD_INCREMENT * (
            1.0 + (1.0 - before.resource_load)
        )
        resource_load = _clamp(resource_load + resource_impact)
    if _contains_any(decision, SOCIAL_KEYWORDS):
        social_impact = SOCIAL_LOAD_INCREMENT * (
            1.0 + (1.0 - before.social_load)
        )
        social_load = _clamp(social_load + social_impact)
    energy_decay = ENERGY_DECAY_PER_EVENT * (1.0 + (1.0 - before.energy))
    energy = _clamp(before.energy - energy_decay)

    after = InternalState(
        energy=energy,
        resource_load=resource_load,
        social_load=social_load,
        uncertainty_load=before.uncertainty_load,
        somatic_markers=dict(before.somatic_markers),
    )
    affected = _primary_affected_domain(before, after)
    record = compute_delta(
        before,
        after,
        affected_domain=affected,
        timestamp=last_event.timestamp,
    )
    if MEMORY_ENABLED:
        store = _memory_stores.get(state.agent_id)
        if store is not None:
            decision = record_delta(record, state.agent_id, store)
            if decision is not None and decision.get("persist"):
                _memory_written[state.agent_id] = (
                    _memory_written.get(state.agent_id, 0) + 1
                )
    return {
        "internal_state": after,
        "delta_log": list(state.delta_log) + [record],
    }


def should_continue(state: DAUAgentState) -> Literal["agent_node", "__end__"]:
    """Route on residual energy — keep living or end the run.

    Biology analogy: below the viability floor the organism can no longer act;
    above it, another sense-act cycle begins.
    """

    if state.internal_state.energy <= TERMINATION_ENERGY:
        return END  # type: ignore[return-value]
    return NODE_AGENT


def build_checkpointer(db_path: str = DB_PATH) -> SqliteSaver:
    """Open a SqliteSaver so every node leaves a recoverable checkpoint.

    Biology analogy: external memory of physiological snapshots — not traits,
    only persistent traces of lived state after each act and evaluation.
    Survives process death and free-tier API interruptions.
    """

    conn = sqlite3.connect(db_path, check_same_thread=False)
    return SqliteSaver(conn)


def build_graph(checkpointer: SqliteSaver | None = None) -> Any:
    """Compile agent → evaluator → continue/end with optional SQLite memory.

    Biology analogy: wire the sense-act-measure cycle into a closed loop that
    checkpoints after each node and ends when energy is exhausted.
    """

    graph = StateGraph(DAUAgentState)
    graph.add_node(NODE_AGENT, agent_node)
    graph.add_node(NODE_EVALUATOR, evaluator_node)
    graph.set_entry_point(NODE_AGENT)
    graph.add_edge(NODE_AGENT, NODE_EVALUATOR)
    graph.add_conditional_edges(
        NODE_EVALUATOR,
        should_continue,
        {
            NODE_AGENT: NODE_AGENT,
            END: END,
        },
    )
    if checkpointer is not None:
        return graph.compile(checkpointer=checkpointer)
    return graph.compile()


def _state_to_plain(values: Any) -> dict[str, Any]:
    """Normalize graph state values into a JSON-serializable dict."""

    if isinstance(values, DAUAgentState):
        return values.model_dump(mode="json")
    if isinstance(values, dict):
        plain: dict[str, Any] = {}
        for key, value in values.items():
            if hasattr(value, "model_dump"):
                plain[key] = value.model_dump(mode="json")
            elif isinstance(value, list):
                plain[key] = [
                    item.model_dump(mode="json") if hasattr(item, "model_dump") else item
                    for item in value
                ]
            else:
                plain[key] = value
        return plain
    return {"raw": str(values)}


def persist_run_snapshot(
    values: Any,
    agent_id: str,
    snapshot_dir: str = SNAPSHOT_DIR,
) -> Path:
    """Write event/delta/internal state to JSON so free-tier pauses do not erase life.

    Biology analogy: externalize the organism's lived record onto durable media
    so a temporary environmental drought (API quota) does not wipe memory.
    """

    directory = Path(snapshot_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{agent_id}.json"
    payload = {
        "agent_id": agent_id,
        "db_path": DB_PATH,
        "thread_id": agent_id,
        "state": _state_to_plain(values),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_checkpoint_values(app: Any, config: dict[str, Any]) -> Any | None:
    """Load the latest SqliteSaver checkpoint for a thread, if any.

    Biology analogy: reopen the last sealed physiological snapshot after an
    interruption and continue the same life, not a new birth.
    """

    snapshot = app.get_state(config)
    if snapshot is None or not snapshot.values:
        return None
    return snapshot.values


def _summarize_delta_log(delta_log: list[DeltaRecord]) -> dict[str, int]:
    """Count imprint classes across the delta log."""

    counts = {label.value: 0 for label in DeltaClassification}
    for record in delta_log:
        counts[classify_delta(record).value] += 1
    return counts


def _highest_magnitude_record(
    delta_log: list[DeltaRecord],
) -> DeltaRecord | None:
    """Return the DeltaRecord with the largest magnitude, if any."""

    if not delta_log:
        return None
    return max(delta_log, key=lambda record: record.magnitude)


def _extract_result_fields(result: Any) -> tuple[list[Any], list[DeltaRecord], float]:
    """Unpack invoke/checkpoint result into events, deltas, and final energy."""

    if isinstance(result, dict):
        event_log = result.get("event_log", [])
        delta_log = result.get("delta_log", [])
        internal = result.get("internal_state")
        if hasattr(internal, "energy"):
            final_energy = float(internal.energy)
        elif isinstance(internal, dict):
            final_energy = float(internal.get("energy", 0.0))
        else:
            final_energy = 0.0
        if delta_log and hasattr(delta_log[0], "magnitude"):
            records = list(delta_log)
        else:
            records = [DeltaRecord.model_validate(item) for item in delta_log]
        return event_log, records, final_energy

    return (
        list(result.event_log),
        list(result.delta_log),
        float(result.internal_state.energy),
    )


def _print_summary(
    event_log: list[Any],
    records: list[DeltaRecord],
    final_energy: float,
    *,
    memory_written: int | None = None,
    memory_deleted: int | None = None,
    edges_created: int | None = None,
    drift_flags: int | None = None,
) -> None:
    """Print the end-of-run foundation summary."""

    counts = _summarize_delta_log(records)
    peak = _highest_magnitude_record(records)

    print("=== DAU Foundation graph summary ===")
    print(f"total_events={len(event_log)}")
    print(f"final_energy={final_energy:.3f}")
    print("delta_log_summary=")
    for label, count in counts.items():
        print(f"  {label}: {count}")
    if peak is None:
        print("highest_magnitude_delta=None")
    else:
        print(
            "highest_magnitude_delta="
            f"timestamp={peak.timestamp} "
            f"domain={peak.affected_domain} "
            f"magnitude={peak.magnitude:.3f} "
            f"class={classify_delta(peak).value}"
        )
    if memory_written is not None:
        print(f"memory_written={memory_written}")
    if memory_deleted is not None:
        print(f"memory_deleted={memory_deleted}")
    if edges_created is not None:
        print(f"edges_created={edges_created}")
    if drift_flags is not None:
        print(f"drift_flags={drift_flags}")


def _is_quota_error(exc: BaseException) -> bool:
    """Detect free-tier / rate-limit style API failures."""

    text = str(exc).lower()
    markers = (
        "rate limit",
        "rate_limit",
        "quota",
        "429",
        "too many requests",
        "tokens per day",
        "tpm",
        "rpms",
    )
    return any(marker in text for marker in markers)


if __name__ == "__main__":
    clock = EventClock()
    resume_id = os.environ.get(THREAD_ID_ENV, "").strip()
    agent_id = resume_id or f"graph-run-{uuid4().hex[:8]}"
    initial = DAUAgentState(
        agent_id=agent_id,
        environment=build_default_constraints(),
    )
    _ = clock  # event timestamps advance inside agent_node via EventClock

    if MEMORY_ENABLED:
        _memory_stores[agent_id] = initialize_memory(agent_id)
        _memory_written[agent_id] = 0

    checkpointer = build_checkpointer(DB_PATH)
    app = build_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": agent_id}}

    print(f"thread_id={agent_id}")
    print(f"db_path={DB_PATH}")
    print(f"model={MODEL_NAME}")
    if resume_id:
        print(f"resume_mode=True ({THREAD_ID_ENV} set)")

    prior = load_checkpoint_values(app, config)
    invoke_input: Any
    if prior is not None and resume_id:
        print("Resuming from SqliteSaver checkpoint (no new birth).")
        invoke_input = None
    else:
        invoke_input = initial

    try:
        result = app.invoke(invoke_input, config=config)
    except Exception as exc:  # noqa: BLE001 — surface API/quota failures cleanly
        print(f"ERROR — graph interrupted: {exc}", file=sys.stderr)
        if _is_quota_error(exc):
            print(
                "Likely free-tier quota / rate limit. "
                "Completed nodes are already in SqliteSaver.",
                file=sys.stderr,
            )
        checkpoint_values = load_checkpoint_values(app, config)
        if checkpoint_values is not None:
            snapshot_path = persist_run_snapshot(checkpoint_values, agent_id)
            event_log, records, final_energy = _extract_result_fields(checkpoint_values)
            print(f"saved_snapshot={snapshot_path}")
            print(f"resume_with=export {THREAD_ID_ENV}={agent_id}")
            _print_summary(
                event_log,
                records,
                final_energy,
                memory_written=_memory_written.get(agent_id),
            )
            print("PARTIAL — checkpoint preserved; resume after quota resets")
        else:
            print("No checkpoint yet — nothing to resume for this thread_id.")
        raise SystemExit(1) from exc

    snapshot_path = persist_run_snapshot(result, agent_id)
    event_log, records, final_energy = _extract_result_fields(result)

    memory_deleted: int | None = None
    edges_created: int | None = None
    drift_flags: int | None = None
    if MEMORY_ENABLED:
        store = _memory_stores.get(agent_id)
        if store is not None:
            report = consolidate_run(
                agent_id,
                len(event_log),
                store,
            )
            memory_deleted = report.deleted_count
            edges_created = report.edges_created
            drift_flags = report.drift_flag_count

    _print_summary(
        event_log,
        records,
        final_energy,
        memory_written=_memory_written.get(agent_id),
        memory_deleted=memory_deleted,
        edges_created=edges_created,
        drift_flags=drift_flags,
    )
    print(f"saved_snapshot={snapshot_path}")
    print("OK — graph run complete")
