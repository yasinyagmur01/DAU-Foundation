"""Cognitive Level-of-Detail — System 1 (NPC) vs System 2 (LLM) switching.

Research: Dual-process ABM + Gemini report (Problem 3). LLM tokens are spent
only when T_cognitive crosses the escalate threshold. Below that, the agent
is a deterministic state machine. Hysteresis (T_COOLDOWN_STEPS) prevents jitter.

No LLM calls in this module. All decisions and thresholds are pure Python.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from .delta import DELTA_THRESHOLD_DEEP
from .state import METRIC_MAX, METRIC_MIN

# ---------------------------------------------------------------------------
# Cognitive LOD thresholds, weights, and NPC heuristics (no magic numbers)
# ---------------------------------------------------------------------------

T_COGNITIVE_ESCALATE: float = 0.65  # System 1 → System 2 threshold
T_COGNITIVE_DEESCALATE: float = 0.25  # System 2 → System 1 threshold
T_COOLDOWN_STEPS: int = 5  # consecutive low steps before deescalation

W_DELTA: float = 0.35  # weight: prediction error / delta magnitude
W_DRIFT: float = 0.25  # weight: max drift bias
W_SOCIAL: float = 0.20  # weight: coordination_friction
W_SCARCITY: float = 0.20  # weight: resource scarcity (1 - pool_ratio)

NPC_POOL_RATIO_CONSERVE: float = 0.3  # below: conserve regardless of domain

DOMAIN_RESOURCE_LOAD: str = "resource_load"
DOMAIN_SOCIAL_LOAD: str = "social_load"
DOMAIN_UNCERTAINTY_LOAD: str = "uncertainty_load"

NPC_ACTION_CONSERVE: str = "conserve"
NPC_ACTION_EXTRACT_MODERATE: str = "extract_moderate"
NPC_ACTION_COOPERATE: str = "cooperate"
NPC_ACTION_OBSERVE: str = "observe"
NPC_ACTION_MAINTAIN: str = "maintain"


class CognitiveMode(StrEnum):
    """Which cognitive process is currently driving the agent.

    Biology analogy: System 1 is a fast reflex circuit; System 2 is costly
    deliberative attention reserved for high prediction-error / stress events.
    """

    SYSTEM_1 = "system_1"
    SYSTEM_2 = "system_2"


@dataclass
class LODState:
    """Mutable-looking but immutably updated cognitive LOD snapshot.

    Biology analogy: whether the organism is on autopilot or paying attention,
    how urgent the current sensory load feels, and how long calm has lasted
    since the last escalation.
    """

    mode: CognitiveMode = CognitiveMode.SYSTEM_1
    t_cognitive: float = 0.0
    consecutive_low_steps: int = 0  # hysteresis counter for deescalation
    last_escalation_event: int = 0  # event_counter at last escalation


def _clamp(value: float) -> float:
    """Keep T_cognitive inside the unit interval."""

    return max(METRIC_MIN, min(METRIC_MAX, value))


def compute_t_cognitive(
    delta_magnitude: float,
    max_drift_bias: float,
    coordination_friction: float,
    pool_ratio: float,
) -> float:
    """Composite cognitive demand in [0, 1] from delta, drift, social, scarcity.

    T = W_DELTA * (delta_magnitude / DELTA_THRESHOLD_DEEP)
      + W_DRIFT * max_drift_bias
      + W_SOCIAL * coordination_friction
      + W_SCARCITY * (1 - pool_ratio)
    """

    raw = (
        W_DELTA * (delta_magnitude / DELTA_THRESHOLD_DEEP)
        + W_DRIFT * max_drift_bias
        + W_SOCIAL * coordination_friction
        + W_SCARCITY * (1.0 - pool_ratio)
    )
    return _clamp(raw)


def update_lod(
    lod: LODState,
    t_cognitive: float,
    now_counter: int,
) -> LODState:
    """Apply hysteresis: escalate immediately, deescalate only after cooldown.

    Returns a new LODState — never mutates the input.
    """

    if lod.mode == CognitiveMode.SYSTEM_1:
        if t_cognitive >= T_COGNITIVE_ESCALATE:
            return replace(
                lod,
                mode=CognitiveMode.SYSTEM_2,
                t_cognitive=t_cognitive,
                consecutive_low_steps=0,
                last_escalation_event=now_counter,
            )
        return replace(lod, t_cognitive=t_cognitive)

    # SYSTEM_2
    if t_cognitive <= T_COGNITIVE_DEESCALATE:
        consecutive = lod.consecutive_low_steps + 1
        if consecutive >= T_COOLDOWN_STEPS:
            return replace(
                lod,
                mode=CognitiveMode.SYSTEM_1,
                t_cognitive=t_cognitive,
                consecutive_low_steps=0,
            )
        return replace(
            lod,
            t_cognitive=t_cognitive,
            consecutive_low_steps=consecutive,
        )

    return replace(
        lod,
        t_cognitive=t_cognitive,
        consecutive_low_steps=0,
    )


def should_run_llm(lod: LODState) -> bool:
    """True only when the agent is in costly System 2 mode."""

    return lod.mode == CognitiveMode.SYSTEM_2


def npc_decision(
    agent_id: str,
    dominant_domain: str,
    pool_ratio: float,
) -> str:
    """Deterministic System 1 heuristic — no LLM.

    ``agent_id`` is reserved for future per-agent NPC policies; unused here.
    """

    _ = agent_id  # API surface; heuristic is currently domain/pool only

    if pool_ratio < NPC_POOL_RATIO_CONSERVE:
        return NPC_ACTION_CONSERVE
    if dominant_domain == DOMAIN_RESOURCE_LOAD:
        return NPC_ACTION_EXTRACT_MODERATE
    if dominant_domain == DOMAIN_SOCIAL_LOAD:
        return NPC_ACTION_COOPERATE
    if dominant_domain == DOMAIN_UNCERTAINTY_LOAD:
        return NPC_ACTION_OBSERVE
    return NPC_ACTION_MAINTAIN
