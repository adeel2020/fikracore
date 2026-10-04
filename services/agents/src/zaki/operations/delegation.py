"""Domain Agent Delegation Manager for Zaki v1."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from ..contracts.agent import AgentTaskContract
from ..enums import AuthorityLevel
from .task_ledger import default_task_ledger



class DelegationRequest(BaseModel):
    """Structured delegation request from Zaki NOC Lead to domain spoke agents."""

    delegation_id: str
    target_domain: str
    target_entity: str
    objective: str
    safety_ceiling: str = "PASSIVE_MONITORING"
    originating_task_id: str
    status: str = "PENDING"  # PENDING, ACTIVE, COMPLETED, FAILED
    result_summary: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DelegationManager:
    """Coordinates task delegation between Zaki NOC Lead and domain spoke agents."""

    def __init__(self) -> None:
        self._delegations: Dict[str, DelegationRequest] = {}

    def create_delegation_request(
        self,
        delegation_id: str,
        target_domain: str,
        target_entity: str,
        objective: str,
        originating_task_id: str,
        safety_ceiling: str = "PASSIVE_MONITORING",
    ) -> DelegationRequest:
        req = DelegationRequest(
            delegation_id=delegation_id,
            target_domain=target_domain,
            target_entity=target_entity,
            objective=objective,
            safety_ceiling=safety_ceiling,
            originating_task_id=originating_task_id,
            status="ACTIVE",
        )
        self._delegations[delegation_id] = req
        return req

    def register_delegation(self, request: DelegationRequest) -> DelegationRequest:
        self._delegations[request.delegation_id] = request
        return request

    def get_delegation(self, delegation_id: str) -> Optional[DelegationRequest]:
        return self._delegations.get(delegation_id)

    def list_delegations(self, originating_task_id: Optional[str] = None) -> List[DelegationRequest]:
        if originating_task_id:
            return [d for d in self._delegations.values() if d.originating_task_id == originating_task_id]
        return list(self._delegations.values())

    def complete_delegation(self, delegation_id: str, result_summary: str) -> Optional[DelegationRequest]:
        req = self._delegations.get(delegation_id)
        if req:
            req.status = "COMPLETED"
            req.result_summary = result_summary
        return req

    def create_delegation_task(
        self,
        parent_task_id: str,
        incident_id: str,
        domain: str,
        requested_capability: str,
        objective: str,
        context: Optional[Dict[str, Any]] = None,
        authority: AuthorityLevel = AuthorityLevel.LEVEL_1_ANALYZE,
    ) -> AgentTaskContract:
        # Create subtask in task ledger
        subtask = default_task_ledger.create_task(
            incident_id=incident_id,
            parent_task_id=parent_task_id,
            metadata={"domain": domain, "capability": requested_capability},
        )
        return AgentTaskContract(
            task_id=subtask.task_id,
            incident_id=incident_id,
            parent_task_id=parent_task_id,
            intent=f"Delegated domain analysis: {domain}",
            domain=domain,
            objective=objective,
            context=context or {},
            requested_capability=requested_capability,
            authority=authority,
        )


default_delegation_manager = DelegationManager()

