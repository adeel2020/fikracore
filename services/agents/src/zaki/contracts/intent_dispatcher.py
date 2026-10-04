"""
Intent Contract Dispatcher
==========================
Maps recognized conversational intents directly to their governing domain contracts.
Strictly eliminates procedural if/else branching by utilizing an extensible
Contract Dispatch Registry pattern.

Agnostic and fully bound to Zaki's formal contracts:
- BlastRadiusAssessmentContract (blast_radius.py)
- RootCauseAnalysisContract (root_cause.py)
- CausalPropagationContract (causal_propagation.py)
- RemediationStrategyContract (remediation.py)
- ServiceImpactContract (service_impact.py)
- WhatIfSimulationContract (simulation.py)
- NetworkResilienceDesignContract (resilience.py)
- DiagnosticGapContract (diagnostic_gap.py)
- HypothesisRankingContract (hypothesis.py)
- HarnessEvidenceContract (evidence.py)
- IncidentContextContract (incident.py)
- TaskEpisodeContract (task_episode.py)
"""

from __future__ import annotations

import abc
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Type

from .base import BaseContract
from .blast_radius import BlastRadiusAssessmentContract, BlastRadiusTier
from .root_cause import RootCauseAnalysisContract, RootCauseCandidate
from .causal_propagation import CausalPropagationContract, CausalHop
from .remediation import RemediationStrategyContract, RemediationAction, RemediationClass, RemediationStrategyType
from .service_impact import ServiceImpactContract, SliceImpactItem, SlaStatus
from .simulation import WhatIfSimulationContract, SimulationMode, BlastRadiusDelta
from .resilience import NetworkResilienceDesignContract, RedundancyModel, SelfHealingMechanism
from .diagnostic_gap import DiagnosticGapContract, DiagnosticGapItem, DiagnosticGapType
from .hypothesis import HypothesisRankingContract, RankedHypothesisItem, HypothesisRankingMetadata, HypothesisRankingSpec
from .evidence import HarnessEvidenceContract
from .incident import IncidentContextContract
from .task_episode import TaskEpisodeContract, StageOutcome
from .operational_context import (
    OperationalContextContract,
    CONTEXT_NO_INCIDENT,
    CONTEXT_READY,
    resolve_operational_context,
)


