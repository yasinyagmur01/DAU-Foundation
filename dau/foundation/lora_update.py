"""Generation-end lived-trace LoRA update (optional, flag-gated).

Biology analogy: when one life ends, somatic scars and prediction errors are
condensed into a small adapter graft for the next generation — never a
designer-written personality.

Signal v1 (strict): PE / delta / trauma / drift scalars only.
No F_agent threshold. No trait / persona target text.
Default DAU_LORA_ENABLED=0 → no-op (today's behaviour).

LoRA is a leading testable path, not a guaranteed metacognition fix.
"""

from __future__ import annotations

import json
import os
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

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

ADAPTER_ROOT_DIR: str = "dau_lora_adapters"
LIVED_TRACES_FILE_NAME: str = "lived_traces.jsonl"
ADAPTER_META_FILE_NAME: str = "lora_update_meta.json"

DRIFT_BIAS_DOMAINS: tuple[str, ...] = (
    "energy",
    "resource",
    "social",
    "uncertainty",
)

# Loss weight from lived scalars — no F_agent, no trait labels.
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

# Signal v2 — PE-ranked preference (MiniLM judge only; no LLM-as-judge).
SIGNAL_V1_ID: str = "pe_delta_trauma_drift_v1"
SIGNAL_V2_ID: str = "pe_ranked_pref_v2"
PREF_TRACES_FILE_NAME: str = "preference_pairs.jsonl"
PREF_EXPECTED_OUTCOME: str = (
    "extract resources carefully while preserving the shared commons"
)
PREF_REJECT_CANDIDATE: str = (
    "abandon all care and drain the pool for maximum short-term gain"
)
PREF_CONTEXT_TEMPLATE: str = (
    "Context expectation: {expected}\nLived scalars: pe={pe:.3f}"
)
PE_RANK_MIN_GAP: float = 1e-6

