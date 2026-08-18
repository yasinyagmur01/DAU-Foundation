"""Tool identity + explicit LoRA gate (D-004, GAP-1).

A run must not be able to deny its own configuration. Two mechanisms:

1. ``resolve_lora_choice`` — the runner refuses to start unless the operator
   said ``--lora`` or ``--no-lora``. Falling through to the default is not a
   choice; GAP-1 is exactly what falling through produced: three arms that
   were copies of each other, and a results file reporting it in a corner
   nobody reads.
2. ``build_tool_identity`` — every results JSON carries the instrument it was
   produced with: backend, model id, quantization, DPO settings, adapter
   state, sampling parameters, seed range, library versions.

Reported values are read from the code that actually runs, never re-derived
here. Where the code leaves a setting at a library default, this module
reports the default rather than what the docs assume it is.
"""

from __future__ import annotations

import importlib.metadata
import os
import platform
import sys
from pathlib import Path
from typing import Any

from dau.foundation.constraints import (
    ADAPTER_BASE_DIR,
    DPO_BATCH_SIZE,
    DPO_GRADIENT_ACCUMULATION_STEPS,
    DPO_BETA,
    DPO_EPOCHS,
    DPO_LEARNING_RATE,
    DPO_MAX_GRAD_NORM,
    DPO_MAX_SEQUENCE_TOKENS,
    LANDMARK_EVENT,
    METABOLIC_GAIN_CALIBRATED,
    METABOLIC_GAIN_HALF_SATURATION,
    METABOLIC_GAIN_MAX,
    METABOLIC_GRACE_EVENTS,
    PER_AGENT_LORA_ALPHA,
    PER_AGENT_LORA_RANK,
)
from dau.foundation.lora_update import LORA_ENABLED_DEFAULT, LORA_ENABLED_ENV
from dau.generation.fitness import (
    FITNESS_ENERGY_READING,
    FITNESS_W_ENERGY,
    FITNESS_W_POOL,
    FITNESS_W_SURVIVAL,
)
from dau.society.extraction import EXTRACTION_DEFECT

# LoRA choice states written into the results JSON.
LORA_CHOICE_ON: str = "explicit_on"
LORA_CHOICE_OFF: str = "explicit_off"

LORA_ENABLED_ON: str = "1"
LORA_ENABLED_OFF: str = LORA_ENABLED_DEFAULT

# Spelled here rather than imported from graph so this module stays importable
# without pulling the graph in; asserted equal to graph's constant in tests.
BACKEND_LOCAL: str = "local"
# Same reasoning for the control arm's name, which preflight needs without
# importing the runner; asserted equal to ARM_NULL in tests.
ARM_NULL_NAME: str = "null"

# D-021/A1 implemented (U4): read from constraints rather than restated here,
# so the block cannot claim an accumulation the trainer does not perform. The
# previous literal 1 was true only because no accumulation existed.
GRADIENT_ACCUMULATION_STEPS: int = DPO_GRADIENT_ACCUMULATION_STEPS

VERSION_PACKAGES: tuple[str, ...] = (
    "torch",
    "transformers",
    "peft",
    "bitsandbytes",
    "accelerate",
    "numpy",
    "scipy",
)
VERSION_MISSING: str = "not_installed"

GROQ_LORA_MESSAGE: str = (
    "--lora requires DAU_LLM_BACKEND=local. Per-agent adapters need weight "
    "access, which a remote endpoint cannot give: training would be skipped "
    "while the results JSON reported lora_enabled=1. Re-run with "
    "DAU_LLM_BACKEND=local, or with --no-lora if an untrained run is intended."
)
LORA_UNSET_MESSAGE: str = (
    "Refusing to start: neither --lora nor --no-lora was given. LoRA training "
    "is off by default, so falling through would run three identical arms and "
    "report a p-value for it (GAP-1). Pass --lora to train, or --no-lora to "
    "state that an untrained run is intended."
)


