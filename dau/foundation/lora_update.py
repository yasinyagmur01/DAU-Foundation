"""Generation-end lived-trace LoRA update (optional, flag-gated).

Biology analogy: when one life ends, somatic scars and prediction errors are
condensed into a small per-agent adapter graft — never a shared personality
written by the designer.

Default DAU_LORA_ENABLED=0 → no-op.
Per-agent save path: dau_runs/adapters/{agent_id}/ (Punica pattern).
"""

from __future__ import annotations

import json
import os
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from dau.foundation.constraints import SNR_MARGIN_FLOOR
from dau.foundation.delta import is_trauma
from dau.foundation.drift import DriftState, get_drift_bias
from dau.foundation.nli_filter import is_genuine_polarity_pair
from dau.foundation.state import DAUAgentState, DeltaRecord

# ---------------------------------------------------------------------------
# LoRA update flags and signal constants (no magic numbers in logic)
# ---------------------------------------------------------------------------

LORA_ENABLED_ENV: str = "DAU_LORA_ENABLED"
LORA_ENABLED_DEFAULT: str = "0"
LORA_TRUTHY: frozenset[str] = frozenset({"1", "true", "TRUE", "yes", "YES"})

LIVED_TRACES_FILE_NAME: str = "lived_traces.jsonl"
ADAPTER_META_FILE_NAME: str = "lora_update_meta.json"

DRIFT_BIAS_DOMAINS: tuple[str, ...] = (
    "energy",
    "resource",
    "social",
    "uncertainty",
)

LOSS_WEIGHT_BASE: float = 1.0
TRAUMA_WEIGHT_BONUS: float = 0.25
DRIFT_WEIGHT_SCALE: float = 0.1
LOSS_WEIGHT_MIN: float = 0.05
LOSS_WEIGHT_MAX: float = 2.0

PROMPT_TEMPLATE: str = (
    "Lived scalars: pe={pe:.3f} magnitude={magnitude:.3f} "
    "class={delta_class} trauma={trauma} drift_sum={drift_sum:.3f}"
)
COMPLETION_FALLBACK: str = "continue"
DECISION_PAYLOAD_KEY: str = "decision"
EVENT_TYPE_DECISION: str = "agent_decision"

SIGNAL_V1_ID: str = "pe_delta_trauma_drift_v1"
SIGNAL_V2_ID: str = "pe_ranked_pref_v2"
PREF_TRACES_FILE_NAME: str = "preference_pairs.jsonl"
# Endogenous preference: lower lived PE beats higher lived PE. No designer
# value sentence, no fixed reject template (those were recipe A — trait-
# adjacent and mini-tested to inflate PE without teaching contrast).
PREF_LIVED_CONTEXT_TEMPLATE: str = (
    "Lived preference: pe={pe_chosen:.3f} decision over pe={pe_rejected:.3f}"
)
PE_RANK_MIN_GAP: float = 1e-6

# total_candidates/rejected are per-candidate (pre-dedup); passed is
# per-event (post PE-rank dedup) — these do not sum to total_candidates
# by design.
NLI_FILTER_STATS: dict[str, int] = {
    "total_candidates": 0,
    "passed": 0,
    "rejected": 0,
}

# D-030. Reported, not just applied: MIN_PAIRS is uncalibrated (I1.5), so
# without this count "few but strong pairs" and "the filter emptied the
# training set" look identical in the results JSON.
SNR_FILTER_STATS: dict[str, int] = {
    "total_candidates": 0,
    "rejected_below_margin": 0,
}


@dataclass
class LivedTraceExample:
    """One generation-end training row derived only from lived scalars."""

    event_counter: int
    prediction_error: float
    delta_magnitude: float
    delta_class: str
    trauma_flag: bool
    drift_sum: float
    loss_weight: float
    prompt: str
    completion: str


@dataclass
class PreferencePair:
    """Lived-PE preference row — chosen has lower life PE than rejected."""

    prompt: str
    chosen: str
    rejected: str
    pe_chosen: float
    pe_rejected: float
    event_counter: int = 0


