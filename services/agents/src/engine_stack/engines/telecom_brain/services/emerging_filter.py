"""
Emerging Evidence Filter (Tier 2 Evidence Bridge)
=================================================
Windowed aggregation and pre-incident weak-signal correlation.

Role & Architectural Boundary:
- Filters and aggregates raw telemetry events (Tier 1 RawEvidenceContract / stream events)
  before formal incident creation.
- Correlates INFO, WARN, and baseline drift sequences over a sliding window (default 300s).
- Detects emerging abnormal conditions, directional severity trends, and weak signals.
- Emits EmergingEvidenceContract (Tier 2) and optionally graduates them to canonical
  Evidence (Tier 3) for active investigation.
- 100% epistemic integrity: never accesses or leaks hidden simulation ground truth.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional, Tuple, Union

from ..investigation.contracts.evidence import (
    EmergingEvidenceContract,
    Evidence,
    RawEvidenceContract,
)

FORBIDDEN_FIELDS = {
    "hidden", "hidden_truth", "ground_truth", "causal_chain", "root_condition",
    "root_entity", "root_domain", "expected_root", "evaluator_expectations",
    "noise_manifest", "simulator_world", "actual_blast_radius",
}


def reject_truth(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower().replace("-", "_") in FORBIDDEN_FIELDS:
                raise ValueError(f"Evaluator-only field is forbidden: {key}")
            reject_truth(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            reject_truth(child)


class EmergingEvidenceFilter:
    """
    Sliding window aggregator for detecting emerging anomalies from pre-incident telemetry.
    """

    def __init__(
        self,
        window_duration_seconds: int = 300,
        weak_signal_threshold: int = 2,
        anomaly_threshold: int = 3,
        candidate_incident_threshold: int = 5,
        baseline_z_score_threshold: float = 2.0,
    ) -> None:
        """
        Initialize the Emerging Evidence Filter.

        Args:
            window_duration_seconds: Duration of the rolling aggregation window in seconds.
            weak_signal_threshold: Minimum signal count to register WEAK_SIGNAL.
            anomaly_threshold: Minimum signal count to register ANOMALY_DETECTED.
            candidate_incident_threshold: Signal count to escalate to PRE_INCIDENT_CANDIDATE.
            baseline_z_score_threshold: Standard deviations from baseline indicating drift.
        """
        self.window_duration_seconds = window_duration_seconds
        self.weak_signal_threshold = weak_signal_threshold
        self.anomaly_threshold = anomaly_threshold
        self.candidate_incident_threshold = candidate_incident_threshold
        self.baseline_z_score_threshold = baseline_z_score_threshold

        # Aggregation state: key -> list of raw observation tuples (timestamp, severity, value, baseline, raw_id)
        self._window_buffers: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = defaultdict(list)
        self._active_conditions: Dict[str, EmergingEvidenceContract] = {}

    def _extract_event_metadata(
        self, event: Union[RawEvidenceContract, Evidence, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Normalize raw event into common metadata dictionary, rejecting hidden truth."""
        if isinstance(event, RawEvidenceContract):
            raw = event.raw_payload
            reject_truth(raw)
            event_time = event.event_time
            domain = raw.get("domain", "unknown")
            entity = raw.get("entity", raw.get("entity_id", "unknown"))
            signal = str(raw.get("signal", raw.get("metric_name", raw.get("alarm_name", "unknown"))))
            severity = str(raw.get("severity", "INFO")).upper()
            value = raw.get("value")
            baseline = raw.get("baseline_value", raw.get("baseline"))
            raw_id = event.telemetry_id
        elif isinstance(event, Evidence):
            event_time = event.event_time
            domain = event.domain
            entity = event.canonical_entity or event.entity
            signal = event.signal
            severity = str(event.severity).upper()
            value = event.value
            baseline = None
            raw_id = event.evidence_id
        else:
            reject_truth(event)
            event_time = event.get("event_time")
            if isinstance(event_time, str):
                try:
                    event_time = datetime.fromisoformat(event_time.replace("Z", "+00:00"))
                except Exception:
                    event_time = datetime.now(timezone.utc)
            elif not isinstance(event_time, datetime):
                event_time = datetime.now(timezone.utc)

            domain = event.get("domain", "unknown")
            entity = event.get("entity", event.get("entity_id", event.get("canonical_entity", "unknown")))
            signal = str(event.get("signal", event.get("metric_name", event.get("alarm_name", "unknown"))))
            severity = str(event.get("severity", "INFO")).upper()
            value = event.get("value")
            baseline = event.get("baseline_value", event.get("baseline"))
            raw_id = str(event.get("evidence_id", event.get("event_id", event.get("telemetry_id", "raw"))))

        return {
            "event_time": event_time,
            "domain": domain,
            "target_entity": entity,
            "signal_name": signal,
            "severity": severity,
            "value": value,
            "baseline": baseline,
            "raw_id": raw_id,
        }

    def process_event(
        self, event: Union[RawEvidenceContract, Evidence, Dict[str, Any]]
    ) -> Optional[EmergingEvidenceContract]:
        """
        Process a single telemetry event into the rolling window.

        Returns:
            EmergingEvidenceContract if the event triggered or updated an emerging condition;
            None if the event was filtered out or below significance thresholds.
        """
        meta = self._extract_event_metadata(event)
        key = (meta["domain"], meta["target_entity"], meta["signal_name"])
        now = meta["event_time"]

        # Append to buffer
        self._window_buffers[key].append(meta)

        # Evict events outside rolling window
        cutoff = now.timestamp() - self.window_duration_seconds
        self._window_buffers[key] = [
            ev for ev in self._window_buffers[key]
            if ev["event_time"].timestamp() >= cutoff
        ]

        events = self._window_buffers[key]
        count = len(events)

        if count < self.weak_signal_threshold:
            return None

        # Compute baseline deviation if numerical values are available
        num_values = [ev["value"] for ev in events if isinstance(ev["value"], (int, float))]
        num_baselines = [ev["baseline"] for ev in events if isinstance(ev["baseline"], (int, float))]

        z_score = 0.0
        if num_values and num_baselines:
            mean_val = sum(num_values) / len(num_values)
            mean_base = sum(num_baselines) / len(num_baselines)
            variance = sum((v - mean_val) ** 2 for v in num_values) / len(num_values)
            std_dev = math.sqrt(variance) if variance > 0.0001 else max(abs(mean_base) * 0.1, 0.01)
            z_score = round(abs(mean_val - mean_base) / std_dev, 2)

        # Compute directional trend
        if len(events) >= 3:
            first_half = events[:len(events) // 2]
            second_half = events[len(events) // 2:]
            sev_weights = {"INFO": 1, "NOTICE": 1, "WARN": 2, "WARNING": 2, "MINOR": 3, "MAJOR": 4, "CRITICAL": 5}
            w_first = sum(sev_weights.get(e["severity"], 1) for e in first_half) / len(first_half)
            w_second = sum(sev_weights.get(e["severity"], 1) for e in second_half) / len(second_half)
            if w_second > w_first + 0.5 or len(second_half) > len(first_half) * 1.5:
                trend = "ESCALATING"
            elif w_first > w_second + 0.5:
                trend = "DE-ESCALATING"
            else:
                trend = "STABLE"
        else:
            trend = "STABLE"

        # Determine operational significance
        if count >= self.candidate_incident_threshold or z_score >= self.baseline_z_score_threshold * 1.5:
            significance = "PRE_INCIDENT_CANDIDATE"
        elif count >= self.anomaly_threshold or z_score >= self.baseline_z_score_threshold:
            significance = "ANOMALY_DETECTED"
        else:
            significance = "WEAK_SIGNAL"

        first_seen = min(e["event_time"] for e in events)
        last_seen = max(e["event_time"] for e in events)

        emerging_id = f"EMG-{meta['domain']}-{meta['target_entity']}-{meta['signal_name']}".replace("/", "_").replace(" ", "_")

        condition = EmergingEvidenceContract(
            emerging_id=emerging_id,
            signal_name=meta["signal_name"],
            domain=meta["domain"],
            target_entity=meta["target_entity"],
            severity_trend=trend,
            window_duration_seconds=self.window_duration_seconds,
            aggregated_signal_count=count,
            observed_baseline_deviation=z_score,
            operational_significance=significance,
            first_seen=first_seen,
            last_seen=last_seen,
        )

        self._active_conditions[emerging_id] = condition
        return condition

    def process_batch(
        self, events: List[Union[RawEvidenceContract, Evidence, Dict[str, Any]]]
    ) -> List[EmergingEvidenceContract]:
        """Process a sequence of telemetry events, returning all emerging conditions detected."""
        detected = []
        for ev in sorted(events, key=lambda e: getattr(e, "event_time", e.get("event_time") if isinstance(e, dict) else datetime.min)):
            res = self.process_event(ev)
            if res and res not in detected:
                detected.append(res)
        return list(self._active_conditions.values())

    def get_active_conditions(self) -> List[EmergingEvidenceContract]:
        """Return all currently active emerging condition contracts."""
        return list(self._active_conditions.values())

    def graduate_to_evidence(
        self, condition: EmergingEvidenceContract, canonical_entity_slug: Optional[str] = None
    ) -> Evidence:
        """
        Promote an EmergingEvidenceContract into a canonical Evidence record ready for investigation.
        """
        now = datetime.now(timezone.utc)
        return Evidence(
            evidence_id=f"EV-{condition.emerging_id}",
            event_time=condition.last_seen,
            ingestion_time=now,
            domain=condition.domain,
            entity=condition.target_entity,
            canonical_entity=canonical_entity_slug or condition.target_entity,
            entity_type="NETWORK_ELEMENT",
            service=[],
            evidence_type="EMERGING_CONDITION",
            value={
                "signal_name": condition.signal_name,
                "aggregated_count": condition.aggregated_signal_count,
                "baseline_deviation": condition.observed_baseline_deviation,
                "severity_trend": condition.severity_trend,
                "window_duration_seconds": condition.window_duration_seconds,
            },
            signal=condition.signal_name,
            source="emerging_evidence_filter",
            source_vendor="FikraCore",
            source_native_entity=condition.target_entity,
            source_reliability=0.9,
            freshness=1.0,
            observed_or_inferred="OBSERVED",
            polarity="abnormal",
            severity=condition.operational_significance,
            observed_path=[],
        )

    def reset(self) -> None:
        """Clear all active buffers and condition state."""
        self._window_buffers.clear()
        self._active_conditions.clear()
