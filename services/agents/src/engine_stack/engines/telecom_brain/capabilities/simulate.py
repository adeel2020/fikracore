"""Simulate Capability for FikraCore (§38, §39, §231).

Execute and replay simulator scenarios across any stage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

from .registry import CapabilityDefinition, ExecutionContext, RolePermission, CapabilityError
from .investigate import investigate_handler
from .predict import predict_handler
from ..presentation.scenario_resolver import get_default_h4_registry, ScenarioResolver
from ..simulator.simulation_manager import simulation_manager


def simulate_handler(inputs: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
    """Handler executing scenario simulation or replay."""
    scenario_query = inputs.get("scenario") or "H4-WI-001"
    stage_input = inputs.get("stage")
    stage = str(stage_input).upper() if stage_input else ""

    if "H4" in str(scenario_query).upper() or stage == "H4":
        # Forward What-If simulation
        predict_res = predict_handler(inputs, context)
        return {
            "simulation_id": f"SIM-{scenario_query}",
            "scenario": scenario_query,
            "stage": "H4",
            "status": "COMPLETED",
            "simulation_type": "PROACTIVE_WHAT_IF",
            "results": predict_res,
        }
    else:
        # Causal RCA / Investigation simulation
        inv_res = investigate_handler(inputs, context)
        if inv_res.get("status") == "NEEDS_SIMULATION":
            run = simulation_manager.start_clean_run_for_scenario(
                scenario_id=str(inv_res.get("scenario_id") or scenario_query),
                speed=float(inputs.get("speed") or 1.0),
                mode=str(inputs.get("mode") or "live"),
            )
            state = simulation_manager.get_state(scenario_id=run.scenario_id, run_id=run.run_id)
            return {
                "simulation_id": f"SIM-{scenario_query}",
                "scenario": run.scenario_id,
                "display_name": inv_res.get("display_name"),
                "stage": stage or state.get("current_stage") or "TRIGGER",
                "status": run.status,
                "simulation_type": "LIVE_SCENARIO_STATE",
                "run_id": run.run_id,
                "started_at": run.started_at,
                "message": f"Simulation state started for {run.scenario_id}. Use this active run context for Zaki status, explanation, and Storyteller actions.",
                "state": {
                    "current_stage": state.get("current_stage"),
                    "stage_status": state.get("stage_status"),
                    "snapshot_version": state.get("snapshot_version"),
                    "sequence": state.get("sequence"),
                },
                "next_action": "Open the selected scenario in Simulator Lab or advance the run to collect execution evidence.",
            }
        return {
            "simulation_id": f"SIM-{scenario_query}",
            "scenario": scenario_query,
            "stage": stage or "H1",
            "status": "COMPLETED",
            "simulation_type": "CAUSAL_INVESTIGATION",
            "results": inv_res,
        }


simulate_capability = CapabilityDefinition(
    name="simulate",
    description="Execute and replay simulator scenarios across any stage",
    input_schema={
        "type": "object",
        "properties": {
            "scenario": {"type": "string", "description": "Scenario ID, display name, or alias"},
            "stage": {"type": "string", "enum": ["H1", "H2", "H3", "H4"]},
            "runs_dir": {"type": "string"},
        },
    },
    output_schema={"type": "object", "description": "Simulation execution results"},
    permissions=[RolePermission.OPERATOR, RolePermission.SME_VALIDATOR, RolePermission.ADMIN],
    supports_cli=True,
    supports_ui=True,
    supports_zaki=True,
    supports_demo=True,
    supports_api=True,
    read_only=True,
    handler=simulate_handler,
)
