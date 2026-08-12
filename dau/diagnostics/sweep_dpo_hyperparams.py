"""Sweep DPO hyperparameters against a fixed corpus, without re-living events.

B2 measured two things that make this sweep the next question rather than a
side quest: every optimizer step hit the clip ceiling (`DPO_MAX_GRAD_NORM=1.0`,
smallest observed gradient ~2.96), and `dpo_loss` sat at ln 2 = 0.6931 in both
training arms — the preference margin after training was ~0. Whatever the
learning rate was doing, the ceiling was doing more of it.

D-029 chose `lr=1e-6` from the literature to avoid the unlikelihood push that
`5e-5` produced, and it chose the *bottom* of the band `[5e-7, 1e-6]`. B2 says
that bottom is too weak to measure. The band between "invisible" and
"suppression" is what this sweep maps.

⚠ **Exploratory, not pre-registered.** This does not touch the pre-registered
harness (CLAUDE.md 2.7): `constraints.py` is never edited, the run path is a
separate entry point, and **no adapter is saved** — `save_agent_adapter` is
deliberately not called, so a sweep cannot leak weights into a later run and
trip I0.7. The constants are overridden on the module object for the duration
of one config and restored in a `finally`.

The sweep proves a *direction*, not a value. Picking `lr` from whichever cell
of this table looks best is post-hoc tuning; the value that gets locked must
still be justified, and this output is evidence about the shape of the band.

Usage:
    python -m dau.diagnostics.sweep_dpo_hyperparams
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dau.diagnostics.training_artifacts import (
    ARTIFACTS_BASE_DIR,
    load_training_artifacts,
)

EXPLORATORY_NOTE: str = "exploratory, not pre-registered"
RESULTS_PATH: Path = Path("dau_runs/sweep_dpo_hyperparams.json")
# Rows are appended here as they finish. The sweep takes hours and the machine
# it runs on gets shut down; writing only at the end meant a laptop closing at
# hour three threw away hour three. On restart the finished cells are read back
# and skipped, so the sweep resumes instead of restarting.
PROGRESS_PATH: Path = Path("dau_runs/sweep_dpo_hyperparams.jsonl")

# The band D-029 locked sits at the bottom of this grid; B2 showed it too
# weak. Upper end stops below 5e-5, which D-029 measured producing suppression
# (chosen -0.123 / rejected -4.371), so the sweep maps the gap rather than
# re-deriving a known failure.
LEARNING_RATES: tuple[float, ...] = (1e-6, 5e-6, 1e-5, 2e-5)
# 1.0 is the B2 value where 100% of steps clipped. The rest let progressively
# more of the true gradient through; the largest is above the observed
# gradient scale so at least one cell is effectively unclipped.
MAX_GRAD_NORMS: tuple[float, ...] = (1.0, 3.0, 10.0)

# A sweep agent id must never collide with a real run's, because switch_adapter
# loads from disk when an adapter exists and would silently start a config from
# someone else's trained weights.
SWEEP_AGENT_PREFIX: str = "sweep-ephemeral-"


def cell_key(learning_rate: float, max_grad_norm: float, agent_id: str) -> str:
    """Identity of one sweep cell — what resume matches on."""

    return f"{learning_rate!r}|{max_grad_norm!r}|{agent_id}"


def load_completed_cells(path: Path = PROGRESS_PATH) -> dict[str, dict[str, Any]]:
    """Read finished cells back so a resumed sweep skips them.

    A truncated final line is dropped rather than raising: the common way this
    file ends is a process killed mid-write, and refusing to start because the
    last row is half-written would defeat the point of having it.
    """

    if not path.exists():
        return {}
    done: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        done[cell_key(row["learning_rate"], row["max_grad_norm"], row["agent_id"])] = row
    return done


def _append_row(row: dict[str, Any], path: Path = PROGRESS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _corpus_agent_ids(base_dir: str | Path = ARTIFACTS_BASE_DIR) -> list[str]:
    base = Path(base_dir)
    if not base.is_dir():
        raise FileNotFoundError(
            f"{base} does not exist — run the corpus generation first with "
            "DAU_DUMP_TRAINING_ARTIFACTS=1"
        )
    return sorted(p.stem for p in base.glob("*.json"))


def _train_once(
    *,
    model: Any,
    tokenizer: Any,
    pairs: list[Any],
    learning_rate: float,
    max_grad_norm: float,
    config_tag: str,
) -> dict[str, Any]:
    """One config against one arm's pairs, from a fresh adapter graft.

    Overrides are applied to the module object rather than to constraints.py:
    the pre-registered constant file stays untouched, and a crash mid-sweep
    cannot leave a changed threshold behind because the restore is in
    ``finally``.
    """

    import dau.foundation.local_llm as local_llm

    original_lr = local_llm.DPO_LEARNING_RATE
    original_clip = local_llm.DPO_MAX_GRAD_NORM
    try:
        local_llm.DPO_LEARNING_RATE = learning_rate
        local_llm.DPO_MAX_GRAD_NORM = max_grad_norm
        # No adapter exists for this id, so this is a fresh identity graft —
        # every config starts from the base policy rather than inheriting the
        # previous config's training.
        local_llm.switch_adapter(model, f"{SWEEP_AGENT_PREFIX}{config_tag}")
        before = local_llm.lora_b_abs_sum(model)
        stats = local_llm._run_dpo_epochs(model, tokenizer, list(pairs))
        after = local_llm.lora_b_abs_sum(model)
        # Deliberately no save_agent_adapter: an exploratory run must not put
        # weights on disk (CLAUDE.md 2.7) or a later real run trips I0.7.
        return {
            "lora_b_abs_sum_before": before,
            "lora_b_abs_sum_after": after,
            "lora_b_abs_sum_delta": after - before,
            **stats,
        }
    finally:
        local_llm.DPO_LEARNING_RATE = original_lr
        local_llm.DPO_MAX_GRAD_NORM = original_clip


def main() -> int:
    import dau.foundation.local_llm as local_llm
    from dau.foundation.lora_update import LORA_ENABLED_ENV

    if os.environ.get(LORA_ENABLED_ENV, "0") not in {"1", "true", "TRUE", "yes", "YES"}:
        raise SystemExit(
            f"{LORA_ENABLED_ENV} must be truthy — the sweep trains adapters"
        )

    agent_ids = _corpus_agent_ids()
    completed = load_completed_cells()
    total = len(LEARNING_RATES) * len(MAX_GRAD_NORMS) * len(agent_ids)
    print(
        f"corpus: {len(agent_ids)} arm(s) · grid {total} cell(s) · "
        f"{len(completed)} already done, resuming"
    )

    rows: list[dict[str, Any]] = list(completed.values())
    # The model is only worth loading if there is anything left to run — a
    # resumed sweep that is already complete should cost nothing.
    model = tokenizer = None

    for lr in LEARNING_RATES:
        for clip in MAX_GRAD_NORMS:
            for agent_id in agent_ids:
                if cell_key(lr, clip, agent_id) in completed:
                    continue
                if model is None:
                    model, tokenizer = local_llm.load_local_model()
                payload = load_training_artifacts(agent_id)
                pairs = _rehydrate(payload["pairs"])
                if not pairs:
                    continue
                tag = f"lr{lr}-clip{clip}-{agent_id}"
                stats = _train_once(
                    model=model,
                    tokenizer=tokenizer,
                    pairs=pairs,
                    learning_rate=lr,
                    max_grad_norm=clip,
                    config_tag=tag,
                )
                row = {
                    "learning_rate": lr,
                    "max_grad_norm": clip,
                    "agent_id": agent_id,
                    "arm": payload["arm"],
                    "n_pairs": payload["n_pairs"],
                    **stats,
                }
                rows.append(row)
                # Written before the print, so a kill between the two loses a
                # log line rather than an hour of GPU.
                _append_row(row)
                print(
                    f"  lr={lr:<8g} clip={clip:<5g} {agent_id:28s} "
                    f"loss={row.get('dpo_loss', float('nan')):.4f} "
                    f"clipped={row.get('dpo_clipped_steps')}/"
                    f"{row.get('dpo_optimizer_steps')} "
                    f"dlogp_chosen={row.get('dpo_delta_logp_chosen', 0.0):+.4f}",
                    flush=True,
                )

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(
        json.dumps(
            {
                "note": EXPLORATORY_NOTE,
                "what": (
                    "DPO learning rate x gradient clip ceiling against a fixed "
                    "corpus of lived pairs. Measures whether the preference "
                    "margin can be moved off ln 2 without the suppression "
                    "pattern D-029 found at 5e-5. No adapter was saved."
                ),
                "learning_rates": list(LEARNING_RATES),
                "max_grad_norms": list(MAX_GRAD_NORMS),
                "rows": rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"wrote {RESULTS_PATH}")
    return 0


def _rehydrate(rows: list[dict[str, Any]]) -> list[Any]:
    from dau.foundation.lora_update import PreferencePair

    return [PreferencePair(**row) for row in rows]


if __name__ == "__main__":
    raise SystemExit(main())
