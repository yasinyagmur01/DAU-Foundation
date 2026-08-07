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
    DPO_BATCH_SIZE,
    DPO_BETA,
    DPO_EPOCHS,
    DPO_LEARNING_RATE,
    DPO_MAX_GRAD_NORM,
    DPO_MAX_SEQUENCE_TOKENS,
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
PLAIN_PROMPT_TEMPLATE: str = "{system}\n\n{user}\n"

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
    # get_peft_model hands back a model in train mode, and _run_dpo_epochs only
    # restores eval when it found eval. Left alone the singleton generates in
    # train mode for the rest of the process.
    model.eval()

    _model = model
    _tokenizer = tokenizer
    _active_agent_id = None
    switch_adapter(model, agent_id)
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


def _reset_active_adapter(model: Any) -> None:
    """Return the in-memory adapter to a fresh zero-B initialisation.

    Agents must not inherit each other's scars: an agent with no adapter on
    disk has to start from the base policy, not from whatever the previously
    trained agent left in the shared singleton.
    """

    try:
        from peft.tuners.lora import LoraLayer
    except ImportError:
        return

    reset_count = 0
    for module in model.modules():
        if not isinstance(module, LoraLayer):
            continue
        try:
            module.reset_lora_parameters(ACTIVE_ADAPTER_NAME, init_lora_weights=True)
            reset_count += 1
        except Exception:  # noqa: BLE001 — fall back to manual zeroing below
            import torch

            with torch.no_grad():
                lora_b = getattr(module, "lora_B", None)
                if lora_b is not None and ACTIVE_ADAPTER_NAME in lora_b:
                    lora_b[ACTIVE_ADAPTER_NAME].weight.zero_()
                    reset_count += 1
    logger.debug("reset %d LoRA layers to fresh init", reset_count)


def _load_adapter_weights(model: Any, adapter_dir: Path) -> bool:
    """Load saved LoRA weights into the single in-memory adapter slot."""

    weights_path = adapter_dir / ADAPTER_WEIGHTS_FILE
    if not weights_path.exists():
        return False
    try:
        from peft import set_peft_model_state_dict
        from safetensors.torch import load_file
    except ImportError:
        return False

    state_dict = load_file(str(weights_path))
    set_peft_model_state_dict(
        model,
        state_dict,
        adapter_name=ACTIVE_ADAPTER_NAME,
    )
    return True


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
    if _active_agent_id == agent_id:
        return

    try:
        from peft import PeftModel
    except ImportError:
        _active_agent_id = agent_id
        return

    if not isinstance(model, PeftModel):
        _disable_adapters(model)
        _active_agent_id = None
        return

    # One in-memory adapter slot, swapped from disk. Registering a slot per
    # agent would make peft write every registered adapter into each agent's
    # directory on save, leaking one agent's training into the next.
    try:
        enable = getattr(model, "enable_adapter_layers", None)
        if callable(enable):
            try:
                enable()
            except Exception:  # noqa: BLE001 — layers may already be enabled
                pass
        set_adapter = getattr(model, "set_adapter", None)
        if callable(set_adapter):
            try:
                set_adapter(ACTIVE_ADAPTER_NAME)
            except Exception:  # noqa: BLE001 — single-adapter models
                pass

        if adapter_exists(agent_id) and _load_adapter_weights(
            model, get_adapter_path(agent_id)
        ):
            _active_agent_id = agent_id
        else:
            _reset_active_adapter(model)
            _active_agent_id = agent_id
    except Exception as exc:  # noqa: BLE001 — inference must fall back to base
        logger.warning("switch_adapter(%s) failed: %s — using base", agent_id, exc)
        _reset_active_adapter(model)
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


def _build_prompt(tokenizer: Any, system: str, user: str) -> tuple[str, bool]:
    """Return (prompt_text, used_chat_template).

    LOCAL_MODEL_NAME is an -Instruct checkpoint: without its chat template the
    model sees no instruction boundary and continues the text instead of
    answering, echoing the prompt back. Fall back to plain concatenation only
    for tokenizers that carry no template.
    """

    messages = [
        {"role": "system", "content": system.strip()},
        {"role": "user", "content": user.strip()},
    ]
    try:
        prompt = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=False,
        )
        return str(prompt), True
    except Exception:  # noqa: BLE001 — templateless tokenizer / test double
        return PLAIN_PROMPT_TEMPLATE.format(
            system=system.strip(),
            user=user.strip(),
        ), False


