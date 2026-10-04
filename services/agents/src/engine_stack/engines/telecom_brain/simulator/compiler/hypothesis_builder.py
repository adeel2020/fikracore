from datetime import datetime, timedelta, timezone
import json
from typing import Any, Optional, Callable
from pathlib import Path

# Hypothesis ranking templates for each causal cohort (4 ranks: Leading → Rejected)
COHORT_HYPOTHESIS_TEMPLATES: list[dict[str, Any]] = [
    {
        "rank": 1,
        "status": "LEADING",
        "supports_template": [
            "{trigger_name} failure precedes service impact",
            "Blast radius consistent with single point of failure",
            "Temporal correlation confirmed",
        ],
        "against_template": [
            "No redundant path verification yet",
        ],
        "missing_template": [
            "Detailed {trigger_name} health metrics",
        ],
    },
    {
        "rank": 2,
        "status": "COMPETING",
        "confidence_base": 25.0,
        "supports_template": [
            "Symptom pattern matches secondary cause",
        ],
        "against_template": [
            "Primary evidence points to {trigger_name}",
        ],
        "missing_template": [],
    },
    {
        "rank": 3,
        "status": "COMPETING",
        "confidence_base": 12.0,
        "supports_template": [
            "Latency pattern correlation",
        ],
        "against_template": [
            "Insufficient evidence for alternative",
        ],
        "missing_template": [],
    },
    {
        "rank": 4,
        "status": "REJECTED",
        "confidence_base": 3.0,
        "supports_template": [],
        "against_template": [
            "Contradicted by observed evidence",
        ],
        "missing_template": [],
    },
]


