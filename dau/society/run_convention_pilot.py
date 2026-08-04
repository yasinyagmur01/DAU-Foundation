"""Spontaneous-convention micro-pilot harness — society closed loop (NPC baseline).

Closes Layer 4 gaps the graph never wired: multi-agent rounds, decision →
OUTCOME_* / extraction → record_interaction + step_pool, open utterance
transcript, deterministic convention metrics.

Mode: NPC System 1 only (no LLM, no trait injection, no LLM-as-judge).
LLM open-comm pilot is a later file once this harness is proven.

Empiric label: SENSOR_LABEL — results are under current Jaccard sensor
even though this NPC path does not invoke PE (future LLM path will).
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

# (agent_id, pool_ratio, transcript, round_index) → decision text
DecideFn = Callable[[str, float, list["Utterance"], int], str]

from dau.foundation.lod import (
    DOMAIN_RESOURCE_LOAD,
    DOMAIN_SOCIAL_LOAD,
    DOMAIN_UNCERTAINTY_LOAD,
    NPC_ACTION_CONSERVE,
    NPC_ACTION_COOPERATE,
    NPC_ACTION_EXTRACT_MODERATE,
    NPC_ACTION_MAINTAIN,
    NPC_ACTION_OBSERVE,
    npc_decision,
)
from dau.foundation.social import (
    OUTCOME_COORDINATE,
    OUTCOME_COOPERATE,
    OUTCOME_DEADLOCK,
    OUTCOME_DEFECT,
    InteractionRecord,
    SocialState,
    record_interaction,
    shannon_entropy,
)
from dau.foundation.semantic_similarity import SENSOR_LABEL
from dau.society.environment import (
    EnvironmentState,
    get_pool_ratio,
    step_pool,
)

# ---------------------------------------------------------------------------
# Pilot parameters (no magic numbers in logic)
# ---------------------------------------------------------------------------

N_AGENTS: int = 3
N_ROUNDS: int = 50
AGENT_ID_PREFIX: str = "convention-agent-"

PILOT_MODE: str = "npc_baseline"

# CPR harvest amounts — cooperate restrains, defect over-extracts
EXTRACTION_COOPERATE: float = 2.0
EXTRACTION_DEFECT: float = 8.0
EXTRACTION_COORDINATE: float = 1.0
EXTRACTION_DEADLOCK: float = 0.0
EXTRACTION_DEFAULT: float = 1.0

# Decision token → social outcome (NPC actions + keyword stubs)
DECISION_TO_OUTCOME: dict[str, str] = {
    NPC_ACTION_COOPERATE: OUTCOME_COOPERATE,
    NPC_ACTION_EXTRACT_MODERATE: OUTCOME_DEFECT,
    NPC_ACTION_CONSERVE: OUTCOME_COORDINATE,
    NPC_ACTION_OBSERVE: OUTCOME_COORDINATE,
    NPC_ACTION_MAINTAIN: OUTCOME_COORDINATE,
}

OUTCOME_TO_EXTRACTION: dict[str, float] = {
    OUTCOME_COOPERATE: EXTRACTION_COOPERATE,
    OUTCOME_DEFECT: EXTRACTION_DEFECT,
    OUTCOME_COORDINATE: EXTRACTION_COORDINATE,
    OUTCOME_DEADLOCK: EXTRACTION_DEADLOCK,
}

# Heterogeneous NPC domains so agents do not trivially clone one policy
AGENT_DOMAINS: tuple[str, ...] = (
    DOMAIN_RESOURCE_LOAD,
    DOMAIN_SOCIAL_LOAD,
    DOMAIN_UNCERTAINTY_LOAD,
)

# Convention detection: modal share ≥ threshold for CONVENTION_STREAK rounds
CONVENTION_MODAL_SHARE_MIN: float = 0.75
CONVENTION_STREAK_MIN: int = 5
MODAL_SHARE_EMPTY: float = 0.0
ENTROPY_EMPTY: float = 0.0

# Format sync: strip quantities so "collect 0.5 units" ≡ "collect 0.9 units"
FORMAT_NUMBER_RE: re.Pattern[str] = re.compile(r"\d+(?:\.\d+)?")
FORMAT_TEMPLATE_EMPTY: str = ""

# Restraint sync: cooperate/coordinate share (not universal defect)
RESTRAINT_OUTCOMES: frozenset[str] = frozenset(
    {OUTCOME_COOPERATE, OUTCOME_COORDINATE}
)

DEFECT_KEYWORDS: tuple[str, ...] = (
    "extract",
    "take",
    "defect",
    "refuse",
    "harvest",
    "gather",
    "collect",
)
COOPERATE_KEYWORDS: tuple[str, ...] = ("cooperate", "share", "talk", "social")
CONSERVE_KEYWORDS: tuple[str, ...] = (
    "conserve",
    "rest",
    "wait",
    "observe",
    "restrain",
    "spare",
)

# Parse explicit harvest quantities from free-text LLM announcements
HARVEST_UNITS_RE: re.Pattern[str] = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:units?|of the resource)",
    re.IGNORECASE,
)
HARVEST_PERCENT_RE: re.Pattern[str] = re.compile(
    r"(\d+(?:\.\d+)?)\s*%",
    re.IGNORECASE,
)
EXTRACTION_PARSE_MAX: float = 25.0
PERCENT_TO_POOL_SCALE: float = 100.0  # pct/100 * scale → absolute units



@dataclass
class Utterance:
    """One open-channel message for a round (decision text is the utterance)."""

    round_index: int
    agent_id: str
    text: str


@dataclass
class RoundRecord:
    """Deterministic census of one multi-agent round."""

    round_index: int
    decisions: dict[str, str]
    outcomes: dict[str, str]
    extractions: dict[str, float]
    outcome_entropy: float
    modal_outcome: str
    modal_share: float
    format_share: float
    restraint_share: float
    pool_after: float
    pool_ratio_after: float
    collapsed: bool


@dataclass
class PilotResult:
    """Full pilot summary — no LLM scoring."""

    mode: str
    sensor_label: str
    n_agents: int
    n_rounds: int
    rounds: list[RoundRecord] = field(default_factory=list)
    transcript: list[Utterance] = field(default_factory=list)
    # Legacy: any modal outcome streak (can be all-defect — ambiguous)
    convention_detected: bool = False
    convention_onset_round: int | None = None
    # Split metrics: linguistic format sync vs restraint/cooperate sync
    format_convention_detected: bool = False
    format_convention_onset_round: int | None = None
    restraint_convention_detected: bool = False
    restraint_convention_onset_round: int | None = None
    final_pool: float = 0.0
    collapsed: bool = False
    mean_outcome_entropy: float = 0.0
    mean_modal_share: float = 0.0
    mean_format_share: float = 0.0
    mean_restraint_share: float = 0.0


def agent_ids(n_agents: int = N_AGENTS) -> list[str]:
    """Stable agent id list for the pilot."""

    return [f"{AGENT_ID_PREFIX}{i}" for i in range(n_agents)]


def domain_for_agent(agent_id: str, n_agents: int = N_AGENTS) -> str:
    """Assign a fixed dominant domain from AGENT_DOMAINS by agent index."""

    index = int(agent_id.rsplit("-", maxsplit=1)[-1])
    return AGENT_DOMAINS[index % len(AGENT_DOMAINS)]


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    """True if any keyword appears in lowercased text."""

    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def decision_to_outcome(decision: str) -> str:
    """Map free-text / NPC decision to OUTCOME_* (deterministic, no LLM judge)."""

    token = decision.strip().lower()
    if token in DECISION_TO_OUTCOME:
        return DECISION_TO_OUTCOME[token]
    if _contains_any(token, DEFECT_KEYWORDS):
        return OUTCOME_DEFECT
    if _contains_any(token, COOPERATE_KEYWORDS):
        return OUTCOME_COOPERATE
    if _contains_any(token, CONSERVE_KEYWORDS):
        return OUTCOME_COORDINATE
    return OUTCOME_DEADLOCK


def decision_to_extraction(decision: str) -> float:
    """Map decision → harvest amount; prefer parsed quantity, else outcome table."""

    units_match = HARVEST_UNITS_RE.search(decision)
    if units_match is not None:
        return min(float(units_match.group(1)), EXTRACTION_PARSE_MAX)
    percent_match = HARVEST_PERCENT_RE.search(decision)
    if percent_match is not None:
        fraction = float(percent_match.group(1)) / 100.0
        return min(fraction * PERCENT_TO_POOL_SCALE, EXTRACTION_PARSE_MAX)
    outcome = decision_to_outcome(decision)
    return OUTCOME_TO_EXTRACTION.get(outcome, EXTRACTION_DEFAULT)


def _modal_outcome(outcomes: list[str]) -> tuple[str, float]:
    """Return (modal label, share in [0, 1]). Empty → deadlock @ 0 share."""

    if not outcomes:
        return OUTCOME_DEADLOCK, MODAL_SHARE_EMPTY
    counts = Counter(outcomes)
    modal, count = counts.most_common(1)[0]
    return modal, float(count) / float(len(outcomes))


def format_template(text: str) -> str:
    """Normalize announcement by replacing numbers with # (format sync key)."""

    stripped = text.strip().lower()
    if not stripped:
        return FORMAT_TEMPLATE_EMPTY
    return FORMAT_NUMBER_RE.sub("#", stripped)


