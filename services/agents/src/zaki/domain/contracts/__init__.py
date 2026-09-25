"""Domain Contracts Package for Zaki v1."""

from .base import BaseContract
from .intent import OperatorIntentContract, IntentSpec, FCAPSClassification
from .task import TaskContract
from .incident import IncidentContextContract
from .evidence import HarnessEvidenceContract
from .hypothesis import RankedHypothesisItem, HypothesisRankingContract, HypothesisRankingMetadata, HypothesisRankingSpec
from .finding import CorrelationFindingItem, CorrelationFindingContract
from .action import ActionContract
from .validation import HumanValidationContract, ValidationMetadata, ValidationSpec
from .handover import HandoverRecordContract
from .story import StoryStatement, IncidentStoryContract
from .task_episode import TaskEpisodeContract
from .agent import AgentManifestContract, AgentMetadata, AgentManifestSpec, AgentTaskContract, AgentResultContract
from .tool import ToolContract, ToolMetadata, ToolSpec

__all__ = [
    "BaseContract",
    "OperatorIntentContract",
    "IntentSpec",
    "FCAPSClassification",
    "TaskContract",
    "IncidentContextContract",
    "HarnessEvidenceContract",
    "RankedHypothesisItem",
    "HypothesisRankingContract",
    "HypothesisRankingMetadata",
    "HypothesisRankingSpec",
    "CorrelationFindingItem",
    "CorrelationFindingContract",
    "ActionContract",
    "HumanValidationContract",
    "ValidationMetadata",
    "ValidationSpec",
    "HandoverRecordContract",
    "StoryStatement",
    "IncidentStoryContract",
    "TaskEpisodeContract",
    "AgentManifestContract",
    "AgentMetadata",
    "AgentManifestSpec",
    "AgentTaskContract",
    "AgentResultContract",
    "ToolContract",
    "ToolMetadata",
    "ToolSpec",
]
