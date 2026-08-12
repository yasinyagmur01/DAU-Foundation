"""Tests for the training-artifact dump (D-057).

The dump exists so a hyperparameter sweep can replay a fixed corpus instead of
re-living 50 events per arm. That only holds if the dump is (a) faithful to
what training received and (b) incapable of changing it.
"""

from __future__ import annotations

import json

import pytest

from dau.diagnostics.training_artifacts import (
    ARTIFACTS_SCHEMA,
    DUMP_ARTIFACTS_ENV,
    dump_enabled,
    dump_training_artifacts,
    load_training_artifacts,
    pairs_digest,
)
from dau.foundation.lora_update import (
    LivedTraceExample,
    PreferencePair,
    shuffle_preference_pairs,
)


def _pair(prompt: str, chosen: str, rejected: str) -> PreferencePair:
    return PreferencePair(
        prompt=prompt,
        chosen=chosen,
        rejected=rejected,
        pe_chosen=0.2,
        pe_rejected=0.8,
        event_counter=1,
        system="sys",
    )


def _example(counter: int) -> LivedTraceExample:
    return LivedTraceExample(
        event_counter=counter,
        prediction_error=0.4,
        delta_magnitude=0.3,
        delta_class="MEDIUM",
        trauma_flag=False,
        drift_sum=0.1,
        loss_weight=1.0,
        prompt="p",
        completion="c",
        decision_system="ds",
        decision_user="du",
    )


def test_dump_is_off_by_default(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.delenv(DUMP_ARTIFACTS_ENV, raising=False)
    assert dump_enabled() is False
    written = dump_training_artifacts(
        agent_id="a1",
        arm="lived",
        lived_examples=[_example(1)],
        pairs=[_pair("p", "c", "r")],
        shuffled=False,
        base_dir=tmp_path,
    )
    assert written is None
    assert list(tmp_path.iterdir()) == []


def test_unrecognised_flag_raises_rather_than_defaulting_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # D-023: a misspelled flag must not quietly disable the dump — the cost is
    # discovered only after the GPU hours are spent.
    monkeypatch.setenv(DUMP_ARTIFACTS_ENV, "yep")
    with pytest.raises(ValueError, match="not a recognised boolean"):
        dump_enabled()


def test_dump_round_trips_pairs_and_candidate_pool(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.setenv(DUMP_ARTIFACTS_ENV, "1")
    pairs = [_pair("p1", "c1", "r1"), _pair("p2", "c2", "r2")]
    examples = [_example(1), _example(2), _example(3)]

    path = dump_training_artifacts(
        agent_id="cprime-lived-2004-g1",
        arm="lived",
        lived_examples=examples,
        pairs=pairs,
        shuffled=False,
        base_dir=tmp_path,
    )
    assert path is not None

    payload = load_training_artifacts("cprime-lived-2004-g1", base_dir=tmp_path)
    assert payload["schema"] == ARTIFACTS_SCHEMA
    assert payload["n_pairs"] == 2
    # The candidate pool is kept as well as the pairs: replaying a different
    # pair-construction strategy needs the pool, not the product.
    assert payload["n_lived_examples"] == 3
    assert [p["chosen"] for p in payload["pairs"]] == ["c1", "c2"]
    assert payload["lived_examples"][0]["decision_user"] == "du"


def test_shuffled_arm_records_post_inversion_pairs(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    # The control's pairs are already inverted when training sees them. A dump
    # taken before inversion would hand a replay the lived direction under the
    # control's name — the exact confusion D-040 was written to end.
    monkeypatch.setenv(DUMP_ARTIFACTS_ENV, "1")
    inverted = shuffle_preference_pairs([_pair("p1", "c1", "r1")])

    dump_training_artifacts(
        agent_id="cprime-shuffle-2004-g1",
        arm="shuffle",
        lived_examples=[_example(1)],
        pairs=inverted,
        shuffled=True,
        base_dir=tmp_path,
    )
    payload = load_training_artifacts("cprime-shuffle-2004-g1", base_dir=tmp_path)
    assert payload["shuffled"] is True
    assert payload["pairs"][0]["chosen"] == "r1"
    assert payload["pairs"][0]["rejected"] == "c1"


def test_dump_does_not_change_training_inputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    # The dump must be a leaf. If it mutated or reordered the list, the run
    # would train on something other than what a dump-off run trains on, and
    # every artifact-enabled run would be a different experiment.
    monkeypatch.setenv(DUMP_ARTIFACTS_ENV, "1")
    pairs = [_pair("p1", "c1", "r1"), _pair("p2", "c2", "r2")]
    before = [(p.prompt, p.chosen, p.rejected) for p in pairs]
    digest_before = pairs_digest(pairs)

    dump_training_artifacts(
        agent_id="a2",
        arm="lived",
        lived_examples=[_example(1)],
        pairs=pairs,
        shuffled=False,
        base_dir=tmp_path,
    )

    assert [(p.prompt, p.chosen, p.rejected) for p in pairs] == before
    assert pairs_digest(pairs) == digest_before


def test_digest_is_order_sensitive() -> None:
    # Under gradient accumulation the same pairs in a different sequence are a
    # different trajectory, so a digest that ignored order would call two
    # different training inputs identical.
    a = _pair("p1", "c1", "r1")
    b = _pair("p2", "c2", "r2")
    assert pairs_digest([a, b]) != pairs_digest([b, a])


def test_load_refuses_foreign_schema(tmp_path) -> None:
    path = tmp_path / "a3.json"
    path.write_text(json.dumps({"schema": "something-else/9"}), encoding="utf-8")
    with pytest.raises(ValueError, match="is not"):
        load_training_artifacts("a3", base_dir=tmp_path)
