"""
Evidence Lifecycle Contracts: Raw, Emerging, & Validated
=========================================================
This module implements the 3-Tier Telecommunications Evidence Lifecycle.

Architecture & Progression:
1. RAW (Tier 1 - RawEvidenceContract):
   Pristine stream events directly from Kafka topics, gNMI subscriptions, Syslog,
   or SNMP trap daemons. Preserves raw payload exactly as ingested for forensic audit.
2. EMERGING (Tier 2 - EmergingEvidenceContract):
   Windowed aggregations, subtle baseline drifts, rate deviations, and pre-incident
   weak signals detected before hard threshold alarms trigger.
3. VALIDATED (Tier 3 - ValidatedEvidenceContract & Evidence):
   Evidence evaluated during an active investigation against specific hypotheses,
   tagged with definitive polarity verdicts (CONFIRMS, SUPPORTS, CONTRADICTS, RULES_OUT).
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from pydantic import Field
from .base import Contract


class EvidenceTier(str, Enum):
    """
    Classification tier representing the maturation stage of telemetry evidence.
    """
    RAW = "RAW"             # Unprocessed external telemetry event
    EMERGING = "EMERGING"   # Correlated weak signal / statistical baseline deviation
    VALIDATED = "VALIDATED" # Evaluated and cross-referenced with topology hypotheses


class GeneratedRunInput(Contract):
    """
    Simulation environment input manifest for FikraCore synthetic runs.

    Attributes:
        run_id: Unique simulation run identifier.
        scenario_id: Telecommunications scenario identifier (e.g. 'IMS_EMERGENCY_DROP').
        difficulty_profile: Complexity rating (L1 simple to L5 multi-domain cascade).
        seed: Random seed for deterministic reproducibility.
        alarms_path: Filesystem path to simulated alarm journal.
        logs_path: Filesystem path to raw application logs.
        metrics_path: Filesystem path to time-series performance metrics.
        kpis_path: Filesystem path to high-level SLA/KPI metrics.
        traces_path: Filesystem path to protocol call flows (PCAP/JSON).
        changes_path: Filesystem path to maintenance and configuration change events.
        tickets_path: Filesystem path to ITSM/trouble tickets.
        recovery_path: Filesystem path to post-incident recovery telemetry.
        source_profiles_path: Filesystem path to synthetic noise and source profiles.
    """
    run_id: str = Field(description="Unique simulation run execution identifier")
    scenario_id: str = Field(description="Scenario identifier for the telecom failure mode")
    difficulty_profile: Literal["L1", "L2", "L3", "L4", "L5"] = Field(
        description="Scenario complexity tier from L1 (isolated) to L5 (adversarial cascade)"
    )
    seed: int = Field(description="Random generator seed for reproducible telemetry")
    alarms_path: str | None = Field(default=None, description="Path to simulated alarm events")
    logs_path: str | None = Field(default=None, description="Path to simulated component log files")
    metrics_path: str | None = Field(default=None, description="Path to simulated counter and gauge time series")
    kpis_path: str | None = Field(default=None, description="Path to calculated service KPIs")
    traces_path: str | None = Field(default=None, description="Path to protocol signaling traces (e.g. SIP/NGAP)")
    changes_path: str | None = Field(default=None, description="Path to network configuration change audit records")
    tickets_path: str | None = Field(default=None, description="Path to trouble ticketing entries")
    recovery_path: str | None = Field(default=None, description="Path to post-remediation verification telemetry")
    source_profiles_path: str | None = Field(default=None, description="Path to vendor telemetry schema profiles")


class RawEvidenceContract(Contract):
    """
    Tier 1 Evidence: Pristine network telemetry ingested directly from collectors.
    Zero semantic mutation; used for forensic integrity and raw audit replay.

    Attributes:
        telemetry_id: Unique telemetry event identifier.
        event_time: Telemetry generation timestamp at network element.
        stream_source: Collection protocol/bus (e.g. 'kafka', 'gnmi', 'snmp', 'syslog').
        raw_payload: Unmodified dictionary payload from network source.
        ingestion_time: Timestamp when event reached FikraCore ingestion bus.
    """
    telemetry_id: str = Field(description="Unique event ID assigned upon ingestion")
    event_time: datetime = Field(description="Timestamp recorded by generating network element")
    stream_source: str = Field(description="Ingestion bus or transport protocol (kafka, gnmi, syslog)")
    raw_payload: dict[str, Any] = Field(default_factory=dict, description="Pristine unparsed raw source payload")
    ingestion_time: datetime | None = Field(default=None, description="Timestamp received by platform")


class EmergingEvidenceContract(Contract):
    """
    Tier 2 Evidence: The Emerging Condition Bridge.
    Windowed sequences of INFO/WARN alerts, rate deviations, and weak signals
    that indicate developing anomalies before major incident declarations.

    Attributes:
        emerging_id: Unique identifier for the emerging condition.
        signal_name: Name of metric or pattern showing drift (e.g., 'crc_error_rate_drift').
        domain: Relevant operational domain (e.g., 'IP_TRANSPORT').
        target_entity: Affected network element or interface.
        severity_trend: Progression vector ('STABLE', 'ESCALATING', 'DE-ESCALATING').
        window_duration_seconds: Time window over which anomaly aggregated.
        aggregated_signal_count: Number of weak signals rolled into this condition.
        observed_baseline_deviation: Standard deviations from historical baseline.
        operational_significance: Triage categorization ('WEAK_SIGNAL', 'ANOMALY_DETECTED', 'PRE_INCIDENT_CANDIDATE').
        first_seen: Earliest signal timestamp in aggregation window.
        last_seen: Most recent signal timestamp in aggregation window.
    """
    emerging_id: str = Field(description="Unique identifier for emerging anomaly cluster")
    signal_name: str = Field(description="Descriptive metric or alarm pattern showing baseline drift")
    domain: str = Field(description="Operational domain jurisdiction where signal originated")
    target_entity: str = Field(description="Canonical or native ID of the degrading network element")
    severity_trend: str = Field(
        default="STABLE",
        description="Directional severity movement: STABLE, ESCALATING, or DE-ESCALATING"
    )
    window_duration_seconds: int = Field(default=300, description="Rolling time window for correlation")
    aggregated_signal_count: int = Field(default=1, description="Count of underlying telemetry events")
    observed_baseline_deviation: float = Field(
        default=0.0,
        description="Z-score or percentage deviation from normal operating baseline"
    )
    operational_significance: str = Field(
        default="WEAK_SIGNAL",
        description="NOC SME triage category: WEAK_SIGNAL, ANOMALY_DETECTED, or PRE_INCIDENT_CANDIDATE"
    )
    first_seen: datetime = Field(description="Timestamp of first constituent event")
    last_seen: datetime = Field(description="Timestamp of latest constituent event")


class Evidence(Contract):
    """
    Canonical normalized evidence contract in FikraCore (100% backward compatible).
    Represents an observed or inferred diagnostic fact during an investigation.

    Attributes:
        evidence_id: Semantic evidence ID.
        event_time: Timestamp of event occurrence.
        ingestion_time: Timestamp of ingestion into memory graph.
        domain: Telecom domain jurisdiction.
        entity: Display name of the network entity.
        canonical_entity: Canonical gbrain entity slug (e.g., 'router-agg-01').
        entity_type: Type of network node (e.g., 'PE_ROUTER', 'UPF').
        service: List of user-facing or transport services traversing entity.
        evidence_type: Category (e.g., 'ALARM', 'METRIC_ANOMALY', 'LOG_PATTERN').
        value: Numeric, textual, or dictionary measurement payload.
        signal: Named telemetry signal.
        source: System providing telemetry (e.g., 'Prometheus', 'Netcool').
        source_vendor: Equipment manufacturer (e.g., 'Cisco', 'Nokia', 'Huawei').
        source_native_entity: Raw element name before normalization.
        source_reliability: Confidence weight in collector accuracy (0.0 to 1.0).
        freshness: Temporal decay factor (0.0 stale to 1.0 real-time).
        observed_or_inferred: Epistemic status of evidence.
        polarity: Operational state ('abnormal', 'healthy', 'context', 'unknown').
        severity: Operational severity string.
        observed_path: Causal or network path sequence.
        duplicate_ids: Redundant event IDs deduplicated into this record.
    """
    evidence_id: str = Field(description="Semantic unique identifier for this evidence record")
    event_time: datetime = Field(description="Timestamp when event occurred at element")
    ingestion_time: datetime = Field(description="Timestamp when ingested into investigation engine")
    domain: str = Field(description="Telecommunications domain scope")
    entity: str = Field(description="Human-readable node or link display name")
    canonical_entity: str = Field(description="Authoritative gbrain canonical node identifier")
    entity_type: str = Field(default="unknown", description="Hardware or VNF element classification")
    service: list[str] = Field(default_factory=list, description="Associated telecommunication services impacted")
    evidence_type: str = Field(description="Modality of telemetry: ALARM, METRIC, LOG, CONFIG, TRACE")
    value: Any = Field(default=None, description="Scalar, boolean, or structured value of observation")
    signal: str = Field(default="", description="Specific metric, KPI, or event signal name")
    source: str = Field(description="Collection subsystem or data lake source name")
    source_vendor: str = Field(default="unknown", description="Equipment vendor of the originating element")
    source_native_entity: str = Field(description="Original EMS/vendor identifier before canonical normalization")
    source_reliability: float = Field(default=0.5, ge=0.0, le=1.0, description="Inherent sensor reliability score")
    freshness: float = Field(default=1.0, ge=0.0, le=1.0, description="Freshness coefficient reflecting time decay")
    observed_or_inferred: Literal["OBSERVED", "INFERRED", "CONFIRMED", "REJECTED"] = Field(
        default="OBSERVED",
        description="Whether evidence was directly captured or causally synthesized"
    )
    polarity: Literal["abnormal", "healthy", "context", "unknown"] = Field(
        default="unknown",
        description="Diagnostic polarity indicating health state"
    )
    severity: str = Field(default="UNKNOWN", description="Severity classification string")
    observed_path: list[str] = Field(default_factory=list, description="Topological transmission hops observed")
    duplicate_ids: list[str] = Field(default_factory=list, description="Deduplicated event identifiers")


class ValidatedEvidenceContract(Contract):
    """
    Tier 3 Evidence: Evaluated Evidence with Explicit Hypothesis Verdict.
    Produced when a specialist agent or discrimination probe analyzes an Evidence record
    against active competing hypotheses.

    Attributes:
        evidence_id: Reference to evaluated Evidence record.
        canonical_entity: Canonical entity under evaluation.
        domain: Domain jurisdiction of the validating agent.
        verdict: Definite diagnostic impact on hypotheses (SUPPORTS, CONTRADICTS, CONFIRMS, RULES_OUT).
        corroborating_hypotheses: List of hypothesis IDs influenced by this verdict.
        confidence: Evaluator certainty score (0.0 to 1.0).
        validated_by_agent: ID or name of the specialist agent executing validation.
        timestamp: Time when validation was concluded.
    """
    evidence_id: str = Field(description="Identifier of the evaluated evidence item")
    canonical_entity: str = Field(description="Canonical network node or link identifier")
    domain: str = Field(description="Domain jurisdiction of evaluating specialist")
    verdict: Literal["SUPPORTS", "CONTRADICTS", "CONFIRMS", "RULES_OUT"] = Field(
        description="Diagnostic verdict indicating causal impact on evaluated hypotheses"
    )
    corroborating_hypotheses: list[str] = Field(
        default_factory=list,
        description="Identifiers of hypotheses whose confidence was affected by this verdict"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score of the verdict")
    validated_by_agent: str = Field(description="Agent identifier that evaluated and signed this verdict")
    timestamp: datetime = Field(description="Timestamp when verdict was finalized")
