from __future__ import annotations

import json
import yaml
from pathlib import Path
from datetime import datetime
import networkx as nx

FORBIDDEN_FIELDS = {
    'hidden', 'hidden_truth', 'ground_truth', 'causal_chain', 
    'root_condition', 'root_entity', 'root_domain', 'expected_root', 
    'evaluator_expectations', 'noise_manifest', 'simulator_world', 
    'actual_blast_radius'
}

OPERATIONAL_JSONL_FILES = [
    'alarms.jsonl', 'logs.jsonl', 'metrics.jsonl', 'kpis.jsonl',
    'traces.jsonl', 'changes.jsonl', 'tickets.jsonl', 'recovery.jsonl'
]

def _parse_iso(ts: str) -> datetime:
    if ts.endswith('Z'):
        ts = ts[:-1] + '+00:00'
    return datetime.fromisoformat(ts)

def _get_all_keys(data) -> set:
    keys = set()
    if isinstance(data, dict):
        for k, v in data.items():
            keys.add(k)
            keys.update(_get_all_keys(v))
    elif isinstance(data, list):
        for item in data:
            keys.update(_get_all_keys(item))
    return keys

def validate_run(run_dir: Path) -> dict:
    """Validate a single run directory."""
    result = {
        "run_id": run_dir.name,
        "passed": True,
        "checks": {
            "manifest_structure": {"passed": True, "failures": []},
            "operational_files_exist": {"passed": True, "failures": []},
            "hidden_files_exist": {"passed": True, "failures": []},
            "evidence_parsable": {"passed": True, "failures": []},
            "no_truth_leakage": {"passed": True, "failures": []},
            "timestamp_consistency": {"passed": True, "failures": []},
            "entity_coverage": {"passed": True, "failures": []},
            "cross_file_consistency": {"passed": True, "failures": []},
            "causal_graph_acyclicity": {"passed": True, "failures": []},
            "difficulty_profile_valid": {"passed": True, "failures": []},
        },
        "scenario_id": None,
        "seed": None
    }
    
    # 1. manifest_structure & 10. difficulty_profile_valid
    manifest_path = run_dir / "scenario_manifest.yaml"
    manifest_data = {}
    if not manifest_path.exists():
        result["checks"]["manifest_structure"]["passed"] = False
        result["checks"]["manifest_structure"]["failures"].append("Missing scenario_manifest.yaml")
        result["passed"] = False
    else:
        try:
            with open(manifest_path, "r") as f:
                manifest_data = yaml.safe_load(f)
            
            result["scenario_id"] = manifest_data.get("scenario_id")
            result["seed"] = manifest_data.get("random_seed")
            
            diff_level = manifest_data.get("difficulty_profile", {}).get("level")
            if diff_level not in ["L1", "L2", "L3", "L4", "L5"]:
                result["checks"]["manifest_structure"]["passed"] = False
                result["checks"]["manifest_structure"]["failures"].append(f"Invalid difficulty level: {diff_level}")
                result["checks"]["difficulty_profile_valid"]["passed"] = False
                result["checks"]["difficulty_profile_valid"]["failures"].append(f"Invalid difficulty level: {diff_level}")
                result["passed"] = False
                
            if manifest_data.get("compile_status") != "VALID":
                result["checks"]["manifest_structure"]["passed"] = False
                result["checks"]["manifest_structure"]["failures"].append("compile_status not VALID")
                result["passed"] = False
        except Exception as e:
            result["checks"]["manifest_structure"]["passed"] = False
            result["checks"]["manifest_structure"]["failures"].append(f"Error parsing manifest: {e}")
            result["passed"] = False

    # 2. operational_files_exist
    op_dir = run_dir / "operational"
    if not op_dir.exists():
        result["checks"]["operational_files_exist"]["passed"] = False
        result["checks"]["operational_files_exist"]["failures"].append("Missing operational directory")
        result["passed"] = False
    else:
        for fname in OPERATIONAL_JSONL_FILES + ["topology_view.yaml"]:
            if not (op_dir / fname).exists():
                result["checks"]["operational_files_exist"]["passed"] = False
                result["checks"]["operational_files_exist"]["failures"].append(f"Missing {fname}")
                result["passed"] = False

    # 3. hidden_files_exist
    hidden_dir = run_dir / "hidden"
    hidden_files = ["ground_truth.yaml", "causal_graph.yaml", "noise_manifest.yaml", "evaluator_expectations.yaml"]
    if not hidden_dir.exists():
        result["checks"]["hidden_files_exist"]["passed"] = False
        result["checks"]["hidden_files_exist"]["failures"].append("Missing hidden directory")
        result["passed"] = False
    else:
        for fname in hidden_files:
            if not (hidden_dir / fname).exists():
                result["checks"]["hidden_files_exist"]["passed"] = False
                result["checks"]["hidden_files_exist"]["failures"].append(f"Missing {fname}")
                result["passed"] = False

    evidence_entities = set()
    
    # 4, 5, 6. Parse evidence files
    if result["checks"]["operational_files_exist"]["passed"]:
        for fname in OPERATIONAL_JSONL_FILES:
            fpath = op_dir / fname
            if not fpath.exists():
                continue
            with open(fpath, "r") as f:
                for idx, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        
                        ent = record.get("entity_id") or record.get("entity") or record.get("changed_entity") or record.get("canonical_entity_id")
                        if not all(k in record for k in ("event_id", "event_time", "ingestion_time")) or not ent:
                            result["checks"]["evidence_parsable"]["passed"] = False
                            result["checks"]["evidence_parsable"]["failures"].append(f"{fname} line {idx+1} missing required keys")
                            result["passed"] = False
                        else:
                            evidence_entities.add(ent)
                        
                        # Check timestamp consistency
                        if "event_time" in record and "ingestion_time" in record:
                            try:
                                etime = _parse_iso(record["event_time"])
                                itime = _parse_iso(record["ingestion_time"])
                                if etime > itime:
                                    result["checks"]["timestamp_consistency"]["passed"] = False
                                    result["checks"]["timestamp_consistency"]["failures"].append(f"{fname} line {idx+1} event_time > ingestion_time")
                                    result["passed"] = False
                            except ValueError:
                                result["checks"]["timestamp_consistency"]["passed"] = False
                                result["checks"]["timestamp_consistency"]["failures"].append(f"{fname} line {idx+1} invalid timestamp format")
                                result["passed"] = False

                        # Check truth leakage
                        record_keys = _get_all_keys(record)
                        leakage = record_keys.intersection(FORBIDDEN_FIELDS)
                        if leakage:
                            result["checks"]["no_truth_leakage"]["passed"] = False
                            result["checks"]["no_truth_leakage"]["failures"].append(f"{fname} line {idx+1} contains forbidden fields: {leakage}")
                            result["passed"] = False

                    except json.JSONDecodeError:
                        result["checks"]["evidence_parsable"]["passed"] = False
                        result["checks"]["evidence_parsable"]["failures"].append(f"{fname} line {idx+1} invalid JSON")
                        result["passed"] = False
                        
    # Load hidden files for remaining checks
    hidden_data = {}
    if result["checks"]["hidden_files_exist"]["passed"]:
        for fname in hidden_files:
            try:
                with open(hidden_dir / fname, "r") as f:
                    hidden_data[fname] = yaml.safe_load(f)
            except Exception as e:
                pass
                
    # 7. entity_coverage & 9. causal_graph_acyclicity
    cg_data = hidden_data.get("causal_graph.yaml")
    if cg_data and "nodes" in cg_data:
        graph_entities = {n.get("entity_id") for n in cg_data["nodes"] if "entity_id" in n}
        missing_entities = graph_entities - evidence_entities
        if missing_entities:
            result["checks"]["entity_coverage"]["passed"] = False
            result["checks"]["entity_coverage"]["failures"].append(f"Entities in causal graph missing from evidence: {missing_entities}")
            result["passed"] = False
            
        if "edges" in cg_data:
            G = nx.DiGraph()
            for edge in cg_data["edges"]:
                if "source_entity" in edge and "target_entity" in edge:
                    G.add_edge(edge["source_entity"], edge["target_entity"])
            if not nx.is_directed_acyclic_graph(G):
                result["checks"]["causal_graph_acyclicity"]["passed"] = False
                result["checks"]["causal_graph_acyclicity"]["failures"].append("Causal graph is not a DAG")
                result["passed"] = False

    # 8. cross_file_consistency
    gt_data = hidden_data.get("ground_truth.yaml")
    ee_data = hidden_data.get("evaluator_expectations.yaml")
    
    if manifest_data and gt_data and ee_data:
        m_scen = manifest_data.get("scenario_id")
        gt_scen = gt_data.get("scenario_id")
        ee_scen = ee_data.get("scenario_id")
        if not (m_scen == gt_scen == ee_scen):
            result["checks"]["cross_file_consistency"]["passed"] = False
            result["checks"]["cross_file_consistency"]["failures"].append("scenario_id mismatch across manifest, ground_truth, evaluator_expectations")
            result["passed"] = False
            
        gt_root = gt_data.get("hidden_truth", {}).get("root_entity")
        ee_root = ee_data.get("expected_root_entity")
        if gt_root != ee_root:
            result["checks"]["cross_file_consistency"]["passed"] = False
            result["checks"]["cross_file_consistency"]["failures"].append(f"root_entity mismatch: ground_truth={gt_root}, expected={ee_root}")
            result["passed"] = False

    return result

