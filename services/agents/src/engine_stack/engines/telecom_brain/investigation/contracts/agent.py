"""
Agent Manifest & Capability Contracts
====================================
This module defines the agent persona contracts, authority ceilings, and lifecycle states
for autonomous and semi-autonomous telecom domain agents.

Design Principles:
- FikraCore defines the canonical AgentManifestContract (Tier 1 capability specifications).
- Zaki orchestrates active agent runtimes (Tier 2 execution instances).
- Authority levels enforce strict guardrails preventing unauthorized mutations to network elements.
"""

from enum import Enum
from pydantic import Field
from .base import Contract


class AuthorityLevel(str, Enum):
    """
    Authority tier determining agent operational privileges and execution safety ceilings.
    """
    LEVEL_1_ANALYZE = "LEVEL_1_ANALYZE"       # Read-only telemetry, counter inspections, log queries
    LEVEL_2_DIAGNOSE = "LEVEL_2_DIAGNOSE"     # Active discrimination probes (e.g. ping, trace, synthetic tests)
    LEVEL_3_EXECUTE = "LEVEL_3_EXECUTE"       # Controlled remediation execution (Strictly requires HITL approval)


class AgentLifecycleState(str, Enum):
    """
    Operational lifecycle health state of an autonomous specialist agent.
    """
    ACTIVE = "ACTIVE"           # Fully operational, ready to accept diagnostic or investigation tasks
    DEGRADED = "DEGRADED"       # Reduced capabilities (e.g., downstream EMS/SNMP connection down)
    DISABLED = "DISABLED"       # Administratively taken out of service
    MAINTENANCE = "MAINTENANCE" # Under calibration, synthetic testing, or model retraining


class AgentManifestContract(Contract):
    """
    Canonical definition of a specialist telecom domain agent.

    Attributes:
        agent_id: Semantic agent identifier (e.g., 'AGENT_IP_TRANSPORT_SME').
        display_name: Formatted name presented in Zaki's UI and audit logs.
        domain: Primary domain jurisdiction (e.g., 'IP_TRANSPORT').
        authority_level: Operational ceiling for automated diagnostic & remediation actions.
        lifecycle_state: Current operational health status of the agent.
        authorized_tools: Whitelist of tool identifiers the agent is permitted to invoke.
        managed_entities: Entity categories or regex patterns the agent has jurisdiction over.
        version: Semantic version of the agent's capability manifest.
    """
    agent_id: str = Field(description="Unique semantic agent identifier (e.g., 'AGENT_IP_TRANSPORT_SME')")
    display_name: str = Field(description="Human-readable title displayed in NOC consoles")
    domain: str = Field(description="DomainCode or domain string this agent specializes in")
    authority_level: AuthorityLevel = Field(
        default=AuthorityLevel.LEVEL_1_ANALYZE,
        description="Maximum permissible operational authority tier"
    )
    lifecycle_state: AgentLifecycleState = Field(
        default=AgentLifecycleState.ACTIVE,
        description="Current health and execution readiness state"
    )
    authorized_tools: list[str] = Field(
        default_factory=list,
        description="Allowed tool identifiers registered in the DomainToolRegistry"
    )
    managed_entities: list[str] = Field(
        default_factory=list,
        description="List of telecom element types or scopes this agent evaluates"
    )
    version: str = Field(default="1.0.0", description="Semantic version of the manifest specification")
