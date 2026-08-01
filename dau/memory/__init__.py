"""DAU Memory public API — Layer 1 long-term store, decay, retrieval, sleep."""

from __future__ import annotations

from typing import Any

__all__ = [
    "ConsolidationReport",
    "MemoryStore",
    "compute_memory_score",
    "compute_retention",
    "compute_strength_init",
    "persist_decision",
    "retrieve_top_k",
    "run_consolidation",
    "should_forget",
]

_EXPORT_MAP: dict[str, tuple[str, str]] = {
    "ConsolidationReport": (".consolidation", "ConsolidationReport"),
    "MemoryStore": (".store", "MemoryStore"),
    "compute_memory_score": (".retrieval", "compute_memory_score"),
    "compute_retention": (".decay", "compute_retention"),
    "compute_strength_init": (".decay", "compute_strength_init"),
    "persist_decision": (".store", "persist_decision"),
    "retrieve_top_k": (".retrieval", "retrieve_top_k"),
    "run_consolidation": (".consolidation", "run_consolidation"),
    "should_forget": (".decay", "should_forget"),
}


def __getattr__(name: str) -> Any:
    """Lazy-load public symbols so `python -m dau.memory.*` stays clean."""

    if name not in _EXPORT_MAP:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr = _EXPORT_MAP[name]
    from importlib import import_module

    module = import_module(module_name, __name__)
    value = getattr(module, attr)
    globals()[name] = value
    return value


if __name__ == "__main__":
    print("DAU Memory public API:")
    for name in __all__:
        print(f"  - {name}")
    print("OK — memory package exports listed")
