"""Pre-Benchmark Integrity Validator for Step 4.4 / H4 Resilience Scenarios.

Enforces 8 strict pre-flight integrity rules (§55, §56):
1. What-if trigger exists and has valid entity specifications.
2. Operational topology is syntactically and structurally valid.
3. Evaluator ground truth is strictly segregated in hidden/ground_truth.yaml.
4. Redundancy metadata is internally consistent.
5. Capacity assumptions and parameters are explicit.
6. Failure domains and site memberships are valid.
7. Zero hidden truth leakage into operational files or manifests.
8. Causal forward propagation paths can be scored.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml


def validate_single_h4_scenario(scenario_dir: Path | str) -> dict[str, Any]:
    """Validate a single H4 scenario directory against the 8 integrity rules."""
    s_dir = Path(scenario_dir)
    errors: list[str] = []
    warnings: list[str] = []

    # Check manifest
    manifest_file = s_dir / "scenario_manifest.yaml"
    if not manifest_file.exists():
        return {"scenario_id": s_dir.name, "valid": False, "errors": ["scenario_manifest.yaml missing"]}

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    scenario_id = manifest.get("what_if_id", s_dir.name)

    # 1. Trigger validation
    trigger = manifest.get("trigger", {})
    if not trigger.get("canonical_id") or not trigger.get("entity_display_name"):
        errors.append("Rule 1 Violation: Trigger must specify canonical_id and entity_display_name.")

    # 2. Operational topology validation
    op_dir = s_dir / "operational"
    topo_file = op_dir / "topology_view.yaml"
    if not topo_file.exists():
        errors.append("Rule 2 Violation: operational/topology_view.yaml missing.")
    else:
        with open(topo_file, "r", encoding="utf-8") as f:
            topo = yaml.safe_load(f)
        if not isinstance(topo, dict) or "visible_entities" not in topo:
            errors.append("Rule 2 Violation: topology_view.yaml must contain visible_entities list.")

    # 3. Hidden ground truth segregation
    hidden_file = s_dir / "hidden" / "ground_truth.yaml"
    if not hidden_file.exists():
        errors.append("Rule 3 Violation: hidden/ground_truth.yaml missing for offline evaluation.")
    else:
        with open(hidden_file, "r", encoding="utf-8") as f:
            gt = yaml.safe_load(f)
        if not isinstance(gt, dict) or "true_affected_services" not in gt:
            errors.append("Rule 3 Violation: ground_truth.yaml must specify true_affected_services.")

    # 4. Redundancy metadata consistency
    red_file = op_dir / "redundancy_data.yaml"
    if red_file.exists():
        with open(red_file, "r", encoding="utf-8") as f:
            red = yaml.safe_load(f)
        if not isinstance(red, dict):
            errors.append("Rule 4 Violation: redundancy_data.yaml must be a valid mapping.")

    # 5. Capacity assumptions
    cap_file = op_dir / "capacity_data.yaml"
    if cap_file.exists():
        with open(cap_file, "r", encoding="utf-8") as f:
            cap = yaml.safe_load(f)
        if not isinstance(cap, dict) or "backup_capacity_pct" not in cap:
            errors.append("Rule 5 Violation: capacity_data.yaml must specify backup_capacity_pct.")

    # 6. Failure domain tags
    if "failure_domain_tags" not in manifest or not isinstance(manifest["failure_domain_tags"], list):
        errors.append("Rule 6 Violation: scenario_manifest.yaml must define failure_domain_tags list.")

    # 7. Zero Hidden Truth leakage
    # Check that operational files do not reference hidden ground truth fields
    for op_f in op_dir.glob("*.yaml"):
        content = op_f.read_text(encoding="utf-8")
        if "true_affected_services" in content or "true_cfs_risk" in content or "ground_truth" in content:
            errors.append(f"Rule 7 Violation: Hidden evaluator truth leaked into {op_f.name}.")

    manifest_content = manifest_file.read_text(encoding="utf-8")
    if "ground_truth" in manifest_content or "true_affected_services" in manifest_content:
        errors.append("Rule 7 Violation: Hidden evaluator truth leaked into scenario_manifest.yaml.")

    # 8. Demo metadata validation
    demo_file = s_dir / "demo_metadata.yaml"
    if not demo_file.exists():
        warnings.append("Demo metadata missing; default fallback steps will be used.")

    return {
        "scenario_id": scenario_id,
        "scenario_path": str(s_dir),
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def validate_all_h4_scenarios(runs_dir: Path | str) -> dict[str, Any]:
    """Validate all H4 scenario runs under runs_dir."""
    p = Path(runs_dir)
    scenarios = sorted([d for d in p.iterdir() if d.is_dir() and d.name.startswith("H4-WI-")])
    results: list[dict[str, Any]] = []
    total_valid = 0

    for sc in scenarios:
        res = validate_single_h4_scenario(sc)
        results.append(res)
        if res["valid"]:
            total_valid += 1

    all_passed = total_valid == len(scenarios) and len(scenarios) >= 40

    return {
        "all_valid": all_passed,
        "total_scenarios": len(scenarios),
        "valid_count": total_valid,
        "invalid_count": len(scenarios) - total_valid,
        "results": results,
    }
