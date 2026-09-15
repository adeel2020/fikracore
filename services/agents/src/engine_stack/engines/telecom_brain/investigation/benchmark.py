import json
import traceback
import yaml
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, Optional, List

from engine_stack.engines.telecom_brain.investigation import Investigator
from engine_stack.engines.telecom_brain.investigation.evidence import input_from_run, load_evidence
from engine_stack.engines.telecom_brain.investigation.evaluator import compare
from engine_stack.engines.telecom_brain.investigation.knowledge import InMemoryKnowledgeProvider

REF_NET_PATH = Path(__file__).resolve().parent.parent / "simulator" / "operator_model" / "reference_synthetic_network.yaml"
_REF_RELS: Optional[Dict[str, Any]] = None

def get_ref_relationships() -> Dict[str, Any]:
    global _REF_RELS
    if _REF_RELS is None:
        if REF_NET_PATH.exists():
            with open(REF_NET_PATH, "r") as f:
                net = yaml.safe_load(f)
            _REF_RELS = {r["relationship_id"]: r for r in net.get("relationships", [])}
        else:
            _REF_RELS = {}
    return _REF_RELS

def benchmark_run(run_dir: Path) -> Dict[str, Any]:
    """Run investigation + evaluation on a single run."""
    run_id = run_dir.name
    
    with open(run_dir / "scenario_manifest.yaml", "r") as f:
        manifest = yaml.safe_load(f)
    scenario_id = manifest.get("scenario_id", "unknown")
    difficulty = manifest.get("difficulty_profile", {}).get("level", "L0")
    
    with open(run_dir / "operational" / "topology_view.yaml", "r") as f:
        topology_view = yaml.safe_load(f)
        
    with open(run_dir / "hidden" / "causal_graph.yaml", "r") as f:
        causal_graph = yaml.safe_load(f)
        
    with open(run_dir / "hidden" / "evaluator_expectations.yaml", "r") as f:
        expectations = yaml.safe_load(f)
        
    visible_entities = topology_view.get("visible_entities", [])
    visible_rel_ids = set(topology_view.get("visible_relationships", []))
    
    ref_rels = get_ref_relationships()
    pages = [{"slug": entity_id} for entity_id in visible_entities]
    relationships = []
    for rid in visible_rel_ids:
        if rid in ref_rels:
            r = ref_rels[rid]
            relationships.append({
                "relationship_id": rid,
                "source": r["source_entity"],
                "target": r["target_entity"],
                "link_type": r.get("relationship_type", "depends-on").lower().replace("_", "-"),
                "state": r.get("status", "CONFIRMED"),
                "confidence": r.get("confidence", 0.95),
                "provenance": "benchmark-operational-fixture"
            })
        else:
            for edge in causal_graph.get("edges", []):
                if edge.get("relationship_id") == rid:
                    relationships.append({
                        "relationship_id": edge["relationship_id"],
                        "source": edge["source_entity"],
                        "target": edge["target_entity"],
                        "link_type": "depends-on",
                        "state": "CONFIRMED",
                        "confidence": 0.95,
                        "provenance": "benchmark-operational-fixture"
                    })
            
    provider = InMemoryKnowledgeProvider(pages, relationships, version=f"{run_id}-operational-v1")
    
    run_input = input_from_run(run_dir)
    evidence, hashes = load_evidence(run_input, run_dir / "operational")
    
    investigator = Investigator(provider)
    if hasattr(investigator, "investigate"):
        result = investigator.investigate(run_input, evidence, hashes)
    else:
        result = investigator.run(run_input, run_dir / "operational")
    
    expected_root = expectations.get("expected_root_entity")
    expected_terminal_state = expectations.get("expected_terminal_state")
    unknown_correct = (expected_terminal_state != "EXPLAINED")
    expected_roots = [expected_root] if expected_root else []
    
    comp = compare(result, expected_roots, unknown_correct)
    
    return {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "difficulty": difficulty,
        "unknown_correct": unknown_correct,
        "result": result.model_dump(mode="json"),
        "comparison": comp
    }