def format_share(decisions: dict[str, str]) -> float:
    """Share of agents using the modal announcement template this round."""

    if not decisions:
        return MODAL_SHARE_EMPTY
    templates = [format_template(text) for text in decisions.values()]
    _modal, share = _modal_outcome(templates)
    return share


def restraint_share(outcomes: dict[str, str]) -> float:
    """Fraction of agents choosing cooperate/coordinate (not defect/deadlock)."""

    if not outcomes:
        return MODAL_SHARE_EMPTY
    restrained = sum(
        1 for outcome in outcomes.values() if outcome in RESTRAINT_OUTCOMES
    )
    return float(restrained) / float(len(outcomes))


def decide_npc(agent_id: str, pool_ratio: float, n_agents: int = N_AGENTS) -> str:
    """System 1 decision from heterogeneous domain + pool scarcity."""

    return npc_decision(
        agent_id=agent_id,
        dominant_domain=domain_for_agent(agent_id, n_agents=n_agents),
        pool_ratio=pool_ratio,
    )


def _pair_opponents(ids: list[str], agent_id: str) -> list[str]:
    """All other agents (all-to-all directed social updates)."""

    return [other for other in ids if other != agent_id]


def run_round(
    *,
    round_index: int,
    ids: list[str],
    env: EnvironmentState,
    social: SocialState,
    transcript: list[Utterance],
    decide_fn: DecideFn | None = None,
) -> tuple[EnvironmentState, SocialState, RoundRecord, list[Utterance]]:
    """One round: decide → utter → map → dyadic record → step_pool."""

    pool_ratio = get_pool_ratio(env)
    decisions: dict[str, str] = {}
    for agent_id in ids:
        if decide_fn is None:
            decision = decide_npc(agent_id, pool_ratio, n_agents=len(ids))
        else:
            decision = decide_fn(agent_id, pool_ratio, transcript, round_index)
        decisions[agent_id] = decision
        transcript.append(
            Utterance(round_index=round_index, agent_id=agent_id, text=decision)
        )

    outcomes = {
        agent_id: decision_to_outcome(decision)
        for agent_id, decision in decisions.items()
    }
    extractions = {
        agent_id: decision_to_extraction(decision)
        for agent_id, decision in decisions.items()
    }

    event_counter = int(env.event_counter) + 1
    for agent_id, outcome in outcomes.items():
        for opponent_id in _pair_opponents(ids, agent_id):
            social = record_interaction(
                social,
                InteractionRecord(
                    agent_id=agent_id,
                    opponent_id=opponent_id,
                    outcome=outcome,
                    event_counter=event_counter,
                ),
            )

    env = step_pool(env, extractions)
    outcome_list = list(outcomes.values())
    modal, share = _modal_outcome(outcome_list)
    record = RoundRecord(
        round_index=round_index,
        decisions=dict(decisions),
        outcomes=dict(outcomes),
        extractions=dict(extractions),
        outcome_entropy=shannon_entropy(outcome_list),
        modal_outcome=modal,
        modal_share=share,
        format_share=format_share(decisions),
        restraint_share=restraint_share(outcomes),
        pool_after=float(env.pool),
        pool_ratio_after=get_pool_ratio(env),
        collapsed=bool(env.collapsed),
    )
    return env, social, record, transcript