@dataclass
class LoraUpdateResult:
    """Outcome of an optional generation-end LoRA update attempt."""

    enabled: bool
    skipped: bool
    reason: str
    example_count: int = 0
    adapter_dir: str | None = None
    trained: bool = False
    examples: list[LivedTraceExample] = field(default_factory=list)
    agent_id: str = "default"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def is_lora_enabled() -> bool:
    """True when DAU_LORA_ENABLED is truthy (default off)."""

    raw = os.environ.get(LORA_ENABLED_ENV, LORA_ENABLED_DEFAULT).strip()
    if not raw:
        return False
    return raw in LORA_TRUTHY


def _clamp_weight(value: float) -> float:
    return max(LOSS_WEIGHT_MIN, min(LOSS_WEIGHT_MAX, float(value)))


def compute_loss_weight(
    *,
    prediction_error: float,
    trauma_flag: bool,
    drift_sum: float,
) -> float:
    """Deterministic scalar weight from PE / trauma / drift (no F_agent)."""

    weight = LOSS_WEIGHT_BASE - float(prediction_error)
    if trauma_flag:
        weight += TRAUMA_WEIGHT_BONUS
    weight += DRIFT_WEIGHT_SCALE * float(drift_sum)
    return _clamp_weight(weight)


def _drift_sum(drift_state: Any) -> float:
    if not isinstance(drift_state, DriftState):
        drift_state = DriftState()
    total = 0.0
    for domain in DRIFT_BIAS_DOMAINS:
        total += float(get_drift_bias(drift_state, domain))
    return total


def _decision_by_counter(agent_state: DAUAgentState) -> dict[int, str]:
    mapping: dict[int, str] = {}
    for event in agent_state.event_log:
        if event.event_type != EVENT_TYPE_DECISION:
            continue
        payload = event.payload if isinstance(event.payload, dict) else {}
        decision = payload.get(DECISION_PAYLOAD_KEY)
        if decision is None:
            continue
        mapping[int(event.timestamp)] = str(decision).strip() or COMPLETION_FALLBACK
    return mapping


def build_lived_trace_examples(
    agent_state: DAUAgentState,
    pe_event_log: list[dict[str, Any]] | None = None,
) -> list[LivedTraceExample]:
    """Build SFT rows from PE / delta / trauma / drift — no F_agent filter."""

    pe_rows = list(pe_event_log) if pe_event_log is not None else []
    pe_by_counter: dict[int, dict[str, Any]] = {}
    for row in pe_rows:
        pe_by_counter[int(row["event_counter"])] = row

    decisions = _decision_by_counter(agent_state)
    drift_total = _drift_sum(agent_state.drift_state)
    examples: list[LivedTraceExample] = []

    deltas: list[DeltaRecord] = list(agent_state.delta_log)
    if not deltas and pe_by_counter:
        for counter, row in sorted(pe_by_counter.items()):
            pe = float(row["prediction_error"])
            magnitude = float(row.get("delta_magnitude", 0.0))
            delta_class = str(row.get("delta_class", "NO_TRACE"))
            trauma_flag = delta_class == "TRAUMA"
            weight = compute_loss_weight(
                prediction_error=pe,
                trauma_flag=trauma_flag,
                drift_sum=drift_total,
            )
            prompt = PROMPT_TEMPLATE.format(
                pe=pe,
                magnitude=magnitude,
                delta_class=delta_class,
                trauma=trauma_flag,
                drift_sum=drift_total,
            )
            examples.append(
                LivedTraceExample(
                    event_counter=counter,
                    prediction_error=pe,
                    delta_magnitude=magnitude,
                    delta_class=delta_class,
                    trauma_flag=trauma_flag,
                    drift_sum=drift_total,
                    loss_weight=weight,
                    prompt=prompt,
                    completion=decisions.get(counter, COMPLETION_FALLBACK),
                )
            )
        return examples

    for record in deltas:
        counter = int(record.timestamp)
        pe_row = pe_by_counter.get(counter)
        if pe_row is not None:
            pe = float(pe_row["prediction_error"])
            delta_class = str(pe_row.get("delta_class", record.affected_domain))
            magnitude = float(pe_row.get("delta_magnitude", record.magnitude))
        else:
            pe = float(record.magnitude)
            magnitude = float(record.magnitude)
            delta_class = str(record.affected_domain)
        trauma_flag = bool(is_trauma(record))
        weight = compute_loss_weight(
            prediction_error=pe,
            trauma_flag=trauma_flag,
            drift_sum=drift_total,
        )
        prompt = PROMPT_TEMPLATE.format(
            pe=pe,
            magnitude=magnitude,
            delta_class=delta_class,
            trauma=trauma_flag,
            drift_sum=drift_total,
        )
        examples.append(
            LivedTraceExample(
                event_counter=counter,
                prediction_error=pe,
                delta_magnitude=magnitude,
                delta_class=delta_class,
                trauma_flag=trauma_flag,
                drift_sum=drift_total,
                loss_weight=weight,
                prompt=prompt,
                completion=decisions.get(counter, COMPLETION_FALLBACK),
            )
        )
    return examples


