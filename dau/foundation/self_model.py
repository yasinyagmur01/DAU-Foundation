"""Unified self-model (S_self) — telemetry consolidation for metacognition.

Biology analogy: S_self is the organism's structured readout of its own
homeostatic and cognitive signals. The Meta-Observer reads this telemetry
only — never LLM-generated narrative text — to close the control loop.

Layer 5A: consolidates existing state fields; invents no new sensors.
"""

from __future__ import annotations

from statistics import fmean
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field

from dau.generation.fitness import compute_fitness
from dau.society.environment import EnvironmentState, agent_delta_pool

from .drift import DriftState
from .emotional_weight import EmotionalWeight, compute_emotional_weight
from .lod import LODState
from .state import DAUAgentState, METRIC_MIN

# ---------------------------------------------------------------------------
# Metacognitive history / calibration (no magic numbers in logic)
# ---------------------------------------------------------------------------

META_HISTORY_SIZE: int = 10
EPSILON: float = 1e-6
M_RATIO_OPTIMAL: float = 1.0
M_RATIO_LOW_THRESHOLD: float = 0.6  # below → metacognitive intervention needed

DEFAULT_DELTA_CURRENT: float = 0.0
DEFAULT_T_COGNITIVE: float = 0.0
DEFAULT_F_AGENT: float = 0.0
DEFAULT_DELTA_POOL: float = 0.0
EMPTY_DELTA_HISTORY_MEAN: float = 0.0
MIN_SURVIVAL_DENOMINATOR: int = 1

# Retrieval score keys used by Layer 1 bridge / Layer 3 inheritance entries.
MEMORY_SCORE_KEY: str = "memory_score"
MEMORY_SCORE_ALT_KEY: str = "score"


