"""Domain Agent Delegation Manager for Zaki v1."""

from __future__ import annotations

from typing import Any, Dict, Optional
from ..domain.contracts.agent import AgentTaskContract
from ..domain.enums import AuthorityLevel
from .task_ledger import default_task_ledger


class DelegationManager:
    """Coordinates task delegation to domain agents."""

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
