"""Run local 4-bit + MiniLM + QLoRA micro-train VRAM spike; write JSON report.

Usage:
  python -m dau.diagnostics.run_vram_spike

Exit codes: 0=GO, 2=NO_GO/CUDA_UNAVAILABLE/DEPS_MISSING.
"""

from __future__ import annotations

import sys

from dau.foundation.local_llm import (
    STATUS_GO,
    run_vram_spike,
    write_vram_spike_report,
)

EXIT_GO: int = 0
EXIT_NOGO: int = 2


def main() -> int:
    report = run_vram_spike()
    path = write_vram_spike_report(report)
    print(f"status={report.status}")
    print(f"detail={report.detail}")
    print(f"peak_allocated_mib={report.peak_allocated_mib:.1f}")
    print(f"wrote={path}")
    return EXIT_GO if report.status == STATUS_GO else EXIT_NOGO


if __name__ == "__main__":
    sys.exit(main())
