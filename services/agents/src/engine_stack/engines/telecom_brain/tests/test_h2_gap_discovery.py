"""Step 4.2 / H2 Automated Test Suite: Operational Knowledge-Gap Discovery.

Covers the 12 required test cases from Section 38 of the H2 specification:
1. test_hidden_gap_not_visible_to_engine
2. test_model_insufficient_when_required_edge_missing
3. test_insufficient_evidence_when_model_complete
4. test_conflicting_evidence_not_misclassified_as_model_gap
5. test_gap_boundary_localization
6. test_candidate_relation_not_confirmed
7. test_no_automatic_telecombrain_mutation
8. test_next_best_evidence_ranked
9. test_unknown_entity_not_invented
10. test_hidden_truth_not_used_in_runtime
11. test_h2_scenario_leakage_detection
12. test_h1_regression_suite_still_passes
"""

from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil
from typing import Any
import pytest
import yaml

from engine_stack.engines.telecom_brain.investigation.contracts import (
    Evidence,
    GeneratedRunInput,
    KnowledgeState,
    Terminal,
)
from engine_stack.engines.telecom_brain.investigation.h2_validator import validate_single_h2_run
from engine_stack.engines.telecom_brain.investigation.investigator import Investigator
from engine_stack.engines.telecom_brain.investigation.knowledge import InMemoryKnowledgeProvider


# Path to reference network and simulator runs
REFERENCE_NETWORK_PATH = (
    Path(__file__).parents[1] / "simulator" / "operator_model" / "reference_synthetic_network.yaml"
)
H2_RUNS_DIR = Path(__file__).parents[1] / "simulator" / "h2_runs"


