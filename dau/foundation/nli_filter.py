"""NLI polarity filter for Signal v2 preference pairs.

Biology analogy: two lived choices must oppose each other at the decision
level — surface paraphrase is not genuine contradiction. The cross-encoder
scores contradiction probability; pairs below threshold are rejected.
"""

from __future__ import annotations

import os
from functools import lru_cache

from dau.foundation.constraints import (
    NLI_CONTRADICTION_THRESHOLD,
    NLI_MODEL_NAME,
)

NLI_ENABLED = os.environ.get("DAU_NLI_FILTER_ENABLED", "1") != "0"

# Label order for cross-encoder/nli-deberta-v3-small:
# [contradiction, entailment, neutral] — index 0 is contradiction.
NLI_CONTRADICTION_INDEX: int = 0


@lru_cache(maxsize=1)
def _get_nli_model():
    """Load tokenizer + classifier once (CPU)."""

    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL_NAME)
    model.eval()
    return tokenizer, model


def contradiction_score(text_a: str, text_b: str) -> float:
    """Return contradiction probability between text_a and text_b."""

    if not NLI_ENABLED:
        return 0.0
    import torch

    tokenizer, model = _get_nli_model()
    inputs = tokenizer(text_a, text_b, return_tensors="pt", truncation=True)
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1).numpy()[0]
    return float(probs[NLI_CONTRADICTION_INDEX])


def is_genuine_polarity_pair(chosen: str, rejected: str) -> bool:
    """True when chosen/rejected show genuine decision-level contradiction."""

    if not NLI_ENABLED:
        return True
    return contradiction_score(chosen, rejected) >= NLI_CONTRADICTION_THRESHOLD
