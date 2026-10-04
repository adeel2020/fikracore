"""
Hypothesis & Discrimination Probe Contracts (Plane 3 - Reasoning Spine)
======================================================================
This module defines the cognitive reasoning artifacts used by Zaki and FikraCore
during root-cause isolation and diagnostic discrimination.

Core Capabilities:
1. Hypothesis Tracking: Competing explanations with confidence metrics, explanation coverage,
   supporting/contradicting evidence lists, and assumption checks.
2. Evidence Requests: Information-theoretic scoring of telemetry queries (information gain vs cost/risk).
3. Discrimination Probes: Active targeted diagnostics executed to decisively validate or rule out
   competing hypotheses in Step 3 of investigation.
4. Investigation Result: The authoritative aggregated output of a diagnostic run.
"""

from datetime import datetime
from typing import Any, Literal
from pydantic import Field
from .base import Contract, KnowledgeState, CausalRole, Terminal
from .topology import CandidateRelationship


class Assumption(Contract):
    """
    An underlying factual or structural premise required for a hypothesis to remain viable.

    Attributes:
        statement: Textual statement of premise (e.g. 'BGP session between PE1 and PE2 is UP').
        state: Current evaluation status (CONFIRMED, SUPPORTED, UNCERTAIN, UNTESTED, CONTRADICTED, REJECTED).
        evidence_ids: List of evidence records validating or refuting this assumption.
    """
    statement: str = Field(description="Underlying operational or topological assumption")
    state: Literal["CONFIRMED", "SUPPORTED", "UNCERTAIN", "UNTESTED", "CONTRADICTED", "REJECTED"] = Field(
        description="Epistemic validation status of this assumption"
    )
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="References to telemetry records testing this assumption"
    )


class Hypothesis(Contract):
    """
    A competing explanation of an observed network anomaly or service degradation.

    Attributes:
        hypothesis_id: Unique semantic hypothesis identifier (e.g. 'HYP_BGP_FLAP_AGG01').
        statement: Clear technical assertion describing root cause and propagation.
        candidate_root_domain: Primary technical domain suspected (e.g. 'IP_TRANSPORT').
        candidate_root_entity: Suspected culprit element display name.
        canonical_root_entity: Suspected culprit element gbrain canonical slug.
        root_entities: All network elements directly involved in root cause trigger.
        causal_role: Role assigned to candidate root entity (ROOT, TRIGGER, AMPLIFIER).
        assumptions: List of constituent assumptions that must hold.
        expected_observations: Symptoms expected if this hypothesis is ground truth.
        supporting_evidence: Evidence IDs corroborating this hypothesis.
        contradicting_evidence: Evidence IDs refuting this hypothesis.
        missing_evidence: Telemetry observations needed to confirm or rule out.
        knowledge_relationships_used: gbrain edge relationships traversed.
        status: KnowledgeState (CANDIDATE, SUPPORTED, CONFIRMED, REJECTED).
        hypothesis_confidence: Composite confidence score (0.0 to 1.0).
        causal_confidence: Specific confidence in the causal chain mechanism.
        explanation_coverage: Ratio of observed symptoms explained by this hypothesis (0.0 to 1.0).
        score_dimensions: Detailed dimensional scores (e.g. topology_fit, temporal_alignment).
        failed_assumptions: Statements of assumptions refuted by evidence.
    """
    hypothesis_id: str = Field(description="Unique semantic hypothesis identifier")
    statement: str = Field(description="Technical summary of the proposed causal explanation")
    candidate_root_domain: str = Field(description="Suspected operational domain where defect originated")
    candidate_root_entity: str = Field(description="Display name of suspect culprit network entity")
    canonical_root_entity: str = Field(description="Canonical gbrain slug of suspect network entity")
    root_entities: list[str] = Field(description="All entities constituting root cause trigger")
    causal_role: CausalRole = Field(description="Causal role attributed to the candidate entity")
    assumptions: list[Assumption] = Field(description="Constituent operational assumptions required for hypothesis validity")
    expected_observations: list[str] = Field(description="Observations expected if this hypothesis is correct")
    supporting_evidence: list[str] = Field(description="Evidence IDs confirming or supporting hypothesis")
    contradicting_evidence: list[str] = Field(description="Evidence IDs conflicting with or refuting hypothesis")
    missing_evidence: list[str] = Field(description="Unobserved telemetry needed to resolve hypothesis uncertainty")
    knowledge_relationships_used: list[str] = Field(description="gbrain edge IDs leveraged in causal reasoning")
    status: KnowledgeState = Field(description="Current validation state of hypothesis")
    hypothesis_confidence: float = Field(description="Overall probability score assigned to hypothesis")
    causal_confidence: float = Field(description="Confidence that the causal mechanism is sound")
    explanation_coverage: float = Field(description="Fraction of total incident symptoms accounted for")
    score_dimensions: dict[str, float] = Field(description="Breakdown of multi-criteria heuristic scores")
    failed_assumptions: list[str] = Field(
        default_factory=list,
        description="Assumptions that have been proven false by evidence"
    )