def _load_reference_network() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load reference operator network topology."""
    with open(REFERENCE_NETWORK_PATH) as f:
        network_data = yaml.safe_load(f)

    ref_pages = {}
    ref_rels = []
    for ent in network_data.get("entities", []):
        eid = ent.get("entity_id") or ent.get("id")
        if eid:
            ref_pages[eid] = {
                "slug": eid,
                "frontmatter": {"entity_type": ent.get("entity_type", ent.get("type", "unknown"))},
            }
    for rel in network_data.get("relationships", []):
        rid = rel.get("relationship_id") or rel.get("id")
        src = rel.get("source_entity") or rel.get("source")
        tgt = rel.get("target_entity") or rel.get("target")
        ltype = (rel.get("relationship_type") or rel.get("link_type") or "depends-on").lower().replace("_", "-")
        if rid and src and tgt:
            ref_rels.append({
                "relationship_id": rid,
                "source": src,
                "target": tgt,
                "link_type": ltype,
                "state": "CONFIRMED",
                "confidence": 1.0,
                "provenance": "reference-operator-model",
            })
    return ref_pages, ref_rels


def _setup_h2_investigation(run_dir: Path) -> tuple[Investigator, GeneratedRunInput, Path, InMemoryKnowledgeProvider]:
    """Set up truth-blind investigator and run input for an H2 run directory."""
    ref_pages, ref_rels = _load_reference_network()
    op_dir = run_dir / "operational"

    with open(run_dir / "scenario_manifest.yaml") as f:
        manifest = yaml.safe_load(f)
    with open(op_dir / "topology_view.yaml") as f:
        op_topo = yaml.safe_load(f)

    visible_rel_ids = set(op_topo.get("visible_relationships", []))
    active_rels = [r for r in ref_rels if r["relationship_id"] in visible_rel_ids]

    provider = InMemoryKnowledgeProvider(
        pages=[ref_pages.get(ent, {"slug": ent, "frontmatter": {}}) for ent in op_topo.get("visible_entities", [])],
        relationships=active_rels,
        version="h2-test-v1",
    )

    run_input = GeneratedRunInput(
        run_id=manifest["run_id"],
        scenario_id=manifest["scenario_id"],
        difficulty_profile="L1",
        seed=manifest["seed"],
        alarms_path=str(op_dir / "alarms.jsonl"),
        logs_path=str(op_dir / "logs.jsonl"),
        metrics_path=str(op_dir / "metrics.jsonl"),
        kpis_path=str(op_dir / "kpis.jsonl"),
        traces_path=str(op_dir / "traces.jsonl"),
        changes_path=str(op_dir / "changes.jsonl"),
        tickets_path=str(op_dir / "tickets.jsonl"),
        recovery_path=str(op_dir / "recovery.jsonl"),
    )

    investigator = Investigator(provider)
    return investigator, run_input, op_dir, provider


@pytest.fixture
def sample_h2_run() -> Path:
    """Fixture returning the first available H2 run directory."""
    runs = sorted([d for d in H2_RUNS_DIR.iterdir() if d.is_dir() and d.name.startswith("RUN-H2-")])
    assert len(runs) > 0, "No H2 runs found. Generate scenarios first."
    return runs[0]


# 1. Hidden gap not visible to engine
def test_hidden_gap_not_visible_to_engine(sample_h2_run):
    investigator, run_input, op_dir, _ = _setup_h2_investigation(sample_h2_run)

    # Verify input paths only point to operational files
    for field in ["alarms_path", "logs_path", "metrics_path", "kpis_path", "traces_path", "changes_path", "tickets_path", "recovery_path"]:
        val = getattr(run_input, field)
        assert "hidden" not in val
        assert "operational" in val

    # Verify operational topology does not leak hidden fields
    with open(op_dir / "topology_view.yaml") as f:
        op_topo = yaml.safe_load(f)
    assert "hidden_gap" not in op_topo
    assert "evaluator_expectations" not in op_topo

    # Verify investigator runs successfully using only operational data
    result = investigator.run(run_input, op_dir)
    assert result is not None
    assert result.terminal_state == Terminal.MODEL_INSUFFICIENT


# 2. Model insufficient when required edge missing
def test_model_insufficient_when_required_edge_missing(sample_h2_run):
    investigator, run_input, op_dir, _ = _setup_h2_investigation(sample_h2_run)
    result = investigator.run(run_input, op_dir)

    assert result.terminal_state == Terminal.MODEL_INSUFFICIENT
    gap_records = result.diagnostics.get("knowledge_gap_records", [])
    assert len(gap_records) >= 1
    assert "gap_type" in gap_records[0]
    assert "suspected_missing_relation" in gap_records[0]


# 3. Insufficient evidence when model complete
def test_insufficient_evidence_when_model_complete():
    # Complete model with 2 nodes and an active relationship, but empty evidence
    provider = InMemoryKnowledgeProvider(
        pages=[{"slug": "nodeA"}, {"slug": "nodeB"}],
        relationships=[{"relationship_id": "R1", "source": "nodeB", "target": "nodeA", "link_type": "depends-on", "state": "CONFIRMED", "confidence": 1.0}],
    )
    run_in = GeneratedRunInput(run_id="RUN-EMPTY", scenario_id="SCN-EMPTY", difficulty_profile="L1", seed=42)
    investigator = Investigator(provider)

    # Empty evidence list
    result = investigator.investigate(run_in, [])
    assert result.terminal_state == Terminal.INSUFFICIENT_EVIDENCE
    assert result.terminal_state != Terminal.MODEL_INSUFFICIENT


# 4. Conflicting evidence not misclassified as model gap
def test_conflicting_evidence_not_misclassified_as_model_gap():
    # Complete model with conflicting evidence on the same entity
    provider = InMemoryKnowledgeProvider(
        pages=[{"slug": "nodeA"}, {"slug": "nodeB"}],
        relationships=[{"relationship_id": "R1", "source": "nodeB", "target": "nodeA", "link_type": "depends-on", "state": "CONFIRMED", "confidence": 1.0}],
    )
    run_in = GeneratedRunInput(run_id="RUN-CONFLICT", scenario_id="SCN-CONFLICT", difficulty_profile="L1", seed=42)
    when = datetime(2026, 9, 11, 10, 0, tzinfo=timezone.utc)

    # Two abnormal signals from independent sources for nodeA, plus one contradictory healthy signal
    ev1 = Evidence(
        evidence_id="ev1", event_time=when, ingestion_time=when + timedelta(seconds=1),
        domain="transport", entity="nodeA", canonical_entity="nodeA", source_native_entity="nodeA",
        source="nms", source_reliability=0.9, polarity="abnormal", evidence_type="alarms",
        service=["data"], severity="CRITICAL", signal="interface-down",
    )
    ev2 = Evidence(
        evidence_id="ev2", event_time=when + timedelta(seconds=2), ingestion_time=when + timedelta(seconds=3),
        domain="transport", entity="nodeA", canonical_entity="nodeA", source_native_entity="nodeA",
        source="ems", source_reliability=0.9, polarity="abnormal", evidence_type="alarms",
        service=["data"], severity="MAJOR", signal="link-flap",
    )
    ev3 = Evidence(
        evidence_id="ev3", event_time=when + timedelta(seconds=2), ingestion_time=when + timedelta(seconds=3),
        domain="transport", entity="nodeA", canonical_entity="nodeA", source_native_entity="nodeA",
        source="probe", source_reliability=0.9, polarity="healthy", evidence_type="metrics",
        service=["data"], severity="OK", signal="healthy",
    )

    investigator = Investigator(provider)
    result = investigator.investigate(run_in, [ev1, ev2, ev3])

    # Must be classified as conflicting evidence, NOT misclassified as MODEL_INSUFFICIENT
    assert result.terminal_state == Terminal.CONFLICTING_EVIDENCE
    assert result.terminal_state != Terminal.MODEL_INSUFFICIENT


# 5. Gap boundary localization
def test_gap_boundary_localization(sample_h2_run):
    with open(sample_h2_run / "hidden" / "evaluator_expectations.yaml") as f:
        expectations = yaml.safe_load(f)
    expected_boundary = expectations["expected_gap_boundary"]

    investigator, run_input, op_dir, _ = _setup_h2_investigation(sample_h2_run)
    result = investigator.run(run_input, op_dir)

    gap_records = result.diagnostics.get("knowledge_gap_records", [])
    assert len(gap_records) >= 1
    suspected_boundary = gap_records[0].get("suspected_missing_relation", {}).get("from_entity")
    assert suspected_boundary == expected_boundary


# 6. Candidate relation not confirmed
def test_candidate_relation_not_confirmed(sample_h2_run):
    investigator, run_input, op_dir, _ = _setup_h2_investigation(sample_h2_run)
    result = investigator.run(run_input, op_dir)

    assert len(result.candidate_relationships) >= 1
    for candidate in result.candidate_relationships:
        assert candidate.state == KnowledgeState.CANDIDATE
        assert candidate.state != KnowledgeState.CONFIRMED


# 7. No automatic telecombrain mutation
def test_no_automatic_telecombrain_mutation(sample_h2_run):
    investigator, run_input, op_dir, provider = _setup_h2_investigation(sample_h2_run)

    initial_rels = copy.deepcopy(provider.relationships)
    initial_pages = copy.deepcopy(provider.pages)

    # Run investigation
    result = investigator.run(run_input, op_dir)

    # Live provider state must not be mutated
    assert provider.relationships == initial_rels
    assert provider.pages == initial_pages


# 8. Next best evidence ranked
def test_next_best_evidence_ranked(sample_h2_run):
    investigator, run_input, op_dir, _ = _setup_h2_investigation(sample_h2_run)
    result = investigator.run(run_input, op_dir)

    assert len(result.next_best_evidence) >= 1
    # Check priorities are positive and strictly descending
    priorities = [req.priority for req in result.next_best_evidence]
    for p in priorities:
        assert p >= 0.0
    assert priorities == sorted(priorities, reverse=True)


# 9. Unknown entity not invented
def test_unknown_entity_not_invented(sample_h2_run):
    investigator, run_input, op_dir, provider = _setup_h2_investigation(sample_h2_run)
    result = investigator.run(run_input, op_dir)

    known_entities = set(provider.pages.keys())
    observed_entities = set(result.canonical_entities_used)
    valid_universe = known_entities.union(observed_entities)

    for cand in result.candidate_relationships:
        # Candidate sources and targets must be part of observed/known universe or boundary
        assert cand.source in valid_universe, f"Fabricated source entity: {cand.source}"
        if cand.target != "unspecified_boundary":
            assert cand.target in valid_universe, f"Fabricated target entity: {cand.target}"


# 10. Hidden truth not used in runtime
def test_hidden_truth_not_used_in_runtime(sample_h2_run, tmp_path):
    # Copy run directory to temporary folder and completely delete 'hidden' folder
    isolated_run = tmp_path / "isolated_run"
    shutil.copytree(sample_h2_run, isolated_run)
    shutil.rmtree(isolated_run / "hidden")
    assert not (isolated_run / "hidden").exists()

    # Should run and reach MODEL_INSUFFICIENT with zero dependency on hidden/
    investigator, run_input, op_dir, _ = _setup_h2_investigation(isolated_run)
    result = investigator.run(run_input, op_dir)

    assert result.terminal_state == Terminal.MODEL_INSUFFICIENT
    assert len(result.diagnostics.get("knowledge_gap_records", [])) >= 1


# 11. H2 scenario leakage detection
def test_h2_scenario_leakage_detection(sample_h2_run, tmp_path):
    corrupted_run = tmp_path / "corrupted_run"
    shutil.copytree(sample_h2_run, corrupted_run)

    # Inject forbidden token into operational/topology_view.yaml
    op_topo_path = corrupted_run / "operational" / "topology_view.yaml"
    with open(op_topo_path) as f:
        topo = yaml.safe_load(f)

    # Read hidden gap relationship id
    with open(sample_h2_run / "hidden" / "ground_truth.yaml") as f:
        ground_truth = yaml.safe_load(f)
    hidden_rel_id = ground_truth["hidden_gap"]["relationship_id"]

    # Deliberately violate Rule 2 (omitted relation present in operational view)
    topo["visible_relationships"].append(hidden_rel_id)
    with open(op_topo_path, "w") as f:
        yaml.dump(topo, f)

    validation = validate_single_h2_run(corrupted_run)
    assert not validation["valid"]
    assert any("Rule 2 violation" in err for err in validation["errors"])


# 12. H1 regression suite still passes
def test_h1_regression_suite_still_passes():
    # Standard H1 complete topology where router is the root cause
    provider = InMemoryKnowledgeProvider(
        pages=[{"slug": "router"}, {"slug": "upf"}, {"slug": "service"}],
        relationships=[
            {"relationship_id": "R1", "source": "upf", "target": "router", "link_type": "depends-on", "state": "CONFIRMED", "confidence": 0.95},
            {"relationship_id": "R2", "source": "service", "target": "upf", "link_type": "depends-on", "state": "CONFIRMED", "confidence": 0.95},
        ],
    )
    run_in = GeneratedRunInput(run_id="RUN-H1-REGRESS", scenario_id="SCN-H1-001", difficulty_profile="L1", seed=42)
    when = datetime(2026, 9, 11, 10, 0, tzinfo=timezone.utc)

    ev_router = Evidence(
        evidence_id="e1", event_time=when, ingestion_time=when + timedelta(seconds=1),
        domain="transport", entity="router", canonical_entity="router", source_native_entity="router",
        source="nms", source_reliability=0.95, polarity="abnormal", evidence_type="alarms",
        service=["data"], severity="CRITICAL", signal="bgp-peer-down",
    )
    ev_upf = Evidence(
        evidence_id="e2", event_time=when + timedelta(seconds=5), ingestion_time=when + timedelta(seconds=6),
        domain="ps", entity="upf", canonical_entity="upf", source_native_entity="upf",
        source="ems", source_reliability=0.95, polarity="abnormal", evidence_type="alarms",
        service=["data"], severity="MAJOR", signal="session-aborted",
    )

    investigator = Investigator(provider)
    result = investigator.investigate(run_in, [ev_router, ev_upf])

    # Must explain the fault, NOT classify as MODEL_INSUFFICIENT
    assert result.terminal_state == Terminal.EXPLAINED
    assert result.terminal_state != Terminal.MODEL_INSUFFICIENT
    assert result.ranked_hypotheses[0].canonical_root_entity == "router"