def build_pe_ranked_pairs(
    examples: list[LivedTraceExample],
) -> list[PreferencePair]:
    """Rank lived decisions by PE, then keep only genuine polarity pairs.

    Chosen = lower lived prediction_error, rejected = higher. One strongest-
    contrast pair is kept per low-PE event so the train set stays O(n) rather
    than O(n²). Each PE-ranked candidate must also pass
    ``is_genuine_polarity_pair`` (contradiction ≥ NLI_CONTRADICTION_THRESHOLD
    from constraints / nli_filter); non-genuine pairs are dropped and counted
    in NLI_FILTER_STATS["rejected"]. Preference direction remains PE-defined;
    NLI only gates linguistic polarity.
    """

    usable = [
        ex
        for ex in examples
        if (ex.completion or COMPLETION_FALLBACK).strip()
        and (ex.completion or COMPLETION_FALLBACK).strip() != COMPLETION_FALLBACK
    ]
    best_by_event: dict[int, PreferencePair] = {}
    for index, left in enumerate(usable):
        for right in usable[index + 1 :]:
            pe_left = float(left.prediction_error)
            pe_right = float(right.prediction_error)
            if abs(pe_left - pe_right) < PE_RANK_MIN_GAP:
                continue
            if pe_left <= pe_right:
                low, high = left, right
            else:
                low, high = right, left
            chosen = (low.completion or COMPLETION_FALLBACK).strip()
            rejected = (high.completion or COMPLETION_FALLBACK).strip()
            if not chosen or not rejected or chosen == rejected:
                continue

            # D-030: signal magnitude before linguistic polarity. A margin
            # inside the noise band teaches nothing however contradictory the
            # two sentences read, and this gate is cheaper than the NLI pass.
            margin = float(high.prediction_error) - float(low.prediction_error)
            SNR_FILTER_STATS["total_candidates"] += 1
            if margin < SNR_MARGIN_FLOOR:
                SNR_FILTER_STATS["rejected_below_margin"] += 1
                continue

            NLI_FILTER_STATS["total_candidates"] += 1
            if not is_genuine_polarity_pair(chosen, rejected):
                NLI_FILTER_STATS["rejected"] += 1
                continue
            pe_chosen = float(low.prediction_error)
            pe_rejected = float(high.prediction_error)
            gap = pe_rejected - pe_chosen
            pair = PreferencePair(
                prompt=PREF_LIVED_CONTEXT_TEMPLATE.format(
                    pe_chosen=pe_chosen,
                    pe_rejected=pe_rejected,
                ),
                chosen=chosen,
                rejected=rejected,
                pe_chosen=pe_chosen,
                pe_rejected=pe_rejected,
                event_counter=int(low.event_counter),
            )
            previous = best_by_event.get(pair.event_counter)
            if previous is None or gap > (previous.pe_rejected - previous.pe_chosen):
                best_by_event[pair.event_counter] = pair
    NLI_FILTER_STATS["passed"] += len(best_by_event)
    return list(best_by_event.values())