class SelfModel(BaseModel):
    """Structured self-representation assembled from existing DAU telemetry.

    Biology analogy: a momentary self-map — how hard the last swing hit, how
    the recent delta trajectory looks, which niches are scarred, what the body
    is prioritizing, how costly cognition feels, what memory cues scored, and
    how fit the lineage currently reads. m_ratio is the metacognitive
    calibration proxy (meta-d' / d').
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    delta_current: float = Field(
        ...,
        description="Latest Delta magnitude from evaluator_node / delta_log.",
    )
    delta_history: list[float] = Field(
        ...,
        description=f"Last {META_HISTORY_SIZE} delta magnitudes (oldest→newest).",
    )
    drift_state: DriftState = Field(
        ...,
        description="Per-domain trauma drift flags and magnitudes (Layer 2).",
    )
    emotional_weight: EmotionalWeight = Field(
        ...,
        description="Somatic marker weights from latest delta (Layer 2).",
    )
    t_cognitive: float = Field(
        ...,
        description="Current T_cognitive from LOD engine (Layer 4).",
    )
    memory_retrieval_scores: list[float] = Field(
        ...,
        description="Recent retrieval scores from Layer 1 / retrieval_context.",
    )
    f_agent: float = Field(
        ...,
        description="Ancestral survival fitness F_agent (Layer 4).",
    )
    generation_count: int = Field(
        ...,
        description="Lineage generation index from DAUAgentState.generation.",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def m_ratio(self) -> float:
        """Metacognitive calibration proxy: mean(delta_history) / (delta_current + ε)."""

        if self.delta_history:
            history_mean = float(fmean(self.delta_history))
        else:
            history_mean = EMPTY_DELTA_HISTORY_MEAN
        return history_mean / (float(self.delta_current) + EPSILON)


def _copy_drift_state(raw: Any) -> DriftState:
    """Snapshot DriftState so SelfModel does not alias mutable agent state."""

    if isinstance(raw, DriftState):
        return DriftState(
            flags=dict(raw.flags),
            magnitudes=dict(raw.magnitudes),
        )
    return DriftState()


def _resolve_t_cognitive(state: DAUAgentState) -> float:
    """Read T_cognitive from lod_state when present, else the birth default."""

    lod = state.lod_state
    if isinstance(lod, LODState):
        return float(lod.t_cognitive)
    return DEFAULT_T_COGNITIVE


def _resolve_emotional_weight(state: DAUAgentState) -> EmotionalWeight:
    """Derive EmotionalWeight from the latest delta; empty markers at birth."""

    if not state.delta_log:
        return EmotionalWeight()
    return compute_emotional_weight(state.delta_log[-1], state.internal_state)


def _resolve_memory_retrieval_scores(state: DAUAgentState) -> list[float]:
    """Collect recent memory scores from retrieval_context entries."""

    scores: list[float] = []
    for entry in state.retrieval_context:
        if not isinstance(entry, dict):
            continue
        if MEMORY_SCORE_KEY in entry:
            scores.append(float(entry[MEMORY_SCORE_KEY]))
        elif MEMORY_SCORE_ALT_KEY in entry:
            scores.append(float(entry[MEMORY_SCORE_ALT_KEY]))
    return scores[-META_HISTORY_SIZE:]


def f_agent_inputs(state: DAUAgentState, t_generation: int) -> dict[str, float]:
    """The quantities compute_fitness reads, straight off the state.

    Public so a results file can report what F_agent was computed FROM
    without re-deriving it — the pilot returned f_agent=0.000 for all nine
    lineages (D-034) and the score alone cannot distinguish a genuinely
    unfit cohort from a term that clamped. Anything reporting these must
    call this, not rebuild the reads (CLAUDE.md 2.8).

    ``t_generation`` is the generation's event BUDGET and the caller must
    supply it — there is no default, because the only value this function can
    reach on its own is the agent's own lifespan, which is what it used to
    pass. That made the survival term t_survived/t_survived ≡ 1.0 for every
    lineage ever scored: the pilot's spread came entirely from the pool term
    (0.3·(1−130.80/100)+0.3 = 0.2076 and 0.3·(1−62.17/100)+0.3 = 0.4135,
    both exact to seven digits), contradicting compute_fitness's own docstring
    and D-068's reading of it. Since D-066 a life can end early, so the
    fraction of the span endured is a real measurement and the budget is
    genuinely outside information (K4-b, D-070).
    """

    env = state.env_state
    t_survived = len(state.event_log)
    return {
        "energy_final": float(state.internal_state.energy),
        "delta_pool": (
            float(agent_delta_pool(env, state.agent_id))
            if isinstance(env, EnvironmentState)
            else DEFAULT_DELTA_POOL
        ),
        "t_survived": float(t_survived),
        "t_generation": float(max(int(t_generation), MIN_SURVIVAL_DENOMINATOR)),
    }


def _resolve_f_agent(state: DAUAgentState, t_generation: int) -> float:
    """Compute live F_agent from energy, pool extraction, and event survival."""

    inputs = f_agent_inputs(state, t_generation)
    return float(
        compute_fitness(
            energy_final=inputs["energy_final"],
            delta_pool=inputs["delta_pool"],
            t_survived=int(inputs["t_survived"]),
            t_generation=int(inputs["t_generation"]),
        )
    )


def build_self_model(state: DAUAgentState, t_generation: int) -> SelfModel:
    """Assemble S_self from existing DAUAgentState telemetry fields only.

    Biology analogy: the Meta-Observer never invents new senses — it only
    binds the instruments already wired into the organism into one map.

    ``t_generation`` is threaded through to F_agent; see f_agent_inputs for
    why it cannot be defaulted.
    """

    magnitudes = [
        float(record.magnitude) for record in state.delta_log[-META_HISTORY_SIZE:]
    ]
    delta_current = magnitudes[-1] if magnitudes else DEFAULT_DELTA_CURRENT

    return SelfModel(
        delta_current=delta_current,
        delta_history=list(magnitudes),
        drift_state=_copy_drift_state(state.drift_state),
        emotional_weight=_resolve_emotional_weight(state),
        t_cognitive=_resolve_t_cognitive(state),
        memory_retrieval_scores=_resolve_memory_retrieval_scores(state),
        f_agent=_resolve_f_agent(state, t_generation),
        generation_count=int(state.generation),
    )


DEMO_T_GENERATION: int = 10


if __name__ == "__main__":
    from .constraints import build_default_constraints

    demo = DAUAgentState(
        agent_id="self-model-demo-0",
        environment=build_default_constraints(),
    )
    self_model = build_self_model(demo, DEMO_T_GENERATION)
    print(
        f"OK — SelfModel built; delta_current={self_model.delta_current}, "
        f"m_ratio={self_model.m_ratio}, f_agent={self_model.f_agent}, "
        f"generation_count={self_model.generation_count}, "
        f"energy_floor_check={METRIC_MIN}"
    )
