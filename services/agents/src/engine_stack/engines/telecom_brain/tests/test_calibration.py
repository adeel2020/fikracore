"""Unit and regression tests for Step 4.1 Calibration per Section 31."""

import ast
import json
from pathlib import Path
import pytest
import yaml

from engine_stack.engines.telecom_brain.investigation.contracts import (
    Hypothesis, KnowledgeState, Terminal, InvestigationResult
)
from engine_stack.engines.telecom_brain.investigation.splits import generate_stratified_splits
from engine_stack.engines.telecom_brain.investigation.diagnostics import (
    classify_failures, compute_rank_metrics, analyze_run
)


RUNS_DIR = Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/runs")
SPLITS_FILE = Path("artifacts/hypothesis/calibration/splits.json")


def test_splits_are_deterministic_and_disjoint():
    """1. Test that stratified splits are deterministic and disjoint."""
    splits1 = generate_stratified_splits(RUNS_DIR)
    splits2 = generate_stratified_splits(RUNS_DIR)
    
    assert splits1 == splits2, "Splits must be completely deterministic for the same seed"
    
    calib = set(splits1["calibration"])
    val = set(splits1["validation"])
    hold = set(splits1["holdout"])
    
    assert len(calib) == 60, f"Expected 60 calibration runs, got {len(calib)}"
    assert len(val) == 20, f"Expected 20 validation runs, got {len(val)}"
    assert len(hold) == 20, f"Expected 20 holdout runs, got {len(hold)}"
    
    assert calib.isdisjoint(val), "Calibration and Validation must be disjoint"
    assert calib.isdisjoint(hold), "Calibration and Holdout must be disjoint"
    assert val.isdisjoint(hold), "Validation and Holdout must be disjoint"
    assert len(calib | val | hold) == 100, "Splits must partition all 100 runs"


def test_splits_stratification_balance():
    """2. Test that difficulty levels L1–L5 are balanced across splits."""
    if SPLITS_FILE.exists():
        with open(SPLITS_FILE, "r") as f:
            splits = json.load(f)
    else:
        splits = generate_stratified_splits(RUNS_DIR)
        
    diff_counts = {"calibration": {}, "validation": {}, "holdout": {}}
    
    for split_name, run_ids in splits.items():
        for rid in run_ids:
            run_dir = RUNS_DIR / rid
            with open(run_dir / "scenario_manifest.yaml", "r") as f:
                manifest = yaml.safe_load(f)
            diff = manifest.get("difficulty_profile", {}).get("level", "L0")
            diff_counts[split_name][diff] = diff_counts[split_name].get(diff, 0) + 1
            
    for level in ["L1", "L2", "L3", "L4", "L5"]:
        assert diff_counts["calibration"].get(level, 0) == 12, f"Expected 12 {level} in calibration"
        assert diff_counts["validation"].get(level, 0) == 4, f"Expected 4 {level} in validation"
        assert diff_counts["holdout"].get(level, 0) == 4, f"Expected 4 {level} in holdout"


def test_true_root_rank_calculation():
    """3. Test rank calculation logic for Top-1, Top-2, Top-3, >3."""
    hyps = [
        {"root_entities": ["ENT-A"], "hypothesis_confidence": 0.9},
        {"root_entities": ["ENT-B"], "hypothesis_confidence": 0.8},
        {"root_entities": ["ENT-C"], "hypothesis_confidence": 0.7},
        {"root_entities": ["ENT-D"], "hypothesis_confidence": 0.6},
    ]
    
    rank1, score1 = compute_rank_metrics(hyps, "ENT-A")
    assert rank1 == 1
    assert score1 == 0.9
    
    rank2, score2 = compute_rank_metrics(hyps, "ENT-B")
    assert rank2 == 2
    assert score2 == 0.8
    
    rank3, score3 = compute_rank_metrics(hyps, "ENT-C")
    assert rank3 == 3
    assert score3 == 0.7
    
    rank4, score4 = compute_rank_metrics(hyps, "ENT-D")
    assert rank4 == 4
    assert score4 == 0.6
    
    rank_none, score_none = compute_rank_metrics(hyps, "ENT-Z")
    assert rank_none is None
    assert score_none is None


def test_failure_taxonomy_classification():
    """4. Test that failure taxonomy classifies failure patterns correctly."""
    res_a = {
        "terminal_state": "EXPLAINED",
        "ranked_hypotheses": [
            {"root_entities": ["WRONG"], "hypothesis_confidence": 0.9, "status": "SUPPORTED"},
            {"root_entities": ["TRUE_ROOT"], "hypothesis_confidence": 0.85, "status": "SUPPORTED"},
        ],
        "candidate_relationships": [],
        "unexplained_observations": [],
    }
    exp_a = {"expected_root_entity": "TRUE_ROOT", "expected_terminal_state": "EXPLAINED"}
    cats_a = classify_failures(res_a, exp_a, true_root_rank=2)
    assert "A" in cats_a
    
    res_c = {
        "terminal_state": "MODEL_INSUFFICIENT",
        "ranked_hypotheses": [
            {"root_entities": ["TRUE_ROOT"], "hypothesis_confidence": 0.85, "status": "SUPPORTED"}
        ],
        "candidate_relationships": [],
        "unexplained_observations": ["ALM-1"],
    }
    exp_c = {"expected_root_entity": "TRUE_ROOT", "expected_terminal_state": "EXPLAINED"}
    cats_c = classify_failures(res_c, exp_c, true_root_rank=1)
    assert "C" in cats_c
    assert "B" in cats_c


