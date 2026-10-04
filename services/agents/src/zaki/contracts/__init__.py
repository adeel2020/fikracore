"""
Zaki Contracts Package
======================
This package encapsulates Zaki's operational orchestration contracts:
- task_episode.py: TaskEpisodeContract (Operational Spine), StageOutcome
- operational_context.py: OperationalContextContract (Section 22 Context Scaffolding Envelope)
- base.py: BaseContract
- incident.py: IncidentContextContract
- task.py: TaskContract
- intent.py: OperatorIntentContract, IntentSpec, FCAPSClassification
- story.py: IncidentStoryContract, StoryStatement
- agent.py: AgentManifestContract, AgentTaskContract, AgentResultContract
- tool.py: ToolContract, ToolMetadata, ToolSpec
- finding.py: CorrelationFindingContract, CorrelationFindingItem
- handover.py: HandoverRecordContract
- hypothesis.py: RankedHypothesisItem, HypothesisRankingContract
- action.py: ActionContract
- evidence.py: HarnessEvidenceContract
- resilience.py: NetworkResilienceDesignContract, RedundancyModel, SelfHealingMechanism
- service_impact.py: ServiceImpactContract, SliceImpactItem, SlaStatus
- remediation.py: RemediationStrategyContract, RemediationAction, RemediationClass, RemediationStrategyType
- blast_radius.py: BlastRadiusAssessmentContract, BlastRadiusTier
- root_cause.py: RootCauseAnalysisContract, RootCauseCandidate
- causal_propagation.py: CausalPropagationContract, CausalHop
- diagnostic_gap.py: DiagnosticGapContract, DiagnosticGapItem, DiagnosticGapType
- simulation.py: WhatIfSimulationContract, SimulationMode, BlastRadiusDelta
"""

from .base import BaseContract
from .task_episode import TaskEpisodeContract, StageOutcome
from .operational_context import OperationalContextContract
from .intent import OperatorIntentContract, IntentSpec, FCAPSClassification
from .task import TaskContract
from .incident import IncidentContextContract
from .evidence import HarnessEvidenceContract
from .hypothesis import RankedHypothesisItem, HypothesisRankingContract, HypothesisRankingMetadata, HypothesisRankingSpec
from .finding import CorrelationFindingItem, CorrelationFindingContract
from .action import ActionContract
from .handover import HandoverRecordContract
from .story import StoryStatement, IncidentStoryContract
from .agent import AgentManifestContract, AgentMetadata, AgentManifestSpec, AgentTaskContract, AgentResultContract
from .tool import ToolContract, ToolMetadata, ToolSpec

# Capability Contracts (Event & Incident Agnostic)
from .resilience import NetworkResilienceDesignContract, RedundancyModel, SelfHealingMechanism
from .service_impact import ServiceImpactContract, SliceImpactItem, SlaStatus
from .remediation import RemediationStrategyContract, RemediationAction, RemediationClass, RemediationStrategyType
from .blast_radius import BlastRadiusAssessmentContract, BlastRadiusTier
from .root_cause import RootCauseAnalysisContract, RootCauseCandidate
from .causal_propagation import CausalPropagationContract, CausalHop
from .diagnostic_gap import DiagnosticGapContract, DiagnosticGapItem, DiagnosticGapType
from .simulation import WhatIfSimulationContract, SimulationMode, BlastRadiusDelta
from .prosody import ProsodyContract
from .intent_dispatcher import dispatch_intent_contract, INTENT_CONTRACT_REGISTRY

try:
    from ..governance.validation import HumanValidationContract, ValidationMetadata, ValidationSpec
except ImportError:
    HumanValidationContract = None  # type: ignore
    ValidationMetadata = None  # type: ignore
    ValidationSpec = None  # type: ignore

__all__ = [
    "BaseContract",
    "ProsodyContract",
    "TaskEpisodeContract",
    "StageOutcome",
    "OperationalContextContract",
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
    "AgentManifestContract",
    "AgentMetadata",
    "AgentManifestSpec",
    "AgentTaskContract",
    "AgentResultContract",
    "ToolContract",
    "ToolMetadata",
    "ToolSpec",
    # Capability Contracts
    "NetworkResilienceDesignContract",
    "RedundancyModel",
    "SelfHealingMechanism",
    "ServiceImpactContract",
    "SliceImpactItem",
    "SlaStatus",
    "RemediationStrategyContract",
    "RemediationAction",
    "RemediationClass",
    "RemediationStrategyType",
    "BlastRadiusAssessmentContract",
    "BlastRadiusTier",
    "RootCauseAnalysisContract",
    "RootCauseCandidate",
    "CausalPropagationContract",
    "CausalHop",
    "DiagnosticGapContract",
    "DiagnosticGapItem",
    "DiagnosticGapType",
    "WhatIfSimulationContract",
    "SimulationMode",
    "BlastRadiusDelta",
    "dispatch_intent_contract",
    "INTENT_CONTRACT_REGISTRY",
]
