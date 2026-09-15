"""Validate Capability for FikraCore (§236).

Validate scenarios, learning units, runs, and artifacts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .registry import CapabilityDefinition, ExecutionContext, RolePermission, CapabilityError


def validate_handler(inputs: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
    """Handler dispatching artifact, scenario, or learning unit validation."""
    target = str(inputs.get("target") or "scenarios").lower()
    stage = str(inputs.get("stage") or "all").lower()

    if stage == "h4" or target == "h4":
        from ..resilience.h4_validator import validate_all_h4_scenarios
        runs_dir = Path(inputs.get("runs_dir") or Path(__file__).parent.parent / "simulator" / "h4_runs")
        report = validate_all_h4_scenarios(runs_dir)
        return {"stage": "H4", "validation": report}

    elif stage == "h3" or target in ("h3", "learning-units", "units"):
        from ..learning.h3_validator import validate_all_h3_units
        units_dir = Path(inputs.get("units_dir") or Path(__file__).parent.parent / "simulator" / "h3_runs")
        report = validate_all_h3_units(units_dir)
        return {"stage": "H3", "validation": report}

    elif stage == "h2" or target == "h2":
        from ..investigation.h2_validator import validate_all_h2_runs
        runs_dir = Path(inputs.get("runs_dir") or Path(__file__).parent.parent / "simulator" / "h2_runs")
        report = validate_all_h2_runs(runs_dir)
        return {"stage": "H2", "validation": report}

    else:
        # Default H1 runs validation
        from ..investigation.validator import validate_all
        runs_dir = Path(inputs.get("runs_dir") or inputs.get("runs_directory") or Path(__file__).parent.parent / "simulator" / "runs")
        report = validate_all(runs_dir)
        return {"stage": "H1", "validation": report}


validate_capability = CapabilityDefinition(
    name="validate",
    description="Validate scenarios, learning units and artifacts",
    input_schema={
        "type": "object",
        "properties": {
            "target": {"type": "string", "enum": ["scenarios", "learning-units", "runs", "h2", "h3", "h4"]},
            "stage": {"type": "string", "enum": ["h1", "h2", "h3", "h4", "all"]},
            "runs_dir": {"type": "string"},
        },
    },
    output_schema={"type": "object", "description": "Validation results"},
    permissions=[RolePermission.OPERATOR, RolePermission.SME_VALIDATOR, RolePermission.ADMIN],
    supports_cli=True,
    supports_ui=True,
    supports_zaki=False,
    supports_demo=False,
    supports_api=True,
    read_only=True,
    handler=validate_handler,
)
