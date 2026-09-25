"""Decoupled Capability Registry for Domain Agents."""

from __future__ import annotations

from typing import Dict, List, Optional
from ..domain.contracts.agent import AgentManifestContract


class DomainCapabilityRegistry:
    """Maintains mapping between abstract capability IDs and implementing agent manifests."""

    def __init__(self) -> None:
        # capability_id -> List[agent_id]
        self._capability_to_agents: Dict[str, List[str]] = {}

    def register_capability(self, capability_id: str, agent_id: str) -> None:
        if capability_id not in self._capability_to_agents:
            self._capability_to_agents[capability_id] = []
        if agent_id not in self._capability_to_agents[capability_id]:
            self._capability_to_agents[capability_id].append(agent_id)

    def find_agents_for_capability(self, capability_id: str) -> List[str]:
        return self._capability_to_agents.get(capability_id, [])

    def list_all_capabilities(self) -> Dict[str, List[str]]:
        return dict(self._capability_to_agents)


default_domain_capability_registry = DomainCapabilityRegistry()
