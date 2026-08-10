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
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from dau.foundation.constraints import SNR_MARGIN_FLOOR
from dau.foundation.delta import is_trauma
from dau.foundation.drift import DriftState, get_drift_bias
from dau.foundation.polarity_filter import is_genuine_polarity_pair
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
# The two halves of the prompt the decision was actually made under, stored on
# the decision event by agent_node. Channel 2 trains on these verbatim, so they
# must be the strings that went to the model — never regenerated from
# SYSTEM_PROMPT or rebuilt from state, which would drift from what was lived.
# System 1 (NPC) decisions carry neither key: they never had a prompt.
DECISION_PROMPT_SYSTEM_KEY: str = "decision_prompt_system"
DECISION_PROMPT_USER_KEY: str = "decision_prompt_user"

SIGNAL_V1_ID: str = "pe_delta_trauma_drift_v1"
SIGNAL_V2_ID: str = "pe_ranked_pref_v2"
PREF_TRACES_FILE_NAME: str = "preference_pairs.jsonl"
# Endogenous preference: lower lived PE beats higher lived PE. No designer
# value sentence, no fixed reject template (those were recipe A — trait-
# adjacent and mini-tested to inflate PE without teaching contrast).
# D-032 retired PREF_LIVED_CONTEXT_TEMPLATE — it was
# "Lived preference: pe={pe_chosen:.3f} decision over pe={pe_rejected:.3f}".
# Measured at 51 prompt tokens with no system message, against 246-306 at
# inference, and it handed the model both PE values, which are only computed
# AFTER the decision. The pair prompt is now the chosen event's recorded
# prompt.
PE_RANK_MIN_GAP: float = 1e-6

