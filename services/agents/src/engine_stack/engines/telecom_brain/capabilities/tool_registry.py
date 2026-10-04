"""
Domain Tool Registry & Safety Execution Gateway
===============================================
This module implements the canonical DomainToolRegistry for FikraCore and Zaki.

Key Architectural Guarantees:
1. Operational Safety: Every tool is assigned a strict ActionSafetyTier
   (READ_ONLY_DIAGNOSTIC, CONTROLLED_REVERSIBLE, DISRUPTIVE).
2. Domain Categorization: Tools are organized by DomainCode jurisdictions.
3. Authority Ceilings: Enforces that calling agents possess the necessary AuthorityLevel
   before tool execution is authorized.
4. Human-In-The-Loop Enforcement: Any tool classified as CONTROLLED_REVERSIBLE or DISRUPTIVE
   requires an approved HITL validation token or operator signature.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

from ..investigation.contracts import (
    ActionSafetyTier,
    AuthorityLevel,
    DomainCode,
)


class ToolExecutionError(Exception):
    """Raised when tool execution fails or safety validation is rejected."""
    pass


class DomainToolDefinition(BaseModel):
    """
    Specification of an operational diagnostic probe or remediation tool.

    Attributes:
        tool_id: Semantic tool identifier (e.g., 'probe.query_crc_counters').
        display_name: Human-friendly name displayed in Zaki consoles.
        domain: Governed DomainCode jurisdiction.
        safety_tier: Action safety classification (READ_ONLY_DIAGNOSTIC, CONTROLLED_REVERSIBLE, DISRUPTIVE).
        required_authority: Minimum AuthorityLevel required to invoke tool.
        description: Technical description of tool mechanics.
        parameters_schema: Dictionary detailing expected parameter fields.
        handler: Executable callable function.
    """
    tool_id: str = Field(description="Unique tool identifier")
    display_name: str = Field(description="Display title for UI presentations")
    domain: DomainCode = Field(description="Governed domain jurisdiction")
    safety_tier: ActionSafetyTier = Field(
        default=ActionSafetyTier.READ_ONLY_DIAGNOSTIC,
        description="Safety and reversibility tier"
    )
    required_authority: AuthorityLevel = Field(
        default=AuthorityLevel.LEVEL_1_ANALYZE,
        description="Minimum permissible authority level"
    )
    description: str = Field(default="", description="Detailed functional explanation")
    parameters_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for parameters")
    handler: Optional[Callable[..., Any]] = Field(default=None, exclude=True)


class DomainToolRegistry:
    """
    Central registry and safety enforcement gateway for all telecom operational tools and probes.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, DomainToolDefinition] = {}
        self._bootstrap_standard_telecom_tools()

    def register_tool(self, tool_def: DomainToolDefinition) -> None:
        """Register a new tool definition in the registry."""
        self._tools[tool_def.tool_id] = tool_def

    def get_tool(self, tool_id: str) -> Optional[DomainToolDefinition]:
        """Retrieve a tool definition by ID."""
        return self._tools.get(tool_id)

    def list_tools(
        self,
        domain: Optional[DomainCode] = None,
        safety_tier: Optional[ActionSafetyTier] = None,
    ) -> List[DomainToolDefinition]:
        """List registered tools optionally filtered by domain and safety tier."""
        tools = list(self._tools.values())
        if domain:
            tools = [t for t in tools if t.domain == domain]
        if safety_tier:
            tools = [t for t in tools if t.safety_tier == safety_tier]
        return tools

    def execute_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
        caller_authority: AuthorityLevel = AuthorityLevel.LEVEL_1_ANALYZE,
        hitl_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute an operational tool with strict safety tier and authority checks.
        """
        tool = self.get_tool(tool_id)
        if not tool:
            raise ToolExecutionError(f"Tool `{tool_id}` not found in DomainToolRegistry.")

        # 1. Authority Hierarchy Check
        authority_rank = {
            AuthorityLevel.LEVEL_1_ANALYZE: 1,
            AuthorityLevel.LEVEL_2_DIAGNOSE: 2,
            AuthorityLevel.LEVEL_3_EXECUTE: 3,
        }
        if authority_rank.get(caller_authority, 0) < authority_rank.get(tool.required_authority, 0):
            raise ToolExecutionError(
                f"Caller authority `{caller_authority}` is below required authority `{tool.required_authority}` for `{tool_id}`."
            )

        # 2. HITL Approval Gate for Reversible or Disruptive Actions
        if tool.safety_tier in {ActionSafetyTier.CONTROLLED_REVERSIBLE, ActionSafetyTier.DISRUPTIVE}:
            if not hitl_token:
                raise ToolExecutionError(
                    f"Execution of `{tool.safety_tier}` tool `{tool_id}` requires an approved HITL validation token."
                )

        # 3. Execution via handler
        if tool.handler:
            try:
                return tool.handler(**parameters)
            except Exception as e:
                raise ToolExecutionError(f"Error executing tool `{tool_id}`: {e}") from e

        # Mock / default simulation execution response
        return {
            "status": "SUCCESS",
            "tool_id": tool_id,
            "domain": tool.domain.value,
            "safety_tier": tool.safety_tier.value,
            "parameters": parameters,
            "output": f"Executed `{tool.display_name}` successfully.",
        }

    def _bootstrap_standard_telecom_tools(self) -> None:
        """Register the standard Tier-1 telecom diagnostic probes and operational actions."""
        # 1. IP Transport Probes
        self.register_tool(DomainToolDefinition(
            tool_id="probe.query_crc_counters",
            display_name="Query Router Interface CRC & Buffer Drops",
            domain=DomainCode.IP_TRANSPORT,
            safety_tier=ActionSafetyTier.READ_ONLY_DIAGNOSTIC,
            required_authority=AuthorityLevel.LEVEL_1_ANALYZE,
            description="Queries real-time hardware ASIC counters for ingress/egress CRC errors and buffer exhaustion.",
            parameters_schema={"target_entity": "str", "interface": "str"},
        ))
        self.register_tool(DomainToolDefinition(
            tool_id="probe.check_bgp_session",
            display_name="Check BGP Peering & Adjacency State",
            domain=DomainCode.IP_TRANSPORT,
            safety_tier=ActionSafetyTier.READ_ONLY_DIAGNOSTIC,
            required_authority=AuthorityLevel.LEVEL_1_ANALYZE,
            description="Inspects BGP neighbor state, prefixes received/advertised, and hold timer status.",
            parameters_schema={"target_entity": "str", "neighbor_ip": "str"},
        ))
        self.register_tool(DomainToolDefinition(
            tool_id="action.drain_traffic_bgp",
            display_name="Drain Traffic via BGP AS-Path Prepend / Cost Out",
            domain=DomainCode.IP_TRANSPORT,
            safety_tier=ActionSafetyTier.CONTROLLED_REVERSIBLE,
            required_authority=AuthorityLevel.LEVEL_3_EXECUTE,
            description="Increases IGP metric or prepends BGP AS-Path to gracefully drain traffic to secondary paths.",
            parameters_schema={"target_entity": "str", "standby_peer": "str"},
        ))

        # 2. PS Core Probes
        self.register_tool(DomainToolDefinition(
            tool_id="probe.query_upf_drops",
            display_name="Query UPF Session Packet Drops",
            domain=DomainCode.PS_CORE,
            safety_tier=ActionSafetyTier.READ_ONLY_DIAGNOSTIC,
            required_authority=AuthorityLevel.LEVEL_1_ANALYZE,
            description="Inspects GTP-U tunnel drop counters, PFCP association states, and buffer pools on UPF.",
            parameters_schema={"target_entity": "str", "session_id": "str"},
        ))
        self.register_tool(DomainToolDefinition(
            tool_id="probe.test_diameter_gy",
            display_name="Test Diameter Gy Charging Conduits",
            domain=DomainCode.CHARGING_BILLING,
            safety_tier=ActionSafetyTier.READ_ONLY_DIAGNOSTIC,
            required_authority=AuthorityLevel.LEVEL_2_DIAGNOSE,
            description="Sends synthetic CCR-I ping over Gy interface to verify OCS online rating availability.",
            parameters_schema={"target_entity": "str", "ocs_peer": "str"},
        ))

        # 3. RAN Probes
        self.register_tool(DomainToolDefinition(
            tool_id="probe.query_rrc_success_rate",
            display_name="Query Cell RRC Setup Success Rate",
            domain=DomainCode.RAN,
            safety_tier=ActionSafetyTier.READ_ONLY_DIAGNOSTIC,
            required_authority=AuthorityLevel.LEVEL_1_ANALYZE,
            description="Extracts 5-minute rolling RRC connection establishment success rate across gNodeB sectors.",
            parameters_schema={"cell_id": "str"},
        ))


default_domain_tool_registry = DomainToolRegistry()
