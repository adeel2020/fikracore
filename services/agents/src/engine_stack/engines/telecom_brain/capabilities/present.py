"""Present Capability for FikraCore (§50, §51, §52, §233).

Produce investigation or curated-demo presentation state consuming shared structured state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

from .registry import CapabilityDefinition, ExecutionContext, RolePermission, CapabilityError
from ..investigation.contracts import (
    GeneratedRunInput,
    StandardPresentationModel,
    WhatIfScenario,
    WhatIfTrigger,
    WhatIfAssumptions,
)
from ..investigation.investigator import Investigator
from ..investigation.knowledge import InMemoryKnowledgeProvider
from ..presentation.naming import default_naming_resolver
from ..presentation.scenario_resolver import get_default_h4_registry, ScenarioResolver
from ..presentation.ui_adapter import build_ui_presentation_model, build_ui_presentation_model_h4
from ..resilience.analyzer import WhatIfAnalyzer


def present_handler(inputs: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
    """Handler building StandardPresentationModel for UI or Curated Demo Mode."""
    scenario_query = inputs.get("scenario") or "H4-WI-001"
    mode = str(inputs.get("mode") or context.mode or "INVESTIGATION").upper()
    step = int(inputs.get("step") or context.current_step or 1)

    resolver = ScenarioResolver(get_default_h4_registry())
    rec, candidates, disambig_msg = resolver.resolve_or_disambiguate(str(scenario_query))

    if not rec:
        if candidates:
            raise CapabilityError("AMBIGUOUS_SCENARIO", disambig_msg or "Ambiguous query", {"candidates": [c.model_dump(mode="json") for c in candidates]})
        raise CapabilityError("SCENARIO_NOT_FOUND", f"Scenario not found for '{scenario_query}'")

    if rec.stage == "H4" or "H4" in rec.id:
        runs_dir = Path(inputs.get("runs_dir") or Path(__file__).parent.parent / "simulator" / "h4_runs")
        sc_dir = runs_dir / rec.id
        if not sc_dir.exists():
            raise CapabilityError("SCENARIO_NOT_FOUND", f"Directory does not exist: {sc_dir}")

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
        sim_res = analyzer.analyze_scenario(scenario_obj, op_topo, red_data, cap_data)
        ui_model = build_ui_presentation_model_h4(sim_res, sc_dir, mode=mode, current_step=step)
        return ui_model.model_dump(mode="json")

    else:
        # H1 or H2 or H3 scenario
        base_dir = Path(__file__).parent.parent / "simulator"
        sc_dir = None
        for cand_dir in [base_dir / "h2_runs" / rec.id, base_dir / "runs" / rec.id, base_dir / "h3_runs" / rec.id]:
            if cand_dir.exists():
                sc_dir = cand_dir
                break

        if not sc_dir:
            raise CapabilityError("SCENARIO_NOT_FOUND", f"Directory not found for {rec.id}")

        op_dir = sc_dir / "operational" if (sc_dir / "operational").exists() else sc_dir
        with open(sc_dir / "scenario_manifest.yaml", "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
        with open(op_dir / "topology_view.yaml", "r", encoding="utf-8") as f:
            op_topo = yaml.safe_load(f)

        provider = InMemoryKnowledgeProvider(
            pages=[{"slug": e, "frontmatter": {}} for e in op_topo.get("visible_entities", [])],
            relationships=[],
            version="present-v1",
        )
        run_input = GeneratedRunInput(
            run_id=manifest.get("run_id", rec.id),
            scenario_id=manifest.get("scenario_id", rec.id),
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
        inv_res = Investigator(provider).run(run_input, op_dir)
        ui_model = build_ui_presentation_model(inv_res, sc_dir, mode=mode, current_step=step)
        return ui_model.model_dump(mode="json")


present_capability = CapabilityDefinition(
    name="present",
    description="Produce investigation or curated-demo presentation state",
    input_schema={
        "type": "object",
        "properties": {
            "scenario": {"type": "string", "description": "Scenario ID, display name, or alias"},
            "mode": {"type": "string", "enum": ["INVESTIGATION", "DEMO"], "default": "INVESTIGATION"},
            "step": {"type": "integer", "default": 1},
        },
    },
    output_schema={"type": "object", "description": "StandardPresentationModel payload"},
    permissions=[RolePermission.VIEWER, RolePermission.OPERATOR, RolePermission.SME_VALIDATOR, RolePermission.ADMIN],
    supports_cli=True,
    supports_ui=True,
    supports_zaki=True,
    supports_demo=True,
    supports_api=True,
    read_only=True,
    handler=present_handler,
)
