"""
Unit Tests for Zaki Capability Contracts (Event & Incident Agnostic)
===================================================================
Validates schema correctness, serialization, and architectural invariants for:
- NetworkResilienceDesignContract
- ServiceImpactContract
- RemediationStrategyContract
- BlastRadiusAssessmentContract
- RootCauseAnalysisContract
- CausalPropagationContract
- DiagnosticGapContract
- WhatIfSimulationContract
"""

import json
from zaki.contracts import (
    NetworkResilienceDesignContract,
    RedundancyModel,
    SelfHealingMechanism,
    ServiceImpactContract,
    SliceImpactItem,
    SlaStatus,
    RemediationStrategyContract,
    RemediationAction,
    RemediationClass,
    RemediationStrategyType,
    BlastRadiusAssessmentContract,
    BlastRadiusTier,
    RootCauseAnalysisContract,
    RootCauseCandidate,
    CausalPropagationContract,
    CausalHop,
    DiagnosticGapContract,
    DiagnosticGapItem,
    DiagnosticGapType,
    WhatIfSimulationContract,
    SimulationMode,
    BlastRadiusDelta,
    IncidentContextContract,
    TaskEpisodeContract,
    StageOutcome,
    OperationalContextContract,
)


def test_network_resilience_design_contract():
    """Verify structural resilience profile (1+1, MPLS FRR, K8s auto-healing)."""
    resilience = NetworkResilienceDesignContract(
        entity_id="entity-rtr-01",
        domain="IP_TRANSPORT",
        redundancy_model=RedundancyModel.ONE_PLUS_ONE,
        availability_zone="AZ-1",
        region="REGION-WEST",
        standby_peer_ids=["entity-rtr-02"],
        configured_self_healing=SelfHealingMechanism.MPLS_FRR_TI_LFA,
        self_healing_target_mttr_ms=50,
        backup_path_healthy=True,
        capacity_headroom_pct=75.5,
    )
    data = resilience.model_dump()
    assert data["redundancy_model"] == "1+1"
    assert data["configured_self_healing"] == "MPLS_FRR_TI_LFA"
    assert data["self_healing_target_mttr_ms"] == 50
    assert data["backup_path_healthy"] is True


def test_service_impact_contract():
    """Verify service, slice, and SLA impact contract."""
    impact = ServiceImpactContract(
        incident_id="EVENT-REF-101",
        impacted_slices=[
            SliceImpactItem(
                slice_id="SLICE-TAG-01",
                slice_type="URLLC",
                sla_tier="PLATINUM",
                status="DEGRADED",
                dropped_sessions=420,
            )
        ],
        impacted_apns_dnns=["voice-ims", "data-internet"],
        dropped_throughput_gbps=12.5,
        affected_active_subscribers=8500,
        sla_status=SlaStatus.AT_RISK,
        vip_enterprise_accounts=["Enterprise-Account-A"],
        critical_services_affected=True,
    )
    data = impact.model_dump()
    assert data["sla_status"] == "AT_RISK"
    assert data["dropped_throughput_gbps"] == 12.5
    assert len(data["impacted_slices"]) == 1
    assert data["impacted_slices"][0]["slice_type"] == "URLLC"


