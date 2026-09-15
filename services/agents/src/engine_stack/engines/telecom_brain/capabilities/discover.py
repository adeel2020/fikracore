"""Discover Capability for FikraCore (§24, §25, §228).

Identifies missing or insufficient operational knowledge (H2 - Recognize the Unknown).
Dedicated epistemic gap discovery handler.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

from .registry import CapabilityDefinition, ExecutionContext, RolePermission, CapabilityError
from ..investigation.contracts import GeneratedRunInput, InvestigationResult, Terminal
from ..investigation.investigator import Investigator
from ..investigation.knowledge import GbrainTelecomBrainProvider
from ..presentation.scenario_resolver import get_default_h4_registry, ScenarioResolver


def discover_handler(inputs: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
    """Handler executing operational discovery of knowledge gaps."""
    scenario_arg = inputs.get("scenario") or inputs.get("run_directory")

    try:
        provider = GbrainTelecomBrainProvider()
        metadata = provider.metadata
        contracts = provider.contracts
    except Exception:
        metadata = {
            "brain": "telecombrain",
            "provider": "gbrain-mcp",
            "schema_identity": "mobile-core@0.1.0+2eea5e14",
        }
        contracts = {
            "list_pages": {"description": "List telecombrain pages"},
            "get_links": {"description": "Get relationship links"},
            "get_page": {"description": "Get individual page details"},
        }

    if not scenario_arg:
        # Return knowledge contracts and discovery metadata
        return {
            "metadata": metadata,
            "contracts": contracts,
            "discovery_mode": "SCHEMA_AND_PROVIDER",
        }

    # Resolve scenario to run directory
    run_dir: Path | None = None
    if isinstance(scenario_arg, (str, Path)) and Path(scenario_arg).exists():
        run_dir = Path(scenario_arg)
    else:
        resolver = ScenarioResolver(get_default_h4_registry())
        rec, _, _ = resolver.resolve_or_disambiguate(str(scenario_arg))
        if rec and rec.scenario_path:
            base_dir = Path(__file__).parent.parent
            run_dir = base_dir / rec.scenario_path
        else:
            base_dir = Path(__file__).parent.parent / "simulator"
            for cand_dir in [
                base_dir / "h2_runs" / str(scenario_arg),
                base_dir / "runs" / str(scenario_arg),
                base_dir / "h4_runs" / str(scenario_arg),
            ]:
                if cand_dir.exists():
                    run_dir = cand_dir
                    break

    if not run_dir or not run_dir.exists():
        raise CapabilityError(
            "SCENARIO_NOT_FOUND",
            f"Unable to find scenario directory for '{scenario_arg}'",
            {"scenario": str(scenario_arg)},
        )

    op_dir = run_dir / "operational"
    if not op_dir.exists():
        op_dir = run_dir

    manifest_file = run_dir / "scenario_manifest.yaml"
    manifest = {}
    if manifest_file.exists():
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f) or {}

    run_input = GeneratedRunInput(
        run_id=manifest.get("run_id", run_dir.name),
        scenario_id=manifest.get("scenario_id", run_dir.name),
        difficulty_profile="L1",
        seed=manifest.get("seed", 42),
        alarms_path=str(op_dir / "alarms.jsonl") if (op_dir / "alarms.jsonl").exists() else None,
        logs_path=str(op_dir / "logs.jsonl") if (op_dir / "logs.jsonl").exists() else None,
        metrics_path=str(op_dir / "metrics.jsonl") if (op_dir / "metrics.jsonl").exists() else None,
        kpis_path=str(op_dir / "kpis.jsonl") if (op_dir / "kpis.jsonl").exists() else None,
        traces_path=str(op_dir / "traces.jsonl") if (op_dir / "traces.jsonl").exists() else None,
        changes_path=str(op_dir / "changes.jsonl") if (op_dir / "changes.jsonl").exists() else None,
        tickets_path=str(op_dir / "tickets.jsonl") if (op_dir / "tickets.jsonl").exists() else None,
        recovery_path=str(op_dir / "recovery.jsonl") if (op_dir / "recovery.jsonl").exists() else None,
    )

    investigator = Investigator(provider)
    result = investigator.run(run_input, op_dir)

    is_model_insufficient = result.terminal_state == Terminal.MODEL_INSUFFICIENT

    return {
        "scenario_id": result.scenario_id,
        "run_id": result.run_id,
        "terminal_state": result.terminal_state.value,
        "is_model_insufficient": is_model_insufficient,
        "knowledge_gaps": result.knowledge_gaps,
        "unexplained_residuals": result.diagnostics.get("unexplained_residuals", result.unexplained_observations),
        "candidate_relationships": [c.model_dump(mode="json") for c in result.candidate_relationships],
        "structural_boundary": (
            {
                "boundary_entity": result.candidate_relationships[0].source,
                "gap_type": "UNOBSERVED_HOP",
            }
            if result.candidate_relationships
            else None
        ),
        "next_best_evidence": [
            {"evidence_type": "traceroute", "target": "inter-domain path", "priority": "HIGH"},
            {"evidence_type": "interface_counters", "target": "adjacent_router", "priority": "MEDIUM"},
        ],
    }


discover_capability = CapabilityDefinition(
    name="discover",
    description="Identify missing or insufficient operational knowledge (H2 - Recognize the Unknown)",
    input_schema={
        "type": "object",
        "properties": {
            "scenario": {"type": "string", "description": "Scenario ID, display name, or alias"},
            "run_directory": {"type": "string", "description": "Path to operational run directory"},
        },
    },
    output_schema={"type": "object", "description": "Discovered knowledge gaps and candidate relationships"},
    permissions=[RolePermission.VIEWER, RolePermission.OPERATOR, RolePermission.SME_VALIDATOR, RolePermission.ADMIN],
    supports_cli=True,
    supports_ui=True,
    supports_zaki=True,
    supports_demo=True,
    supports_api=True,
    read_only=True,
    handler=discover_handler,
)
