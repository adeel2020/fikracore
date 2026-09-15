import json
from pathlib import Path
from engine_stack.engines.telecom_brain.investigation.benchmark import benchmark_run, benchmark_all

def test_benchmark_single_run(tmp_path, monkeypatch):
    runs_dir = Path(__file__).parents[1] / "simulator" / "runs"
    run_dir = runs_dir / "RUN-SCN-001-L1-SEED-42001"
    
    if not run_dir.exists():
        # Mock the run directory for testing if it doesn't exist
        run_dir = tmp_path / "RUN-SCN-001-L1-SEED-42001"
        run_dir.mkdir(parents=True)
        (run_dir / "operational").mkdir()
        (run_dir / "hidden").mkdir()
        
        with open(run_dir / "scenario_manifest.yaml", "w") as f:
            f.write("scenario_id: SCN-001\ndifficulty_profile:\n  level: L1\n")
        with open(run_dir / "operational" / "topology_view.yaml", "w") as f:
            f.write("visible_entities: ['E1']\nvisible_relationships: ['R1']\n")
        with open(run_dir / "hidden" / "causal_graph.yaml", "w") as f:
            f.write("edges:\n  - relationship_id: R1\n    source_entity: E1\n    target_entity: E2\n")
        with open(run_dir / "hidden" / "evaluator_expectations.yaml", "w") as f:
            f.write("expected_root_entity: E1\nexpected_terminal_state: EXPLAINED\n")
            
        # Mocking input_from_run and load_evidence
        import engine_stack.engines.telecom_brain.investigation.evidence as evidence
        monkeypatch.setattr(evidence, "input_from_run", lambda r: None)
        monkeypatch.setattr(evidence, "load_evidence", lambda i, r: (None, None))
        
        # Mocking Investigator
        import engine_stack.engines.telecom_brain.investigation as inv
        class MockResult:
            def model_dump(self, **kwargs):
                return {"terminal_state": "EXPLAINED"}
        class MockInvestigator:
            def __init__(self, provider):
                pass
            def investigate(self, i, e, h):
                return MockResult()
            def run(self, i, r):
                return MockResult()
        monkeypatch.setattr(inv, "Investigator", MockInvestigator)
        
        # Mocking compare
        import engine_stack.engines.telecom_brain.investigation.evaluator as evaluator
        monkeypatch.setattr(evaluator, "compare", lambda r, e, u: {"correct": True})
        
    result = benchmark_run(run_dir)
    assert result["run_id"] == "RUN-SCN-001-L1-SEED-42001"
    assert "comparison" in result
    
def test_benchmark_subset(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    
    # Create 5 dummy runs
    for i in range(5):
        run_dir = runs_dir / f"RUN-SCN-00{i}-L1-SEED-1000{i}"
        run_dir.mkdir()
        
    def mock_benchmark_run(run_dir):
        return {
            "run_id": run_dir.name,
            "scenario_id": "SCN-001",
            "difficulty": "L1",
            "result": {"terminal_state": "EXPLAINED"},
            "comparison": {"correct": True, "method_a_correct": False, "unknown_correct": False}
        }
        
    monkeypatch.setattr("engine_stack.engines.telecom_brain.investigation.benchmark.benchmark_run", mock_benchmark_run)
    
    output_dir = tmp_path / "output"
    report = benchmark_all(runs_dir, output_dir, max_runs=5)
    
    assert report["total_runs"] == 5
    assert "metrics" in report
    
def test_aggregate_report_structure(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    
    run_dir = runs_dir / "RUN-SCN-001-L1-SEED-10001"
    run_dir.mkdir()
    
    def mock_benchmark_run(run_dir):
        return {
            "run_id": run_dir.name,
            "scenario_id": "SCN-001",
            "difficulty": "L1",
            "result": {"terminal_state": "EXPLAINED"},
            "comparison": {"correct": True, "method_a_correct": False, "unknown_correct": False}
        }
        
    monkeypatch.setattr("engine_stack.engines.telecom_brain.investigation.benchmark.benchmark_run", mock_benchmark_run)
    
    output_dir = tmp_path / "output"
    report = benchmark_all(runs_dir, output_dir)
    
    assert "metrics" in report
    assert "baseline_comparison" in report
    assert "terminal_state_distribution" in report
    assert "per_difficulty" in report
    assert "per_run" in report


def test_benchmark_all_optional_params(tmp_path, monkeypatch):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    run_dir = runs_dir / "RUN-SCN-001-L1-SEED-10001"
    run_dir.mkdir()

    def mock_benchmark_run(rd):
        return {
            "run_id": rd.name,
            "scenario_id": "SCN-001",
            "difficulty": "L1",
            "result": {"terminal_state": "EXPLAINED"},
            "comparison": {"correct": True, "method_a_correct": False, "unknown_correct": False}
        }

    monkeypatch.setattr("engine_stack.engines.telecom_brain.investigation.benchmark.benchmark_run", mock_benchmark_run)
    report = benchmark_all(runs_dir=runs_dir, output_dir=tmp_path / "out_default")
    assert "metrics" in report

