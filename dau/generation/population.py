"""Generation bookkeeping — who becomes whose parent, and closing Price (E2-4a).

E4 gave the reproduction rule (tournament, `w`, the Price partition) and E2-1..3
gave the machinery to run N agents through one life. This module is the seam
between them: at the end of a generation it turns fitness into a plan for the
next one, and once that next generation has lived it closes the Price partition
for the transition.

⭐ The two-generation dependency is the reason this is its own layer. Price
needs the HEIRS' z to compute Δzᵢ:

    Δz̄ = (1/w̄)·Cov(wᵢ, zᵢ) + (1/w̄)·E(wᵢ·Δzᵢ)

so the partition for the g → g+1 transition cannot be computed at the end of
generation g. Nothing in the run can report "the selection term" for the
generation it just finished; it can only report it one generation late. A reader
who forgets that would line up the wrong pair of numbers, so the plan is kept as
an explicit object rather than being reconstructed from agent ids later.

⚠ NOT WIRED YET. No runner calls this. Attaching it to the experiment wrapper —
with the memory-vault and adapter lifecycles opened up to N agents — is E2-4b,
and that is the first step that touches the real run path.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from dau.generation.reproduction import (
    TOURNAMENT_K,
    Candidate,
    allocate_heirs,
    price_partition,
    reproduction_report,
)

# ---------------------------------------------------------------------------
# Heir naming (deterministic, no magic strings in logic)
# ---------------------------------------------------------------------------
# The ordinal suffix is load-bearing: a parent that wins two tournaments needs
# two DISTINCT heir ids, and `w` is exactly the count of them. Naming heirs
# after the parent alone would silently merge them and drive Var(w) to zero —
# the degenerate case the whole layer exists to escape.
HEIR_ID_TEMPLATE: str = "{parent_id}-g{generation}-h{ordinal}"
FIRST_HEIR_ORDINAL: int = 1
FIRST_GENERATION: int = 1


@dataclass(frozen=True)
class HeirAssignment:
    """One newborn and the parent whose life it inherits."""

    heir_id: str
    parent_id: str


@dataclass(frozen=True)
class GenerationPlan:
    """How generation `generation` is populated from the previous one's parents.

    `parents` carries each parent's f_agent AND its z, so the transition can be
    closed later without going back to the run output — the run output is where
    the wrong-pair mistake would happen.
    """

    generation: int
    parents: tuple[Candidate, ...]
    w_by_parent: dict[str, int]
    heirs: tuple[HeirAssignment, ...]
    report: dict[str, object]


def heir_id(parent_id: str, generation: int, ordinal: int) -> str:
    """Deterministic id for the `ordinal`-th heir of a parent in a generation."""

    return HEIR_ID_TEMPLATE.format(
        parent_id=parent_id, generation=int(generation), ordinal=int(ordinal)
    )


def plan_next_generation(
    generation: int,
    candidates: list[Candidate],
    rng: random.Random,
    n_slots: int,
    k: int = TOURNAMENT_K,
) -> GenerationPlan:
    """Turn one generation's fitness into the next generation's parentage.

    P3: population size is fixed, so `n_slots` is the whole population — a
    generation is one life per agent and at its end every slot is refilled.
    Parents are drawn by tournament (P2), and a parent may fill several slots or
    none, which is what makes `w` variable.

    Heirs are emitted in a deterministic order (parent id, then ordinal) so the
    same rng seed reproduces the same pedigree. Tournament ORDER is not sorted
    away, only the emission order is: the draws already consumed `rng` in the
    order `allocate_heirs` made them.
    """

    if generation < FIRST_GENERATION:
        raise ValueError(f"generation must be >= {FIRST_GENERATION}, got {generation}")
    w_by_parent = allocate_heirs(candidates, n_slots=n_slots, rng=rng, k=k)
    ordered_parents = sorted(candidates, key=lambda c: c.agent_id)
    heirs: list[HeirAssignment] = []
    for parent in ordered_parents:
        for ordinal in range(
            FIRST_HEIR_ORDINAL, w_by_parent[parent.agent_id] + FIRST_HEIR_ORDINAL
        ):
            heirs.append(
                HeirAssignment(
                    heir_id=heir_id(parent.agent_id, generation, ordinal),
                    parent_id=parent.agent_id,
                )
            )
    return GenerationPlan(
        generation=int(generation),
        parents=tuple(ordered_parents),
        w_by_parent=w_by_parent,
        heirs=tuple(heirs),
        report=reproduction_report(candidates, w_by_parent),
    )


def close_transition(
    plan: GenerationPlan,
    heir_z: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    """Close the Price partition for the transition this plan created.

    `heir_z` maps heir id → that heir's landmark drift vector, read after the
    heirs have lived. Every heir in the plan must appear: a missing one would
    make Δzᵢ an average over fewer offspring than `w` says exist, and the
    identity would quietly stop holding rather than fail (§2.9).
    """

    grouped: dict[str, list[dict[str, float]]] = {
        parent.agent_id: [] for parent in plan.parents
    }
    for assignment in plan.heirs:
        if assignment.heir_id not in heir_z:
            raise ValueError(
                f"{assignment.heir_id}: no z recorded, Price partition would be wrong"
            )
        grouped[assignment.parent_id].append(heir_z[assignment.heir_id])
    return price_partition(list(plan.parents), plan.w_by_parent, grouped)
