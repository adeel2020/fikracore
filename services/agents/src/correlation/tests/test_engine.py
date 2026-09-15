from datetime import datetime, timedelta, timezone

from correlation.engine import CorrelationEngine
from correlation.models import AlarmEvent, EvidenceEvent, ServiceIntent


NOW = datetime(2026, 8, 28, 10, 0, tzinfo=timezone.utc)


def alarm(source_id: str, *, domain: str = "ran", severity: str = "major", service: str = "registration") -> AlarmEvent:
    return AlarmEvent("tenant-a", source_id, NOW + timedelta(minutes=int(source_id[-1])), severity, domain, "nms", source_id, "LINK_DOWN", service_ids=(service,))


def test_inter_domain_incident_requires_structural_and_support_evidence():
    engine = CorrelationEngine(known_novelty_keys={("ran", "nms", "LINK_DOWN", "component"), ("transport", "nms", "LINK_DOWN", "component")})
    result = engine.correlate(
        [alarm("alarm-1", domain="ran", severity="critical"), alarm("alarm-2", domain="transport")],
        [EvidenceEvent("kpi-1", "kpi", NOW, "registration", breached=True)],
        [ServiceIntent("registration", "registration-availability", "rsr", 99.5)],
    )[0]
    assert result.outcome == "incident"
    assert result.scope == "inter-domain"


def test_time_and_severity_without_support_remain_candidate():
    engine = CorrelationEngine(known_novelty_keys={("ran", "nms", "LINK_DOWN", "component")})
    result = engine.correlate([alarm("alarm-1", severity="critical"), alarm("alarm-2")])[0]
    assert result.outcome == "candidate"


def test_unknown_critical_alarm_is_not_dropped():
    result = CorrelationEngine().correlate([alarm("alarm-1", severity="critical")])[0]
    assert result.outcome == "candidate"
    assert result.scope == "intra-domain"