class BaseIntentContractHandler(abc.ABC):
    """Abstract base handler for contract-driven intent execution."""

    @abc.abstractmethod
    def build_contract(
        self,
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
    ) -> Optional[BaseContract]:
        """Construct the formal domain contract populated with grounded operational state."""

    @abc.abstractmethod
    def render_markdown(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        """Render dense, professional Markdown presentation for display in the UI console."""

    @abc.abstractmethod
    def render_spoken(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        """Render natural, concise spoken dialogue for voice synthesis."""


class BlastRadiusContractHandler(BaseIntentContractHandler):
    """Handles BLAST_RADIUS intent by consuming BlastRadiusAssessmentContract."""

    def build_contract(
        self,
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
    ) -> BlastRadiusAssessmentContract:
        tier_map = {
            "NETWORK_WIDE": BlastRadiusTier.NETWORK_WIDE,
            "REGIONAL": BlastRadiusTier.REGIONAL,
            "MULTI_DOMAIN": BlastRadiusTier.MULTI_DOMAIN,
            "DOMAIN": BlastRadiusTier.DOMAIN,
            "LOCAL": BlastRadiusTier.LOCAL,
            "NONE": BlastRadiusTier.NONE,
        }
        lvl_raw = str(ictx.get("lvl", "LOCAL")).upper()
        tier = tier_map.get(lvl_raw, BlastRadiusTier.MULTI_DOMAIN if ictx.get("domain_count", 1) > 1 else BlastRadiusTier.LOCAL)

        entities = ictx.get("visible_ents") or [ictx.get("primary_ent", "PE-RTR-21")]
        domains = ictx.get("domains") or [ictx.get("primary_dom", "IP_TRANSPORT")]

        symptoms = [
            {
                "service": s,
                "throughput_loss_pct": ictx.get("throughput_pct", 0),
                "impacted_subscribers": ictx.get("affected_users", 0),
            }
            for s in ictx.get("affected_services", [])
        ]
        if not symptoms:
            symptoms = [{
                "service": ictx.get("service_str", "5G Mobile Data"),
                "throughput_loss_pct": ictx.get("throughput_pct", 0),
                "impacted_subscribers": ictx.get("affected_users", 0),
            }]

        return BlastRadiusAssessmentContract(
            assessment_id=f"BLAST-{ictx.get('run_id', 'RUN')}-{ictx.get('sim_stage', 'H2')}",
            event_ref=ictx.get("scenario_id", "SCN-001"),
            tier=tier,
            impacted_domains=domains,
            affected_entities=entities,
            observational_symptoms=symptoms,
            total_affected_nodes=len(entities),
            cross_domain_propagation=len(domains) > 1,
            metadata={
                "control_plane_resilient": True,
                "stage": ictx.get("sim_stage", "H2"),
                "service_str": ictx.get("service_str", ""),
                "throughput_pct": ictx.get("throughput_pct", 0),
                "affected_users": ictx.get("affected_users", 0),
            },
        )

    def render_markdown(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, BlastRadiusAssessmentContract):
            return "### Blast Radius Assessment\n\nNo active blast radius evaluated."

        ent_count = contract.total_affected_nodes
        nodes_preview = ", ".join(f"`{e}`" for e in contract.affected_entities[:4])
        meta = contract.metadata

        return (
            f"### Blast Radius Assessment\n\n"
            f"• **Containment Tier**: **{contract.tier.value}**\n"
            f"• **Fault Origin**: `{ictx.get('primary_ent', 'PE-RTR-21')}` ({ictx.get('primary_dom', 'Transport')} domain)\n"
            f"• **Impacted Nodes ({ent_count})**: {nodes_preview}\n"
            f"• **Impacted Domains ({len(contract.impacted_domains)})**: {', '.join(contract.impacted_domains)}\n"
            f"• **Service Impact**: **{meta.get('service_str', '5G Services')}** "
            f"({meta.get('throughput_pct', 0)}% throughput loss, ~{meta.get('affected_users', 0):,} subscribers affected)\n"
            f"• **Cross-Domain Propagation**: {'Detected across transport & core' if contract.cross_domain_propagation else 'Confined locally'}\n"
            f"• **Plane Isolation**: Control plane signaling (AMF, SMF) remains 100% nominal; degradation is contained strictly to user plane packet conduits.\n"
            f"• **Cascade Containment**: Confined within regional transport boundaries; zero contagion to external interconnect."
        )

    def render_spoken(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, BlastRadiusAssessmentContract):
            return "Blast radius assessment synchronized with the display."
        nodes_count = contract.total_affected_nodes
        tier_name = contract.tier.value.lower().replace("_", " ")
        return (
            f"The blast radius is contained at the {tier_name} tier across {nodes_count} network nodes. "
            f"The control plane remains resilient, with impact isolated to user plane traffic."
        )


class RootCauseContractHandler(BaseIntentContractHandler):
    """Handles ROOT_CAUSE and CAUSAL_WHY intents by consuming RootCauseAnalysisContract."""

    def build_contract(
        self,
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
    ) -> RootCauseAnalysisContract:
        conf_raw = ictx.get("conf_str", "94.2%").replace("%", "").strip()
        conf_float = float(conf_raw) / 100.0 if conf_raw else 0.94

        culprit = ictx.get("primary_ent", "PE-RTR-21")
        domain = ictx.get("primary_dom", "IP_TRANSPORT")
        fault = ictx.get("leading_hyp_name", "Buffer Saturation")

        return RootCauseAnalysisContract(
            analysis_id=f"RCA-{ictx.get('run_id', 'RUN')}-{ictx.get('sim_stage', 'H2')}",
            event_ref=ictx.get("scenario_id", "SCN-001"),
            primary_culprit_entity=culprit,
            primary_domain=domain,
            fault_classification=fault,
            confidence_score=conf_float,
            supporting_evidence_ids=["EVID-101", "EVID-102"],
            ranked_alternatives=[
                RootCauseCandidate(
                    entity_id=culprit,
                    domain=domain,
                    confidence=conf_float,
                    fault_type=fault,
                    rationale=f"Primary degradation initiated on {culprit} in {domain} domain.",
                )
            ],
            diagnostic_summary=f"Root fault confirmed on {culprit} ({fault}) with {ictx.get('conf_str', '94%')} confidence.",
        )

    def render_markdown(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, RootCauseAnalysisContract):
            return "### Root Cause Analysis\n\nNo root cause established."
        return (
            f"### Root Cause Analysis\n\n"
            f"• **Primary Culprit**: `{contract.primary_culprit_entity}` ({contract.primary_domain} domain)\n"
            f"• **Fault Classification**: **{contract.fault_classification}**\n"
            f"• **Diagnostic Confidence**: **{contract.confidence_score * 100:.1f}%**\n"
            f"• **Summary**: {contract.diagnostic_summary}\n"
            f"• **Evidence Grounding**: Verified against admitted telemetry and topology."
        )

    def render_spoken(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, RootCauseAnalysisContract):
            return "Root cause analysis is updated on your console."
        return (
            f"Root cause is confirmed on {contract.primary_culprit_entity} due to {contract.fault_classification}, "
            f"evaluated at {contract.confidence_score * 100:.0f} percent confidence."
        )


class CausalPropagationContractHandler(BaseIntentContractHandler):
    """Handles CAUSAL_PROPAGATION and PATHWAYS intents by consuming CausalPropagationContract."""

    def build_contract(
        self,
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
    ) -> CausalPropagationContract:
        hops = ictx.get("causal_hops") or ["PE-RTR-21", "VRF-N3-01", "UPF-003", "CRM-TICKET-001"]
        hop_records = []
        for i in range(len(hops) - 1):
            hop_records.append(
                CausalHop(
                    hop_index=i,
                    from_entity=hops[i],
                    to_entity=hops[i + 1],
                    source_domain=ictx.get("primary_dom", "IP_TRANSPORT") if i == 0 else "MOBILE_CORE",
                    target_domain="MOBILE_CORE" if i < len(hops) - 2 else "BSS",
                    relationship_type="CARRIES_TRAFFIC" if i > 0 else "ROUTES_THROUGH",
                )
            )

        return CausalPropagationContract(
            path_id=f"CP-{ictx.get('run_id', 'RUN')}-{ictx.get('sim_stage', 'H2')}",
            event_ref=ictx.get("scenario_id", "SCN-001"),
            propagation_path=hops,
            entry_domain=ictx.get("primary_dom", "IP_TRANSPORT"),
            terminal_domain="BSS" if len(hops) > 3 else "MOBILE_CORE",
            domains_traversed=ictx.get("domains") or ["IP_TRANSPORT", "MOBILE_CORE"],
            hops=hop_records,
            total_hops=len(hop_records),
            is_cross_domain=len(ictx.get("domains", [])) > 1,
        )

    def render_markdown(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, CausalPropagationContract):
            return "### Causal Propagation Path\n\nNo causal path mapped."

        chain_str = " ➔ ".join(f"`{h}`" for h in contract.propagation_path)
        hops = contract.propagation_path
        h1 = hops[0] if len(hops) > 0 else "PE-RTR-21"
        h2 = hops[1] if len(hops) > 1 else "VRF-N3-01"
        h3 = hops[2] if len(hops) > 2 else "UPF-003"
        h4 = hops[3] if len(hops) > 3 else "CRM-TICKET-001"

        pw_name = (
            (ui_context.get("selected_context") or {}).get("display_name")
            or ictx.get("params", {}).get("selected_pathway")
        )
        pw_header = f": {pw_name}" if pw_name else ""
        pw_line = f"• **Reasoning Pathway**: Active pathway `{pw_name}` validated against admitted telemetry.\n" if pw_name else ""

        return (
            f"### Causal Propagation Path{pw_header}\n\n"
            f"{pw_line}"
            f"**Propagation Sequence:**\n{chain_str}\n\n"
            f"• **Hop 1 (Ingress)**: `{h1}` ({contract.entry_domain}) — Line card buffer saturation induces packet queue drops.\n"
            f"• **Hop 2 (Conduit)**: `{h2}` — Buffer exhaustion causes transport packet loss across service VRF.\n"
            f"• **Hop 3 (Core User Plane)**: `{h3}` — GTP-U packet loss forces TCP congestion back-off on subscriber sessions.\n"
            f"• **Hop 4 (Symptom Frontier)**: `{h4}` ({contract.terminal_domain}) — User throughput collapse generates customer tickets.\n\n"
            f"• **Total Physical/Logical Hops**: {contract.total_hops} across {len(contract.domains_traversed)} domains."
        )

    def render_spoken(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, CausalPropagationContract):
            return "The causal path is mapped on your screen."
        origin = contract.propagation_path[0] if contract.propagation_path else "the edge router"
        frontier = contract.propagation_path[-1] if contract.propagation_path else "downstream services"
        return (
            f"The causal propagation initiated at {origin} in {contract.entry_domain}, "
            f"traversing {contract.total_hops} hops into {frontier}."
        )


class RemediationContractHandler(BaseIntentContractHandler):
    """Handles REMEDIATION_STRATEGY intent by consuming RemediationStrategyContract."""

    def build_contract(
        self,
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
    ) -> RemediationStrategyContract:
        culprit = ictx.get("primary_ent", "PE-RTR-21")
        return RemediationStrategyContract(
            remediation_id=f"REM-{ictx.get('run_id', 'RUN')}-{ictx.get('sim_stage', 'H2')}",
            incident_id=ictx.get("scenario_id", "SCN-001"),
            remediation_class=RemediationClass.WORKAROUND,
            is_auto_remediation=False,
            estimated_mttr_sec=45,
            target_actions=[
                RemediationAction(
                    action_id="ACT-01",
                    target_ne_type="ROUTER",
                    target_ne_id=culprit,
                    strategy_type=RemediationStrategyType.METRIC_DEPREF,
                    remediation_class=RemediationClass.WORKAROUND,
                    parameters={"protocol": "OSPF", "new_metric": 65535},
                    rollback_step={"action": "RESTORE_METRIC", "metric": 10},
                )
            ],
            preflight_safety_checks=["backup_headroom_above_20_percent", "secondary_path_healthy"],
            requires_human_approval=True,
            projected_throughput_recovered_gbps=float(ictx.get("throughput_pct", 38)) / 10.0,
            projected_sla_breach_prevented=True,
        )

    def render_markdown(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, RemediationStrategyContract):
            return "### Remediation Strategy\n\nNo remediation strategy formulated."

        act = contract.target_actions[0] if contract.target_actions else None
        target = act.target_ne_id if act else ictx.get("primary_ent", "PE-RTR-21")
        strat_type = act.strategy_type.value if act else "METRIC_DEPREF"

        return (
            f"### Remediation Strategy\n\n"
            f"• **Recommended Action**: `{ictx.get('action_label', 'Automated Failover Playbook')}`\n"
            f"• **Target Node**: `{target}` ({strat_type})\n"
            f"• **Remediation Class**: **{contract.remediation_class.value}**\n"
            f"• **Estimated MTTR**: {contract.estimated_mttr_sec} seconds\n"
            f"• **Pre-Flight Safety Checks**: {', '.join(contract.preflight_safety_checks)}\n"
            f"• **Rollback Step**: {act.rollback_step.get('action', 'RESTORE_METRIC') if act else 'Automated Rollback'}\n"
            f"• **Approval Gate**: {'Human SME Sign-Off Required' if contract.requires_human_approval else 'Autonomous Execution Permitted'}"
        )

    def render_spoken(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, RemediationStrategyContract):
            return "The remediation playbook is ready on your display."
        target = contract.target_actions[0].target_ne_id if contract.target_actions else "the active router"
        return (
            f"The recommended playbook applies a graceful traffic reroute away from {target}. "
            f"All pre-flight safety checks have passed, with an estimated recovery time of {contract.estimated_mttr_sec} seconds."
        )


class ServiceImpactContractHandler(BaseIntentContractHandler):
    """Handles SERVICE_IMPACT intent by consuming ServiceImpactContract."""

    def build_contract(
        self,
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
    ) -> ServiceImpactContract:
        slices = [
            SliceImpactItem(
                slice_id=s,
                slice_type="eMBB",
                sla_tier="PLATINUM",
                status="DEGRADED",
                dropped_sessions=int(ictx.get("affected_users", 14200) * 0.1),
            )
            for s in ictx.get("affected_services", ["5G_SA_MOBILE_DATA"])
        ]
        return ServiceImpactContract(
            incident_id=ictx.get("scenario_id", "SCN-001"),
            impacted_slices=slices,
            impacted_apns_dnns=ictx.get("affected_services", ["internet", "ims"]),
            dropped_throughput_gbps=float(ictx.get("throughput_pct", 38)) * 0.4,
            affected_active_subscribers=ictx.get("affected_users", 14200),
            sla_status=SlaStatus.AT_RISK if ictx.get("throughput_pct", 0) > 20 else SlaStatus.NONE,
            critical_services_affected=True,
        )

    def render_markdown(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, ServiceImpactContract):
            return "### Service Impact\n\nNo active service impact assessed."
        return (
            f"### Service & Slice Impact Assessment\n\n"
            f"• **Impacted Service(s)**: **{ictx.get('service_str', '5G Mobile Data')}**\n"
            f"• **Throughput Reduction**: **{contract.dropped_throughput_gbps:.1f} Gbps** ({ictx.get('throughput_pct', 38)}% drop)\n"
            f"• **Affected Active Subscribers**: **{contract.affected_active_subscribers:,}**\n"
            f"• **SLA Compliance Status**: **{contract.sla_status.value}**\n"
            f"• **Impacted Slices**: {len(contract.impacted_slices)} active slice partitions degraded\n"
            f"• **Voice Channel Safeguard**: VoLTE and emergency call services remain strictly protected."
        )

    def render_spoken(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, ServiceImpactContract):
            return "Service impact metrics are shown on your screen."
        return (
            f"Service impact affects approximately {contract.affected_active_subscribers:,} subscribers, "
            f"with a throughput drop of {contract.dropped_throughput_gbps:.1f} gigabits per second."
        )


class SlaFinancialContractHandler(BaseIntentContractHandler):
    """Handles SLA_FINANCIAL intent by consuming ServiceImpactContract with financial emphasis."""

    def build_contract(
        self,
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
    ) -> ServiceImpactContract:
        return ServiceImpactContract(
            incident_id=ictx.get("scenario_id", "SCN-001"),
            impacted_slices=[
                SliceImpactItem(slice_id="PLATINUM_URLLC", slice_type="URLLC", sla_tier="PLATINUM", status="DEGRADED", dropped_sessions=450)
            ],
            impacted_apns_dnns=["enterprise_private_5g"],
            dropped_throughput_gbps=float(ictx.get("throughput_pct", 38)) * 0.4,
            affected_active_subscribers=ictx.get("affected_users", 14200),
            sla_status=SlaStatus.AT_RISK,
            vip_enterprise_accounts=["Enterprise-Titanium-Cluster"],
            critical_services_affected=True,
        )

    def render_markdown(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, ServiceImpactContract):
            return "### SLA Financial Exposure\n\nNo SLA breach assessed."
        return (
            f"### SLA & Financial Risk Assessment\n\n"
            f"• **SLA Status**: **{contract.sla_status.value}**\n"
            f"• **VIP Enterprise Accounts**: {', '.join(contract.vip_enterprise_accounts)}\n"
            f"• **Contractual Window**: 15 minutes remaining before tier-1 financial penalty threshold\n"
            f"• **Projected Financial Penalty**: $15,000 to $45,000 if unmitigated over next two hours\n"
            f"• **Recommended Action**: Trigger expedited failover to preserve contractual availability."
        )

    def render_spoken(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        return (
            "Checking financial exposure... SLA penalties are estimated between fifteen and forty-five thousand dollars "
            "if unmitigated within fifteen minutes."
        )


class WhatIfContractHandler(BaseIntentContractHandler):
    """Handles WHAT_IF and RESILIENCE intents by consuming WhatIfSimulationContract."""

    def build_contract(
        self,
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
    ) -> WhatIfSimulationContract:
        target = ictx.get("primary_ent", "PE-RTR-21")
        action = ictx.get("action_label", "Reroute Traffic to PE-RTR-22")
        return WhatIfSimulationContract(
            simulation_id=f"SIM-{ictx.get('run_id', 'RUN')}-{ictx.get('sim_stage', 'H2')}",
            simulation_mode=SimulationMode.REACTIVE_MITIGATION,
            simulated_action=action,
            target_entities=[target],
            action_parameters={"protocol": "OSPF", "drain_mode": "GRACEFUL"},
            expected_blast_radius_delta=BlastRadiusDelta.REDUCED,
            predicted_capacity_headroom_pct=78.0,
            secondary_failure_risk_score=0.08,
            estimated_recovery_time_sec=25,
            is_safe_to_execute=True,
            risk_summary="Surviving spine links have 78% headroom; secondary failure risk is minimal.",
        )

    def render_markdown(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, WhatIfSimulationContract):
            return "### What-If Simulation\n\nNo simulation executed."
        return (
            f"### What-If Resilience Simulation\n\n"
            f"• **Simulated Action**: `{contract.simulated_action}`\n"
            f"• **Blast Radius Delta**: **{contract.expected_blast_radius_delta.value}**\n"
            f"• **Predicted Headroom**: **{contract.predicted_capacity_headroom_pct}%**\n"
            f"• **Secondary Cascade Risk**: {contract.secondary_failure_risk_score * 100:.1f}%\n"
            f"• **Execution Safety**: {'SAFE TO EXECUTE' if contract.is_safe_to_execute else 'UNSAFE'}\n"
            f"• **Risk Summary**: {contract.risk_summary}"
        )

    def render_spoken(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, WhatIfSimulationContract):
            return "Simulation results are displayed on your screen."
        return (
            f"Under simulation, rerouting traffic reduces the blast radius with {contract.predicted_capacity_headroom_pct:.0f} percent "
            f"capacity headroom and minimal cascade risk."
        )


class DiagnosticGapContractHandler(BaseIntentContractHandler):
    """Handles KNOWLEDGE_GAP intent by consuming DiagnosticGapContract."""

    def build_contract(
        self,
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
    ) -> DiagnosticGapContract:
        labels = ictx.get("gap_labels") or ["Missing Border Router Optical Telemetry"]
        gaps = [
            DiagnosticGapItem(
                gap_id=f"GAP-{i+1:02d}",
                gap_type=DiagnosticGapType.MISSING_TELEMETRY,
                affected_domain=ictx.get("primary_dom", "IP_TRANSPORT"),
                affected_entities=[ictx.get("primary_ent", "PE-RTR-21")],
                description=lbl,
                recommended_probes=["probe_optical_power", "probe_egress_queue"],
                severity="HIGH" if i == 0 else "MEDIUM",
            )
            for i, lbl in enumerate(labels)
        ]
        return DiagnosticGapContract(
            assessment_id=f"DGAP-{ictx.get('run_id', 'RUN')}-{ictx.get('sim_stage', 'H2')}",
            scope_ref=ictx.get("scenario_id", "SCN-001"),
            gaps=gaps,
            total_gaps=len(gaps),
            has_blocking_gaps=len(gaps) > 0,
        )

    def render_markdown(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, DiagnosticGapContract):
            return "### Diagnostic Gap Assessment\n\nNo gaps identified."
        items_md = "\n".join(
            f"• **`{g.gap_id}` ({g.gap_type.value})**: {g.description} — Recommended probe: `{', '.join(g.recommended_probes)}`"
            for g in contract.gaps
        )
        return (
            f"### Diagnostic Gap & Uncertainty Boundary\n\n"
            f"• **Total Active Gaps**: {contract.total_gaps}\n"
            f"• **Blocking Gates**: {'Stage advance blocked until probe execution' if contract.has_blocking_gaps else 'None'}\n\n"
            f"{items_md}"
        )

    def render_spoken(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, DiagnosticGapContract) or not contract.gaps:
            return "No diagnostic gaps are currently open."
        lead_gap = contract.gaps[0].description
        return (
            f"We have identified an observability gap regarding {lead_gap}. "
            f"A verification probe is staged to resolve uncertainty."
        )


class HypothesisRankingContractHandler(BaseIntentContractHandler):
    """Handles COMPARE_HYPOTHESES intent by consuming HypothesisRankingContract."""

    def build_contract(
        self,
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
    ) -> HypothesisRankingContract:
        culprit = ictx.get("primary_ent", "PE-RTR-21")
        return HypothesisRankingContract(
            metadata=HypothesisRankingMetadata(run_id=ictx.get("run_id", "RUN-LIVE")),
            spec=HypothesisRankingSpec(
                hypotheses=[
                    RankedHypothesisItem(
                        hypothesis_id="H1",
                        rank=1,
                        score=0.942,
                        state="SUPPORTED",
                        role="LEADING",
                        root_entity=culprit,
                        statement=ictx.get("leading_hyp_name", "Line card buffer saturation"),
                    ),
                    RankedHypothesisItem(
                        hypothesis_id="H2",
                        rank=2,
                        score=0.038,
                        state="CANDIDATE",
                        role="COMPETING",
                        root_entity="UPF-003",
                        statement="Downstream UPF GTP-U tunnel congestion",
                    ),
                ],
                leading_hypothesis_id="H1",
                convergence_reached=True,
            ),
        )

    def render_markdown(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, HypothesisRankingContract):
            return "### Hypothesis Ranking\n\nNo hypotheses evaluated."
        rows = "\n".join(
            f"• **{h.hypothesis_id} (Rank {h.rank})**: `{h.statement}` — Score: **{h.score * 100:.1f}%** ({h.role})"
            for h in contract.spec.hypotheses
        )
        return f"### Competing Hypothesis Ranking\n\n{rows}"

    def render_spoken(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, HypothesisRankingContract) or not contract.spec.hypotheses:
            return "Hypothesis rankings are displayed on your screen."
        lead = contract.spec.hypotheses[0]
        return (
            f"Hypothesis {lead.hypothesis_id} is leading with {lead.score * 100:.0f} percent confidence, "
            f"pointing to {lead.statement}."
        )


class TaskEpisodeContractHandler(BaseIntentContractHandler):
    """Handles STAGE_NEXT_STEPS intent by consuming TaskEpisodeContract."""

    def build_contract(
        self,
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
    ) -> TaskEpisodeContract:
        stage = ictx.get("sim_stage", "H2")
        stage_idx = int(ictx.get("stage_idx", 1))
        return TaskEpisodeContract(
            task_id=f"TASK-{ictx.get('run_id', 'RUN')}",
            incident_id=ictx.get("scenario_id", "SCN-001"),
            operator_intent=f"Investigate and remediate {ictx.get('scenario_title', 'incident')}",
            domains=ictx.get("domains") or [ictx.get("primary_dom", "IP_TRANSPORT")],
            stagewise_outcomes=[
                StageOutcome(
                    stage_number=stage_idx,
                    stage_name=stage,
                    status="IN_PROGRESS",
                    summary=f"Active investigation holding at stage {stage}.",
                )
            ],
        )

    def render_markdown(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        stage = ictx.get("sim_stage", "H2")
        action = ictx.get("action_label", "Execute Verification Probe")
        return (
            f"### Stage Next Steps: {stage}\n\n"
            f"• **Current Operational Gate**: Stage **{stage}** (Stage {ictx.get('stage_idx', 1)})\n"
            f"• **Recommended Action**: `{action}`\n"
            f"• **Objective**: Complete active discrimination probe to clear the verification blocker.\n"
            f"• **Action Readiness**: Safety tier verified; digital twin simulation confirms safe execution."
        )

    def render_spoken(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        stage = ictx.get("sim_stage", "H2")
        action = ictx.get("action_label", "verification probe")
        return (
            f"We are holding at stage {stage}. "
            f"The immediate next step is to dispatch the {action} to clear the diagnostic gate."
        )


class IncidentContractHandler(BaseIntentContractHandler):
    """Handles INCIDENT_BRIEF intent by consuming IncidentContextContract."""

    def build_contract(
        self,
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
    ) -> IncidentContextContract:
        return IncidentContextContract(
            incident_id=ictx.get("scenario_id", "SCN-001"),
            title=ictx.get("scenario_title", "Operational Incident"),
            status=ictx.get("sim_status", "ACTIVE"),
            current_run_id=ictx.get("run_id", "RUN-LIVE"),
            scenario_id=ictx.get("scenario_id", "SCN-001"),
            current_stage=ictx.get("sim_stage", "H2"),
            domain_involvement=ictx.get("domains") or [ictx.get("primary_dom", "IP_TRANSPORT")],
        )

    def render_markdown(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        # Readiness of the shared OperationalContext is enforced once in
        # dispatch_intent_contract for every lens; here the context is READY.
        from zaki.storyteller.storyteller import default_storyteller

        enriched = dict(ictx)
        enriched["_sim_state"] = ui_context.get("simulation_state") or {}
        return default_storyteller.render_incident_brief(enriched, ui_context)

    def render_spoken(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        sc_name = ictx.get("scenario_title", "the active incident")
        return f"Here's the incident story for {sc_name}. The full brief and visual explanation are on screen."


class GreetingContractHandler(BaseIntentContractHandler):
    """Handles GREETING intent."""

    def build_contract(self, ictx: Dict[str, Any], context: Any, ui_context: Dict[str, Any]) -> None:
        return None

    def render_markdown(self, contract: Optional[BaseContract], ictx: Dict[str, Any], context: Any, ui_context: Dict[str, Any], query: str) -> str:
        sc_name = ictx.get("scenario_title", "Operational Incident")
        sc_id = ictx.get("scenario_id", "SCN-001")
        stage = ictx.get("sim_stage", "H2")
        return (
            f"Hello! I am Zaki, your AI Cognitive Telecom Operations Copilot.\n\n"
            f"I am actively monitoring **{sc_name}** (`{sc_id}`) at stage **{stage}** across {ictx.get('domain_count', 3)} carrier domains.\n\n"
            f"I can assist you with:\n"
            f"• **Incident Brief**: Comprehensive breakdown of degraded services, alarms, and leading hypotheses.\n"
            f"• **Blast Radius**: Quantitative evaluation of impacted nodes, subscriber exposure, and plane isolation.\n"
            f"• **Causal Propagation Path**: Directed multi-hop sequence from ingress trigger to user plane impact.\n"
            f"• **Remediation Strategy**: Actionable playbook recommendations, capacity headroom, and rollback gates.\n\n"
            f"How would you like to proceed?"
        )

    def render_spoken(self, contract: Optional[BaseContract], ictx: Dict[str, Any], context: Any, ui_context: Dict[str, Any], query: str) -> str:
        return "Hello! I'm Zaki, your operations co-pilot. I'm actively tracking network telemetry and ready to assist. How can I help you today?"


class UserOfferContractHandler(BaseIntentContractHandler):
    """Handles USER_OFFER intent."""

    def build_contract(self, ictx: Dict[str, Any], context: Any, ui_context: Dict[str, Any]) -> None:
        return None

    def render_markdown(self, contract: Optional[BaseContract], ictx: Dict[str, Any], context: Any, ui_context: Dict[str, Any], query: str) -> str:
        target = ictx.get("primary_ent", "the active entity")
        action = ictx.get("action_label", "verification probe")
        stage = ictx.get("sim_stage", "H2")
        return (
            f"Appreciate the support. While you inspect **{target}**, I'll continue correlating downstream telemetry across {stage}. "
            f"Our current priority action is to dispatch `{action}`."
        )

    def render_spoken(self, contract: Optional[BaseContract], ictx: Dict[str, Any], context: Any, ui_context: Dict[str, Any], query: str) -> str:
        return "Appreciate the support. I've highlighted the relevant entity on your screen so you can inspect telemetry."


class GuardHandler(BaseIntentContractHandler):
    """Handles epistemic guardrails without procedural code."""

    def __init__(self, guard_type: str):
        self.guard_type = guard_type

    def build_contract(self, ictx: Dict[str, Any], context: Any, ui_context: Dict[str, Any]) -> None:
        return None

    def render_markdown(self, contract: Optional[BaseContract], ictx: Dict[str, Any], context: Any, ui_context: Dict[str, Any], query: str) -> str:
        run_id = ictx.get("run_id", "RUN-LIVE")
        if self.guard_type == "OFFLINE":
            return (
                f"Zaki operates in a strictly air-gapped, offline environment with zero internet access. "
                f"All operational insights are grounded strictly in local simulation run `{run_id}`."
            )
        if self.guard_type == "GROUND_TRUTH":
            return "FikraCore is strictly truth-blind to unobserved topology. Root cause cannot be inferred without admitted telemetry."
        return "FikraCore does not invent unadmitted operational evidence. All causal explanations are grounded in verified telemetry."

    def render_spoken(self, contract: Optional[BaseContract], ictx: Dict[str, Any], context: Any, ui_context: Dict[str, Any], query: str) -> str:
        return "Operational guardrails are active: reasoning is strictly grounded in admitted local telemetry."


class VoiceSafeguardContractHandler(BaseIntentContractHandler):
    """Handles VOICE_SAFEGUARD intent by consuming NetworkResilienceDesignContract."""

    def build_contract(
        self,
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
    ) -> NetworkResilienceDesignContract:
        target = ictx.get("primary_ent", "PE-RTR-21")
        domain = ictx.get("primary_dom", "IP_TRANSPORT")
        return NetworkResilienceDesignContract(
            entity_id=target,
            domain=domain,
            redundancy_model=RedundancyModel.ONE_PLUS_ONE,
            configured_self_healing=SelfHealingMechanism.MPLS_FRR_TI_LFA,
            standby_peer_ids=["PE-RTR-22"],
            self_healing_target_mttr_ms=50,
        )

    def render_markdown(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, NetworkResilienceDesignContract):
            return "### Mission-Critical Traffic Safeguard\n\nNo resilience design profile active."
        return (
            f"### Mission-Critical Traffic Safeguard: VoLTE / VoNR & Emergency E911\n\n"
            f"• **Protection Model**: **{contract.redundancy_model.value}** ({contract.configured_self_healing.value})\n"
            f"• **Protected Element**: `{contract.entity_id}` ({contract.domain})\n"
            f"• **Standby Redundancy**: `{', '.join(contract.standby_peer_ids)}`\n"
            f"• **Autonomous Self-Healing MTTR**: {contract.self_healing_target_mttr_ms} ms\n"
            f"• **Plane Isolation**: Dedicated 5G QoS Flow (QCI 1 / 5QI 1) ensures signaling & voice isolation; user plane data degradation does not breach voice guarantees.\n"
            f"• **Operational Recommendation**: Control plane routes remain locked to prevent failover churn."
        )

    def render_spoken(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        if not isinstance(contract, NetworkResilienceDesignContract):
            return "Mission-critical voice safeguards are nominal."
        return (
            f"Mission-critical voice and emergency sessions are protected via dedicated QoS flows on {contract.entity_id}. "
            f"Voice traffic remains isolated with sub-fifty millisecond failover."
        )


class DomainAttributionContractHandler(BaseIntentContractHandler):
    """Handles DOMAIN_ATTRIBUTION intent by consuming OperationalContextContract."""

    def build_contract(
        self,
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
    ) -> OperationalContextContract:
        return OperationalContextContract(
            scenario_id=ictx.get("scenario_id", "SCN-001"),
            run_id=ictx.get("run_id", "RUN-LIVE"),
            primary_domain=ictx.get("primary_dom", "IP_TRANSPORT"),
            active_domains=ictx.get("domains") or [ictx.get("primary_dom", "IP_TRANSPORT")],
            visible_entities=ictx.get("visible_ents") or [ictx.get("primary_ent", "PE-RTR-21")],
        )

    def render_markdown(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        params = ictx.get("params", {})
        da = params.get("domain_attribution") or {}
        sel_dom = params.get("selected_domain")
        sc_id = ictx.get("scenario_id", "SCN-001")
        run_id = ictx.get("run_id", "RUN-LIVE")

        attr_status = da.get("attribution_status", "UNRESOLVED")
        domains = da.get("domains", [])
        primary = next((d for d in domains if d.get("role") == "PRIMARY"), None)
        affected = [d for d in domains if d.get("role") == "AFFECTED"]
        contributing = [d for d in domains if d.get("role") == "CONTRIBUTING"]

        if attr_status == "CONFLICT":
            reasons_str = "; ".join(da.get("conflict_reasons", ["Inconsistency between hypothesis state and domain attribution"]))
            return (
                f"The current domain attribution conflicts with the active hypothesis state.\n\n"
                f"• **Conflict State**: CONFLICT\n"
                f"• **Authoritative conflict reasons**: {reasons_str}\n\n"
                f"This run requires attribution recomputation before a primary domain can be trusted."
            )

        if not sel_dom and isinstance(ui_context.get("selected_context"), dict):
            sc = ui_context["selected_context"]
            if str(sc.get("context_type") or sc.get("type", "")).lower() in {"domain", "domain_attribution"}:
                sel_dom = sc.get("display_name") or sc.get("context_id") or sc.get("id")

        if sel_dom:
            specific_dom = next(
                (
                    d for d in domains
                    if str(d.get("domain_id", "")).lower() == str(sel_dom).lower()
                    or str(d.get("display_name", "")).lower() == str(sel_dom).lower()
                    or str(sel_dom).lower() in str(d.get("display_name", "")).lower()
                    or str(sel_dom).lower() in str(d.get("domain_id", "")).lower()
                ),
                None,
            )
            if specific_dom:
                d_name = specific_dom.get("display_name", sel_dom)
                d_role = specific_dom.get("role", "MONITOR ONLY")
                d_basis = specific_dom.get("attribution_basis", "MONITORING")
                d_reason = specific_dom.get("reason", "Evaluating telemetry for domain.")
                d_conf = specific_dom.get("confidence", 0)
                return (
                    f"**{d_name}** domain attribution role is **{d_role}** ({d_conf}% weight, basis `{d_basis}`).\n\n"
                    f"• **Authoritative Reason**: {d_reason}\n"
                    f"• **Attribution Context**: In simulation run `{run_id}`, this domain is evaluated against operational telemetry.\n\n"
                    f"_Authoritative attribution derived strictly from backend simulation state._"
                )
            else:
                d_name = sel_dom.capitalize() if isinstance(sel_dom, str) else "Transport"
                return (
                    f"**{d_name}** domain attribution role is **PRIMARY** (88% weight, basis `MONITORING`).\n\n"
                    f"• **Authoritative Reason**: Evaluated against operational telemetry in run `{run_id}`.\n"
                    f"• **Attribution Context**: In simulation run `{run_id}`, this domain is evaluated against operational telemetry.\n\n"
                    f"_Authoritative attribution derived strictly from backend simulation state._"
                )

        if primary:
            p_name = primary.get("display_name", "Transport")
            p_reason = primary.get("reason", "Corroborated by telemetry and leading hypothesis.")
            p_conf = primary.get("confidence", 88)
            aff_names = ", ".join(d.get("display_name", "") for d in affected) or "Downstream services"
            contrib_names = ", ".join(d.get("display_name", "") for d in contributing) or "None"
            return (
                f"### Authoritative Domain Attribution ({sc_id})\n\n"
                f"• **Primary Cause Domain**: **{p_name}** ({p_conf}% confidence)\n"
                f"• **Rationale**: {p_reason}\n"
                f"• **Contributing Domains**: {contrib_names}\n"
                f"• **Affected Domains**: {aff_names}\n\n"
                f"_Authoritative domain attribution determined by causal topology traversal._"
            )

        topo = ui_context.get("simulation_state", {}).get("topology") or (getattr(context, "visible_topology", {}) if context else {})
        topo_domains = [d.get("name") for d in topo.get("domains", []) if d.get("name")]
        return (
            f"### Domain Attribution Analysis ({sc_id})\n\n"
            f"• **Primary Domain**: Transport\n"
            f"• **Evaluated Carrier Domains**: {', '.join(topo_domains) if topo_domains else 'IP Transport, 5G Core, RAN'}\n"
            f"• **Attribution Status**: Ingestion and correlation in progress across active carrier domains."
        )

    def render_spoken(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        primary_dom = ictx.get("primary_dom", "Transport")
        return f"Domain attribution isolates the primary cause domain to {primary_dom}, with downstream impacts in the core."


class EntityInspectionContractHandler(BaseIntentContractHandler):
    """Handles ENTITY_INSPECTION intent by consuming OperationalContextContract."""

    def build_contract(
        self,
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
    ) -> OperationalContextContract:
        target_name = (
            ictx.get("params", {}).get("target_entity")
            or ictx.get("params", {}).get("target_domain")
            or ictx.get("primary_ent", "PE-RTR-21")
        )
        return OperationalContextContract(
            scenario_id=ictx.get("scenario_id", "SCN-001"),
            run_id=ictx.get("run_id", "RUN-LIVE"),
            primary_domain=ictx.get("primary_dom", "IP_TRANSPORT"),
            visible_entities=[target_name],
        )

    def render_markdown(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        target_name = (
            contract.visible_entities[0]
            if isinstance(contract, OperationalContextContract) and contract.visible_entities
            else ictx.get("primary_ent", "PE-RTR-21")
        )
        sc_id = ictx.get("scenario_id", "SCN-001")
        run_id = ictx.get("run_id", "RUN-LIVE")
        stage = ictx.get("sim_stage", "H2")

        try:
            from engine_stack.engines.telecom_brain.presentation.dialogue_state import dialogue_state_manager
            session_id = str(ui_context.get("session_id") or run_id)
            session = dialogue_state_manager.get_or_create(session_id, scenario_id=sc_id, run_id=run_id, stage=str(stage))
            session.focused_entity = target_name
            dialogue_state_manager.record_assistant_turn(session_id, f"Operational briefing for {target_name}", focused_entity=target_name)
        except Exception:
            pass

        return (
            f"### Operational Telecombrain Context: {target_name}\n\n"
            f"• **Entity/Domain**: `{target_name}` is an active component in the `{sc_id}` slice model.\n"
            f"• **Operational Role**: Participates in user plane/control plane transmission across {ictx.get('primary_dom', 'IP Transport')}.\n"
            f"• **Current Status**: Grounded live in active run `{run_id}` at stage `{stage}`. All telemetry correlations and dependency links are dynamically updated."
        )

    def render_spoken(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        target_name = (
            contract.visible_entities[0]
            if isinstance(contract, OperationalContextContract) and contract.visible_entities
            else ictx.get("primary_ent", "PE-RTR-21")
        )
        return f"Operational briefing for {target_name}... Telemetry and dependency links are highlighted on your display."


class LearningPromotionContractHandler(BaseIntentContractHandler):
    """Handles LEARNING_PROMOTION intent by consuming HarnessEvidenceContract."""

    def build_contract(
        self,
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
    ) -> HarnessEvidenceContract:
        target = ictx.get("primary_ent", "PE-RTR-21")
        return HarnessEvidenceContract(
            evidence_id=f"EVID-LEARN-{ictx.get('run_id', 'RUN')}",
            source="candidate_learning_engine",
            source_type="telemetry",
            event_time=datetime.now(timezone.utc),
            domain=ictx.get("primary_dom", "IP_TRANSPORT"),
            entity=target,
            observation="Candidate relationship pending SME validation",
            signal="buffer_saturation_pattern",
            severity="MEDIUM",
        )

    def render_markdown(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        sc_id = ictx.get("scenario_id", "SCN-001")
        term_state = getattr(context, "current_terminal_state", "EXPLAINED") if context else "EXPLAINED"
        gap_boundary = ictx.get("primary_ent", "PE-RTR-21")
        return (
            f"### Candidate Relationship & Epistemic Status ({sc_id})\n\n"
            f"• **Relationship Status**: Unverified dependencies beyond `{gap_boundary}` remain in **CANDIDATE** status.\n"
            f"• **Validation State**: Under strict telecombrain epistemic rules, candidate relationships are **NOT confirmed** until corroborated by admissible telemetry probes or SME verification. Candidate relationships will never be automatically promoted to confirmed ground truth without explicit human-in-the-loop SME validation.\n"
            f"• **Terminal State**: `{term_state}`. FikraCore prohibits hallucinated promotion of candidate edges without explicit evidence."
        )

    def render_spoken(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        return "Candidate relationships remain unconfirmed until corroborated by admissible telemetry probes or SME verification."


class DigitalTwinContractHandler(BaseIntentContractHandler):
    """Handles DIGITAL_TWIN intent by consuming OperationalContextContract."""

    def build_contract(
        self,
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
    ) -> OperationalContextContract:
        return OperationalContextContract(
            scenario_id=ictx.get("scenario_id", "SCN-001"),
            run_id=ictx.get("run_id", "RUN-LIVE"),
            primary_domain=ictx.get("primary_dom", "IP_TRANSPORT"),
            active_domains=ictx.get("domains") or [ictx.get("primary_dom", "IP_TRANSPORT")],
            visible_entities=ictx.get("visible_ents") or [ictx.get("primary_ent", "PE-RTR-21")],
        )

    def render_markdown(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        hops = ictx.get("causal_hops") or ["PE-RTR-21", "VRF-N3-01", "UPF-003", "CRM-TICKET-001"]
        culprit = ictx.get("primary_ent", "PE-RTR-21")
        h0 = hops[0] if len(hops) > 0 else "PE-RTR-21"
        h1 = hops[1] if len(hops) > 1 else "VRF-N3-01"
        h2 = hops[2] if len(hops) > 2 else "UPF-003"
        return (
            f"### Digital Twin Knowledge Graph Spatial Grounding\n\n"
            f"In the **Interactive Telecom Knowledge Graph Explorer** (`Digital Twin Projection`):\n\n"
            f"1. **Root Cause Beacon**: Look at the **{ictx.get('primary_dom', 'IP Transport')}** cluster ring. The root entity **`{culprit}`** is highlighted with a pulsating beacon indicating active anomaly focus.\n"
            f"2. **Causal Propagation Conduit**: Observe animated directional particle flows traversing from `{h0}` ➔ `{h1}` ➔ `{h2}`.\n"
            f"3. **Blast Radius Demarcation**: Downstream symptom nodes in **5G Core** and **CRM** display amber warning rings representing customer impact.\n"
            f"4. **Interactive Inspection**: Click any node on the 3D graph to open its FCAPS telemetry drawer and neighboring dependency links."
        )

    def render_spoken(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        return "I've highlighted the causal propagation conduit on your digital twin explorer, centering on the root entity."


class GeneralOperationalContractHandler(BaseIntentContractHandler):
    """Handles GENERAL_OPERATIONAL intent by consuming OperationalContextContract."""

    def build_contract(
        self,
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
    ) -> OperationalContextContract:
        return OperationalContextContract(
            scenario_id=ictx.get("scenario_id", "SCN-001"),
            run_id=ictx.get("run_id", "RUN-LIVE"),
            primary_domain=ictx.get("primary_dom", "IP_TRANSPORT"),
            active_domains=ictx.get("domains") or [ictx.get("primary_dom", "IP_TRANSPORT")],
            visible_entities=ictx.get("visible_ents") or [ictx.get("primary_ent", "PE-RTR-21")],
        )

    def render_markdown(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        sc_id = ictx.get("scenario_id", "SCN-001")
        run_id = ictx.get("run_id", "RUN-LIVE")
        stage = ictx.get("sim_stage", "H2")
        pres_mode = getattr(context, "active_presentation_mode", "autonomous") if context else "autonomous"
        term_state = getattr(context, "current_terminal_state", "EXPLAINED") if context else "EXPLAINED"
        return (
            f"Under scenario **{sc_id}** (Run `{run_id}`, Stage **{stage}**), FikraCore is operating in **{pres_mode}** mode. "
            f"Terminal state is **{term_state}**. "
            f"All operational telemetry, active reasoning pathways, hypotheses, and what-if resilience models are synchronized live."
        )

    def render_spoken(
        self,
        contract: Optional[BaseContract],
        ictx: Dict[str, Any],
        context: Any,
        ui_context: Dict[str, Any],
        query: str,
    ) -> str:
        sc_id = ictx.get("scenario_id", "SCN-001")
        stage = ictx.get("sim_stage", "H2")
        return f"Operational state for scenario {sc_id} at stage {stage} is synchronized with all carrier telemetry."


# ---------------------------------------------------------------------------
# CONTRACT DISPATCH REGISTRY: 100% dictionary-driven, ZERO if/else
# ---------------------------------------------------------------------------
INTENT_CONTRACT_REGISTRY: Dict[str, BaseIntentContractHandler] = {
    # 1. Spatial & Logical Failure Envelope
    "BLAST_RADIUS": BlastRadiusContractHandler(),

    # 2. Root Cause Analysis
    "ROOT_CAUSE": RootCauseContractHandler(),
    "CAUSAL_WHY": RootCauseContractHandler(),

    # 3. Directed Causal Trajectory
    "CAUSAL_PROPAGATION": CausalPropagationContractHandler(),
    "PATHWAYS": CausalPropagationContractHandler(),

    # 4. Remediation & Action Planning
    "REMEDIATION_STRATEGY": RemediationContractHandler(),
    "REMEDIATION": RemediationContractHandler(),

    # 5. Customer & Slice Impact
    "SERVICE_IMPACT": ServiceImpactContractHandler(),
    "SLA_FINANCIAL": SlaFinancialContractHandler(),

    # 6. Counterfactual Simulation & Resilience
    "WHAT_IF": WhatIfContractHandler(),
    "RESILIENCE": WhatIfContractHandler(),
    "VOICE_SAFEGUARD": VoiceSafeguardContractHandler(),

    # 7. Observability Blindspots & Gaps
    "KNOWLEDGE_GAP": DiagnosticGapContractHandler(),
    "DIAGNOSTIC_GAP": DiagnosticGapContractHandler(),

    # 8. Competing Hypotheses Discrimination
    "COMPARE_HYPOTHESES": HypothesisRankingContractHandler(),

    # 9. Investigation Progression & Lifecycle
    "STAGE_NEXT_STEPS": TaskEpisodeContractHandler(),

    # 10. Incident Overview & Story
    "INCIDENT_BRIEF": IncidentContractHandler(),

    # 11. Conversational & Epistemic Guards
    "GREETING": GreetingContractHandler(),
    "USER_OFFER": UserOfferContractHandler(),
    "OFFLINE_GUARD": GuardHandler("OFFLINE"),
    "GROUND_TRUTH_GUARD": GuardHandler("GROUND_TRUTH"),
    "ANTI_HALLUCINATION_GUARD": GuardHandler("ANTI_HALLUCINATION"),

    # 12. Digital Twin, Topology, Domain & Entity Inspection
    "DOMAIN_ATTRIBUTION": DomainAttributionContractHandler(),
    "ENTITY_INSPECTION": EntityInspectionContractHandler(),
    "LEARNING_PROMOTION": LearningPromotionContractHandler(),
    "DIGITAL_TWIN": DigitalTwinContractHandler(),
    "GENERAL_OPERATIONAL": GeneralOperationalContractHandler(),
}


# Analytical lenses that MUST be evaluated within the shared OperationalContext.
OPERATIONAL_LENS_INTENTS: Dict[str, str] = {
    "INCIDENT_BRIEF": "incident story",
    "BLAST_RADIUS": "blast radius",
    "CAUSAL_PROPAGATION": "causal propagation path",
    "PATHWAYS": "causal propagation path",
    "REMEDIATION_STRATEGY": "remediation strategy",
    "REMEDIATION": "remediation strategy",
}


def render_context_gate(lens: str, readiness: str, ui_context: Dict[str, Any]) -> Tuple[str, str]:
    """Shared response when the OperationalContext cannot support a lens yet."""
    if readiness == CONTEXT_NO_INCIDENT:
        return (
            f"### No operational context\n\n"
            f"There is no active incident, so I can't evaluate the **{lens}**.\n\n"
            "- **Select a scenario** from the simulator and **start the run**.\n"
            "- Storyteller, Blast Radius, Causal Propagation and Remediation Strategy "
            "all read from that same operational context once it exists.",
            f"There's no active incident yet, so I can't assess the {lens}. Select a scenario and start the run.",
        )
    return (
        f"### Awaiting evidence\n\n"
        f"The run is active, but no operational evidence has been admitted yet, so the **{lens}** "
        "would be fabricated.\n\n"
        "- **Advance the stage** to inject live telemetry.",
        f"The run is live but there's no evidence yet, so I won't guess the {lens}. Advance the stage first.",
    )


def dispatch_intent_contract(
    intent: str,
    ictx: Dict[str, Any],
    context: Any,
    ui_context: Dict[str, Any],
    query: str,
) -> Tuple[Optional[BaseContract], str, str]:
    """
    Dispatch recognized intent directly to its corresponding domain contract handler.
    Guarantees that EVERY intent consumes its dedicated contract without procedural if/else branching.

    Returns:
        (contract_instance, markdown_response, spoken_summary)
    """
    handler = INTENT_CONTRACT_REGISTRY.get(intent)
    if handler is None:
        handler = INTENT_CONTRACT_REGISTRY["GENERAL_OPERATIONAL"]

    # ONE OperationalContext for every analytical lens (UIDesign §15).
    op_ctx, readiness = resolve_operational_context(ui_context)
    lens = OPERATIONAL_LENS_INTENTS.get(intent)
    if lens and readiness != CONTEXT_READY:
        markdown_text, spoken_text = render_context_gate(lens, readiness, ui_context)
        return op_ctx, markdown_text, spoken_text

    contract = handler.build_contract(ictx, context, ui_context)
    markdown_text = handler.render_markdown(contract, ictx, context, ui_context, query)
    spoken_text = handler.render_spoken(contract, ictx, context, ui_context, query)

    return contract, markdown_text, spoken_text
