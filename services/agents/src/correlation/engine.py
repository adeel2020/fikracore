"""Deterministic, incident-agnostic correlation policy."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from hashlib import sha256
from typing import Iterable

from .models import AlarmEvent, CorrelationResult, EvidenceEvent, ServiceIntent


class CorrelationEngine:
    """Correlates any normalized alarms; no incident, domain, or code is seeded."""

    def __init__(
        self,
        *,
        window_minutes: int = 10,
        incident_threshold: int = 70,
        candidate_threshold: int = 40,
        known_novelty_keys: Iterable[tuple[str, str, str, str]] = (),
    ) -> None:
        self.window = timedelta(minutes=window_minutes)
        self.incident_threshold = incident_threshold
        self.candidate_threshold = candidate_threshold
        self.known_novelty_keys = set(known_novelty_keys)

    def correlate(
        self,
        alarms: Iterable[AlarmEvent],
        evidence: Iterable[EvidenceEvent] = (),
        intents: Iterable[ServiceIntent] = (),
    ) -> list[CorrelationResult]:
        events = self._dedupe(sorted(alarms, key=lambda event: event.timestamp))
        evidence_events = list(evidence)
        intent_by_service = {intent.service_id: intent for intent in intents}
        groups: list[list[AlarmEvent]] = []
        remaining = list(events)
        while remaining:
            seed = remaining.pop(0)
            group = [seed]
            changed = True
            while changed:
                changed = False
                for event in remaining[:]:
                    if any(self._related(event, member) for member in group):
                        group.append(event)
                        remaining.remove(event)
                        changed = True
            groups.append(group)

        results = [self._score(group, evidence_events, intent_by_service) for group in groups]
        return sorted(results, key=lambda result: (result.outcome != "incident", -result.score))

    @staticmethod
    def _dedupe(events: list[AlarmEvent]) -> list[AlarmEvent]:
        seen: set[tuple[str, str]] = set()
        unique: list[AlarmEvent] = []
        for event in events:
            key = (event.source_system, event.source_id)
            if key not in seen:
                seen.add(key)
                unique.append(event)
        return unique

    def _related(self, left: AlarmEvent, right: AlarmEvent) -> bool:
        if left.tenant_id != right.tenant_id:
            return False
        if abs(left.timestamp - right.timestamp) > self.window:
            return False
        same_location = bool(left.location and right.location and left.location == right.location)
        return bool(set(left.service_ids) & set(right.service_ids)) or same_location

    def _score(
        self,
        alarms: list[AlarmEvent],
        evidence: list[EvidenceEvent],
        intents: dict[str, ServiceIntent],
    ) -> CorrelationResult:
        services = sorted({service for alarm in alarms for service in alarm.service_ids})
        domains = {alarm.domain for alarm in alarms}
        related_evidence = [
            item for item in evidence
            if item.service_id in services
            and any(abs(item.timestamp - alarm.timestamp) <= self.window for alarm in alarms)
        ]
        reasons: list[str] = []
        score = 0
        structural = bool(services)
        support = False
        if len(alarms) >= 2:
            score += 25
            reasons.append("multiple alarms in the correlation window")
        if structural:
            score += 20
            reasons.append("shared affected service")
        if any(item.kind == "kpi" and item.breached for item in related_evidence):
            score += 15
            support = True
            reasons.append("KPI breach supports service impact")
        if any(item.kind in {"ticket", "log", "trace"} for item in related_evidence):
            score += 10
            support = True
            reasons.append("independent operational evidence")
        violated = any(intent.service_id in services and any(item.kind == "kpi" and item.breached for item in related_evidence) for intent in intents.values())
        if violated:
            score += 15
            support = True
            reasons.append("service intent is violated")
        if any(alarm.severity.lower() == "critical" for alarm in alarms):
            score += 10
            reasons.append("critical source alarm")
        novel = any(alarm.novelty_key not in self.known_novelty_keys for alarm in alarms)
        if novel:
            reasons.append("novel alarm signature retained for review")

        # An incident needs both structural and independent impact/support evidence.
        if len(alarms) >= 2 and structural and support and score >= self.incident_threshold:
            outcome = "incident"
        elif score >= self.candidate_threshold or novel or any(a.severity.lower() == "critical" for a in alarms):
            outcome = "candidate"
        else:
            outcome = "standalone"
        anchor = min(alarm.timestamp for alarm in alarms).replace(second=0, microsecond=0).isoformat()
        raw_key = f"{alarms[0].tenant_id}|{services[0] if services else 'unmapped'}|{anchor}"
        key = sha256(raw_key.encode()).hexdigest()[:16]
        return CorrelationResult(
            correlation_key=key,
            tenant_id=alarms[0].tenant_id,
            alarms=alarms,
            evidence=related_evidence,
            services=services,
            score=score,
            reasons=reasons,
            outcome=outcome,
            scope="inter-domain" if len(domains) > 1 else "intra-domain",
            intent_status="violated" if violated else ("matched" if any(s in intents for s in services) else "not_matched"),
        )
