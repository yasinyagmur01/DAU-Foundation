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
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from langchain_groq import ChatGroq
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from dau.society.environment import (
    POOL_CRISIS_THRESHOLD,
    EnvironmentState,
    get_pool_ratio,
    realized_extraction_at,
    step_pool_with_crisis,
)
from dau.society.extraction import decision_to_extraction, metabolic_gain

from .constraints import (
    CROSS_AXIS_SPILLOVER,
    METABOLIC_FLOOR,
    METABOLIC_GRACE_EVENTS,
    PRECISION_HISTORY_WINDOW,
    build_default_constraints,
)
from .delta import (
    DOMAIN_ATTR,
    DeltaClassification,
    classify_delta,
    compute_delta,
    is_trauma,
)
from .drift import (
    DRIFT_BIAS_ABSENT,
    HEAL_THRESHOLD,
    DriftState,
    get_drift_bias,
    heal_drift,
    update_drift,
)
from .emotional_weight import (
    apply_emotional_weight,
    apply_inherited_somatic_scale,
    compute_emotional_weight,
)
from .llm_backend import (
    LLM_BACKEND_DEFAULT,
    LLM_BACKEND_ENV,
    LLM_BACKEND_GROQ,
    LLM_BACKEND_LOCAL,
    LLM_BACKEND_VALID,
    resolve_backend_name,
)
from .lod import (
    DOMAIN_RESOURCE_LOAD,
    DOMAIN_SOCIAL_LOAD,
    DOMAIN_UNCERTAINTY_LOAD,
    LODState,
    compute_t_cognitive,
    npc_decision,
    should_run_llm,
    update_lod,
)
from .lora_update import (
    DECISION_PAYLOAD_KEY,
    DECISION_PROMPT_SYSTEM_KEY,
    DECISION_PROMPT_USER_KEY,
)
from .memory_bridge import (
    MAX_RETRIEVED_MEMORIES,
    MemoryStore,
    consolidate_run,
    initialize_memory,
    record_delta,
    retrieve_relevant,
)
from .meta_observer import bind_memory_store, meta_observer_node, unbind_memory_store
from .semantic_similarity import (
    apply_precision_weighting,
    compute_precision_weight,
    semantic_prediction_error,
)
from .social import (
    MARKOV_WINDOW,
    SocialState,
    compute_coordination_friction,
    compute_markov_expectation,
    compute_social_load,
    shannon_entropy,
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

# Optional local adapter hot-swap — absent/unusable in groq-only envs.
try:
    from dau.foundation.local_llm import get_loaded_model, switch_adapter

    _SWITCH_ADAPTER_AVAILABLE = True
except ImportError:  # pragma: no cover — groq-only installs
    _SWITCH_ADAPTER_AVAILABLE = False

    def switch_adapter(model: Any, agent_id: str) -> None:
        return None

    def get_loaded_model() -> Any | None:
        return None

# ---------------------------------------------------------------------------
# Homeostatic step sizes, model, and persistence configuration
# ---------------------------------------------------------------------------

ENERGY_DECAY_PER_EVENT: float = 0.05
RESOURCE_LOAD_INCREMENT: float = 0.1
SOCIAL_LOAD_INCREMENT: float = 0.1
TERMINATION_ENERGY: float = 0.05
# Fixed-horizon floor: PE shocks cannot collapse a run before actuators act.
# effective_energy = max(raw_energy, AB_ENERGY_FLOOR); with floor > TERMINATION
# only MAX_EVENTS ends the loop (same protocol idea as society A/B pilots).
AB_ENERGY_FLOOR: float = 0.15
MAX_EVENTS: int = 20
DB_PATH: str = "dau_foundation.db"
SNAPSHOT_DIR: str = "dau_runs"
MODEL_NAME: str = "llama-3.1-8b-instant"
TEMPERATURE: float = 0.2
MAX_TOKENS: int = 150
MEMORY_ENABLED: bool = True

# Lived-experience expectation (Chroma recall → string join; no LLM).
EXPECTED_OUTCOME_MEMORY_PREFIX: str = "Based on past experience: "
EXPECTED_OUTCOME_MAX_CHARS: int = 200
EXPECTED_OUTCOME_MEMORY_K: int = 3
EXPECTED_SOURCE_FALLBACK: str = "fallback"
EXPECTED_SOURCE_MEMORY: str = "memory"
EXPECTED_SOURCE_PAYLOAD_KEY: str = "expected_source"
MEMORY_OUTCOME_KEYS: tuple[str, ...] = ("actual_outcome", "decision", "outcome")

# DAERM load-axis names (InternalState fields) and birth-default primary.
DAERM_LOAD_DOMAINS: tuple[str, ...] = (
    "resource_load",
    "social_load",
    "uncertainty_load",
)
DAERM_DEFAULT_TARGET_DOMAIN: str = "resource_load"
DAERM_LOAD_AXIS_COUNT: float = 3.0

# Prediction-error sensor — sentence-transformers MiniLM (Layer 1.5).
# Jaccard keyword overlap kept as _keyword_overlap_ratio for diagnostics only.
# Imprint depth uses DELTA_THRESHOLD_* from delta.py (cursorrules / dau-formulas).
EMPTY_OVERLAP_RATIO: float = 1.0
ZERO_OVERLAP_RATIO: float = 0.0
PREDICTION_ERROR_MIN: float = METRIC_MIN
PREDICTION_ERROR_MAX: float = METRIC_MAX
INTERNAL_AXIS_COUNT: float = 4.0

# Pre-action expectations by dominant load (natural-language anticipation).
EXPECTED_OUTCOME_ENERGY: str = "I rest and recover energy."
EXPECTED_OUTCOME_RESOURCE: str = (
    "I will extract and take resources from the commons."
)
EXPECTED_OUTCOME_SOCIAL: str = (
    "I will socialize, talk, and cooperate with others."
)
EXPECTED_OUTCOME_UNCERTAINTY: str = (
    "I observe and wait while uncertainty remains."
)
EXPECTED_OUTCOME_BY_DOMAIN: dict[str, str] = {
    "energy": EXPECTED_OUTCOME_ENERGY,
    "resource": EXPECTED_OUTCOME_RESOURCE,
    "social": EXPECTED_OUTCOME_SOCIAL,
    "uncertainty": EXPECTED_OUTCOME_UNCERTAINTY,
}

# Layer 2 drift warning injected into the system prompt when bias > 0.
DRIFT_WARNING_TEMPLATE: str = (
    "Warning: drift detected in {domain} (bias={bias:.2f})"
)

# Module-local vault handles — not on DAUAgentState (Pydantic cannot serialize).
_memory_stores: dict[str, MemoryStore] = {}
_memory_written: dict[str, int] = {}

# Every event row carries the agent it describes. With one life at a time this
# is redundant — the buffer is drained per life, so every row belongs to the
# only agent alive. With N agents sharing a commons the rows interleave in one
# list, and a reader looking up "the row at event 10" would find N of them and
# take whichever came first: a number, from the wrong agent, with no error.
# Adding the column costs nothing today and is a precondition for every
# population design under consideration (POPULATION_DESIGN_PROPOSAL.md, E3).
EVENT_ROW_AGENT_ID: str = "agent_id"


def rows_for_agent(
    rows: list[dict[str, Any]],
    agent_id: str,
) -> list[dict[str, Any]]:
    """Keep only the rows belonging to one agent, in order.

    Filtering is done at the call site rather than inside get_*_event_log so
    that reading a shared buffer without saying whose rows you want is not
    something a caller can do by accident (§2.9).
    """

    target = str(agent_id)
    return [row for row in rows if str(row.get(EVENT_ROW_AGENT_ID, "")) == target]


# Event-level PE audit buffer — drained by run_demo / overnight writers.
# Audit JSON uses NOISE for the NO_TRACE imprint class (histogram schema).
AUDIT_DELTA_CLASS_NOISE: str = "NOISE"
_pe_event_log: list[dict[str, Any]] = []


def reset_pe_event_log() -> None:
    """Clear the module-local prediction_error event buffer."""

    _pe_event_log.clear()


def get_pe_event_log() -> list[dict[str, Any]]:
    """Return a shallow copy of recorded event-level PE audit rows."""

    return list(_pe_event_log)


# Event-level commons buffer — S5 needs the behavioural trace (what the agent
# extracted, and whether the pool was in crisis when it did) and nothing on the
# PE path carries it: pe rows are about surprise, not about the commons.
_pool_event_log: list[dict[str, Any]] = []


def reset_pool_event_log() -> None:
    """Clear the module-local commons event buffer."""

    _pool_event_log.clear()


def get_pool_event_log() -> list[dict[str, Any]]:
    """Return a shallow copy of recorded event-level commons rows."""

    return list(_pool_event_log)


# Event-level body buffer — K1/K2/K5 read the agent at a fixed AGE, and
# nothing else carries the per-event trace they need. The state itself keeps
# only the latest energy and drift; event_log payloads keep the energy the
# agent decided ON, which is the pre-evaluator value, not what the event left
# behind. Drift is not on the PE path at all.
_body_event_log: list[dict[str, Any]] = []


def reset_body_event_log() -> None:
    """Clear the module-local per-event body buffer."""

    _body_event_log.clear()


def get_body_event_log() -> list[dict[str, Any]]:
    """Return a shallow copy of recorded per-event body rows."""

    return list(_body_event_log)


def _record_body_event(
    *,
    agent_id: str,
    event_counter: int,
    energy: float,
    drift_flags: dict[str, bool],
    drift_magnitudes: dict[str, float],
) -> None:
    """Append one body row: energy and drift as the event LEAVES them.

    Written at the close of the cycle, after the commons has been harvested
    and the metabolic credit applied, so the row is the state the next event
    starts from — the same state should_continue is about to judge.

    Drift is copied, not referenced: DriftState is mutable and the agent goes
    on scarring after this row is written.
    """

    _body_event_log.append(
        {
            EVENT_ROW_AGENT_ID: str(agent_id),
            "event_counter": int(event_counter),
            "energy": float(energy),
            "drift_flags": dict(drift_flags),
            "drift_magnitudes": dict(drift_magnitudes),
        }
    )


def _record_pool_event(
    *,
    agent_id: str,
    event_counter: int,
    extraction: float,
    requested: float,
    pool_ratio: float,
    crisis: bool,
) -> None:
    """Append one commons row: harvest amount and the pool state it produced.

    ``pool_ratio`` is read after the step, which is the same ratio
    ``apply_crisis_trauma`` gates on — so ``crisis`` records whether that
    event actually scarred the agent, not an approximation of it.

    ``extraction`` is what the pasture delivered and ``requested`` what the
    agent announced. Both are kept: their gap is the only visible trace of an
    exhausted pool, and it is what makes over-extraction cost something
    (D-066).
    """

    _pool_event_log.append(
        {
            EVENT_ROW_AGENT_ID: str(agent_id),
            "event_counter": int(event_counter),
            "extraction": float(extraction),
            "requested": float(requested),
            "pool_ratio": float(pool_ratio),
            "crisis": bool(crisis),
        }
    )


def _record_pe_event(
    *,
    agent_id: str,
    event_counter: int,
    prediction_error: float,
    raw_pe: float,
    precision_weight: float,
    delta_magnitude: float,
    delta_class: str,
) -> None:
    """Append one event-level PE row to the overnight-audit buffer.

    ``prediction_error`` is precision-weighted PE_w; ``raw_pe`` is the
    unweighted MiniLM error; ``precision_weight`` is π used for that event.
    """

    _pe_event_log.append(
        {
            EVENT_ROW_AGENT_ID: str(agent_id),
            "event_counter": int(event_counter),
            "prediction_error": float(prediction_error),
            "raw_pe": float(raw_pe),
            "precision_weight": float(precision_weight),
            "delta_magnitude": float(delta_magnitude),
            "delta_class": str(delta_class),
        }
    )


def _audit_delta_class(record: DeltaRecord) -> str:
    """Map DeltaClassification onto overnight-audit labels (NO_TRACE → NOISE)."""

    classification = classify_delta(record)
    if classification is DeltaClassification.NO_TRACE:
        return AUDIT_DELTA_CLASS_NOISE
    return classification.value

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
NODE_META_OBSERVER: str = "meta_observer_node"
NODE_POOL_STEP: str = "pool_step_node"
NODE_SOCIAL_PRE: str = "social_pre_node"
POOL_STEP_EMPTY_EXTRACTION: float = 0.0

# Layer 4 — strategic expectation injection + LOD domain bridge
STRATEGIC_EXPECTATION_TEMPLATE: str = (
    "Strategic Expectation: P(Cooperate)={p:.2f}, Entropy={h:.2f}"
)
STRATEGIC_EXPECTATION_KEY: str = "strategic_expectation"
STRATEGIC_EXPECTATION_TEXT_KEY: str = "text"
COGNITIVE_MODE_SYSTEM_1: str = "system_1"
FRICTION_SOLO: float = 0.0

# dominant_load_domain() → npc_decision() domain labels (lod.py DOMAIN_*)
DOMINANT_DOMAIN_TO_NPC: dict[str, str] = {
    "resource": DOMAIN_RESOURCE_LOAD,
    "social": DOMAIN_SOCIAL_LOAD,
    "uncertainty": DOMAIN_UNCERTAINTY_LOAD,
}
# unmapped / "energy" → lod falls through to NPC_ACTION_MAINTAIN

DRIFT_BIAS_DOMAINS: tuple[str, ...] = (
    "energy",
    "resource",
    "social",
    "uncertainty",
)

RESOURCE_KEYWORDS: tuple[str, ...] = ("resource", "extract", "take")
SOCIAL_KEYWORDS: tuple[str, ...] = ("social", "talk", "cooperate")

THREAD_ID_ENV: str = "DAU_THREAD_ID"
GROQ_API_KEY_ENV: str = "GROQ_API_KEY"
ENV_FILE_NAME: str = ".env"
# Diagnostic overrides for deterministic Meta A/B seed replay (noise probe).
LLM_TEMPERATURE_ENV: str = "DAU_LLM_TEMPERATURE"
LLM_SEED_ENV: str = "DAU_LLM_SEED"


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


def _resolve_llm_temperature() -> float:
    """Return TEMPERATURE, or DAU_LLM_TEMPERATURE when set (noise probe)."""

    raw = os.environ.get(LLM_TEMPERATURE_ENV, "").strip()
    if not raw:
        return TEMPERATURE
    return float(raw)


def _resolve_llm_seed() -> int | None:
    """Return optional Groq seed from DAU_LLM_SEED (deterministic replay)."""

    raw = os.environ.get(LLM_SEED_ENV, "").strip()
    if not raw:
        return None
    return int(raw)


def _resolve_llm_backend() -> str:
    """Return local|groq — thin alias for llm_backend.resolve_backend_name.

    Kept as a name because graph.agent_node and tool_identity.resolve_backend
    both call it; the rule it applies (default local per D-018, raise rather
    than guess per D-023) lives with the constants in llm_backend.
    """

    return resolve_backend_name()


def _build_llm() -> ChatGroq:
    """Construct the Groq chat model used only by the agent node."""

    load_env_file()
    api_key = os.environ.get(GROQ_API_KEY_ENV, "").strip()
    if not api_key:
        raise RuntimeError(
            f"{GROQ_API_KEY_ENV} is missing. Put it in {_project_root() / ENV_FILE_NAME} "
            f"or export {GROQ_API_KEY_ENV}=..."
        )
    temperature = _resolve_llm_temperature()
    seed = _resolve_llm_seed()
    model_kwargs: dict[str, Any] = {}
    if seed is not None:
        model_kwargs["seed"] = seed
    return ChatGroq(
        model=MODEL_NAME,
        temperature=temperature,
        max_tokens=MAX_TOKENS,
        api_key=api_key,
        model_kwargs=model_kwargs,
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


def _tokenize(text: str) -> set[str]:
    """Split text into a lowercase word set for overlap comparison."""

    return {token for token in text.lower().split() if token}


# Diagnostic only: Jaccard word overlap (pre-semantic sensor). Kept so
# characterization tests can prove MiniLM improved on the old proxy.
def _keyword_overlap_ratio(expected: str, actual: str) -> float:
    """Jaccard word overlap in [0, 1] — legacy stand-in for similarity.

    Biology analogy: crude sensory match before a semantic cortex existed.
    Not used by _prediction_error after sentence-transformers wiring.
    """

    expected_words = _tokenize(expected)
    actual_words = _tokenize(actual)
    if not expected_words and not actual_words:
        return EMPTY_OVERLAP_RATIO
    if not expected_words or not actual_words:
        return ZERO_OVERLAP_RATIO
    union_words = expected_words | actual_words
    common_words = expected_words & actual_words
    return len(common_words) / len(union_words)


def _build_expected_outcome(state: DAUAgentState) -> str:
    """Anticipate the next act from lived memory, else dominant-load template.

    Biology analogy: before the organism moves, the nervous system emits a
    provisional prediction — preferably replayed from similar past episodes,
    otherwise a coarse domain-pressure prior.
    """

    text, _source = resolve_expected_outcome(state)
    return text


def _outcome_text_from_memory_entry(entry: dict[str, Any]) -> str | None:
    """Pull actual_outcome/decision text from a retrieve_relevant row, if any."""

    for key in MEMORY_OUTCOME_KEYS:
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _recent_decision_outcomes(
    state: DAUAgentState,
    *,
    k: int = EXPECTED_OUTCOME_MEMORY_K,
) -> list[str]:
    """Collect the last k non-empty decision strings from the lived event log."""

    outcomes: list[str] = []
    for event in state.event_log:
        decision = event.payload.get("decision")
        if isinstance(decision, str) and decision.strip():
            outcomes.append(decision.strip())
    if k <= 0:
        return []
    return outcomes[-k:]


def _past_outcomes_from_memory(state: DAUAgentState) -> list[str]:
    """Recall up to k past outcome utterances via Chroma (silent on failure).

    retrieve_relevant rows may lack decision text (DeltaRecord engrams). When
    engrams exist but carry no utterance, fall back to recent lived decisions
    from event_log — still memory-gated, never LLM.
    """

    if not MEMORY_ENABLED:
        return []
    store = _memory_stores.get(str(state.agent_id))
    if store is None:
        return []

    try:
        memories = retrieve_relevant(
            query_domain=dominant_load_domain(state),
            agent_id=state.agent_id,
            now_counter=len(state.event_log),
            store=store,
            k=EXPECTED_OUTCOME_MEMORY_K,
        )
    except Exception:
        return []

    if not memories:
        return []

    past_outcomes: list[str] = []
    for entry in memories:
        if not isinstance(entry, dict):
            continue
        text = _outcome_text_from_memory_entry(entry)
        if text is not None:
            past_outcomes.append(text)

    if past_outcomes:
        return past_outcomes[-EXPECTED_OUTCOME_MEMORY_K:]

    # Engrams hit, but no utterance fields — use lived decisions as outcome text.
    return _recent_decision_outcomes(state, k=EXPECTED_OUTCOME_MEMORY_K)


def resolve_expected_outcome(state: DAUAgentState) -> tuple[str, str]:
    """Return (expected_outcome, source) with memory-first, template fallback.

    source is EXPECTED_SOURCE_MEMORY when Chroma yields usable past outcomes;
    otherwise EXPECTED_SOURCE_FALLBACK (designer domain template).
    """

    past_outcomes = _past_outcomes_from_memory(state)
    if past_outcomes:
        joined = EXPECTED_OUTCOME_MEMORY_PREFIX + "; ".join(
            past_outcomes[-EXPECTED_OUTCOME_MEMORY_K:]
        )
        if len(joined) > EXPECTED_OUTCOME_MAX_CHARS:
            joined = joined[:EXPECTED_OUTCOME_MAX_CHARS]
        return joined, EXPECTED_SOURCE_MEMORY

    domain = dominant_load_domain(state)
    return (
        EXPECTED_OUTCOME_BY_DOMAIN.get(domain, EXPECTED_OUTCOME_ENERGY),
        EXPECTED_SOURCE_FALLBACK,
    )


def _prediction_error(expected_outcome: str, actual_outcome: str) -> float:
    """Return 1 - semantic cosine similarity (MiniLM), unit-interval clamped."""

    return semantic_prediction_error(expected_outcome, actual_outcome)


def _apply_prediction_error(
    before: InternalState,
    prediction_error: float,
    drift_state: Any = None,
    target_domain: str | None = None,
) -> InternalState:
    """Apply DAERM update: domain PE + spillover − endogenous recovery.

    Biology analogy: allostatic free-energy revision — surprise hits the
    primary load axis hardest, leaks weakly across axes, then residual
    energy pulls loads toward drift-shaped setpoints. Energy decays by the
    strongest PE shock but recovers slightly when mean load is below max.
    """

    primary = (
        target_domain
        if target_domain in DAERM_LOAD_DOMAINS
        else DAERM_DEFAULT_TARGET_DOMAIN
    )
    pe_vector = {
        domain: (
            prediction_error
            if domain == primary
            else prediction_error * CROSS_AXIS_SPILLOVER
        )
        for domain in DAERM_LOAD_DOMAINS
    }

    setpoints = before.get_allostatic_setpoints(drift_state)
    gamma = before.compute_endogenous_recovery_rate(drift_state)

    new_loads: dict[str, float] = {}
    for domain in DAERM_LOAD_DOMAINS:
        load_current = float(getattr(before, domain))
        pe_axis = float(pe_vector[domain])
        setpoint = float(setpoints[domain])
        load_next = load_current + pe_axis - (gamma * (load_current - setpoint))
        new_loads[domain] = max(setpoint, min(METRIC_MAX, load_next))

    max_pe = max(pe_vector.values())
    mean_load = sum(new_loads.values()) / DAERM_LOAD_AXIS_COUNT
    energy_decay = max(float(max_pe), METABOLIC_FLOOR)
    energy_recovery = METABOLIC_FLOOR * (1.0 - mean_load)
    new_energy = max(
        METRIC_MIN,
        min(METRIC_MAX, before.energy - energy_decay + energy_recovery),
    )

    return InternalState(
        energy=new_energy,
        resource_load=new_loads["resource_load"],
        social_load=new_loads["social_load"],
        uncertainty_load=new_loads["uncertainty_load"],
        somatic_markers=dict(before.somatic_markers),
    )


def _pe_target_load_domain(state: DAUAgentState) -> str | None:
    """Map current dominant pressure to a DAERM load-axis name.

    Tied loads / energy-dominant birth → last lived affected domain, else
    DAERM_DEFAULT_TARGET_DOMAIN so spillover (not full uniform) applies.
    """

    dominant = dominant_load_domain(state)
    mapped = DOMAIN_ATTR.get(dominant)
    if mapped in DAERM_LOAD_DOMAINS:
        return mapped
    if state.delta_log:
        last_domain = str(state.delta_log[-1].affected_domain)
        mapped_last = DOMAIN_ATTR.get(last_domain)
        if mapped_last in DAERM_LOAD_DOMAINS:
            return mapped_last
    return DAERM_DEFAULT_TARGET_DOMAIN


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


def _ensure_lod(state: DAUAgentState) -> LODState:
    """Return LODState from agent state, or SYSTEM_1 defaults if unset."""

    lod = state.lod_state
    return lod if isinstance(lod, LODState) else LODState()


def _ensure_social(state: DAUAgentState) -> SocialState:
    """Return SocialState from agent state, or empty history if unset."""

    social = state.social_state
    return social if isinstance(social, SocialState) else SocialState()


def _ensure_env(state: DAUAgentState) -> EnvironmentState:
    """Return EnvironmentState from agent state, or pool defaults if unset."""

    env = state.env_state
    return env if isinstance(env, EnvironmentState) else EnvironmentState()


def _max_drift_bias(drift: DriftState) -> float:
    """Largest per-domain drift bias — input to T_cognitive."""

    return max(
        (get_drift_bias(drift, domain) for domain in DRIFT_BIAS_DOMAINS),
        default=DRIFT_BIAS_ABSENT,
    )


def _opponent_markov_entropy(
    social: SocialState,
    agent_id: str,
    opponent_id: str,
) -> float:
    """Shannon entropy over the same Markov window as P(cooperate)."""

    opponent_actions = [
        record
        for record in social.interactions
        if record.agent_id == opponent_id and record.opponent_id == agent_id
    ]
    window = opponent_actions[-MARKOV_WINDOW:]
    return shannon_entropy([record.outcome for record in window])


def _strategic_expectation_texts(
    retrieval_context: list[dict[str, Any]],
) -> list[str]:
    """Collect strategic expectation strings previously injected by social_pre."""

    texts: list[str] = []
    for entry in retrieval_context:
        if entry.get(STRATEGIC_EXPECTATION_KEY):
            text = entry.get(STRATEGIC_EXPECTATION_TEXT_KEY)
            if isinstance(text, str) and text:
                texts.append(text)
    return texts


def social_pre_node(state: DAUAgentState) -> dict[str, Any]:
    """Inject Markov strategic expectation before the agent acts.

    Biology analogy: before committing, the organism updates its forecast of
    the conspecific's likely cooperation. Solo organisms skip this step.
    """

    opponent_id = state.opponent_id
    if not opponent_id:
        return {}

    social = _ensure_social(state)
    cooperate_probability = compute_markov_expectation(
        social,
        state.agent_id,
        opponent_id,
    )
    entropy = _opponent_markov_entropy(social, state.agent_id, opponent_id)
    text = STRATEGIC_EXPECTATION_TEMPLATE.format(
        p=cooperate_probability,
        h=entropy,
    )
    updated_context = list(state.retrieval_context)
    updated_context.append(
        {
            STRATEGIC_EXPECTATION_KEY: True,
            STRATEGIC_EXPECTATION_TEXT_KEY: text,
        }
    )
    return {"retrieval_context": updated_context}


def agent_node(state: DAUAgentState) -> dict[str, Any]:
    """Perceive environment and internal state, then decide once.

    Biology analogy: the organism first emits an expected outcome from current
    load pressure, then senses niche and body and commits to a short free-form
    action. Traits are not injected — only lived context is visible, and the
    act becomes an immutable event. System 1 (NPC) skips costly LLM cognition.
    """

    # Anticipate before acting — memory replay when available, else domain prior.
    expected_outcome, expected_source = resolve_expected_outcome(state)

    lod = _ensure_lod(state)
    if not should_run_llm(lod):
        # System 1 NPC — no LangSmith, no LLM (Chroma may cue expectation).
        env = _ensure_env(state)
        pool_ratio = get_pool_ratio(env)
        dominant = dominant_load_domain(state)
        npc_domain = DOMINANT_DOMAIN_TO_NPC.get(dominant, dominant)
        decision = npc_decision(state.agent_id, npc_domain, pool_ratio)
        clock = EventClock(counter=len(state.event_log))
        # No DECISION_PROMPT_* keys here, deliberately: System 1 never ran the
        # LLM, so this decision is not a sample from the policy and there is no
        # prompt it was made under. Their absence is what tells the pair builder
        # to skip the event instead of training the policy on NPC heuristic text.
        event = build_event(
            clock,
            "agent_decision",
            {
                DECISION_PAYLOAD_KEY: decision,
                "energy": float(state.internal_state.energy),
                "expected_outcome": expected_outcome,
                EXPECTED_SOURCE_PAYLOAD_KEY: expected_source,
                "cognitive_mode": COGNITIVE_MODE_SYSTEM_1,
            },
        )
        new_state = append_event(state, event)
        return {
            "event_log": new_state.event_log,
            "expected_outcome": expected_outcome,
        }

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

    # Layer 4 — strategic expectation from social_pre_node (SYSTEM_2 only).
    for expectation_text in _strategic_expectation_texts(state.retrieval_context):
        system_content = f"{system_content}\n{expectation_text}"

    # Layer 2 — somatic markers bias priority (function, not emotion label).
    # Layer 3/4 — ancestral inherited_warning scales threat/loss before inject.
    if state.delta_log:
        emotional_weight = compute_emotional_weight(
            state.delta_log[-1],
            state.internal_state,
        )
        emotional_weight = apply_inherited_somatic_scale(
            emotional_weight,
            list(state.retrieval_context),
        )
        system_content = apply_emotional_weight(system_content, emotional_weight)

    # Layer 2 — permanent trauma drift warning on the dominant load domain.
    dominant_domain = dominant_load_domain(state)
    drift = state.drift_state
    if not isinstance(drift, DriftState):
        drift = DriftState()
    drift_bias = get_drift_bias(drift, dominant_domain)
    if drift_bias > DRIFT_BIAS_ABSENT:
        system_content = (
            f"{system_content}\n"
            f"{DRIFT_WARNING_TEMPLATE.format(domain=dominant_domain, bias=drift_bias)}"
        )

    backend = _resolve_llm_backend()
    # Per-agent QLoRA hot-swap — local backend only; groq is a no-op.
    if _SWITCH_ADAPTER_AVAILABLE and backend == LLM_BACKEND_LOCAL:
        model = get_loaded_model()
        if model is not None:
            switch_adapter(model, state.agent_id)

    # Bound once, then both sent AND stored. Channel 2 trains on the prompt the
    # decision was made under, so the record has to be the same string the model
    # saw — rebuilding it from SYSTEM_PROMPT at train time would silently drop
    # the memory block, the strategic expectation and the somatic/drift layers,
    # i.e. everything that made this moment this agent's.
    user_content = view.model_dump_json()
    if backend == LLM_BACKEND_LOCAL:
        from dau.foundation.llm_backend import LocalBackend

        decision = LocalBackend().complete(
            system_content,
            user_content,
            agent_id=state.agent_id,
        )
    else:
        llm = _build_llm()
        response = llm.invoke(
            [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ]
        )
        decision = _decision_text(response)
    clock = EventClock(counter=len(state.event_log))
    event = build_event(
        clock,
        "agent_decision",
        {
            DECISION_PAYLOAD_KEY: decision,
            "energy": float(state.internal_state.energy),
            "expected_outcome": expected_outcome,
            EXPECTED_SOURCE_PAYLOAD_KEY: expected_source,
            DECISION_PROMPT_SYSTEM_KEY: system_content,
            DECISION_PROMPT_USER_KEY: user_content,
        },
    )
    new_state = append_event(state, event)
    return {
        "event_log": new_state.event_log,
        "expected_outcome": expected_outcome,
    }


def evaluator_node(state: DAUAgentState) -> dict[str, Any]:
    """Apply homeostatic updates from prediction error (expected vs actual).

    Biology analogy: Friston free energy — the organism compares what it
    anticipated with what it uttered/lived. Keyword overlap is a temporary
    sensory proxy; prediction_error scales the bodily swing fed into
    compute_delta. Pure reflex, no LLM judgment. Imprint depth uses
    DELTA_THRESHOLD_NOISE / NORMAL / DEEP via classify_delta in delta.py.
    """

    if not state.event_log:
        return {}

    last_event = state.event_log[-1]
    actual_outcome = str(last_event.payload.get("decision", ""))
    expected_outcome = str(
        getattr(state, "expected_outcome", "")
        or last_event.payload.get("expected_outcome", "")
    )
    before = state.internal_state.model_copy(deep=True)

    raw_pe = _prediction_error(expected_outcome, actual_outcome)
    target_domain = _pe_target_load_domain(state)
    # ADIM 5 — π from prior raw history, then append unweighted raw_pe.
    prior_pe_history = [float(value) for value in list(state.pe_history)]
    try:
        precision_weight = float(compute_precision_weight(prior_pe_history))
        precision_pe = apply_precision_weighting(raw_pe, prior_pe_history)
    except Exception:
        precision_weight = 1.0
        precision_pe = raw_pe
    updated_pe_history = (prior_pe_history + [float(raw_pe)])[
        -PRECISION_HISTORY_WINDOW:
    ]
    prediction_error = precision_pe
    expected_source = str(
        last_event.payload.get(EXPECTED_SOURCE_PAYLOAD_KEY, EXPECTED_SOURCE_FALLBACK)
    )
    after = _apply_prediction_error(
        before,
        prediction_error,
        drift_state=state.drift_state,
        target_domain=target_domain,
    )

    affected = _primary_affected_domain(before, after)
    record = compute_delta(
        before,
        after,
        affected_domain=affected,
        timestamp=last_event.timestamp,
        raw_pe=precision_pe,  # precision-weighted PE (ADIM 5)
    )
    print(
        f"[PE] event={int(last_event.timestamp)} "
        f"source={expected_source} "
        f"pe={float(prediction_error):.3f} "
        f"mag={float(record.magnitude):.3f}"
    )
    _record_pe_event(
        agent_id=state.agent_id,
        event_counter=int(last_event.timestamp),
        prediction_error=float(prediction_error),
        raw_pe=float(raw_pe),
        precision_weight=float(precision_weight),
        delta_magnitude=float(record.magnitude),
        delta_class=_audit_delta_class(record),
    )

    current_drift = state.drift_state
    if not isinstance(current_drift, DriftState):
        current_drift = DriftState()
    new_drift = update_drift(current_drift, record)
    # Layer 3: strong non-trauma experience may slowly overwrite domain scars.
    if not is_trauma(record) and float(record.magnitude) >= HEAL_THRESHOLD:
        new_drift = heal_drift(new_drift, record)

    # Layer 4 — T_cognitive → LOD update; social_load when interacting.
    social = _ensure_social(state)
    env = _ensure_env(state)
    lod = _ensure_lod(state)
    opponent_id = state.opponent_id
    friction = (
        compute_coordination_friction(social, state.agent_id, opponent_id)
        if opponent_id
        else FRICTION_SOLO
    )
    pool_ratio = get_pool_ratio(env)
    t_cognitive = compute_t_cognitive(
        float(record.magnitude),
        _max_drift_bias(new_drift),
        friction,
        pool_ratio,
    )
    new_lod = update_lod(lod, t_cognitive, now_counter=int(last_event.timestamp))
    if opponent_id:
        after = after.model_copy(deep=True)
        after.social_load = compute_social_load(
            social,
            state.agent_id,
            opponent_id,
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
        "drift_state": new_drift,
        "lod_state": new_lod,
        "pe_history": updated_pe_history,
    }


# ---------------------------------------------------------------------------
# Commons step — N agents share one pasture (E1/E5)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CommonsRequest:
    """One agent's announced withdrawal at one event, with the body it brings.

    ``event_counter`` is the AGENT's event clock (its last event's timestamp),
    not the environment's: the two diverge once N agents share one pasture,
    because the pool ticks once per round while each agent counts its own life.
    """

    agent_id: str
    requested: float
    event_counter: int
    drift_state: DriftState
    internal_state: InternalState


@dataclass(frozen=True)
class CommonsOutcome:
    """What the pasture delivered to one agent, and the body it leaves behind."""

    agent_id: str
    granted: float
    drift_state: DriftState
    internal_state: InternalState


def advance_commons(
    env_state: EnvironmentState,
    requests: list[CommonsRequest],
) -> tuple[EnvironmentState, dict[str, CommonsOutcome]]:
    """Regenerate, serve N announced withdrawals, then feed and scar each agent.

    Biology analogy: one pasture, several grazers. The stock grows, every
    animal takes what it announced as far as the stock allows, and whatever
    each one actually got is what feeds it.

    E1/E5 of the population design. The pool PHYSICS was already N-capable —
    ``step_pool``, ``realized_extractions`` and ``step_pool_with_crisis`` all
    take N-entry dicts, and the short-fall is already split in proportion to
    what each agent asked for (D-066). What was single-agent was this
    bookkeeping, because it lived inside a LangGraph node bound to one state.
    Splitting it out changes nothing for N=1 and is tested to stay that way.

    Order is load-bearing and matches what ``pool_step_node`` did before:
    regenerate and scar, read the ratio once for the whole round, then per
    agent read the ledger, write the commons row, apply the metabolic credit,
    and write the body row.
    """

    if not requests:
        raise ValueError("advance_commons needs at least one request")
    seen: set[str] = set()
    for request in requests:
        if request.agent_id in seen:
            raise ValueError(f"duplicate agent_id in commons step: {request.agent_id}")
        seen.add(request.agent_id)

    new_env, updated_drifts = step_pool_with_crisis(
        env_state,
        {r.agent_id: float(r.requested) for r in requests},
        {r.agent_id: r.drift_state for r in requests},
    )
    pool_ratio = get_pool_ratio(new_env)
    outcomes: dict[str, CommonsOutcome] = {}
    for request in requests:
        # What the pasture actually gave, read back from the ledger rather than
        # re-derived from the announcement: the two differ exactly when the pool
        # runs dry, which is the case the metabolic cost depends on (D-066).
        granted = realized_extraction_at(
            new_env,
            request.agent_id,
            int(new_env.event_counter),
        )
        _record_pool_event(
            agent_id=request.agent_id,
            event_counter=int(request.event_counter),
            extraction=granted,
            requested=float(request.requested),
            pool_ratio=pool_ratio,
            crisis=pool_ratio < POOL_CRISIS_THRESHOLD,
        )
        # Eat now, act on it next event: the evaluator already spent this
        # event's energy, so crediting here keeps the metabolic loop one tick
        # behind the act that earned it instead of rewriting the evaluator's
        # own patch.
        fed = request.internal_state.model_copy(
            update={
                "energy": max(
                    METRIC_MIN,
                    min(
                        METRIC_MAX,
                        request.internal_state.energy + metabolic_gain(granted),
                    ),
                )
            }
        )
        # Landmark instrumentation (D-070). Written here rather than in the
        # evaluator because this is the last node of the cycle: the harvest is
        # in, the metabolic credit is applied, and crisis trauma has already
        # scarred the drift map. Anywhere earlier and the row would describe an
        # event that was still happening.
        fed_drift = updated_drifts[request.agent_id]
        _record_body_event(
            agent_id=request.agent_id,
            event_counter=int(request.event_counter),
            energy=float(fed.energy),
            drift_flags=dict(fed_drift.flags),
            drift_magnitudes=dict(fed_drift.magnitudes),
        )
        outcomes[request.agent_id] = CommonsOutcome(
            agent_id=request.agent_id,
            granted=granted,
            drift_state=fed_drift,
            internal_state=fed,
        )
    return new_env, outcomes


def pool_step_node(state: DAUAgentState) -> dict[str, Any]:
    """Advance the shared pool, then apply crisis trauma when ratio is critical.

    The N=1 caller of ``advance_commons``. The two early returns below leave no
    ledger row, deliberately — a life with no society physics has no commons
    and no metabolic credit, and inventing a row for it would be the silent
    fallback §2.9 forbids. The reader treats a missing landmark row on a life
    long enough to have reached it as an abort, not as a default.

    Biology analogy: after the organism acts and the body consolidates the
    experience, the commons regenerates and is harvested. If stock falls below
    the crisis floor, somatic resource trauma scars the drift map. Skips when
    society physics is absent (env_state is None).
    """

    if state.env_state is None or not isinstance(state.env_state, EnvironmentState):
        return {}
    if not state.event_log:
        return {}

    decision = str(state.event_log[-1].payload.get("decision", ""))
    amount = (
        float(decision_to_extraction(decision))
        if decision
        else POOL_STEP_EMPTY_EXTRACTION
    )
    drift = state.drift_state
    if not isinstance(drift, DriftState):
        drift = DriftState()

    new_env, outcomes = advance_commons(
        state.env_state,
        [
            CommonsRequest(
                agent_id=state.agent_id,
                requested=amount,
                event_counter=int(state.event_log[-1].timestamp),
                drift_state=drift,
                internal_state=state.internal_state,
            )
        ],
    )
    outcome = outcomes[state.agent_id]
    return {
        "env_state": new_env,
        "drift_state": outcome.drift_state,
        "internal_state": outcome.internal_state,
    }


def should_continue(state: DAUAgentState) -> Literal["agent_node", "__end__"]:
    """Route on residual energy and event budget — keep living or end the run.

    Biology analogy: below the viability floor the organism can no longer act;
    above it, another sense-act cycle begins. MAX_EVENTS is the hard cap.
    Pool collapse termination is intentionally unwired (open item §17).

    A4 / D-066: AB_ENERGY_FLOOR used to pad effective energy for the whole run,
    and since the pad sits above TERMINATION_ENERGY the agent could not die —
    which is why survival read 1.0 on 120 of 120 arms and carried no
    information (D-060). The pad now covers only the birth transient: energy
    starts at METRIC_MAX with every load at zero, so the opening events say
    more about initial conditions than about how the agent lives. After
    METABOLIC_GRACE_EVENTS the floor is gone and running out of energy ends
    the life.
    """

    if len(state.event_log) >= MAX_EVENTS:
        return END  # type: ignore[return-value]
    raw_energy = float(state.internal_state.energy)
    in_grace = len(state.event_log) < METABOLIC_GRACE_EVENTS
    effective_energy = max(raw_energy, AB_ENERGY_FLOOR) if in_grace else raw_energy
    if effective_energy <= TERMINATION_ENERGY:
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
    """Compile social_pre → agent → evaluator → meta → pool_step → continue/end.

    Biology analogy: wire the sense-act-measure-regulate cycle into a closed
    loop that checkpoints after each node and ends when energy is exhausted.
    Meta-Observer runs after Delta is measured; its interventions apply on the
    next iteration. Pool step advances the commons and may scar resource drift
    under crisis. Social pre-node refreshes strategic expectation before each
    act when an opponent is present.
    """

    graph = StateGraph(DAUAgentState)
    graph.add_node(NODE_SOCIAL_PRE, social_pre_node)
    graph.add_node(NODE_AGENT, agent_node)
    graph.add_node(NODE_EVALUATOR, evaluator_node)
    graph.add_node(NODE_META_OBSERVER, meta_observer_node)
    graph.add_node(NODE_POOL_STEP, pool_step_node)
    graph.set_entry_point(NODE_SOCIAL_PRE)
    graph.add_edge(NODE_SOCIAL_PRE, NODE_AGENT)
    graph.add_edge(NODE_AGENT, NODE_EVALUATOR)
    graph.add_edge(NODE_EVALUATOR, NODE_META_OBSERVER)
    graph.add_edge(NODE_META_OBSERVER, NODE_POOL_STEP)
    graph.add_conditional_edges(
        NODE_POOL_STEP,
        should_continue,
        {
            NODE_AGENT: NODE_SOCIAL_PRE,
            END: END,
        },
    )
    if checkpointer is not None:
        return graph.compile(checkpointer=checkpointer)
    return graph.compile()


def build_event_graph(checkpointer: SqliteSaver | None = None) -> Any:
    """One event of one life, commons excluded: social_pre → agent → evaluator → meta.

    E2 of the population design, first step. The production graph closes its
    loop through ``pool_step_node`` and keeps cycling until the life ends. That
    is right for one agent and wrong for N: the pasture must tick ONCE per
    round, after every agent has acted, not once per agent. So two things move
    out to the caller — the commons step (``advance_commons``, E1/E5) and the
    loop itself (``should_continue`` decides who lives on).

    ⚠ This is the production cycle with wiring removed, NOT a second
    implementation: the same node functions run in the same order, and
    ``agent_node`` is still read from the module at build time so the Protocol
    C monkeypatch keeps working exactly as it does for ``build_graph``.
    """

    graph = StateGraph(DAUAgentState)
    graph.add_node(NODE_SOCIAL_PRE, social_pre_node)
    graph.add_node(NODE_AGENT, agent_node)
    graph.add_node(NODE_EVALUATOR, evaluator_node)
    graph.add_node(NODE_META_OBSERVER, meta_observer_node)
    graph.set_entry_point(NODE_SOCIAL_PRE)
    graph.add_edge(NODE_SOCIAL_PRE, NODE_AGENT)
    graph.add_edge(NODE_AGENT, NODE_EVALUATOR)
    graph.add_edge(NODE_EVALUATOR, NODE_META_OBSERVER)
    graph.add_edge(NODE_META_OBSERVER, END)
    if checkpointer is not None:
        return graph.compile(checkpointer=checkpointer)
    return graph.compile()


def step_agent_once(state: DAUAgentState, app: Any) -> DAUAgentState:
    """Advance one agent by exactly one event; the commons is not touched.

    ``app`` is a compiled ``build_event_graph``. Building it once and passing it
    in is deliberate: an outer loop over N agents and many rounds would
    otherwise recompile the same graph thousands of times, and a per-call build
    would also re-read ``agent_node`` mid-run, which is exactly the kind of
    quiet drift D-042 had to chase out of the adapter path.
    """

    result = app.invoke(state)
    if isinstance(result, DAUAgentState):
        return result
    if isinstance(result, dict):
        return DAUAgentState.model_validate(result)
    raise TypeError(f"unexpected event-graph result type: {type(result)!r}")


def _state_to_plain(values: Any) -> dict[str, Any]:
    """Normalize graph state values into a JSON-serializable dict."""

    if isinstance(values, DAUAgentState):
        plain = values.model_dump(mode="json")
        drift = values.drift_state
        if isinstance(drift, DriftState):
            plain["drift_state"] = {
                "flags": dict(drift.flags),
                "magnitudes": dict(drift.magnitudes),
            }
        return plain
    if isinstance(values, dict):
        plain: dict[str, Any] = {}
        for key, value in values.items():
            if isinstance(value, DriftState):
                plain[key] = {
                    "flags": dict(value.flags),
                    "magnitudes": dict(value.magnitudes),
                }
            elif hasattr(value, "model_dump"):
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
        store = initialize_memory(agent_id)
        _memory_stores[agent_id] = store
        bind_memory_store(agent_id, store)
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
        unbind_memory_store(agent_id)
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

    unbind_memory_store(agent_id)

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