def resolve_lora_choice(explicit: bool | None, *, mock: bool = False) -> str:
    """Return the recorded LoRA choice, or exit loudly when none was made.

    Sets DAU_LORA_ENABLED to match, so the three gate layers downstream
    (_train_adapter, run_micro_train_preference_step, lora_update) cannot
    disagree with what the results JSON reports.

    ``mock`` exempts the backend check: a mock run takes decisions from a
    canned LLM, so neither backend is in play and the remote-endpoint
    objection does not apply. Such a run can never be stamped clean —
    preflight marks it RUN_QUALITY_MOCK — so the exemption cannot let a
    mock be mistaken for an experiment.
    """

    if explicit is None:
        raise SystemExit(LORA_UNSET_MESSAGE)

    if explicit:
        if not mock and resolve_backend() != BACKEND_LOCAL:
            raise SystemExit(GROQ_LORA_MESSAGE)
        os.environ[LORA_ENABLED_ENV] = LORA_ENABLED_ON
        return LORA_CHOICE_ON

    os.environ[LORA_ENABLED_ENV] = LORA_ENABLED_OFF
    return LORA_CHOICE_OFF


def resolve_backend() -> str:
    """Backend name as the graph resolves it at decision time (graph.py:921)."""

    from dau.foundation.graph import _resolve_llm_backend

    return str(_resolve_llm_backend())


def _model_id(backend: str) -> str:
    """Name the weights that produced the numbers, not the current config.

    Once a base model is loaded it is a process-wide singleton, so the
    checkpoint in VRAM is the authority; DAU_LOCAL_MODEL only says what the
    next load would pick. Reporting the env value while older weights are
    still resident is the same class of silent mismatch describe_quantization
    exists to prevent (D-020).
    """

    if backend == BACKEND_LOCAL:
        from dau.foundation.local_llm import (
            get_loaded_model_name,
            resolve_local_model_name,
        )

        loaded = get_loaded_model_name()
        return str(loaded if loaded is not None else resolve_local_model_name())
    from dau.foundation.graph import MODEL_NAME

    return str(MODEL_NAME)


def _quantization(backend: str) -> dict[str, Any]:
    if backend != BACKEND_LOCAL:
        return {"available": False, "reason": "remote backend — not applicable"}
    from dau.foundation.local_llm import describe_quantization

    return dict(describe_quantization())


def _versions() -> dict[str, str]:
    versions: dict[str, str] = {"python": platform.python_version()}
    for package in VERSION_PACKAGES:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = VERSION_MISSING
    return versions


def _adapter_state() -> dict[str, Any]:
    """Adapter root as it stands at write time.

    Count only, not the names: the directory accumulates across runs (94 of
    them at the time of writing) and the per-agent isolation question belongs
    to the preflight gate, not to a field repeated in every results file.
    """

    base = Path(ADAPTER_BASE_DIR)
    n_dirs = sum(1 for p in base.iterdir() if p.is_dir()) if base.is_dir() else 0
    return {
        "base_dir": str(base),
        "base_dir_exists": base.is_dir(),
        "n_agent_dirs": n_dirs,
    }


def _sampling() -> dict[str, Any]:
    from dau.foundation.graph import _resolve_llm_temperature
    from dau.foundation.local_llm import (
        GENERATION_MAX_NEW_TOKENS,
        LLM_DO_SAMPLE_DEFAULT,
        LLM_DO_SAMPLE_ENV,
        LLM_DO_SAMPLE_TRUTHY,
        LLM_SEED_ENV,
    )

    do_sample_raw = os.environ.get(LLM_DO_SAMPLE_ENV, LLM_DO_SAMPLE_DEFAULT).strip()
    return {
        "do_sample": do_sample_raw in LLM_DO_SAMPLE_TRUTHY,
        "do_sample_env": do_sample_raw,
        # Temperature as the graph resolves it at decision time (GAP-15).
        "temperature": float(_resolve_llm_temperature()),
        "seed_env": os.environ.get(LLM_SEED_ENV, "").strip(),
        "max_new_tokens": int(GENERATION_MAX_NEW_TOKENS),
    }


