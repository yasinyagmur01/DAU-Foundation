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
    DPO_GRADIENT_ACCUMULATION_STEPS,
    DPO_EPOCHS,
    DPO_LEARNING_RATE,
    DPO_MAX_GRAD_NORM,
    DPO_MAX_SEQUENCE_TOKENS,
    LORA_B_ABS_SUM_UNREAD,
    LORA_INIT_SEED,
    PER_AGENT_LORA_ALPHA,
    PER_AGENT_LORA_RANK,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Local model / adapter constants (no magic numbers in logic)
# ---------------------------------------------------------------------------

LOCAL_MODEL_NAME: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"
# U3/D-019 needs the same harness pointed at two checkpoints. Unset or blank
# means "not set" and yields LOCAL_MODEL_NAME, matching graph's temperature
# and backend resolvers (GAP-15, D-023). No value validation: any HF repo id
# is legal here, and a wrong one fails loudly inside from_pretrained.
LOCAL_MODEL_ENV: str = "DAU_LOCAL_MODEL"
MODEL_ALREADY_LOADED_MESSAGE: str = (
    "Refusing to serve {loaded!r} for a request for {requested!r}. The base "
    "model is a process-wide singleton, so changing {env} after a load cannot "
    "swap it — the run would keep generating with the old weights while "
    "tool_identity reported the new name. Measure one model per process."
)
ADAPTER_CONFIG_FILE: str = "adapter_config.json"
ADAPTER_WEIGHTS_FILE: str = "adapter_model.safetensors"
ACTIVE_ADAPTER_NAME: str = "default"
LORA_TARGET_MODULES: tuple[str, ...] = ("q_proj", "v_proj")
LORA_TASK_TYPE: str = "CAUSAL_LM"
LORA_BIAS: str = "none"
GENERATION_MAX_NEW_TOKENS: int = 64
PLAIN_PROMPT_TEMPLATE: str = "{system}\n\n{user}\n"
LLM_DO_SAMPLE_ENV: str = "DAU_LLM_DO_SAMPLE"
LLM_TEMPERATURE_ENV: str = "DAU_LLM_TEMPERATURE"
LLM_SEED_ENV: str = "DAU_LLM_SEED"
LLM_DO_SAMPLE_DEFAULT: str = "0"
LLM_TEMPERATURE_DEFAULT: float = 0.0
LLM_DO_SAMPLE_TRUTHY: frozenset[str] = frozenset({"1", "true", "TRUE", "yes", "YES"})
# Floor below which sampling is treated as greedy even if the flag is on.
LLM_SAMPLE_TEMPERATURE_FLOOR: float = 1e-6
# D-020: pinned, not inherited. The point is not that nf4 beats fp4 — it is
# that leaving the flag unwritten hands the tool to a library default (fp4 /
# double_quant off in transformers 5.14.1), which can change under us and
# invalidate a pre-registration with nobody noticing. Same risk D-018 refused
# to accept for a remote endpoint, only on our own machine.
QUANT_TYPE_NF4: str = "nf4"
DOUBLE_QUANT_ENABLED: bool = True

# Process-wide singleton — frozen base loaded once; adapters hot-swapped.
_model: Any | None = None
_tokenizer: Any | None = None
_active_agent_id: str | None = None
# What is actually in VRAM, as opposed to what the env currently asks for.
# tool_identity reports this when set, so the results file names the weights
# that produced the numbers rather than the configuration at write time.
_loaded_model_name: str | None = None


def _resolve_generation_sampling() -> tuple[bool, float]:
    """Return (do_sample, temperature) from env. Default remains greedy."""

    flagged = os.environ.get(LLM_DO_SAMPLE_ENV, LLM_DO_SAMPLE_DEFAULT).strip()
    if flagged not in LLM_DO_SAMPLE_TRUTHY:
        return False, LLM_TEMPERATURE_DEFAULT
    raw = os.environ.get(LLM_TEMPERATURE_ENV, str(LLM_TEMPERATURE_DEFAULT)).strip()
    try:
        temperature = float(raw)
    except ValueError:
        return False, LLM_TEMPERATURE_DEFAULT
    if temperature <= LLM_SAMPLE_TEMPERATURE_FLOOR:
        return False, LLM_TEMPERATURE_DEFAULT
    return True, temperature


