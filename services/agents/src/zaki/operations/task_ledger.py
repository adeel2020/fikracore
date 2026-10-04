"""Durable Task Ledger for Zaki v1."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional
from ..contracts.task import TaskContract
from ..enums import TaskPriority, TaskStatus, TaskType


class TaskLedger:
    """Manages the lifecycle and state transitions of operational tasks."""

    def __init__(self) -> None:
        self._tasks: Dict[str, TaskContract] = {}

    def create_task(
        self,
        incident_id: Optional[str] = None,
        intent_id: Optional[str] = None,
        task_type: TaskType = TaskType.INVESTIGATION,
        priority: TaskPriority = TaskPriority.HIGH,
        owner: str = "NOC_SHIFT_CURRENT",
        parent_task_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> TaskContract:
        task = TaskContract(
            incident_id=incident_id,
            intent_id=intent_id,
            task_type=task_type,
            status=TaskStatus.ACTIVE,
            priority=priority,
            owner=owner,
            parent_task_id=parent_task_id,
            metadata=metadata or {},
        )
        self._tasks[task.task_id] = task
        if parent_task_id and parent_task_id in self._tasks:
            parent = self._tasks[parent_task_id]
            parent.subtask_ids.append(task.task_id)
            parent.updated_at = datetime.now(timezone.utc)
        return task

    def get_task(self, task_id: str) -> Optional[TaskContract]:
        return self._tasks.get(task_id)

    def update_task_stage(self, task_id: str, stage: str, status: Optional[TaskStatus] = None) -> Optional[TaskContract]:
        task = self._tasks.get(task_id)
        if not task:
            return None
        task.current_stage = stage
        if status:
            task.status = status
        task.updated_at = datetime.now(timezone.utc)
        return task

    def update_status(self, task_id: str, status: TaskStatus) -> Optional[TaskContract]:
        task = self._tasks.get(task_id)
        if not task:
            return None
        task.status = status
        task.updated_at = datetime.now(timezone.utc)
        return task

    def list_tasks(
        self,
        incident_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
    ) -> List[TaskContract]:
        tasks = list(self._tasks.values())
        if incident_id:
            tasks = [t for t in tasks if t.incident_id == incident_id]
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks


default_task_ledger = TaskLedger()
