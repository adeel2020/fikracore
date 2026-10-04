"""
Governance Package for Zaki
===========================
This package encapsulates governance engines, policies, audit logging,
and Human-In-The-Loop validation contracts.
"""

from .policy_engine import PolicyEngine, PolicyDecision, default_policy_engine
from .hitl import HITLManager, default_hitl_manager
from .audit import AuditLogger, AuditRecord, default_audit_logger
from .behavior import BehaviorContract
from .validation import HumanValidationContract, ValidationMetadata, ValidationSpec

__all__ = [
    "BehaviorContract",
    "HumanValidationContract",
    "ValidationMetadata",
    "ValidationSpec",
    "PolicyEngine",
    "PolicyDecision",
    "default_policy_engine",
    "HITLManager",
    "default_hitl_manager",
    "AuditLogger",
    "AuditRecord",
    "default_audit_logger",
]
