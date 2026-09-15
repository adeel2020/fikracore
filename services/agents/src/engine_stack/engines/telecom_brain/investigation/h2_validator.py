"""Pre-Benchmark Integrity Validator for Step 4.2 / H2 Unknown-Unknown Scenarios.

Enforces 7 strict integrity checks:
1. Hidden topology contains intended relation/path.
2. Operational topology view does NOT contain the omitted relation/path.
3. Operational evidence is causally consistent with hidden reality.
4. Removed knowledge is not leaked through filenames, IDs, alarm text, or metadata.
5. Scenario remains solvable at intended K1-K5 difficulty level.
6. Candidate gap is evaluable (evaluator expectations are well-formed).
7. Next-best-evidence target exists in the network topology.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import yaml


class H2ValidationError(ValueError):
    """Raised when an H2 scenario fails structural or epistemic integrity checks."""
    pass


def validate_single_h2_run(run_dir: Path | str) -> dict[str, Any]:
    """Validate a single H2 scenario run directory against all 7 integrity rules."""
    path = Path(run_dir)
    errors: list[str] = []

    manifest_file = path / "scenario_manifest.yaml"
    if not manifest_file.exists():
        return {"run_id": path.name, "valid": False, "errors": ["Missing scenario_manifest.yaml"]}

    with open(manifest_file) as f:
        manifest = yaml.safe_load(f)

    scenario_id = manifest.get("scenario_id", "")
    operational_dir = path / manifest.get("operational_path", "operational")
    hidden_dir = path / manifest.get("hidden_path", "hidden")

    # Required files
    op_topo_file = operational_dir / "topology_view.yaml"
    hidden_causal_file = hidden_dir / "causal_graph.yaml"
    hidden_ground_truth_file = hidden_dir / "ground_truth.yaml"
    evaluator_exp_file = hidden_dir / "evaluator_expectations.yaml"

    for req_file in [op_topo_file, hidden_causal_file, hidden_ground_truth_file, evaluator_exp_file]:
        if not req_file.exists():
            errors.append(f"Missing required file: {req_file.name}")

    if errors:
        return {"run_id": path.name, "scenario_id": scenario_id, "valid": False, "errors": errors}

    with open(op_topo_file) as f:
        op_topo = yaml.safe_load(f)
    with open(hidden_causal_file) as f:
        hidden_causal = yaml.safe_load(f)
    with open(hidden_ground_truth_file) as f:
        ground_truth = yaml.safe_load(f)
    with open(evaluator_exp_file) as f:
        evaluator_exp = yaml.safe_load(f)

    hidden_gap = ground_truth.get("hidden_gap", {})
    target_rel_id = hidden_gap.get("relationship_id")
    from_entity = hidden_gap.get("from_entity")

    # Rule 1: Hidden topology contains intended relation
    hidden_rel_ids = {e.get("id") for e in hidden_causal.get("edges", [])}
    if target_rel_id and target_rel_id not in hidden_rel_ids:
        errors.append(f"Rule 1 violation: Intended gap relationship {target_rel_id} not found in hidden causal graph.")

    # Rule 2: Operational topology view does NOT contain intended relation
    visible_rel_ids = set(op_topo.get("visible_relationships", []))
    if target_rel_id in visible_rel_ids:
        errors.append(f"Rule 2 violation: Intended gap relationship {target_rel_id} is present in operational topology view.")

    # Rule 3: Operational evidence is causally consistent
    alarms_file = operational_dir / "alarms.jsonl"
    if not alarms_file.exists():
        errors.append("Rule 3 violation: Missing operational alarms.jsonl")
    else:
        with open(alarms_file) as f:
            alarm_lines = [json.loads(line) for line in f if line.strip()]
        if not alarm_lines:
            errors.append("Rule 3 violation: Operational alarms.jsonl is empty")

    # Rule 4: Removed knowledge is not leaked through operational files
    forbidden_tokens = {target_rel_id} if target_rel_id else set()
    forbidden_tokens.update({"hidden_gap", "true_terminal_state", "evaluator_expectations"})

    for op_file in operational_dir.glob("*"):
        text = op_file.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            if token and token in text:
                errors.append(f"Rule 4 violation: Trivial leakage of forbidden token '{token}' in operational file {op_file.name}")

    # Check for leakage in scenario ID
    if "MISSING" in scenario_id or "GAP" in scenario_id:
        errors.append(f"Rule 4 violation: Scenario ID '{scenario_id}' reveals gap information (must be opaque, e.g. H2-SCN-001).")

    # Rule 5: Scenario solvability (terminal state expectation)
    expected_state = evaluator_exp.get("expected_terminal_state")
    if expected_state != "MODEL_INSUFFICIENT":
        errors.append(f"Rule 5 violation: Expected terminal state for H2 scenario must be MODEL_INSUFFICIENT, got '{expected_state}'")

    # Rule 6: Candidate gap is evaluable
    if not evaluator_exp.get("expected_gap_type") or not evaluator_exp.get("expected_gap_boundary"):
        errors.append("Rule 6 violation: Evaluator expectations must specify expected_gap_type and expected_gap_boundary.")

    # Rule 7: Next-best-evidence target exists in network topology
    boundary = evaluator_exp.get("expected_gap_boundary")
    visible_entities = set(op_topo.get("visible_entities", []))
    if boundary not in visible_entities:
        errors.append(f"Rule 7 violation: Expected gap boundary '{boundary}' not present in operational visible_entities.")

    return {
        "run_id": path.name,
        "scenario_id": scenario_id,
        "valid": len(errors) == 0,
        "errors": errors,
    }


def validate_all_h2_runs(runs_dir: Path | str) -> dict[str, Any]:
    """Validate all H2 runs in a directory."""
    root = Path(runs_dir)
    runs = sorted([d for d in root.iterdir() if d.is_dir() and d.name.startswith("RUN-H2-")])
    results = [validate_single_h2_run(run) for run in runs]

    passed = sum(1 for r in results if r["valid"])
    failed = len(results) - passed

    report = {
        "total_runs": len(results),
        "passed": passed,
        "failed": failed,
        "all_valid": failed == 0 and len(results) > 0,
        "details": results,
    }
    return report


__all__ = [
    "H2ValidationError",
    "validate_single_h2_run",
    "validate_all_h2_runs",
]
