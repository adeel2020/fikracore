from pathlib import Path

from correlation.adapters import SyntheticGrafanaAdapter
from correlation.engine import CorrelationEngine


FIXTURES = Path("services/agents/src/correlation/fixtures/grafana-lgtm")


def test_synthetic_adapter_filters_by_intent() -> None:
    alarms, evidence, intents = SyntheticGrafanaAdapter(FIXTURES).load(intent="4g_attach_sr")

    assert {intent.intent_id for intent in intents} == {"4g_attach_sr"}
    assert {service for alarm in alarms for service in alarm.service_ids} == {"lte-attach"}
    assert {item.service_id for item in evidence} == {"lte-attach"}


def test_synthetic_grafana_inputs_correlate_to_incident() -> None:
    alarms, evidence, intents = SyntheticGrafanaAdapter(FIXTURES).load(intent="sgi_throughput")

    result = CorrelationEngine().correlate(alarms, evidence, intents)[0]

    assert result.outcome == "incident"
    assert result.scope == "inter-domain"
    assert result.intent_status == "violated"
    assert "sgi-data" in result.services
