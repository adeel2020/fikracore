#!/usr/bin/env python3
"""CLI script to run diagnostic pipeline on benchmark results."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to pythonpath
src_dir = Path(__file__).resolve().parent.parent / "services" / "agents" / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from engine_stack.engines.telecom_brain.investigation.diagnostics import (
    run_full_diagnosis,
    write_diagnostic_artifacts,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/runs"),
        help="Directory containing run folders",
    )
    parser.add_argument(
        "--benchmark-dir",
        type=Path,
        default=Path("artifacts/hypothesis/calibration/before"),
        help="Directory containing benchmark per-run results",
    )
    parser.add_argument(
        "--scenarios-dir",
        type=Path,
        default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/scenarios"),
        help="Directory containing scenario catalog YAML files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/hypothesis/calibration"),
        help="Output directory for diagnostic artifacts",
    )
    args = parser.parse_args()

    print(f"Running diagnosis on benchmark from {args.benchmark_dir}...")
    diagnosis = run_full_diagnosis(args.runs_dir, args.benchmark_dir, args.scenarios_dir)
    
    if "error" in diagnosis:
        print(f"Diagnosis failed: {diagnosis['error']}")
        sys.exit(1)
        
    print(f"Writing diagnostic reports to {args.output_dir}...")
    write_diagnostic_artifacts(diagnosis, args.output_dir)
    
    print("\n================ DIAGNOSTIC SUMMARY ================")
    print(f"Total Runs Evaluated: {diagnosis['total_runs']}")
    print(f"Strict Correct: {diagnosis['strict_correct']} / {diagnosis['total_runs']} ({diagnosis['strict_correct']/diagnosis['total_runs']:.1%})")
    print(f"\nRank Distribution (Known RCA):")
    for r, count in diagnosis["rank_distribution"].items():
        print(f"  {r}: {count}")
    print(f"\nTop Failure Modes:")
    for code, info in sorted(diagnosis["taxonomy_summary"].items(), key=lambda x: -x[1]["count"]):
        if info["count"] > 0:
            print(f"  [{code}] {info['description']}: {info['count']} runs ({info['percentage']}%)")
    print("====================================================\n")


if __name__ == "__main__":
    main()