def test_remediation_strategy_contract_with_ne_specific_actions():
    """Verify remediation strategy with NE-specific actions and taxonomy."""
    strategy = RemediationStrategyContract(
        remediation_id="REM-PLAN-001",
        incident_id="EVENT-REF-101",
        remediation_class=RemediationClass.WORKAROUND,
        is_auto_remediation=False,
        estimated_mttr_sec=45,
        target_actions=[
            RemediationAction(
                action_id="ACT-01",
                target_ne_type="ROUTER",
                target_ne_id="entity-rtr-01",
                strategy_type=RemediationStrategyType.METRIC_DEPREF,
                remediation_class=RemediationClass.WORKAROUND,
                parameters={"protocol": "OSPF", "new_metric": 65535},
                rollback_step={"action": "RESTORE_METRIC", "metric": 10},
            ),
            RemediationAction(
                action_id="ACT-02",
                target_ne_type="OCS_CHF",
                target_ne_id="chf-cluster-01",
                strategy_type=RemediationStrategyType.HOT_BILLING_BYPASS,
                remediation_class=RemediationClass.WORKAROUND,
                parameters={"bypass_duration_sec": 3600},
                rollback_step={"action": "RESTORE_ONLINE_CHARGING"},
            ),
        ],
        preflight_safety_checks=["backup_headroom_above_20_percent"],
        requires_human_approval=True,
        projected_throughput_recovered_gbps=12.5,
        projected_sla_breach_prevented=True,
    )
    assert len(strategy.target_actions) == 2
    assert strategy.target_actions[0].strategy_type == RemediationStrategyType.METRIC_DEPREF
    assert strategy.target_actions[1].strategy_type == RemediationStrategyType.HOT_BILLING_BYPASS
    assert strategy.projected_sla_breach_prevented is True


def test_blast_radius_assessment_contract():
    """Verify spatial/logical failure envelope contract."""
    blast = BlastRadiusAssessmentContract(
        assessment_id="BLAST-001",
        event_ref="EVENT-REF-101",
        tier=BlastRadiusTier.MULTI_DOMAIN,
        impacted_domains=["IP_TRANSPORT", "MOBILE_CORE", "RAN"],
        affected_entities=["node-rtr-01", "node-upf-01", "node-enb-01"],
        observational_symptoms=[{"type": "TICKET_SURGE", "count": 14}],
        total_affected_nodes=3,
        cross_domain_propagation=True,
    )
    data = blast.model_dump()
    assert data["tier"] == "MULTI_DOMAIN"
    assert len(data["affected_entities"]) == 3
    assert data["cross_domain_propagation"] is True


def test_root_cause_analysis_contract():
    """Verify root cause diagnosis contract."""
    rca = RootCauseAnalysisContract(
        analysis_id="RCA-001",
        event_ref="EVENT-REF-101",
        primary_culprit_entity="node-rtr-01",
        primary_domain="IP_TRANSPORT",
        fault_classification="OPTICAL_POWER_FLAP",
        confidence_score=0.96,
        supporting_evidence_ids=["EVID-101", "EVID-102"],
        ranked_alternatives=[
            RootCauseCandidate(
                entity_id="node-upf-01",
                domain="MOBILE_CORE",
                confidence=0.04,
                fault_type="CONGESTION",
                rationale="Downstream queue backlog observed as secondary effect",
            )
        ],
        diagnostic_summary="Intermittent optical power degradation triggered route flapping.",
    )
    assert rca.confidence_score == 0.96
    assert rca.primary_culprit_entity == "node-rtr-01"
    assert len(rca.ranked_alternatives) == 1


def test_causal_propagation_contract_pure_network_hops():
    """Verify strictly ordered pure network hops without symptom pollution."""
    causal = CausalPropagationContract(
        path_id="CP-001",
        event_ref="EVENT-REF-101",
        propagation_path=["node-rtr-01", "node-vrf-01", "node-upf-01", "node-enb-01"],
        entry_domain="IP_TRANSPORT",
        terminal_domain="RAN",
        domains_traversed=["IP_TRANSPORT", "MOBILE_CORE", "RAN"],
        hops=[
            CausalHop(
                hop_index=0,
                from_entity="node-rtr-01",
                to_entity="node-vrf-01",
                source_domain="IP_TRANSPORT",
                target_domain="IP_TRANSPORT",
                relationship_type="ROUTES_THROUGH",
            ),
            CausalHop(
                hop_index=1,
                from_entity="node-vrf-01",
                to_entity="node-upf-01",
                source_domain="IP_TRANSPORT",
                target_domain="MOBILE_CORE",
                relationship_type="CARRIES_TRAFFIC",
            ),
            CausalHop(
                hop_index=2,
                from_entity="node-upf-01",
                to_entity="node-enb-01",
                source_domain="MOBILE_CORE",
                target_domain="RAN",
                relationship_type="TUNNELS_TO",
            ),
        ],
        total_hops=3,
        is_cross_domain=True,
    )
    assert causal.total_hops == 3
    assert len(causal.propagation_path) == 4
    assert causal.entry_domain == "IP_TRANSPORT"
    assert causal.terminal_domain == "RAN"