# Backward compatibility and alternative naming alias
InvestigationHypothesis = Hypothesis


class EvidenceRequest(Contract):
    """
    Prioritized request for diagnostic telemetry, evaluated on information gain and operational risk.

    Attributes:
        request_id: Semantic request ID.
        question: Diagnostic question to be answered by the query.
        target_entities: Network entities to query.
        discriminates: Hypothesis IDs that this query will differentiate between.
        information_gain: Expected entropy reduction / diagnostic clarity gain.
        cost: Resource or computational cost of query (default 1.0).
        latency: Expected response latency weight (default 1.0).
        risk: Safety risk to live network stability (0.0 safe to 1.0 disruptive).
        reliability: Sensor or tool reliability coefficient.
        availability: Telemetry data source availability score.
        priority: Computed scheduling priority score.
    """
    request_id: str = Field(description="Unique telemetry request identifier")
    question: str = Field(description="Diagnostic question formulating what is being measured")
    target_entities: list[str] = Field(description="Entities whose telemetry should be retrieved")
    discriminates: list[str] = Field(description="List of competing hypothesis IDs differentiated by this request")
    information_gain: float = Field(description="Expected information gain from retrieving this telemetry")
    cost: float = Field(default=1.0, description="Resource or computational cost coefficient")
    latency: float = Field(default=1.0, description="Expected collection latency coefficient")
    risk: float = Field(default=0.0, description="Operational risk tier associated with query")
    reliability: float = Field(default=0.9, description="Collector accuracy and reliability score")
    availability: float = Field(default=1.0, description="Current availability of the target data source")
    priority: float = Field(description="Calculated composite priority score")


class DiscriminationProbeContract(Contract):
    """
    Step 3 Active Discrimination Probe: Dispatched by Zaki to distinguish between competing hypotheses.
    Binds a specific diagnostic tool from the DomainToolRegistry to candidate hypotheses.

    Attributes:
        probe_id: Semantic probe identifier (e.g. 'PROBE_N3_PING_CHECK').
        target_domain: Domain jurisdiction where probe executes.
        target_entity: Network node or link targeted by the probe.
        competing_hypotheses: The hypothesis IDs this probe was dispatched to separate.
        diagnostic_tool_ref: Registered tool identifier in DomainToolRegistry.
        execution_params: Parameter payload passed to tool execution.
        expected_outcome_if_true: Observation verifying primary hypothesis.
        expected_outcome_if_false: Observation refuting primary hypothesis.
        execution_status: Current execution phase ('PENDING', 'EXECUTING', 'COMPLETED', 'FAILED').
        discrimination_result: Resulting verdict or diagnostic conclusion.
    """
    probe_id: str = Field(description="Unique discrimination probe identifier")
    target_domain: str = Field(description="Domain where probe executes")
    target_entity: str = Field(description="Canonical slug or address of probed entity")
    competing_hypotheses: list[str] = Field(description="Hypothesis IDs to be differentiated")
    diagnostic_tool_ref: str = Field(description="Tool reference key registered in DomainToolRegistry")
    execution_params: dict[str, Any] = Field(default_factory=dict, description="Execution parameters for the diagnostic tool")
    expected_outcome_if_true: str = Field(description="Expected signal value if primary hypothesis is TRUE")
    expected_outcome_if_false: str = Field(description="Expected signal value if primary hypothesis is FALSE")
    execution_status: str = Field(
        default="PENDING",
        description="Lifecycle status: PENDING, EXECUTING, COMPLETED, or FAILED"
    )
    discrimination_result: str | None = Field(
        default=None,
        description="Diagnostic outcome and hypothesis resolution notes"
    )