def benchmark_all(
    runs_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    max_runs: Optional[int] = None,
    split: Optional[str] = None,
    split_file: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run benchmark on all (or first max_runs) runs. Returns aggregate report."""
    if output_dir is None:
        output_dir = Path("artifacts/hypothesis/calibration/before")
    output_dir.mkdir(parents=True, exist_ok=True)
    per_run_dir = output_dir / "per-run"
    per_run_dir.mkdir(parents=True, exist_ok=True)
    
    if runs_dir is None:
        runs_dir = Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/runs")
    elif isinstance(runs_dir, (str, Path)) and not Path(runs_dir).exists():
        r_path = Path(runs_dir)
        base_dir = Path(__file__).parent.parent
        for cand in [
            base_dir / "simulator" / "runs" / r_path.name,
            base_dir / "simulator" / "scenarios" / r_path.name,
            base_dir / "simulator" / "h2_runs" / r_path.name,
            base_dir / "simulator" / "h3_runs" / r_path.name,
            base_dir / "simulator" / "h4_runs" / r_path.name,
            Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/runs") / r_path.name,
            Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/scenarios") / r_path.name,
            Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h2_runs") / r_path.name,
            Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/h4_runs") / r_path.name,
        ]:
            if cand.exists():
                runs_dir = cand
                break

    runs_dir = Path(runs_dir) if runs_dir else Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/runs")

    if runs_dir.exists():
        if (runs_dir / "scenario_manifest.yaml").exists() or (runs_dir / "operational").exists() or (runs_dir / "alarms.jsonl").exists():
            runs = [runs_dir]
        else:
            runs = sorted([
                d for d in runs_dir.iterdir()
                if d.is_dir() and (d.name.startswith("RUN-") or d.name.startswith("SCN-") or d.name.startswith("H4-") or (d / "scenario_manifest.yaml").exists())
            ])
    else:
        runs = []
    
    if split:
        s_file = split_file or Path("artifacts/hypothesis/calibration/splits.json")
        if s_file.exists():
            with open(s_file, "r") as f:
                splits_data = json.load(f)
            allowed_ids = set(splits_data.get(split, []))
            runs = [d for d in runs if d.name in allowed_ids]
            print(f"Filtered to {len(runs)} runs for split: {split}")
        else:
            print(f"Warning: split file {s_file} not found; running without split filter.")
            
    if max_runs is not None:
        runs = runs[:max_runs]
        
    per_run_results = []
    
    for run_dir in runs:
        try:
            res = benchmark_run(run_dir)
            with open(per_run_dir / f"{res['run_id']}.json", "w") as f:
                json.dump(res["result"], f, indent=2)
            per_run_results.append(res)
        except Exception as e:
            print(f"Error processing {run_dir.name}: {e}")
            traceback.print_exc()
            
    # Compute aggregate metrics
    total_runs = len(per_run_results)
    if total_runs == 0:
        return {"error": "No runs completed successfully"}
        
    non_unknown_runs = 0
    total_accuracy = 0.0
    wrong_hypotheses_falsified = 0
    total_evidence_requests = 0
    total_steps_to_useful = 0
    runs_with_useful = 0
    
    unknown_correct_cases = 0
    forced_rca_cases = 0
    
    total_provenance_quality = 0.0
    
    method_a_correct = 0
    method_b_correct = 0
    
    terminal_state_dist = defaultdict(int)
    per_difficulty = defaultdict(lambda: {"count": 0, "method_b_correct": 0, "method_a_correct": 0, "avg_coverage": 0.0})
    
    for res in per_run_results:
        comp = res["comparison"]
        diff = res["difficulty"]
        unknown_correct = res.get("unknown_correct", False)
        
        terminal_state = res["result"].get("terminal_state", "UNKNOWN")
        terminal_state_dist[terminal_state] += 1
        
        per_difficulty[diff]["count"] += 1
        
        is_b_correct = comp.get("method_b_correct", False)
        if is_b_correct:
            method_b_correct += 1
            per_difficulty[diff]["method_b_correct"] += 1
            
        is_a_correct = comp.get("baseline_correct", False)
        if is_a_correct:
            method_a_correct += 1
            per_difficulty[diff]["method_a_correct"] += 1
            
        per_difficulty[diff]["avg_coverage"] += comp.get("explanation_coverage", 0.0)
        
        top_3 = comp.get("root_cause_top_3_accuracy")
        if top_3 is not None:
            non_unknown_runs += 1
            total_accuracy += float(top_3)
            
        if unknown_correct:
            unknown_correct_cases += 1
            if comp.get("forced_rca_when_unknown_correct", 0) > 0:
                forced_rca_cases += 1
                
        wrong_hypotheses_falsified += comp.get("wrong_hypotheses_correctly_falsified", 0)
        total_evidence_requests += comp.get("evidence_requests_before_terminal_decision", 0)
        
        steps_useful = comp.get("steps_to_first_useful_hypothesis")
        if steps_useful is not None:
            total_steps_to_useful += steps_useful
            runs_with_useful += 1
            
        total_provenance_quality += comp.get("explanation_provenance_quality", 0.0)

    for d in per_difficulty.values():
        if d["count"] > 0:
            d["avg_coverage"] /= d["count"]

    metrics = {
        "root_cause_top_3_accuracy": total_accuracy / non_unknown_runs if non_unknown_runs > 0 else 0.0,
        "wrong_hypotheses_correctly_falsified": wrong_hypotheses_falsified,
        "avg_evidence_requests_before_terminal": total_evidence_requests / total_runs if total_runs > 0 else 0.0,
        "avg_steps_to_first_useful_hypothesis": total_steps_to_useful / runs_with_useful if runs_with_useful > 0 else None,
        "forced_rca_rate": forced_rca_cases / unknown_correct_cases if unknown_correct_cases > 0 else 0.0,
        "avg_explanation_provenance_quality": total_provenance_quality / total_runs if total_runs > 0 else 0.0,
    }

    report = {
        "scope": "Full 100-scenario benchmark" if total_runs >= 100 else f"Partial benchmark ({total_runs} runs)",
        "total_runs": total_runs,
        "metrics": metrics,
        "baseline_comparison": {
            "method_a_name": "earliest severe alarm",
            "method_b_name": "hypothesis reasoning",
            "method_a_correct": method_a_correct,
            "method_b_correct": method_b_correct,
        },
        "terminal_state_distribution": dict(terminal_state_dist),
        "per_difficulty": dict(per_difficulty),
        "per_run": [{"run_id": r["run_id"], "scenario_id": r["scenario_id"], "difficulty": r["difficulty"], **r["comparison"]} for r in per_run_results],
        "caveat": "Synthetic benchmark using in-memory operational fixtures; not a production accuracy claim."
    }
    
    with open(output_dir / "aggregate-report.json", "w") as f:
        json.dump(report, f, indent=2)
        
    return report
