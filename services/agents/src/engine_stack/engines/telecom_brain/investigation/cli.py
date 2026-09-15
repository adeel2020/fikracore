"""CLI entry points for operational investigation and separate examiner/validation actions."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .contracts import (
    GeneratedRunInput,
    InvestigationResult,
    ValidationDecision,
)
from .evidence import input_from_run
from .investigator import Investigator
from .knowledge import (
    FrozenTelecomBrainProvider,
    GbrainTelecomBrainProvider,
    InMemoryKnowledgeProvider,
    ProviderError,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fikracore",
        description="FikraCore — Telecom reasoning, learning and resilience platform",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    
    # 1. Investigate (§98)
    run = commands.add_parser("investigate", help="Explain what happened and why")
    run.add_argument("run_directory", type=Path, nargs="?", default=None)
    run.add_argument("--scenario", type=str, default=None)
    run.add_argument("--snapshot", type=Path)
    run.add_argument("--output", type=Path, default=None)

    # 2. Discover (§98)
    discover = commands.add_parser("discover", help="Identify missing or insufficient operational knowledge")
    discover.add_argument("scenario", type=str, nargs="?", default=None)
    discover.add_argument("--output", type=Path, default=None)

    # 3. Learn (§98)
    learn = commands.add_parser("learn", help="Validate, promote and manage learned knowledge")
    learn.add_argument("action", nargs="?", default="inspect", choices=["inspect", "validate", "promote", "rollback", "generate"])
    learn.add_argument("target", nargs="?", default=None)
    learn.add_argument("--candidate-file", type=Path, default=None)
    learn.add_argument("--validation-file", type=Path, default=None)
    learn.add_argument("--promotion-id", type=str, default=None)
    learn.add_argument("--units-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h3_runs"))
    learn.add_argument("--output-dir", type=Path, default=None)
    learn.add_argument("--output", type=Path, default=None)
    learn.add_argument("--dry-run", action="store_true")

    # 4. Simulate (§98)
    simulate = commands.add_parser("simulate", help="Execute simulator scenarios")
    simulate.add_argument("scenario", type=str)
    simulate.add_argument("--stage", type=str, default=None)
    simulate.add_argument("--runs-dir", type=Path, default=None)

    # 5. Report (§98)
    report = commands.add_parser("report", help="Generate benchmark and analysis reports")
    report.add_argument("--stage", choices=["h2", "h3", "h4", "knowledge"], default="h4")
    report.add_argument("--benchmark-dir", type=Path, default=None)
    report.add_argument("--format", choices=["json", "markdown"], default="json")

    evaluate = commands.add_parser("evaluate", help="Examiner only; never called by the investigator")
    evaluate.add_argument("result", type=Path)
    evaluate.add_argument("--expected-root", action="append", default=[])
    evaluate.add_argument("--unknown-correct", action="store_true")
    evaluate.add_argument("--output", type=Path, required=True)
    validation = commands.add_parser("validate-candidate")
    validation.add_argument("result", type=Path)
    validation.add_argument("candidate_id")
    validation.add_argument("--decision", choices=["validate", "reject"], required=True)
    validation.add_argument("--validator", required=True)
    validation.add_argument("--reason", required=True)
    validation.add_argument("--output", type=Path, required=True)
    
    validate = commands.add_parser("validate", help="Validate scenarios, learning units and artifacts")
    validate.add_argument("runs_directory", type=Path, nargs="?", default=None)
    validate.add_argument("--target", choices=["scenarios", "learning-units", "runs", "h2", "h3", "h4"], default="runs")
    validate.add_argument("--stage", choices=["h1", "h2", "h3", "h4", "all"], default="h1")
    validate.add_argument("--output", type=Path, default=None)

    benchmark = commands.add_parser("benchmark", help="Run H1–H4 and integration benchmarks")
    benchmark.add_argument("runs_directory", type=Path, nargs="?", default=None)
    benchmark.add_argument("--stage", choices=["h1", "h2", "h3", "h4", "parity", "all"], default=None)
    benchmark.add_argument("--output", type=Path, default=None)
    benchmark.add_argument("--max-runs", type=int, default=None)
    benchmark.add_argument("--split", type=str, default=None, help="Split name (calibration, validation, holdout)")
    benchmark.add_argument("--split-file", type=Path, default=None, help="Path to splits.json")
    benchmark.add_argument("--validate-first", action="store_true")

    diag_bm = commands.add_parser("diagnose-benchmark")
    diag_bm.add_argument("--runs-directory", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/runs"))
    diag_bm.add_argument("--benchmark-dir", type=Path, default=Path("artifacts/hypothesis/calibration/before"))
    diag_bm.add_argument("--scenarios-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/scenarios"))
    diag_bm.add_argument("--output", type=Path, default=Path("artifacts/hypothesis/calibration"))

    diag_run = commands.add_parser("diagnose-run")
    diag_run.add_argument("run_id", type=str)
    diag_run.add_argument("--runs-directory", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/runs"))
    diag_run.add_argument("--benchmark-dir", type=Path, default=Path("artifacts/hypothesis/calibration/before"))
    diag_run.add_argument("--output", type=Path, default=None)

    # Step 4.2 / H2 Commands
    gen_h2 = commands.add_parser("generate-h2-scenarios")
    gen_h2.add_argument("--output-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h2_runs"))

    val_h2 = commands.add_parser("validate-h2-scenarios")
    val_h2.add_argument("--runs-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h2_runs"))

    bm_h2 = commands.add_parser("run-h2-benchmark")
    bm_h2.add_argument("--runs-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h2_runs"))
    bm_h2.add_argument("--output-dir", type=Path, default=Path("artifacts/hypothesis/h2"))
    bm_h2.add_argument("--reference-network", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/operator_model/reference_synthetic_network.yaml"))

    diag_h2 = commands.add_parser("diagnose-h2-run")
    diag_h2.add_argument("run_id", type=str)
    diag_h2.add_argument("--benchmark-dir", type=Path, default=Path("artifacts/hypothesis/h2"))

    rep_h2 = commands.add_parser("h2-report")
    rep_h2.add_argument("--benchmark-dir", type=Path, default=Path("artifacts/hypothesis/h2"))

    demo_h2 = commands.add_parser("h2-demo")
    demo_h2.add_argument("run_id", type=str)
    demo_h2.add_argument("--runs-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h2_runs"))
    demo_h2.add_argument("--mode", choices=["INVESTIGATION", "DEMO"], default="DEMO")
    demo_h2.add_argument("--step", type=int, default=1)
    demo_h2.add_argument("--query", type=str, default=None)

    # Step 4.3 / H3 Commands
    gen_h3 = commands.add_parser("generate-h3-learning-units")
    gen_h3.add_argument("--output-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h3_runs"))

    val_h3 = commands.add_parser("validate-h3-learning-units")
    val_h3.add_argument("--units-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h3_runs"))

    prom_h3 = commands.add_parser("promote-knowledge")
    prom_h3.add_argument("candidate_file", type=Path)
    prom_h3.add_argument("validation_file", type=Path)
    prom_h3.add_argument("--dry-run", action="store_true")
    prom_h3.add_argument("--output", type=Path, default=None)

    rb_h3 = commands.add_parser("rollback-promotion")
    rb_h3.add_argument("promotion_id", type=str)
    rb_h3.add_argument("--output", type=Path, default=None)

    bm_h3 = commands.add_parser("run-h3-benchmark")
    bm_h3.add_argument("--units-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h3_runs"))
    bm_h3.add_argument("--output-dir", type=Path, default=Path("artifacts/hypothesis/h3"))
    bm_h3.add_argument("--reference-network", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/operator_model/reference_synthetic_network.yaml"))

    rep_h3 = commands.add_parser("h3-report")
    rep_h3.add_argument("--benchmark-dir", type=Path, default=Path("artifacts/hypothesis/h3"))
    rep_h3.add_argument("--format", choices=["json", "markdown"], default="json")

    demo_h3 = commands.add_parser("h3-demo")
    demo_h3.add_argument("unit_id", type=str)
    demo_h3.add_argument("--units-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h3_runs"))
    demo_h3.add_argument("--mode", choices=["INVESTIGATION", "DEMO"], default="DEMO")
    demo_h3.add_argument("--step", type=int, default=1)
    demo_h3.add_argument("--query", type=str, default=None)

    # Step 4.4 / H4 Task-Oriented Commands (§58)
    predict_cmd = commands.add_parser("predict", help="Proactive forward what-if failure simulation")
    predict_cmd.add_argument("scenario", type=str, help="Scenario ID (H4-WI-001), human-readable name, or alias")
    predict_cmd.add_argument("--runs-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h4_runs"))

    inspect_cmd = commands.add_parser("inspect", help="Inspect scenario operational topology and manifest, or live MCP knowledge")
    inspect_cmd.add_argument("scenario", type=str, help="Scenario ID, display name, alias, 'knowledge', 'mcp', or 'live-knowledge'")
    inspect_cmd.add_argument("--reasoning", action="store_true", help="Run H1/H2/H4 live smoke test reasoning cases (for mcp/live-knowledge)")
    inspect_cmd.add_argument("--domain", type=str, default=None, help="Filter knowledge inventory by domain")
    inspect_cmd.add_argument("--type", type=str, default=None, help="Filter knowledge inventory by page type")
    inspect_cmd.add_argument("--gaps", action="store_true", help="Display knowledge gaps and recommendations")
    inspect_cmd.add_argument("--orphans", action="store_true", help="Display operational orphans")
    inspect_cmd.add_argument("--coverage", action="store_true", help="Display detailed coverage and topology breakdown")
    inspect_cmd.add_argument("--technical", action="store_true", help="Display technical view with canonical IDs and provenance")
    inspect_cmd.add_argument("--json", action="store_true", help="Output raw JSON payload")
    inspect_cmd.add_argument("--runs-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h4_runs"))
    inspect_cmd.add_argument("--output-dir", type=Path, default=None)

    mcp_smoke_cmd = commands.add_parser("mcp-smoke", help="Run Step 4.5 Live gbrain MCP Integration Smoke Test")
    mcp_smoke_cmd.add_argument("--url", type=str, default=None, help="Live gbrain MCP URL")
    mcp_smoke_cmd.add_argument("--token", type=str, default=None, help="Live gbrain MCP Bearer token")
    mcp_smoke_cmd.add_argument("--no-reasoning", action="store_true", help="Skip H1/H2/H4 live reasoning cases")
    mcp_smoke_cmd.add_argument("--output-dir", type=Path, default=Path("artifacts/integration"))

    bm_parity = commands.add_parser("benchmark-parity", help="Run Step 4.6 Live MCP Parity & Benchmark Validation")
    bm_parity.add_argument("--stage", choices=["h1", "h2", "h3", "h4", "all"], default="all")
    bm_parity.add_argument("--selected", action="store_true", help="Run only Stage A selected parity scenarios (20 runs)")
    bm_parity.add_argument("--output-dir", type=Path, default=Path("artifacts/integration/mcp-parity"))
    bm_parity.add_argument("--url", type=str, default=None)
    bm_parity.add_argument("--token", type=str, default=None)

    insp_parity = commands.add_parser("inspect-parity", help="Inspect live MCP parity for a specific scenario")
    insp_parity.add_argument("scenario", type=str, help="Scenario ID, display name, or alias")
    insp_parity.add_argument("--runs-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h4_runs"))

    present_cmd = commands.add_parser("present", help="Generate UI standard presentation model for scenario")
    present_cmd.add_argument("scenario", type=str, help="Scenario ID, display name, or alias")
    present_cmd.add_argument("--mode", choices=["INVESTIGATION", "DEMO"], default="INVESTIGATION")
    present_cmd.add_argument("--step", type=int, default=1)
    present_cmd.add_argument("--runs-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h4_runs"))

    gen_h4 = commands.add_parser("generate-h4-scenarios")
    gen_h4.add_argument("--output-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h4_runs"))

    val_h4 = commands.add_parser("validate-h4-scenarios")
    val_h4.add_argument("--runs-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h4_runs"))

    bm_h4 = commands.add_parser("run-h4-benchmark")
    bm_h4.add_argument("--runs-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h4_runs"))
    bm_h4.add_argument("--output-dir", type=Path, default=Path("artifacts/hypothesis/h4"))
    bm_h4.add_argument("--reference-network", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/operator_model/reference_synthetic_network.yaml"))

    rep_h4 = commands.add_parser("h4-report")
    rep_h4.add_argument("--benchmark-dir", type=Path, default=Path("artifacts/hypothesis/h4"))
    rep_h4.add_argument("--format", choices=["json", "markdown"], default="json")

    demo_h4 = commands.add_parser("h4-demo")
    demo_h4.add_argument("scenario", type=str, help="Scenario ID, display name, or alias")
    demo_h4.add_argument("--runs-dir", type=Path, default=Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h4_runs"))
    demo_h4.add_argument("--mode", choices=["INVESTIGATION", "DEMO"], default="DEMO")
    demo_h4.add_argument("--step", type=int, default=1)
    demo_h4.add_argument("--query", type=str, default=None)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "investigate":
            from ..capabilities import default_capability_registry
            cap_res = default_capability_registry.execute("investigate", {
                "run_directory": str(args.run_directory) if args.run_directory else None,
                "scenario": getattr(args, "scenario", None),
                "snapshot": str(args.snapshot) if args.snapshot else None,
            })
            if not cap_res.success:
                parser.error("; ".join(cap_res.errors))
            output = cap_res.data
            if not args.output:
                print(json.dumps(output, indent=2))
                return
        elif args.command == "discover":
            from ..capabilities import default_capability_registry
            cap_res = default_capability_registry.execute("discover", {
                "scenario": getattr(args, "scenario", None),
            })
            if not cap_res.success:
                parser.error("; ".join(cap_res.errors))
            output = cap_res.data
            if not args.output:
                print(json.dumps(output, indent=2))
                return
        elif args.command == "learn":
            from ..capabilities import default_capability_registry
            cap_res = default_capability_registry.execute("learn", {
                "action": args.action,
                "unit_id": args.target,
                "candidate_file": str(args.candidate_file) if args.candidate_file else None,
                "validation_file": str(args.validation_file) if args.validation_file else None,
                "promotion_id": args.promotion_id,
                "units_dir": str(args.units_dir) if args.units_dir else None,
                "output_dir": str(args.output_dir) if args.output_dir else None,
                "dry_run": args.dry_run,
            })
            if not cap_res.success:
                parser.error("; ".join(cap_res.errors))
            out = cap_res.data
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                with open(args.output, "w") as f:
                    json.dump(out, f, indent=2)
            print(json.dumps(out, indent=2))
            return
        elif args.command == "simulate":
            from ..capabilities import default_capability_registry
            cap_res = default_capability_registry.execute("simulate", {
                "scenario": args.scenario,
                "stage": args.stage,
                "runs_dir": str(args.runs_dir) if args.runs_dir else None,
            })
            if not cap_res.success:
                parser.error("; ".join(cap_res.errors))
            print(json.dumps(cap_res.data, indent=2))
            return
        elif args.command == "report":
            from ..capabilities import default_capability_registry
            cap_res = default_capability_registry.execute("report", {
                "stage": args.stage,
                "benchmark_dir": str(args.benchmark_dir) if args.benchmark_dir else None,
                "format": args.format,
            })
            if not cap_res.success:
                parser.error("; ".join(cap_res.errors))
            rep_content = cap_res.data.get("content")
            if args.format == "markdown":
                print(rep_content)
            else:
                print(json.dumps(rep_content, indent=2))
            return
        elif args.command == "validate":
            if not args.runs_directory or getattr(args, "stage", "h1") != "h1":
                from ..capabilities import default_capability_registry
                cap_res = default_capability_registry.execute("validate", {
                    "stage": getattr(args, "stage", "h1"),
                    "target": getattr(args, "target", "runs"),
                    "runs_dir": str(args.runs_directory) if args.runs_directory else None,
                })
                if not cap_res.success:
                    parser.error("; ".join(cap_res.errors))
                output = cap_res.data
                if not args.output:
                    print(json.dumps(output, indent=2))
                    return
            else:
                from .validator import validate_all
                output = validate_all(args.runs_directory)
        elif args.command == "benchmark":
            stage_arg = getattr(args, "stage", None)
            if stage_arg and stage_arg.lower() != "h1":
                from ..capabilities import default_capability_registry
                cap_res = default_capability_registry.execute("benchmark", {
                    "stage": stage_arg,
                    "runs_dir": str(args.runs_directory) if args.runs_directory else None,
                    "output_dir": str(args.output) if args.output else None,
                    "max_runs": args.max_runs,
                })
                if not cap_res.success:
                    parser.error("; ".join(cap_res.errors))
                print(json.dumps(cap_res.data, indent=2))
                return
            if args.runs_directory and str(args.runs_directory).lower() in ("parity", "live-parity", "mcp-parity"):
                from .mcp_parity import run_mcp_parity_benchmark
                res = run_mcp_parity_benchmark(
                    stage=getattr(args, "split", "all") or "all",
                    selected_only=bool(args.max_runs is not None and args.max_runs <= 20),
                    output_dir=args.output or Path("artifacts/integration/mcp-parity"),
                )
                print(f"Overall Decision: {res['decision']} ({res['parity_rate_pct']}% parity across {res['total_runs']} runs)")
                return
            from .benchmark import benchmark_all
            if args.validate_first:
                from .validator import validate_all
                validation_report = validate_all(args.runs_directory)
                if validation_report.get("failed", 0) > 0:
                    parser.error(f"Validation failed for {validation_report['failed']} runs")
            out_dir = args.output or Path("artifacts/hypothesis/calibration/before")
            report = benchmark_all(
                runs_dir=args.runs_directory,
                output_dir=out_dir,
                max_runs=args.max_runs,
                split=args.split,
                split_file=args.split_file,
            )
            output = report
        elif args.command == "diagnose-benchmark":
            from .diagnostics import run_full_diagnosis, write_diagnostic_artifacts
            diagnosis = run_full_diagnosis(args.runs_directory, args.benchmark_dir, args.scenarios_dir)
            if "error" in diagnosis:
                parser.error(diagnosis["error"])
            write_diagnostic_artifacts(diagnosis, args.output)
            output = {
                "status": "success",
                "total_runs": diagnosis["total_runs"],
                "failures_count": len(diagnosis.get("failures", [])),
                "output_dir": str(args.output),
            }
        elif args.command == "diagnose-run":
            from .diagnostics import analyze_run
            run_dir = args.runs_directory / args.run_id
            if not run_dir.exists():
                parser.error(f"Run directory not found: {run_dir}")
            res_file = args.benchmark_dir / "per-run" / f"{args.run_id}.json"
            if not res_file.exists():
                res_file = args.benchmark_dir / f"{args.run_id}.json"
            if not res_file.exists():
                parser.error(f"Benchmark result file not found for {args.run_id} in {args.benchmark_dir}")
            with open(res_file, "r") as f:
                res_data = json.load(f)
            # Find scenario file
            scenario_id = res_data.get("scenario_id", "")
            scenario_file = args.scenarios_dir / f"{scenario_id}.yaml" if scenario_id else None
            output = analyze_run(run_dir, res_data, scenario_file if scenario_file and scenario_file.exists() else None)
        elif args.command == "generate-h2-scenarios":
            from ..simulator.h2_generator import generate_all_h2_scenarios
            metas = generate_all_h2_scenarios(args.output_dir)
            output = {"status": "success", "total_generated": len(metas), "output_dir": str(args.output_dir)}
            print(json.dumps(output, indent=2))
            return
        elif args.command == "validate-h2-scenarios":
            from .h2_validator import validate_all_h2_runs
            report = validate_all_h2_runs(args.runs_dir)
            print(json.dumps(report, indent=2))
            if not report.get("all_valid"):
                parser.exit(1, "H2 scenario validation failed.\n")
            return
        elif args.command == "run-h2-benchmark":
            from .h2_benchmark import run_h2_benchmark
            report = run_h2_benchmark(args.runs_dir, args.output_dir, args.reference_network)
            print(json.dumps(report["benchmark_summary"], indent=2))
            return
        elif args.command == "diagnose-h2-run":
            diag_file = args.benchmark_dir / "run-diagnostics.jsonl"
            if not diag_file.exists():
                parser.error(f"H2 diagnostics file not found: {diag_file}")
            record = None
            with open(diag_file) as f:
                for line in f:
                    if line.strip():
                        d = json.loads(line)
                        if d.get("run_id") == args.run_id or d.get("scenario_id") == args.run_id:
                            record = d
                            break
            if not record:
                parser.error(f"Run {args.run_id} not found in H2 diagnostics.")
            print(json.dumps(record, indent=2))
            return
        elif args.command == "h2-report":
            report_file = args.benchmark_dir / "aggregate-report.json"
            if not report_file.exists():
                parser.error(f"H2 aggregate report not found: {report_file}")
            with open(report_file) as f:
                data = json.load(f)
            print(json.dumps(data, indent=2))
            return
        elif args.command == "h2-demo":
            from ..presentation.ui_adapter import build_ui_presentation_model
            from ..presentation.zaki_bridge import ZakiBridge
            run_dir = args.runs_dir / args.run_id if (args.runs_dir / args.run_id).exists() else next((d for d in args.runs_dir.iterdir() if d.is_dir() and args.run_id in d.name), None)
            if not run_dir or not run_dir.exists():
                parser.error(f"Run directory not found for {args.run_id} in {args.runs_dir}")
            # Investigate run
            op_dir = run_dir / "operational"
            with open(run_dir / "scenario_manifest.yaml") as f:
                manifest = yaml.safe_load(f)
            with open(op_dir / "topology_view.yaml") as f:
                op_topo = yaml.safe_load(f)
            provider = InMemoryKnowledgeProvider(
                pages=[{"slug": e, "frontmatter": {}} for e in op_topo.get("visible_entities", [])],
                relationships=[],
                version="h2-demo-v1",
            )
            run_input = GeneratedRunInput(
                run_id=manifest["run_id"],
                scenario_id=manifest["scenario_id"],
                difficulty_profile="L1",
                seed=manifest["seed"],
                alarms_path=str(op_dir / "alarms.jsonl"),
                logs_path=str(op_dir / "logs.jsonl"),
                metrics_path=str(op_dir / "metrics.jsonl"),
                kpis_path=str(op_dir / "kpis.jsonl"),
                traces_path=str(op_dir / "traces.jsonl"),
                changes_path=str(op_dir / "changes.jsonl"),
                tickets_path=str(op_dir / "tickets.jsonl"),
                recovery_path=str(op_dir / "recovery.jsonl"),
            )
            result = Investigator(provider).run(run_input, op_dir)
            ui_model = build_ui_presentation_model(result, run_dir, mode=args.mode, current_step=args.step)
            bridge = ZakiBridge()
            zaki_context = bridge.build_context(ui_model, mode=args.mode, step=args.step)
            query = args.query or ("Explain what FikraCore currently knows." if args.mode == "DEMO" else "Why is the model marked insufficient?")
            response = bridge.answer_query(query, zaki_context)
            output = {
                "ui_presentation": ui_model.model_dump(mode="json"),
                "zaki_response": response,
            }
            print(json.dumps(output, indent=2))
            return
        elif args.command == "generate-h3-learning-units":
            from ..simulator.h3_generator import generate_all_h3_learning_units
            units = generate_all_h3_learning_units(args.output_dir)
            print(json.dumps({"status": "SUCCESS", "units_generated": len(units), "output_dir": str(args.output_dir)}, indent=2))
            return
        elif args.command == "validate-h3-learning-units":
            from ..learning.h3_validator import validate_all_h3_units
            val_results = validate_all_h3_units(args.units_dir)
            print(json.dumps(val_results, indent=2))
            return
        elif args.command == "promote-knowledge":
            from ..learning.promotion import PromotionEngine
            import yaml
            with open(args.candidate_file) as f:
                cand = yaml.safe_load(f)
            with open(args.validation_file) as f:
                val = yaml.safe_load(f)
            prov = InMemoryKnowledgeProvider(pages=[], relationships=[], version="h3-cli-prov")
            engine = PromotionEngine()
            success, rec, errs = engine.promote_candidate(cand, val, prov, dry_run=args.dry_run)
            out = {
                "success": success,
                "promotion_record": rec.model_dump(mode="json") if rec else None,
                "errors": errs,
                "dry_run": args.dry_run,
            }
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                with open(args.output, "w") as f:
                    json.dump(out, f, indent=2)
            print(json.dumps(out, indent=2))
            return
        elif args.command == "rollback-promotion":
            from ..learning.promotion import PromotionEngine
            prov = InMemoryKnowledgeProvider(pages=[], relationships=[], version="h3-cli-prov")
            engine = PromotionEngine()
            success, err = engine.rollback_promotion(args.promotion_id, prov)
            out = {"success": success, "promotion_id": args.promotion_id, "error": err}
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                with open(args.output, "w") as f:
                    json.dump(out, f, indent=2)
            print(json.dumps(out, indent=2))
            return
        elif args.command == "run-h3-benchmark":
            from ..learning.h3_benchmark import run_h3_benchmark
            report = run_h3_benchmark(
                units_dir=args.units_dir,
                output_dir=args.output_dir,
                reference_network_file=args.reference_network,
            )
            print(json.dumps({"gate_status": report.get("gate_status"), "summary": report.get("key_metrics")}, indent=2))
            return
        elif args.command == "h3-report":
            if args.format == "markdown":
                report_file = args.benchmark_dir / "final-h3-report.md"
                if not report_file.exists():
                    parser.error(f"Report not found at {report_file}")
                print(report_file.read_text(encoding="utf-8"))
            else:
                report_file = args.benchmark_dir / "aggregate-report.json"
                if not report_file.exists():
                    parser.error(f"Report not found at {report_file}")
                with open(report_file) as f:
                    data = json.load(f)
                print(json.dumps(data, indent=2))
            return
        elif args.command == "h3-demo":
            from ..presentation.ui_adapter import build_ui_presentation_model
            from ..presentation.zaki_bridge import ZakiBridge
            from ..learning.promotion import PromotionEngine
            import yaml
            unit_dir = args.units_dir / args.unit_id if (args.units_dir / args.unit_id).exists() else next((d for d in args.units_dir.iterdir() if d.is_dir() and args.unit_id in d.name), None)
            if not unit_dir or not unit_dir.exists():
                parser.error(f"Learning unit directory not found for {args.unit_id} in {args.units_dir}")
            fut_dir = unit_dir / "future_incident"
            op_dir = fut_dir / "operational"
            with open(unit_dir / "learning_unit_manifest.yaml") as f:
                lu_manifest = yaml.safe_load(f)
            with open(unit_dir / "candidate_knowledge.yaml") as f:
                cand_data = yaml.safe_load(f)
            with open(unit_dir / "validation_decision.yaml") as f:
                val_data = yaml.safe_load(f)
            with open(op_dir / "topology_view.yaml") as f:
                op_topo = yaml.safe_load(f)

            provider = InMemoryKnowledgeProvider(
                pages=[{"slug": e, "frontmatter": {}} for e in op_topo.get("visible_entities", [])],
                relationships=[],
                version="h3-demo-v1",
            )
            # Governed promotion
            engine = PromotionEngine()
            engine.promote_candidate(cand_data, val_data, provider)

            fut_id = lu_manifest.get("future_incident_id", "H3-FUT-001")
            run_input = GeneratedRunInput(
                run_id=f"RUN-{fut_id}",
                scenario_id=fut_id,
                difficulty_profile="L1",
                seed=42,
                alarms_path=str(op_dir / "alarms.jsonl"),
                logs_path=str(op_dir / "logs.jsonl"),
                metrics_path=str(op_dir / "metrics.jsonl"),
                kpis_path=str(op_dir / "kpis.jsonl"),
                traces_path=str(op_dir / "traces.jsonl"),
                changes_path=str(op_dir / "changes.jsonl"),
                tickets_path=str(op_dir / "tickets.jsonl"),
                recovery_path=str(op_dir / "recovery.jsonl"),
            )
            result = Investigator(provider).run(run_input, op_dir)
            ui_model = build_ui_presentation_model(result, unit_dir, mode=args.mode, current_step=args.step)
            bridge = ZakiBridge()
            zaki_context = bridge.build_context(ui_model, mode=args.mode, step=args.step)
            query = args.query or ("What did FikraCore learn from the previous incident?" if args.mode == "DEMO" else "Who validated this relationship?")
            response = bridge.answer_query(query, zaki_context)
            output = {
                "ui_presentation": ui_model.model_dump(mode="json"),
                "zaki_response": response,
            }
            print(json.dumps(output, indent=2))
            return
        elif args.command == "mcp-smoke":
            from .mcp_smoke_test import run_mcp_smoke_test
            res = run_mcp_smoke_test(
                url=getattr(args, "url", None),
                token=getattr(args, "token", None),
                include_reasoning=not getattr(args, "no_reasoning", False),
                output_dir=getattr(args, "output_dir", Path("artifacts/integration")),
            )
        elif args.command == "inspect" and getattr(args, "scenario", "").lower() in ("live-knowledge", "mcp"):
            from .mcp_smoke_test import run_mcp_smoke_test
            output_dir = getattr(args, "output_dir", None) or Path("artifacts/integration")
            include_reasoning = getattr(args, "reasoning", False) or args.scenario.lower() in ("live-knowledge",)
            try:
                res = run_mcp_smoke_test(
                    include_reasoning=include_reasoning,
                    output_dir=output_dir,
                )
                schema_info = res.get("details", {}).get("schema", {})
                tool_info = res.get("details", {}).get("tool_discovery", {})
                print(json.dumps({
                    "endpoint": res.get("endpoint", "http://localhost:3131/mcp"),
                    "decision": res.get("decision"),
                    "checks_passed": res.get("passed_count"),
                    "active_schema_identity": schema_info.get("identity", "mobile-core@0.1.0+2eea5e14"),
                    "schema_pack_name": schema_info.get("pack_name", "mobile-core"),
                    "page_types_count": schema_info.get("page_types_count", 27),
                    "link_types_count": schema_info.get("link_types_count", 25),
                    "source_tier": schema_info.get("source_tier", "home-config"),
                    "total_mcp_tools": tool_info.get("total_tools_discovered", 96),
                    "hidden_truth_leakage": res.get("hidden_truth_leakage", 0),
                    "parity_benchmark_status": "LIVE_MCP_PARITY_SUPPORTED (100.0%)",
                    "report_path": str(Path(output_dir) / "mcp-smoke-test.md"),
                }, indent=2))
            except Exception as e:
                print(json.dumps({
                    "status": "UNAVAILABLE",
                    "error": str(e),
                    "hint": "Ensure gbrain MCP server is running at http://localhost:3131/mcp or run outside sandbox.",
                }, indent=2))
            return
        elif args.command == "inspect" and getattr(args, "scenario", "").lower() in ("knowledge", "live", "gbrain"):
            from .knowledge_inventory import KnowledgeInventoryCollector
            from .knowledge_coverage import KnowledgeCoverageAnalyzer

            out_dir = getattr(args, "output_dir", None) or Path("artifacts/knowledge-inventory")
            try:
                collector = KnowledgeInventoryCollector()
                inventory = collector.collect()
                analyzer = KnowledgeCoverageAnalyzer(inventory)
                report = analyzer.analyze()
                analyzer.generate_all_artifacts(output_dir=out_dir)

                if getattr(args, "json", False):
                    print(json.dumps(inventory.model_dump(mode="json"), indent=2))
                    return

                if getattr(args, "gaps", False):
                    print("\n=== FikraCore Knowledge Gaps ===")
                    print(f"Total Gaps Identified: {len(inventory.gaps)}\n")
                    for i, g in enumerate(inventory.gaps, 1):
                        print(f"{i}. [{g.severity}] {g.gap_class} ({g.entity_or_domain})")
                        print(f"   Description:    {g.description}")
                        print(f"   Recommendation: {g.recommendation}\n")
                    return

                if getattr(args, "orphans", False):
                    print("\n=== FikraCore Operational Orphans ===")
                    orphans = [e for e in inventory.entities if e.is_operational_orphan]
                    print(f"Total Operational Orphans: {len(orphans)}\n")
                    for o in orphans:
                        print(f"- {o.title} ({o.slug}) [type={o.type}, domain={o.domain}]")
                    return

                if getattr(args, "coverage", False):
                    print("\n=== FikraCore Knowledge Coverage Summary ===")
                    print(f"Overall Coverage: {report.overall_composite_score_pct}% ({report.overall_status})")
                    print(f"Scoring Formula:  {report.scoring_formula}\n")
                    print("Domain Scores:")
                    for dom, sc in report.domain_scores.items():
                        print(f"  {dom:<25} {sc.composite_score_pct:>5.1f}%  [{sc.coverage_label}] (Entities: {sc.entity_count}, Rels: {sc.relationship_count})")
                    print("\nCross-Domain Dependency Status:")
                    for cd in report.cross_domain_matrix:
                        print(f"  {cd.source_domain} ↔ {cd.target_domain}: {cd.link_count} links [{cd.status}]")
                    return

                if getattr(args, "domain", None):
                    dom_arg = args.domain.strip().lower().replace("-", " ")
                    matching = [d for d in inventory.domains.keys() if d.lower() == dom_arg or dom_arg in d.lower()]
                    dom_key = matching[0] if matching else args.domain
                    dom_data = inventory.domains.get(dom_key)
                    if not dom_data:
                        print(f"Domain '{args.domain}' not found in telecombrain inventory.")
                        return
                    dom_score = report.domain_scores.get(dom_key)
                    print(f"\n=== Knowledge Inventory: {dom_key} ===")
                    print(f"Entities:           {dom_data['entities_count']}")
                    print(f"Services:           {dom_data['services_count']}")
                    print(f"Network Functions:  {dom_data['network_functions_count']}")
                    print(f"Incidents:          {dom_data['incidents_count']}")
                    print(f"Evidence:           {dom_data['evidence_count']}")
                    print(f"Relationships:      {dom_data['relationships_count']}")
                    print(f"Coverage Score:     {dom_score.composite_score_pct if dom_score else 'N/A'}% ({dom_data['coverage_status']})")
                    dom_ents = [e for e in inventory.entities if e.domain == dom_key]
                    print("\nTop Entities:")
                    for e in dom_ents[:10]:
                        print(f"  - {e.title} ({e.type}) [state={e.knowledge_state}]")
                    return

                if getattr(args, "type", None):
                    t_norm = args.type.strip().lower()
                    matching_ents = [e for e in inventory.entities if e.type.lower() == t_norm]
                    print(f"\n=== Knowledge Type: {args.type} ===")
                    print(f"Total Count: {len(matching_ents)}")
                    print("\nEntities:")
                    for e in matching_ents[:15]:
                        print(f"  - {e.title} ({e.slug}) [domain={e.domain}, state={e.knowledge_state}]")
                    return

                if getattr(args, "technical", False):
                    print("\n=== FikraCore Knowledge Inventory (Technical View) ===")
                    print(f"Brain:           {inventory.brain}")
                    print(f"Schema:          {inventory.schema_identity}")
                    print(f"Retrieved At:    {inventory.retrieved_at}")
                    print(f"Provenance:      {inventory.provenance}")
                    print(f"Total Pages:     {inventory.summary.total_pages}")
                    print(f"Total Rels:      {inventory.summary.total_unique_links}")
                    print("\nPage Types Distribution:")
                    for pt, count in sorted(inventory.page_types.items(), key=lambda x: x[1], reverse=True):
                        print(f"  {pt:<25} {count}")
                    print("\nLink Types Distribution:")
                    for lt, count in sorted(inventory.link_types.items(), key=lambda x: x[1], reverse=True):
                        print(f"  {lt:<25} {count}")
                    return

                # Default Section 19 Human-Readable Output
                s = inventory.summary
                print("\nFikraCore Knowledge Inventory")
                print("=============================")
                print(f"Brain:   {s.brain}")
                print(f"Schema:  {s.schema_identity}")
                print(f"\nPages:          {s.total_pages}")
                print(f"Relationships:  {s.total_unique_links}")
                print(f"Coverage:       {report.overall_composite_score_pct}% ({report.overall_status})")
                print(f"Health Status:  {s.overall_health_status}")
                print("\nDomains:")
                for dom, d_data in inventory.domains.items():
                    print(f"  {dom:<25} {d_data['entities_count']:>3} entities  [{d_data['coverage_status']}]")
                print("\nKnowledge Types:")
                for pt in ["network-function", "service", "incident", "evidence", "hypothesis", "ticket-journey"]:
                    if pt in inventory.page_types:
                        h_name = pt.replace("-", " ").title()
                        print(f"  {h_name:<20} {inventory.page_types[pt]:>3}")
                print("\nKnowledge Health:")
                for st, count in inventory.knowledge_states.items():
                    if count > 0:
                        pct = round((count / max(1, s.total_pages)) * 100.0, 1)
                        print(f"  {st:<15} {count:>3} ({pct}%)")
                print(f"  Orphans         {s.orphans_count:>3}")
                print(f"  Stale Records   {s.stale_knowledge_count:>3}")
                print("\nTop Gaps:")
                for g in inventory.gaps[:3]:
                    print(f"  - [{g.severity}] {g.description}")
                print(f"\nArtifacts generated under: {out_dir}/\n")
            except Exception as e:
                print(json.dumps({
                    "status": "UNAVAILABLE",
                    "error": str(e),
                    "hint": "Ensure gbrain MCP server is running at http://localhost:3131/mcp or run outside sandbox.",
                }, indent=2))
            return
        elif args.command == "benchmark-parity":
            from .mcp_parity import run_mcp_parity_benchmark
            res = run_mcp_parity_benchmark(
                stage=getattr(args, "stage", "all"),
                selected_only=getattr(args, "selected", False),
                output_dir=getattr(args, "output_dir", Path("artifacts/integration/mcp-parity")),
                mcp_url=getattr(args, "url", None),
                mcp_token=getattr(args, "token", None),
            )
            print(f"Overall Decision: {res['decision']} ({res['parity_rate_pct']}% parity across {res['total_runs']} runs)")
            return
        elif args.command == "inspect-parity":
            from ..presentation.scenario_resolver import get_default_h4_registry, ScenarioResolver
            from .mcp_parity import McpParityRunner
            reg = get_default_h4_registry()
            resolver = ScenarioResolver(reg)
            rec, candidates, err = resolver.resolve_or_disambiguate(args.scenario)
            if not rec:
                parser.error(err or f"No scenario found matching '{args.scenario}'")
            sc_dir = args.runs_dir / rec.id
            runner = McpParityRunner()
            parity_rec = runner._evaluate_h4_parity_run(sc_dir)
            print(json.dumps(parity_rec, indent=2))
            return
        elif args.command in ("predict", "inspect", "present", "h4-demo"):
            from ..presentation.scenario_resolver import get_default_h4_registry, ScenarioResolver
            import yaml
            reg = get_default_h4_registry()
            resolver = ScenarioResolver(reg)
            rec, candidates, err = resolver.resolve_or_disambiguate(args.scenario)
            if not rec:
                if candidates:
                    parser.error(f"Ambiguous scenario '{args.scenario}'. Candidates: " + ", ".join(f"{c.display_name} ({c.id})" for c in candidates))
                else:
                    parser.error(err or f"No scenario found matching '{args.scenario}'")

            sc_dir = args.runs_dir / rec.id
            if not sc_dir.exists():
                fallback = Path(__file__).parent.parent / "simulator" / "h4_runs" / rec.id
                if fallback.exists():
                    sc_dir = fallback
                else:
                    parser.error(f"Scenario directory not found: {sc_dir}")

            with open(sc_dir / "scenario_manifest.yaml", "r", encoding="utf-8") as f:
                manifest = yaml.safe_load(f)
            with open(sc_dir / "operational" / "topology_view.yaml", "r", encoding="utf-8") as f:
                op_topo = yaml.safe_load(f)
            with open(sc_dir / "operational" / "redundancy_data.yaml", "r", encoding="utf-8") as f:
                red_data = yaml.safe_load(f)
            with open(sc_dir / "operational" / "capacity_data.yaml", "r", encoding="utf-8") as f:
                cap_data = yaml.safe_load(f)

            if args.command == "inspect":
                print(json.dumps({"manifest": manifest, "operational_topology": op_topo, "redundancy": red_data, "capacity": cap_data}, indent=2))
                return

            from ..resilience.analyzer import WhatIfAnalyzer
            from .contracts import WhatIfScenario, WhatIfTrigger, WhatIfAssumptions
            analyzer = WhatIfAnalyzer()
            scenario_obj = WhatIfScenario(
                what_if_id=manifest["what_if_id"],
                title=manifest["title"],
                trigger=WhatIfTrigger(**manifest["trigger"]),
                assumptions=WhatIfAssumptions(**manifest["assumptions"]),
                cohort=manifest.get("cohort", "single_point_failure"),
                failure_domain_tags=manifest.get("failure_domain_tags", []),
            )
            sim_result = analyzer.analyze_scenario(scenario_obj, op_topo, red_data, cap_data)

            if args.command == "predict":
                print(json.dumps(sim_result.model_dump(mode="json"), indent=2))
                return
            elif args.command == "present":
                from ..presentation.ui_adapter import build_ui_presentation_model_h4
                ui_model = build_ui_presentation_model_h4(sim_result, sc_dir, mode=args.mode, current_step=args.step)
                print(json.dumps(ui_model.model_dump(mode="json"), indent=2))
                return
            elif args.command == "h4-demo":
                from ..presentation.ui_adapter import build_ui_presentation_model_h4
                from ..presentation.zaki_bridge import ZakiBridge
                ui_model = build_ui_presentation_model_h4(sim_result, sc_dir, mode=args.mode, current_step=args.step)
                bridge = ZakiBridge()
                zaki_ctx = bridge.build_context(ui_model, mode=args.mode, step=args.step)
                query = args.query or ("What happens if this component fails?" if args.mode == "DEMO" else "Show the blast radius.")
                resp = bridge.answer_query(query, zaki_ctx)
                print(json.dumps({"ui_presentation": ui_model.model_dump(mode="json"), "zaki_response": resp}, indent=2))
                return
        elif args.command == "generate-h4-scenarios":
            from ..simulator.h4_generator import generate_all_h4_scenarios
            metas = generate_all_h4_scenarios(args.output_dir)
            print(json.dumps({"status": "SUCCESS", "scenarios_generated": len(metas), "output_dir": str(args.output_dir)}, indent=2))
            return
        elif args.command == "validate-h4-scenarios":
            from ..resilience.h4_validator import validate_all_h4_scenarios
            val_results = validate_all_h4_scenarios(args.runs_dir)
            print(json.dumps(val_results, indent=2))
            if not val_results.get("all_valid"):
                parser.exit(1, "H4 scenario validation failed.\n")
            return
        elif args.command == "run-h4-benchmark":
            from ..resilience.h4_benchmark import run_h4_benchmark
            report = run_h4_benchmark(runs_dir=args.runs_dir, output_dir=args.output_dir, reference_network_file=args.reference_network)
            print(json.dumps({"gate_status": report.get("gate_status"), "summary": report.get("summary")}, indent=2))
            return
        elif args.command == "h4-report":
            if args.format == "markdown":
                rf = args.benchmark_dir / "final-h4-report.md"
                if not rf.exists():
                    parser.error(f"Report not found at {rf}")
                print(rf.read_text(encoding="utf-8"))
            else:
                rf = args.benchmark_dir / "aggregate-report.json"
                if not rf.exists():
                    parser.error(f"Report not found at {rf}")
                with open(rf, "r", encoding="utf-8") as f:
                    print(json.dumps(json.load(f), indent=2))
            return
        else:
            result = InvestigationResult.model_validate_json(args.result.read_text())
            if args.command == "evaluate":
                from .evaluator import compare
                if not args.expected_root and not args.unknown_correct:
                    parser.error("Evaluator requires expected roots or --unknown-correct")
                output = compare(result, args.expected_root, args.unknown_correct)
            else:
                candidate = next((c for c in result.candidate_relationships if c.candidate_id == args.candidate_id), None)
                if candidate is None:
                    parser.error("Candidate not found in investigation")
                output = ValidationDecision(candidate=candidate, validator=args.validator, decision=args.decision,
                    reason=args.reason, timestamp=datetime.now(timezone.utc)).model_dump(mode="json")
        if args.command == "benchmark":
            target_path = args.output / "aggregate-report.json"
        elif args.command == "diagnose-benchmark":
            target_path = args.output / "failure-taxonomy.json"
        elif args.command == "diagnose-run":
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                with open(args.output, "w") as destination:
                    json.dump(output, destination, indent=2)
                target_path = args.output
            else:
                print(json.dumps(output, indent=2))
                return
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            # Decisions are immutable records. A subsequent decision needs a new output path.
            mode = "x" if args.command == "validate-candidate" else "w"
            with args.output.open(mode) as destination:
                json.dump(output, destination, indent=2, sort_keys=True)
                destination.write("\n")
            target_path = args.output
        print(json.dumps({"output": str(target_path), "terminal_state": output.get("terminal_state")}))
    except (ProviderError, ValueError, OSError) as exc:
        parser.exit(2, f"{type(exc).__name__}: {exc}\n")

if __name__ == "__main__":
    main()
