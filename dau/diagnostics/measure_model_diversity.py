"""U3 (D-019 + D-025): generation diversity and VRAM peak for ONE checkpoint.

Biology analogy: before comparing two nervous systems, check that each one
still produces distinguishable behaviour at all — a body that says the same
thing to every niche has no preference signal to learn from.

Measures ``_phase1_diversity``'s ``n_unique`` — the production metric that
gates DPO training — over 3 seeds x 10 events, greedy, plus the VRAM peak.
No new metric is invented (D-019).

One model per process, deliberately. The base model is a process-wide
singleton and a 7.62 GiB card cannot hold two 8B checkpoints, so the two
arms are two invocations:

    DAU_LLM_BACKEND=local python -m dau.diagnostics.measure_model_diversity
    DAU_LLM_BACKEND=local DAU_LOCAL_MODEL=Qwen/Qwen2.5-7B-Instruct \\
        python -m dau.diagnostics.measure_model_diversity

This script does NOT pick a winner. The acceptance criterion is locked in
D-019 (median n_unique >= DIVERSITY_MIN_UNIQUE and strictly above the other
arm; ties go to the status quo). Comparing the two JSON files and recording
the decision is a separate, human step — a script that announced a winner
would be one refactor away from being the place the criterion gets loosened.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from pathlib import Path
from typing import Any

from dau.diagnostics.run_protocol_c_prime import (
    DIVERSITY_MIN_UNIQUE,
    _collect_pe_events,
    _lock_seeds,
    _phase1_diversity,
    _json_sanitize,
)
from dau.diagnostics.tool_identity import BACKEND_LOCAL, resolve_backend
from dau.foundation.local_llm import (
    LLM_DO_SAMPLE_ENV,
    LLM_DO_SAMPLE_TRUTHY,
    LOCAL_MODEL_ENV,
    _build_prompt,
    adapter_exists,
    describe_quantization,
    get_loaded_model_name,
    load_local_model,
    resolve_local_model_name,
)

# ---------------------------------------------------------------------------
# Pre-registered measurement parameters (D-019; do not tune after seeing data)
# ---------------------------------------------------------------------------

MEASURE_SEEDS: tuple[int, ...] = (2001, 2002, 2003)
MEASURE_EVENTS: int = 10
AGENT_ID_PREFIX: str = "u3-diversity"
RESULTS_DIR: Path = Path("dau_runs")
RESULTS_STEM: str = "u3_model_diversity"

# Probe strings for the chat-template check. Content is irrelevant — only
# whether the tokenizer carries a template at all.
PROBE_SYSTEM: str = "You are an agent in a resource niche."
PROBE_USER: str = "State your decision."

BYTES_PER_MIB: float = 1024.0 * 1024.0

BACKEND_MESSAGE: str = (
    "Refusing to start: this measurement needs DAU_LLM_BACKEND=local. It reads "
    "generation diversity off real weights; a remote endpoint would measure "
    "someone else's model and D-019 compares local checkpoints."
)
ALREADY_LOADED_MESSAGE: str = (
    "Refusing to start: {loaded!r} is already resident. Each arm must be its "
    "own process so the VRAM peak belongs to one checkpoint and the singleton "
    "cannot serve stale weights."
)
TEMPLATE_MESSAGE: str = (
    "Refusing to measure {model!r}: its tokenizer carries no chat template, so "
    "_build_prompt fell back to plain concatenation. D-025 makes that arm "
    "invalid rather than silently comparable — an instruction-tuned model run "
    "outside its own format continues the prompt instead of deciding, which "
    "inflates n_unique for the wrong reason."
)
ADAPTER_MESSAGE: str = (
    "Refusing to measure with agent_id {agent_id!r}: an adapter already exists "
    "at {path}. switch_adapter would load it and the numbers would describe "
    "trained weights, not the base checkpoint D-019 is comparing."
)
SAMPLING_MESSAGE: str = (
    "Refusing to measure with {env}={value!r}. D-019 pre-registered greedy "
    "decoding; sampling would make n_unique a property of the temperature."
)


def _safe_model_slug(model_name: str) -> str:
    """Filesystem-safe stem so the two arms cannot overwrite each other."""

    return model_name.replace("/", "__").replace(":", "_")


def _vram_peak_mib() -> float | None:
    """Peak allocated VRAM in MiB, or None on a CPU-only build."""

    try:
        import torch
    except ImportError:
        return None
    if not torch.cuda.is_available():
        return None
    return float(torch.cuda.max_memory_allocated()) / BYTES_PER_MIB


def _reset_vram_peak() -> None:
    """Zero the peak counter so it measures this run, not the process history."""

    try:
        import torch
    except ImportError:
        return
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()


def _check_preconditions(agent_id: str) -> str:
    """Fail loudly before loading 15 GB. Returns the checkpoint to be measured."""

    if resolve_backend() != BACKEND_LOCAL:
        raise SystemExit(BACKEND_MESSAGE)

    loaded = get_loaded_model_name()
    if loaded is not None:
        raise SystemExit(ALREADY_LOADED_MESSAGE.format(loaded=loaded))

    sampling = os.environ.get(LLM_DO_SAMPLE_ENV, "").strip()
    if sampling in LLM_DO_SAMPLE_TRUTHY:
        raise SystemExit(
            SAMPLING_MESSAGE.format(env=LLM_DO_SAMPLE_ENV, value=sampling)
        )

    if adapter_exists(agent_id):
        from dau.foundation.local_llm import get_adapter_path

        raise SystemExit(
            ADAPTER_MESSAGE.format(agent_id=agent_id, path=get_adapter_path(agent_id))
        )

    return resolve_local_model_name()


def measure_one_model(
    *,
    seeds: tuple[int, ...] = MEASURE_SEEDS,
    n_events: int = MEASURE_EVENTS,
) -> dict[str, Any]:
    """Run every seed against the resident checkpoint and return the record."""

    agent_id = f"{AGENT_ID_PREFIX}-{os.getpid()}"
    requested = _check_preconditions(agent_id)

    print(f"[U3] loading {requested} — this pulls ~15 GB into VRAM", flush=True)
    started = time.perf_counter()
    _, tokenizer = load_local_model(agent_id=agent_id)

    _, used_chat_template = _build_prompt(tokenizer, PROBE_SYSTEM, PROBE_USER)
    if not used_chat_template:
        raise SystemExit(TEMPLATE_MESSAGE.format(model=requested))

    # Peak is reset after the load so the number covers generation as well as
    # resident weights, which is what U7's budget actually has to fit.
    _reset_vram_peak()

    rows: list[dict[str, Any]] = []
    for seed in seeds:
        seed_started = time.perf_counter()
        _lock_seeds(seed)
        _, lived_examples, pe_rows = _collect_pe_events(agent_id, seed, n_events)
        n_unique, pe_gap_max = _phase1_diversity(lived_examples)
        rows.append(
            {
                "seed": int(seed),
                "n_unique": int(n_unique),
                "pe_gap_max": float(pe_gap_max),
                "n_lived_examples": len(lived_examples),
                "n_pe_rows": len(pe_rows),
                "wall_seconds": time.perf_counter() - seed_started,
            }
        )
        print(
            f"[U3] seed={seed} n_unique={n_unique} "
            f"(gate needs >= {DIVERSITY_MIN_UNIQUE})",
            flush=True,
        )

    uniques = [int(row["n_unique"]) for row in rows]
    return {
        "protocol": "U3_MODEL_DIVERSITY",
        "records": ["D-019", "D-025"],
        "model_requested": requested,
        "model_loaded": get_loaded_model_name(),
        "quantization": describe_quantization(),
        "used_chat_template": used_chat_template,
        "greedy": True,
        "seeds": [int(seed) for seed in seeds],
        "n_events": int(n_events),
        "per_seed": rows,
        "n_unique_median": float(statistics.median(uniques)),
        "n_unique_values": uniques,
        "diversity_min_unique": int(DIVERSITY_MIN_UNIQUE),
        "vram_peak_mib": _vram_peak_mib(),
        "total_wall_seconds": time.perf_counter() - started,
    }


def write_results_json(record: dict[str, Any], path: Path | None = None) -> Path:
    """Write one arm's record; the stem carries the model so arms never collide."""

    if path is None:
        slug = _safe_model_slug(str(record.get("model_loaded") or "unknown"))
        path = RESULTS_DIR / f"{RESULTS_STEM}_{slug}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_json_sanitize(record), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Measure n_unique + VRAM peak for the checkpoint named by "
            f"{LOCAL_MODEL_ENV} (default: LOCAL_MODEL_NAME). One model per "
            "process; this script does not choose between them."
        )
    )
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    record = measure_one_model()
    path = write_results_json(record, args.out)

    print(
        f"\n[U3] {record['model_loaded']}\n"
        f"     n_unique per seed : {record['n_unique_values']}\n"
        f"     median            : {record['n_unique_median']} "
        f"(gate {record['diversity_min_unique']})\n"
        f"     VRAM peak         : {record['vram_peak_mib']} MiB\n"
        f"     quantization      : {record['quantization'].get('quant_type')} "
        f"double_quant={record['quantization'].get('double_quant')}\n"
        f"     written to        : {path}\n"
        "     Decision belongs to D-019/D-025, not to this script.",
        flush=True,
    )


if __name__ == "__main__":
    main()