def adapter_dir(agent_id: str) -> Path:
    """Where this agent's adapter lives. Read-only — does not create it."""

    return Path(ADAPTER_BASE_DIR) / str(agent_id)


def get_adapter_path(agent_id: str) -> Path:
    """Return the adapter directory for a given agent. Creates it if needed."""

    path = adapter_dir(agent_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def adapter_exists(agent_id: str) -> bool:
    """Return True if a saved adapter exists for this agent.

    Asks through adapter_dir, not get_adapter_path: a query that creates the
    directory it is asked about leaves a trail of empty ones (79 of the 114
    under dau_runs/adapters on 2026-08-10 were this side effect) and makes
    I0.7's read-only audit mutate the thing it inspects.
    """

    return (adapter_dir(agent_id) / ADAPTER_CONFIG_FILE).exists()


def get_loaded_model() -> Any | None:
    """Return the process-wide loaded model, or None if not yet loaded."""

    return _model


def build_load_kwargs() -> dict[str, Any]:
    """from_pretrained kwargs for the base model — the single source of truth.

    4-bit when bitsandbytes is importable, full precision on CPU otherwise.
    quant_type and double_quant are written out rather than inherited from
    BitsAndBytesConfig (D-020): a library default can change between versions
    and silently change the instrument. describe_quantization reads this
    config back, so the tool-identity block cannot disagree with the loader.
    """

    import torch

    kwargs: dict[str, Any] = {"device_map": "auto"}
    try:
        from transformers import BitsAndBytesConfig

        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type=QUANT_TYPE_NF4,
            bnb_4bit_use_double_quant=DOUBLE_QUANT_ENABLED,
        )
    except Exception:  # noqa: BLE001 — CPU / no bitsandbytes: smoke only
        kwargs["torch_dtype"] = torch.float32
        kwargs["device_map"] = "cpu"
    return kwargs


def describe_quantization() -> dict[str, Any]:
    """Report the quantization the base model is actually loaded with.

    Read from build_load_kwargs, never re-derived: a tool-identity block that
    builds its own config would eventually disagree with the loader, which is
    exactly the silent mismatch it is meant to expose.
    """

    try:
        kwargs = build_load_kwargs()
    except ImportError:
        return {"available": False, "reason": "torch not installed"}

    config = kwargs.get("quantization_config")
    if config is None:
        return {
            "available": True,
            "load_in_4bit": False,
            "dtype": str(kwargs.get("torch_dtype")),
            "device_map": str(kwargs.get("device_map")),
        }
    return {
        "available": True,
        "load_in_4bit": bool(getattr(config, "load_in_4bit", False)),
        "quant_type": str(getattr(config, "bnb_4bit_quant_type", "")),
        "compute_dtype": str(getattr(config, "bnb_4bit_compute_dtype", "")),
        "double_quant": bool(getattr(config, "bnb_4bit_use_double_quant", False)),
        "device_map": str(kwargs.get("device_map")),
    }


