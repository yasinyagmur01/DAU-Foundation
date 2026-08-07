"""Semantic similarity sensor for Layer 1.5 prediction error.

Replaces keyword Jaccard with frozen sentence-transformers embeddings.
Deterministic cosine similarity — no LLM-as-judge, no trainable weights
updated at runtime.

Biology analogy: a fixed sensory cortex that matches anticipated vs lived
utterances by meaning, not by shared surface tokens.
"""

from __future__ import annotations

from typing import Any

from dau.foundation.state import METRIC_MAX, METRIC_MIN

# ---------------------------------------------------------------------------
# Semantic sensor constants (no magic numbers in logic)
# ---------------------------------------------------------------------------

SEMANTIC_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
SENSOR_LABEL: str = "under sentence-transformers MiniLM"
EMPTY_PAIR_SIMILARITY: float = 1.0
MISSING_TEXT_SIMILARITY: float = 0.0

# Module-local singleton — load once per process
_model: Any | None = None


def get_sensor_label() -> str:
    """Public empiric label for pilots / A/B summaries."""

    return SENSOR_LABEL


def _load_model() -> Any:
    """Lazy-load MiniLM; prefer local cache, then Hub download."""

    global _model
    if _model is not None:
        return _model

    from sentence_transformers import SentenceTransformer

    try:
        _model = SentenceTransformer(SEMANTIC_MODEL_NAME, local_files_only=True)
    except Exception:
        _model = SentenceTransformer(SEMANTIC_MODEL_NAME, local_files_only=False)
    return _model


def semantic_similarity(expected: str, actual: str) -> float:
    """Cosine similarity in [0, 1] between two English utterances.

    Empty/empty → 1.0 (vacuous match). One empty → 0.0.
    Negative cosine values are clamped to 0 before return.
    """

    expected_text = expected.strip()
    actual_text = actual.strip()
    if not expected_text and not actual_text:
        return EMPTY_PAIR_SIMILARITY
    if not expected_text or not actual_text:
        return MISSING_TEXT_SIMILARITY

    from sentence_transformers import util

    model = _load_model()
    embeddings = model.encode(
        [expected_text, actual_text],
        convert_to_tensor=True,
    )
    raw = float(util.cos_sim(embeddings[0], embeddings[1])[0][0])
    return max(METRIC_MIN, min(METRIC_MAX, raw))


def semantic_prediction_error(expected: str, actual: str) -> float:
    """Return 1 - semantic_similarity, clamped to the unit interval."""

    similarity = semantic_similarity(expected, actual)
    error = 1.0 - similarity
    return max(METRIC_MIN, min(METRIC_MAX, error))


def compute_precision_weight(pe_vector: dict[str, float]) -> float:
    """
    Computes global precision scalar from current pe_vector variance.
    Low variance (stable agent) → high precision → amplifies PE signal.
    High variance (crisis) → low precision → dampens PE signal.

    Seçenek B: uses current pe_vector only, no history needed.
    No state changes required.

    Formula:
      variance = var(pe_vector.values())
      pi = 1 / (variance + PRECISION_EPSILON)
      pi_clamped = min(pi, PRECISION_MAX_WEIGHT)
    """
    import statistics

    from dau.foundation.constraints import PRECISION_EPSILON, PRECISION_MAX_WEIGHT

    values = list(pe_vector.values())
    if len(values) < 2:
        return 1.0  # neutral weight — not enough data
    variance = statistics.variance(values)
    pi = 1.0 / (variance + PRECISION_EPSILON)
    return min(pi, PRECISION_MAX_WEIGHT)


def apply_precision_weighting(
    raw_pe: float,
    pe_vector: dict[str, float],
) -> float:
    """
    Applies precision weighting to raw PE scalar.
    Returns precision-weighted PE, clamped to [0.0, 1.0].

    Usage: call after compute_pe, before passing to DAERM.
    """
    pi = compute_precision_weight(pe_vector)
    weighted = raw_pe * pi
    return min(weighted, 1.0)