def generate_completion(
    model: Any,
    tokenizer: Any,
    *,
    system: str,
    user: str,
) -> str:
    """Greedy local completion for LocalBackend.complete()."""

    import torch

    prompt, used_template = _build_prompt(tokenizer, system, user)
    # The chat template already emits BOS; re-adding it shifts the turn header.
    encoded = tokenizer(
        prompt,
        return_tensors="pt",
        add_special_tokens=not used_template,
    )
    if hasattr(model, "device"):
        encoded = {key: value.to(model.device) for key, value in encoded.items()}
    prompt_length = int(encoded["input_ids"].shape[-1])
    eos_token_id = getattr(tokenizer, "eos_token_id", None)
    pad_token_id = getattr(tokenizer, "pad_token_id", None) or eos_token_id
    with torch.no_grad():
        output = model.generate(
            **encoded,
            max_new_tokens=GENERATION_MAX_NEW_TOKENS,
            do_sample=False,
            eos_token_id=eos_token_id,
            pad_token_id=pad_token_id,
        )
    generated = output[0][prompt_length:]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


def _encode_pair_side(
    tokenizer: Any,
    prompt: str,
    completion: str,
    system: str = "",
) -> tuple[list[int], int]:
    """Return (token_ids, prompt_length) for one prompt+completion sequence.

    prompt_length marks where the completion starts so the loss ignores tokens
    the policy did not choose.

    The prompt goes through the same chat template as generate_completion.
    Training on raw text moves the policy in a token context that inference
    never presents: measured against a real trained adapter, the same weights
    shift logits by 13.4 on the raw format and only 3.5 on the chat format.
    """

    prompt_text, used_template = _build_prompt(tokenizer, system, prompt)
    prompt_ids = tokenizer(
        prompt_text,
        add_special_tokens=not used_template,
    )["input_ids"]
    completion_ids = tokenizer(completion, add_special_tokens=False)["input_ids"]
    eos_id = getattr(tokenizer, "eos_token_id", None)
    if eos_id is not None:
        completion_ids = list(completion_ids) + [eos_id]
    sequence = list(prompt_ids) + list(completion_ids)
    if len(sequence) > DPO_MAX_SEQUENCE_TOKENS:
        # Keep the completion intact; the prompt head is the expendable part.
        overflow = len(sequence) - DPO_MAX_SEQUENCE_TOKENS
        prompt_ids = list(prompt_ids)[overflow:]
        sequence = list(prompt_ids) + list(completion_ids)
    return sequence, len(prompt_ids)


def _sequence_logprob(
    model: Any,
    token_ids: list[int],
    prompt_length: int,
    device: Any,
) -> Any:
    """Sum log p(token | prefix) over completion tokens only."""

    import torch

    input_ids = torch.tensor([token_ids], device=device)
    logits = model(input_ids=input_ids).logits[0, :-1, :]
    targets = input_ids[0, 1:]
    log_probs = torch.log_softmax(logits.float(), dim=-1)
    token_log_probs = log_probs.gather(-1, targets.unsqueeze(-1)).squeeze(-1)
    # targets[i] is token i+1, so completion tokens start at prompt_length - 1.
    return token_log_probs[prompt_length - 1 :].sum()


def _reference_logprobs(
    model: Any,
    encoded_batch: list[tuple[list[int], int, list[int], int]],
    device: Any,
) -> list[tuple[Any, Any]]:
    """Log-probs under the frozen base — same model, adapters disabled."""

    import torch

    disable_adapter = getattr(model, "disable_adapter", None)
    reference: list[tuple[Any, Any]] = []
    with torch.no_grad():
        if callable(disable_adapter):
            with disable_adapter():
                for chosen_ids, chosen_len, rejected_ids, rejected_len in encoded_batch:
                    reference.append(
                        (
                            _sequence_logprob(model, chosen_ids, chosen_len, device),
                            _sequence_logprob(
                                model, rejected_ids, rejected_len, device
                            ),
                        )
                    )
        else:
            for chosen_ids, chosen_len, rejected_ids, rejected_len in encoded_batch:
                reference.append(
                    (
                        _sequence_logprob(model, chosen_ids, chosen_len, device),
                        _sequence_logprob(model, rejected_ids, rejected_len, device),
                    )
                )
    return reference


def _enable_adapter_training(model: Any) -> None:
    """Re-arm LoRA gradients before a train step.

    Inference paths call disable_adapter_layers(), and peft's enable_adapters
    (False) clears requires_grad on every adapter tensor. Without re-arming,
    the optimizer would see no parameters and the adapter would stay at its
    zero-initialised lora_B — an identity transform.
    """

    enable = getattr(model, "enable_adapter_layers", None)
    if callable(enable):
        try:
            enable()
        except Exception:  # noqa: BLE001 — fall through to manual re-arm
            pass
    active = getattr(model, "active_adapter", None)
    set_adapter = getattr(model, "set_adapter", None)
    if callable(set_adapter) and active:
        try:
            set_adapter(active)
        except Exception:  # noqa: BLE001 — fall through to manual re-arm
            pass
    for name, parameter in model.named_parameters():
        if "lora_" in name:
            parameter.requires_grad_(True)


