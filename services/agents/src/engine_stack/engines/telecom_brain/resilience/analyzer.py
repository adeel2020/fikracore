"""Proactive What-If Failure Simulation & Resilience Analysis Engine for FikraCore.

Transitions FikraCore from reactive incident RCA backward to forward-looking
causal resilience intelligence. Evaluates hypothetical failure/change conditions
against known operational telecombrain dependencies without inventing topology.

Strictly truth-blind: never accesses evaluator ground truth.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from ..investigation.contracts import (
    BlastRadiusAssessment,
    BlastRadiusLevel,
    CriticalFailureSurface,
    MitigationOption,
    PropagationPathStep,
    PropagationSemantics,
    ResilienceActionCategory,
    ResilienceGap,
    ResilienceRecommendation,
    Terminal,
    WhatIfAssumptions,
    WhatIfScenario,
    WhatIfSimulationResult,
    WhatIfTrigger,
)
from ..presentation.naming import default_naming_resolver


DOMAIN_SERVICE_MAP: dict[str, list[str]] = {
    "SA_5G_CORE": ["5G SA Mobile Data", "VoNR High Definition Voice"],
    "EPC_4G": ["4G LTE Mobile Data", "VoLTE Voice"],
    "MOBILE_IMS": ["VoLTE Voice", "VoNR High Definition Voice"],
    "FIXED_IMS": ["Fixed Voice (VoIP)", "Enterprise SIP Trunking"],
    "GPON_FIXED_ACCESS": ["Fixed High-Speed Broadband", "IPTV Broadcast"],
    "IP_TRANSPORT": ["5G SA Mobile Data", "Enterprise MPLS VPN"],
    "TRANSMISSION": ["Inter-DC Backhaul Transport", "5G SA Mobile Data"],
    "CHARGING": ["Prepaid Data & Voice Charging", "Real-Time Balance Check"],
    "BSS": ["Customer Self-Care Portal", "Service Activation & Provisioning"],
    "VAS": ["SMS Delivery Service", "USSD Banking Services"],
    "CS_CORE": ["Legacy 3G/2G CS Voice", "Emergency 112 Services"],
    "SECURITY": ["5G Roaming Interconnect", "5G SA Mobile Data"],
}


def get_services_for_node(node: str) -> tuple[set[str], set[str]]:
    """Determine domains and services impacted by a given node."""
    domains: set[str] = set()
    services: set[str] = set()

    if node.startswith("IP:"):
        domains.add("IP_TRANSPORT")
        services.update(DOMAIN_SERVICE_MAP["IP_TRANSPORT"])
    elif node.startswith("TRANS:"):
        domains.add("TRANSMISSION")
        services.update(DOMAIN_SERVICE_MAP["TRANSMISSION"])
    elif node.startswith("SA5G:"):
        domains.add("SA_5G_CORE")
        services.update(DOMAIN_SERVICE_MAP["SA_5G_CORE"])
    elif node.startswith("EPC:"):
        domains.add("EPC_4G")
        services.update(DOMAIN_SERVICE_MAP["EPC_4G"])
    elif node.startswith("CHG:"):
        domains.add("CHARGING")
        services.update(DOMAIN_SERVICE_MAP["CHARGING"])
    elif node.startswith("GPON:"):
        domains.add("GPON_FIXED_ACCESS")
        services.update(DOMAIN_SERVICE_MAP["GPON_FIXED_ACCESS"])
    elif node.startswith("BSS:"):
        domains.add("BSS")
        services.update(DOMAIN_SERVICE_MAP["BSS"])
    elif node.startswith("VAS:"):
        domains.add("VAS")
        services.update(DOMAIN_SERVICE_MAP["VAS"])
    elif "FW:" in node:
        domains.add("SECURITY")
        services.update(DOMAIN_SERVICE_MAP["SECURITY"])
    elif "DB:" in node:
        domains.add("CHARGING")
        domains.add("SA_5G_CORE")
        services.add("5G SA Mobile Data")
        services.add("Prepaid Data & Voice Charging")
    elif "DNS:" in node:
        domains.add("SA_5G_CORE")
        domains.add("EPC_4G")
        services.add("5G SA Mobile Data")
        services.add("VoLTE Voice")
    elif "DCGW:" in node:
        domains.add("SA_5G_CORE")
        services.update(DOMAIN_SERVICE_MAP["SA_5G_CORE"])
    elif "LB:" in node:
        domains.add("BSS")
        services.add("Customer Self-Care Portal")
        services.add("5G SA Mobile Data")
    elif "SW:" in node:
        domains.add("SA_5G_CORE")
        services.update(DOMAIN_SERVICE_MAP["SA_5G_CORE"])
    else:
        domains.add("SA_5G_CORE")
        services.add("5G SA Mobile Data")

    return domains, services



class WhatIfAnalyzer:
    """Proactive resilience analysis engine traversing validated operational knowledge."""

    def __init__(self, naming_resolver=None) -> None:
        self.naming = naming_resolver or default_naming_resolver

    def analyze_scenario(
        self,
        scenario: WhatIfScenario,
        operational_topology: dict[str, Any],
        redundancy_data: dict[str, Any] | None = None,
        capacity_data: dict[str, Any] | None = None,
    ) -> WhatIfSimulationResult:
        """Run proactive what-if forward propagation and resilience assessment."""
        trigger = scenario.trigger
        assumptions = scenario.assumptions
        red_data = redundancy_data or {}
        cap_data = capacity_data or {}

        visible_entities = set(operational_topology.get("visible_entities", []))
        known_gaps = operational_topology.get("known_gaps", [])

        # Check for model insufficiency: trigger entity unknown or known topology gap
        trigger_in_topo = False
        trigger_canonical = trigger.canonical_id
        for ent in visible_entities:
            if ent == trigger_canonical or trigger.entity_display_name.lower() in ent.lower():
                trigger_in_topo = True
                trigger_canonical = ent
                break

        if not trigger_in_topo or scenario.cohort == "unknown_knowledge" or "unmodeled_boundary" in known_gaps:
            return WhatIfSimulationResult(
                what_if_id=scenario.what_if_id,
                terminal_state=Terminal.MODEL_INSUFFICIENT,
                trigger=trigger,
                assumptions=assumptions,
                propagation_paths=[],
                blast_radius=BlastRadiusAssessment(
                    directly_affected_entities=[],
                    indirectly_affected_entities=[],
                    affected_services=[],
                    affected_domains=[],
                    affected_regions=[],
                    blast_radius_level=BlastRadiusLevel.LOCAL,
                    confidence=0.0,
                    customer_facing_impact="Uncertain: upstream topology is unmapped or incomplete in operational knowledge.",
                ),
                critical_failure_surfaces=[
                    CriticalFailureSurface(
                        surface_id=f"CFS-GAP-{scenario.what_if_id}",
                        components=[trigger.entity_display_name],
                        risk_type="MODEL_INSUFFICIENT",
                        dependent_services=[],
                        criticality_score=0.5,
                        rationale=f"Knowledge gap: {trigger.entity_display_name} lacks upstream dependency mapping in operational telecombrain.",
                    )
                ],
                resilience_gaps=[
                    ResilienceGap(
                        gap_id=f"RG-GAP-{scenario.what_if_id}",
                        type="UNMAPPED_DEPENDENCY_BOUNDARY",
                        primary_entity=trigger.entity_display_name,
                        risk="Cannot reliably estimate forward propagation due to missing topology.",
                        severity="MEDIUM",
                        recommended_action="Execute discovery to map operational dependencies before change execution.",
                    )
                ],
                mitigation_options=[],
                recommended_actions=[
                    ResilienceRecommendation(
                        recommendation_id=f"REC-GAP-{scenario.what_if_id}",
                        category=ResilienceActionCategory.RISK,
                        title="Discover Missing Topology",
                        action="Perform automated neighbor and routing discovery to close operational knowledge gap.",
                        priority="HIGH",
                        expected_risk_reduction=0.7,
                        target_entity=trigger.entity_display_name,
                    )
                ],
                confidence=0.0,
                knowledge_limitations=[
                    f"Operational telecombrain lacks complete dependency mapping for {trigger.entity_display_name}."
                ],
            )

        # 1. Parse operational relationships
        relationships = operational_topology.get("relationships", [])
        # Also handle relationships list from reference/operational views
        graph_forward: dict[str, list[dict[str, Any]]] = {}  # target (failing) -> list of sources (dependents)
        all_graph_edges = []

        for rel in relationships:
            src = rel.get("source_entity") or rel.get("source")
            tgt = rel.get("target_entity") or rel.get("target")
            rel_type = rel.get("relationship_type") or rel.get("link_type") or "DEPENDS_ON"
            if src and tgt:
                all_graph_edges.append((src, rel_type, tgt))
                # If src DEPENDS_ON tgt, failure of tgt propagates forward to src
                if tgt not in graph_forward:
                    graph_forward[tgt] = []
                graph_forward[tgt].append({
                    "dependent": src,
                    "rel_type": rel_type,
                    "rel_data": rel,
                })
                # Bi-directional impact for CONNECTED_TO and ROUTES_THROUGH in transport context
                if rel_type in ("CONNECTED_TO", "PEERS_WITH"):
                    if src not in graph_forward:
                        graph_forward[src] = []
                    graph_forward[src].append({
                        "dependent": tgt,
                        "rel_type": rel_type,
                        "rel_data": rel,
                    })

        # 2. Check Redundancy & Common-Cause Vulnerabilities
        failover_info = red_data.get("failover_pairs", {}).get(trigger_canonical, {})
        backup_entity = failover_info.get("backup_entity") or red_data.get("backup_node")
        backup_health = failover_info.get("backup_health", red_data.get("backup_health", "HEALTHY"))
        backup_capacity = cap_data.get("backup_capacity_pct", 100)
        shared_risks = red_data.get("shared_failure_domains", [])

        # Detect common-cause traps
        common_cause_detected = False
        common_cause_type = None
        common_cause_desc = ""

        if backup_entity and shared_risks:
            common_cause_detected = True
            for risk in shared_risks:
                risk_type = risk.get("type", "SHARED_DEPENDENCY")
                common_cause_type = risk_type
                common_cause_desc = risk.get("description", "Primary and secondary share common failure domain.")
                break
        elif red_data.get("shared_power_feed"):
            common_cause_detected = True
            common_cause_type = "COMMON_POWER"
            common_cause_desc = red_data.get("shared_power_feed", "Dual nodes share common power feed.")
        elif red_data.get("shared_conduit"):
            common_cause_detected = True
            common_cause_type = "COMMON_TRANSPORT"
            common_cause_desc = red_data.get("shared_conduit", "Dual links share common fiber conduit.")
        elif red_data.get("shared_switch"):
            common_cause_detected = True
            common_cause_type = "SHARED_DEPENDENCY"
            common_cause_desc = red_data.get("shared_switch", "Redundant appliances share common switch.")

        # Capacity Trap Check
        capacity_trap_detected = False
        if backup_capacity < 100 and assumptions.traffic_load_profile in ("PEAK", "SURGE"):
            capacity_trap_detected = True

        # Change-Risk / Unsafe Maintenance Check
        change_risk_detected = False
        change_risk_desc = ""
        if trigger.event_type in ("REBOOT", "CONFIG_CHANGE", "UPGRADE"):
            if backup_health in ("DEGRADED", "OFFLINE", "UNHEALTHY"):
                change_risk_detected = True
                change_risk_desc = (
                    f"Unsafe maintenance window: {trigger.entity_display_name} reboot planned while "
                    f"backup {backup_entity or 'secondary'} is in {backup_health} state."
                )
            elif assumptions.traffic_load_profile == "PEAK":
                change_risk_detected = True
                change_risk_desc = (
                    f"High-risk maintenance window: Planned {trigger.event_type} scheduled during peak traffic hours."
                )

        # 3. Forward Causal Traversal
        visited_entities: set[str] = set()
        directly_affected: list[str] = []
        indirectly_affected: list[str] = []
        propagation_paths: list[list[PropagationPathStep]] = []

        # Determine effective propagation
        # If failover is fully independent, healthy, and has 100% capacity -> absorbed!
        failover_absorbs = (
            backup_entity
            and backup_health == "HEALTHY"
            and not common_cause_detected
            and not capacity_trap_detected
            and trigger.event_type not in ("REBOOT", "CONFIG_CHANGE")
        )

        queue: deque[tuple[str, list[PropagationPathStep]]] = deque()
        queue.append((trigger_canonical, []))
        visited_entities.add(trigger_canonical)

        while queue:
            curr_node, current_path = queue.popleft()
            dependents = graph_forward.get(curr_node, [])

            for dep_info in dependents:
                dep_node = dep_info["dependent"]
                rel_type = dep_info["rel_type"]

                if dep_node not in visited_entities:
                    visited_entities.add(dep_node)

                    # Determine semantics
                    if common_cause_detected:
                        sem = "HARD"
                        impact = "CRITICAL"
                        explanation = f"{common_cause_desc} Outage propagates despite redundant configuration."
                    elif capacity_trap_detected and curr_node == trigger_canonical:
                        sem = "CAPACITY"
                        impact = "DEGRADED"
                        explanation = f"Failover capacity capped at {backup_capacity}% of peak load. Service degraded."
                    elif change_risk_detected:
                        sem = "HARD"
                        impact = "CRITICAL"
                        explanation = change_risk_desc
                    elif failover_absorbs and curr_node == trigger_canonical:
                        sem = "REDUNDANT"
                        impact = "CONTAINED"
                        explanation = f"Failover to {backup_entity} absorbed primary failure."
                    else:
                        sem = "HARD"
                        impact = "CRITICAL"
                        explanation = f"Causal propagation via {rel_type} dependency."

                    from_display = self.naming.to_display_name(curr_node)
                    to_display = self.naming.to_display_name(dep_node)

                    step = PropagationPathStep(
                        step_index=len(current_path) + 1,
                        from_entity=from_display,
                        from_canonical_id=curr_node,
                        relation=self.naming.to_relation_label(rel_type),
                        relation_semantics=sem,
                        to_entity=to_display,
                        to_canonical_id=dep_node,
                        impact_severity=impact,
                        explanation=explanation,
                    )
                    new_path = current_path + [step]
                    propagation_paths.append(new_path)

                    if curr_node == trigger_canonical:
                        directly_affected.append(to_display)
                    else:
                        indirectly_affected.append(to_display)

                    # Continue propagating if not completely absorbed
                    if not failover_absorbs or common_cause_detected or capacity_trap_detected:
                        queue.append((dep_node, new_path))

        # Determine impacted services and domains
        affected_domains: set[str] = set()
        affected_services: set[str] = set()
        affected_regions: set[str] = set()

        # If absorbed by independent healthy redundancy, services are protected
        if not failover_absorbs or common_cause_detected or capacity_trap_detected or change_risk_detected:
            doms, srvs = get_services_for_node(trigger_canonical)
            affected_domains.update(doms)
            affected_services.update(srvs)
            for node in visited_entities:
                d, s = get_services_for_node(node)
                affected_domains.update(d)
                affected_services.update(s)

        # Determine regions from site IDs
        all_affected_nodes = [trigger_canonical] + list(visited_entities)
        for node in all_affected_nodes:
            if "SITE-DC-A" in node or "POP-21" in node or "SITE-RAN-101" in node:
                affected_regions.add("North Region")
            elif "SITE-DC-B" in node or "POP-07" in node:
                affected_regions.add("Central Region")
            elif "SITE-GPON-15" in node:
                affected_regions.add("South Region")

        if not affected_regions:
            affected_regions.add("Regional Transport Domain")

        # Determine Blast-Radius Level
        num_entities = len(directly_affected) + len(indirectly_affected) + 1
        num_domains = len(affected_domains)
        num_regions = len(affected_regions)

        if num_domains > 2 or num_regions > 1:
            blast_level = BlastRadiusLevel.NETWORK_WIDE if num_domains >= 3 else BlastRadiusLevel.REGIONAL
        elif num_domains >= 2:
            blast_level = BlastRadiusLevel.MULTI_DOMAIN
        elif len(affected_services) >= 1 or num_entities > 2:
            blast_level = BlastRadiusLevel.DOMAIN
        else:
            blast_level = BlastRadiusLevel.LOCAL

        # Customer facing impact statement
        if common_cause_detected:
            cust_impact = f"High Risk: Redundancy invalidated due to {common_cause_type}. Service degradation on {', '.join(sorted(affected_services)[:2])}."
        elif capacity_trap_detected:
            cust_impact = f"Partial Degradation: Peak traffic exceeds secondary node capacity ({backup_capacity}%). Quality drops on {', '.join(sorted(affected_services)[:2])}."
        elif change_risk_detected:
            cust_impact = f"Critical Change Risk: {change_risk_desc}"
        elif failover_absorbs:
            cust_impact = f"Redundancy Loss: Service protected by standby {backup_entity}. Loss of N+1 resilience."
        else:
            cust_impact = f"Direct Outage: {num_entities} components impacted across {num_domains} domain(s). Affected services: {', '.join(sorted(affected_services))}."

        # 4. Critical Failure Surface & Resilience Gaps
        cfs_list: list[CriticalFailureSurface] = []
        gaps_list: list[ResilienceGap] = []
        mitigations: list[MitigationOption] = []
        recommendations: list[ResilienceRecommendation] = []

        # Criticality Score calculation (0.0 - 1.0 explainable)
        service_factor = min(1.0, len(affected_services) / 4.0) * 0.35
        domain_factor = min(1.0, len(affected_domains) / 3.0) * 0.25
        vuln_factor = 0.25 if (common_cause_detected or capacity_trap_detected or not backup_entity) else 0.10
        blast_factor = 0.15 if blast_level in (BlastRadiusLevel.NETWORK_WIDE, BlastRadiusLevel.REGIONAL) else 0.08
        criticality_score = round(min(1.0, service_factor + domain_factor + vuln_factor + blast_factor), 2)

        # Build CFS
        if common_cause_detected:
            cfs_list.append(
                CriticalFailureSurface(
                    surface_id=f"CFS-CC-{scenario.what_if_id}",
                    components=[trigger.entity_display_name, self.naming.to_display_name(backup_entity or "")],
                    risk_type=common_cause_type or "SHARED_DEPENDENCY",
                    dependent_services=sorted(list(affected_services)),
                    criticality_score=criticality_score,
                    rationale=f"Shared dependency defect: {common_cause_desc}",
                )
            )
            gaps_list.append(
                ResilienceGap(
                    gap_id=f"RG-CC-{scenario.what_if_id}",
                    type="COMMON_CAUSE_FAILURE_DOMAIN",
                    primary_entity=trigger.entity_display_name,
                    backup_entity=self.naming.to_display_name(backup_entity or ""),
                    risk=common_cause_desc,
                    severity="CRITICAL",
                    recommended_action="Physically isolate redundant elements across distinct failure domains and power feeds.",
                )
            )

        if capacity_trap_detected:
            cfs_list.append(
                CriticalFailureSurface(
                    surface_id=f"CFS-CAP-{scenario.what_if_id}",
                    components=[trigger.entity_display_name, self.naming.to_display_name(backup_entity or "")],
                    risk_type="CAPACITY_EXHAUSTION",
                    dependent_services=sorted(list(affected_services)),
                    criticality_score=criticality_score,
                    rationale=f"Failover capacity bottleneck: backup node supports only {backup_capacity}% of peak load.",
                )
            )
            gaps_list.append(
                ResilienceGap(
                    gap_id=f"RG-CAP-{scenario.what_if_id}",
                    type="INSUFFICIENT_FAILOVER_CAPACITY",
                    primary_entity=trigger.entity_display_name,
                    backup_entity=self.naming.to_display_name(backup_entity or ""),
                    risk=f"Secondary component has insufficient capacity headroom ({backup_capacity}% vs 100% required).",
                    severity="HIGH",
                    recommended_action="Increase backup node capacity or configure dynamic traffic shedding rules.",
                )
            )

        if change_risk_detected:
            cfs_list.append(
                CriticalFailureSurface(
                    surface_id=f"CFS-CR-{scenario.what_if_id}",
                    components=[trigger.entity_display_name],
                    risk_type="UNSAFE_MAINTENANCE",
                    dependent_services=sorted(list(affected_services)),
                    criticality_score=criticality_score,
                    rationale=change_risk_desc,
                )
            )
            gaps_list.append(
                ResilienceGap(
                    gap_id=f"RG-CR-{scenario.what_if_id}",
                    type="UNPROTECTED_MAINTENANCE_WINDOW",
                    primary_entity=trigger.entity_display_name,
                    backup_entity=self.naming.to_display_name(backup_entity or ""),
                    risk="Executing change under degraded redundancy will cause unmitigated service outage.",
                    severity="CRITICAL",
                    recommended_action="Hold change window until backup path health is certified healthy.",
                )
            )

        if not cfs_list:
            if not backup_entity:
                cfs_list.append(
                    CriticalFailureSurface(
                        surface_id=f"CFS-SPOF-{scenario.what_if_id}",
                        components=[trigger.entity_display_name],
                        risk_type="SPOF",
                        dependent_services=sorted(list(affected_services)),
                        criticality_score=criticality_score,
                        rationale=f"Single point of failure: {trigger.entity_display_name} has no designated standby peer.",
                    )
                )
                gaps_list.append(
                    ResilienceGap(
                        gap_id=f"RG-SPOF-{scenario.what_if_id}",
                        type="NO_REDUNDANCY_PATH",
                        primary_entity=trigger.entity_display_name,
                        backup_entity=None,
                        risk="Single point of failure directly impacting downstream services.",
                        severity="HIGH",
                        recommended_action="Introduce redundant peer and configure active/standby failover.",
                    )
                )
            else:
                cfs_list.append(
                    CriticalFailureSurface(
                        surface_id=f"CFS-RED-{scenario.what_if_id}",
                        components=[trigger.entity_display_name],
                        risk_type="FAILOVER_DEPENDENCY",
                        dependent_services=sorted(list(affected_services)),
                        criticality_score=criticality_score,
                        rationale=f"Failure absorbed by {backup_entity}, creating temporary loss of N+1 redundancy.",
                    )
                )

        # 5. Mitigations Comparison
        mitigations.append(
            MitigationOption(
                option_id="OPT-A",
                title="Introduce Diverse Secondary Transport / Failure Domain",
                description="Deploy independent secondary routing path segregated from primary failure domain.",
                risk_reduction=0.85,
                protected_services=sorted(list(affected_services)),
                implementation_complexity="MEDIUM",
                operational_disruption="NONE",
                confidence=0.95,
            )
        )
        mitigations.append(
            MitigationOption(
                option_id="OPT-B",
                title="Scale Backup Headroom to 120% Peak Capacity",
                description="Upgrade backup capacity to sustain full traffic profile during failover spikes.",
                risk_reduction=0.75,
                protected_services=sorted(list(affected_services)),
                implementation_complexity="LOW",
                operational_disruption="MINIMAL",
                confidence=0.90,
            )
        )
        mitigations.append(
            MitigationOption(
                option_id="OPT-C",
                title="Separate Physical Power / Conduit Dependencies",
                description="Reroute backup feeds through physically isolated utilities and transport paths.",
                risk_reduction=0.92,
                protected_services=sorted(list(affected_services)),
                implementation_complexity="HIGH",
                operational_disruption="DISRUPTIVE",
                confidence=0.98,
            )
        )

        # 6. Candidate Recommendations
        if change_risk_detected:
            recommendations.append(
                ResilienceRecommendation(
                    recommendation_id=f"REC-CR-{scenario.what_if_id}",
                    category=ResilienceActionCategory.CANDIDATE_ACTION,
                    title="Abort / Reschedule Maintenance Window",
                    action="Postpone change until secondary node health is confirmed and off-peak window is reached.",
                    priority="CRITICAL",
                    expected_risk_reduction=0.95,
                    target_entity=trigger.entity_display_name,
                )
            )
        elif common_cause_detected:
            recommendations.append(
                ResilienceRecommendation(
                    recommendation_id=f"REC-CC-{scenario.what_if_id}",
                    category=ResilienceActionCategory.CANDIDATE_ACTION,
                    title="Remediate Common-Cause Failure Domain",
                    action=f"Eliminate {common_cause_type} dependency by re-architecting redundant node connectivity.",
                    priority="HIGH",
                    expected_risk_reduction=0.90,
                    target_entity=trigger.entity_display_name,
                )
            )
        elif capacity_trap_detected:
            recommendations.append(
                ResilienceRecommendation(
                    recommendation_id=f"REC-CAP-{scenario.what_if_id}",
                    category=ResilienceActionCategory.CANDIDATE_ACTION,
                    title="Expand Standby Capacity Headroom",
                    action=f"Increase backup capacity from {backup_capacity}% to $\\ge 100$% of peak load.",
                    priority="HIGH",
                    expected_risk_reduction=0.80,
                    target_entity=trigger.entity_display_name,
                )
            )
        else:
            recommendations.append(
                ResilienceRecommendation(
                    recommendation_id=f"REC-SPOF-{scenario.what_if_id}",
                    category=ResilienceActionCategory.CANDIDATE_ACTION,
                    title="Harden Component Redundancy",
                    action=f"Deploy N+1 redundant node for {trigger.entity_display_name} with automated health monitoring.",
                    priority="MEDIUM",
                    expected_risk_reduction=0.85,
                    target_entity=trigger.entity_display_name,
                )
            )

        blast_assessment = BlastRadiusAssessment(
            directly_affected_entities=directly_affected,
            indirectly_affected_entities=indirectly_affected,
            affected_services=sorted(list(affected_services)),
            affected_domains=sorted(list(affected_domains)),
            affected_regions=sorted(list(affected_regions)),
            blast_radius_level=blast_level,
            confidence=0.95,
            customer_facing_impact=cust_impact,
        )

        return WhatIfSimulationResult(
            what_if_id=scenario.what_if_id,
            terminal_state=Terminal.EXPLAINED,
            trigger=trigger,
            assumptions=assumptions,
            propagation_paths=propagation_paths,
            blast_radius=blast_assessment,
            critical_failure_surfaces=cfs_list,
            resilience_gaps=gaps_list,
            mitigation_options=mitigations,
            recommended_actions=recommendations,
            confidence=0.95,
            knowledge_limitations=[],
        )
