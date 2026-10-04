"""
Unit Tests for FikraCore Sanity Validators (S1–S11)
===================================================
Certifies all cross-cutting invariant checks defined in:
docs/Reasoning_Contracts/FikraCore_Sanity_Checks_and_Runtime_Rules.md
"""

from datetime import datetime, timedelta, timezone
import pytest

from engine_stack.engines.telecom_brain.investigation.sanity import (
    SanityOutcome,
    SanityCategory,
    StructuralValidator,
    ReferenceIntegrityValidator,
    TemporalConsistencyValidator,
    LifecycleIntegrityValidator,
    SemanticSeparationValidator,
    TopologyIntegrityValidator,
    CausalityIntegrityValidator,
    AuthorityIntegrityValidator,
    KnowledgeIntegrityValidator,
    IndexIntegrityValidator,
    OracleIsolationValidator,
    run_all_sanity_checks,
)
from zaki.contracts.operational_context import OperationalContextContract
from zaki.contracts.task_episode import TaskEpisodeContract


def test_s1_structural_valid():
    """Verify S1 Structural Integrity passes on valid contract."""
    ctx = OperationalContextContract(
        scenario_id="SCN-001",
        primary_domain="IP_TRANSPORT",
        visible_entities=["router-01", "router-02"],
    )
    val = StructuralValidator()
    results = val.validate(ctx)
    assert any(r.outcome == SanityOutcome.PASS for r in results)
    assert not any(r.outcome == SanityOutcome.BLOCK for r in results)


def test_s1_structural_duplicates_warn():
    """Verify S1 Structural Integrity warns on duplicate items in collections."""
    data = {
        "kind": "TaskEpisode",
        "episode_id": "EP-001",
        "domains": ["IP_TRANSPORT", "IP_TRANSPORT"],
    }
    val = StructuralValidator()
    results = val.validate(data)
    assert any(r.outcome == SanityOutcome.WARN and "Duplicate" in r.message for r in results)


def test_s2_reference_dangling_blocks():
    """Verify S2 blocks dangling operational context reference."""
    episode = {
        "kind": "TaskEpisode",
        "episode_id": "EP-100",
        "operational_context_ref": "CTX-NONEXISTENT",
    }
    val = ReferenceIntegrityValidator()
    context = {"known_contexts": {"CTX-001", "CTX-002"}}
    results = val.validate(episode, context=context)
    assert any(r.outcome == SanityOutcome.BLOCK and "Dangling" in r.message for r in results)


def test_s3_temporal_inversion_blocks():
    """Verify S3 blocks temporal inversion (closed_at before created_at)."""
    now = datetime.now(timezone.utc)
    episode = {
        "kind": "TaskEpisode",
        "episode_id": "EP-200",
        "created_at": now.isoformat(),
        "closed_at": (now - timedelta(minutes=10)).isoformat(),
    }
    val = TemporalConsistencyValidator()
    results = val.validate(episode)
    assert any(r.outcome == SanityOutcome.BLOCK and "inversion" in r.message for r in results)


def test_s4_lifecycle_illegal_transition_blocks():
    """Verify S4 blocks illegal hypothesis jump from PROPOSED to CONFIRMED."""
    hyp = {
        "kind": "Hypothesis",
        "hypothesis_id": "HYP-001",
        "status": "CONFIRMED",
    }
    val = LifecycleIntegrityValidator()
    results = val.validate(hyp, context={"previous_status": "PROPOSED"})
    assert any(r.outcome == SanityOutcome.BLOCK for r in results)


def test_s5_semantic_separation_blocks_raw_rca():
    """Verify S5 blocks raw telemetry declaring confirmed root cause."""
    raw = {
        "kind": "RawTelemetry",
        "telemetry_id": "RAW-001",
        "signal": "n3_packet_drop_ratio",
        "value": 0.15,
        "root_cause": "Transport SFP failure",
    }
    val = SemanticSeparationValidator()
    results = val.validate(raw)
    assert any(r.outcome == SanityOutcome.BLOCK and "cannot declare 'root_cause'" in r.message for r in results)


def test_s6_topology_missing_endpoints_blocks():
    """Verify S6 blocks topology relationship with missing endpoints."""
    rel = {
        "relationship": {
            "source": "router-01",
            "target": None,
            "predicate": "CONNECTS_TO",
        }
    }
    val = TopologyIntegrityValidator()
    results = val.validate(rel)
    assert any(r.outcome == SanityOutcome.BLOCK for r in results)


def test_s7_causality_unresolved_contradiction_blocks():
    """Verify S7 blocks hypothesis confirmation when contradictory evidence exists."""
    hyp = {
        "kind": "Hypothesis",
        "hypothesis_id": "HYP-001",
        "status": "CONFIRMED",
        "supporting_evidence": ["EV-001"],
        "contradictory_evidence": ["EV-002"],
    }
    val = CausalityIntegrityValidator()
    results = val.validate(hyp)
    assert any(r.outcome == SanityOutcome.BLOCK and "contradictory evidence exists" in r.message for r in results)


def test_s8_authority_disruptive_autonomous_blocks():
    """Verify S8 blocks disruptive action without HITL approval."""
    action = {
        "id": "ACT-001",
        "action_type": "TRAFFIC_REROUTE",
        "autonomous": True,
        "hitl_validated": False,
    }
    val = AuthorityIntegrityValidator()
    results = val.validate(action)
    assert any(r.outcome == SanityOutcome.BLOCK and "without explicit HITL approval" in r.message for r in results)


def test_s9_knowledge_insufficient_recurrence_blocks():
    """Verify S9 blocks pattern promotion with recurrence count < 2."""
    pattern = {
        "pattern_id": "PAT-001",
        "status": "PROMOTED",
        "recurrence_count": 1,
        "observed_episodes": ["EP-001"],
    }
    val = KnowledgeIntegrityValidator()
    results = val.validate(pattern)
    assert any(r.outcome == SanityOutcome.BLOCK and "insufficient empirical recurrence" in r.message for r in results)


def test_s10_index_heavy_payload_warns():
    """Verify S10 warns if an index entry contains full semantic body."""
    index_entry = {
        "kind": "IncidentIndexEntry",
        "id": "INC-001",
        "executive_summary": "Extensive paragraph describing the entire outage in detail...",
    }
    val = IndexIntegrityValidator()
    results = val.validate(index_entry)
    assert any(r.outcome == SanityOutcome.WARN and "duplicates heavy semantic body" in r.message for r in results)


def test_s11_oracle_leakage_hard_blocks():
    """Verify S11 hard BLOCKS on any hidden simulation ground truth leakage."""
    leaked_payload = {
        "visible_metrics": {"loss": 0.05},
        "debug_info": {
            "hidden_truth": {
                "root_entity": "UPF-01",
                "root_condition": "FIBER_CUT",
            }
        },
    }
    val = OracleIsolationValidator()
    results = val.validate(leaked_payload)
    assert any(r.outcome == SanityOutcome.BLOCK and "Hard Epistemic Violation" in r.message for r in results)


def test_run_all_sanity_checks_fail_on_block():
    """Verify run_all_sanity_checks raises ValueError when fail_on_block=True on violation."""
    bad_data = {
        "kind": "RawEvidence",
        "root_cause": "Forbidden early RCA",
    }
    with pytest.raises(ValueError) as excinfo:
        run_all_sanity_checks(bad_data, fail_on_block=True)
    assert "Sanity Check BLOCK" in str(excinfo.value)
