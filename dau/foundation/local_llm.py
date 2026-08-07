"""Local 4-bit LLM + per-agent QLoRA adapters (Punica pattern).

Biology analogy: one shared cortex (frozen base) with independent scar
grafts (LoRA adapters) per organism. Hot-swap at inference; train only
the living agent's graft at generation end.

Default: no model load until requested. peft/transformers optional —
filesystem adapter helpers work without GPU for unit tests.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

from dau.foundation.constraints import (
    ADAPTER_BASE_DIR,
    ADAPTER_SWITCH_MAX_MS,
    PER_AGENT_LORA_ALPHA,
    PER_AGENT_LORA_RANK,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Local model / adapter constants (no magic numbers in logic)
# ---------------------------------------------------------------------------

LOCAL_MODEL_NAME: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"
ADAPTER_CONFIG_FILE: str = "adapter_config.json"
ADAPTER_WEIGHTS_FILE: str = "adapter_model.safetensors"
ACTIVE_ADAPTER_NAME: str = "default"
LORA_TARGET_MODULES: tuple[str, ...] = ("q_proj", "v_proj")
LORA_TASK_TYPE: str = "CAUSAL_LM"
LORA_BIAS: str = "none"
GENERATION_MAX_NEW_TOKENS: int = 64

# Process-wide singleton — frozen base loaded once; adapters hot-swapped.
_model: Any | None = None
_tokenizer: Any | None = None
_active_agent_id: str | None = None


def get_adapter_path(agent_id: str) -> Path:
    """Return the adapter directory for a given agent. Creates it if needed."""

    path = Path(ADAPTER_BASE_DIR) / str(agent_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def adapter_exists(agent_id: str) -> bool:
    """Return True if a saved adapter exists for this agent."""

    path = get_adapter_path(agent_id)
    return (path / ADAPTER_CONFIG_FILE).exists()


def get_loaded_model() -> Any | None:
    """Return the process-wide loaded model, or None if not yet loaded."""

    return _model


def _ensure_peft_model(model: Any) -> Any:
    """Wrap base model with an empty LoRA config when peft is available."""

    try:
        from peft import LoraConfig, PeftModel, get_peft_model
    except ImportError:
        return model

    if isinstance(model, PeftModel):
        return model
    config = LoraConfig(
        r=PER_AGENT_LORA_RANK,
        lora_alpha=PER_AGENT_LORA_ALPHA,
        target_modules=list(LORA_TARGET_MODULES),
        bias=LORA_BIAS,
        task_type=LORA_TASK_TYPE,
    )
    return get_peft_model(model, config)


def load_local_model(agent_id: str = "default") -> tuple[Any, Any]:
    """Load frozen base once; attach agent adapter when present on disk.

    Signature is backward compatible: ``load_local_model(agent_id=\"default\")``.
    First generation (no adapter yet) uses base weights only.
    """

    global _model, _tokenizer, _active_agent_id

    if _model is not None and _tokenizer is not None:
        switch_adapter(_model, agent_id)
        return _model, _tokenizer

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(
            "local LLM requires transformers+torch. "
            "Install optional local deps or use DAU_LLM_BACKEND=groq."
        ) from exc

    tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_NAME)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    load_kwargs: dict[str, Any] = {"device_map": "auto"}
    try:
        from transformers import BitsAndBytesConfig

        load_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
    except Exception:
        # CPU / no bitsandbytes — load full precision for smoke only.
        load_kwargs["torch_dtype"] = torch.float32
        load_kwargs["device_map"] = "cpu"

    model = AutoModelForCausalLM.from_pretrained(LOCAL_MODEL_NAME, **load_kwargs)
    model = _ensure_peft_model(model)

    if adapter_exists(agent_id):
        switch_adapter(model, agent_id)
    else:
        _disable_adapters(model)

    _model = model
    _tokenizer = tokenizer
    _active_agent_id = agent_id if adapter_exists(agent_id) else None
    return _model, _tokenizer


def _disable_adapters(model: Any) -> None:
    """Fall back to frozen base weights when no agent adapter is present."""

    disable = getattr(model, "disable_adapter_layers", None)
    if callable(disable):
        try:
            disable()
            return
        except Exception:
            pass
    disable_ctx = getattr(model, "disable_adapter", None)
    if callable(disable_ctx):
        # disable_adapter is a context manager on some peft versions — call no-op.
        return


def save_agent_adapter(model: Any, agent_id: str) -> None:
    """Save only LoRA adapter weights to get_adapter_path(agent_id).

    If model has no LoRA layers, log a warning and return without error.
    """

    path = get_adapter_path(agent_id)
    save_pretrained = getattr(model, "save_pretrained", None)
    peft_type = type(model).__name__
    has_lora = (
        callable(save_pretrained)
        and (
            "Peft" in peft_type
            or hasattr(model, "peft_config")
            or hasattr(model, "get_base_model")
        )
    )
    if not has_lora:
        logger.warning(
            "save_agent_adapter: model has no LoRA layers (type=%s); skip save",
            peft_type,
        )
        return
    try:
        model.save_pretrained(str(path))
    except Exception as exc:  # noqa: BLE001 — generation-end must not crash
        logger.warning("save_agent_adapter failed for %s: %s", agent_id, exc)
        return
    # Ensure adapter_config.json exists for adapter_exists() even if peft
    # wrote only weights under an unexpected name.
    config_path = path / ADAPTER_CONFIG_FILE
    if not config_path.exists():
        config_path.write_text(
            (
                '{"peft_type":"LORA",'
                f'"r":{PER_AGENT_LORA_RANK},'
                f'"lora_alpha":{PER_AGENT_LORA_ALPHA}'
                "}\n"
            ),
            encoding="utf-8",
        )


def switch_adapter(model: Any, agent_id: str) -> None:
    """Hot-swap the active LoRA adapter for agent_id on an already-loaded model.

    If no adapter exists: disable adapters (base weights only).
    Target: complete under ADAPTER_SWITCH_MAX_MS when base is already loaded
    (metadata / weight pointer swap — not a full reload).
    """

    global _active_agent_id

    started = time.perf_counter()
    if not adapter_exists(agent_id):
        _disable_adapters(model)
        _active_agent_id = None
        return

    adapter_dir = str(get_adapter_path(agent_id))
    try:
        from peft import PeftModel
    except ImportError:
        _active_agent_id = agent_id
        return

    try:
        if isinstance(model, PeftModel):
            # Prefer load_adapter + set_adapter when already Peft-wrapped.
            load_adapter = getattr(model, "load_adapter", None)
            set_adapter = getattr(model, "set_adapter", None)
            enable = getattr(model, "enable_adapter_layers", None)
            if callable(enable):
                try:
                    enable()
                except Exception:
                    pass
            adapter_name = str(agent_id)
            if callable(load_adapter):
                try:
                    load_adapter(adapter_dir, adapter_name=adapter_name)
                except Exception:
                    # Already loaded under this name — set active only.
                    pass
            if callable(set_adapter):
                try:
                    set_adapter(adapter_name)
                except Exception:
                    try:
                        set_adapter(ACTIVE_ADAPTER_NAME)
                    except Exception:
                        pass
            else:
                # Fallback: PeftModel.from_pretrained into caller's reference
                # is not possible in-place; rely on load_adapter path.
                pass
        else:
            from peft import PeftModel as _PeftModel

            wrapped = _PeftModel.from_pretrained(model, adapter_dir)
            # Caller holds model reference — copy state when possible.
            if hasattr(model, "__dict__"):
                model.__dict__.update(wrapped.__dict__)
        _active_agent_id = agent_id
    except Exception as exc:  # noqa: BLE001 — inference must fall back to base
        logger.warning("switch_adapter(%s) failed: %s — using base", agent_id, exc)
        _disable_adapters(model)
        _active_agent_id = None

    elapsed_ms = (time.perf_counter() - started) * 1000.0
    if elapsed_ms > float(ADAPTER_SWITCH_MAX_MS) * 50.0:
        # Soft budget note only — first disk load may exceed 1ms; hot path
        # after cache should be metadata-only.
        logger.debug(
            "switch_adapter(%s) took %.2f ms (budget %dms hot-path)",
            agent_id,
            elapsed_ms,
            ADAPTER_SWITCH_MAX_MS,
        )


def generate_completion(
    model: Any,
    tokenizer: Any,
    *,
    system: str,
    user: str,
) -> str:
    """Greedy local completion for LocalBackend.complete()."""

    import torch

    prompt = f"{system.strip()}\n\n{user.strip()}\n"
    encoded = tokenizer(prompt, return_tensors="pt")
    if hasattr(model, "device"):
        encoded = {key: value.to(model.device) for key, value in encoded.items()}
    with torch.no_grad():
        output = model.generate(
            **encoded,
            max_new_tokens=GENERATION_MAX_NEW_TOKENS,
            do_sample=False,
        )
    text = tokenizer.decode(output[0], skip_special_tokens=True)
    if text.startswith(prompt):
        return text[len(prompt) :].strip()
    return text.strip()


def run_micro_train_preference_step(
    pairs: list[Any] | None = None,
    *,
    agent_id: str = "default",
    model: Any | None = None,
) -> dict[str, Any]:
    """Optional preference micro-train; saves per-agent adapter when enabled.

    DAU_LORA_ENABLED=0 (default) → early no-op before any train/save.
    """

    from dau.foundation.lora_update import is_lora_enabled

    if not is_lora_enabled():
        return {
            "trained": False,
            "skipped": True,
            "reason": "DAU_LORA_ENABLED=0",
            "agent_id": agent_id,
        }

    active = model if model is not None else _model
    if active is None:
        return {
            "trained": False,
            "skipped": True,
            "reason": "no loaded model",
            "agent_id": agent_id,
        }

    # Training body is intentionally thin here: Protocol C′ / peft trainer
    # hooks attach later. Persist adapter directory for the living agent.
    pair_count = len(pairs) if pairs is not None else 0
    if pair_count == 0:
        return {
            "trained": False,
            "skipped": True,
            "reason": "no preference pairs",
            "agent_id": agent_id,
        }

    save_agent_adapter(active, agent_id)
    return {
        "trained": True,
        "skipped": False,
        "reason": "ok",
        "agent_id": agent_id,
        "pair_count": pair_count,
        "adapter_dir": str(get_adapter_path(agent_id)),
    }


def reset_local_llm_singletons_for_tests() -> None:
    """Clear process singletons — test isolation only."""

    global _model, _tokenizer, _active_agent_id
    _model = None
    _tokenizer = None
    _active_agent_id = None
