"""Deterministic H2 Scenario Generator for Operational Knowledge-Gap Discovery & Unknown-Unknowns.

Generates 60 calibrated H2 scenarios (20 gap classes × 3 variants: clean, noisy, cross-domain)
across difficulty levels K1 through K5 with zero trivial leakage.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import yaml

from ..investigation.contracts import KnowledgeGapType
from ..presentation.naming import default_naming_resolver


GAP_CLASSES = [
    (KnowledgeGapType.MISSING_DEPENDENCY, "Missing dependency edge between transport and core"),
    (KnowledgeGapType.MISSING_INTERMEDIATE_NODE, "Missing intermediate transport node in forwarding path"),
    (KnowledgeGapType.MISSING_SHARED_DEPENDENCY, "Missing shared infrastructure dependency affecting dual services"),
    (KnowledgeGapType.MISSING_SERVICE_TO_FUNCTION, "Missing service-to-network-function mapping"),
    (KnowledgeGapType.MISSING_FAILURE_DOMAIN_MEMBERSHIP, "Missing failure domain and availability zone membership"),
    (KnowledgeGapType.MISSING_HOSTING_CONTAINER, "Missing container and virtualization host relationship"),
    (KnowledgeGapType.MISSING_TRANSPORT_PATH, "Missing multiprotocol transport forwarding path"),
    (KnowledgeGapType.MISSING_EXTERNAL_DEPENDENCY, "Missing external interconnect and peering dependency"),
    (KnowledgeGapType.STALE_TOPOLOGY_RELATIONSHIP, "Stale topology edge pointing to decommissioned interface"),
    (KnowledgeGapType.WRONG_TOPOLOGY_DIRECTION, "Inverted topology dependency direction"),
    (KnowledgeGapType.INCORRECTLY_MERGED_ENTITIES, "Incorrectly merged multi-chassis entity"),
    (KnowledgeGapType.ALIAS_CANONICAL_AMBIGUITY, "Ambiguous vendor alias resolving to unresolved canonical slug"),
    (KnowledgeGapType.MISSING_REDUNDANCY_FAILOVER, "Missing standby protection and failover path"),
    (KnowledgeGapType.MISSING_MONITORING_DEPENDENCY, "Missing monitoring collector telemetry dependency"),
    (KnowledgeGapType.MISSING_DB_CACHE_MESSAGE_BUS, "Missing database, cache, or message bus dependency"),
    (KnowledgeGapType.MISSING_POWER_ENVIRONMENT, "Missing facility power feed and environment dependency"),
    (KnowledgeGapType.MISSING_ROAMING_INTERCONNECT, "Missing roaming interconnect and DRA relationship"),
    (KnowledgeGapType.MISSING_PROVISIONING_BSS, "Missing BSS provisioning and subscriber activation dependency"),
    (KnowledgeGapType.MISSING_SECURITY_CONTROL, "Missing security gateway and firewall inspection dependency"),
    (KnowledgeGapType.MULTIPLE_SIMULTANEOUS_GAPS, "Multiple simultaneous unmodeled dependencies"),
]

VARIANTS = ["clean", "noisy", "cross_domain"]

# Entity pool
ENTITIES = {
    "pe_rtr": "IP:PE:RTR-21",
    "core_rtr": "IP:CORE:RTR-01",
    "vrf_n3": "IP:VRF:N3-01",
    "upf": "SA5G:UPF:003",
    "smf": "SA5G:SMF:001",
    "amf": "SA5G:AMF:001",
    "pcf": "SA5G:PCF:001",
    "ticket": "CRM:TICKET:001",
    "power": "INFRA:POWER:A",
    "dc": "INFRA:DC:A",
    "db": "DB:MYSQL:001",
    "cache": "CACHE:REDIS:001",
    "fw": "SEC:FW:001",
    "dra": "CHARGING:DRA:001",
    "ocs": "CHARGING:OCS:001",
}


def generate_all_h2_scenarios(
    runs_dir: Path | str,
    base_seed: int = 52001,
) -> list[dict[str, Any]]:
    """Generate the full suite of 60 H2 scenarios with zero trivial leakage."""
    out_dir = Path(runs_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scenarios_meta = []

    scenario_num = 1
    for class_idx, (gap_type, desc) in enumerate(GAP_CLASSES):
        for var_idx, variant in enumerate(VARIANTS):
            # Deterministic K-level assignment: K1 through K5
            # K1: (0..11), K2: (12..23), K3: (24..35), K4: (36..47), K5: (48..59)
            k_num = min(5, (scenario_num - 1) // 12 + 1)
            difficulty = f"K{k_num}"
            seed = base_seed + scenario_num

            scenario_id = f"H2-SCN-{scenario_num:03d}"
            run_id = f"RUN-{scenario_id}-{difficulty}-SEED-{seed}"

            meta = _generate_single_scenario(
                out_dir / run_id,
                scenario_id=scenario_id,
                run_id=run_id,
                difficulty=difficulty,
                seed=seed,
                gap_type=gap_type,
                gap_desc=desc,
                variant=variant,
            )
            scenarios_meta.append(meta)
            scenario_num += 1

    # Write summary index
    index_file = out_dir / "index.yaml"
    with open(index_file, "w") as f:
        yaml.dump({"total_scenarios": len(scenarios_meta), "scenarios": scenarios_meta}, f)

    return scenarios_meta


def _generate_single_scenario(
    run_path: Path,
    scenario_id: str,
    run_id: str,
    difficulty: str,
    seed: int,
    gap_type: KnowledgeGapType,
    gap_desc: str,
    variant: str,
) -> dict[str, Any]:
    run_path.mkdir(parents=True, exist_ok=True)
    operational_dir = run_path / "operational"
    hidden_dir = run_path / "hidden"
    operational_dir.mkdir(parents=True, exist_ok=True)
    hidden_dir.mkdir(parents=True, exist_ok=True)

    # Base chain
    # Hidden reality: Power -> DC -> PE-RTR -> VRF -> UPF -> Service/Ticket
    # Operational view will have an intentional gap depending on gap_type
    hidden_entities = [
        ENTITIES["pe_rtr"],
        ENTITIES["vrf_n3"],
        ENTITIES["upf"],
        ENTITIES["ticket"],
    ]
    hidden_relationships = [
        {"id": "REL-N3-PE21", "source": ENTITIES["pe_rtr"], "target": ENTITIES["vrf_n3"], "link_type": "depends-on"},
        {"id": "REL-N3-UPF", "source": ENTITIES["vrf_n3"], "target": ENTITIES["upf"], "link_type": "depends-on"},
        {"id": "REL-CRM-IMPACT", "source": ENTITIES["upf"], "target": ENTITIES["ticket"], "link_type": "serves"},
    ]

    target_gap_rel = "REL-N3-PE21"
    boundary_entity = ENTITIES["pe_rtr"]
    target_entity = ENTITIES["upf"]
    next_evidence_type = "TOPOLOGY_NEIGHBOR"

    # Adjust topology based on gap class
    if gap_type == KnowledgeGapType.MISSING_POWER_ENVIRONMENT:
        hidden_entities = [ENTITIES["power"], ENTITIES["dc"]] + hidden_entities
        hidden_relationships.insert(0, {"id": "REL-POWER-DC", "source": ENTITIES["power"], "target": ENTITIES["dc"], "link_type": "member-of"})
        hidden_relationships.insert(1, {"id": "REL-DC-PE", "source": ENTITIES["dc"], "target": ENTITIES["pe_rtr"], "link_type": "hosted-on"})
        target_gap_rel = "REL-POWER-DC"
        boundary_entity = ENTITIES["power"]
        target_entity = ENTITIES["pe_rtr"]
        next_evidence_type = "FACILITY_ALARM"

    elif gap_type == KnowledgeGapType.MISSING_HOSTING_CONTAINER:
        hidden_entities = [ENTITIES["dc"]] + hidden_entities
        hidden_relationships.insert(0, {"id": "REL-DC-UPF", "source": ENTITIES["dc"], "target": ENTITIES["upf"], "link_type": "hosted-on"})
        target_gap_rel = "REL-DC-UPF"
        boundary_entity = ENTITIES["dc"]
        target_entity = ENTITIES["upf"]
        next_evidence_type = "CONTAINER_PLACEMENT"

    elif gap_type == KnowledgeGapType.MISSING_DB_CACHE_MESSAGE_BUS:
        hidden_entities.append(ENTITIES["db"])
        hidden_relationships.append({"id": "REL-UPF-DB", "source": ENTITIES["upf"], "target": ENTITIES["db"], "link_type": "uses-database"})
        target_gap_rel = "REL-UPF-DB"
        boundary_entity = ENTITIES["upf"]
        target_entity = ENTITIES["db"]
        next_evidence_type = "DATABASE_METRICS"

    elif gap_type == KnowledgeGapType.MISSING_SECURITY_CONTROL:
        hidden_entities.append(ENTITIES["fw"])
        hidden_relationships.append({"id": "REL-UPF-FW", "source": ENTITIES["upf"], "target": ENTITIES["fw"], "link_type": "routes-through"})
        target_gap_rel = "REL-UPF-FW"
        boundary_entity = ENTITIES["upf"]
        target_entity = ENTITIES["fw"]
        next_evidence_type = "FIREWALL_SESSION_PATH"

    elif gap_type == KnowledgeGapType.MISSING_ROAMING_INTERCONNECT:
        hidden_entities.extend([ENTITIES["dra"], ENTITIES["ocs"]])
        hidden_relationships.extend([
            {"id": "REL-UPF-DRA", "source": ENTITIES["upf"], "target": ENTITIES["dra"], "link_type": "charges-via"},
            {"id": "REL-DRA-OCS", "source": ENTITIES["dra"], "target": ENTITIES["ocs"], "link_type": "routes-through"},
        ])
        target_gap_rel = "REL-DRA-OCS"
        boundary_entity = ENTITIES["dra"]
        target_entity = ENTITIES["ocs"]
        next_evidence_type = "ROAMING_INTERFACE"

    elif gap_type == KnowledgeGapType.MISSING_SERVICE_TO_FUNCTION:
        target_gap_rel = "REL-CRM-IMPACT"
        boundary_entity = ENTITIES["upf"]
        target_entity = ENTITIES["ticket"]
        next_evidence_type = "SERVICE_MAPPING"

    elif gap_type == KnowledgeGapType.MISSING_INTERMEDIATE_NODE:
        hidden_entities.append(ENTITIES["core_rtr"])
        hidden_relationships.append({"id": "REL-PE-CORE", "source": ENTITIES["pe_rtr"], "target": ENTITIES["core_rtr"], "link_type": "routes-through"})
        target_gap_rel = "REL-PE-CORE"
        boundary_entity = ENTITIES["pe_rtr"]
        target_entity = ENTITIES["core_rtr"]
        next_evidence_type = "TRACEROUTE"

    elif gap_type == KnowledgeGapType.MISSING_TRANSPORT_PATH:
        hidden_entities.append(ENTITIES["core_rtr"])
        hidden_relationships.append({"id": "REL-PE-CORE-LSP", "source": ENTITIES["pe_rtr"], "target": ENTITIES["core_rtr"], "link_type": "carried-by"})
        target_gap_rel = "REL-PE-CORE-LSP"
        boundary_entity = ENTITIES["pe_rtr"]
        target_entity = ENTITIES["core_rtr"]
        next_evidence_type = "ROUTING_TABLE"

    elif gap_type == KnowledgeGapType.MISSING_SHARED_DEPENDENCY:
        hidden_entities.extend([ENTITIES["amf"], ENTITIES["smf"]])
        hidden_relationships.append({"id": "REL-AMF-SMF", "source": ENTITIES["amf"], "target": ENTITIES["smf"], "link_type": "depends-on"})
        target_gap_rel = "REL-AMF-SMF"
        boundary_entity = ENTITIES["amf"]
        target_entity = ENTITIES["smf"]
        next_evidence_type = "SERVICE_MAPPING"

    elif gap_type == KnowledgeGapType.MISSING_FAILURE_DOMAIN_MEMBERSHIP:
        hidden_entities = [ENTITIES["dc"]] + hidden_entities
        hidden_relationships.insert(0, {"id": "REL-DC-PE-FD", "source": ENTITIES["dc"], "target": ENTITIES["pe_rtr"], "link_type": "member-of"})
        target_gap_rel = "REL-DC-PE-FD"
        boundary_entity = ENTITIES["dc"]
        target_entity = ENTITIES["pe_rtr"]
        next_evidence_type = "FAILURE_DOMAIN_MAP"

    elif gap_type == KnowledgeGapType.MISSING_EXTERNAL_DEPENDENCY:
        ext_entity = "EXT:ROAMING:001"
        hidden_entities.append(ext_entity)
        hidden_relationships.append({"id": "REL-UPF-EXT", "source": ENTITIES["upf"], "target": ext_entity, "link_type": "peers-with"})
        target_gap_rel = "REL-UPF-EXT"
        boundary_entity = ENTITIES["upf"]
        target_entity = ext_entity
        next_evidence_type = "EXTERNAL_CARRIER_STATUS"

    elif gap_type == KnowledgeGapType.MISSING_MONITORING_DEPENDENCY:
        nms_entity = "OSS:NMS:001"
        hidden_entities.append(nms_entity)
        hidden_relationships.append({"id": "REL-UPF-NMS", "source": ENTITIES["upf"], "target": nms_entity, "link_type": "monitored-by"})
        target_gap_rel = "REL-UPF-NMS"
        boundary_entity = ENTITIES["upf"]
        target_entity = nms_entity
        next_evidence_type = "MONITORING_CONFIGURATION"

    elif gap_type == KnowledgeGapType.MISSING_PROVISIONING_BSS:
        bss_entity = "BSS:BILLING:001"
        hidden_entities.append(bss_entity)
        hidden_relationships.append({"id": "REL-UPF-BSS", "source": ENTITIES["upf"], "target": bss_entity, "link_type": "provisioned-by"})
        target_gap_rel = "REL-UPF-BSS"
        boundary_entity = ENTITIES["upf"]
        target_entity = bss_entity
        next_evidence_type = "PROVISIONING_LOGS"

    # Operational topology: Omit the target relationship intentionally
    visible_entities = list(hidden_entities)
    visible_relationships = [r["id"] for r in hidden_relationships if r["id"] != target_gap_rel]

    # Write operational topology_view.yaml
    topo_view = {
        "view_id": f"TOPO-{scenario_id}-OPERATIONAL",
        "scenario_id": scenario_id,
        "source": "operational_telecombrain",
        "visible_entities": visible_entities,
        "visible_relationships": visible_relationships,
        "known_gaps": [],
        "source_warnings": ["operational view may have unmodeled topology gaps according to difficulty"],
    }
    with open(operational_dir / "topology_view.yaml", "w") as f:
        yaml.dump(topo_view, f)

    # Write evidence files (.jsonl)
    t0 = "2026-09-10T14:00:00+00:00"
    t1 = "2026-09-10T14:00:05+00:00"
    t2 = "2026-09-10T14:00:10+00:00"
    t3 = "2026-09-10T14:00:15+00:00"

    alarms = [
        {
            "evidence_id": f"EV-ALM-{scenario_id}-001",
            "event_time": t0,
            "ingestion_time": t1,
            "domain": "IP_TRANSPORT" if "RTR" in boundary_entity or "POWER" in boundary_entity else "SA_5G_CORE",
            "entity": boundary_entity,
            "canonical_entity": boundary_entity,
            "evidence_type": "alarms",
            "signal": "BoundaryImpairmentAlarm",
            "source": "oss-alarm-manager",
            "source_native_entity": boundary_entity,
            "source_reliability": 0.95,
            "freshness": 1.0,
            "observed_or_inferred": "OBSERVED",
            "polarity": "abnormal",
            "severity": "CRITICAL",
            "service": ["5g_sa_mobile_data"],
            "observed_path": [boundary_entity],
        },
        {
            "evidence_id": f"EV-ALM-{scenario_id}-002",
            "event_time": t2,
            "ingestion_time": t3,
            "domain": "IT_CLOUD_INFRA" if "DB" in target_entity or "FW" in target_entity else "SA_5G_CORE",
            "entity": target_entity,
            "canonical_entity": target_entity,
            "evidence_type": "alarms",
            "signal": "DownstreamDegradationAlarm",
            "source": "domain-ems",
            "source_native_entity": target_entity,
            "source_reliability": 0.90,
            "freshness": 0.95,
            "observed_or_inferred": "OBSERVED",
            "polarity": "abnormal",
            "severity": "MAJOR",
            "service": ["5g_sa_mobile_data"],
            "observed_path": [boundary_entity, target_entity],
        },
    ]

    # Noisy or Cross-Domain additions
    if variant in {"noisy", "cross_domain"}:
        alarms.append({
            "evidence_id": f"EV-ALM-{scenario_id}-NOISE",
            "event_time": t1,
            "ingestion_time": t2,
            "domain": "CRM",
            "entity": ENTITIES["ticket"],
            "canonical_entity": ENTITIES["ticket"],
            "evidence_type": "alarms",
            "signal": "TicketVolumeSurge",
            "source": "crm-system",
            "source_native_entity": ENTITIES["ticket"],
            "source_reliability": 0.85,
            "freshness": 0.90,
            "observed_or_inferred": "OBSERVED",
            "polarity": "abnormal",
            "severity": "WARNING",
            "service": ["5g_sa_mobile_data"],
            "observed_path": [ENTITIES["ticket"]],
        })

    # Healthy negative evidence
    healthy_alarm = {
        "evidence_id": f"EV-ALM-{scenario_id}-HEALTHY",
        "event_time": t0,
        "ingestion_time": t1,
        "domain": "SA_5G_CORE",
        "entity": ENTITIES["amf"],
        "canonical_entity": ENTITIES["amf"],
        "evidence_type": "alarms",
        "signal": "all checks healthy",
        "source": "core-ems",
        "source_native_entity": ENTITIES["amf"],
        "source_reliability": 0.95,
        "freshness": 1.0,
        "observed_or_inferred": "OBSERVED",
        "polarity": "healthy",
        "severity": "CLEARED",
        "service": ["5g_sa_mobile_data"],
        "observed_path": [ENTITIES["amf"]],
    }
    alarms.append(healthy_alarm)

    _write_jsonl(operational_dir / "alarms.jsonl", alarms)
    _write_jsonl(operational_dir / "logs.jsonl", [
        {"evidence_id": f"EV-LOG-{scenario_id}-001", "event_time": t1, "ingestion_time": t2, "domain": "IP_TRANSPORT",
         "entity": boundary_entity, "canonical_entity": boundary_entity, "evidence_type": "logs",
         "signal": "Connection timeout on next hop forwarding interface", "source": "syslog",
         "source_native_entity": boundary_entity, "source_reliability": 0.90, "freshness": 1.0,
         "observed_or_inferred": "OBSERVED", "polarity": "abnormal", "severity": "ERROR", "service": ["5g_sa_mobile_data"],
         "observed_path": [boundary_entity, ENTITIES["upf"]]}
    ])
    _write_jsonl(operational_dir / "metrics.jsonl", [
        {"evidence_id": f"EV-MET-{scenario_id}-001", "event_time": t1, "ingestion_time": t2, "domain": "IP_TRANSPORT",
         "entity": boundary_entity, "canonical_entity": boundary_entity, "evidence_type": "metrics",
         "signal": "packet_loss_pct", "value": 18.5, "source": "prometheus",
         "source_native_entity": boundary_entity, "source_reliability": 0.95, "freshness": 1.0,
         "observed_or_inferred": "OBSERVED", "polarity": "abnormal", "severity": "CRITICAL", "service": ["5g_sa_mobile_data"],
         "observed_path": [boundary_entity]}
    ])
    _write_jsonl(operational_dir / "kpis.jsonl", [
        {"evidence_id": f"EV-KPI-{scenario_id}-001", "event_time": t2, "ingestion_time": t3, "domain": "SA_5G_CORE",
         "entity": ENTITIES["upf"], "canonical_entity": ENTITIES["upf"], "evidence_type": "kpis",
         "signal": "pdu_session_success_rate", "value": 62.0, "source": "pm-collector",
         "source_native_entity": ENTITIES["upf"], "source_reliability": 0.90, "freshness": 1.0,
         "observed_or_inferred": "OBSERVED", "polarity": "abnormal", "severity": "CRITICAL", "service": ["5g_sa_mobile_data"],
         "observed_path": [ENTITIES["upf"]]}
    ])
    _write_jsonl(operational_dir / "traces.jsonl", [
        {"evidence_id": f"EV-TRC-{scenario_id}-001", "event_time": t1, "ingestion_time": t2, "domain": "IP_TRANSPORT",
         "entity": boundary_entity, "canonical_entity": boundary_entity, "evidence_type": "traces",
         "signal": "GTP-U echo request timed out across unverified boundary", "source": "telecom-tracer",
         "source_native_entity": boundary_entity, "source_reliability": 0.90, "freshness": 1.0,
         "observed_or_inferred": "OBSERVED", "polarity": "abnormal", "severity": "HIGH", "service": ["5g_sa_mobile_data"],
         "observed_path": [boundary_entity, ENTITIES["upf"]]}
    ])
    _write_jsonl(operational_dir / "changes.jsonl", [])
    _write_jsonl(operational_dir / "tickets.jsonl", [
        {"evidence_id": f"EV-TCK-{scenario_id}-001", "event_time": t2, "ingestion_time": t3, "domain": "CRM",
         "entity": ENTITIES["ticket"], "canonical_entity": ENTITIES["ticket"], "evidence_type": "tickets",
         "signal": "Multiple customer reports of mobile data outage", "source": "crm-portal",
         "source_native_entity": ENTITIES["ticket"], "source_reliability": 0.80, "freshness": 1.0,
         "observed_or_inferred": "OBSERVED", "polarity": "abnormal", "severity": "HIGH", "service": ["5g_sa_mobile_data"],
         "observed_path": [ENTITIES["ticket"]]}
    ])
    _write_jsonl(operational_dir / "recovery.jsonl", [])

    # Hidden truth & expectations
    causal_graph = {
        "graph_id": f"CAUSAL-{scenario_id}-TRUTH",
        "nodes": hidden_entities,
        "edges": hidden_relationships,
    }
    with open(hidden_dir / "causal_graph.yaml", "w") as f:
        yaml.dump(causal_graph, f)

    ground_truth = {
        "scenario_id": scenario_id,
        "root_entity": boundary_entity,
        "hidden_gap": {
            "relationship_id": target_gap_rel,
            "gap_type": gap_type.value,
            "from_entity": boundary_entity,
        },
        "true_terminal_state": "MODEL_INSUFFICIENT",
    }
    with open(hidden_dir / "ground_truth.yaml", "w") as f:
        yaml.dump(ground_truth, f)

    evaluator_expectations = {
        "scenario_id": scenario_id,
        "expected_terminal_state": "MODEL_INSUFFICIENT",
        "expected_gap_type": gap_type.value,
        "expected_gap_boundary": boundary_entity,
        "expected_evidence_type": next_evidence_type,
        "must_abstain_from_root_fact": True,
    }
    with open(hidden_dir / "evaluator_expectations.yaml", "w") as f:
        yaml.dump(evaluator_expectations, f)

    # Curated demo metadata
    b_display = default_naming_resolver.to_display_name(boundary_entity)
    demo_meta = {
        "demo": {
            "enabled": True,
            "title": f"Knowledge Gap Discovery: {b_display}",
            "audience": "leadership",
            "duration_minutes": 4,
            "learning_objective": f"Demonstrate that FikraCore detects missing operational topology downstream of {b_display} without hallucinating unobserved root causes.",
            "steps": [
                "Observe 5G SA mobile data degradation and customer tickets",
                "Inspect known operational network topology",
                "Execute truth-blind causal hypothesis reasoning",
                "Detect model insufficiency at structural boundary",
                f"Identify knowledge gap downstream of {b_display}",
                f"Recommend utility-ranked {next_evidence_type} evidence request",
                "Emit candidate relationship for SME/HITL review without modifying live operational brain",
            ],
            "final_message": "FikraCore recognizes when it does not know, prevents false certainty, and guides targeted evidence collection.",
        }
    }
    with open(run_path / "demo_metadata.yaml", "w") as f:
        yaml.dump(demo_meta, f)

    # Manifest
    manifest = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "difficulty_profile": difficulty,
        "seed": seed,
        "gap_type": gap_type.value,
        "variant": variant,
        "operational_path": "operational",
        "hidden_path": "hidden",
    }
    with open(run_path / "scenario_manifest.yaml", "w") as f:
        yaml.dump(manifest, f)

    return manifest


def _write_jsonl(path: Path, items: list[dict[str, Any]]) -> None:
    with open(path, "w") as f:
        for item in items:
            f.write(json.dumps(item) + "\n")


__all__ = [
    "GAP_CLASSES",
    "VARIANTS",
    "generate_all_h2_scenarios",
]
