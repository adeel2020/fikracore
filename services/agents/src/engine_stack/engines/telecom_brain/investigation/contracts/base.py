"""
Base Contract Architecture & Canonical Primitive Types
======================================================
This module establishes the foundational base class and core enumerations
for all FikraCore and Zaki operational contracts.

Design Principles:
1. Immutability: All contracts are frozen (`frozen=True`, `extra="forbid"`) to prevent
   in-flight state corruption across distributed agent invocations.
2. Dual-Version Compatibility: Seamless execution on both Pydantic v1 and v2 environments
   using transparent runtime feature shims (`model_validate`, `model_dump`).
3. Telecom Rigor: Strictly typed terminal states, causal roles, and action safety tiers
   modeled after Tier-1 Telco NOC SME diagnostic workflows.
"""

import pydantic
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

IS_PYDANTIC_V2 = getattr(pydantic, "__version__", "1.").startswith("2")

if IS_PYDANTIC_V2:
    from pydantic import ConfigDict

    class Contract(BaseModel):
        """
        Abstract base class for all FikraCore and Zaki contracts (Pydantic v2).
        Enforces strict immutability, prohibiting arbitrary extra fields.
        """
        model_config = ConfigDict(extra="forbid", frozen=True)
else:
    class Contract(BaseModel):
        """
        Abstract base class for all FikraCore and Zaki contracts (Pydantic v1 shim).
        Enforces strict immutability, prohibiting arbitrary extra fields, with
        forward-compatible Pydantic v2 method aliases.
        """
        class Config:
            extra = "forbid"
            allow_mutation = False
            frozen = True

        @classmethod
        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)
            if not hasattr(cls, "model_fields"):
                cls.model_fields = getattr(cls, "__fields__", {})

        @classmethod
        def model_validate(cls, obj: Any):
            """Validate an object against the contract schema."""
            if isinstance(obj, cls):
                return obj
            return cls.parse_obj(obj)

        @classmethod
        def model_validate_json(cls, json_data: str | bytes, **kwargs):
            """Parse and validate raw JSON against the contract schema."""
            return cls.parse_raw(json_data, **kwargs)

        def model_dump(self, mode: str = "python", **kwargs) -> dict:
            """Serialize the contract instance to a Python dictionary."""
            import json
            if mode == "json":
                return json.loads(self.json(**kwargs))
            return self.dict(**kwargs)

        def model_dump_json(self, **kwargs) -> str:
            """Serialize the contract instance to a JSON string."""
            return self.json(**kwargs)

        def model_copy(self, update: dict = None, deep: bool = False):
            """Create a shallow or deep copy of the contract with optional field overrides."""
            return self.copy(update=update, deep=deep)


class Terminal(str, Enum):
    """
    Diagnostic termination state representing the definitive resolution
    status of an operational investigation or what-if resilience evaluation.
    """
    EXPLAINED = "EXPLAINED"                      # Incident cause fully explained by evidence and topology
    PARTIALLY_EXPLAINED = "PARTIALLY_EXPLAINED"  # Plausible cause identified but secondary factors unresolved
    UNRESOLVED = "UNRESOLVED"                    # Hypotheses evaluated but no root cause confirmed
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE" # Required discrimination evidence unavailable in time window
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"   # Telemetry contradicts established topology/protocol models
    MODEL_INSUFFICIENT = "MODEL_INSUFFICIENT"       # Topology/causal model lacks necessary relationships to explain anomaly


class KnowledgeState(str, Enum):
    """
    Epistemic confidence tier for entities, relationships, and causal edges in the gbrain.
    """
    CONFIRMED = "CONFIRMED"   # Verified by authoritative configuration or telemetry validation
    SUPPORTED = "SUPPORTED"   # Strongly aligned with observed symptoms and historical patterns
    INFERRED = "INFERRED"     # Synthesized via multi-hop causal graph traversal
    CANDIDATE = "CANDIDATE"   # Proposed by an agent or hypothesis engine, awaiting human/SME validation
    REJECTED = "REJECTED"     # Explicitly refuted by discrimination probes or SME review
    STALE = "STALE"           # Outdated due to topology changes, reconfigurations, or software updates
    UNKNOWN = "UNKNOWN"       # Unmeasured or unseen state


class CausalRole(str, Enum):
    """
    Formal categorization of an entity or event's role in an incident propagation sequence.
    Enforces strict causal discrimination across NOC SME reasoning stages.
    """
    ROOT = "ROOT"                                   # Primary initial defect or failure trigger
    TRIGGER = "TRIGGER"                             # Immediate external or scheduled event that initiated degradation
    CONTRIBUTING_CONDITION = "CONTRIBUTING_CONDITION" # Latent defect or pre-existing state enabling failure
    PROPAGATION_MECHANISM = "PROPAGATION_MECHANISM"   # Path or protocol through which degradation spread
    AMPLIFIER = "AMPLIFIER"                         # Mechanism exacerbating degradation (e.g., retry storm)
    SYMPTOM = "SYMPTOM"                             # Observable downstream operational manifestation
    COINCIDENTAL = "COINCIDENTAL"                   # Event occurring in same window with no causal linkage
    UNKNOWN = "UNKNOWN"                             # Relationship not yet characterized


class ActionSafetyTier(str, Enum):
    """
    Safety classification determining authorization gates and Human-In-The-Loop (HITL)
    requirements prior to executing remediation or diagnostic probes on live telecom infrastructure.
    """
    READ_ONLY_DIAGNOSTIC = "READ_ONLY_DIAGNOSTIC"   # Safe telemetry queries, passive counters, config reads
    CONTROLLED_REVERSIBLE = "CONTROLLED_REVERSIBLE" # BGP metric shifts, traffic drains with active rollbacks
    DISRUPTIVE = "DISRUPTIVE"                       # Element restarts, route withdrawal, interface shut (Mandatory SME Approval)