def build_hypotheses(
    scenario_id: str,
    run_id: str,
    trigger_display: str,
    trigger_entity: str,
    affected_service: str,
    cohort: str,
    tested_hypotheses: list[str],
    stage_vals: dict[str, Any],
    stage_index: int,
    is_confirmed: bool,
    evidence_count: int = 0,
 *, _generate_hypothesis_names: Callable) -> list[dict[str, Any]]:
    """Build scenario-specific hypotheses with stage-aware ranking and Oracle Isolation guard."""
    if stage_index < 2:
        return []
    hypotheses = []
    hyp_names = _generate_hypothesis_names(trigger_display, cohort, scenario_id, affected_service)
    service_id = affected_service.lower().replace(" ", "-")
    path_specs = [
        {
            "entity_ids": [trigger_entity, service_id, "enterprise-users"],
            "edge_ids": ["EDGE-HYP-001-0", "EDGE-HYP-001-1"],
            "role": "CONFIRMED" if is_confirmed else ("LEADING" if stage_index >= 4 and evidence_count >= 3 else "CANDIDATE"),
            "last_reason": f"{trigger_display} failure precedes downstream service degradation",
        },
        {
            "entity_ids": [service_id, "enterprise-users"],
            "edge_ids": ["EDGE-HYP-002-0"],
            "role": "WEAKENING" if stage_index >= 5 and evidence_count >= 3 else "CANDIDATE",
            "last_reason": f"{affected_service} overload explains symptoms but not initial telemetry alarm",
        },
        {
            "entity_ids": ["dns-resolution", service_id],
            "edge_ids": ["EDGE-HYP-003-0"],
            "role": "WEAKENING" if stage_index >= 5 and evidence_count >= 3 else "CANDIDATE",
            "last_reason": "Cross-domain protocol latency remains unverified by direct alarms",
        },
        {
            "entity_ids": ["ran-access", service_id],
            "edge_ids": ["EDGE-HYP-004-0"],
            "role": "REJECTED" if stage_index >= 5 and evidence_count >= 3 else "CANDIDATE",
            "last_reason": "Access domain cause conflicts with core/transport temporal order",
        },
    ]
    confidence_by_stage = {
        3: [None, None, None, None],
        4: [61.0, 33.0, 18.0, 8.0],
        5: [68.0, 28.0, 12.0, 4.0],
        6: [74.0, 22.0, 9.0, 2.0],
        7: [94.2, 12.0, 4.0, 1.0],
    }
    confidences = confidence_by_stage.get(min(stage_index, 7), confidence_by_stage[3])
    previous_by_stage = {
        3: [None, None, None, None],
        4: [47.0, 26.0, 15.0, 10.0],
        5: [61.0, 33.0, 18.0, 8.0],
        6: [68.0, 28.0, 12.0, 4.0],
        7: [74.0, 22.0, 9.0, 2.0],
    }
    previous = previous_by_stage.get(min(stage_index, 7), previous_by_stage[3])

    rank_titles = [
        "Leading Root Cause",
        "Competing Candidate",
        "Plausible Candidate",
        "Rejected Candidate",
    ]

    for i, tmpl in enumerate(COHORT_HYPOTHESIS_TEMPLATES):
        hyp_id = f"HYP-{i + 1:03d}"
        name = hyp_names[i] if i < len(hyp_names) else f"Alternative Cause {i + 1}"
        tested = hyp_id in tested_hypotheses
        # Oracle Guard (R8): Cannot rank hypotheses or fabricate confidence without evidence
        should_rank = stage_index >= 4 and evidence_count >= 3
        confidence = confidences[i] if should_rank else None
        prior = previous[i] if should_rank else None
        delta_value = None if confidence is None or prior is None else round(confidence - prior, 1)
        status = tmpl["status"] if (should_rank and i > 0) else ("LEADING" if should_rank else "CANDIDATE")
        if should_rank and i == 0 and is_confirmed:
            status = "LEADING"
            lifecycle_state = "CONFIRMED"
            confidence_state = "CONFIRMED"
        elif should_rank and i == 0 and stage_index >= 5 and not is_confirmed:
            lifecycle_state = "NEEDS_MORE_EVIDENCE"
            confidence_state = "ROOT_CANDIDATE"
        elif should_rank and i == 0:
            lifecycle_state = "TESTING"
            confidence_state = "RANKED"
        elif should_rank and i == 3 and stage_index >= 5:
            lifecycle_state = "REJECTED"
            confidence_state = "REJECTED"
        elif should_rank and i > 0:
            lifecycle_state = "WEAKENING" if stage_index >= 5 else "TESTING"
            confidence_state = "RANKED"
        else:
            lifecycle_state = "CANDIDATE"
            confidence_state = "UNRANKED"
        path_spec = path_specs[i]
        evidence_ids = [f"EVT-{scenario_id.upper()}-{stage_index}-{idx}" for idx in range(min(max(stage_index, 1), 4))]
        history = []
        if should_rank:
            history.append({
                "hypothesis_id": hyp_id,
                "previous": prior,
                "new": confidence,
                "delta": delta_value,
                "reason": path_spec["last_reason"],
                "evidence_ids": evidence_ids[:2],
                "sequence": stage_index * 10 + i,
                "timestamp": (datetime.now(timezone.utc) - timedelta(seconds=(4 - i) * 9)).isoformat(),
            })

        hypotheses.append({
            "id": hyp_id,
            "hypothesis_id": hyp_id,
            "display_id": f"H{i + 1}",
            "rank_label": f"Rank #{i + 1} · {rank_titles[i]}",
            "label": name,
            "rank": tmpl["rank"] if should_rank else None,
            "display_name": name,
            "confidence": confidence,
            "confidence_state": confidence_state,
            "delta": f"{delta_value:+.1f}%" if delta_value is not None else "Unranked",
            "last_delta": delta_value,
            "last_delta_reason": path_spec["last_reason"] if should_rank else "Awaiting enough correlated evidence to rank",
            "status": status,
            "lifecycle_state": lifecycle_state,
            "supports": [s.format(trigger_name=trigger_display) for s in tmpl.get("supports_template", [])],
            "against": [a.format(trigger_name=trigger_display) for a in tmpl.get("against_template", [])],
            "missing": [m.format(trigger_name=trigger_display) for m in tmpl.get("missing_template", [])],
            "support_count": max(0, 4 - i) if should_rank else 0,
            "contradiction_count": i if should_rank else 0,
            "missing_evidence_count": len(tmpl.get("missing_template", [])),
            "evidence_count": len(evidence_ids) if should_rank else 0,
            "evidence_ids": evidence_ids if should_rank else [],
            "path_entity_ids": path_spec["entity_ids"],
            "path_edge_ids": path_spec["edge_ids"],
            "path_role": path_spec["role"],
            "frontier_ids": [f"FR-{scenario_id}-001"] if i == 0 and stage_index >= 5 and not is_confirmed else [],
            "confidence_history": history,
            "tested": tested,
            "scenario_id": scenario_id,
            "run_id": run_id,
        })

    return hypotheses



