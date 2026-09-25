"""Agent Registry for Zaki v1 Dark NOC."""

from __future__ import annotations

from typing import Dict, List, Optional
from ..domain.contracts.agent import (
    AgentLifecycle,
    AgentManifestContract,
    AgentManifestSpec,
    AgentMetadata,
    AgentPolicyProfile,
)
from ..domain.enums import AgentLifecycleState, AuthorityLevel
from .capability_registry import default_domain_capability_registry


class AgentRegistry:
    """Manages discoverable domain agent capabilities and metadata."""

    def __init__(self) -> None:
        self._agents: Dict[str, AgentManifestContract] = {}
        self._bootstrap_default_domain_agents()

    def register_agent(self, manifest: AgentManifestContract) -> None:
        self._agents[manifest.metadata.id] = manifest
        for cap in manifest.spec.capabilities:
            default_domain_capability_registry.register_capability(cap, manifest.metadata.id)

    def get_agent(self, agent_id: str) -> Optional[AgentManifestContract]:
        return self._agents.get(agent_id)

    def list_agents(self, domain: Optional[str] = None) -> List[AgentManifestContract]:
        agents = list(self._agents.values())
        if domain:
            agents = [a for a in agents if a.metadata.domain.upper() == domain.upper()]
        return agents

    def find_by_capability(self, capability: str) -> List[AgentManifestContract]:
        agent_ids = default_domain_capability_registry.find_agents_for_capability(capability)
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    def _bootstrap_default_domain_agents(self) -> None:
        default_agents_data = [
            {
                "id": "agent-ps",
                "name": "PS Domain Agent",
                "domain": "PS",
                "capabilities": ["pdu-session-investigation", "upf-health-analysis", "pfcp-analysis", "ps-change-analysis"],
                "accepted_intents": ["INVESTIGATE_SERVICE_DEGRADATION", "EXPLAIN_HYPOTHESIS"],
                "tools": ["metric.query", "log.query", "trace.query", "topology.query"],
            },
            {
                "id": "agent-cs",
                "name": "CS Domain Agent",
                "domain": "CS",
                "capabilities": ["msc-analysis", "isup-tcap-analysis", "call-drop-investigation"],
                "accepted_intents": ["INVESTIGATE_SERVICE_DEGRADATION"],
                "tools": ["alarm.query", "kpi.query", "trace.analyze"],
            },
            {
                "id": "agent-ran",
                "name": "RAN Domain Agent",
                "domain": "RAN",
                "capabilities": ["cell-degradation-analysis", "gnb-alarms-investigation", "rf-coverage-analysis"],
                "accepted_intents": ["INVESTIGATE_SERVICE_DEGRADATION"],
                "tools": ["alarm.query", "kpi.query", "topology.query"],
            },
            {
                "id": "agent-ip-transport",
                "name": "IP Transport Agent",
                "domain": "IP_TRANSPORT",
                "capabilities": ["router-bgp-investigation", "mpls-lsp-path-analysis", "transport-change-correlation"],
                "accepted_intents": ["INVESTIGATE_SERVICE_DEGRADATION", "EXPLAIN_HYPOTHESIS", "DISCOVER_KNOWLEDGE_GAPS"],
                "tools": ["alarm.query", "metric.query", "routing.query", "path.analyze"],
            },
            {
                "id": "agent-in-ocs",
                "name": "IN/OCS Domain Agent",
                "domain": "IN_OCS",
                "capabilities": ["diameter-charging-analysis", "balance-quota-investigation"],
                "accepted_intents": ["INVESTIGATE_SERVICE_DEGRADATION"],
                "tools": ["kpi.query", "log.query"],
            },
            {
                "id": "agent-vas",
                "name": "VAS Domain Agent",
                "domain": "VAS",
                "capabilities": ["smsc-analysis", "mms-investigation"],
                "accepted_intents": ["INVESTIGATE_SERVICE_DEGRADATION"],
                "tools": ["alarm.query", "log.query"],
            },
            {
                "id": "agent-igw",
                "name": "IGW Domain Agent",
                "domain": "IGW",
                "capabilities": ["roaming-interconnect-investigation", "peering-analysis"],
                "accepted_intents": ["INVESTIGATE_SERVICE_DEGRADATION"],
                "tools": ["traffic.query", "kpi.query"],
            },
            {
                "id": "agent-infra",
                "name": "Infra Domain Agent",
                "domain": "INFRA",
                "capabilities": ["power-hvac-investigation", "chassis-hardware-check"],
                "accepted_intents": ["INVESTIGATE_SERVICE_DEGRADATION"],
                "tools": ["alarm.query", "metric.query"],
            },
            {
                "id": "agent-it",
                "name": "IT Domain Agent",
                "domain": "IT",
                "capabilities": ["bss-crm-investigation", "ldap-auth-investigation"],
                "accepted_intents": ["INVESTIGATE_SERVICE_DEGRADATION"],
                "tools": ["ticket.query", "change.query"],
            },
        ]

        for item in default_agents_data:
            manifest = AgentManifestContract(
                metadata=AgentMetadata(
                    id=item["id"],
                    name=item["name"],
                    domain=item["domain"],
                ),
                spec=AgentManifestSpec(
                    capabilities=item["capabilities"],
                    accepted_intents=item["accepted_intents"],
                    tools=item["tools"],
                    policies=AgentPolicyProfile(
                        risk_level="MEDIUM",
                        authority_level=AuthorityLevel.LEVEL_1_ANALYZE,
                        allowed_tools=item["tools"],
                    ),
                    lifecycle=AgentLifecycle(state=AgentLifecycleState.ACTIVE),
                ),
            )
            self.register_agent(manifest)


default_agent_registry = AgentRegistry()