def _ensure_peft_model(model: Any) -> Any:
    """Wrap base model with an empty LoRA config when peft is available.

    Built on a forked RNG for the same reason the reset is (D-042).
    get_peft_model initialises lora_A, and this runs exactly once per process
    — inside whichever arm happened to load the model first. That arm would
    otherwise pay an RNG draw none of the others do, which is precisely the
    position dependence D-042 removes.
    """

    try:
        import torch
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
    devices = [torch.cuda.current_device()] if torch.cuda.is_available() else []
    with torch.random.fork_rng(devices=devices):
        torch.manual_seed(LORA_INIT_SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(LORA_INIT_SEED)
        return get_peft_model(model, config)


def resolve_local_model_name() -> str:
    """Return the checkpoint to load — DAU_LOCAL_MODEL, else LOCAL_MODEL_NAME.

    Unset or blank counts as "not set", the same reading graph applies to
    DAU_LLM_TEMPERATURE (GAP-15) and DAU_LLM_BACKEND (D-023). Values are not
    validated against a list: any HF repo id is legal, and a wrong one raises
    inside from_pretrained rather than falling through to a default.
    """

    raw = os.environ.get(LOCAL_MODEL_ENV, "").strip()
    if not raw:
        return LOCAL_MODEL_NAME
    return raw


def get_loaded_model_name() -> str | None:
    """Return the checkpoint currently in VRAM, or None before the first load."""

    return _loaded_model_name


def load_local_model(agent_id: str = "default") -> tuple[Any, Any]:
    """Load frozen base once; attach agent adapter when present on disk.

    Signature is backward compatible: ``load_local_model(agent_id=\"default\")``.
    First generation (no adapter yet) uses base weights only.

    Quantization comes from build_load_kwargs so describe_quantization() can
    report what is actually loaded. Two constructions would drift, and a
    results file that misreports its own quantization is the failure D-004
    exists to prevent.
    """

    global _model, _tokenizer, _active_agent_id, _loaded_model_name

    model_name = resolve_local_model_name()
    if _model is not None and _tokenizer is not None:
        if _loaded_model_name != model_name:
            raise RuntimeError(
                MODEL_ALREADY_LOADED_MESSAGE.format(
                    loaded=_loaded_model_name,
                    requested=model_name,
                    env=LOCAL_MODEL_ENV,
                )
            )
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

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    load_kwargs = build_load_kwargs()

    model = AutoModelForCausalLM.from_pretrained(model_name, **load_kwargs)
    model = _ensure_peft_model(model)
    # get_peft_model hands back a model in train mode, and _run_dpo_epochs only
    # restores eval when it found eval. Left alone the singleton generates in
    # train mode for the rest of the process.
    model.eval()

    _model = model
    _tokenizer = tokenizer
    _active_agent_id = None
    _loaded_model_name = model_name
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

    D-042 — the reset runs on its own RNG, forked from the live stream:

    ``reset_lora_parameters`` re-initialises lora_A with kaiming_uniform_,
    which both DRAWS from the torch stream and lands wherever that stream
    happens to be. Neither is acceptable here. Drawing meant the reset shifted
    the life's sampling stream by an amount that depended on how many resets
    had already happened; landing meant lora_A itself became a function of
    position in the process. Measured: the same shuffle arm digests to
    598d67bce291 as the first arm of a process and 43930cf5013b as the third,
    with one training in between. Since lived always runs first and shuffle
    third, that difference sat inside the experiment's primary contrast as a
    systematic term — one that repeats identically every run, so it never
    averages out.

    fork_rng closes both: the draw is taken from a private stream seeded by a
    constant, and the outer stream is restored untouched. Phase 1 was never
    affected — lora_B is zero there, so the adapter is an identity transform
    and lora_A cannot reach the decisions. It is training that turns the
    starting point into an outcome.

    This supersedes the older symmetry argument in switch_adapter's docstring,
    which kept the draw but made every arm pay it equally. Equal consumption
    fixed phase1 vs phase2; it could not fix arm vs arm.
    """

    try:
        import torch
        from peft.tuners.lora import LoraLayer
    except ImportError:
        return

    devices = [torch.cuda.current_device()] if torch.cuda.is_available() else []
    reset_count = 0
    with torch.random.fork_rng(devices=devices):
        torch.manual_seed(LORA_INIT_SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(LORA_INIT_SEED)
        for module in model.modules():
            if not isinstance(module, LoraLayer):
                continue
            try:
                module.reset_lora_parameters(
                    ACTIVE_ADAPTER_NAME, init_lora_weights=True
                )
                reset_count += 1
            except Exception:  # noqa: BLE001 — fall back to manual zeroing below
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

    If no adapter exists: reset to a fresh identity graft (base policy).
    Target: complete under ADAPTER_SWITCH_MAX_MS when base is already loaded
    (metadata / weight pointer swap — not a full reload).

    Do not short-circuit on ``_active_agent_id == agent_id``. Lived phase2
    needs a disk reload after training even when the agent_id did not change,
    and a NULL arm's second phase must be reset like its first.

    ⚠ This used to read "a no-disk reset draws torch RNG for LoRA-A; skipping
    it leaves sampling on a different stream". As of D-042 the reset draws
    nothing — it runs on a forked stream — so calling it is RNG-neutral and
    the symmetry argument no longer applies. The call is still unconditional,
    now for the reason above.
    """

    global _active_agent_id

    started = time.perf_counter()

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
        #
        # GAP-6: this is host-side dispatch time, not GPU completion. Making it
        # true would need a torch.cuda.synchronize() here, and this runs on
        # every local decision — stalling the pipeline 50+ times a phase to
        # sharpen a debug log is a bad trade. Labelled instead of measured, so
        # the number is not read as something it is not (2.8).
        logger.debug(
            "switch_adapter(%s) took %.2f ms host-side (budget %dms hot-path; "
            "GPU work may still be in flight)",
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
    """Local completion for LocalBackend.complete().

    Default is greedy. ``DAU_LLM_DO_SAMPLE=1`` with ``DAU_LLM_TEMPERATURE`` > 0
    enables sampling. Each sampled call re-seeds from ``DAU_LLM_SEED`` and the
    prompt so prior RNG consumers (LoRA reset, model load, MiniLM) cannot shift
    the stream — required for NULL phase1≡phase2 under sampling.
    """

    import hashlib
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
    do_sample, temperature = _resolve_generation_sampling()
    generate_kwargs: dict[str, Any] = {
        "max_new_tokens": GENERATION_MAX_NEW_TOKENS,
        "do_sample": do_sample,
        "eos_token_id": eos_token_id,
        "pad_token_id": pad_token_id,
    }
    if do_sample:
        generate_kwargs["temperature"] = temperature
        phase_seed_raw = os.environ.get(LLM_SEED_ENV, "0").strip()
        try:
            phase_seed = int(phase_seed_raw)
        except ValueError:
            phase_seed = 0
        digest = hashlib.sha256(f"{phase_seed}:{prompt}".encode("utf-8")).hexdigest()
        step_seed = int(digest[:16], 16) % (2**31)
        torch.manual_seed(step_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(step_seed)
    with torch.no_grad():
        output = model.generate(**encoded, **generate_kwargs)
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


def _enable_gradient_checkpointing(model: Any) -> bool:
    """Turn on gradient checkpointing for the DPO step when the model supports it.

    Returns True only when enable succeeded so the caller can restore afterward.
    PeftModel may need the flag on the wrapped base; try both surfaces.
    """

    for target in (model, getattr(model, "get_base_model", lambda: None)()):
        if target is None:
            continue
        enable = getattr(target, "gradient_checkpointing_enable", None)
        if not callable(enable):
            continue
        try:
            enable(gradient_checkpointing_kwargs={"use_reentrant": False})
            return True
        except TypeError:
            try:
                enable()
                return True
            except Exception:  # noqa: BLE001 — fall through
                continue
        except Exception:  # noqa: BLE001 — fall through to next target
            continue
    return False


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


def _release_train_memory(trained_parameters: list[Any]) -> None:
    """Drop the train step's gradients and its cached CUDA blocks (GAP-6).

    Two separate concerns that happen to share a home:

    Isolation — the adapter slot is reused across agents, so a stale .grad on
    a LoRA tensor is one agent's state sitting on the next agent's weights.
    Setting it to None rather than zeroing releases the buffer as well.

    Memory — the DPO step is the run's high-water mark (the D-034 pilot
    already logged one OOM warning), and the blocks it cached stay reserved
    for an allocator that generation cannot use for its own KV cache.

    Deliberately NOT called from switch_adapter, which graph.agent_node runs
    on every local decision: empty_cache walks the whole allocator, so paying
    it 50+ times a phase would buy nothing — the swap allocates nothing to
    release. The cost belongs where the allocation was made.
    """

    for parameter in trained_parameters:
        parameter.grad = None
    try:
        import torch
    except ImportError:  # pragma: no cover — torch absent means no train path
        return
    if torch.cuda.is_available():
        # After the frees above, so the blocks they released are collected too.
        torch.cuda.empty_cache()


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
    checkpointing = _enable_gradient_checkpointing(model)
    config = getattr(model, "config", None)
    prior_use_cache = getattr(config, "use_cache", None)
    if config is not None:
        config.use_cache = False

    total_loss = 0.0
    total_accuracy = 0.0
    step_count = 0
    optimizer_step_count = 0
    # I1.3. clip_grad_norm_ already computes the pre-clip norm and we were
    # throwing it away. Keeping it answers two questions nothing else can:
    # whether any gradient reached the optimizer at all (a norm of exactly 0
    # means the step was a no-op even though the optimizer ran), and how often
    # the norm exceeded DPO_MAX_GRAD_NORM. The second matters because a run
    # that clips on every step has an effective step size set by the clip
    # ceiling, not by the DPO_LEARNING_RATE locked in D-029.
    grad_norm_min = float("inf")
    grad_norm_total = 0.0
    clipped_step_count = 0
    accumulation = max(1, int(DPO_GRADIENT_ACCUMULATION_STEPS))
    # Micro-batches per epoch. The last accumulation group is usually short —
    # with 1-2 surviving pairs it is the ONLY group — so its size is computed
    # rather than assumed, otherwise the tail would be silently under-weighted
    # or, worse, never stepped at all.
    micro_batches = (len(pairs) + DPO_BATCH_SIZE - 1) // DPO_BATCH_SIZE
    try:
        for _ in range(DPO_EPOCHS):
            optimizer.zero_grad()
            pending = 0
            for micro_index, start in enumerate(
                range(0, len(pairs), DPO_BATCH_SIZE)
            ):
                group_index = micro_index // accumulation
                group_size = min(
                    accumulation, micro_batches - group_index * accumulation
                )
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
                # Reported loss keeps its old meaning — mean over pairs. Only
                # the tensor that reaches backward() carries the accumulation
                # divisor, so dpo_loss stays comparable across runs.
                mean_batch_loss = batch_loss / len(encoded)
                (mean_batch_loss / group_size).backward()
                total_loss += float(mean_batch_loss.item()) * len(encoded)

                pending += 1
                if pending == group_size:
                    grad_norm = float(
                        torch.nn.utils.clip_grad_norm_(trainable, DPO_MAX_GRAD_NORM)
                    )
                    # Pre-clip norm, which is what clip_grad_norm_ returns.
                    grad_norm_min = min(grad_norm_min, grad_norm)
                    grad_norm_total += grad_norm
                    if grad_norm > DPO_MAX_GRAD_NORM:
                        clipped_step_count += 1
                    optimizer.step()
                    optimizer.zero_grad()
                    optimizer_step_count += 1
                    pending = 0

            if pending:  # pragma: no cover — group_size math should prevent it
                raise RuntimeError(
                    f"{pending} micro-step(s) were accumulated but never "
                    "stepped: their gradient would be discarded silently"
                )
    finally:
        # Checkpointing and use_cache=False make generation far slower, so they
        # must not outlive the train step on this shared singleton.
        if checkpointing:
            disable = getattr(model, "gradient_checkpointing_disable", None)
            if disable is not None:
                disable()
        if config is not None and prior_use_cache is not None:
            config.use_cache = prior_use_cache
        if not was_training:
            model.eval()
        # GAP-6. There is ONE in-memory adapter slot (see switch_adapter), so
        # these same tensors are what the next agent's adapter loads into, and
        # whatever .grad this arm left is still hanging off them. zero_grad at
        # the top of the next epoch loop happens to clear it, but that puts one
        # agent's isolation in the hands of another call's ordering — the exact
        # shape of the leak f25b0ef and D-042 both turned out to be.
        _release_train_memory(trainable)

    if step_count == 0:
        raise RuntimeError("no DPO steps executed")
    return {
        "dpo_loss": total_loss / step_count,
        "dpo_accuracy": total_accuracy / step_count,
        # dpo_steps keeps counting micro-steps (one per pair) so its meaning is
        # unchanged; the optimizer count is a new field rather than a silent
        # redefinition of an existing one.
        "dpo_steps": step_count,
        "dpo_optimizer_steps": optimizer_step_count,
        "dpo_gradient_accumulation_steps": accumulation,
        # I1.3. Reported from what the step actually did, never from the
        # constants that configured it (§2.8) — a run whose gradients are all
        # clipped must not read as one whose learning rate was honoured.
        "dpo_grad_norm_min": (
            grad_norm_min if optimizer_step_count else GRAD_NORM_UNREAD
        ),
        "dpo_grad_norm_mean": (
            grad_norm_total / optimizer_step_count
            if optimizer_step_count
            else GRAD_NORM_UNREAD
        ),
        "dpo_clipped_steps": clipped_step_count,
    }


def lora_b_abs_sum(model: Any) -> float:
    """Σ|lora_B| over the active adapter — the fingerprint of a real gradient step.

    lora_B is zero by construction at init (the identity graft), so a train
    step that never fired leaves this at exactly 0.0. That is what makes it
    the right probe for I1.1: the pre-e4c026b bug looked like a successful run
    from every other angle — pairs were built, the loop ran, an adapter was
    written to disk — and only the weights knew nothing had happened.

    Reads the weights rather than trusting the train step's own report, which
    is the whole point (CLAUDE.md 2.8: the report must follow the tool).
    """

    try:
        import torch
        from peft.tuners.lora import LoraLayer
    except ImportError:
        return LORA_B_ABS_SUM_UNREAD

    total = 0.0
    seen = 0
    with torch.no_grad():
        for module in model.modules():
            if not isinstance(module, LoraLayer):
                continue
            lora_b = getattr(module, "lora_B", None)
            if lora_b is None or ACTIVE_ADAPTER_NAME not in lora_b:
                continue
            total += float(lora_b[ACTIVE_ADAPTER_NAME].weight.abs().sum().item())
            seen += 1
    # No LoRA layers at all is not "sum zero" — it is "there was nothing to
    # measure", and reporting 0.0 would let a model with no adapter pass as a
    # model whose adapter did not move.
    return total if seen else LORA_B_ABS_SUM_UNREAD


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

    # I1.1: read the weights either side of the step. Sampled here rather than
    # inside _run_dpo_epochs so the reading brackets the whole train call,
    # including a loop that exits without ever stepping.
    lora_b_before = lora_b_abs_sum(active)
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
    lora_b_after = lora_b_abs_sum(active)

    save_agent_adapter(active, agent_id)
    return {
        "trained": True,
        "skipped": False,
        "reason": "ok",
        "agent_id": agent_id,
        "pair_count": pair_count,
        "adapter_dir": str(get_adapter_path(agent_id)),
        "lora_b_abs_sum_before": lora_b_before,
        "lora_b_abs_sum_after": lora_b_after,
        **stats,
    }


def reset_local_llm_singletons_for_tests() -> None:
    """Clear process singletons — test isolation only."""

    global _model, _tokenizer, _active_agent_id, _loaded_model_name
    _model = None
    _tokenizer = None
    _active_agent_id = None
    _loaded_model_name = None
