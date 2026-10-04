"""Allowlisted operational ingestion, timestamp handling, and flood reduction."""

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .contracts import Evidence, GeneratedRunInput, EmergingEvidenceContract, RawEvidenceContract

STREAMS = ("alarms", "logs", "metrics", "kpis", "traces", "changes", "tickets", "recovery")
FORBIDDEN = {"hidden", "hidden_truth", "ground_truth", "causal_chain", "root_condition",
             "root_entity", "root_domain", "expected_root", "evaluator_expectations",
             "noise_manifest", "simulator_world", "actual_blast_radius"}


def reject_truth(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower().replace("-", "_") in FORBIDDEN:
                raise ValueError(f"Evaluator-only field is forbidden: {key}")
            reject_truth(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            reject_truth(child)


def operational_path(path: str | Path, root: Path) -> Path:
    candidate = Path(path).resolve()
    if not candidate.is_relative_to(root.resolve()) or "hidden" in candidate.parts:
        raise ValueError("Evidence must reside within the designated operational directory")
    return candidate


def input_from_run(directory: Path) -> GeneratedRunInput:
    # Only metadata is selected. Manifest references to world/scenario/hidden files are never followed.
    import yaml
    manifest = yaml.safe_load((directory / "scenario_manifest.yaml").read_text())
    return GeneratedRunInput(
        run_id=manifest["run_id"], scenario_id=manifest["scenario_id"],
        difficulty_profile=manifest["difficulty_profile"]["level"], seed=manifest["random_seed"],
        **{f"{stream}_path": str(directory / "operational" / f"{stream}.jsonl")
           for stream in STREAMS if (directory / "operational" / f"{stream}.jsonl").exists()},
    )


def normalize(raw: dict, stream: str, profiles: dict | None = None) -> Evidence:
    reject_truth(raw)
    source = raw.get("source", raw.get("source_system", "unknown"))
    profile = (profiles or {}).get(source, {})
    entity = raw.get("entity", raw.get("entity_id", raw.get("changed_entity")))
    if not entity:
        raise ValueError("Operational evidence requires an entity")
    signal = str(raw.get("signal") or raw.get("alarm_name") or raw.get("metric_name") or
                 raw.get("kpi_name") or raw.get("message") or raw.get("result") or "")
    polarity = raw.get("polarity", "unknown")
    if polarity == "unknown":
        words = set(re.findall(r"[a-z]+", signal.lower()))
        if words & {"healthy", "normal", "stable", "successful"}:
            polarity = "healthy"
        elif stream in {"changes", "recovery"}:
            polarity = "context"
        elif words & {"degraded", "failure", "failed", "high", "timeout", "breach", "drop", "retries"}:
            polarity = "abnormal"
        elif stream in {"metrics", "kpis"} and isinstance(raw.get("value"), (int, float)):
            baseline = raw.get("baseline_value")
            if isinstance(baseline, (int, float)):
                polarity = "abnormal" if abs(raw["value"] - baseline) > max(abs(baseline) * .2, .01) else "healthy"
        elif stream == "tickets":
            polarity = "abnormal"
    services = raw.get("service", raw.get("service_context", raw.get("impacted_service", [])))
    return Evidence(
        evidence_id=raw.get("evidence_id", raw.get("event_id")),
        event_time=raw["event_time"], ingestion_time=raw["ingestion_time"],
        domain=raw.get("domain", "unknown"), entity=entity,
        canonical_entity=raw.get("canonical_entity", raw.get("canonical_entity_id", entity)),
        entity_type=raw.get("entity_type", "unknown"), service=[services] if isinstance(services, str) else services,
        evidence_type=stream, value=raw.get("value"), signal=signal, source=source,
        source_vendor=raw.get("source_vendor", raw.get("vendor_profile", "unknown")),
        source_native_entity=raw.get("source_native_entity", raw.get("source_native_entity_name", entity)),
        source_reliability=raw.get("source_reliability", profile.get("reliability", raw.get("confidence", .5))),
        freshness=raw.get("freshness", profile.get("freshness", 1)),
        observed_or_inferred=raw.get("observed_or_inferred", "OBSERVED"),
        polarity=polarity, severity=raw.get("severity", "UNKNOWN"), observed_path=raw.get("observed_path", []),
    )


def load_evidence(run: GeneratedRunInput, operational_root: Path) -> tuple[list[Evidence], dict]:
    profiles = {}
    hashes = {}
    if run.source_profiles_path:
        path = operational_path(run.source_profiles_path, operational_root)
        content = path.read_bytes()
        if path.suffix.lower() in {".yaml", ".yml"}:
            import yaml
            profiles = yaml.safe_load(content)
        else:
            profiles = json.loads(content)
        reject_truth(profiles)
        hashes["source_profiles"] = hashlib.sha256(content).hexdigest()
    result = []
    for stream in STREAMS:
        value = getattr(run, f"{stream}_path")
        if value is None:
            continue
        path = operational_path(value, operational_root)
        content = path.read_bytes()
        hashes[stream] = hashlib.sha256(content).hexdigest()
        for line in content.splitlines():
            if line.strip():
                result.append(normalize(json.loads(line), stream, profiles))
    seen = {}
    for item in result:
        if item.evidence_id in seen and item != seen[item.evidence_id]:
            raise ValueError(f"Conflicting duplicate evidence ID: {item.evidence_id}")
        seen[item.evidence_id] = item
    return list(seen.values()), hashes


def collapse(evidence: list[Evidence]) -> list[Evidence]:
    groups = {}
    for item in sorted(evidence, key=lambda e: (e.event_time, e.evidence_id)):
        # Source identity matters: independent observations never count as duplicate alarms.
        key = (item.canonical_entity, item.source, item.evidence_type, item.signal,
               item.polarity, json.dumps(item.value, sort_keys=True), int(item.event_time.timestamp()) // 60)
        if key not in groups:
            groups[key] = item
        else:
            previous = groups[key]
            groups[key] = previous.model_copy(update={"duplicate_ids": previous.duplicate_ids + [item.evidence_id]})
    return list(groups.values())
