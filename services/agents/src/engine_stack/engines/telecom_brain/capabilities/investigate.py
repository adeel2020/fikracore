"""Investigate Capability for FikraCore (§23, §227).

Explains what happened and why (H1 - Reason).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

from .registry import CapabilityDefinition, ExecutionContext, RolePermission, CapabilityError
from ..investigation.contracts import GeneratedRunInput, InvestigationResult
from ..investigation.evidence import input_from_run
from ..investigation.investigator import Investigator
from ..investigation.knowledge import (
    FrozenTelecomBrainProvider,
    GbrainTelecomBrainProvider,
    InMemoryKnowledgeProvider,
)
from ..presentation.scenario_resolver import get_default_h4_registry, ScenarioResolver


def investigate_handler(inputs: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
    """Handler executing operational investigation without truth leakage."""
    run_dir_str = inputs.get("run_directory") or inputs.get("runs_directory")
    scenario_arg = inputs.get("scenario")

    run_dir: Path | None = None
    if run_dir_str:
        run_dir = Path(run_dir_str)
    elif scenario_arg:
        resolver = ScenarioResolver(get_default_h4_registry())
        rec, _, _ = resolver.resolve_or_disambiguate(str(scenario_arg))
        if rec and rec.scenario_path:
            run_dir = Path(rec.scenario_path)
            if not run_dir.is_absolute():
                base_dir = Path(__file__).parent.parent
                run_dir = base_dir / rec.scenario_path
        else:
            # Check default simulator paths
            base_dir = Path(__file__).parent.parent / "simulator"
            for candidate_dir in [
                base_dir / "runs" / str(scenario_arg),
                base_dir / "h2_runs" / str(scenario_arg),
                base_dir / "h4_runs" / str(scenario_arg),
            ]:
                if candidate_dir.exists():
                    run_dir = candidate_dir
                    break

    if not run_dir or not run_dir.exists():
        raise CapabilityError(
            "SCENARIO_NOT_FOUND",
            f"Unable to locate scenario run directory for inputs: {inputs}",
            {"input_data": inputs},
        )

    snapshot_path = inputs.get("snapshot")
    provider = FrozenTelecomBrainProvider(Path(snapshot_path)) if snapshot_path else GbrainTelecomBrainProvider()

    op_dir = run_dir / "operational"
    if not op_dir.exists():
        op_dir = run_dir

    try:
        generated = input_from_run(run_dir)
    except Exception:
        # Fallback if standard operational files exist
        manifest_file = run_dir / "scenario_manifest.yaml"
        manifest = {}
        if manifest_file.exists():
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = yaml.safe_load(f) or {}

        generated = GeneratedRunInput(
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
    res: InvestigationResult = investigator.run(generated, op_dir)
    return res.model_dump(mode="json")


investigate_capability = CapabilityDefinition(
    name="investigate",
    description="Explain what happened and why (H1 - Reason)",
    input_schema={
        "type": "object",
        "properties": {
            "run_directory": {"type": "string", "description": "Path to the scenario run directory"},
            "scenario": {"type": "string", "description": "Scenario ID, display name, or alias"},
            "snapshot": {"type": "string", "description": "Optional snapshot path for FrozenProvider"},
        },
    },
    output_schema={"type": "object", "description": "Standard InvestigationResult payload"},
    permissions=[RolePermission.VIEWER, RolePermission.OPERATOR, RolePermission.SME_VALIDATOR, RolePermission.ADMIN],
    supports_cli=True,
    supports_ui=True,
    supports_zaki=True,
    supports_demo=True,
    supports_api=True,
    read_only=True,
    handler=investigate_handler,
)
