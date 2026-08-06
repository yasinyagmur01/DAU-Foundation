"""Local Llama-3.1-8B 4-bit loader + QLoRA micro-train VRAM spike.

Biology analogy: grow a local sensory-motor cortex beside the frozen MiniLM
sensor and measure whether the shared skull (VRAM) still has room for a
generation-end plasticity pulse.

GO: peak training VRAM < VRAM_GO_BUDGET_BYTES and no OOM.
NO-GO: OOM or over budget → freeze DAU_LORA_ENABLED plastisite path.

LoRA is a leading testable path, not a guaranteed metacognition fix.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Local model / QLoRA / VRAM constants (no magic numbers in logic)
# ---------------------------------------------------------------------------

LOCAL_MODEL_NAME: str = "meta-llama/Meta-Llama-3.1-8B"
LOCAL_MODEL_ENV: str = "DAU_LOCAL_MODEL_NAME"
ADAPTER_DIR_NAME: str = "dau_lora_adapters"
DEFAULT_ADAPTER_NAME: str = "gen_lived"

LORA_RANK: int = 16
LORA_ALPHA: int = 32
LORA_DROPOUT: float = 0.05
LORA_TARGET_MODULES: tuple[str, ...] = (
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
)

MICRO_TRAIN_BATCH_SIZE: int = 1
MICRO_TRAIN_SEQ_LEN: int = 256
MICRO_TRAIN_STEPS: int = 2
MICRO_TRAIN_LEARNING_RATE: float = 2e-4

# ~7.5 GiB GO budget for RTX 4070 Laptop peak during train step
VRAM_GO_BUDGET_BYTES: int = int(7.5 * 1024 * 1024 * 1024)
BYTES_PER_MIB: int = 1024 * 1024

QUANT_LOAD_IN_4BIT: bool = True
QUANT_BNB_4BIT_COMPUTE_DTYPE: str = "float16"
QUANT_BNB_4BIT_QUANT_TYPE: str = "nf4"
QUANT_BNB_4BIT_USE_DOUBLE_QUANT: bool = True

MINILM_PROBE_TEXT: str = "local vram coexistence probe"
MICRO_TRAIN_PROMPT: str = "Lived trace: extract resource under scarcity."
MICRO_TRAIN_COMPLETION: str = "I take resources carefully from the commons."

STATUS_GO: str = "GO"
STATUS_NOGO: str = "NO_GO"
STATUS_CUDA_UNAVAILABLE: str = "CUDA_UNAVAILABLE"
STATUS_DEPS_MISSING: str = "DEPS_MISSING"
STATUS_MODEL_ACCESS: str = "MODEL_ACCESS_DENIED"

RESULTS_DIR_NAME: str = "dau_runs"
VRAM_SPIKE_RESULTS_FILE: str = "vram_spike_results.json"

# Module-local handles — one process, optional load
_model: Any | None = None
_tokenizer: Any | None = None
_peft_model: Any | None = None
_active_adapter: str | None = None


@dataclass
class VramSpikeReport:
    """Empiric VRAM / dependency outcome for the local plasticity spike."""

    status: str
    cuda_available: bool
    peak_allocated_bytes: int = 0
    peak_reserved_bytes: int = 0
    peak_allocated_mib: float = 0.0
    go_budget_bytes: int = VRAM_GO_BUDGET_BYTES
    minilm_loaded: bool = False
    base_model_loaded: bool = False
    micro_train_ran: bool = False
    oom: bool = False
    detail: str = ""
    missing_deps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_local_model_name() -> str:
    """Return HF model id from env or default Llama-3.1-8B."""

    raw = os.environ.get(LOCAL_MODEL_ENV, "").strip()
    return raw if raw else LOCAL_MODEL_NAME


def cuda_is_available() -> bool:
    """True only when a real CUDA device answers a device-name query.

    Biology analogy: do not trust a rumour that lungs exist — try one breath.
    Broken drivers can make torch.cuda.is_available() flake true while NVML fails.
    """

    try:
        import torch
    except ImportError:
        return False
    try:
        if not bool(torch.cuda.is_available()):
            return False
        if int(torch.cuda.device_count()) < 1:
            return False
        _ = torch.cuda.get_device_name(0)
        return True
    except Exception:
        return False


def _is_gated_model_error(exc: BaseException) -> bool:
    """True when Hugging Face rejects a gated / unauthenticated model fetch."""

    text = str(exc).lower()
    markers = ("gated repo", "401 client error", "access to model", "not authenticated")
    return any(marker in text for marker in markers)


def vram_peak_bytes() -> tuple[int, int]:
    """Return (max_allocated, max_reserved) CUDA bytes; zeros if no CUDA."""

    import torch

    if not torch.cuda.is_available():
        return 0, 0
    return int(torch.cuda.max_memory_allocated()), int(torch.cuda.max_memory_reserved())


def reset_vram_peak_stats() -> None:
    """Clear CUDA peak memory stats before a measurement window."""

    import torch

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.empty_cache()


def _missing_optional_deps() -> list[str]:
    """Return names of packages required for 4-bit + LoRA that are absent."""

    missing: list[str] = []
    for name in ("transformers", "peft", "bitsandbytes", "accelerate"):
        try:
            __import__(name)
        except ImportError:
            missing.append(name)
    return missing


def ensure_minilm_loaded() -> bool:
    """Load MiniLM PE sensor in-process; return True on success."""

    from dau.foundation.semantic_similarity import _load_model

    _load_model()
    _ = _load_model().encode([MINILM_PROBE_TEXT])
    return True


def load_base_model_4bit(*, device_map: str = "auto") -> Any:
    """Load Llama-3.1-8B in 4-bit NF4; require CUDA + bitsandbytes."""

    global _model, _tokenizer

    if _model is not None:
        return _model

    missing = _missing_optional_deps()
    if missing:
        raise RuntimeError(f"Missing deps for local 4-bit load: {missing}")
    if not cuda_is_available():
        raise RuntimeError("CUDA required for 4-bit LocalBackend load.")

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    model_name = resolve_local_model_name()
    compute_dtype = getattr(torch, QUANT_BNB_4BIT_COMPUTE_DTYPE)
    quant_config = BitsAndBytesConfig(
        load_in_4bit=QUANT_LOAD_IN_4BIT,
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_quant_type=QUANT_BNB_4BIT_QUANT_TYPE,
        bnb_4bit_use_double_quant=QUANT_BNB_4BIT_USE_DOUBLE_QUANT,
    )
    _tokenizer = AutoTokenizer.from_pretrained(model_name)
    if _tokenizer.pad_token is None:
        _tokenizer.pad_token = _tokenizer.eos_token
    _model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=quant_config,
        device_map=device_map,
    )
    return _model


def attach_lora_adapter(
    model: Any | None = None,
    *,
    adapter_name: str = DEFAULT_ADAPTER_NAME,
) -> Any:
    """Attach a fresh LoRA adapter (r=16) for micro-train / inference."""

    global _peft_model, _active_adapter

    from peft import LoraConfig, get_peft_model, TaskType

    base = model if model is not None else _model
    if base is None:
        raise RuntimeError("Base model not loaded; call load_base_model_4bit first.")

    config = LoraConfig(
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=list(LORA_TARGET_MODULES),
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    _peft_model = get_peft_model(base, config, adapter_name=adapter_name)
    _active_adapter = adapter_name
    return _peft_model


def set_active_adapter(adapter_name: str) -> None:
    """Activate a named PEFT adapter for subsequent inference."""

    global _active_adapter

    if _peft_model is None:
        raise RuntimeError("No PEFT model; attach_lora_adapter first.")
    _peft_model.set_adapter(adapter_name)
    _active_adapter = adapter_name


def save_adapter(path: Path, *, adapter_name: str | None = None) -> Path:
    """Write active (or named) adapter weights to disk."""

    if _peft_model is None:
        raise RuntimeError("No PEFT model to save.")
    path.mkdir(parents=True, exist_ok=True)
    name = adapter_name if adapter_name is not None else _active_adapter
    if name is not None and hasattr(_peft_model, "set_adapter"):
        _peft_model.set_adapter(name)
    _peft_model.save_pretrained(str(path))
    return path


def load_adapter(path: Path, *, adapter_name: str = DEFAULT_ADAPTER_NAME) -> None:
    """Load adapter from disk onto the PEFT model and activate it."""

    global _peft_model, _active_adapter

    if _model is None:
        load_base_model_4bit()
    from peft import PeftModel

    if _peft_model is None:
        _peft_model = PeftModel.from_pretrained(
            _model,
            str(path),
            adapter_name=adapter_name,
        )
    else:
        _peft_model.load_adapter(str(path), adapter_name=adapter_name)
    _peft_model.set_adapter(adapter_name)
    _active_adapter = adapter_name


def complete_local(
    messages: list[dict[str, str]],
    *,
    seed: int | None = None,
    temperature: float = 0.2,
    max_tokens: int = 150,
) -> str:
    """Generate assistant text with the loaded local (optional LoRA) model."""

    import torch

    if _model is None or _tokenizer is None:
        load_base_model_4bit()
    assert _tokenizer is not None

    model = _peft_model if _peft_model is not None else _model
    assert model is not None

    if seed is not None:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

    # Flatten chat messages into a single prompt (no chat-template dependency).
    parts: list[str] = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        parts.append(f"{role}: {content}")
    parts.append("assistant:")
    prompt = "\n".join(parts)

    inputs = _tokenizer(prompt, return_tensors="pt")
    if torch.cuda.is_available():
        inputs = {key: value.cuda() for key, value in inputs.items()}

    do_sample = temperature > 0.0
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=do_sample,
            temperature=max(temperature, 1e-5) if do_sample else None,
            pad_token_id=_tokenizer.eos_token_id,
        )
    generated = output_ids[0][inputs["input_ids"].shape[-1] :]
    return _tokenizer.decode(generated, skip_special_tokens=True).strip()


def run_micro_train_step(model: Any | None = None) -> None:
    """One tiny causal-LM train step (batch=1) for VRAM peak measurement."""

    import torch
    from torch.optim import AdamW

    if _tokenizer is None:
        raise RuntimeError("Tokenizer missing; load_base_model_4bit first.")
    peft_model = model if model is not None else _peft_model
    if peft_model is None:
        peft_model = attach_lora_adapter()

    text = f"{MICRO_TRAIN_PROMPT}\n{MICRO_TRAIN_COMPLETION}"
    encoded = _tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=MICRO_TRAIN_SEQ_LEN,
        padding="max_length",
    )
    if torch.cuda.is_available():
        encoded = {key: value.cuda() for key, value in encoded.items()}
    labels = encoded["input_ids"].clone()

    peft_model.train()
    optimizer = AdamW(
        (param for param in peft_model.parameters() if param.requires_grad),
        lr=MICRO_TRAIN_LEARNING_RATE,
    )
    for _ in range(MICRO_TRAIN_STEPS):
        optimizer.zero_grad(set_to_none=True)
        outputs = peft_model(
            input_ids=encoded["input_ids"],
            attention_mask=encoded["attention_mask"],
            labels=labels,
        )
        loss = outputs.loss
        loss.backward()
        optimizer.step()
    peft_model.eval()


def run_vram_spike(*, skip_model_download: bool = False) -> VramSpikeReport:
    """Empiric spike: MiniLM + 4-bit base + micro QLoRA; report GO/NO-GO.

    When CUDA or deps are missing, returns a non-GO status without raising so
    CI / CPU hosts can still exercise the harness. Plastisite stays frozen
    until a real GPU GO is recorded.
    """

    missing = _missing_optional_deps()
    if missing:
        return VramSpikeReport(
            status=STATUS_DEPS_MISSING,
            cuda_available=cuda_is_available(),
            detail=f"Install missing packages: {missing}",
            missing_deps=missing,
        )
    if not cuda_is_available():
        return VramSpikeReport(
            status=STATUS_CUDA_UNAVAILABLE,
            cuda_available=False,
            detail=(
                "No CUDA device — VRAM GO/NO-GO deferred. "
                "Keep DAU_LORA_ENABLED=0 until a GPU spike returns GO."
            ),
        )
    if skip_model_download and not _model_cached_locally():
        return VramSpikeReport(
            status=STATUS_NOGO,
            cuda_available=True,
            detail="Model weights not cached; skip_model_download=True.",
        )

    import torch

    report = VramSpikeReport(status=STATUS_GO, cuda_available=True)
    try:
        reset_vram_peak_stats()
        report.minilm_loaded = ensure_minilm_loaded()
        load_base_model_4bit()
        report.base_model_loaded = True
        attach_lora_adapter()
        run_micro_train_step()
        report.micro_train_ran = True
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        allocated, reserved = vram_peak_bytes()
        report.peak_allocated_bytes = allocated
        report.peak_reserved_bytes = reserved
        report.peak_allocated_mib = allocated / float(BYTES_PER_MIB)
        if allocated > VRAM_GO_BUDGET_BYTES:
            report.status = STATUS_NOGO
            report.detail = (
                f"Peak allocated {report.peak_allocated_mib:.1f} MiB "
                f"exceeds GO budget {VRAM_GO_BUDGET_BYTES / BYTES_PER_MIB:.1f} MiB."
            )
        else:
            report.detail = (
                f"Peak allocated {report.peak_allocated_mib:.1f} MiB "
                f"within GO budget."
            )
    except torch.cuda.OutOfMemoryError as exc:
        report.status = STATUS_NOGO
        report.oom = True
        report.detail = f"CUDA OOM: {exc}"
        allocated, reserved = vram_peak_bytes()
        report.peak_allocated_bytes = allocated
        report.peak_reserved_bytes = reserved
        report.peak_allocated_mib = allocated / float(BYTES_PER_MIB)
    except Exception as exc:  # noqa: BLE001 — spike must always return a report
        if _is_gated_model_error(exc):
            report.status = STATUS_MODEL_ACCESS
            report.detail = (
                f"Gated/unauthenticated model fetch for {resolve_local_model_name()}. "
                "Accept the HF license and `huggingface-cli login`, "
                f"or set {LOCAL_MODEL_ENV} to an accessible 8B checkpoint. ({exc})"
            )
        else:
            report.status = STATUS_NOGO
            report.detail = f"{type(exc).__name__}: {exc}"
    return report


def _model_cached_locally() -> bool:
    """Best-effort check whether HF cache already has the local model."""

    try:
        from huggingface_hub import try_to_load_from_cache
    except ImportError:
        return False
    model_name = resolve_local_model_name()
    # Presence of config.json is a cheap proxy for a prior download.
    path = try_to_load_from_cache(model_name, "config.json")
    return path is not None and path != "___not_found___"


def write_vram_spike_report(report: VramSpikeReport, path: Path | None = None) -> Path:
    """Persist spike JSON under dau_runs/."""

    out = path
    if out is None:
        out = Path.cwd() / RESULTS_DIR_NAME / VRAM_SPIKE_RESULTS_FILE
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    return out


def lora_plasticity_allowed(report: VramSpikeReport | None = None) -> bool:
    """True only after an empiric GO spike (or an explicit GO report)."""

    if report is not None:
        return report.status == STATUS_GO
    results_path = Path.cwd() / RESULTS_DIR_NAME / VRAM_SPIKE_RESULTS_FILE
    if not results_path.is_file():
        return False
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    return payload.get("status") == STATUS_GO
