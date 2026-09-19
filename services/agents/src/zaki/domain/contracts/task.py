"""Task Contract for Zaki v1."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract
from ..enums import TaskPriority, TaskStatus, TaskType


class TaskContract(BaseContract):
    api_version: str = "zaki.ai/v1"
    kind: str = "Task"
    task_id: str = Field(default_factory=lambda: f"TASK-{int(datetime.now(timezone.utc).timestamp())}")
    incident_id: Optional[str] = None
    intent_id: Optional[str] = None
    task_type: TaskType = TaskType.INVESTIGATION
    status: TaskStatus = TaskStatus.CREATED
    priority: TaskPriority = TaskPriority.HIGH
    owner: str = "NOC_SHIFT_CURRENT"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_stage: str = "INGESTION"
    delegated_agent_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    subtask_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
