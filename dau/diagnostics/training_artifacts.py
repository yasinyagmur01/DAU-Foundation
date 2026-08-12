"""Persist the exact inputs a training arm consumed, so they can be replayed.

Why this exists. B2 (N=40, ~13.1 GPU hours) answered one configuration's
question and left the next one — what learning rate, what clip ceiling, what
pair-construction strategy — costing another full run each time. But the
expensive part of a run is *living* the 50 events, not training on them:
each arm took ~11 optimizer steps, seconds of GPU. The lives are what needed
persisting, and nothing persisted them.

With the candidate pool and the built pairs on disk, a sweep re-runs training
alone against a fixed corpus. Pair construction, filter thresholds and DPO
hyperparameters all become minutes instead of hours.

Two invariants shape the design.

**It follows the tool, it does not repeat it** (CLAUDE.md 2.8). The dump
serialises the objects that were actually handed to training — after the SNR
and polarity gates, after the shuffle inversion — rather than rebuilding them
from the same inputs with a second copy of the logic. A reconstruction would
agree with the run right up until the moment the two drifted apart, which is
the moment it would matter.

**It is off unless asked** (default ``0``). Writing files must not change what
a run computes, so the dump is a leaf: it reads, serialises, returns. A run
with dumping on and one with it off produce the same ``arm_digest``, and
``test_dump_does_not_change_training_inputs`` holds that line.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

DUMP_ARTIFACTS_ENV: str = "DAU_DUMP_TRAINING_ARTIFACTS"
DUMP_ARTIFACTS_DEFAULT: str = "0"
# Same vocabulary as LORA_TRUTHY (lora_update.py) — one spelling of "yes"
# across the codebase, so a run cannot be half-enabled by a synonym.
DUMP_TRUTHY: frozenset[str] = frozenset({"1", "true", "TRUE", "yes", "YES"})

ARTIFACTS_BASE_DIR: str = "dau_runs/training_artifacts"
ARTIFACTS_SCHEMA: str = "training-artifacts/1"

# Digest over the pairs actually trained on. Two corpora with the same digest
# are the same training input, which is what lets a replay claim it is
# replaying a specific arm rather than something that merely resembles it.
DIGEST_ENCODING: str = "utf-8"


def dump_enabled() -> bool:
    """Whether this run should persist training inputs.

    Unrecognised values raise rather than defaulting to off (D-023): a
    misspelled flag that silently disables the dump would be discovered only
    after the GPU hours were already spent.
    """

    raw = os.environ.get(DUMP_ARTIFACTS_ENV, DUMP_ARTIFACTS_DEFAULT).strip()
    if not raw:
        return False
    if raw in DUMP_TRUTHY:
        return True
    if raw in {"0", "false", "FALSE", "no", "NO"}:
        return False
    raise ValueError(
        f"{DUMP_ARTIFACTS_ENV}={raw!r} is not a recognised boolean; "
        f"use one of {sorted(DUMP_TRUTHY)} or 0/false/no"
    )


def pairs_digest(pairs: list[Any]) -> str:
    """sha256 over the ordered (prompt, chosen, rejected) triples.

    Order is part of the identity: the same pairs in a different sequence are
    a different gradient trajectory under accumulation.
    """

    hasher = hashlib.sha256()
    for pair in pairs:
        for field in ("prompt", "chosen", "rejected"):
            hasher.update(str(getattr(pair, field, "")).encode(DIGEST_ENCODING))
            hasher.update(b"\x00")
    return hasher.hexdigest()


def artifact_path(agent_id: str, base_dir: str | Path = ARTIFACTS_BASE_DIR) -> Path:
    return Path(base_dir) / f"{agent_id}.json"


def dump_training_artifacts(
    *,
    agent_id: str,
    arm: str,
    lived_examples: list[Any],
    pairs: list[Any],
    shuffled: bool,
    base_dir: str | Path = ARTIFACTS_BASE_DIR,
) -> Path | None:
    """Write one arm's training inputs. Returns the path, or None when off.

    ``lived_examples`` is the candidate pool *before* pair construction, so a
    replay can try a different construction strategy (KTO, GAP-18's disjoint
    matching) without re-living the events. ``pairs`` is what training actually
    received, so a replay can skip construction entirely and sweep DPO
    hyperparameters against a fixed set.
    """

    if not dump_enabled():
        return None

    path = artifact_path(agent_id, base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": ARTIFACTS_SCHEMA,
        "agent_id": agent_id,
        "arm": arm,
        # Recorded because the shuffle arm's pairs are already inverted here;
        # a replay that inverted them again would train the lived direction
        # while believing it was the control.
        "shuffled": bool(shuffled),
        "n_lived_examples": len(lived_examples),
        "n_pairs": len(pairs),
        "pairs_digest": pairs_digest(pairs),
        "lived_examples": [asdict(example) for example in lived_examples],
        "pairs": [asdict(pair) for pair in pairs],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding=DIGEST_ENCODING)
    return path


def load_training_artifacts(
    agent_id: str, base_dir: str | Path = ARTIFACTS_BASE_DIR
) -> dict[str, Any]:
    """Read one arm's dump back, refusing a schema this code cannot read."""

    path = artifact_path(agent_id, base_dir)
    payload = json.loads(path.read_text(encoding=DIGEST_ENCODING))
    schema = payload.get("schema")
    if schema != ARTIFACTS_SCHEMA:
        raise ValueError(
            f"{path}: schema {schema!r} is not {ARTIFACTS_SCHEMA!r} — "
            "the dump was written by a different version of this tool"
        )
    return payload
