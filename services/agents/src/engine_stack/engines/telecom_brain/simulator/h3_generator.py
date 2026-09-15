"""Dedicated 30-Unit H3 Learning Pair Generator.

Generates 30 Paired Learning Units across 4 distinct cohorts:
1. Positive Transfer (10 units)
2. Cross-Domain / Cross-Service Transfer (10 units)
3. Stale / Changed Topology (5 units)
4. Poisoned / Incorrect Validation (5 units)

Enforces strict epistemic hygiene (§4, §6, §7):
- Incident B differs from Incident A in service, symptoms, timestamps, and blast radius.
- Zero replay-as-learning.
- Hidden truth is strictly isolated to future_incident/hidden/ (evaluator only).
- Produces clean operational telemetry files for Incident B.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any
import yaml

from ..presentation.naming import default_naming_resolver


REFERENCE_NETWORK_PATH = (
    Path(__file__).parent / "operator_model" / "reference_synthetic_network.yaml"
)
H2_RUNS_DIR = Path(__file__).parent / "h2_runs"
H3_RUNS_DIR = Path(__file__).parent / "h3_runs"


def generate_all_h3_learning_units(output_dir: Path | str | None = None) -> list[dict[str, Any]]:
    """Generate all 30 paired learning units under output_dir."""
    target_dir = Path(output_dir) if output_dir else H3_RUNS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    with open(REFERENCE_NETWORK_PATH) as f:
        network_data = yaml.safe_load(f)

    entities = network_data.get("entities", [])
    relationships = network_data.get("relationships", [])

    h2_runs = sorted([d for d in H2_RUNS_DIR.iterdir() if d.is_dir() and d.name.startswith("RUN-H2-")])
    assert len(h2_runs) >= 30, f"Expected at least 30 H2 runs in {H2_RUNS_DIR}, found {len(h2_runs)}"

    units: list[dict[str, Any]] = []

    for idx in range(1, 31):
        h2_run_dir = h2_runs[idx - 1]
        with open(h2_run_dir / "scenario_manifest.yaml") as f:
            h2_manifest = yaml.safe_load(f)
        with open(h2_run_dir / "hidden" / "ground_truth.yaml") as f:
            h2_ground_truth = yaml.safe_load(f)
        with open(h2_run_dir / "operational" / "topology_view.yaml") as f:
            h2_op_topo = yaml.safe_load(f)

        if idx <= 10:
            cohort = "positive_transfer"
            val_decision = "ACCEPT"
            exp_value = "Improved causal path reconstruction and root cause accuracy"
        elif idx <= 20:
            cohort = "cross_domain_transfer"
            val_decision = "ACCEPT"
            exp_value = "Cross-domain fault propagation explainability across network domains"
        elif idx <= 25:
            cohort = "stale_topology"
            val_decision = "ACCEPT"
            exp_value = "Detection of stale/reconfigured topology without false confidence"
        else:
            cohort = "poisoned_validation"
            val_decision = "ACCEPT"  # Erroneous SME acceptance of incorrect candidate
            exp_value = "Poisoning resistance: detection of model contradiction or negative evidence"

        unit = _generate_single_learning_unit(
            unit_index=idx,
            cohort=cohort,
            val_decision=val_decision,
            expected_value=exp_value,
            h2_manifest=h2_manifest,
            h2_ground_truth=h2_ground_truth,
            h2_op_topo=h2_op_topo,
            h2_run_dir=h2_run_dir,
            target_dir=target_dir,
            reference_entities=entities,
            reference_relationships=relationships,
        )
        units.append(unit)

    return units


def _generate_single_learning_unit(
    unit_index: int,
    cohort: str,
    val_decision: str,
    expected_value: str,
    h2_manifest: dict[str, Any],
    h2_ground_truth: dict[str, Any],
    h2_op_topo: dict[str, Any],
    h2_run_dir: Path,
    target_dir: Path,
    reference_entities: list[dict[str, Any]],
    reference_relationships: list[dict[str, Any]],
) -> dict[str, Any]:
    unit_id = f"H3-LU-{unit_index:03d}"
    fut_id = f"H3-FUT-{unit_index:03d}"
    unit_dir = target_dir / unit_id
    unit_dir.mkdir(parents=True, exist_ok=True)

    future_dir = unit_dir / "future_incident"
    operational_dir = future_dir / "operational"
    hidden_dir = future_dir / "hidden"
    operational_dir.mkdir(parents=True, exist_ok=True)
    hidden_dir.mkdir(parents=True, exist_ok=True)

    hidden_gap = h2_ground_truth.get("hidden_gap", {})
    root_ent = hidden_gap.get("from_entity", "IP:PE:RTR-21")
    gap_type = hidden_gap.get("gap_type", "MISSING_SERVICE_TO_FUNCTION")
    downstream_ent = "SA5G:UPF:003" if root_ent != "SA5G:UPF:003" else "SA5G:AMF:001"

    # In telecom DAGs, downstream depends-on / routes-through upstream root
    # So candidate: source=downstream_ent, target=root_ent, proposed_type="routes-through"
    if cohort == "poisoned_validation":
        candidate_src = downstream_ent
        candidate_tgt = "INFRA:COOL:A"  # Erroneous facility node
        candidate_rel_type = "depends-on"
    else:
        candidate_src = downstream_ent
        candidate_tgt = root_ent
        candidate_rel_type = "routes-through"

    candidate_id = f"KG-H3-{unit_index:03d}"

    # 1. Candidate Record
    candidate_record = {
        "candidate_id": candidate_id,
        "discovery_incident": h2_manifest["scenario_id"],
        "gap_type": gap_type,
        "source": candidate_src,
        "target": candidate_tgt,
        "proposed_type": candidate_rel_type,
        "state": "CANDIDATE",
        "confidence": 0.85,
        "supporting_evidence": [f"EV-H2-{h2_manifest['scenario_id']}-001"],
        "reason": f"Operational discovery in {h2_manifest['scenario_id']} indicates traffic forwarding from {candidate_src} to {candidate_tgt}",
    }

    # 2. Validation Record
    validation_record = {
        "validation_id": f"VAL-H3-{unit_index:03d}",
        "candidate_id": candidate_id,
        "decision": val_decision,
        "validated_by_role": "Transport Domain SME" if "RTR" in root_ent else "Mobile Core SME",
        "reason": f"SME operational assessment confirms dependency path between {candidate_src} and {candidate_tgt}.",
        "timestamp": "2026-09-11T12:00:00Z",
        "evidence_refs": [f"EV-H2-{h2_manifest['scenario_id']}-001"],
        "modified_relation": None,
    }

    # 3. Learning Unit Manifest
    unit_manifest = {
        "learning_unit_id": unit_id,
        "cohort": cohort,
        "discovery_incident": h2_manifest["scenario_id"],
        "candidate_id": candidate_id,
        "validation_decision": val_decision,
        "future_incident_id": fut_id,
        "expected_learning_value": expected_value,
        "validated_relation": {
            "source": candidate_src,
            "target": candidate_tgt,
            "relation": candidate_rel_type,
            "relationship_id": f"REL-PROM-H3-{unit_index:03d}",
        },
    }
    with open(unit_dir / "learning_unit_manifest.yaml", "w") as f:
        yaml.dump(unit_manifest, f, sort_keys=False)

    with open(unit_dir / "candidate_knowledge.yaml", "w") as f:
        yaml.dump(candidate_record, f, sort_keys=False)

    with open(unit_dir / "validation_decision.yaml", "w") as f:
        yaml.dump(validation_record, f, sort_keys=False)

    # 4. Future Incident B Telemetry (§6, §7: distinct from Incident A)
    t_start = datetime(2026, 9, 11, 14, 0, 0, tzinfo=timezone.utc)
    t1 = t_start.isoformat()
    t2 = (t_start + timedelta(seconds=12)).isoformat()
    t3 = (t_start + timedelta(seconds=25)).isoformat()

    if cohort == "positive_transfer":
        fut_service = "enterprise_l3_vpn"
        fut_signal_root = "BGP session down with customer edge router"
        fut_signal_down = "VPN tunnel packet discard threshold exceeded"
    elif cohort == "cross_domain_transfer":
        fut_service = "ims_voice_telephony"
        fut_signal_root = "Forwarding linecard buffer exhaustion"
        fut_signal_down = "SIP 503 Service Unavailable spike"
    elif cohort == "stale_topology":
        fut_service = "5g_sa_mission_critical"
        fut_signal_root = "healthy"
        fut_signal_down = "Ultra-reliable low-latency stream degraded"
    else:  # poisoned_validation
        fut_service = "corporate_internet_access"
        fut_signal_root = "Interface flap on peering port"
        fut_signal_down = "NAT pool exhaustion and customer gateway timeout"

    # Alarms for Future Incident B
    fut_alarms = []
    if cohort == "stale_topology":
        # Root node is completely healthy (evidence of stale dependency)
        fut_alarms.append({
            "evidence_id": f"EV-FUT-ALM-{fut_id}-001",
            "event_time": t1,
            "ingestion_time": t2,
            "domain": "IP_TRANSPORT",
            "entity": root_ent,
            "canonical_entity": root_ent,
            "evidence_type": "alarms",
            "signal": "healthy",
            "severity": "OK",
            "polarity": "healthy",
            "source": "nms-transport",
            "source_native_entity": root_ent,
            "source_reliability": 0.95,
            "freshness": 1.0,
            "observed_or_inferred": "OBSERVED",
            "service": [fut_service],
            "observed_path": [root_ent],
        })
    else:
        fut_alarms.append({
            "evidence_id": f"EV-FUT-ALM-{fut_id}-001",
            "event_time": t1,
            "ingestion_time": t2,
            "domain": "IP_TRANSPORT",
            "entity": root_ent,
            "canonical_entity": root_ent,
            "evidence_type": "alarms",
            "signal": fut_signal_root,
            "severity": "CRITICAL",
            "polarity": "abnormal",
            "source": "nms-transport",
            "source_native_entity": root_ent,
            "source_reliability": 0.95,
            "freshness": 1.0,
            "observed_or_inferred": "OBSERVED",
            "service": [fut_service],
            "observed_path": [root_ent],
        })

    # Downstream alarm
    fut_alarms.append({
        "evidence_id": f"EV-FUT-ALM-{fut_id}-002",
        "event_time": t2,
        "ingestion_time": t3,
        "domain": "MOBILE_CORE" if "ims" in fut_service else "IP_TRANSPORT",
        "entity": downstream_ent,
        "canonical_entity": downstream_ent,
        "evidence_type": "alarms",
        "signal": fut_signal_down,
        "severity": "MAJOR",
        "polarity": "abnormal",
        "source": "ems-core",
        "source_native_entity": downstream_ent,
        "source_reliability": 0.90,
        "freshness": 1.0,
        "observed_or_inferred": "OBSERVED",
        "service": [fut_service],
        "observed_path": [downstream_ent],
    })

    _write_jsonl(operational_dir / "alarms.jsonl", fut_alarms)

    # Logs for Incident B
    fut_logs = [
        {
            "evidence_id": f"EV-FUT-LOG-{fut_id}-001",
            "event_time": t1,
            "ingestion_time": t2,
            "domain": "IP_TRANSPORT",
            "entity": root_ent,
            "canonical_entity": root_ent,
            "evidence_type": "logs",
            "signal": "Carrier link fault detected" if cohort != "stale_topology" else "healthy",
            "severity": "ERROR" if cohort != "stale_topology" else "OK",
            "polarity": "abnormal" if cohort != "stale_topology" else "healthy",
            "source": "syslog",
            "source_native_entity": root_ent,
            "source_reliability": 0.90,
            "freshness": 1.0,
            "observed_or_inferred": "OBSERVED",
            "service": [fut_service],
            "observed_path": [root_ent],
        }
    ]
    _write_jsonl(operational_dir / "logs.jsonl", fut_logs)

    # Metrics
    fut_metrics = [
        {
            "evidence_id": f"EV-FUT-MET-{fut_id}-001",
            "event_time": t1,
            "ingestion_time": t2,
            "domain": "IP_TRANSPORT",
            "entity": root_ent,
            "canonical_entity": root_ent,
            "evidence_type": "metrics",
            "signal": "packet_loss_pct" if cohort != "stale_topology" else "healthy",
            "value": 24.5 if cohort != "stale_topology" else 0.0,
            "severity": "CRITICAL" if cohort != "stale_topology" else "OK",
            "polarity": "abnormal" if cohort != "stale_topology" else "healthy",
            "source": "prometheus",
            "source_native_entity": root_ent,
            "source_reliability": 0.95,
            "freshness": 1.0,
            "observed_or_inferred": "OBSERVED",
            "service": [fut_service],
            "observed_path": [root_ent],
        }
    ]
    _write_jsonl(operational_dir / "metrics.jsonl", fut_metrics)

    # KPIs
    fut_kpis = [
        {
            "evidence_id": f"EV-FUT-KPI-{fut_id}-001",
            "event_time": t2,
            "ingestion_time": t3,
            "domain": "SERVICE_QUALITY",
            "entity": downstream_ent,
            "canonical_entity": downstream_ent,
            "evidence_type": "kpis",
            "signal": "service_availability_pct",
            "value": 71.0,
            "severity": "MAJOR",
            "polarity": "abnormal",
            "source": "sla-monitor",
            "source_native_entity": downstream_ent,
            "source_reliability": 0.90,
            "freshness": 1.0,
            "observed_or_inferred": "OBSERVED",
            "service": [fut_service],
            "observed_path": [downstream_ent],
        }
    ]
    _write_jsonl(operational_dir / "kpis.jsonl", fut_kpis)

    # Traces
    fut_traces = [
        {
            "evidence_id": f"EV-FUT-TRC-{fut_id}-001",
            "event_time": t1,
            "ingestion_time": t2,
            "domain": "NETWORK_TRACE",
            "entity": downstream_ent,
            "canonical_entity": downstream_ent,
            "evidence_type": "traces",
            "signal": "Downstream flow interrupted beyond node",
            "severity": "HIGH",
            "polarity": "abnormal",
            "source": "telecom-tracer",
            "source_native_entity": downstream_ent,
            "source_reliability": 0.90,
            "freshness": 1.0,
            "observed_or_inferred": "OBSERVED",
            "service": [fut_service],
            "observed_path": [downstream_ent],
        }
    ]
    _write_jsonl(operational_dir / "traces.jsonl", fut_traces)

    _write_jsonl(operational_dir / "changes.jsonl", [])
    _write_jsonl(operational_dir / "tickets.jsonl", [
        {
            "evidence_id": f"EV-FUT-TCK-{fut_id}-001",
            "event_time": t2,
            "ingestion_time": t3,
            "domain": "CRM",
            "entity": "CRM:TICKET:001",
            "canonical_entity": "CRM:TICKET:001",
            "evidence_type": "tickets",
            "signal": f"Customer incident ticket opened for {fut_service}",
            "severity": "HIGH",
            "polarity": "abnormal",
            "source": "crm-portal",
            "source_native_entity": "CRM:TICKET:001",
            "source_reliability": 0.85,
            "freshness": 1.0,
            "observed_or_inferred": "OBSERVED",
            "service": [fut_service],
            "observed_path": ["CRM:TICKET:001"],
        }
    ])
    _write_jsonl(operational_dir / "recovery.jsonl", [])

    # Operational topology view for Incident B (BEFORE learning state)
    visible_entities = list(set(h2_op_topo.get("visible_entities", []) + [root_ent, downstream_ent, "CRM:TICKET:001"]))
    visible_rels = list(set(h2_op_topo.get("visible_relationships", [])))
    op_topo = {
        "visible_entities": visible_entities,
        "visible_relationships": visible_rels,
    }
    with open(operational_dir / "topology_view.yaml", "w") as f:
        yaml.dump(op_topo, f, sort_keys=False)

    # Hidden Truth & Expectations for Future Incident B
    hidden_ground_truth = {
        "scenario_id": fut_id,
        "root_entity": root_ent if cohort != "stale_topology" else downstream_ent,
        "impacted_service": fut_service,
        "requires_promoted_relation": (cohort in {"positive_transfer", "cross_domain_transfer"}),
        "is_stale_relation": (cohort == "stale_topology"),
        "is_poisoned_relation": (cohort == "poisoned_validation"),
    }
    with open(hidden_dir / "ground_truth.yaml", "w") as f:
        yaml.dump(hidden_ground_truth, f, sort_keys=False)

    evaluator_exp = {
        "scenario_id": fut_id,
        "expected_root_entity": root_ent if cohort != "stale_topology" else downstream_ent,
        "cohort": cohort,
        "expected_terminal_before": "MODEL_INSUFFICIENT" if cohort in {"positive_transfer", "cross_domain_transfer"} else "EXPLAINED",
        "expected_terminal_after": "EXPLAINED" if cohort in {"positive_transfer", "cross_domain_transfer"} else "MODEL_INSUFFICIENT",
        "expected_rank_improvement": (cohort in {"positive_transfer", "cross_domain_transfer"}),
    }
    with open(hidden_dir / "evaluator_expectations.yaml", "w") as f:
        yaml.dump(evaluator_exp, f, sort_keys=False)

    # Demo metadata
    src_disp = default_naming_resolver.to_display_name(candidate_src)
    tgt_disp = default_naming_resolver.to_display_name(candidate_tgt)
    demo_meta = {
        "demo": {
            "enabled": True,
            "title": f"Learning Transfer: {src_disp} -> {tgt_disp}",
            "cohort": cohort,
            "audience": "leadership",
            "duration_minutes": 5,
            "learning_objective": f"Demonstrate that validated operational knowledge ({src_disp} {candidate_rel_type} {tgt_disp}) improves reasoning on a different future incident ({fut_service}).",
            "steps": [
                f"Incident {h2_manifest['scenario_id']} exposes missing dependency",
                "FikraCore proposes safe candidate relationship",
                "Domain SME validates relationship with operational evidence",
                "Knowledge is promoted under 8 governance guardrails",
                f"Different future incident {fut_id} occurs on {fut_service}",
                "FikraCore reuses validated knowledge to reconstruct causal chain",
                "Root cause identified with higher accuracy and zero hallucination",
            ],
            "final_message": "Validated experience becomes reusable operational knowledge.",
        }
    }
    with open(unit_dir / "demo_metadata.yaml", "w") as f:
        yaml.dump(demo_meta, f, sort_keys=False)

    return unit_manifest


def _write_jsonl(path: Path, items: list[dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item) + "\n")


__all__ = [
    "generate_all_h3_learning_units",
    "H3_RUNS_DIR",
]
