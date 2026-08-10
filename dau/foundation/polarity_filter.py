"""Which two lived decisions count as opposite — the preference polarity gate.

Biology analogy: two acts oppose each other when the organism went somewhere
else, not when a logician can derive a contradiction from them.

D-032 moved this gate from NLI contradiction to embedding cosine distance.
Measured on 85 real candidate pairs (``dau_runs/nli_score_distribution.json``,
2 seeds x 10 events, greedy Llama-3.1-8B): contradiction scores had median
0.0024, and lowering the threshold from 0.60 to 0.30 changed the pass rate by
nothing at all (12.9% -> 12.9%) because the distribution is bimodal — the mass
sits at zero and a small minority sits at 0.99. That is not a miscalibrated
threshold, it is the wrong instrument: ``nli-deberta-v3-small`` was trained on
MNLI/SNLI to score propositional contradiction, and two alternative actions at
the same register do not falsify each other. On the same 85 pairs cosine
distance had median 0.3575 and passed 56.5% at 0.35.

The gate is two-sided on purpose. The lower bound rejects paraphrase, which is
what NLI was there for; the upper bound rejects pairs that drifted to an
unrelated subject, where the preference direction would not be about the
decision at all.

No LLM-as-judge: MiniLM is a frozen encoder already carrying the PE sensor.
"""

from __future__ import annotations

from typing import Any

from dau.foundation.constraints import (
    NLI_CONTRADICTION_THRESHOLD,
    NLI_MODEL_NAME,
    POLARITY_COSINE_CALIBRATED,
    POLARITY_COSINE_MAX,
    POLARITY_COSINE_MIN,
    POLARITY_FILTER,
    POLARITY_FILTER_COSINE,
    POLARITY_FILTER_NLI,
    POLARITY_FILTER_VALID,
)
from dau.foundation.semantic_similarity import (
    SEMANTIC_MODEL_NAME,
    semantic_prediction_error,
)


# D-035 step 0, item 2. Every score the active gate actually compared against
# its bounds. A rejection count cannot locate a threshold; the distribution
# can. Whichever gate resolved writes here, so the samples always describe the
# instrument that ran rather than the one the constants happen to name.
POLARITY_SCORE_SAMPLES: list[float] = []


def _resolve_filter_name() -> str:
    """Return the active filter, or fail loudly on an unrecognised one.

    D-023's rule: an unknown value is an undetermined state, and an
    undetermined state raises rather than quietly picking a default.
    """

    name = str(POLARITY_FILTER).strip()
    if name not in POLARITY_FILTER_VALID:
        raise ValueError(
            f"POLARITY_FILTER={name!r} is not one of "
            f"{sorted(POLARITY_FILTER_VALID)} — refusing to guess"
        )
    return name


def polarity_distance(chosen: str, rejected: str) -> float:
    """Cosine distance in [0, 1] between the two completions."""

    return semantic_prediction_error(chosen, rejected)


def is_genuine_polarity_pair(chosen: str, rejected: str) -> bool:
    """True when the two decisions are far enough apart, but still on topic."""

    if _resolve_filter_name() == POLARITY_FILTER_NLI:
        from dau.foundation import nli_filter

        # NLI_ENABLED=0 accepts everything and must keep doing so: inlining
        # the threshold comparison alone would turn "score 0.0 when disabled"
        # into a gate that rejects everything — the opposite behaviour.
        if not nli_filter.NLI_ENABLED:
            return True
        score = nli_filter.contradiction_score(chosen, rejected)
        POLARITY_SCORE_SAMPLES.append(float(score))
        return score >= NLI_CONTRADICTION_THRESHOLD

    distance = polarity_distance(chosen, rejected)
    POLARITY_SCORE_SAMPLES.append(float(distance))
    return POLARITY_COSINE_MIN <= distance <= POLARITY_COSINE_MAX


def describe_polarity_filter() -> dict[str, Any]:
    """Report the gate that actually ran, derived from the same switch it uses.

    CLAUDE.md 2.8: a results file that named the filter from a separate
    constant could label cosine numbers "nli". This reads the resolver.
    """

    name = _resolve_filter_name()
    if name == POLARITY_FILTER_NLI:
        return {
            "polarity_filter": name,
            "polarity_model": NLI_MODEL_NAME,
            "polarity_threshold": NLI_CONTRADICTION_THRESHOLD,
            "polarity_calibrated": False,
        }
    return {
        "polarity_filter": name,
        "polarity_model": SEMANTIC_MODEL_NAME,
        "polarity_cosine_min": POLARITY_COSINE_MIN,
        "polarity_cosine_max": POLARITY_COSINE_MAX,
        "polarity_calibrated": POLARITY_COSINE_CALIBRATED,
    }
