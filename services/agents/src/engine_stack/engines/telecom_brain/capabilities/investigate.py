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


def _simulator_dir() -> Path:
    return Path(__file__).parent.parent / "simulator"


def _scenario_match_values(path: Path, manifest: dict[str, Any]) -> set[str]:
    aliases = manifest.get("aliases") or []
    if not isinstance(aliases, list):
        aliases = []
    values = {
        path.stem,
        str(manifest.get("id") or ""),
        str(manifest.get("display_name") or ""),
        *(str(alias) for alias in aliases),
    }
    return {value.strip().lower() for value in values if value and value.strip()}


def _resolve_scenario_definition(scenario_arg: str) -> tuple[Path | None, dict[str, Any]]:
    """Resolve a scenario definition file without treating it as executed evidence."""
    scenario_dir = _simulator_dir() / "scenarios"
    if not scenario_dir.exists():
        return None, {}

    query = scenario_arg.strip().lower()
    for path in sorted(scenario_dir.glob("*.yaml")):
        try:
            manifest = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        if query in _scenario_match_values(path, manifest):
            return path, manifest

    return None, {}


def _needs_simulation_response(
    scenario_arg: str,
    scenario_file: Path | None,
    scenario_manifest: dict[str, Any],
) -> dict[str, Any]:
    scenario_id = str(scenario_manifest.get("id") or scenario_arg)
    display_name = str(scenario_manifest.get("display_name") or scenario_id)
    return {
        "status": "NEEDS_SIMULATION",
        "scenario_id": scenario_id,
        "display_name": display_name,
        "message": (
            f"{scenario_id} is a known scenario, but no simulation run evidence is available yet. "
            "Start the scenario run first, then rerun investigation against the generated run state."
        ),
        "next_action": "Start the selected scenario in Simulator Lab, then run investigate again with the active run context.",
        "scenario_definition": str(scenario_file) if scenario_file else None,
        "reason": "Investigation requires operational evidence from a simulation run; a scenario definition alone is not enough.",
    }


def investigate_handler(inputs: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
    """Handler executing operational investigation without truth leakage."""
    run_dir_str = inputs.get("run_directory") or inputs.get("runs_directory")
    scenario_arg = inputs.get("scenario")

    run_dir: Path | None = None
    scenario_file: Path | None = None
    scenario_manifest: dict[str, Any] = {}
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
            if run_dir.is_file():
                scenario_file = run_dir
                try:
                    scenario_manifest = yaml.safe_load(run_dir.read_text(encoding="utf-8")) or {}
                except Exception:
                    scenario_manifest = {}
                run_dir = None
        else:
            # Check default simulator paths
            base_dir = _simulator_dir()
            for candidate_dir in [
                base_dir / "runs" / str(scenario_arg),
                base_dir / "h2_runs" / str(scenario_arg),
                base_dir / "h4_runs" / str(scenario_arg),
            ]:
                if candidate_dir.exists():
                    run_dir = candidate_dir
                    break
            if not run_dir:
                scenario_file, scenario_manifest = _resolve_scenario_definition(str(scenario_arg))

    if not run_dir or not run_dir.exists():
        if scenario_arg and scenario_file:
            return _needs_simulation_response(str(scenario_arg), scenario_file, scenario_manifest)
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
