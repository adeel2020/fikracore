"""Predict Capability for FikraCore (§30, §31, §32, §33, §230).

Run proactive what-if and resilience analysis (H4 - Predict / Resilience).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

from .registry import CapabilityDefinition, ExecutionContext, RolePermission, CapabilityError
from ..investigation.contracts import WhatIfScenario, WhatIfTrigger, WhatIfAssumptions
from ..presentation.scenario_resolver import get_default_h4_registry, ScenarioResolver
from ..resilience.analyzer import WhatIfAnalyzer


def _find_dir(rel_path: str | Path) -> Path:
    p = Path(rel_path)
    if p.exists():
        return p
    cur = Path(__file__).resolve().parent
    while cur != cur.parent:
        candidate = cur / rel_path
        if candidate.exists():
            return candidate
        cur = cur.parent
    return p


def predict_handler(inputs: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
    """Handler executing proactive forward failure simulation and CFS analysis."""
    scenario_query = inputs.get("scenario") or "H4-WI-001"
    runs_dir_str = inputs.get("runs_dir")

    resolver = ScenarioResolver(get_default_h4_registry())
    rec, candidates, disambig_msg = resolver.resolve_or_disambiguate(str(scenario_query))

    if not rec:
        if candidates:
            raise CapabilityError(
                "AMBIGUOUS_SCENARIO",
                disambig_msg or f"Ambiguous scenario query: '{scenario_query}'",
                {"candidates": [c.model_dump(mode="json") for c in candidates]},
            )
        raise CapabilityError("SCENARIO_NOT_FOUND", f"Scenario not found matching '{scenario_query}'")

    runs_dir = _find_dir(runs_dir_str) if runs_dir_str else Path(__file__).parent.parent / "simulator" / "h4_runs"
    sc_dir = runs_dir / rec.id

    if not sc_dir.exists():
        # Fallback to module simulator path
        fallback = Path(__file__).parent.parent / "simulator" / "h4_runs" / rec.id
        if fallback.exists():
            sc_dir = fallback
        else:
            raise CapabilityError("SCENARIO_NOT_FOUND", f"Scenario directory does not exist: {sc_dir}")

    manifest_file = sc_dir / "scenario_manifest.yaml"
    op_dir = sc_dir / "operational"

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
    with open(op_dir / "topology_view.yaml", "r", encoding="utf-8") as f:
        op_topo = yaml.safe_load(f)
    with open(op_dir / "redundancy_data.yaml", "r", encoding="utf-8") as f:
        red_data = yaml.safe_load(f)
    with open(op_dir / "capacity_data.yaml", "r", encoding="utf-8") as f:
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
    return sim_result.model_dump(mode="json")


predict_capability = CapabilityDefinition(
    name="predict",
    description="Run proactive what-if and resilience analysis (H4 - Predict / Resilience)",
    input_schema={
        "type": "object",
        "properties": {
            "scenario": {"type": "string", "description": "Scenario ID, display name, or alias"},
            "runs_dir": {"type": "string", "description": "Optional path to H4 runs directory"},
        },
    },
    output_schema={"type": "object", "description": "WhatIfSimulationResult payload with blast radius and CFS"},
    permissions=[RolePermission.VIEWER, RolePermission.OPERATOR, RolePermission.SME_VALIDATOR, RolePermission.ADMIN],
    supports_cli=True,
    supports_ui=True,
    supports_zaki=True,
    supports_demo=True,
    supports_api=True,
    read_only=True,
    handler=predict_handler,
)