def validate_all(runs_dir: Path) -> dict:
    """Validate all runs in a directory."""
    runs = [d for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith("RUN-")]
    
    report = {
        "total_runs": len(runs),
        "passed": 0,
        "failed": 0,
        "checks": {
            "manifest_structure": {"passed": 0, "failed": 0, "failures": []},
            "operational_files_exist": {"passed": 0, "failed": 0, "failures": []},
            "hidden_files_exist": {"passed": 0, "failed": 0, "failures": []},
            "evidence_parsable": {"passed": 0, "failed": 0, "failures": []},
            "no_truth_leakage": {"passed": 0, "failed": 0, "failures": []},
            "timestamp_consistency": {"passed": 0, "failed": 0, "failures": []},
            "entity_coverage": {"passed": 0, "failed": 0, "failures": []},
            "cross_file_consistency": {"passed": 0, "failed": 0, "failures": []},
            "causal_graph_acyclicity": {"passed": 0, "failed": 0, "failures": []},
            "difficulty_profile_valid": {"passed": 0, "failed": 0, "failures": []},
        },
        "seed_uniqueness": {"passed": True, "duplicates": []},
        "per_run": []
    }
    
    seen_seeds = {}
    
    for run_dir in runs:
        run_res = validate_run(run_dir)
        report["per_run"].append({
            "run_id": run_res["run_id"],
            "passed": run_res["passed"],
            "failures": [f for check in run_res["checks"].values() for f in check["failures"]]
        })
        
        if run_res["passed"]:
            report["passed"] += 1
        else:
            report["failed"] += 1
            
        for check_name, check_data in run_res["checks"].items():
            if check_data["passed"]:
                report["checks"][check_name]["passed"] += 1
            else:
                report["checks"][check_name]["failed"] += 1
                report["checks"][check_name]["failures"].extend([f"[{run_res['run_id']}] {f}" for f in check_data["failures"]])
                
        scenario_id = run_res.get("scenario_id")
        seed = run_res.get("seed")
        if scenario_id and seed is not None:
            key = (scenario_id, seed)
            if key in seen_seeds:
                report["seed_uniqueness"]["passed"] = False
                report["seed_uniqueness"]["duplicates"].append(f"{key} seen in {seen_seeds[key]} and {run_res['run_id']}")
            else:
                seen_seeds[key] = run_res["run_id"]
                
    return report
