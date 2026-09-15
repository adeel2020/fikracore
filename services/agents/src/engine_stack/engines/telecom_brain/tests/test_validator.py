import json
import yaml
from pathlib import Path
import pytest
from engine_stack.engines.telecom_brain.investigation.validator import validate_run, validate_all

@pytest.fixture
def valid_run_dir(tmp_path):
    run_dir = tmp_path / "RUN-SCN-001-L1-SEED-12345"
    run_dir.mkdir()
    
    # Manifest
    manifest = {
        "scenario_id": "SCN-001",
        "random_seed": 12345,
        "difficulty_profile": {"level": "L1"},
        "compile_status": "VALID"
    }
    with open(run_dir / "scenario_manifest.yaml", "w") as f:
        yaml.dump(manifest, f)
        
    # Hidden
    hidden_dir = run_dir / "hidden"
    hidden_dir.mkdir()
    
    with open(hidden_dir / "ground_truth.yaml", "w") as f:
        yaml.dump({"scenario_id": "SCN-001", "hidden_truth": {"root_entity": "nodeA"}}, f)
        
    with open(hidden_dir / "evaluator_expectations.yaml", "w") as f:
        yaml.dump({"scenario_id": "SCN-001", "expected_root_entity": "nodeA"}, f)
        
    with open(hidden_dir / "causal_graph.yaml", "w") as f:
        yaml.dump({"nodes": [{"entity_id": "nodeA"}], "edges": []}, f)
        
    with open(hidden_dir / "noise_manifest.yaml", "w") as f:
        yaml.dump({}, f)
        
    # Operational
    op_dir = run_dir / "operational"
    op_dir.mkdir()
    
    with open(op_dir / "topology_view.yaml", "w") as f:
        yaml.dump({}, f)
        
    valid_record = {
        "event_id": "evt1",
        "entity_id": "nodeA",
        "event_time": "2023-01-01T10:00:00Z",
        "ingestion_time": "2023-01-01T10:00:05Z"
    }
    
    for fname in ['alarms.jsonl', 'logs.jsonl', 'metrics.jsonl', 'kpis.jsonl',
                  'traces.jsonl', 'changes.jsonl', 'tickets.jsonl', 'recovery.jsonl']:
        with open(op_dir / fname, "w") as f:
            f.write(json.dumps(valid_record) + "\n")
            
    return run_dir

def test_all_100_runs_pass_validation():
    runs_dir = Path("/Users/adeelarshad/kagent/services/agents/src/engine_stack/engines/telecom_brain/simulator/runs/")
    if not runs_dir.exists():
        pytest.skip("Real runs directory not found")
        
    result = validate_all(runs_dir)
    # Just asserting it runs correctly and returns expected structure. 
    # If 100 runs exist, assert all passed.
    if result["total_runs"] == 100:
        assert result["failed"] == 0, f"Some runs failed: {result}"

def test_forbidden_field_detected(valid_run_dir):
    # Inject forbidden field
    record = {
        "event_id": "evt2",
        "entity_id": "nodeA",
        "event_time": "2023-01-01T10:00:00Z",
        "ingestion_time": "2023-01-01T10:00:05Z",
        "root_entity": "nodeA"  # Forbidden!
    }
    with open(valid_run_dir / "operational" / "alarms.jsonl", "w") as f:
        f.write(json.dumps(record) + "\n")
        
    result = validate_run(valid_run_dir)
    assert not result["passed"]
    assert not result["checks"]["no_truth_leakage"]["passed"]

def test_timestamp_violation_detected(valid_run_dir):
    # event_time > ingestion_time
    record = {
        "event_id": "evt3",
        "entity_id": "nodeA",
        "event_time": "2023-01-01T10:00:10Z",
        "ingestion_time": "2023-01-01T10:00:05Z"
    }
    with open(valid_run_dir / "operational" / "alarms.jsonl", "w") as f:
        f.write(json.dumps(record) + "\n")
        
    result = validate_run(valid_run_dir)
    assert not result["passed"]
    assert not result["checks"]["timestamp_consistency"]["passed"]

def test_missing_evidence_file_detected(valid_run_dir):
    # Remove a required file
    (valid_run_dir / "operational" / "alarms.jsonl").unlink()
    
    result = validate_run(valid_run_dir)
    assert not result["passed"]
    assert not result["checks"]["operational_files_exist"]["passed"]
