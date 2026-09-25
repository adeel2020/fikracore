"""Batch Backfill: Generates operational/story_context.json across all simulation runs.

Iterates all runs in simulator/runs/, compiles their authentic operational evidence
(alarms.jsonl, kpis.jsonl, recovery.jsonl) into the canonical materialized presentation view,
and writes operational/story_context.json.

Strict Guardrails:
Zero Oracle Leakage: Never accesses hidden/ground_truth.yaml or hidden_reality.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import sys

from .story_compiler import compile_story_context

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backfill_story_context")


def backfill_all_runs(runs_dir: Path | str | None = None) -> dict[str, int]:
    """Scan all simulation runs and compile story_context.json for each."""
    if runs_dir:
        base_dir = Path(runs_dir).resolve()
    else:
        base_dir = Path(__file__).parent / "runs"

    if not base_dir.is_dir():
        logger.error("Runs directory not found: %s", base_dir)
        return {"total": 0, "success": 0, "skipped": 0, "failed": 0}

    run_dirs = sorted([d for d in base_dir.glob("RUN-*") if d.is_dir()])
    stats = {"total": len(run_dirs), "success": 0, "skipped": 0, "failed": 0}

    logger.info("Found %d run directories in %s", len(run_dirs), base_dir)

    for r_dir in run_dirs:
        op_dir = r_dir / "operational"
        if not op_dir.is_dir():
            stats["skipped"] += 1
            continue

        try:
            story = compile_story_context(r_dir, stage_index=7)
            story_file = op_dir / "story_context.json"
            story_file.write_text(json.dumps(story, indent=2), encoding="utf-8")
            stats["success"] += 1
        except Exception as e:
            logger.warning("Failed to compile story_context for %s: %s", r_dir.name, e)
            stats["failed"] += 1

    logger.info(
        "Backfill complete: Total=%d, Success=%d, Skipped=%d, Failed=%d",
        stats["total"],
        stats["success"],
        stats["skipped"],
        stats["failed"],
    )
    return stats


if __name__ == "__main__":
    result = backfill_all_runs()
    sys.exit(0 if result["failed"] == 0 else 1)
