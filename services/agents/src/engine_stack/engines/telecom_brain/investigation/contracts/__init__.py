"""
Telecom Brain Investigation Contracts Package
=============================================
This package provides the canonical data contracts, epistemic models, and
structural schemas governing FikraCore and Zaki's 4-Plane Knowledge Graph.

Planes & Modular Structure:
- base.py: Foundation Contract base class, Pydantic v1/v2 compatibility shim,
  and primitive enums (Terminal, KnowledgeState, CausalRole, ActionSafetyTier).
- domain.py: DomainCode enum and DomainContract governing operational jurisdictions.
- agent.py: AgentManifestContract, AuthorityLevel, and AgentLifecycleState.
- evidence.py: 3-Tier evidence lifecycle (RawEvidenceContract, EmergingEvidenceContract,
  Evidence, ValidatedEvidenceContract, GeneratedRunInput).
- topology.py: Plane 1 Topology contracts, TypedEdgeType (including HA redundancy edges),
  Relationship, RelationshipContract, CandidateRelationship, BlastRadiusAssessment.
- hypothesis.py: Plane 3 Reasoning spine (Hypothesis, Assumption, EvidenceRequest,
  DiscriminationProbeContract, InvestigationResult, ValidationDecision).
- pattern.py: Plane 4 Enterprise Intelligence (PatternContract, PatternRecognitionContract).
- remediation.py: Plane 4 MOPs (RemediationPlaybookContract, PlaybookPrecondition, RollbackStep).
- promotion.py: Continuous learning ledger, ValidationRecord, PromotionRecord,
  LearningUnit, LearningLedgerEntry, LearningPerformanceDelta.
- simulation.py: KnowledgeGap, SharedStructuredState, StandardPresentationModel,
  ZakiContextContract, and Step 4.4 / H4 What-If Resilience contracts.

100% Backward Compatibility:
All symbols formerly exported from monolithic `contracts.py` are re-exported here.
"""

import pydantic
from datetime import datetime
from enum import Enum
from typing import Any, Literal, Union
from pydantic import BaseModel, Field

from .base import (
    IS_PYDANTIC_V2,
    Contract,
    Terminal,
    KnowledgeState,
    CausalRole,
    ActionSafetyTier,
)
from .domain import (
    DomainCode,
    DomainContract,
)
from .agent import (
    AuthorityLevel,
    AgentLifecycleState,
    AgentManifestContract,
)
from .evidence import (
    EvidenceTier,
    GeneratedRunInput,
    RawEvidenceContract,
    EmergingEvidenceContract,
    Evidence,
    ValidatedEvidenceContract,
)
from .topology import (
    TypedEdgeType,
    Relationship,
    RelationshipContract,
    CandidateRelationship,
    BlastRadiusLevel,
    BlastRadiusAssessment,
)
from .hypothesis import (
    Assumption,
    Hypothesis,
    InvestigationHypothesis,
    EvidenceRequest,
    DiscriminationProbeContract,
    InvestigationResult,
    ValidationDecision,
)
from .pattern import (
    PatternContract,
    PatternRecognitionContract,
)
from .remediation import (
    PlaybookPrecondition,
    RollbackStep,
    RemediationPlaybookContract,
)
from .promotion import (
    ValidationDecisionType,
    KnowledgePromotionState,
    ValidationRecord,
    PromotionRecord,
    LearningLedgerEntry,
    LearningUnit,
    LearningPerformanceDelta,
)
from .simulation import (
    KnowledgeGapType,
    SuspectedMissingRelation,
    KnowledgeGap,
    UnexplainedResidual,
    ModelContradiction,
    NextBestEvidenceRequest,
    CuratedDemoMetadata,
    StandardPresentationModel,
    SharedStructuredState,
    ZakiContextContract,
    PropagationSemantics,
    ResilienceActionCategory,
    WhatIfTrigger,
    WhatIfAssumptions,
    WhatIfScenario,
    PropagationPathStep,
    CriticalFailureSurface,
    ResilienceGap,
    MitigationOption,
    ResilienceRecommendation,
    WhatIfSimulationResult,
)

__all__ = [
    # Base Primitives
    "IS_PYDANTIC_V2",
    "Contract",
    "Terminal",
    "KnowledgeState",
    "CausalRole",
    "ActionSafetyTier",
    # Domain Jurisdictions
    "DomainCode",
    "DomainContract",
    # Agent Capabilities
    "AuthorityLevel",
    "AgentLifecycleState",
    "AgentManifestContract",
    # Evidence Lifecycle
    "EvidenceTier",
    "GeneratedRunInput",
    "RawEvidenceContract",
    "EmergingEvidenceContract",
    "Evidence",
    "ValidatedEvidenceContract",
    # Topology & Redundancy
    "TypedEdgeType",
    "Relationship",
    "RelationshipContract",
    "CandidateRelationship",
    "BlastRadiusLevel",
    "BlastRadiusAssessment",
    # Hypothesis & Reasoning
    "Assumption",
    "Hypothesis",
    "EvidenceRequest",
    "DiscriminationProbeContract",
    "InvestigationResult",
    "ValidationDecision",
    # Patterns & Signatures
    "PatternContract",
    "PatternRecognitionContract",
    # Remediation & Procedures
    "PlaybookPrecondition",
    "RollbackStep",
    "RemediationPlaybookContract",
    # Learning & Promotion
    "ValidationDecisionType",
    "KnowledgePromotionState",
    "ValidationRecord",
    "PromotionRecord",
    "LearningLedgerEntry",
    "LearningUnit",
    "LearningPerformanceDelta",
    # Simulation, State & Resilience
    "KnowledgeGapType",
    "SuspectedMissingRelation",
    "KnowledgeGap",
    "UnexplainedResidual",
    "ModelContradiction",
    "NextBestEvidenceRequest",
    "CuratedDemoMetadata",
    "StandardPresentationModel",
    "SharedStructuredState",
    "ZakiContextContract",
    "PropagationSemantics",
    "ResilienceActionCategory",
    "WhatIfTrigger",
    "WhatIfAssumptions",
    "WhatIfScenario",
    "PropagationPathStep",
    "CriticalFailureSurface",
    "ResilienceGap",
    "MitigationOption",
    "ResilienceRecommendation",
    "WhatIfSimulationResult",
]
