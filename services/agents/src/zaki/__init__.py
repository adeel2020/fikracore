"""Zaki v1 Agent Harness Package.

Telecom operator Dark NOC Agent Harness built around the FikraCore execution flow.
FikraCore reasons. Domain Agents operate. Zaki orchestrates, governs and explains.
"""

from .runtime.orchestrator import ZakiOrchestrator
from .fikracore.adapter import FikraCoreAdapter
from .intent.manager import IntentManager
from .agents.registry import default_agent_registry
from .operations.incident_ledger import default_incident_ledger
from .operations.task_ledger import default_task_ledger
from .governance.policy_engine import default_policy_engine
from .governance.hitl import default_hitl_manager
from .governance.audit import default_audit_logger

__version__ = "1.0.0"

__all__ = [
    "ZakiOrchestrator",
    "FikraCoreAdapter",
    "IntentManager",
    "default_agent_registry",
    "default_incident_ledger",
    "default_task_ledger",
    "default_policy_engine",
    "default_hitl_manager",
    "default_audit_logger",
]
