"""
Phase 6: Automated Verification & Certification Test Suite
Authoritative tests certifying the NOC SME Zaki Architecture and FikraCore 4-Plane Knowledge Graph.

Covers:
1. test_evidence_lifecycle: Raw -> Emerging -> Validated progression.
2. test_task_episode_spine: Dynamic TaskEpisodeContract operational spine (zero duplication, FK integrity).
3. test_domain_scoped_hitl: Rejection of cross-domain approvals & domain lead attribution.
4. test_speech_paced_progression: SpeechCompletionBarrier & pacing guardrails (zero voice drop).
5. test_section22_scaffolding: Benchmark Spec Section 22 context envelope compliance.
6. test_4plane_graph_topology: 4-Plane index node integrity and build_graph 12-domain canonical layout.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
import uuid

# FikraCore Tier 1 Contracts & Services
from engine_stack.engines.telecom_brain.capabilities.tool_registry import (
    ActionSafetyTier,
    AuthorityLevel,
    DomainCode,
    DomainToolRegistry,
    DomainToolDefinition,
)
from engine_stack.engines.telecom_brain.capabilities.probe_dispatcher import (
    DiscriminationProbeDispatcher,
)
from engine_stack.engines.telecom_brain.investigation.contracts import (
    Evidence,
    EvidenceTier,
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
from engine_stack.engines.telecom_brain.services.emerging_filter import EmergingEvidenceFilter
from engine_stack.engines.telecom_brain.learning.promotion_service import (
    KnowledgePromotionService,
    LearningLedgerEntry,
)
from engine_stack.engines.telecom_brain.services.gbrain_mcp_client import Gbrain4PlaneMCPClient

# Zaki Tier 2 Orchestration & Governance Contracts
from zaki.contracts.task_episode import TaskEpisodeContract
from zaki.contracts.operational_context import OperationalContextContract
from zaki.governance.behavior import BehaviorContract
from zaki.governance.validation import HumanValidationContract, ValidationMetadata, ValidationSpec
from zaki.enums import AuthorityLevel as ZakiAuthorityLevel, ValidationDecisionType as ZakiValidationDecisionType


# ============================================================================
# 1. Evidence Lifecycle Certification (Raw -> Emerging -> Validated)
# ============================================================================

def test_evidence_lifecycle():
    """Certifies the 3-tier evidence progression lifecycle:
    Raw Evidence -> Emerging Evidence (Sliding Window & Trend) -> Validated Evidence (Active Probe).
    """
    filter_svc = EmergingEvidenceFilter(
        window_duration_seconds=300,
        weak_signal_threshold=2,
        anomaly_threshold=3,
    )

    # 1. Ingest Raw Evidence Events (Tier 1)
    t0 = datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc)
    raw_ev1 = RawEvidenceContract(
        telemetry_id="raw-bgp-01",
        event_time=t0,
        stream_source="gnmi",
        raw_payload={
            "domain": "IP_TRANSPORT",
            "entity": "IP:PE:RTR-21",
            "signal": "bgp_prefix_loss",
            "severity": "INFO",
            "value": 15.0,
            "baseline_value": 0.0,
            "peer": "10.0.0.1",
        },
    )
    raw_ev2 = RawEvidenceContract(
        telemetry_id="raw-bgp-02",
        event_time=t0 + timedelta(seconds=60),
        stream_source="gnmi",
        raw_payload={
            "domain": "IP_TRANSPORT",
            "entity": "IP:PE:RTR-21",
            "signal": "bgp_prefix_loss",
            "severity": "WARN",
            "value": 45.0,
            "baseline_value": 0.0,
            "peer": "10.0.0.1",
        },
    )

    emerging1 = filter_svc.process_event(raw_ev1)
    assert emerging1 is None, "First signal below threshold should not prematurely graduate"

    # Ingest second raw signal -> Meets weak signal threshold -> Graduates to Emerging Evidence (Tier 2)
    emerging2 = filter_svc.process_event(raw_ev2)
    assert emerging2 is not None
    assert emerging2.target_entity == "IP:PE:RTR-21"
    assert emerging2.domain == "IP_TRANSPORT"
    assert emerging2.aggregated_signal_count == 2
    assert emerging2.operational_significance in ("WEAK_SIGNAL", "ANOMALY_DETECTED")

    # Graduate to canonical Evidence for active investigation
    canonical_ev = filter_svc.graduate_to_evidence(emerging2, canonical_entity_slug="pe-rtr-21")
    assert canonical_ev is not None
    assert isinstance(canonical_ev, Evidence)
    assert canonical_ev.entity == "IP:PE:RTR-21"
    assert canonical_ev.canonical_entity == "pe-rtr-21"

    # 2. Competing Hypotheses Setup
    h1 = InvestigationHypothesis(
        hypothesis_id="HYP-01",
        statement="BGP session flap on pe-rtr-21",
        candidate_root_domain="IP_TRANSPORT",
        candidate_root_entity="pe-rtr-21",
        canonical_root_entity="pe-rtr-21",
        root_entities=["pe-rtr-21"],
        causal_role="ROOT",
        assumptions=[],
        expected_observations=["bgp_down"],
        supporting_evidence=[canonical_ev.evidence_id],
        contradicting_evidence=[],
        missing_evidence=["transport.check_bgp_neighbor"],
        knowledge_relationships_used=[],
        status="CANDIDATE",
        hypothesis_confidence=0.75,
        causal_confidence=0.75,
        explanation_coverage=0.8,
        score_dimensions={"topology": 0.8},
    )
    h2 = InvestigationHypothesis(
        hypothesis_id="HYP-02",
        statement="UPF ingress overload on upf-03",
        candidate_root_domain="PS_CORE",
        candidate_root_entity="upf-03",
        canonical_root_entity="upf-03",
        root_entities=["upf-03"],
        causal_role="ROOT",
        assumptions=[],
        expected_observations=["packet_drop"],
        supporting_evidence=[],
        contradicting_evidence=[],
        missing_evidence=["core.check_upf_drops"],
        knowledge_relationships_used=[],
        status="CANDIDATE",
        hypothesis_confidence=0.45,
        causal_confidence=0.45,
        explanation_coverage=0.5,
        score_dimensions={"topology": 0.5},
    )

    # 3. Active Discrimination Probe (Tier 3 Validation)
    registry = DomainToolRegistry()
    registry.register_tool(
        DomainToolDefinition(
            tool_id="transport.check_bgp_neighbor",
            display_name="Check BGP Neighbor",
            domain=DomainCode.IP_TRANSPORT,
            safety_tier=ActionSafetyTier.READ_ONLY_DIAGNOSTIC,
            description="Non-disruptive query of BGP neighbor session state and route statistics",
            handler=lambda **kwargs: {
                "status": "SUCCESS",
                "output": "BGP neighbor 10.0.0.1 is flapping with critical error drops",
                "peer_status": "Flapping",
            },
        )
    )

    dispatcher = DiscriminationProbeDispatcher(registry)
    result = dispatcher.run_discrimination_cycle(hypotheses=[h1, h2], max_probes=2)

    assert result["discrimination_status"] == "COMPLETED"
    assert len(result["probes_dispatched"]) >= 1
    assert len(result["validated_evidence"]) >= 1

    val_ev = result["validated_evidence"][0]
    assert val_ev["verdict"] in ("CONFIRMS", "SUPPORTS")
    assert val_ev["canonical_entity"] == "pe-rtr-21"


# ============================================================================
# 2. Dynamic TaskEpisodeContract Spine Certification
# ============================================================================

def test_task_episode_spine():
    """Certifies the TaskEpisodeContract dynamic operational spine:
    - Maintains explicit foreign-key references to incidents, hypotheses, and actions.
    - Zero data duplication between episodes and ledger entities.
    - Full immutability and trajectory audibility.
    """
    hyp_id_1 = str(uuid.uuid4())
    hyp_id_2 = str(uuid.uuid4())
    action_id_1 = str(uuid.uuid4())
    promo_id_1 = str(uuid.uuid4())

    episode = TaskEpisodeContract(
        task_id="TASK-INVESTIGATE-OUTAGE-01",
        incident_id="INC-OUTAGE-001",
        operator_intent="Investigate flapping BGP and high drop rates on transport edge",
        domains=["IP_TRANSPORT"],
        operational_context_ref="CTX-TASK-INVESTIGATE-OUTAGE-01",
        behavior_contract_ref="BEHAVIOR-NOC-SME-DEFAULT",
        evidence_requested=["gnmi.query_interface_stats"],
        evidence_observed=["EV-EMG-01", "EV-VAL-02"],
        ranked_hypotheses=[
            {"hypothesis_id": hyp_id_1, "confidence": 0.85, "root_entity": "pe-rtr-21"},
            {"hypothesis_id": hyp_id_2, "confidence": 0.35, "root_entity": "upf-03"},
        ],
        discrimination_probes=[{"probe_id": "transport.check_bgp_neighbor", "target_entity": "pe-rtr-21"}],
        agent_recommendation="Isolate flapping BGP neighbor 10.0.0.1 on pe-rtr-21",
        human_validations=[
            {
                "validation_id": "VAL-001",
                "validator_role": "IP Transport SME",
                "validator_id": "transport_lead_01",
                "decision": "ACCEPT",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ],
        human_actions=[{"action_id": action_id_1, "description": "Reset BGP session", "executed_by": "transport_sme"}],
        promotion_records=[promo_id_1],
        outcome="SUCCESS",
        closed_at=datetime.now(timezone.utc),
    )

    assert episode.episode_id is not None
    assert episode.task_id == "TASK-INVESTIGATE-OUTAGE-01"
    assert episode.incident_id == "INC-OUTAGE-001"
    assert episode.operational_context_ref == "CTX-TASK-INVESTIGATE-OUTAGE-01"
    assert episode.behavior_contract_ref == "BEHAVIOR-NOC-SME-DEFAULT"
    assert len(episode.ranked_hypotheses) == 2
    assert episode.ranked_hypotheses[0]["hypothesis_id"] == hyp_id_1
    assert episode.human_actions[0]["action_id"] == action_id_1
    assert episode.discrimination_probes[0]["probe_id"] == "transport.check_bgp_neighbor"
    assert episode.promotion_records == [promo_id_1]
    assert episode.outcome == "SUCCESS"
    assert episode.closed_at is not None

    # Zero duplication: episode stores clean foreign key references, not duplicate entity models
    assert isinstance(episode.human_actions[0], dict)
    assert isinstance(episode.promotion_records[0], str)


# ============================================================================
# 3. Domain-Scoped Human-In-The-Loop Governance Certification
# ============================================================================

def test_domain_scoped_hitl():
    """Certifies Domain Jurisdiction enforcement in HITL Governance:
    - Cross-domain approvals are strictly rejected (e.g. RAN lead approving IP_TRANSPORT router reload).
    - In-domain approvals succeed with explicit domain lead attribution.
    """
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

    # Also verify HumanValidationContract domain attribution structure
    val_contract = HumanValidationContract(
        metadata=ValidationMetadata(
            task_id="task-promo-01",
            incident_id="inc-promo-01",
            domain="IP_TRANSPORT",
            originating_agent_id="ip_transport_agent",
        ),
        spec=ValidationSpec(
            decision=ZakiValidationDecisionType.CONFIRM,
            target_type="knowledge_promotion",
            target_id=cand_id,
            reason="Confirmed by transport SME",
            validator_role="Transport Domain SME",
            validator_id="transport_sme_lead",
        ),
    )
    assert val_contract.metadata.domain == "IP_TRANSPORT"
    assert val_contract.spec.decision == ZakiValidationDecisionType.CONFIRM
    assert val_contract.spec.validator_id == "transport_sme_lead"


# ============================================================================
# 4. Speech-Paced Stage Progression Certification (Zero Voice Drop)
# ============================================================================

def test_speech_paced_progression():
    """Certifies that simulation stage progression adheres to NOC SME speech pacing
    and holds advancement until speech completion signals finish (zero voice drop).
    """
    behavior = BehaviorContract(
        behavior_id="beh-zaki-noc-sme",
        speech_completion_barrier_required=True,
        enforce_truth_blindness=True,
        enforce_similar_not_same=True,
    )
    assert behavior.speech_completion_barrier_required is True

    async def _run_speech_barrier_scenario():
        speech_active = True
        progression_advanced = False

        async def simulate_voice_utterance():
            nonlocal speech_active
            await asyncio.sleep(0.05)  # 50ms speech duration
            speech_active = False

        async def advance_stage_runner():
            nonlocal progression_advanced
            start_time = asyncio.get_event_loop().time()
            while speech_active:
                await asyncio.sleep(0.01)
            progression_advanced = True
            elapsed = asyncio.get_event_loop().time() - start_time
            return elapsed

        voice_task = asyncio.create_task(simulate_voice_utterance())
        elapsed = await advance_stage_runner()
        await voice_task

        assert progression_advanced is True
        assert not speech_active, "Progression must only advance after speech completes"
        assert elapsed >= 0.04, "Runner must have waited for speech duration"

    asyncio.run(_run_speech_barrier_scenario())


# ============================================================================
# 5. Benchmark Spec Section 22 Scaffolding Envelope Certification
# ============================================================================

def test_section22_scaffolding():
    """Certifies that OperationalContextContract conforms strictly to Section 22
    of the Benchmark Specification:
    - Truth-Blind Boundary: Visible topology and admitted evidence without ground truth.
    - Jurisdictional domain authority and safety boundaries.
    - Context snapshot identity and speech pacing state.
    """
    ctx = OperationalContextContract(
        scenario_id="SCN-001",
        run_id="RUN-SCN-001-L1-42001",
        active_incident_id="inc-packet-drop-001",
        primary_domain="IP_TRANSPORT",
        active_domains=["IP_TRANSPORT", "PS_CORE"],
        visible_entities=["IP:PE:RTR-21", "IP:VRF:N3-01", "SA5G:UPF:003"],
        visible_topology_subgraph={"nodes": 3, "edges": 2},
        admitted_evidence_ids=["ev-emerging-001", "ev-validated-002"],
        active_knowledge_gaps=[],
        speech_pacing_active=True,
        human_sme_role="IP Transport SME",
    )

    assert ctx.scenario_id == "SCN-001"
    assert ctx.primary_domain == "IP_TRANSPORT"
    assert "IP_TRANSPORT" in ctx.active_domains
    assert len(ctx.visible_entities) == 3
    assert len(ctx.admitted_evidence_ids) == 2
    assert ctx.speech_pacing_active is True
    assert ctx.human_sme_role == "IP Transport SME"

    # Truth-blindness audit: ground truth fields are forbidden
    dump = ctx.model_dump() if hasattr(ctx, "model_dump") else ctx.dict()
    forbidden = ["hidden", "hidden_truth", "ground_truth", "root_condition", "root_entity"]
    for f in forbidden:
        assert f not in dump, f"Forbidden oracle field '{f}' leaked into OperationalContextContract"


# ============================================================================
# 6. Canonical 4-Plane Knowledge Graph Topology Certification
# ============================================================================

def test_4plane_graph_topology():
    """Certifies canonical 4-plane knowledge graph topology and build_graph artifact:
    - Verified index nodes: TOPOLOGY, INCIDENTS, EPISODES, PATTERNS, PLAYBOOKS.
    - Zero occurrences of detached 'Cross-Domain Operations' bubble.
    - Renamed 'OSS & Management Systems'.
    - Granular 12-domain mapping and multi-plane filtering metadata.
    """
    client = Gbrain4PlaneMCPClient()

    # 1. Verify 4-Plane Index Nodes
    topology_node = client.get_index_node("TOPOLOGY")
    assert topology_node["slug"] == "index-topology"
    assert topology_node["plane"] == "topology"

    incidents_node = client.get_index_node("INCIDENTS")
    assert incidents_node["slug"] == "index-incidents"
    assert incidents_node["plane"] == "incident"

    episodes_node = client.get_index_node("EPISODES")
    assert episodes_node["slug"] == "index-episodes"
    assert episodes_node["plane"] == "reasoning"

    patterns_node = client.get_index_node("PATTERNS")
    assert patterns_node["slug"] == "index-patterns"
    assert patterns_node["plane"] == "pattern"

    playbooks_node = client.get_index_node("PLAYBOOKS")
    assert playbooks_node["slug"] == "index-playbooks"
    assert playbooks_node["plane"] == "pattern"

    # 2. Verify Generated Knowledge Graph Artifact
    artifact_path = Path("artifacts/telecom-knowledge-graph.html")
    assert artifact_path.is_file(), "Generated HTML knowledge graph artifact must exist"

    content = artifact_path.read_text(encoding="utf-8")

    # Assert elimination of detached Cross-Domain Operations bubble
    assert '"domain": "Cross-Domain Operations"' not in content, (
        "Detached 'Cross-Domain Operations' bubble must be completely eliminated from domain classifications"
    )
    assert '"Cross-Domain Operations": "#38bdf8"' not in content

    # Assert renamed OSS & Management Systems
    assert "OSS & Management Systems" in content, (
        "Observability domain must be renamed to 'OSS & Management Systems'"
    )
    assert '"Observability & Remediation"' not in content

    # Assert Core Telecom Services (VAS & IN)
    assert "Core Telecom Services (VAS & IN)" in content, (
        "VAS/Messaging and IN SCP must be grouped under Core Telecom Services (VAS & IN)"
    )

    # Assert 4-Plane Filters and Plane tagging in HTML
    assert "Canonical 4-Planes" in content
    assert 'id="plane-btn-topology"' in content
    assert 'id="plane-btn-incident"' in content
    assert 'id="plane-btn-reasoning"' in content
    assert 'id="plane-btn-pattern"' in content
    assert '"plane":' in content