def generate_hypothesis_names(
    
    trigger_display: str,
    cohort: str,
    scenario_id: str = "",
    affected_service: str = "",
) -> list[str]:
    """Generate scenario-specific candidate hypothesis names tailored to the failure mode."""
    sc_id = (scenario_id or "").upper().strip()
    sc_service = affected_service or "Data Services"

    # Check for curated scenario-specific hypothesis quadruplets
    if "SCN-001" in sc_id or "DEMO-001" in sc_id or "TWIN-INC-001" in sc_id:
        return [
            "SGi Transport MTU Blackhole & Packet Fragmentation",
            "PE Router N3 Transport Interface Saturation",
            "UPF User Plane Session Control Buffer Exhaustion",
            "DNS Resolution Timeout & Latency Surge",
        ]
    elif "H2-GAP-001" in sc_id or "TWIN-GAP-001" in sc_id:
        return [
            "Unmodeled OCS Diameter Gy/Ro Charging Gateway Timeout",
            "PCRF Subscriber Policy Rule Sync Mismatch",
            "PGW-C Control Plane Queue Saturation",
            "SGi Interface MTU Mismatch",
        ]
    elif "H3-LRN-001" in sc_id or "TWIN-LRN-001" in sc_id:
        return [
            "Promoted OCS Charging Path Credit Control Delay",
            "UPF GTP-U Protocol Tunnel Deterioration",
            "AMF Subscriber Authentication Failure",
            "Transport Backbone Core Link Loss",
        ]
    elif "H4-WI-001" in sc_id or "TWIN-WIF-001" in sc_id:
        return [
            "MPLS Edge Router Shared Power Feed Loss",
            "Downstream BGP Route Blackholing",
            "Core IP Transmission Fiber Cut",
            "RAN Access Transport Link Drop",
        ]
    elif "H4-WI-002" in sc_id or "TWIN-WIF-002" in sc_id:
        return [
            "Primary Data Center Gateway Spine Switch Fabric Outage",
            "Virtual Router EVPN VXLAN Overlay Drop",
            "Core Cloud NFVI Hypervisor Saturation",
            "IMS SIP Proxy Session Spike",
        ]
    elif "H4-WI-003" in sc_id or "TWIN-WIF-003" in sc_id:
        return [
            "PGW-U User Plane Forwarding Process Collapse",
            "N4 Interface PFCP Control Association Loss",
            "SGi-LAN Firewall Session Exhaustion",
            "gNodeB RAN User Plane Congestion",
        ]
    elif "H4-WI-011" in sc_id or "TWIN-WIF-011" in sc_id:
        return [
            "Dual Router Shared Power Feed Rack Outage",
            "Optical Line Terminal (OLT) Laser Degradation",
            "Core BGP Peering Memory Leak",
            "Subscriber AAA Server Timeout",
        ]

    # Dynamic fallback based on trigger entity & affected service
    short_name = trigger_display.split("-")[0] if "-" in trigger_display else trigger_display
    return [
        f"{trigger_display} Primary Failure",
        f"Downstream {sc_service} Capacity Overload",
        "Cross-Domain Interconnect Boundary Protocol Latency",
        "RAN Radio Access Sector Congestion",
    ]