class InvestigationResult(Contract):
    """
    Aggregated outcome of an end-to-end operational diagnostic investigation.

    Attributes:
        run_id: Execution run identifier.
        scenario_id: Telecommunications scenario identifier.
        terminal_state: Final diagnostic termination state (EXPLAINED, PARTIALLY_EXPLAINED, etc.).
        ranked_hypotheses: List of competing hypotheses sorted by confidence score.
        selected_hypothesis_id: ID of the winning/confirmed hypothesis (if any).
        supporting_evidence: Evidence IDs confirming the diagnosis.
        contradicting_evidence: Evidence IDs refuting competing hypotheses.
        missing_evidence: Unobserved telemetry items.
        explanation_coverage: Fraction of total incident symptoms accounted for.
        unexplained_observations: Residual symptoms left unexplained by winning hypothesis.
        knowledge_gaps: Topological or causal knowledge gaps uncovered during investigation.
        candidate_relationships: Novel relationships proposed for gbrain promotion.
        canonical_entities_used: Canonical entities participating in the diagnosis.
        reasoning_summary: Human-readable narrative explaining diagnostic deduction.
        provenance: Audit trail records documenting inference steps.
        next_best_evidence: Prioritized queue of telemetry queries if more evidence needed.
        discovery_mode: Whether investigation uncovered previously unmapped dependencies.
        causal_event_graph: Sequence of causal transitions identified.
        metadata: Execution parameters and environment metadata.
        diagnostics: Internal engine debug metrics and residual tracking.
    """
    run_id: str = Field(description="Unique execution run identifier")
    scenario_id: str = Field(description="Scenario identifier for the failure mode")
    terminal_state: Terminal = Field(description="Final diagnostic termination classification")
    ranked_hypotheses: list[Hypothesis] = Field(description="Ranked list of evaluated hypotheses")
    selected_hypothesis_id: str | None = Field(description="Identifier of confirmed root cause hypothesis")
    supporting_evidence: list[str] = Field(description="Evidence IDs directly supporting diagnosis")
    contradicting_evidence: list[str] = Field(description="Evidence IDs refuting alternative hypotheses")
    missing_evidence: list[str] = Field(description="Telemetry requested but unavailable")
    explanation_coverage: float = Field(description="Symptom coverage ratio between 0.0 and 1.0")
    unexplained_observations: list[str] = Field(description="Residual symptoms not accounted for")
    knowledge_gaps: list[str] = Field(description="Knowledge gap IDs identified during triage")
    candidate_relationships: list[CandidateRelationship] = Field(description="Candidate graph edges discovered")
    canonical_entities_used: list[str] = Field(description="Canonical entity slugs involved in reasoning")
    reasoning_summary: str = Field(description="Comprehensive NOC SME diagnostic summary")
    provenance: list[dict[str, Any]] = Field(description="Step-by-step diagnostic provenance records")
    next_best_evidence: list[EvidenceRequest] = Field(description="Next best queries to resolve uncertainty")
    discovery_mode: bool = Field(description="Flag indicating discovery of novel network topology")
    causal_event_graph: list[dict[str, Any]] = Field(description="Directed causal event graph structure")
    metadata: dict[str, Any] = Field(description="Simulation and runtime metadata")
    diagnostics: dict[str, Any] = Field(description="Telemetry sensor and engine diagnostic metrics")

    @property
    def unexplained_residuals(self) -> list[Any]:
        """Convenience property for accessing unexplained residual symptoms."""
        return self.diagnostics.get("unexplained_residuals", self.unexplained_observations)


class ValidationDecision(Contract):
    """
    Legacy binary validation decision for candidate relationships.

    Attributes:
        candidate: CandidateRelationship under evaluation.
        validator: Name or identifier of human reviewer.
        decision: Binary determination ('validate' or 'reject').
        reason: Justification text.
        timestamp: Review timestamp.
    """
    candidate: CandidateRelationship = Field(description="Candidate relationship record")
    validator: str = Field(min_length=1, description="Reviewer name or role")
    decision: Literal["validate", "reject"] = Field(description="Validation determination")
    reason: str = Field(min_length=1, description="Review rationale")
    timestamp: datetime = Field(description="Decision timestamp")
