"""Shift Handover Manager for Dark NOC 24x7 Operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from ..contracts.handover import HandoverRecordContract
from ..enums import AuthorityLevel


class HandoverManager:
    """Manages shift-to-shift handovers with explicit structured state transfer."""

    def __init__(self) -> None:
        self._handovers: Dict[str, HandoverRecordContract] = {}

    def create_handover(
        self,
        incident_id: str,
        from_operator: str,
        what: str,
        why: str,
        state: Dict[str, Any],
        task_id: Optional[str] = None,
        to_operator: Optional[str] = None,
        evidence: Optional[List[str]] = None,
        pending_actions: Optional[List[Dict[str, Any]]] = None,
        pending_validations: Optional[List[Dict[str, Any]]] = None,
        authority: AuthorityLevel = AuthorityLevel.LEVEL_1_ANALYZE,
        sla: Optional[Dict[str, Any]] = None,
    ) -> HandoverRecordContract:
        record = HandoverRecordContract(
            incident_id=incident_id,
            task_id=task_id,
            from_operator=from_operator,
            to_operator=to_operator,
            what=what,
            why=why,
            state=state,
            evidence=evidence or [],
            pending_actions=pending_actions or [],
            pending_validations=pending_validations or [],
            authority=authority,
            sla=sla or {"target_mttr_minutes": 60, "sla_breach_time": None},
        )
        self._handovers[record.handover_id] = record
        return record

    def accept_handover(
        self,
        handover_id: str,
        to_operator: str,
        notes: Optional[str] = None,
    ) -> Optional[HandoverRecordContract]:
        rec = self._handovers.get(handover_id)
        if not rec:
            return None
        rec.to_operator = to_operator
        rec.accepted = True
        rec.acceptance_notes = notes
        rec.accepted_at = datetime.now(timezone.utc)
        return rec

    def get_handover(self, handover_id: str) -> Optional[HandoverRecordContract]:
        return self._handovers.get(handover_id)

    def list_handovers(self, incident_id: Optional[str] = None) -> List[HandoverRecordContract]:
        recs = list(self._handovers.values())
        if incident_id:
            recs = [r for r in recs if r.incident_id == incident_id]
        return recs


default_handover_manager = HandoverManager()
