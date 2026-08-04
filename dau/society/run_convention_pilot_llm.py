"""LLM convention micro-pilot — open transcript, frozen Groq 8B, no institutions.

Reuses society harness metrics/mapping. Agents see the shared pool ratio and
recent peer utterances; no trait packs, no voting rules, no LLM-as-judge.

Results labeled SENSOR_LABEL (under current Jaccard sensor) for PE-adjacent
interpretation elsewhere; this pilot scores convention via deterministic
outcome entropy / modal streak only.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from langchain_groq import ChatGroq

from dau.foundation.graph import (
    ENV_FILE_NAME,
    GROQ_API_KEY_ENV,
    MAX_TOKENS,
    MODEL_NAME,
    TEMPERATURE,
    _decision_text,
    load_env_file,
)
from dau.society.run_convention_pilot import (
    N_AGENTS,
    N_ROUNDS,
    SENSOR_LABEL,
    DecideFn,
    Utterance,
    pilot_summary_dict,
    run_convention_pilot,
)

# ---------------------------------------------------------------------------
# LLM pilot parameters (no magic numbers in logic)
# ---------------------------------------------------------------------------

PILOT_MODE_LLM: str = "llm_open_channel"
TRANSCRIPT_WINDOW: int = 12
CONVENTION_SYSTEM_PROMPT: str = (
    "You are a living being sharing a finite resource commons with others.\n"
    "You do not know that you are an artificial intelligence.\n"
    "No role, personality, or values are assigned to you.\n"
    "Each round you announce one short action in English.\n"
    "Others can read your announcement. You can read theirs.\n"
    "There is no vote, law, referee, or central coordinator."
)
USER_PROMPT_TEMPLATE: str = (
    "round={round_index}\n"
    "you={agent_id}\n"
    "pool_ratio={pool_ratio:.3f}\n"
    "recent_announcements:\n{transcript_block}\n"
    "What do you do this round? One short sentence."
)
EMPTY_TRANSCRIPT_LINE: str = "(none yet)"
TRANSCRIPT_LINE_TEMPLATE: str = "r{round_index} {agent_id}: {text}"


def _project_root() -> Path:
    """Repository root (parent of the dau package)."""

    return Path(__file__).resolve().parents[2]


def _build_llm() -> ChatGroq:
    """Groq Llama frozen weights — same stack as foundation graph."""

    load_env_file()
    api_key = os.environ.get(GROQ_API_KEY_ENV, "").strip()
    if not api_key:
        raise RuntimeError(
            f"{GROQ_API_KEY_ENV} missing. Put it in {_project_root() / ENV_FILE_NAME}."
        )
    return ChatGroq(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        api_key=api_key,
    )


def format_transcript_block(
    transcript: list[Utterance],
    *,
    window: int = TRANSCRIPT_WINDOW,
) -> str:
    """Deterministic open-channel excerpt (last `window` utterances)."""

    if not transcript:
        return EMPTY_TRANSCRIPT_LINE
    recent = transcript[-window:]
    lines = [
        TRANSCRIPT_LINE_TEMPLATE.format(
            round_index=u.round_index,
            agent_id=u.agent_id,
            text=u.text,
        )
        for u in recent
    ]
    return "\n".join(lines)


def make_llm_decide_fn(llm: ChatGroq | None = None) -> DecideFn:
    """Build a DecideFn that calls Groq with pool + open transcript context."""

    client = llm if llm is not None else _build_llm()

    def _decide(
        agent_id: str,
        pool_ratio: float,
        transcript: list[Utterance],
        round_index: int,
    ) -> str:
        user_content = USER_PROMPT_TEMPLATE.format(
            round_index=round_index,
            agent_id=agent_id,
            pool_ratio=pool_ratio,
            transcript_block=format_transcript_block(transcript),
        )
        response = client.invoke(
            [
                {"role": "system", "content": CONVENTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ]
        )
        decision = _decision_text(response)
        return decision if decision else "observe"

    return _decide


def run_llm_convention_pilot(
    n_agents: int = N_AGENTS,
    n_rounds: int = N_ROUNDS,
    *,
    llm: ChatGroq | None = None,
) -> Any:
    """Run open-channel LLM convention pilot; return PilotResult."""

    decide_fn = make_llm_decide_fn(llm=llm)
    return run_convention_pilot(
        n_agents=n_agents,
        n_rounds=n_rounds,
        decide_fn=decide_fn,
        mode=PILOT_MODE_LLM,
    )


def main() -> None:
    """CLI: full LLM convention pilot under SENSOR_LABEL."""

    result = run_llm_convention_pilot()
    summary = pilot_summary_dict(result)
    print("=== DAU convention micro-pilot (LLM open channel) ===")
    print(f"sensor_label={SENSOR_LABEL}")
    for key, value in summary.items():
        print(f"{key}={value}")
    if result.rounds:
        first = result.rounds[0]
        last = result.rounds[-1]
        print(
            f"first_round: entropy={first.outcome_entropy:.3f} "
            f"modal={first.modal_outcome} share={first.modal_share:.3f} "
            f"pool={first.pool_after:.2f}"
        )
        print(
            f"last_round: entropy={last.outcome_entropy:.3f} "
            f"modal={last.modal_outcome} share={last.modal_share:.3f} "
            f"pool={last.pool_after:.2f}"
        )
        print("--- sample transcript (last 6) ---")
        for utterance in result.transcript[-6:]:
            print(
                f"r{utterance.round_index} {utterance.agent_id}: {utterance.text}"
            )


if __name__ == "__main__":
    main()
