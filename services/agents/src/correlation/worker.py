"""Fixture-driven correlation worker. Use --write to publish results to gbrain."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from .adapters import SyntheticGrafanaAdapter
from .engine import CorrelationEngine
from .gbrain_writer import GbrainWriter
from .identity import IdentityResolver
from .models import AlarmEvent, EvidenceEvent, ServiceIntent
from .namespaces import incident_slug
from .registry import IncidentRegistry


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def run(
    fixtures: Path,
    *,
    write: bool = False,
    source: str = "fixtures",
    service: str | None = None,
    intent: str | None = None,
) -> list[dict]:
    alarms, evidence, intents = _load_inputs(fixtures, source=source, service=service, intent=intent)
    results = CorrelationEngine().correlate(alarms, evidence, intents)
    registry = IncidentRegistry()
    writer = GbrainWriter() if write else None
    report: list[dict] = []
    for result in results:
        incident_id = incident_slug(result.services[0] if result.services else "unmapped-service", result.correlation_key)
        if writer and result.outcome != "standalone":
            incident_id = writer.write(result)
        if result.outcome != "standalone":
            registry.upsert({"incident_id": incident_id, "tenant_id": result.tenant_id, "status": "open" if result.outcome == "incident" else "candidate", "scope": result.scope, "score": result.score, "domains": result.domains, "services": result.services, "owner": None})
        report.append({"incident_id": incident_id, "outcome": result.outcome, "scope": result.scope, "score": result.score, "reasons": result.reasons})
    return report


def _load_inputs(
    fixtures: Path,
    *,
    source: str,
    service: str | None,
    intent: str | None,
) -> tuple[list[AlarmEvent], list[EvidenceEvent], list[ServiceIntent]]:
    if source == "grafana-synthetic":
        return SyntheticGrafanaAdapter(fixtures).load(service=service, intent=intent)
    resolver = IdentityResolver.from_file(fixtures / "components.json")
    alarms = [resolver.resolve(AlarmEvent(row.get("tenant_id", "local"), row["id"], _time(row["timestamp"]), row["severity"], row["domain"], row.get("source_system", "fixture"), row["object_id"], row["alarm_code"], row.get("component_kind", "component"), row.get("location"), tuple(row.get("service_ids", [])))) for row in _jsonl(fixtures / "alarms.jsonl")]
    evidence = [EvidenceEvent(row["id"], row["kind"], _time(row["timestamp"]), row.get("service_id"), row.get("breached", False), row) for row in _jsonl(fixtures / "evidence.jsonl")]
    intents = [ServiceIntent(row["service_id"], row["intent_id"], row["target_kpi"], float(row["target_value"])) for row in _jsonl(fixtures / "intents.jsonl")]
    return alarms, evidence, intents


def main() -> None:
    parser = argparse.ArgumentParser(description="Run fixture alarm correlation")
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--source", choices=("fixtures", "grafana-synthetic"), default="fixtures")
    parser.add_argument("--service")
    parser.add_argument("--intent")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.fixtures, write=args.write, source=args.source, service=args.service, intent=args.intent), indent=2))


if __name__ == "__main__":
    main()
