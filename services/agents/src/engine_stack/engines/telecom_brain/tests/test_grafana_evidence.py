from __future__ import annotations

from engine_stack.engines.telecom_brain.services.grafana_evidence import GrafanaEvidenceProvider


class FakeHub:
    def call_tool_sync(self, connector_id, tool_name, arguments):
        assert connector_id == "grafana"
        if tool_name == "read_alerts":
            return {
                "alerts": [
                    {
                        "alertname": "IMSVoiceSetupFailure",
                        "startsAt": "2026-09-04T08:00:00Z",
                        "confidence": 0.88,
                    }
                ]
            }
        return {"results": []}


class DiscoveryHub:
    def __init__(self) -> None:
        self.calls = []

    def list_tools_sync(self, connector_id):
        assert connector_id == "grafana"
        return {
            "tools": [
                {"name": "list_alert_rules"},
                {"name": "list_datasources"},
                {"name": "query_prometheus"},
                {"name": "query_loki_logs"},
                {"name": "query_tempo"},
                {"name": "search_dashboards"},
            ]
        }

    def call_tool_sync(self, connector_id, tool_name, arguments):
        assert connector_id == "grafana"
        self.calls.append((tool_name, arguments))
        if tool_name == "list_datasources":
            return {"datasources": [{"uid": "prom", "type": "prometheus"}, {"uid": "loki", "type": "loki"}]}
        if tool_name == "list_alert_rules":
            return {"alerts": [{"name": "Voice setup failures", "startsAt": "2026-09-04T08:00:00Z"}]}
        if tool_name == "query_prometheus":
            assert set(arguments) == {"datasourceUid", "expr", "queryType", "endTime"}
            return {"data": {"result": [{"metric": {"__name__": "voice_cssr"}, "value": [1, "93.2"]}]}}
        if tool_name == "query_loki_logs":
            assert set(arguments) == {"datasourceUid", "logql", "limit", "direction"}
            return {"streams": [{"stream": {"service": "ims"}, "values": [["1", "SIP timeout spike"]]}]}
        if tool_name == "query_tempo":
            return {"traces": [{"traceID": "trace-1", "service": "ims-call-session"}]}
        if tool_name == "search_dashboards":
            return {"dashboards": [{"uid": "voice-ops", "title": "Voice Operations"}]}
        return {}


def test_grafana_evidence_provider_normalizes_mcp_results() -> None:
    evidence = GrafanaEvidenceProvider(FakeHub()).evidence_for_incident(
        "incidents/ims/voice-call-setup-05841af2e3f4f430",
        query="voice call setup",
    )

    assert len(evidence) == 1
    assert evidence[0].value == "IMSVoiceSetupFailure"
    assert evidence[0].source == "grafana/read_alerts"
    assert evidence[0].relationship == "telemetry-evidence"
    assert evidence[0].confidence == 0.88


def test_grafana_evidence_provider_discovers_real_mcp_tool_aliases() -> None:
    hub = DiscoveryHub()
    evidence = GrafanaEvidenceProvider(hub).evidence_for_incident(
        "incidents/ims/voice-call-setup-05841af2e3f4f430",
        query="voice cssr ims",
        limit=10,
    )

    assert [call[0] for call in hub.calls] == [
        "list_datasources",
        "list_alert_rules",
        "query_prometheus",
        "query_loki_logs",
        "query_tempo",
        "search_dashboards",
    ]
    assert {item.source for item in evidence} == {
        "grafana/list_alert_rules",
        "grafana/query_prometheus",
        "grafana/query_loki_logs",
        "grafana/query_tempo",
        "grafana/search_dashboards",
    }
    assert any(item.value == "Voice Operations" for item in evidence)
