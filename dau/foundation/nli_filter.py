"""
DAU NLI Polarity Filter
Layer: Signal v2 preference pair quality gate
Model: cross-encoder/nli-deberta-v3-small (CPU, ~85MB)
Purpose: reject preference pairs where chosen/rejected differ only in
         surface form (format sync) rather than decision-level polarity.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

from dau.foundation.constraints import (
    DAU_NLI_FILTER_ENABLED,
    NLI_CONTRADICTION_THRESHOLD,
    NLI_MODEL_NAME,
)

_NLI_ENV: str = "DAU_NLI_FILTER_ENABLED"
_NLI_DEFAULT: str = "1" if DAU_NLI_FILTER_ENABLED else "0"

NLI_ENABLED: bool = os.environ.get(_NLI_ENV, _NLI_DEFAULT) != "0"

# Label order for cross-encoder/nli-deberta-v3-small:
# [contradiction, entailment, neutral] — index 0 is contradiction.
NLI_CONTRADICTION_INDEX: int = 0


@lru_cache(maxsize=1)
def _get_nli_bundle() -> tuple[Any, Any]:
    """Load tokenizer + classifier once. CPU inference only.

    sentence-transformers CrossEncoder 5.x fails on DebertaV3 via
    AutoProcessor; transformers AutoModel path is the supported CPU route
    for the same Hub weights. Prefer local cache, then Hub download.
    """

    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    try:
        tokenizer = AutoTokenizer.from_pretrained(
            NLI_MODEL_NAME, local_files_only=True
        )
        model = AutoModelForSequenceClassification.from_pretrained(
            NLI_MODEL_NAME, local_files_only=True
        )
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL_NAME)
    model.eval()
    model.to("cpu")
    return tokenizer, model


def contradiction_score(text_a: str, text_b: str) -> float:
    """
    Returns contradiction probability between text_a and text_b.
    Uses cross-encoder/nli-deberta-v3-small label order:
    [contradiction, entailment, neutral] — index 0 is contradiction.
    Returns 0.0 if NLI filter is disabled.
    """

    if not NLI_ENABLED:
        return 0.0
    tokenizer, model = _get_nli_bundle()
    features = tokenizer(
        text_a,
        text_b,
        padding=True,
        truncation=True,
        return_tensors="pt",
    )
    with torch.no_grad():
        logits = model(**features).logits
    probs = F.softmax(logits, dim=-1)
    scores = np.asarray(probs.detach().cpu(), dtype=float)
    if scores.ndim == 1:
        scores = scores.reshape(1, -1)
    return float(scores[0][NLI_CONTRADICTION_INDEX])


def is_genuine_polarity_pair(chosen: str, rejected: str) -> bool:
    """
    Returns True if chosen and rejected show genuine decision-level
    contradiction (not just surface format variation).
    Threshold: NLI_CONTRADICTION_THRESHOLD from constraints.py
    """

    if not NLI_ENABLED:
        return True  # filter off → accept all pairs
    score = contradiction_score(chosen, rejected)
    return score >= NLI_CONTRADICTION_THRESHOLD
