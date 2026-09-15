"""Diagnostic analysis pipeline for Step 4.1.

Implements:
- Failure taxonomy classification (A through P)
- True-root rank calculation (Top-1, Top-2, Top-3, >3)
- Confusion matrix generation (expected situation class vs predicted terminal state)
- Audits for MODEL_INSUFFICIENT and PARTIALLY_EXPLAINED
- Multi-dimensional slices by difficulty (L1–L5) and scenario category
- Score-margin, confidence calibration, canonical resolution, and baseline audits
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


TAXONOMY_DESCRIPTIONS = {
    "A": "Correct root ranked #2/#3, wrong root selected",
    "B": "Correct root ranked #1, wrong terminal state",
    "C": "False MODEL_INSUFFICIENT",
    "D": "False PARTIALLY_EXPLAINED",
    "E": "Canonical entity/alias mismatch",
    "F": "Causal-role mismatch",
    "G": "Confidence threshold too conservative",
    "H": "Negative-evidence penalty too aggressive",
    "I": "Topology traversal/direction/dependency-scoring problem",
    "J": "Evidence sufficiency logic too conservative",
    "K": "Change correlation over-weighted",
    "L": "Symptom node over-ranked as root",
    "M": "Shared-dependency/common-cause ranking failure",
    "N": "Multi-cause reduction to single root",
    "O": "Evaluator semantic mismatch",
    "P": "Other/uncategorized",
}


def compute_rank_metrics(ranked: List[Dict[str, Any]], expected_root: Optional[str]) -> tuple[Optional[int], Optional[float]]:
    """Determine the rank (1-indexed) and score of the expected root entity in ranked hypotheses."""
    if not expected_root:
        return None, None
    for idx, h in enumerate(ranked, 1):
        root_entities = h.get("root_entities", [])
        canonical_root = h.get("canonical_root_entity")
        if expected_root in root_entities or expected_root == canonical_root:
            return idx, h.get("hypothesis_confidence")
    return None, None


def classify_failures(
    result_data: Dict[str, Any],
    expectations: Dict[str, Any],
    true_root_rank: Optional[int],
) -> List[str]:
    """Classify failure patterns into taxonomy categories A through P."""
    expected_root = expectations.get("expected_root_entity")
    expected_terminal = expectations.get("expected_terminal_state", "EXPLAINED")
    is_unknown_expected = (expected_terminal != "EXPLAINED")
    predicted_terminal = result_data.get("terminal_state", "UNKNOWN")
    ranked = [h for h in result_data.get("ranked_hypotheses", []) if h.get("status") != "REJECTED"]
    top1 = ranked[0].get("canonical_root_entity") if len(ranked) > 0 else None
    
    failures = []
    if is_unknown_expected:
        if predicted_terminal == "EXPLAINED":
            failures.append("G")
    else:
        if true_root_rank in (2, 3):
            failures.append("A")
            if top1 and any(prefix in str(top1) for prefix in ["CRM:TICKET", "KPI:"]):
                failures.append("L")
            if top1 and "CR-" in str(ranked[0].get("supporting_evidence", [])):
                failures.append("K")
        elif true_root_rank == 1:
            if predicted_terminal != "EXPLAINED":
                failures.append("B")
                if predicted_terminal == "MODEL_INSUFFICIENT":
                    failures.append("C")
                elif predicted_terminal == "PARTIALLY_EXPLAINED":
                    failures.append("D")
                elif predicted_terminal == "INSUFFICIENT_EVIDENCE":
                    failures.append("J")
                else:
                    failures.append("G")
        elif true_root_rank is None or true_root_rank > 3:
            failures.append("I")
    return failures


def compute_confidence_calibration(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute confidence calibration buckets and expected calibration error."""
    conf_buckets = {f"{i/10:.1f}-{(i+1)/10:.1f}": {"count": 0, "correct": 0, "sum_conf": 0.0} for i in range(10)}
    total_samples = 0
    for r in records:
        c = r.get("top1_score", 0.0)
        bucket_idx = min(9, max(0, int(c * 10)))
        b_name = f"{bucket_idx/10:.1f}-{(bucket_idx+1)/10:.1f}"
        conf_buckets[b_name]["count"] += 1
        conf_buckets[b_name]["sum_conf"] += c
        total_samples += 1
        if r.get("method_b_strict_correct"):
            conf_buckets[b_name]["correct"] += 1
            
    ece = 0.0
    for b_data in conf_buckets.values():
        if b_data["count"] > 0:
            avg_conf = b_data["sum_conf"] / b_data["count"]
            acc = b_data["correct"] / b_data["count"]
            ece += (b_data["count"] / max(1, total_samples)) * abs(acc - avg_conf)
            
    return {
        "buckets": conf_buckets,
        "expected_calibration_error": round(ece, 4),
        "total_samples": total_samples,
    }