def _cuda_allocator() -> dict[str, Any]:
    from dau.foundation.local_llm import describe_cuda_allocator

    return dict(describe_cuda_allocator())


def build_tool_identity(
    *,
    lora_choice: str,
    seeds: list[int],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Instrument record for a results JSON. Every field is determinable."""

    backend = resolve_backend()
    identity: dict[str, Any] = {
        "backend": backend,
        "model_id": _model_id(backend),
        "quantization": _quantization(backend),
        "dpo": {
            "beta": DPO_BETA,
            "learning_rate": DPO_LEARNING_RATE,
            "epochs": DPO_EPOCHS,
            "batch_size": DPO_BATCH_SIZE,
            "gradient_accumulation_steps": GRADIENT_ACCUMULATION_STEPS,
            "effective_batch_size": DPO_BATCH_SIZE * GRADIENT_ACCUMULATION_STEPS,
            "max_sequence_tokens": DPO_MAX_SEQUENCE_TOKENS,
            "max_grad_norm": DPO_MAX_GRAD_NORM,
        },
        "lora": {
            "choice": lora_choice,
            "enabled_env": os.environ.get(LORA_ENABLED_ENV, LORA_ENABLED_OFF),
            "rank": PER_AGENT_LORA_RANK,
            "alpha": PER_AGENT_LORA_ALPHA,
            "adapter": _adapter_state(),
        },
        # A4/D-066: three declared-but-uncalibrated constants now shape the
        # universe itself. Read straight from constraints so the block cannot
        # drift from the loop it describes (CLAUDE.md 2.8), and carry the
        # calibration flag so nobody reads them as measured (U5/D-030).
        "metabolism": {
            "gain_max": METABOLIC_GAIN_MAX,
            "gain_half_saturation": METABOLIC_GAIN_HALF_SATURATION,
            "grace_events": METABOLIC_GRACE_EVENTS,
            "calibrated": METABOLIC_GAIN_CALIBRATED,
            "death_on_exhaustion": True,
        },
        # K4-b/D-070: F_agent's pool term became a per-event RATE, scaled by
        # the largest harvest the decision→outcome map can yield. Two runs of
        # this harness can now produce the same f_agent from different physics,
        # and nothing else in the results file says which formula ran. Read
        # from the constants the formula reads (CLAUDE.md 2.8); the survival
        # denominator is not restated here because BirthDriftLog carries
        # t_survived and t_generation per lineage, where a reader can see
        # whether they collapsed onto each other.
        "fitness": {
            "w_energy": FITNESS_W_ENERGY,
            "w_pool": FITNESS_W_POOL,
            "w_survival": FITNESS_W_SURVIVAL,
            "pool_term_per_event_max": EXTRACTION_DEFECT,
            "energy_reading": FITNESS_ENERGY_READING,
        },
        # K1/K2/K5 (D-070). Which ordinal every lineage is read at. Two runs of
        # this harness can disagree about what "the endpoint" means without
        # disagreeing about any number in the results file, so the ordinal has
        # to travel with the run that used it.
        "endpoints": {
            "landmark_event": LANDMARK_EVENT,
        },
        "sampling": _sampling(),
        # D-114/D-116. The allocator setting is not a physics constant, but a
        # run that OOMs half way through and one that does not are different
        # measurements, and the difference has to be readable from the file.
        # Read from the environment the process is actually running under
        # (local_llm.describe_cuda_allocator), never restated here.
        "cuda_allocator": _cuda_allocator(),
        "seeds": {
            "n": len(seeds),
            "start": seeds[0] if seeds else None,
            "end": seeds[-1] if seeds else None,
            "list": list(seeds),
        },
        "versions": _versions(),
        "argv": list(sys.argv),
    }
    if extra:
        identity.update(extra)
    return identity