def shuffle_preference_pairs(
    pairs: list[PreferencePair],
    *,
    seed: int,
) -> list[PreferencePair]:
    """Control: swap chosen/rejected (wrong PE preference direction)."""

    rng = random.Random(seed)
    out: list[PreferencePair] = []
    for pair in pairs:
        if rng.random() < 0.5:
            out.append(
                PreferencePair(
                    prompt=pair.prompt,
                    chosen=pair.rejected,
                    rejected=pair.chosen,
                    pe_chosen=pair.pe_rejected,
                    pe_rejected=pair.pe_chosen,
                    event_counter=pair.event_counter,
                )
            )
        else:
            out.append(pair)
    if pairs and out == pairs:
        first = pairs[0]
        out[0] = PreferencePair(
            prompt=first.prompt,
            chosen=first.rejected,
            rejected=first.chosen,
            pe_chosen=first.pe_rejected,
            pe_rejected=first.pe_chosen,
            event_counter=first.event_counter,
        )
    return out


def run_micro_train_preference_step(
    pairs: list[PreferencePair] | None = None,
    *,
    agent_id: str = "default",
    model: Any | None = None,
) -> dict[str, Any]:
    """Generation-end preference micro-train + per-agent adapter save.

    DAU_LORA_ENABLED=0 → return early before any training or saving.
    After train, saves to dau_runs/adapters/{agent_id}/ via save_agent_adapter.
    """

    if not is_lora_enabled():
        return {
            "trained": False,
            "skipped": True,
            "reason": f"{LORA_ENABLED_ENV}=0 (default) — no train/save.",
            "agent_id": agent_id,
        }

    from dau.foundation.local_llm import (
        get_adapter_path,
        get_loaded_model,
        run_micro_train_preference_step as _local_train,
        save_agent_adapter,
    )

    active = model if model is not None else get_loaded_model()
    result = _local_train(pairs=pairs, agent_id=agent_id, model=active)
    # Explicit per-agent save after train path (idempotent if local already saved).
    if active is not None and not result.get("skipped", True):
        save_agent_adapter(active, agent_id)
        result["adapter_dir"] = str(get_adapter_path(agent_id))
    return result


def lora_update(
    agent_state: DAUAgentState,
    *,
    pe_event_log: list[dict[str, Any]] | None = None,
    generation: int = 0,
    force: bool = False,
    agent_id: str | None = None,
) -> LoraUpdateResult:
    """Optional generation-end hook: write traces; train per-agent adapter."""

    resolved_id = str(agent_id or agent_state.agent_id or "default")
    if not force and not is_lora_enabled():
        return LoraUpdateResult(
            enabled=False,
            skipped=True,
            reason=f"{LORA_ENABLED_ENV}=0 (default) — generation-end unchanged.",
            agent_id=resolved_id,
        )

    examples = build_lived_trace_examples(agent_state, pe_event_log)
    if not examples:
        return LoraUpdateResult(
            enabled=True,
            skipped=True,
            reason="No lived-trace examples to train on.",
            example_count=0,
            agent_id=resolved_id,
        )

    pairs = build_pe_ranked_pairs(examples)
    train_result = run_micro_train_preference_step(
        pairs=pairs,
        agent_id=resolved_id,
    )
    return LoraUpdateResult(
        enabled=True,
        skipped=bool(train_result.get("skipped", True)),
        reason=str(train_result.get("reason", "")),
        example_count=len(examples),
        adapter_dir=train_result.get("adapter_dir"),
        trained=bool(train_result.get("trained", False)),
        examples=examples,
        agent_id=resolved_id,
    )


def maybe_lora_update_after_life(
    agent_state: DAUAgentState,
    *,
    pe_event_log: list[dict[str, Any]] | None = None,
    generation: int = 0,
) -> LoraUpdateResult:
    """Graph / consolidate_generation boundary helper — safe no-op when off."""

    return lora_update(
        agent_state,
        pe_event_log=pe_event_log,
        generation=generation,
        force=False,
        agent_id=agent_state.agent_id,
    )
