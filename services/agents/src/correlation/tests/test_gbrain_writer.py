from datetime import datetime, timezone

from correlation.gbrain_writer import GbrainWriter
from correlation.models import AlarmEvent, CorrelationResult, EvidenceEvent


class FakeGbrainClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def call(self, tool: str, params: dict | None = None):
        params = params or {}
        self.calls.append((tool, params))
        if tool == "get_links":
            return []
        return {}


def _result() -> CorrelationResult:
    now = datetime(2026, 8, 28, 10, tzinfo=timezone.utc)
    alarms = [
        AlarmEvent(
            tenant_id="tenant-a",
            source_id="ran-1",
            timestamp=now,
            severity="critical",
            domain="ran",
            source_system="ran-nms",
            object_id="gnodeb-17",
            alarm_code="LINK_DOWN",
            component_kind="gnodeb",
            location="site-42",
            service_ids=("ue-registration",),
        ),
        AlarmEvent(
            tenant_id="tenant-a",
            source_id="transport-1",
            timestamp=now,
            severity="major",
            domain="transport",
            source_system="transport-nms",
            object_id="agg-sw-03",
            alarm_code="HIGH_LOSS",
            component_kind="aggregation-switch",
            location="site-42",
            service_ids=("ue-registration",),
        ),
    ]
    evidence = [
        EvidenceEvent(
            source_id="kpi-ue-registration",
            kind="kpi",
            timestamp=now,
            service_id="ue-registration",
            breached=True,
            attributes={"kpi": "Registration Success Rate", "label": "RSR breach for UE registration"},
        ),
        EvidenceEvent(
            source_id="ticket-1",
            kind="ticket",
            timestamp=now,
            service_id="ue-registration",
            attributes={"label": "Customer-impact ticket opened"},
        ),
    ]
    return CorrelationResult(
        correlation_key="abc123",
        tenant_id="tenant-a",
        alarms=alarms,
        evidence=evidence,
        services=["ue-registration"],
        score=95,
        reasons=["shared affected service", "KPI breach supports service impact"],
        outcome="incident",
        scope="inter-domain",
        intent_status="violated",
    )


def test_writer_publishes_story_graph_shape() -> None:
    client = FakeGbrainClient()
    writer = GbrainWriter(client=client)  # type: ignore[arg-type]

    incident_slug = writer.write(_result())

    assert incident_slug == "incidents/mobile-core/ue-registration-abc123"
    put_slugs = [params["slug"] for tool, params in client.calls if tool == "put_page"]
    links = [params for tool, params in client.calls if tool == "add_link"]

    assert "mobile-core/incidents/ue-registration-abc123" in put_slugs
    assert "correlation/mobile-core/clusters/abc123" in put_slugs
    assert "correlation/mobile-core/decisions/abc123" in put_slugs
    assert "correlation/mobile-core/hypotheses/abc123" in put_slugs
    assert "domains/mobile-core/networks/5gcn/service-procedures/ue-registration" in put_slugs
    assert "domains/ran/functions/gnodeb-17" in put_slugs
    assert "domains/transport/functions/agg-sw-03" in put_slugs
    assert "incidents/mobile-core/kpi-events/kpi-ue-registration" in put_slugs
    assert "storytelling/mobile-core/stories/ue-registration-abc123" in put_slugs
    assert "learning/mobile-core/notes/ue-registration-abc123" in put_slugs
    assert "assets/mobile-core/playbooks/ue-registration-failure-triage" in put_slugs
    assert any(link["link_type"] == "affects" for link in links)
    assert any(link["link_type"] == "involves" for link in links)
    assert any(link["link_type"] == "detected-by" for link in links)
    assert any(link["link_type"] == "measures" for link in links)
    assert any(link["link_type"] == "derived-from" for link in links)
    assert any(link["link_type"] == "has-learning-note" for link in links)


def test_writer_keeps_grafana_evidence_in_grafana_namespace() -> None:
    client = FakeGbrainClient()
    result = _result()
    result.alarms[0] = AlarmEvent(
        tenant_id="tenant-a",
        source_id="grafana-alert-1",
        timestamp=result.alarms[0].timestamp,
        severity="critical",
        domain="ran",
        source_system="grafana-alerting",
        object_id="gnodeb-17",
        alarm_code="LINK_DOWN",
        component_kind="gnodeb",
        service_ids=("ue-registration",),
    )
    result.evidence[0] = EvidenceEvent(
        source_id="grafana-prom-1",
        kind="kpi",
        timestamp=result.evidence[0].timestamp,
        service_id="ue-registration",
        breached=True,
        attributes={
            "source_namespace": "grafana",
            "source_kind": "prometheus",
            "kpi": "Registration Success Rate",
            "label": "RSR breach for UE registration",
        },
    )

    GbrainWriter(client=client).write(result)  # type: ignore[arg-type]

    put_slugs = [params["slug"] for tool, params in client.calls if tool == "put_page"]
    links = [params for tool, params in client.calls if tool == "add_link"]

    assert "grafana/alerts/grafana-alert-1" in put_slugs
    assert "grafana/metrics/grafana-prom-1" in put_slugs
    assert any(
        link["link_type"] == "supported-by" and link["to"] == "grafana/metrics/grafana-prom-1"
        for link in links
    )
