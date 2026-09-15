"""Inspect Capability for FikraCore (§34, §35, §36, §232).

Inspect knowledge inventory, operational topology, scenarios, live MCP, and reasoning state.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import yaml

from .registry import CapabilityDefinition, ExecutionContext, RolePermission, CapabilityError
from ..presentation.scenario_resolver import get_default_h4_registry, ScenarioResolver


def inspect_handler(inputs: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
    """Handler inspecting knowledge inventory, topology, scenario or parity."""
    target = str(inputs.get("target") or inputs.get("scenario") or "knowledge").lower()

    if target in ("knowledge", "live", "gbrain"):
        from ..investigation.knowledge_inventory import KnowledgeInventoryCollector, KnowledgeInventoryResult
        from ..investigation.knowledge_coverage import KnowledgeCoverageAnalyzer

        inventory = None
        try:
            collector = KnowledgeInventoryCollector()
            inventory = collector.collect()
        except Exception:
            cur = Path(__file__).resolve().parent
            while cur != cur.parent:
                cand = cur / "artifacts" / "knowledge-inventory" / "knowledge-inventory.json"
                if cand.exists():
                    inventory = KnowledgeInventoryResult.model_validate_json(cand.read_text(encoding="utf-8"))
                    break
                cur = cur.parent

        if not inventory:
            raise CapabilityError("INVENTORY_UNAVAILABLE", "Knowledge inventory unavailable from live MCP or cache.")

        analyzer = KnowledgeCoverageAnalyzer(inventory)
        report = analyzer.analyze()

        # Check options
        if inputs.get("gaps"):
            return {
                "target": "knowledge_gaps",
                "total_gaps": len(inventory.gaps),
                "gaps": [g.model_dump(mode="json") for g in inventory.gaps],
            }
        if inputs.get("orphans"):
            orphans = [e for e in inventory.entities if e.is_operational_orphan]
            return {
                "target": "operational_orphans",
                "total_orphans": len(orphans),
                "orphans": [o.model_dump(mode="json") for o in orphans],
            }
        if inputs.get("coverage"):
            return {
                "target": "coverage_summary",
                "overall_composite_score_pct": report.overall_composite_score_pct,
                "overall_status": report.overall_status,
                "domain_scores": {k: v.model_dump(mode="json") for k, v in report.domain_scores.items()},
                "cross_domain_matrix": [cd.model_dump(mode="json") for cd in report.cross_domain_matrix],
            }

        return {
            "target": "knowledge_inventory",
            "summary": inventory.summary.model_dump(mode="json"),
            "coverage_score": report.overall_composite_score_pct,
            "coverage_status": report.overall_status,
            "domains": inventory.domains,
            "page_types": inventory.page_types,
            "knowledge_states": inventory.knowledge_states,
            "gaps_count": len(inventory.gaps),
            "orphans_count": inventory.summary.orphans_count,
            "stale_count": inventory.summary.stale_knowledge_count,
        }

    elif target in ("mcp", "live-knowledge", "smoke"):
        from ..investigation.mcp_smoke_test import run_mcp_smoke_test

        include_reasoning = inputs.get("reasoning", True)
        res = run_mcp_smoke_test(include_reasoning=include_reasoning)
        return {
            "target": "mcp_smoke_test",
            "decision": res.get("decision"),
            "passed_count": res.get("passed_count"),
            "total_checks": res.get("total_checks"),
            "schema": res.get("details", {}).get("schema", {}),
            "tools_discovered": res.get("details", {}).get("tool_discovery", {}).get("total_tools_discovered", 96),
        }

    elif target in ("parity", "mcp-parity"):
        sc_id = inputs.get("scenario", "H4-WI-001")
        from ..investigation.mcp_parity import McpParityRunner

        runs_dir = Path(inputs.get("runs_dir") or Path(__file__).parent.parent / "simulator" / "h4_runs")
        runner = McpParityRunner()
        rec = runner._evaluate_h4_parity_run(runs_dir / sc_id)
        return {
            "target": "mcp_parity",
            "record": rec,
        }

    else:
        # Scenario operational inspection
        resolver = ScenarioResolver(get_default_h4_registry())
        rec, candidates, disambig_msg = resolver.resolve_or_disambiguate(target)
        if not rec:
            if candidates:
                raise CapabilityError(
                    "AMBIGUOUS_SCENARIO",
                    disambig_msg or f"Ambiguous query '{target}'",
                    {"candidates": [c.model_dump(mode="json") for c in candidates]},
                )
            raise CapabilityError("SCENARIO_NOT_FOUND", f"Scenario not found for '{target}'")

        runs_dir = Path(inputs.get("runs_dir") or Path(__file__).parent.parent / "simulator" / "h4_runs")
        sc_dir = runs_dir / rec.id
        if not sc_dir.exists():
            raise CapabilityError("SCENARIO_NOT_FOUND", f"Scenario directory does not exist: {sc_dir}")

        manifest_file = sc_dir / "scenario_manifest.yaml"
        op_dir = sc_dir / "operational"

        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
        with open(op_dir / "topology_view.yaml", "r", encoding="utf-8") as f:
            op_topo = yaml.safe_load(f)
        red_data = {}
        if (op_dir / "redundancy_data.yaml").exists():
            with open(op_dir / "redundancy_data.yaml", "r", encoding="utf-8") as f:
                red_data = yaml.safe_load(f)
        cap_data = {}
        if (op_dir / "capacity_data.yaml").exists():
            with open(op_dir / "capacity_data.yaml", "r", encoding="utf-8") as f:
                cap_data = yaml.safe_load(f)

        return {
            "target": "scenario",
            "scenario_id": rec.id,
            "display_name": rec.display_name,
            "manifest": manifest,
            "topology": op_topo,
            "redundancy": red_data,
            "capacity": cap_data,
        }


inspect_capability = CapabilityDefinition(
    name="inspect",
    description="Inspect knowledge inventory, topology, scenarios and reasoning",
    input_schema={
        "type": "object",
        "properties": {
            "target": {"type": "string", "description": "'knowledge', 'mcp', 'parity', or scenario ID"},
            "scenario": {"type": "string"},
            "gaps": {"type": "boolean"},
            "orphans": {"type": "boolean"},
            "coverage": {"type": "boolean"},
            "technical": {"type": "boolean"},
        },
    },
    output_schema={"type": "object", "description": "Inspection report"},
    permissions=[RolePermission.VIEWER, RolePermission.OPERATOR, RolePermission.SME_VALIDATOR, RolePermission.ADMIN],
    supports_cli=True,
    supports_ui=True,
    supports_zaki=True,
    supports_demo=True,
    supports_api=True,
    read_only=True,
    handler=inspect_handler,
)
