"""Standard Enums for Zaki v1 Agent Harness."""

from enum import Enum, IntEnum


class TaskType(str, Enum):
    INVESTIGATION = "INVESTIGATION"
    DISCOVERY = "DISCOVERY"
    REMEDIATION = "REMEDIATION"
    VALIDATION = "VALIDATION"
    HANDOVER = "HANDOVER"


class TaskStatus(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    WAITING_EVIDENCE = "WAITING_EVIDENCE"
    WAITING_HITL = "WAITING_HITL"
    DELEGATED = "DELEGATED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskMode(str, Enum):
    ANALYZE_ONLY = "ANALYZE_ONLY"
    RECOMMEND = "RECOMMEND"
    HITL_EXECUTE = "HITL_EXECUTE"
    AUTO_EXECUTE = "AUTO_EXECUTE"


class AuthorityLevel(IntEnum):
    LEVEL_0_OBSERVE = 0
    LEVEL_1_ANALYZE = 1
    LEVEL_2_RECOMMEND = 2
    LEVEL_3_PLAN = 3
    LEVEL_4_HITL_EXECUTE = 4
    LEVEL_5_AUTO_EXECUTE = 5


class PolicyDecisionType(str, Enum):
    ALLOW = "ALLOW"
    ALLOW_WITH_HITL = "ALLOW_WITH_HITL"
    DENY = "DENY"
    ESCALATE = "ESCALATE"


class ValidationDecisionType(str, Enum):
    CONFIRM = "CONFIRM"
    REJECT = "REJECT"
    MODIFY = "MODIFY"
    REQUEST_EVIDENCE = "REQUEST_EVIDENCE"
    APPROVE_LEARNING = "APPROVE_LEARNING"


class EvidenceStatus(str, Enum):
    SUPPORTING = "SUPPORTING"
    CONTRADICTING = "CONTRADICTING"
    NEUTRAL = "NEUTRAL"
    MISSING = "MISSING"
    UNTRUSTED = "UNTRUSTED"


class StatementProvenance(str, Enum):
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class PresentationDepth(str, Enum):
    EXECUTIVE = "EXECUTIVE"
    OPERATOR = "OPERATOR"
    DEEP_TECHNICAL = "DEEP_TECHNICAL"


class AgentLifecycleState(str, Enum):
    REGISTERED = "REGISTERED"
    VALIDATED = "VALIDATED"
    CERTIFIED = "CERTIFIED"
    DEPLOYED = "DEPLOYED"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class ToolType(str, Enum):
    READ = "READ"
    ANALYZE = "ANALYZE"
    FIKRACORE = "FIKRACORE"
    ACTION = "ACTION"


class ToolInterface(str, Enum):
    TMF_API = "TMF_API"
    MCP = "MCP"
    EVENT = "EVENT"
    INTERNAL = "INTERNAL"


class FCAPSCategory(str, Enum):
    FAULT = "Fault"
    CHANGE = "Change"
    ACCEPTANCE = "Acceptance"
    PERFORMANCE = "Performance"
    SECURITY = "Security"
