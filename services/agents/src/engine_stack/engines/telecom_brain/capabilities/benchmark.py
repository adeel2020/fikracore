"""Benchmark Capability for FikraCore (§87, §88, §234).

Run H1-H4 and integration parity benchmarks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .registry import CapabilityDefinition, ExecutionContext, RolePermission, CapabilityError


def benchmark_handler(inputs: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
    """Handler executing stage-specific or parity benchmarks."""
    stage = str(inputs.get("stage", "all")).lower()

    if stage in ("parity", "mcp-parity", "live-parity"):
        from ..investigation.mcp_parity import run_mcp_parity_benchmark
        out_dir = Path(inputs.get("output_dir") or "artifacts/integration/mcp-parity")
        res = run_mcp_parity_benchmark(
            stage=inputs.get("substage", "all"),
            selected_only=inputs.get("selected_only", False),
            output_dir=out_dir,
        )
        return {
            "stage": "MCP_PARITY",
            "decision": res.get("decision"),
            "parity_rate_pct": res.get("parity_rate_pct"),
            "total_runs": res.get("total_runs"),
            "passed_parity": res.get("passed_parity"),
            "report_path": str(out_dir),
        }

    elif stage in ("h4", "predict", "resilience"):
        from ..resilience.h4_benchmark import run_h4_benchmark
        runs_dir = Path(inputs.get("runs_dir") or Path(__file__).parent.parent / "simulator" / "h4_runs")
        out_dir = Path(inputs.get("output_dir") or "artifacts/hypothesis/h4")
        ref_net = Path(inputs.get("reference_network") or Path(__file__).parent.parent / "simulator" / "operator_model" / "reference_synthetic_network.yaml")
        report = run_h4_benchmark(runs_dir=runs_dir, output_dir=out_dir, reference_network_file=ref_net)
        return {
            "stage": "H4",
            "gate_status": report.get("gate_status"),
            "summary": report.get("summary"),
            "report_path": str(out_dir),
        }

    elif stage in ("h3", "learn"):
        from ..learning.h3_benchmark import run_h3_benchmark
        units_dir = Path(inputs.get("units_dir") or Path(__file__).parent.parent / "simulator" / "h3_runs")
        out_dir = Path(inputs.get("output_dir") or "artifacts/hypothesis/h3")
        ref_net = Path(inputs.get("reference_network") or Path(__file__).parent.parent / "simulator" / "operator_model" / "reference_synthetic_network.yaml")
        report = run_h3_benchmark(units_dir=units_dir, output_dir=out_dir, reference_network_file=ref_net)
        return {
            "stage": "H3",
            "gate_status": report.get("gate_status"),
            "summary": report.get("key_metrics"),
            "report_path": str(out_dir),
        }

    elif stage in ("h2", "discover"):
        from ..investigation.h2_benchmark import run_h2_benchmark
        runs_dir = Path(inputs.get("runs_dir") or Path(__file__).parent.parent / "simulator" / "h2_runs")
        out_dir = Path(inputs.get("output_dir") or "artifacts/hypothesis/h2")
        ref_net = Path(inputs.get("reference_network") or Path(__file__).parent.parent / "simulator" / "operator_model" / "reference_synthetic_network.yaml")
        report = run_h2_benchmark(runs_dir, out_dir, ref_net)
        return {
            "stage": "H2",
            "summary": report.get("benchmark_summary"),
            "report_path": str(out_dir),
        }

    else:
        # Default H1 benchmark
        from ..investigation.benchmark import benchmark_all
        runs_dir = Path(inputs.get("runs_dir") or Path(__file__).parent.parent / "simulator" / "runs")
        out_dir = Path(inputs.get("output_dir") or "artifacts/hypothesis/calibration/before")
        rep = benchmark_all(runs_dir, out_dir, inputs.get("max_runs"), split=inputs.get("split"))
        return {
            "stage": "H1",
            "summary": rep,
            "report_path": str(out_dir),
        }


benchmark_capability = CapabilityDefinition(
    name="benchmark",
    description="Run H1-H4 and integration benchmarks",
    input_schema={
        "type": "object",
        "properties": {
            "stage": {"type": "string", "enum": ["h1", "h2", "h3", "h4", "parity", "all"]},
            "runs_dir": {"type": "string"},
            "output_dir": {"type": "string"},
            "max_runs": {"type": "integer"},
        },
    },
    output_schema={"type": "object", "description": "Benchmark evaluation summary and gate status"},
    permissions=[RolePermission.OPERATOR, RolePermission.ADMIN],
    supports_cli=True,
    supports_ui=True,
    supports_zaki=False,
    supports_demo=False,
    supports_api=True,
    read_only=True,
    handler=benchmark_handler,
)