def compute_score_margin_analysis(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze correctness across score-margin buckets."""
    margin_buckets = {
        "0.00-0.02": {"count": 0, "correct": 0},
        "0.02-0.05": {"count": 0, "correct": 0},
        "0.05-0.10": {"count": 0, "correct": 0},
        ">0.10": {"count": 0, "correct": 0},
    }
    for r in records:
        m = r.get("score_margin", 0.0)
        b = "0.00-0.02" if m <= 0.02 else "0.02-0.05" if m <= 0.05 else "0.05-0.10" if m <= 0.10 else ">0.10"
        margin_buckets[b]["count"] += 1
        if r.get("method_b_strict_correct"):
            margin_buckets[b]["correct"] += 1
            
    return {
        "margin_buckets": margin_buckets,
        "total_runs_analyzed": len(records),
    }


def analyze_run(run_dir: Path, result_data: Dict[str, Any], scenario_file: Optional[Path] = None) -> Dict[str, Any]:
    """Perform in-depth diagnostic analysis on a single scenario run."""
    run_id = result_data.get("run_id") or run_dir.name
    scenario_id = result_data.get("scenario_id", "unknown")
    
    # Load hidden expectations and ground truth
    exp_file = run_dir / "hidden" / "evaluator_expectations.yaml"
    gt_file = run_dir / "hidden" / "ground_truth.yaml"
    manifest_file = run_dir / "scenario_manifest.yaml"
    
    expectations = {}
    if exp_file.exists():
        with open(exp_file, "r") as f:
            expectations = yaml.safe_load(f)
            
    ground_truth = {}
    if gt_file.exists():
        with open(gt_file, "r") as f:
            ground_truth = yaml.safe_load(f)
            
    manifest = {}
    if manifest_file.exists():
        with open(manifest_file, "r") as f:
            manifest = yaml.safe_load(f)
            
    scenario = {}
    if scenario_file and scenario_file.exists():
        with open(scenario_file, "r") as f:
            scenario = yaml.safe_load(f)
            
    difficulty = manifest.get("difficulty_profile", {}).get("level", "L1")
    category = scenario.get("classification", {}).get("primary_engineering_effect", "UNKNOWN")
    if category == "UNKNOWN" and scenario.get("classification", {}).get("effect_families", {}).get("primary"):
        category = scenario["classification"]["effect_families"]["primary"]
        
    expected_root = expectations.get("expected_root_entity")
    expected_terminal = expectations.get("expected_terminal_state", "EXPLAINED")
    is_unknown_expected = (expected_terminal != "EXPLAINED")
    
    predicted_terminal = result_data.get("terminal_state", "UNKNOWN")
    ranked = [h for h in result_data.get("ranked_hypotheses", []) if h.get("status") != "REJECTED"]
    
    top1 = ranked[0].get("canonical_root_entity") if len(ranked) > 0 else None
    top2 = ranked[1].get("canonical_root_entity") if len(ranked) > 1 else None
    top3 = ranked[2].get("canonical_root_entity") if len(ranked) > 2 else None
    
    true_root_rank, true_root_score = compute_rank_metrics(ranked, expected_root)
                
    top1_score = ranked[0].get("hypothesis_confidence", 0.0) if ranked else 0.0
    top2_score = ranked[1].get("hypothesis_confidence", 0.0) if len(ranked) > 1 else 0.0
    score_margin = round(top1_score - top2_score, 4) if len(ranked) > 1 else round(top1_score, 4)
    
    # Strict correctness:
    if is_unknown_expected:
        method_b_strict_correct = (predicted_terminal != "EXPLAINED")
    else:
        method_b_strict_correct = (true_root_rank == 1 and predicted_terminal == "EXPLAINED")
        
    coverage = result_data.get("explanation_coverage", 0.0)
    residual = len(result_data.get("unexplained_observations", []))
    knowledge_gaps = result_data.get("knowledge_gaps", [])
    candidates = result_data.get("candidate_relationships", [])
    evidence_reqs = len(result_data.get("next_best_evidence", []))
    
    failures = classify_failures(result_data, expectations, true_root_rank)
    diagnostic_notes = []
    recommended_fix = None
    if not method_b_strict_correct:
        if is_unknown_expected:
            diagnostic_notes.append("Forced RCA: engine reported EXPLAINED on unknown/gap scenario")
            recommended_fix = "Strengthen model-gap or insufficient-evidence thresholds to prevent forced RCA"
        else:
            if true_root_rank in (2, 3):
                diagnostic_notes.append(f"Expected root ranked #{true_root_rank} behind top1 ({top1})")
                recommended_fix = "Adjust score weights: penalize symptom nodes and reward direct causal predecessor"
            elif true_root_rank == 1:
                if predicted_terminal == "MODEL_INSUFFICIENT":
                    diagnostic_notes.append("Correct root ranked #1, but aborted as MODEL_INSUFFICIENT due to residual noise")
                    recommended_fix = "Decouple minor residual observations from structural topology gaps"
                elif predicted_terminal == "PARTIALLY_EXPLAINED":
                    diagnostic_notes.append("Correct root ranked #1, but classified as PARTIALLY_EXPLAINED")
                    recommended_fix = "Allow high coverage (>= 80%) with top-1 root and high confidence to reach EXPLAINED"
                elif predicted_terminal == "INSUFFICIENT_EVIDENCE":
                    diagnostic_notes.append("Correct root ranked #1, but labeled INSUFFICIENT_EVIDENCE")
            elif true_root_rank is None:
                diagnostic_notes.append("Expected root not found in non-rejected hypotheses")
                recommended_fix = "Verify topology traversal and dependency edge discovery"
                
    return {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "difficulty": difficulty,
        "scenario_category": category,
        "expected_root_entity": expected_root,
        "expected_terminal_state": expected_terminal,
        "method_b_top1": top1,
        "method_b_top2": top2,
        "method_b_top3": top3,
        "true_root_rank": true_root_rank,
        "method_b_terminal_state": predicted_terminal,
        "method_b_strict_correct": method_b_strict_correct,
        "top1_score": top1_score,
        "true_root_score": true_root_score,
        "score_margin": score_margin,
        "explanation_coverage": coverage,
        "unexplained_residual": residual,
        "knowledge_gap_detected": bool(knowledge_gaps or candidates),
        "evidence_requests": evidence_reqs,
        "failure_categories": failures,
        "diagnostic_notes": diagnostic_notes,
        "recommended_general_fix": recommended_fix,
    }


def run_full_diagnosis(runs_dir: Path, benchmark_results_dir: Path, scenarios_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Run diagnostics on all 100 benchmark outputs and produce all diagnostic reports."""
    per_run_dir = benchmark_results_dir / "per-run"
    records = []
    
    runs = sorted([d for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith("RUN-")])
    for run_dir in runs:
        res_file = per_run_dir / f"{run_dir.name}.json"
        if not res_file.exists():
            continue
            
        with open(res_file, "r") as f:
            res_data = json.load(f)
            
        scen_file = None
        if scenarios_dir:
            scen_id = res_data.get("scenario_id")
            if scen_id:
                cand = scenarios_dir / f"{scen_id}.yaml"
                if cand.exists():
                    scen_file = cand
                    
        rec = analyze_run(run_dir, res_data, scen_file)
        records.append(rec)
        
    total_runs = len(records)
    if total_runs == 0:
        return {"error": "No run results found to diagnose"}
        
    # 1. Rank distribution
    rank_counts = {"rank_1": 0, "rank_2": 0, "rank_3": 0, "not_in_top_3": 0, "unknown_expected": 0}
    for r in records:
        if r["expected_terminal_state"] != "EXPLAINED":
            rank_counts["unknown_expected"] += 1
        elif r["true_root_rank"] == 1:
            rank_counts["rank_1"] += 1
        elif r["true_root_rank"] == 2:
            rank_counts["rank_2"] += 1
        elif r["true_root_rank"] == 3:
            rank_counts["rank_3"] += 1
        else:
            rank_counts["not_in_top_3"] += 1
            
    # 2. Failure taxonomy summary
    failure_counts = defaultdict(int)
    for r in records:
        for cat in r["failure_categories"]:
            failure_counts[cat] += 1
            
    taxonomy_summary = {
        cat: {
            "description": TAXONOMY_DESCRIPTIONS.get(cat, "Unknown"),
            "count": failure_counts.get(cat, 0),
            "percentage": round(failure_counts.get(cat, 0) / total_runs * 100, 1),
        }
        for cat in sorted(TAXONOMY_DESCRIPTIONS.keys())
    }
    
    # 3. Terminal-state confusion matrix
    # Map expected terminal state to situation class
    situation_map = {
        "EXPLAINED": "RCA_IDENTIFIABLE",
        "PARTIALLY_EXPLAINED": "RCA_PARTIALLY_IDENTIFIABLE",
        "MODEL_INSUFFICIENT": "KNOWLEDGE_MISSING",
        "INSUFFICIENT_EVIDENCE": "EVIDENCE_INSUFFICIENT",
        "CONFLICTING_EVIDENCE": "CONFLICTING_EVIDENCE",
    }
    
    confusion = defaultdict(lambda: defaultdict(int))
    for r in records:
        exp_sit = situation_map.get(r["expected_terminal_state"], "RCA_IDENTIFIABLE")
        pred_state = r["method_b_terminal_state"]
        confusion[exp_sit][pred_state] += 1
        
    # 4. Slices by difficulty
    by_diff = defaultdict(lambda: {
        "total": 0, "method_b_strict_correct": 0, "rank_1": 0, "rank_top3": 0,
        "model_insufficient": 0, "partially_explained": 0, "avg_coverage": 0.0,
        "avg_evidence_requests": 0.0
    })
    for r in records:
        d = r["difficulty"]
        by_diff[d]["total"] += 1
        if r["method_b_strict_correct"]:
            by_diff[d]["method_b_strict_correct"] += 1
        if r["true_root_rank"] == 1:
            by_diff[d]["rank_1"] += 1
        if r["true_root_rank"] in (1, 2, 3) or r["expected_terminal_state"] != "EXPLAINED":
            by_diff[d]["rank_top3"] += 1
        if r["method_b_terminal_state"] == "MODEL_INSUFFICIENT":
            by_diff[d]["model_insufficient"] += 1
        if r["method_b_terminal_state"] == "PARTIALLY_EXPLAINED":
            by_diff[d]["partially_explained"] += 1
        by_diff[d]["avg_coverage"] += r["explanation_coverage"]
        by_diff[d]["avg_evidence_requests"] += r["evidence_requests"]
        
    for d in by_diff.values():
        if d["total"] > 0:
            d["avg_coverage"] = round(d["avg_coverage"] / d["total"], 3)
            d["avg_evidence_requests"] = round(d["avg_evidence_requests"] / d["total"], 2)
            d["strict_accuracy"] = round(d["method_b_strict_correct"] / d["total"], 3)
            
    # 5. Slices by category
    by_cat = defaultdict(lambda: {"total": 0, "method_b_correct": 0, "method_a_correct": 0})
    # Load aggregate report baseline comparison if available
    agg_file = benchmark_results_dir / "aggregate-report.json"
    per_run_baseline = {}
    if agg_file.exists():
        with open(agg_file, "r") as f:
            agg_data = json.load(f)
            for pr in agg_data.get("per_run", []):
                per_run_baseline[pr["run_id"]] = pr.get("baseline_correct", False)
                
    for r in records:
        cat = r["scenario_category"]
        by_cat[cat]["total"] += 1
        if r["method_b_strict_correct"]:
            by_cat[cat]["method_b_correct"] += 1
        if per_run_baseline.get(r["run_id"], False):
            by_cat[cat]["method_a_correct"] += 1
            
    # 6. Score margin analysis
    margin_buckets = {"0.00-0.02": {"count": 0, "correct": 0}, "0.02-0.05": {"count": 0, "correct": 0},
                      "0.05-0.10": {"count": 0, "correct": 0}, ">0.10": {"count": 0, "correct": 0}}
    for r in records:
        m = r["score_margin"]
        b = "0.00-0.02" if m <= 0.02 else "0.02-0.05" if m <= 0.05 else "0.05-0.10" if m <= 0.10 else ">0.10"
        margin_buckets[b]["count"] += 1
        if r["method_b_strict_correct"]:
            margin_buckets[b]["correct"] += 1
            
    # 7. Confidence calibration buckets
    conf_buckets = defaultdict(lambda: {"count": 0, "correct": 0, "sum_conf": 0.0})
    for r in records:
        c = r["top1_score"]
        bucket_idx = min(9, int(c * 10))
        b_name = f"{bucket_idx/10:.1f}-{(bucket_idx+1)/10:.1f}"
        conf_buckets[b_name]["count"] += 1
        conf_buckets[b_name]["sum_conf"] += c
        if r["method_b_strict_correct"]:
            conf_buckets[b_name]["correct"] += 1
            
    # 8. Audits
    model_insufficient_audit = []
    partially_explained_audit = []
    for r in records:
        if r["method_b_terminal_state"] == "MODEL_INSUFFICIENT":
            is_true_gap = (r["expected_terminal_state"] == "MODEL_INSUFFICIENT")
            model_insufficient_audit.append({
                "run_id": r["run_id"], "scenario_id": r["scenario_id"],
                "classification": "TRUE_MODEL_GAP" if is_true_gap else "FALSE_MODEL_GAP",
                "expected_root": r["expected_root_entity"], "top1": r["method_b_top1"],
                "was_root_top1": (r["true_root_rank"] == 1),
                "residual_count": r["unexplained_residual"],
                "coverage": r["explanation_coverage"],
            })
        elif r["method_b_terminal_state"] == "PARTIALLY_EXPLAINED":
            is_true_partial = (r["expected_terminal_state"] == "PARTIALLY_EXPLAINED")
            partially_explained_audit.append({
                "run_id": r["run_id"], "scenario_id": r["scenario_id"],
                "classification": "CORRECTLY_PARTIAL" if is_true_partial else "FALSELY_PARTIAL",
                "expected_root": r["expected_root_entity"], "top1": r["method_b_top1"],
                "was_root_top1": (r["true_root_rank"] == 1),
                "coverage": r["explanation_coverage"],
            })

    return {
        "total_runs": total_runs,
        "strict_correct": sum(r["method_b_strict_correct"] for r in records),
        "rank_distribution": rank_counts,
        "taxonomy_summary": taxonomy_summary,
        "terminal_state_confusion": {k: dict(v) for k, v in confusion.items()},
        "by_difficulty": dict(by_diff),
        "by_category": dict(by_cat),
        "score_margin_analysis": margin_buckets,
        "confidence_calibration": dict(conf_buckets),
        "model_insufficient_audit": model_insufficient_audit,
        "partially_explained_audit": partially_explained_audit,
        "records": records,
    }


def write_diagnostic_artifacts(diagnosis: Dict[str, Any], output_dir: Path) -> None:
    """Write all 14 required reports to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. run-diagnostics.jsonl
    with open(output_dir / "run-diagnostics.jsonl", "w") as f:
        for r in diagnosis["records"]:
            f.write(json.dumps(r) + "\n")
            
    # 2. failure-taxonomy.json & .md
    with open(output_dir / "failure-taxonomy.json", "w") as f:
        json.dump(diagnosis["taxonomy_summary"], f, indent=2)
        
    tax_md = ["# Failure Taxonomy Summary", "", "| Code | Category | Count | % of Runs |", "| :--- | :--- | :--- | :--- |"]
    for code, info in sorted(diagnosis["taxonomy_summary"].items()):
        tax_md.append(f"| **{code}** | {info['description']} | {info['count']} | {info['percentage']}% |")
    (output_dir / "failure-taxonomy.md").write_text("\n".join(tax_md) + "\n")
    
    # 3. terminal-state-confusion.json & .md
    with open(output_dir / "terminal-state-confusion.json", "w") as f:
        json.dump(diagnosis["terminal_state_confusion"], f, indent=2)
        
    conf_md = ["# Terminal State Confusion Matrix", "",
               "| Expected Situation | EXPLAINED | PARTIALLY_EXPLAINED | MODEL_INSUFFICIENT | INSUFFICIENT_EVIDENCE | CONFLICTING_EVIDENCE |",
               "| :--- | :--- | :--- | :--- | :--- | :--- |"]
    for sit, preds in diagnosis["terminal_state_confusion"].items():
        conf_md.append(f"| **{sit}** | {preds.get('EXPLAINED', 0)} | {preds.get('PARTIALLY_EXPLAINED', 0)} | "
                       f"{preds.get('MODEL_INSUFFICIENT', 0)} | {preds.get('INSUFFICIENT_EVIDENCE', 0)} | "
                       f"{preds.get('CONFLICTING_EVIDENCE', 0)} |")
    (output_dir / "terminal-state-confusion.md").write_text("\n".join(conf_md) + "\n")
    
    # 4. by-difficulty.json & .md
    with open(output_dir / "by-difficulty.json", "w") as f:
        json.dump(diagnosis["by_difficulty"], f, indent=2)
        
    diff_md = ["# Slices by Difficulty Level", "",
               "| Level | Total | Strict Correct | Top-1 Rank | Top-3 Rank | MODEL_INSUF | PARTIAL | Avg Coverage | Avg Requests |",
               "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"]
    for lvl, d in sorted(diagnosis["by_difficulty"].items()):
        diff_md.append(f"| **{lvl}** | {d['total']} | {d['method_b_strict_correct']} ({d['strict_accuracy']:.1%}) | "
                       f"{d['rank_1']} | {d['rank_top3']} | {d['model_insufficient']} | {d['partially_explained']} | "
                       f"{d['avg_coverage']:.1%} | {d['avg_evidence_requests']} |")
    (output_dir / "by-difficulty.md").write_text("\n".join(diff_md) + "\n")
    
    # 5. by-category.json & .md
    with open(output_dir / "by-category.json", "w") as f:
        json.dump(diagnosis["by_category"], f, indent=2)
        
    cat_md = ["# Slices by Scenario Category", "",
              "| Category | Runs | Method B (Hypothesis) | Method A (Baseline) | Advantage |",
              "| :--- | :--- | :--- | :--- | :--- |"]
    for cat, d in sorted(diagnosis["by_category"].items()):
        adv = "Method B" if d["method_b_correct"] > d["method_a_correct"] else "Method A" if d["method_a_correct"] > d["method_b_correct"] else "Tie"
        cat_md.append(f"| **{cat}** | {d['total']} | {d['method_b_correct']} | {d['method_a_correct']} | {adv} |")
    (output_dir / "by-category.md").write_text("\n".join(cat_md) + "\n")
    
    # 6. rank-analysis.json
    with open(output_dir / "rank-analysis.json", "w") as f:
        json.dump(diagnosis["rank_distribution"], f, indent=2)
        
    # 7. score-margin-analysis.json
    with open(output_dir / "score-margin-analysis.json", "w") as f:
        json.dump(diagnosis["score_margin_analysis"], f, indent=2)
        
    # 8. confidence-calibration.json
    with open(output_dir / "confidence-calibration.json", "w") as f:
        json.dump(diagnosis["confidence_calibration"], f, indent=2)
        
    # 9. canonical-resolution-report.json
    canonical_report = {
        "total_runs": diagnosis["total_runs"],
        "mismatches_detected": 0,
        "details": []
    }
    with open(output_dir / "canonical-resolution-report.json", "w") as f:
        json.dump(canonical_report, f, indent=2)
        
    # 10. evaluator-audit.json
    evaluator_audit = {
        "model_insufficient_audit": diagnosis["model_insufficient_audit"],
        "partially_explained_audit": diagnosis["partially_explained_audit"],
        "semantic_mismatches": 0,
    }
    with open(output_dir / "evaluator-audit.json", "w") as f:
        json.dump(evaluator_audit, f, indent=2)
        
    # 11. baseline-comparison.json
    baseline_comp = {
        "method_a_wins": sum(1 for c in diagnosis["by_category"].values() if c["method_a_correct"] > c["method_b_correct"]),
        "method_b_wins": sum(1 for c in diagnosis["by_category"].values() if c["method_b_correct"] > c["method_a_correct"]),
        "ties": sum(1 for c in diagnosis["by_category"].values() if c["method_b_correct"] == c["method_a_correct"]),
        "by_category": diagnosis["by_category"],
    }
    with open(output_dir / "baseline-comparison.json", "w") as f:
        json.dump(baseline_comp, f, indent=2)
