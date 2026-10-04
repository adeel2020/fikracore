"""Agent Manifest & Invocation Contracts for Zaki v1."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract
from ..enums import AgentLifecycleState, AuthorityLevel


class AgentMetadata(BaseContract):
    id: str
    name: str
    version: str = "1.0.0"
    domain: str  # PS, CS, RAN, IP_TRANSPORT, IN_OCS, VAS, IGW, INFRA, IT
    owner: str = "NOC_ENGINEERING"


class AgentPolicyProfile(BaseContract):
    risk_level: str = "MEDIUM"
    authority_level: AuthorityLevel = AuthorityLevel.LEVEL_1_ANALYZE
    max_concurrent_sessions: int = 10
    allowed_tools: List[str] = Field(default_factory=list)


class AgentLifecycle(BaseContract):
    state: AgentLifecycleState = AgentLifecycleState.ACTIVE
    certification: str = "CERTIFIED"
    last_evaluated: Optional[datetime] = None


class AgentManifestSpec(BaseContract):
    capabilities: List[str] = Field(default_factory=list)
    accepted_intents: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    policies: AgentPolicyProfile = Field(default_factory=AgentPolicyProfile)
    knowledge_version: str = "1.0.0"
    skill_versions: List[str] = Field(default_factory=list)
    lifecycle: AgentLifecycle = Field(default_factory=AgentLifecycle)
    trace_enabled: bool = True


class AgentManifestContract(BaseContract):
    api_version: str = "zaki.ai/v1"
    kind: str = "Agent"
    metadata: AgentMetadata
    spec: AgentManifestSpec


class AgentTaskContract(BaseContract):
    task_id: str
    incident_id: str
    parent_task_id: Optional[str] = None
    intent: str
    domain: str
    objective: str
    context: Dict[str, Any] = Field(default_factory=dict)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    requested_capability: str
    authority: AuthorityLevel = AuthorityLevel.LEVEL_1_ANALYZE
    deadline: Optional[datetime] = None


class AgentResultContract(BaseContract):
    task_id: str
    agent_id: str
    status: str = "SUCCESS"  # SUCCESS, FAILURE, PARTIAL
    observations: List[Dict[str, Any]] = Field(default_factory=list)
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_requests: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    delegation_requests: List[Dict[str, Any]] = Field(default_factory=list)
    human_validation_required: bool = False
    confidence: float = 1.0
    provenance: str = "domain_agent"
    next_step: Optional[str] = None
