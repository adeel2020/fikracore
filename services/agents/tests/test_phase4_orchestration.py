"""
Unit and Integration Tests for Phase 4 Engine Orchestration & Ingestion Bridge
=============================================================================
Tests:
1. EmergingEvidenceFilter: Sliding window weak-signal correlation & graduation.
2. DiscriminationProbeDispatcher: Step 3 active discrimination testing & ValidatedEvidenceContract generation.
3. TaskEpisodeContract Dynamic Spine: End-to-end investigation anchored in TaskEpisode.
4. KnowledgePromotionService: 8 Guardrails, recurrence criteria, domain jurisdiction check, and reversible rollback.
5. Gbrain4PlaneMCPClient: 4-Plane typed MCP queries and mutations.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from engine_stack.engines.telecom_brain.capabilities.tool_registry import (
    ActionSafetyTier,
    AuthorityLevel,
    DomainCode,
    DomainToolRegistry,
)
from engine_stack.engines.telecom_brain.capabilities.probe_dispatcher import (
    DiscriminationProbeDispatcher,
)
from engine_stack.engines.telecom_brain.investigation.contracts import (
    Evidence,
    GeneratedRunInput,
    RawEvidenceContract,
    EmergingEvidenceContract,
    ValidatedEvidenceContract,
    InvestigationHypothesis,
    KnowledgePromotionState,
    PromotionRecord,
    ValidationDecisionType,
    ValidationRecord,
)
from engine_stack.engines.telecom_brain.investigation.knowledge import InMemoryKnowledgeProvider
from engine_stack.engines.telecom_brain.learning.promotion_service import (
    KnowledgePromotionService,
)
from engine_stack.engines.telecom_brain.services.emerging_filter import (
    EmergingEvidenceFilter,
)
from engine_stack.engines.telecom_brain.services.gbrain_mcp_client import (
    Gbrain4PlaneMCPClient,
)

from zaki.contracts.task_episode import TaskEpisodeContract
from zaki.governance.validation import HumanValidationContract
from zaki.enums import AuthorityLevel as ZakiAuthorityLevel
from zaki.fikracore.adapter import FikraCoreAdapter
from zaki.runtime.orchestrator import ZakiOrchestrator


# ── 1. Emerging Evidence Filter Tests ─────────────────────────────────────────

def test_emerging_evidence_filter_escalation_and_graduation():
    """Verify EmergingEvidenceFilter aggregates weak signals, computes trend, and graduates to Evidence."""
    filter_svc = EmergingEvidenceFilter(
        window_duration_seconds=300,
        weak_signal_threshold=2,
        anomaly_threshold=3,
        candidate_incident_threshold=4,
    )

    base_time = datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc)
    events = [
        RawEvidenceContract(
            telemetry_id="RAW-01",
            event_time=base_time,
            stream_source="gnmi",
            raw_payload={
                "domain": "IP_TRANSPORT",
                "entity": "router-agg-01",
                "signal": "crc_error_rate_drift",
                "severity": "INFO",
                "value": 12.0,
                "baseline_value": 0.0,
            },
        ),
        RawEvidenceContract(
            telemetry_id="RAW-02",
            event_time=base_time + timedelta(seconds=30),
            stream_source="gnmi",
            raw_payload={
                "domain": "IP_TRANSPORT",
                "entity": "router-agg-01",
                "signal": "crc_error_rate_drift",
                "severity": "WARN",
                "value": 45.0,
                "baseline_value": 0.0,
            },
        ),
        RawEvidenceContract(
            telemetry_id="RAW-03",
            event_time=base_time + timedelta(seconds=60),
            stream_source="gnmi",
            raw_payload={
                "domain": "IP_TRANSPORT",
                "entity": "router-agg-01",
                "signal": "crc_error_rate_drift",
                "severity": "WARNING",
                "value": 110.0,
                "baseline_value": 0.0,
            },
        ),
        RawEvidenceContract(
            telemetry_id="RAW-04",
            event_time=base_time + timedelta(seconds=90),
            stream_source="gnmi",
            raw_payload={
                "domain": "IP_TRANSPORT",
                "entity": "router-agg-01",
                "signal": "crc_error_rate_drift",
                "severity": "MINOR",
                "value": 250.0,
                "baseline_value": 0.0,
            },
        ),
    ]

    detected = filter_svc.process_batch(events)
    assert len(detected) >= 1

    cond = detected[0]
    assert cond.domain == "IP_TRANSPORT"
    assert cond.target_entity == "router-agg-01"
    assert cond.aggregated_signal_count == 4
    assert cond.severity_trend == "ESCALATING"
    assert cond.operational_significance == "PRE_INCIDENT_CANDIDATE"

    # Graduate to canonical Evidence
    evidence = filter_svc.graduate_to_evidence(cond, canonical_entity_slug="router-agg-01")
    assert isinstance(evidence, Evidence)
    assert evidence.domain == "IP_TRANSPORT"
    assert evidence.canonical_entity == "router-agg-01"
    assert evidence.polarity == "abnormal"
    assert evidence.severity == "PRE_INCIDENT_CANDIDATE"


def test_emerging_evidence_filter_rejects_hidden_truth():
    """Verify evaluator-only hidden reality fields are strictly rejected upon ingestion."""
    filter_svc = EmergingEvidenceFilter()
    bad_event = {
        "event_time": datetime.now(timezone.utc),
        "domain": "IP_TRANSPORT",
        "entity": "router-01",
        "hidden_truth": "actual_root_cause_optic_failure",
    }
    with pytest.raises(ValueError, match="forbidden"):
        filter_svc.process_event(bad_event)


# ── 2. Discrimination Probe Dispatcher Tests ─────────────────────────────────

def test_discrimination_probe_dispatcher_active_testing():
    """Verify Step 3 active discrimination executes diagnostic probe and generates ValidatedEvidenceContract."""
    dispatcher = DiscriminationProbeDispatcher()

    h1 = InvestigationHypothesis(
        hypothesis_id="HYP-01",
        statement="Optical transceiver link degradation on router-agg-01",
        candidate_root_domain="IP_TRANSPORT",
        candidate_root_entity="router-agg-01",
        canonical_root_entity="router-agg-01",
        root_entities=["router-agg-01"],
        causal_role="ROOT",
        assumptions=[],
        expected_observations=["crc_errors"],
        supporting_evidence=["EV-01"],
        contradicting_evidence=[],
        missing_evidence=["probe.query_crc_counters"],
        knowledge_relationships_used=[],
        status="CANDIDATE",
        hypothesis_confidence=0.75,
        causal_confidence=0.75,
        explanation_coverage=0.8,
        score_dimensions={"topology": 0.8},
    )

    h2 = InvestigationHypothesis(
        hypothesis_id="HYP-02",
        statement="BGP session flap on router-agg-01",
        candidate_root_domain="IP_TRANSPORT",
        candidate_root_entity="router-agg-01",
        canonical_root_entity="router-agg-01",
        root_entities=["router-agg-01"],
        causal_role="ROOT",
        assumptions=[],
        expected_observations=["bgp_down"],
        supporting_evidence=["EV-02"],
        contradicting_evidence=[],
        missing_evidence=["probe.check_bgp_session"],
        knowledge_relationships_used=[],
        status="CANDIDATE",
        hypothesis_confidence=0.70,
        causal_confidence=0.70,
        explanation_coverage=0.7,
        score_dimensions={"topology": 0.7},
    )

    result = dispatcher.run_discrimination_cycle(hypotheses=[h1, h2], max_probes=2)
    assert result["discrimination_status"] == "COMPLETED"
    assert len(result["probes_dispatched"]) >= 1
    assert len(result["validated_evidence"]) >= 1

    val_ev = result["validated_evidence"][0]
    assert val_ev["verdict"] in ("SUPPORTS", "CONTRADICTS", "CONFIRMS", "RULES_OUT")
    assert val_ev["canonical_entity"] == "router-agg-01"


# ── 3. Dynamic Task Episode Spine Tests ──────────────────────────────────────

def test_task_episode_spine_orchestrator_integration():
    """Verify ZakiOrchestrator initializes and populates TaskEpisodeContract across investigation."""
    pages = [{"slug": "router"}, {"slug": "upf"}]
    relationships = [{"relationship_id": "R1", "source": "upf", "target": "router", "link_type": "depends-on", "state": "CONFIRMED", "confidence": 0.95}]
    provider = InMemoryKnowledgeProvider(pages, relationships)

    ev_list = [
        Evidence(
            evidence_id="E1",
            event_time=datetime(2026, 9, 10, 8, 0, 0, tzinfo=timezone.utc),
            ingestion_time=datetime(2026, 9, 10, 8, 0, 5, tzinfo=timezone.utc),
            domain="transport",
            entity="router",
            canonical_entity="router",
            source_native_entity="router",
            source="nms",
            source_reliability=0.9,
            polarity="abnormal",
            evidence_type="alarms",
            service=["mobile-data"],
            severity="CRITICAL",
            signal="interface-down",
        ),
        Evidence(
            evidence_id="E2",
            event_time=datetime(2026, 9, 10, 8, 0, 1, tzinfo=timezone.utc),
            ingestion_time=datetime(2026, 9, 10, 8, 0, 5, tzinfo=timezone.utc),
            domain="ps",
            entity="upf",
            canonical_entity="upf",
            source_native_entity="upf",
            source="ems",
            source_reliability=0.9,
            polarity="abnormal",
            evidence_type="alarms",
            service=["mobile-data"],
            severity="MAJOR",
            signal="session-drops",
        ),
    ]

    run_input = GeneratedRunInput(run_id="RUN-SPINE-01", scenario_id="SCN-001", difficulty_profile="L1", seed=42)
    adapter = FikraCoreAdapter(provider=provider)
    orchestrator = ZakiOrchestrator(fikracore_adapter=adapter)

    res = orchestrator.investigate(
        intent_or_query="Investigate edge router and UPF failure",
        run_input=run_input,
        evidence=ev_list,
        provider=provider,
    )

    episode = res.get("episode")
    assert isinstance(episode, TaskEpisodeContract)
    assert episode.task_id.startswith("TASK-")
    assert episode.incident_id.startswith("INC-")
    assert episode.operator_intent == "Investigate edge router and UPF failure"
    assert episode.operational_context_ref == f"CTX-{episode.task_id}"
    assert episode.behavior_contract_ref == "BEHAVIOR-NOC-SME-DEFAULT"
    assert len(episode.ranked_hypotheses) > 0
    assert episode.closed_at is not None
    assert episode.outcome is not None


# ── 4. Knowledge Promotion Service & 8 Guardrails Tests ───────────────────────

def test_knowledge_promotion_domain_jurisdiction_and_reversibility():
    """Verify KnowledgePromotionService enforces domain jurisdiction and supports rollback."""
    pages = [{"slug": "pe-rtr-01"}, {"slug": "upf-edge-01"}]
    provider = InMemoryKnowledgeProvider(pages, [])
    promo_svc = KnowledgePromotionService(min_recurrence_threshold=1)

    # 1. Register candidate
    cand_id = "CAND-REL-TRANSPORT-001"
    promo_svc.register_candidate(
        candidate_id=cand_id,
        relationship={"source": "pe-rtr-01", "target": "upf-edge-01", "link_type": "routes-through"},
        domain="IP_TRANSPORT",
        originating_episode_id="EP-101",
        supporting_evidence_ids=["EV-01"],
    )

    # 2. Reject Cross-Domain Approval (e.g. RAN SME validating IP_TRANSPORT relation)
    invalid_validation = {
        "validation_id": "VAL-001",
        "candidate_id": cand_id,
        "decision": "ACCEPT",
        "validated_by_role": "RAN Optimization Lead",
        "reason": "Looks good from cell tower perspective",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    success, record, errors = promo_svc.validate_and_promote(
        candidate_id=cand_id,
        validation=invalid_validation,
        provider=provider,
        validator_domain="RAN",
    )
    assert not success
    assert any("Domain Jurisdiction Violation" in err for err in errors)

    # 3. Accept Valid Domain Approval (IP_TRANSPORT SME)
    valid_validation = {
        "validation_id": "VAL-002",
        "candidate_id": cand_id,
        "decision": "ACCEPT",
        "validated_by_role": "IP Transport Desk Lead",
        "reason": "Confirmed BGP and MPLS tunnel routes through PE router",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    success, record, errors = promo_svc.validate_and_promote(
        candidate_id=cand_id,
        validation=valid_validation,
        provider=provider,
        validator_domain="IP_TRANSPORT",
    )
    assert success
    assert record is not None
    assert record.status == KnowledgePromotionState.PROMOTED

    # Verify edge was inserted into canonical provider
    assert any(e.get("target") == "upf-edge-01" for e in provider.relationships)

    # 4. Test Reversibility (Rollback)
    rollback_success, msg = promo_svc.rollback_promotion(record.promotion_id, provider)
    assert rollback_success
    assert not any(e.get("target") == "upf-edge-01" for e in provider.relationships)


# ── 5. Gbrain 4-Plane Client Tests ───────────────────────────────────────────

def test_gbrain_4plane_client_methods():
    """Verify 4-Plane typed methods for topology, incidents, episodes, and knowledge."""
    client = Gbrain4PlaneMCPClient()

    # Plane 1: Topology & Redundancy
    topo = client.get_topology(node_id="pe-router-01", depth=2)
    assert "pe-router-01" in topo["nodes"]
    redundant = client.get_redundant_paths("pe-router-01")
    assert isinstance(redundant, list)

    # Plane 2: Incident & Blast Radius
    blast = client.get_blast_radius(
        incident_id="INC-001",
        affected_nodes=["pe-router-01", "pe-router-02"]
    )
    assert len(blast.directly_affected_entities) == 2
    assert blast.blast_radius_level.value in ("LOCAL", "DOMAIN", "MULTI_DOMAIN", "REGIONAL", "NETWORK_WIDE")

    # Plane 3: Episode Lifecycle
    episode_payload = {
        "episode_id": "EP-TEST-001",
        "task_id": "TASK-001",
        "incident_id": "INC-001",
        "operator_intent": "Resolve packet loss",
        "outcome": "SUCCESS",
    }
    ep_id = client.record_episode(episode_payload)
    assert ep_id == "EP-TEST-001"
    fetched_ep = client.get_episode_state("EP-TEST-001")
    assert fetched_ep is not None
    assert fetched_ep["outcome"] == "SUCCESS"

    # Plane 4: Patterns & Playbooks
    patterns = client.find_patterns(symptom_vector={"crc": True}, domains=["IP_TRANSPORT"])
    assert len(patterns) >= 1
    assert "IP_TRANSPORT" in patterns[0]["domains"]
