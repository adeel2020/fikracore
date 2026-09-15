"""Dedicated 40-Scenario Generator for Step 4.4 / H4 Proactive What-If Benchmark.

Generates 40 realistic telecom what-if resilience scenarios across 5 cohorts:
1. Single-Point Failure (10 scenarios: H4-WI-001 to H4-WI-010)
2. Shared / Common-Cause Vulnerabilities (10 scenarios: H4-WI-011 to H4-WI-020)
3. Failover / Capacity Traps (10 scenarios: H4-WI-021 to H4-WI-030)
4. Planned Change / Maintenance Risk (5 scenarios: H4-WI-031 to H4-WI-035)
5. Multi-Failure / Complex Resilience / Unknown (5 scenarios: H4-WI-036 to H4-WI-040)

Enforces strict epistemic hygiene:
- Evaluator ground truth is strictly sequestered in hidden/ground_truth.yaml.
- Operational view contains only validated telecombrain topology.
- Demonstrates zero hallucinated paths and explicit uncertainty handling.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

from ..presentation.naming import default_naming_resolver
from ..presentation.scenario_resolver import get_default_h4_registry


REFERENCE_NETWORK_PATH = (
    Path(__file__).parent / "operator_model" / "reference_synthetic_network.yaml"
)
H4_RUNS_DIR = Path(__file__).parent / "h4_runs"


def generate_all_h4_scenarios(output_dir: Path | str | None = None) -> list[dict[str, Any]]:
    """Generate all 40 H4 scenarios under output_dir."""
    target_dir = Path(output_dir) if output_dir else H4_RUNS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    with open(REFERENCE_NETWORK_PATH, "r", encoding="utf-8") as f:
        network_data = yaml.safe_load(f)

    ref_entities = {e["entity_id"]: e for e in network_data.get("entities", [])}
    ref_relationships = network_data.get("relationships", [])

    registry = get_default_h4_registry()
    scenarios_meta: list[dict[str, Any]] = []

    for idx in range(1, 41):
        sc_id = f"H4-WI-{idx:03d}"
        rec = registry.get(sc_id)
        assert rec, f"Missing scenario record for {sc_id} in registry"

        meta = _generate_single_h4_scenario(
            scenario_id=sc_id,
            index=idx,
            record=rec,
            target_dir=target_dir,
            ref_entities=ref_entities,
            ref_relationships=ref_relationships,
        )
        scenarios_meta.append(meta)

    return scenarios_meta


def _generate_single_h4_scenario(
    scenario_id: str,
    index: int,
    record: Any,
    target_dir: Path,
    ref_entities: dict[str, Any],
    ref_relationships: list[dict[str, Any]],
) -> dict[str, Any]:
    run_dir = target_dir / scenario_id
    run_dir.mkdir(parents=True, exist_ok=True)
    op_dir = run_dir / "operational"
    op_dir.mkdir(parents=True, exist_ok=True)
    hidden_dir = run_dir / "hidden"
    hidden_dir.mkdir(parents=True, exist_ok=True)

    # Determine cohort, trigger, assumptions, redundancy, capacity, and ground truth
    if 1 <= index <= 10:
        cohort = "single_point_failure"
    elif 11 <= index <= 20:
        cohort = "shared_common_cause"
    elif 21 <= index <= 30:
        cohort = "failover_capacity"
    elif 31 <= index <= 35:
        cohort = "change_risk"
    else:
        cohort = "unknown_knowledge" if index == 40 else "multi_failure"

    # Entities and triggers
    if index == 1:
        trigger_canonical = "IP:PE:RTR-07"
        trigger_display = "MPLS Edge Router-07"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = None
        backup_health = "NONE"
        backup_cap = 0
        shared_domain = None
        affected_services = ["5G SA Mobile Data", "Enterprise MPLS VPN"]
        cfs_risk = "SPOF"
    elif index == 2:
        trigger_canonical = "INFRA:DCGW:001"
        trigger_display = "Data Center Gateway-01"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = None
        backup_health = "NONE"
        backup_cap = 0
        shared_domain = None
        affected_services = ["5G SA Mobile Data", "VoNR High Definition Voice"]
        cfs_risk = "SPOF"
    elif index == 3:
        trigger_canonical = "SA5G:UPF:001"
        trigger_display = "User Plane Function-01"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = None
        backup_health = "NONE"
        backup_cap = 0
        shared_domain = None
        affected_services = ["5G SA Mobile Data", "VoNR High Definition Voice"]
        cfs_risk = "SPOF"
    elif index == 4:
        trigger_canonical = "INFRA:DB:SUBS-A"
        trigger_display = "Subscriber Database Cluster-01"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = None
        backup_health = "NONE"
        backup_cap = 0
        shared_domain = None
        affected_services = ["5G SA Mobile Data", "Prepaid Data & Voice Charging"]
        cfs_risk = "SPOF"
    elif index == 5:
        trigger_canonical = "INFRA:FW:PERIM-01"
        trigger_display = "Signaling Perimeter Firewall-01"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = None
        backup_health = "NONE"
        backup_cap = 0
        shared_domain = None
        affected_services = ["5G Roaming Interconnect", "5G SA Mobile Data"]
        cfs_risk = "SPOF"
    elif index == 6:
        trigger_canonical = "INFRA:DNS:CORE"
        trigger_display = "DNS Resolution Server-01"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = None
        backup_health = "NONE"
        backup_cap = 0
        shared_domain = None
        affected_services = ["5G SA Mobile Data", "VoLTE Voice"]
        cfs_risk = "SPOF"
    elif index == 7:
        trigger_canonical = "TRANS:DWDM:01"
        trigger_display = "Optical Transport Node-01"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = None
        backup_health = "NONE"
        backup_cap = 0
        shared_domain = None
        affected_services = ["Inter-DC Backhaul Transport", "5G SA Mobile Data"]
        cfs_risk = "SPOF"
    elif index == 8:
        trigger_canonical = "SA5G:SMF:001"
        trigger_display = "Session Management Function-01"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = None
        backup_health = "NONE"
        backup_cap = 0
        shared_domain = None
        affected_services = ["5G SA Mobile Data", "VoNR High Definition Voice"]
        cfs_risk = "SPOF"
    elif index == 9:
        trigger_canonical = "EPC:DRA:001"
        trigger_display = "Diameter Routing Agent-01"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = None
        backup_health = "NONE"
        backup_cap = 0
        shared_domain = None
        affected_services = ["4G LTE Mobile Data", "VoLTE Voice"]
        cfs_risk = "SPOF"
    elif index == 10:
        trigger_canonical = "CHG:CHF:001"
        trigger_display = "BSS Charging Gateway-01"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = None
        backup_health = "NONE"
        backup_cap = 0
        shared_domain = None
        affected_services = ["Prepaid Data & Voice Charging", "Real-Time Balance Check"]
        cfs_risk = "SPOF"
    # 11 - 20: Shared Common Cause
    elif index == 11:
        trigger_canonical = "IP:PE:RTR-21"
        trigger_display = "Transport Router-21"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = "IP:PE:RTR-22"
        backup_health = "HEALTHY"
        backup_cap = 100
        shared_domain = {"type": "COMMON_POWER", "description": "Dual routers share PDU rack Feed-A in Site DC-A."}
        affected_services = ["5G SA Mobile Data", "Enterprise MPLS VPN"]
        cfs_risk = "COMMON_POWER"
    elif index == 12:
        trigger_canonical = "SA5G:UPF:001"
        trigger_display = "User Plane Function-01"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = "SA5G:UPF:002"
        backup_health = "HEALTHY"
        backup_cap = 100
        shared_domain = {"type": "SHARED_DEPENDENCY", "description": "Primary and secondary UPFs hosted on the same hypervisor blade INFRA:NFVI:A."}
        affected_services = ["5G SA Mobile Data", "VoNR High Definition Voice"]
        cfs_risk = "SHARED_DEPENDENCY"
    elif index == 13:
        trigger_canonical = "TRANS:DWDM:01"
        trigger_display = "Optical Transport Node-01"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = "TRANS:DWDM:02"
        backup_health = "HEALTHY"
        backup_cap = 100
        shared_domain = {"type": "COMMON_TRANSPORT", "description": "Dual diverse transmission routes share the same physical underground conduit."}
        affected_services = ["Inter-DC Backhaul Transport", "5G SA Mobile Data"]
        cfs_risk = "COMMON_TRANSPORT"
    elif index == 14:
        trigger_canonical = "INFRA:FW:PERIM-01"
        trigger_display = "Signaling Perimeter Firewall-01"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = "INFRA:FW:PERIM-02"
        backup_health = "HEALTHY"
        backup_cap = 100
        shared_domain = {"type": "SHARED_DEPENDENCY", "description": "Redundant firewalls connected to single top-of-rack management switch."}
        affected_services = ["5G Roaming Interconnect", "5G SA Mobile Data"]
        cfs_risk = "SHARED_DEPENDENCY"
    elif index == 15:
        trigger_canonical = "SA5G:AMF:001"
        trigger_display = "Access and Mobility Management Function-01"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = "SA5G:AMF:002"
        backup_health = "HEALTHY"
        backup_cap = 100
        shared_domain = {"type": "SHARED_DEPENDENCY", "description": "Both regional AMFs depend on non-replicated subscriber DB cluster."}
        affected_services = ["5G SA Mobile Data", "VoNR High Definition Voice"]
        cfs_risk = "SHARED_DEPENDENCY"
    elif index == 16:
        trigger_canonical = "EPC:DRA:001"
        trigger_display = "Diameter Routing Agent-01"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = "EPC:DRA:002"
        backup_health = "HEALTHY"
        backup_cap = 100
        shared_domain = {"type": "SHARED_DEPENDENCY", "description": "Redundant DRAs sync from single upstream PTP clock."}
        affected_services = ["VoLTE Voice", "Prepaid Data & Voice Charging"]
        cfs_risk = "SHARED_DEPENDENCY"
    elif index == 17:
        trigger_canonical = "TRANS:LEASED:CARRIER-A"
        trigger_display = "Carrier A Transit Gateway"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = "TRANS:LEASED:CARRIER-B"
        backup_health = "HEALTHY"
        backup_cap = 100
        shared_domain = {"type": "SHARED_DEPENDENCY", "description": "Both transit providers share common physical dark fiber span."}
        affected_services = ["5G Roaming Interconnect", "5G SA Mobile Data"]
        cfs_risk = "SHARED_DEPENDENCY"
    elif index == 18:
        trigger_canonical = "IP:PE:RTR-07"
        trigger_display = "MPLS Edge Router-07"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = "IP:PE:RTR-08"
        backup_health = "HEALTHY"
        backup_cap = 100
        shared_domain = {"type": "COMMON_POWER", "description": "Primary and backup routers co-located in POP-07 basement subject to flooding."}
        affected_services = ["5G SA Mobile Data", "Enterprise MPLS VPN"]
        cfs_risk = "COMMON_POWER"
    elif index == 19:
        trigger_canonical = "INFRA:LB:INGRESS-01"
        trigger_display = "Ingress Load Balancer-01"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = "INFRA:LB:INGRESS-02"
        backup_health = "HEALTHY"
        backup_cap = 100
        shared_domain = {"type": "SHARED_DEPENDENCY", "description": "Both LBs announce BGP prefixes through single edge upstream gateway."}
        affected_services = ["5G SA Mobile Data", "Customer Self-Care Portal"]
        cfs_risk = "SHARED_DEPENDENCY"
    elif index == 20:
        trigger_canonical = "SA5G:AUSF:001"
        trigger_display = "Authentication Server Function-01"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = "SA5G:AUSF:002"
        backup_health = "HEALTHY"
        backup_cap = 100
        shared_domain = {"type": "SHARED_DEPENDENCY", "description": "Dual AUSF instances share single hardware security module appliance."}
        affected_services = ["5G SA Mobile Data", "VoNR High Definition Voice"]
        cfs_risk = "SHARED_DEPENDENCY"
    # 21 - 30: Capacity & Failover Traps
    elif index == 21:
        trigger_canonical = "SA5G:UPF:001"
        trigger_display = "User Plane Function-01"
        event_type = "FAILURE"
        load_profile = "PEAK"
        backup_node = "SA5G:UPF:002"
        backup_health = "HEALTHY"
        backup_cap = 70
        shared_domain = None
        affected_services = ["5G SA Mobile Data", "VoNR High Definition Voice"]
        cfs_risk = "CAPACITY_EXHAUSTION"
    elif 22 <= index <= 30:
        trigger_canonical = f"IP:PE:RTR-{index}"
        trigger_display = f"Transport Router-{index}"
        event_type = "FAILURE"
        load_profile = "PEAK"
        backup_node = f"IP:PE:RTR-{index+10}"
        backup_health = "HEALTHY"
        backup_cap = 65
        shared_domain = None
        affected_services = ["5G SA Mobile Data", "Enterprise MPLS VPN"]
        cfs_risk = "CAPACITY_EXHAUSTION"
    # 31 - 35: Planned Change Risk
    elif index == 31:
        trigger_canonical = "IP:PE:RTR-07"
        trigger_display = "MPLS Edge Router-07"
        event_type = "REBOOT"
        load_profile = "NORMAL"
        backup_node = "IP:PE:RTR-08"
        backup_health = "DEGRADED"
        backup_cap = 100
        shared_domain = None
        affected_services = ["5G SA Mobile Data", "Enterprise MPLS VPN"]
        cfs_risk = "UNSAFE_MAINTENANCE"
    elif 32 <= index <= 35:
        trigger_canonical = f"INFRA:SW:CORE-0{index-30}"
        trigger_display = f"Core Switch-0{index-30}"
        event_type = "REBOOT" if index % 2 == 0 else "CONFIG_CHANGE"
        load_profile = "PEAK" if index == 32 else "NORMAL"
        backup_node = f"INFRA:SW:CORE-0{index-25}"
        backup_health = "DEGRADED" if index == 34 else "HEALTHY"
        backup_cap = 100
        shared_domain = None
        affected_services = ["5G SA Mobile Data", "VoNR High Definition Voice"]
        cfs_risk = "UNSAFE_MAINTENANCE"
    # 36 - 39: Multi-Failure Complex Resilience
    elif 36 <= index <= 39:
        trigger_canonical = f"IP:CORE:RTR-0{index-35}"
        trigger_display = f"Core Transport Router-0{index-35}"
        event_type = "FAILURE"
        load_profile = "PEAK"
        backup_node = f"IP:CORE:RTR-1{index-35}"
        backup_health = "DEGRADED"
        backup_cap = 50
        shared_domain = {"type": "SHARED_DEPENDENCY", "description": "Dual core paths severely degraded under simultaneous power and transmission flaps."}
        affected_services = ["5G SA Mobile Data", "Enterprise MPLS VPN"]
        cfs_risk = "SHARED_DEPENDENCY"
    # 40: Unknown Knowledge / Model Insufficiency Cohort
    else:
        trigger_canonical = "EXT:UNMAPPED:RTR-99"
        trigger_display = "Unmapped Edge Router-99"
        event_type = "FAILURE"
        load_profile = "NORMAL"
        backup_node = None
        backup_health = "NONE"
        backup_cap = 0
        shared_domain = None
        affected_services = []
        cfs_risk = "MODEL_INSUFFICIENT"

    # Assemble manifest
    manifest = {
        "what_if_id": scenario_id,
        "title": record.display_name,
        "description": record.description,
        "cohort": cohort,
        "trigger": {
            "canonical_id": trigger_canonical,
            "entity_display_name": trigger_display,
            "event_type": event_type,
            "severity": "CRITICAL",
        },
        "assumptions": {
            "failover_available": backup_node is not None,
            "failover_capacity": "FULL" if backup_cap == 100 else ("LIMITED" if backup_cap > 0 else "NONE"),
            "duration_minutes": 30,
            "traffic_load_profile": load_profile,
        },
        "failure_domain_tags": record.tags,
    }
    with open(run_dir / "scenario_manifest.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, indent=2, sort_keys=False)

    # Operational topology
    if cohort == "unknown_knowledge":
        op_topo = {
            "view_id": f"TOPO-{scenario_id}",
            "scenario_id": scenario_id,
            "visible_entities": [],
            "relationships": [],
            "known_gaps": ["unmodeled_boundary", "missing_upstream_topology"],
        }
    else:
        # Build visible subgraph
        vis_ents = [trigger_canonical]
        if backup_node:
            vis_ents.append(backup_node)
        # Add downstream dependents
        vis_rels = []
        for r in ref_relationships:
            src = r.get("source_entity", "")
            tgt = r.get("target_entity", "")
            if tgt == trigger_canonical or src == trigger_canonical:
                vis_rels.append(r)
                if src not in vis_ents:
                    vis_ents.append(src)
                if tgt not in vis_ents:
                    vis_ents.append(tgt)

        op_topo = {
            "view_id": f"TOPO-{scenario_id}",
            "scenario_id": scenario_id,
            "visible_entities": vis_ents,
            "relationships": vis_rels,
            "known_gaps": [],
        }

    with open(op_dir / "topology_view.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(op_topo, f, indent=2, sort_keys=False)

    # Redundancy and Capacity
    redundancy_data = {
        "failover_pairs": {
            trigger_canonical: {
                "backup_entity": backup_node,
                "backup_health": backup_health,
            }
        } if backup_node else {},
        "shared_failure_domains": [shared_domain] if shared_domain else [],
        "backup_node": backup_node,
        "backup_health": backup_health,
    }
    with open(op_dir / "redundancy_data.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(redundancy_data, f, indent=2, sort_keys=False)

    capacity_data = {
        "backup_capacity_pct": backup_cap,
        "load_profile": load_profile,
    }
    with open(op_dir / "capacity_data.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(capacity_data, f, indent=2, sort_keys=False)

    # Evaluator-only Ground Truth
    ground_truth = {
        "scenario_id": scenario_id,
        "cohort": cohort,
        "trigger_entity": trigger_canonical,
        "true_affected_services": affected_services,
        "true_cfs_risk": cfs_risk,
        "true_common_cause_detected": shared_domain is not None,
        "true_capacity_bottleneck": backup_cap < 100 and load_profile == "PEAK",
        "true_change_risk": event_type in ("REBOOT", "CONFIG_CHANGE") and (backup_health != "HEALTHY" or load_profile == "PEAK"),
        "is_model_insufficient": cohort == "unknown_knowledge",
    }
    with open(hidden_dir / "ground_truth.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(ground_truth, f, indent=2, sort_keys=False)

    # Demo metadata
    demo_meta = {
        "demo": {
            "enabled": record.demo_enabled,
            "title": record.display_name,
            "audience": "leadership",
            "duration_minutes": 4,
            "steps": [
                "Select Failure",
                "Propagate Impact",
                "Show Blast Radius",
                "Reveal Shared Dependency",
                "Compare Mitigations",
                "Recommend Resilience Action",
                "Executive Summary",
            ],
            "final_message": "FikraCore uses validated operational knowledge to identify risk before failure occurs.",
        }
    }
    with open(run_dir / "demo_metadata.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(demo_meta, f, indent=2, sort_keys=False)

    return manifest
