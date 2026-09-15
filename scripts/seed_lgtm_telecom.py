#!/usr/bin/env python3
"""Seed local LGTM with telecom-shaped OTLP metrics and logs.

This script is intentionally dependency-free so it can run in the local repo
without installing OpenTelemetry SDK packages. It sends OTLP/HTTP JSON payloads
to the `grafana/otel-lgtm` collector exposed by `deploy/monitoring/lgtm`.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Scenario:
    service_id: str
    domain: str
    object_id: str
    metric_name: str
    metric_value: float
    threshold: float
    log_message: str
    severity: str


SCENARIOS: dict[str, Scenario] = {
    "voice-call-setup": Scenario(
        service_id="voice-call-setup",
        domain="mobile-core",
        object_id="pcscf-01",
        metric_name="cssr_percent",
        metric_value=93.2,
        threshold=99.5,
        log_message="SIP INVITE failure rate increased for voice-call-setup on pcscf-01",
        severity="ERROR",
    ),
    "sgi-data": Scenario(
        service_id="sgi-data",
        domain="mobile-core",
        object_id="pgw-01",
        metric_name="sgi_throughput_percent",
        metric_value=52.5,
        threshold=80.0,
        log_message="SGi throughput degradation observed with NAT allocation warnings",
        severity="WARN",
    ),
    "lte-attach": Scenario(
        service_id="lte-attach",
        domain="mobile-core",
        object_id="mme-01",
        metric_name="lte_attach_success_rate_percent",
        metric_value=91.7,
        threshold=99.0,
        log_message="Attach Reject and Diameter ULR timeout symptoms increased",
        severity="ERROR",
    ),
}


def _attr(key: str, value: str | float | bool) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"key": key, "value": {"boolValue": value}}
    if isinstance(value, (float, int)):
        return {"key": key, "value": {"doubleValue": float(value)}}
    return {"key": key, "value": {"stringValue": str(value)}}


def _post_json(url: str, payload: dict[str, Any]) -> tuple[int, str]:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def _metric_payload(scenario: Scenario, now_ns: int) -> dict[str, Any]:
    attrs = [
        _attr("service", scenario.service_id),
        _attr("service_id", scenario.service_id),
        _attr("domain", scenario.domain),
        _attr("object_id", scenario.object_id),
        _attr("threshold", scenario.threshold),
        _attr("breached", scenario.metric_value < scenario.threshold),
        _attr("source_namespace", "lgtm-local-seed"),
    ]
    return {
        "resourceMetrics": [
            {
                "resource": {
                    "attributes": [
                        _attr("service.name", f"telecom.{scenario.service_id}"),
                        _attr("telecom.scenario", scenario.service_id),
                    ]
                },
                "scopeMetrics": [
                    {
                        "scope": {"name": "kagent.telecom.seed"},
                        "metrics": [
                            {
                                "name": scenario.metric_name,
                                "unit": "%" if "percent" in scenario.metric_name else "1",
                                "description": f"Synthetic telecom KPI for {scenario.service_id}",
                                "gauge": {
                                    "dataPoints": [
                                        {
                                            "timeUnixNano": str(now_ns),
                                            "asDouble": scenario.metric_value,
                                            "attributes": attrs,
                                        }
                                    ]
                                },
                            }
                        ],
                    }
                ],
            }
        ]
    }


def _log_payload(scenario: Scenario, now_ns: int) -> dict[str, Any]:
    return {
        "resourceLogs": [
            {
                "resource": {
                    "attributes": [
                        _attr("service.name", f"telecom.{scenario.service_id}"),
                        _attr("telecom.scenario", scenario.service_id),
                    ]
                },
                "scopeLogs": [
                    {
                        "scope": {"name": "kagent.telecom.seed"},
                        "logRecords": [
                            {
                                "timeUnixNano": str(now_ns),
                                "severityText": scenario.severity,
                                "body": {"stringValue": scenario.log_message},
                                "attributes": [
                                    _attr("service", scenario.service_id),
                                    _attr("service_id", scenario.service_id),
                                    _attr("domain", scenario.domain),
                                    _attr("object_id", scenario.object_id),
                                    _attr("source_namespace", "lgtm-local-seed"),
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    }


def seed(base_url: str, scenario_names: list[str]) -> dict[str, Any]:
    now_ns = time.time_ns()
    results: list[dict[str, Any]] = []
    for name in scenario_names:
        scenario = SCENARIOS[name]
        metric_status, metric_body = _post_json(f"{base_url.rstrip('/')}/v1/metrics", _metric_payload(scenario, now_ns))
        log_status, log_body = _post_json(f"{base_url.rstrip('/')}/v1/logs", _log_payload(scenario, now_ns))
        results.append(
            {
                "scenario": name,
                "metric_status": metric_status,
                "metric_body": metric_body[:300],
                "log_status": log_status,
                "log_body": log_body[:300],
            }
        )
    return {"otlp_http": base_url, "seeded": results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed local LGTM with telecom incident telemetry.")
    parser.add_argument("--otlp-http", default="http://localhost:4318", help="OTLP/HTTP collector base URL")
    parser.add_argument(
        "--scenario",
        action="append",
        choices=sorted(SCENARIOS) + ["all"],
        default=None,
        help="Scenario to seed. Repeatable. Defaults to all.",
    )
    args = parser.parse_args()

    requested = args.scenario or ["all"]
    selected = sorted(SCENARIOS) if "all" in requested else requested
    result = seed(args.otlp_http, selected)
    print(json.dumps(result, indent=2))
    failed = [row for row in result["seeded"] if row["metric_status"] >= 300 or row["log_status"] >= 300]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