def detect_share_streak(
    shares: list[tuple[int, float]],
) -> tuple[bool, int | None]:
    """True if share ≥ threshold for CONVENTION_STREAK_MIN consecutive rounds."""

    streak = 0
    onset: int | None = None
    for round_index, share in shares:
        if share >= CONVENTION_MODAL_SHARE_MIN:
            if streak == 0:
                onset = round_index
            streak += 1
            if streak >= CONVENTION_STREAK_MIN:
                return True, onset
        else:
            streak = 0
            onset = None
    return False, None


def detect_convention(
    rounds: list[RoundRecord],
) -> tuple[bool, int | None]:
    """Legacy modal-outcome streak (ambiguous if modal is all-defect)."""

    return detect_share_streak(
        [(r.round_index, r.modal_share) for r in rounds]
    )


def run_convention_pilot(
    n_agents: int = N_AGENTS,
    n_rounds: int = N_ROUNDS,
    *,
    decide_fn: DecideFn | None = None,
    mode: str = PILOT_MODE,
) -> PilotResult:
    """Run convention pilot; default decide_fn is NPC baseline."""

    ids = agent_ids(n_agents)
    env = EnvironmentState()
    social = SocialState()
    transcript: list[Utterance] = []
    rounds: list[RoundRecord] = []

    for round_index in range(1, n_rounds + 1):
        env, social, record, transcript = run_round(
            round_index=round_index,
            ids=ids,
            env=env,
            social=social,
            transcript=transcript,
            decide_fn=decide_fn,
        )
        rounds.append(record)
        if env.collapsed:
            break

    detected, onset = detect_convention(rounds)
    format_detected, format_onset = detect_share_streak(
        [(r.round_index, r.format_share) for r in rounds]
    )
    restraint_detected, restraint_onset = detect_share_streak(
        [(r.round_index, r.restraint_share) for r in rounds]
    )
    entropies = [r.outcome_entropy for r in rounds]
    shares = [r.modal_share for r in rounds]
    format_shares = [r.format_share for r in rounds]
    restraint_shares = [r.restraint_share for r in rounds]
    mean_entropy = (
        sum(entropies) / float(len(entropies)) if entropies else ENTROPY_EMPTY
    )
    mean_share = (
        sum(shares) / float(len(shares)) if shares else MODAL_SHARE_EMPTY
    )
    mean_format = (
        sum(format_shares) / float(len(format_shares))
        if format_shares
        else MODAL_SHARE_EMPTY
    )
    mean_restraint = (
        sum(restraint_shares) / float(len(restraint_shares))
        if restraint_shares
        else MODAL_SHARE_EMPTY
    )

    return PilotResult(
        mode=mode,
        sensor_label=SENSOR_LABEL,
        n_agents=n_agents,
        n_rounds=len(rounds),
        rounds=rounds,
        transcript=transcript,
        convention_detected=detected,
        convention_onset_round=onset,
        format_convention_detected=format_detected,
        format_convention_onset_round=format_onset,
        restraint_convention_detected=restraint_detected,
        restraint_convention_onset_round=restraint_onset,
        final_pool=float(env.pool),
        collapsed=bool(env.collapsed),
        mean_outcome_entropy=mean_entropy,
        mean_modal_share=mean_share,
        mean_format_share=mean_format,
        mean_restraint_share=mean_restraint,
    )