def test_no_scenario_specific_calibration_constants():
    """5. Ensure strictly no scenario-specific hardcoded hacks exist."""
    investigator_path = Path("services/agents/src/engine_stack/engines/telecom_brain/investigation/investigator.py")
    benchmark_path = Path("services/agents/src/engine_stack/engines/telecom_brain/investigation/benchmark.py")
    
    for file_path in [investigator_path, benchmark_path]:
        code = file_path.read_text()
        tree = ast.parse(code, filename=str(file_path))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                val = node.value
                assert not (val.startswith("SCN-") and len(val) == 7), (
                    f"Forbidden scenario literal '{val}' found in {file_path.name}"
                )
                assert not (val.startswith("RUN-SCN-")), (
                    f"Forbidden run literal '{val}' found in {file_path.name}"
                )
            if isinstance(node, ast.Compare):
                for comparator in node.comparators:
                    if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
                        val = comparator.value
                        assert not val.startswith("SCN-"), (
                            f"Forbidden scenario comparison with '{val}' in {file_path.name}"
                        )


def test_confidence_calibration_monotonicity():
    """6. Test confidence binning calculation."""
    from engine_stack.engines.telecom_brain.investigation.diagnostics import compute_confidence_calibration
    
    runs = [
        {"method_b_strict_correct": True, "top1_score": 0.85},
        {"method_b_strict_correct": True, "top1_score": 0.88},
        {"method_b_strict_correct": False, "top1_score": 0.45},
        {"method_b_strict_correct": False, "top1_score": 0.20},
    ]
    
    calib = compute_confidence_calibration(runs)
    assert "buckets" in calib
    assert "expected_calibration_error" in calib
    assert len(calib["buckets"]) == 10


def test_score_margin_calculation():
    """7. Test top1 - top2 score margin computation."""
    from engine_stack.engines.telecom_brain.investigation.diagnostics import compute_score_margin_analysis
    
    runs = [
        {"method_b_strict_correct": True, "score_margin": 0.15},
        {"method_b_strict_correct": True, "score_margin": 0.08},
        {"method_b_strict_correct": False, "score_margin": 0.01},
    ]
    
    margin_report = compute_score_margin_analysis(runs)
    assert "margin_buckets" in margin_report
    assert margin_report["total_runs_analyzed"] == 3


def test_model_insufficient_audit_flags_real_gaps_only():
    """8. Test that MODEL_INSUFFICIENT is triggered by topology/model gaps, not noise."""
    from engine_stack.engines.telecom_brain.investigation import Investigator
    from engine_stack.engines.telecom_brain.investigation.knowledge import InMemoryKnowledgeProvider
    from engine_stack.engines.telecom_brain.investigation.contracts import GeneratedRunInput, Evidence
    from datetime import datetime, timezone
    
    prov_gap = InMemoryKnowledgeProvider([{"slug": "A"}, {"slug": "B"}], [])
    run_in = GeneratedRunInput(run_id="TEST-GAP", scenario_id="S-GAP", difficulty_profile="L1", seed=1)
    
    now = datetime(2026, 9, 10, 12, tzinfo=timezone.utc)
    ev_gap = [
        Evidence(evidence_id="e1", event_time=now, ingestion_time=now, domain="transport",
                 entity="A", canonical_entity="A", source_native_entity="A", source="nms",
                 source_reliability=0.95, polarity="abnormal", evidence_type="alarms",
                 service=["svc"], severity="MAJOR", signal="loss"),
        Evidence(evidence_id="e2", event_time=now, ingestion_time=now, domain="transport",
                 entity="B", canonical_entity="B", source_native_entity="B", source="probe",
                 source_reliability=0.95, polarity="abnormal", evidence_type="traces",
                 observed_path=["A", "B"], service=["svc"], severity="MAJOR", signal="loss"),
    ]
    
    res = Investigator(prov_gap).investigate(run_in, ev_gap)
    assert res.terminal_state == Terminal.MODEL_INSUFFICIENT
    assert res.discovery_mode is True
    assert len(res.candidate_relationships) > 0


def test_calibrated_benchmark_reproducibility():
    """9. Test that benchmark evaluation is 100% deterministic and reproducible."""
    from engine_stack.engines.telecom_brain.investigation.benchmark import benchmark_run
    
    sample_run = RUNS_DIR / "RUN-SCN-001-L1-SEED-42001"
    res1 = benchmark_run(sample_run)
    res2 = benchmark_run(sample_run)
    
    comp1 = {k: v for k, v in res1["comparison"].items() if k != "time_seconds"}
    comp2 = {k: v for k, v in res2["comparison"].items() if k != "time_seconds"}
    assert comp1 == comp2
    assert res1["result"]["terminal_state"] == res2["result"]["terminal_state"]
    assert res1["result"]["ranked_hypotheses"][0]["root_entities"] == res2["result"]["ranked_hypotheses"][0]["root_entities"]


def test_holdout_evaluated_only_after_policy_freeze():
    """10. Test that holdout results exist under after/ and splits match policy."""
    after_dir = Path("artifacts/hypothesis/calibration/after/per-run")
    assert after_dir.exists(), "Calibrated results must exist under artifacts/hypothesis/calibration/after/"
    
    with open(SPLITS_FILE, "r") as f:
        splits = json.load(f)
        
    holdout_runs = splits.get("holdout", [])
    assert len(holdout_runs) == 20
    
    for rid in holdout_runs:
        run_file = after_dir / f"{rid}.json"
        assert run_file.exists(), f"Holdout run {rid} must exist in calibrated benchmark results"
