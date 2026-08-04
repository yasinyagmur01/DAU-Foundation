"""System 2→1 de-escalation nuance-loss micro-pilot.

Documents the accepted limit: when LOD drops to System 1, LLM decision
history is not summarized into NPC heuristics — behavioral variance collapses
to the deterministic npc_decision rule set.

No trait injection. No LLM-as-judge. Metrics are deterministic Python.
Optional Groq path for live System-2 utterances; default uses scripted
System-2 decisions so CI stays offline.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from dau.foundation.lod import (
    DOMAIN_RESOURCE_LOAD,
    NPC_POOL_RATIO_CONSERVE,
    CognitiveMode,
    LODState,
    npc_decision,
    update_lod,
)
from dau.society.run_convention_pilot import SENSOR_LABEL

# ---------------------------------------------------------------------------
# Pilot parameters (no magic numbers in logic)
# ---------------------------------------------------------------------------

N_PRE_STEPS: int = 10
N_POST_STEPS: int = 10
POOL_RATIO_ABUNDANT: float = 0.8
POOL_RATIO_SCARCE: float = NPC_POOL_RATIO_CONSERVE - 0.05
DOMINANT_DOMAIN: str = DOMAIN_RESOURCE_LOAD
AGENT_ID: str = "lod-nuance-0"

# Scripted System-2 utterances (heterogeneous) — stand-in for LLM diversity
SYSTEM2_SCRIPTED: tuple[str, ...] = (
    "I carefully extract a moderate share from the commons.",
    "I take a little more resource while watching the pool.",
    "I harvest lightly and leave slack for others.",
    "I extract_moderate because scarcity is not urgent.",
    "I gather supplies cautiously from the shared pool.",
    "I take resources but announce restraint in tone.",
    "I extract only what my energy load seems to demand.",
    "I pull a modest amount and reassess next round.",
    "I take from the commons with a short public notice.",
    "I extract_moderate again under abundant pool_ratio.",
)


@dataclass
class NuancePilotResult:
    """Variance before vs after forced System 1 lock."""

    sensor_label: str
    pre_mode: str
    post_mode: str
    pre_unique_decisions: int
    post_unique_decisions: int
    pre_decisions: list[str] = field(default_factory=list)
    post_decisions: list[str] = field(default_factory=list)
    nuance_loss_detected: bool = False


def _unique_count(decisions: list[str]) -> int:
    """Number of distinct decision strings."""

    return len(Counter(decisions))


def run_nuance_loss_pilot(
    *,
    system2_decisions: tuple[str, ...] = SYSTEM2_SCRIPTED,
    n_pre: int = N_PRE_STEPS,
    n_post: int = N_POST_STEPS,
    pool_ratio: float = POOL_RATIO_ABUNDANT,
) -> NuancePilotResult:
    """Compare decision diversity in System 2 vs pinned System 1.

    Biology analogy: cortical deliberation produces varied acts; dropping to
    brainstem reflexes collapses the repertoire to one heuristic.
    """

    pre = [system2_decisions[i % len(system2_decisions)] for i in range(n_pre)]
    post = [
        npc_decision(AGENT_ID, DOMINANT_DOMAIN, pool_ratio) for _ in range(n_post)
    ]
    pre_unique = _unique_count(pre)
    post_unique = _unique_count(post)
    return NuancePilotResult(
        sensor_label=SENSOR_LABEL,
        pre_mode=CognitiveMode.SYSTEM_2.value,
        post_mode=CognitiveMode.SYSTEM_1.value,
        pre_unique_decisions=pre_unique,
        post_unique_decisions=post_unique,
        pre_decisions=pre,
        post_decisions=post,
        nuance_loss_detected=pre_unique > post_unique,
    )


def demonstrate_lod_deescalation() -> LODState:
    """Show update_lod can move System 2 → System 1 after cooldown lows."""

    lod = LODState(mode=CognitiveMode.SYSTEM_2, t_cognitive=1.0)
    # Drive T below deescalate threshold for T_COOLDOWN_STEPS consecutive updates
    from dau.foundation.lod import T_COGNITIVE_DEESCALATE, T_COOLDOWN_STEPS

    low_t = T_COGNITIVE_DEESCALATE - 0.01
    for step in range(T_COOLDOWN_STEPS):
        lod = update_lod(lod, low_t, now_counter=step + 1)
    return lod


def pilot_summary_dict(result: NuancePilotResult) -> dict[str, Any]:
    """JSON-friendly summary."""

    return {
        "sensor_label": result.sensor_label,
        "pre_mode": result.pre_mode,
        "post_mode": result.post_mode,
        "pre_unique_decisions": result.pre_unique_decisions,
        "post_unique_decisions": result.post_unique_decisions,
        "nuance_loss_detected": result.nuance_loss_detected,
        "post_npc_action": result.post_decisions[0] if result.post_decisions else "",
    }


def main() -> None:
    """CLI: print nuance-loss pilot + LOD deescalation check."""

    result = run_nuance_loss_pilot()
    summary = pilot_summary_dict(result)
    print("=== DAU System 2→1 nuance-loss micro-pilot ===")
    for key, value in summary.items():
        print(f"{key}={value}")
    lod = demonstrate_lod_deescalation()
    print(f"lod_after_cooldown_mode={lod.mode.value}")
    print(
        f"scarce_npc={npc_decision(AGENT_ID, DOMINANT_DOMAIN, POOL_RATIO_SCARCE)}"
    )


if __name__ == "__main__":
    main()
