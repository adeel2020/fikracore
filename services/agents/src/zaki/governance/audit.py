"""Audit Logger and Event Journal for Zaki v1."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from ..contracts.base import BaseContract


class AuditRecord(BaseContract):
    event_id: str
    event_type: str
    sequence: int
    timestamp: datetime
    run_id: Optional[str] = None
    task_id: Optional[str] = None
    incident_id: Optional[str] = None
    actor: str = "zaki_orchestrator"
    payload: Dict[str, Any]
    provenance: str = "audit_engine"


class AuditLogger:
    """Maintains an append-only verifiable audit trail of harness execution."""

    def __init__(self) -> None:
        self._records: List[AuditRecord] = []
        self._sequence: int = 0

    def log_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        task_id: Optional[str] = None,
        incident_id: Optional[str] = None,
        run_id: Optional[str] = None,
        actor: str = "zaki_orchestrator",
        provenance: str = "audit_engine",
    ) -> AuditRecord:
        self._sequence += 1
        now = datetime.now(timezone.utc)
        record = AuditRecord(
            event_id=f"EVT-{self._sequence:06d}",
            event_type=event_type,
            sequence=self._sequence,
            timestamp=now,
            run_id=run_id,
            task_id=task_id,
            incident_id=incident_id,
            actor=actor,
            payload=payload,
            provenance=provenance,
        )
        self._records.append(record)
        return record

    def get_events(
        self,
        task_id: Optional[str] = None,
        incident_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> List[AuditRecord]:
        records = list(self._records)
        if task_id:
            records = [r for r in records if r.task_id == task_id]
        if incident_id:
            records = [r for r in records if r.incident_id == incident_id]
        if run_id:
            records = [r for r in records if r.run_id == run_id]
        return records


default_audit_logger = AuditLogger()
