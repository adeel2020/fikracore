"""Human-in-the-Loop (HITL) Governance Manager for Zaki v1."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional
from ..domain.contracts.validation import HumanValidationContract, ValidationMetadata, ValidationSpec
from ..domain.enums import AuthorityLevel, ValidationDecisionType
from .audit import default_audit_logger


class HITLManager:
    """Manages the validation inbox, pending approvals, and operator confirmations."""

    def __init__(self) -> None:
        self._pending: Dict[str, Dict] = {}
        self._history: Dict[str, HumanValidationContract] = {}

    def request_validation(
        self,
        task_id: str,
        incident_id: str,
        target_type: str,
        target_id: str,
        reason: str,
        authority: AuthorityLevel = AuthorityLevel.LEVEL_4_HITL_EXECUTE,
    ) -> str:
        val_id = f"VAL-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        req = {
            "validation_id": val_id,
            "task_id": task_id,
            "incident_id": incident_id,
            "target_type": target_type,
            "target_id": target_id,
            "reason": reason,
            "authority": authority,
            "status": "PENDING",
            "requested_at": datetime.now(timezone.utc).isoformat(),
        }
        self._pending[val_id] = req
        default_audit_logger.log_event(
            event_type="HUMAN_VALIDATION_REQUESTED",
            task_id=task_id,
            incident_id=incident_id,
            payload=req,
        )
        return val_id

    def submit_decision(
        self,
        validation_id: str,
        decision: ValidationDecisionType,
        validator_id: str = "operator-01",
        validator_role: str = "operator",
        reason: str = "Validated by operator",
        authority: AuthorityLevel = AuthorityLevel.LEVEL_4_HITL_EXECUTE,
    ) -> Optional[HumanValidationContract]:
        req = self._pending.pop(validation_id, None)
        if not req:
            return None

        contract = HumanValidationContract(
            metadata=ValidationMetadata(
                id=validation_id,
                task_id=req["task_id"],
                incident_id=req["incident_id"],
            ),
            spec=ValidationSpec(
                decision=decision,
                target_type=req["target_type"],
                target_id=req["target_id"],
                reason=reason,
                validator_role=validator_role,
                validator_id=validator_id,
                authority=authority,
            ),
        )
        self._history[validation_id] = contract
        default_audit_logger.log_event(
            event_type="HUMAN_VALIDATION_RECEIVED",
            task_id=req["task_id"],
            incident_id=req["incident_id"],
            payload={
                "validation_id": validation_id,
                "decision": decision.value,
                "validator_id": validator_id,
                "reason": reason,
            },
        )
        return contract

    def get_pending(self, task_id: Optional[str] = None) -> List[Dict]:
        items = list(self._pending.values())
        if task_id:
            items = [i for i in items if i["task_id"] == task_id]
        return items

    def get_history(self, task_id: Optional[str] = None) -> List[HumanValidationContract]:
        items = list(self._history.values())
        if task_id:
            items = [i for i in items if i.metadata.task_id == task_id]
        return items


default_hitl_manager = HITLManager()