def pilot_summary_dict(result: PilotResult) -> dict[str, Any]:
    """JSON-serializable summary for logging / later A/B comparison."""

    return {
        "mode": result.mode,
        "sensor_label": result.sensor_label,
        "n_agents": result.n_agents,
        "n_rounds": result.n_rounds,
        "convention_detected": result.convention_detected,
        "convention_onset_round": result.convention_onset_round,
        "format_convention_detected": result.format_convention_detected,
        "format_convention_onset_round": result.format_convention_onset_round,
        "restraint_convention_detected": result.restraint_convention_detected,
        "restraint_convention_onset_round": result.restraint_convention_onset_round,
        "final_pool": result.final_pool,
        "collapsed": result.collapsed,
        "mean_outcome_entropy": result.mean_outcome_entropy,
        "mean_modal_share": result.mean_modal_share,
        "mean_format_share": result.mean_format_share,
        "mean_restraint_share": result.mean_restraint_share,
    }


def main() -> None:
    """CLI entry: print labeled NPC convention baseline summary."""

    result = run_convention_pilot()
    summary = pilot_summary_dict(result)
    print("=== DAU convention micro-pilot (NPC baseline) ===")
    for key, value in summary.items():
        print(f"{key}={value}")
    if result.rounds:
        first = result.rounds[0]
        last = result.rounds[-1]
        print(
            f"first_round: entropy={first.outcome_entropy:.3f} "
            f"modal={first.modal_outcome} share={first.modal_share:.3f} "
            f"pool={first.pool_after:.2f}"
        )
        print(
            f"last_round: entropy={last.outcome_entropy:.3f} "
            f"modal={last.modal_outcome} share={last.modal_share:.3f} "
            f"pool={last.pool_after:.2f}"
        )


if __name__ == "__main__":
    main()
