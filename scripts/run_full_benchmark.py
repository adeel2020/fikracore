#!/usr/bin/env python3
"""Run the full 100-scenario RCA benchmark."""
import argparse
import json
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/runs"), help="Directory containing run folders")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/hypothesis/full-benchmark"), help="Output directory for results")
    parser.add_argument("--max-runs", type=int, default=None, help="Maximum number of runs to evaluate")
    parser.add_argument("--validate", action="store_true", help="Run validator first (placeholder)")
    
    args = parser.parse_args()
    
    # Add src to pythonpath so imports work
    src_dir = Path(__file__).resolve().parent.parent / "services" / "agents" / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
        
    try:
        from engine_stack.engines.telecom_brain.investigation.benchmark import benchmark_all
        from engine_stack.engines.telecom_brain.investigation.validator import validate_all
    except ImportError as e:
        print(f"Error importing benchmark/validator module: {e}")
        print("Ensure PYTHONPATH is set correctly or run from the repo root.")
        sys.exit(1)
        
    if args.validate:
        print(f"Validating scenario runs in {args.runs_dir}...")
        val_report = validate_all(args.runs_dir)
        print(f"Validation: {val_report['passed']}/{val_report['total_runs']} passed.")
        if val_report.get("failed", 0) > 0:
            print(f"Validation failed for {val_report['failed']} runs! Aborting benchmark.")
            sys.exit(1)
        
    print(f"Running benchmark on {args.runs_dir}")
    print(f"Outputting to {args.output_dir}")
    
    report = benchmark_all(args.runs_dir, args.output_dir, args.max_runs)
    
    if "error" in report:
        print(f"Benchmark failed: {report['error']}")
        sys.exit(1)
        
    print("\n--- Summary Table ---")
    print(f"Total Runs Evaluated: {report.get('total_runs', 0)}")
    metrics = report.get("metrics", {})
    print(f"Root Cause Top 3 Accuracy: {metrics.get('root_cause_top_3_accuracy', 0):.2%}")
    print(f"Wrong Hypotheses Falsified: {metrics.get('wrong_hypotheses_correctly_falsified', 0)}")
    forced = metrics.get('forced_rca_rate', 0)
    print(f"Forced RCA Rate: {forced:.2%}")
    
    print("\nBaseline Comparison:")
    baseline = report.get("baseline_comparison", {})
    print(f"  Method A ({baseline.get('method_a_name')}): {baseline.get('method_a_correct')} correct")
    print(f"  Method B ({baseline.get('method_b_name')}): {baseline.get('method_b_correct')} correct")
    
if __name__ == "__main__":
    main()