def test_diagnostic_gap_contract():
    """Verify observability blindspots and missing telemetry contract."""
    gaps = DiagnosticGapContract(
        assessment_id="DGAP-001",
        scope_ref="EVENT-REF-101",
        gaps=[
            DiagnosticGapItem(
                gap_id="GAP-01",
                gap_type=DiagnosticGapType.MISSING_TELEMETRY,
                affected_domain="IP_TRANSPORT",
                affected_entities=["interface-ge-0-0-1"],
                description="Optical DOM Rx power metrics missing polling cycle",
                recommended_probes=["probe_optical_power"],
                severity="HIGH",
            )
        ],
        total_gaps=1,
        has_blocking_gaps=True,
    )
    assert gaps.total_gaps == 1
    assert gaps.has_blocking_gaps is True
    assert gaps.gaps[0].gap_type == DiagnosticGapType.MISSING_TELEMETRY


def test_what_if_simulation_contract():
    """Verify proactive and reactive what-if simulation contract."""
    sim = WhatIfSimulationContract(
        simulation_id="SIM-001",
        simulation_mode=SimulationMode.PROACTIVE_PLANNING,
        simulated_action="BUMP_METRIC_TO_65535",
        target_entities=["node-rtr-01"],
        action_parameters={"protocol": "OSPF", "drain_mode": "GRACEFUL"},
        expected_blast_radius_delta=BlastRadiusDelta.REDUCED,
        predicted_capacity_headroom_pct=68.0,
        secondary_failure_risk_score=0.08,
        estimated_recovery_time_sec=25,
        is_safe_to_execute=True,
        risk_summary="Surviving links have 68% headroom; action is safe.",
    )
    assert sim.simulation_mode == SimulationMode.PROACTIVE_PLANNING
    assert sim.expected_blast_radius_delta == BlastRadiusDelta.REDUCED
    assert sim.is_safe_to_execute is True


def test_incident_and_episode_integration():
    """Verify integration of capability contracts inside IncidentContext and TaskEpisode."""
    incident = IncidentContextContract(
        incident_id="INC-TEST-001",
        service_impact=ServiceImpactContract(
            incident_id="INC-TEST-001",
            dropped_throughput_gbps=5.0,
            sla_status=SlaStatus.NONE,
        ),
        blast_radius=BlastRadiusAssessmentContract(
            assessment_id="BLAST-INC-001",
            tier=BlastRadiusTier.LOCAL,
            total_affected_nodes=1,
        ),
    )
    assert incident.service_impact is not None
    assert incident.service_impact.dropped_throughput_gbps == 5.0
    assert incident.blast_radius is not None
    assert incident.blast_radius.tier == BlastRadiusTier.LOCAL

    episode = TaskEpisodeContract(
        task_id="TASK-001",
        incident_id="INC-TEST-001",
        operator_intent="Diagnose and mitigate transport anomaly",
        stagewise_outcomes=[
            StageOutcome(
                stage_number=1,
                stage_name="OBSERVATION",
                status="COMPLETED",
                summary="Detected transport layer metric anomaly",
            ),
            StageOutcome(
                stage_number=4,
                stage_name="CONVERGENCE",
                status="COMPLETED",
                summary="Root cause confirmed via telemetry correlation",
            ),
        ],
        root_cause_analysis=RootCauseAnalysisContract(
            analysis_id="RCA-EP-001",
            primary_culprit_entity="node-rtr-01",
            primary_domain="IP_TRANSPORT",
            fault_classification="OPTICAL_FLAP",
        ),
    )
    assert len(episode.stagewise_outcomes) == 2
    assert episode.root_cause_analysis is not None
    assert episode.root_cause_analysis.primary_culprit_entity == "node-rtr-01"