# NLI polarity filter observability (unit tests; not LangSmith).
NLI_FILTER_STATS: dict[str, int] = {
    "total_candidates": 0,
    "passed": 0,
    "rejected": 0,
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
    """PE-ranked preference row — chosen has lower MiniLM PE than rejected."""

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

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


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
    """Map event timestamp → decision text from agent_decision events."""

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
    """Build SFT rows from PE / delta / trauma / drift — no F_agent filter.

    Trauma is not blindly dropped: trauma_flag becomes a scalar in the prompt
    and a loss-weight bonus. No personality adjectives.
    """

    pe_rows = list(pe_event_log) if pe_event_log is not None else []
    pe_by_counter: dict[int, dict[str, Any]] = {}
    for row in pe_rows:
        pe_by_counter[int(row["event_counter"])] = row

    decisions = _decision_by_counter(agent_state)
    drift_total = _drift_sum(agent_state.drift_state)
    examples: list[LivedTraceExample] = []

    deltas: list[DeltaRecord] = list(agent_state.delta_log)
    if not deltas and pe_by_counter:
        # PE-only path when delta_log empty (diagnostics stubs).
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


def adapter_dir_for_agent(agent_id: str, generation: int = 0) -> Path:
    """Return disk path for this agent's generation adapter."""

    return Path.cwd() / ADAPTER_ROOT_DIR / f"{agent_id}_gen{generation}"


def write_lived_traces(
    examples: list[LivedTraceExample],
    directory: Path,
) -> Path:
    """Persist JSONL traces beside the adapter checkpoint."""

    directory.mkdir(parents=True, exist_ok=True)
    path = directory / LIVED_TRACES_FILE_NAME
    with path.open("w", encoding="utf-8") as handle:
        for example in examples:
            handle.write(json.dumps(asdict(example), ensure_ascii=True) + "\n")
    return path


def write_preference_pairs(
    pairs: list[PreferencePair],
    directory: Path,
) -> Path:
    """Persist PE-ranked preference JSONL beside the adapter checkpoint."""

    directory.mkdir(parents=True, exist_ok=True)
    path = directory / PREF_TRACES_FILE_NAME
    with path.open("w", encoding="utf-8") as handle:
        for pair in pairs:
            handle.write(json.dumps(asdict(pair), ensure_ascii=True) + "\n")
    return path


def build_pe_ranked_pairs(
    examples: list[LivedTraceExample],
    *,
    expected_outcome: str = PREF_EXPECTED_OUTCOME,
    reject_candidate: str = PREF_REJECT_CANDIDATE,
    pe_fn: Any | None = None,
) -> list[PreferencePair]:
    """Rank (completion, reject_candidate) by MiniLM PE vs expected_outcome.

    ``pe_fn(expected, actual) -> float`` defaults to ``semantic_prediction_error``.
    Ties / non-strict gaps are skipped. No trait / persona text.
    """

    if pe_fn is None:
        from dau.foundation.semantic_similarity import semantic_prediction_error

        pe_fn = semantic_prediction_error

    pairs: list[PreferencePair] = []
    expected = expected_outcome.strip()
    reject = reject_candidate.strip()
    for example in examples:
        chosen_raw = (example.completion or COMPLETION_FALLBACK).strip()
        if not chosen_raw or not reject or chosen_raw == reject:
            continue
        pe_a = float(pe_fn(expected, chosen_raw))
        pe_b = float(pe_fn(expected, reject))
        if abs(pe_a - pe_b) < PE_RANK_MIN_GAP:
            continue
        if pe_a < pe_b:
            chosen_text, rejected_text = chosen_raw, reject
            pe_chosen, pe_rejected = pe_a, pe_b
        else:
            chosen_text, rejected_text = reject, chosen_raw
            pe_chosen, pe_rejected = pe_b, pe_a
        prompt = PREF_CONTEXT_TEMPLATE.format(
            expected=expected,
            pe=example.prediction_error,
        )
        pair = PreferencePair(
            prompt=prompt,
            chosen=chosen_text,
            rejected=rejected_text,
            pe_chosen=pe_chosen,
            pe_rejected=pe_rejected,
            event_counter=example.event_counter,
        )
        NLI_FILTER_STATS["total_candidates"] += 1
        if not is_genuine_polarity_pair(pair.chosen, pair.rejected):
            NLI_FILTER_STATS["rejected"] += 1
            continue  # surface format variation — reject
        NLI_FILTER_STATS["passed"] += 1
        pairs.append(pair)
    return pairs


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
    # Force at least one swap when possible so shuffle ≠ lived.
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


def lora_update(
    agent_state: DAUAgentState,
    *,
    pe_event_log: list[dict[str, Any]] | None = None,
    generation: int = 0,
    force: bool = False,
) -> LoraUpdateResult:
    """Optional generation-end hook: write traces; train adapter when allowed.

    When DAU_LORA_ENABLED=0 (default), returns skipped immediately.
    Training runs only if local VRAM spike previously reported GO (or force).
    """

    if not force and not is_lora_enabled():
        return LoraUpdateResult(
            enabled=False,
            skipped=True,
            reason=f"{LORA_ENABLED_ENV}=0 (default) — generation-end unchanged.",
        )

    examples = build_lived_trace_examples(agent_state, pe_event_log)
    if not examples:
        return LoraUpdateResult(
            enabled=True,
            skipped=True,
            reason="No lived-trace examples to train on.",
            example_count=0,
        )

    out_dir = adapter_dir_for_agent(agent_state.agent_id, generation)
    write_lived_traces(examples, out_dir)
    meta = {
        "agent_id": agent_state.agent_id,
        "generation": generation,
        "example_count": len(examples),
        "signal": SIGNAL_V1_ID,
        "f_agent_threshold": None,
    }
    (out_dir / ADAPTER_META_FILE_NAME).write_text(
        json.dumps(meta, indent=2) + "\n",
        encoding="utf-8",
    )

    from dau.foundation.local_llm import (
        STATUS_GO,
        attach_lora_adapter,
        cuda_is_available,
        load_base_model_4bit,
        lora_plasticity_allowed,
        run_micro_train_step,
        save_adapter,
    )

    if not force and not lora_plasticity_allowed():
        return LoraUpdateResult(
            enabled=True,
            skipped=True,
            reason=(
                "Traces written; training deferred — no VRAM GO report. "
                "Run python -m dau.diagnostics.run_vram_spike on GPU first."
            ),
            example_count=len(examples),
            adapter_dir=str(out_dir),
            examples=examples,
        )

    if not cuda_is_available():
        return LoraUpdateResult(
            enabled=True,
            skipped=True,
            reason="Traces written; CUDA unavailable for adapter train.",
            example_count=len(examples),
            adapter_dir=str(out_dir),
            examples=examples,
        )

    try:
        load_base_model_4bit()
        attach_lora_adapter()
        run_micro_train_step(examples=examples)
        save_adapter(out_dir)
    except Exception as exc:  # noqa: BLE001 — hook must not crash life teardown
        return LoraUpdateResult(
            enabled=True,
            skipped=True,
            reason=f"Train failed: {type(exc).__name__}: {exc}",
            example_count=len(examples),
            adapter_dir=str(out_dir),
            examples=examples,
        )

    return LoraUpdateResult(
        enabled=True,
        skipped=False,
        reason=STATUS_GO,
        example_count=len(examples),
        adapter_dir=str(out_dir),
        trained=True,
        examples=examples,
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
    )