def _run_dpo_epochs(
    model: Any,
    tokenizer: Any,
    pairs: list[Any],
) -> dict[str, Any]:
    """DPO micro-train over PE-ranked pairs; updates LoRA weights in place.

    Reference policy is this same model with adapters disabled, which is exact
    for LoRA: disabling the adapter restores the frozen base.
    """

    import torch

    device = getattr(model, "device", None) or torch.device("cpu")
    _enable_adapter_training(model)
    trainable = [p for p in model.parameters() if p.requires_grad]
    if not trainable:
        raise RuntimeError("no trainable LoRA parameters — adapter not attached")

    optimizer = torch.optim.AdamW(trainable, lr=DPO_LEARNING_RATE)
    was_training = model.training
    model.train()

    total_loss = 0.0
    total_accuracy = 0.0
    step_count = 0
    try:
        for _ in range(DPO_EPOCHS):
            for start in range(0, len(pairs), DPO_BATCH_SIZE):
                batch = pairs[start : start + DPO_BATCH_SIZE]
                encoded = []
                for pair in batch:
                    system = str(getattr(pair, "system", "") or "")
                    chosen_ids, chosen_len = _encode_pair_side(
                        tokenizer, pair.prompt, pair.chosen, system
                    )
                    rejected_ids, rejected_len = _encode_pair_side(
                        tokenizer, pair.prompt, pair.rejected, system
                    )
                    encoded.append(
                        (chosen_ids, chosen_len, rejected_ids, rejected_len)
                    )

                reference = _reference_logprobs(model, encoded, device)

                optimizer.zero_grad()
                batch_loss = None
                for (chosen_ids, chosen_len, rejected_ids, rejected_len), (
                    ref_chosen,
                    ref_rejected,
                ) in zip(encoded, reference):
                    policy_chosen = _sequence_logprob(
                        model, chosen_ids, chosen_len, device
                    )
                    policy_rejected = _sequence_logprob(
                        model, rejected_ids, rejected_len, device
                    )
                    logits = (policy_chosen - policy_rejected) - (
                        ref_chosen - ref_rejected
                    )
                    loss = -torch.nn.functional.logsigmoid(DPO_BETA * logits)
                    batch_loss = loss if batch_loss is None else batch_loss + loss
                    total_accuracy += float(logits.item() > 0.0)
                    step_count += 1

                if batch_loss is None:
                    continue
                batch_loss = batch_loss / len(encoded)
                batch_loss.backward()
                torch.nn.utils.clip_grad_norm_(trainable, DPO_MAX_GRAD_NORM)
                optimizer.step()
                total_loss += float(batch_loss.item()) * len(encoded)
    finally:
        if not was_training:
            model.eval()

    if step_count == 0:
        raise RuntimeError("no DPO steps executed")
    return {
        "dpo_loss": total_loss / step_count,
        "dpo_accuracy": total_accuracy / step_count,
        "dpo_steps": step_count,
    }


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

    pair_count = len(pairs) if pairs is not None else 0
    if pair_count == 0:
        return {
            "trained": False,
            "skipped": True,
            "reason": "no preference pairs",
            "agent_id": agent_id,
        }

    tokenizer = _tokenizer
    if tokenizer is None:
        return {
            "trained": False,
            "skipped": True,
            "reason": "no tokenizer",
            "agent_id": agent_id,
            "pair_count": pair_count,
        }

    try:
        stats = _run_dpo_epochs(active, tokenizer, list(pairs or []))
    except Exception as exc:  # noqa: BLE001 — generation end must not crash
        logger.warning("DPO micro-train failed for %s: %s", agent_id, exc)
        return {
            "trained": False,
            "skipped": True,
            "reason": f"train failed: {exc}",
            "agent_id": agent_id,
            "pair_count": pair_count,
        }

    save_agent_adapter(active, agent_id)
    return {
        "trained": True,
        "skipped": False,
        "reason": "ok",
        "agent_id": agent_id,
        "pair_count": pair_count,
        "adapter_dir": str(get_adapter_path(agent_id)),
        **stats,
    }


def reset_local_llm_singletons_for_tests() -> None:
    """Clear process singletons — test isolation only."""

    global _model, _tokenizer, _active_agent_id
    _model = None
    _tokenizer = None
    _active_agent_id = None