# total_candidates/rejected are per-candidate (pre-dedup); passed is
# per-event (post PE-rank dedup) — these do not sum to total_candidates
# by design. Named for the job, not the instrument: D-032 swapped NLI for
# cosine distance behind polarity_filter, and a counter still called
# NLI_FILTER_STATS would have labelled cosine rejections "nli" in every
# results file (CLAUDE.md 2.8).
POLARITY_FILTER_STATS: dict[str, int] = {
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

# D-035 step 0, item 2. Counts say how many a threshold dropped; they cannot
# say where to put it. The pilot reported 3076 of 6800 candidates below
# SNR_MARGIN_FLOOR=0.15 (D-034) — a rejection rate, not a distribution, so
# neither that floor nor the cosine band can be moved off the brief's numbers
# without guessing. Every candidate margin that reaches the SNR gate lands
# here; percentiles are computed at report time, not stored per-run.
SNR_MARGIN_SAMPLES: list[float] = []

# D-032. An event whose decision carries no recorded prompt cannot be trained
# on: System 1 (NPC) decisions never ran the policy, and a life recorded before
# agent_node stored the prompt has nothing to condition on. Both are skipped,
# and the count is reported rather than absorbed — a training set that shrank
# because the log was old must not read like one that shrank because the
# filters were strict.
PROMPT_FILTER_STATS: dict[str, int] = {
    "examples_seen": 0,
    "skipped_no_recorded_prompt": 0,
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
    # The prompt this decision was actually made under (D-032). Empty means the
    # event has none — System 1, or a log predating the record.
    decision_system: str = ""
    decision_user: str = ""


@dataclass
class PreferencePair:
    """Lived-PE preference row — chosen has lower life PE than rejected."""

    prompt: str
    chosen: str
    rejected: str
    pe_chosen: float
    pe_rejected: float
    event_counter: int = 0
    # Read by local_llm._run_dpo_epochs via getattr; the hook predates the
    # field and was dead until D-032 gave it something to carry.
    system: str = ""


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


@dataclass
class LivedDecision:
    """What the agent said, and the prompt it said it under (D-032)."""

    text: str
    system: str = ""
    user: str = ""


# Read-only sentinel for events with no decision at all.
NO_LIVED_DECISION = LivedDecision(text=COMPLETION_FALLBACK)


def _decision_by_counter(agent_state: DAUAgentState) -> dict[int, LivedDecision]:
    mapping: dict[int, LivedDecision] = {}
    for event in agent_state.event_log:
        if event.event_type != EVENT_TYPE_DECISION:
            continue
        payload = event.payload if isinstance(event.payload, dict) else {}
        decision = payload.get(DECISION_PAYLOAD_KEY)
        if decision is None:
            continue
        mapping[int(event.timestamp)] = LivedDecision(
            text=str(decision).strip() or COMPLETION_FALLBACK,
            system=str(payload.get(DECISION_PROMPT_SYSTEM_KEY) or ""),
            user=str(payload.get(DECISION_PROMPT_USER_KEY) or ""),
        )
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
            lived = decisions.get(counter, NO_LIVED_DECISION)
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
                    completion=lived.text,
                    decision_system=lived.system,
                    decision_user=lived.user,
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
        lived = decisions.get(counter, NO_LIVED_DECISION)
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
                completion=lived.text,
                decision_system=lived.system,
                decision_user=lived.user,
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
    ``is_genuine_polarity_pair`` from ``polarity_filter`` — cosine distance
    within [POLARITY_COSINE_MIN, POLARITY_COSINE_MAX] since D-032, NLI
    contradiction before it. Rejects are counted in
    POLARITY_FILTER_STATS["rejected"]. Preference direction remains PE-defined;
    the polarity gate only decides whether the two decisions differ enough to
    be a contrast at all.

    D-032: the pair's prompt is the prompt the CHOSEN decision was made under,
    replayed from the event log, not a template built from the two PE values.
    An event with no recorded prompt cannot be trained on and is skipped with a
    counted [WARN] — never absorbed silently (CLAUDE.md 2.9).
    """

    usable: list[LivedTraceExample] = []
    missing_prompt = 0
    for ex in examples:
        completion = (ex.completion or COMPLETION_FALLBACK).strip()
        if not completion or completion == COMPLETION_FALLBACK:
            continue
        PROMPT_FILTER_STATS["examples_seen"] += 1
        if not ex.decision_user.strip():
            PROMPT_FILTER_STATS["skipped_no_recorded_prompt"] += 1
            missing_prompt += 1
            continue
        usable.append(ex)
    if missing_prompt:
        print(
            f"[LORA][WARN] {missing_prompt} lived decision(s) carry no recorded "
            f"prompt and were skipped — System 1 decisions never ran the policy, "
            f"and logs predating D-032 have nothing to condition on",
            flush=True,
        )
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
            SNR_MARGIN_SAMPLES.append(margin)
            if margin < SNR_MARGIN_FLOOR:
                SNR_FILTER_STATS["rejected_below_margin"] += 1
                continue

            POLARITY_FILTER_STATS["total_candidates"] += 1
            if not is_genuine_polarity_pair(chosen, rejected):
                POLARITY_FILTER_STATS["rejected"] += 1
                continue
            pe_chosen = float(low.prediction_error)
            pe_rejected = float(high.prediction_error)
            gap = pe_rejected - pe_chosen
            # The chosen side's own situation. The rejected completion came
            # from a different event, so it is off-policy for this prompt: the
            # pair reads "in THIS situation, prefer what you said here over
            # what you said when the world surprised you more".
            pair = PreferencePair(
                prompt=low.decision_user,
                system=low.decision_system,
                chosen=chosen,
                rejected=rejected,
                pe_chosen=pe_chosen,
                pe_rejected=pe_rejected,
                event_counter=int(low.event_counter),
            )
            previous = best_by_event.get(pair.event_counter)
            if previous is None or gap > (previous.pe_rejected - previous.pe_chosen):
                best_by_event[pair.event_counter] = pair
    POLARITY_FILTER_STATS["passed"] += len(best_by_event)
    return list(best_by_event.values())


def shuffle_preference_pairs(
    pairs: list[PreferencePair],
    *,
    seed: int,
) -> list[PreferencePair]:
    """Control: swap chosen/rejected (wrong PE preference direction).

    Field-by-field reconstruction is what this used to do, and it silently
    drops any field added later — the shuffled arm would then train under
    different conditioning than the lived arm and the comparison would be
    between two things. ``replace`` swaps only the two sides and carries the
    rest, prompt and system included (D-032).
    """

    def _swap(pair: PreferencePair) -> PreferencePair:
        return replace(
            pair,
            chosen=pair.rejected,
            rejected=pair.chosen,
            pe_chosen=pair.pe_rejected,
            pe_rejected=pair.pe_chosen,
        )

    rng = random.Random(seed)
    out: list[PreferencePair] = []
    for pair in pairs:
        out.append(_swap(pair) if rng.random() < 0.5 else pair)
    if pairs and out == pairs:
        out[0] = _swap(pairs[0])
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
