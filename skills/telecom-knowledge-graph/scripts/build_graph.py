#!/usr/bin/env python3
"""FikraCore Live Telecom Knowledge Graph Builder & Scenario Projection Engine.

Ingests the complete FikraCore ontology (132 entities, 190 relationships) mapped into
11 granular telecom operational domains with visual domain boundary demarcations
(soft clusters, dashed demarcation rings, and domain headers).
Features live domain node stickiness, domain center gravitational anchor physics,
collapsible left/right panels for full visualization real-estate, and dynamic scenario
projections (Baseline, H1 SGi MTU, H2 LTE Attach, H3 Voice Call Setup, H4 UE Storm, H5 Power)
with discrete 3GPP alarm states and animated causal blast-radius particles.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys

# 11 Granular Telecom Operational Domains with vivid carrier palette
DOMAIN_COLORS = {
    "Mobile Core (5G SA)": "#3b82f6",             # Primary Blue
    "Radio Access Network (RAN)": "#10b981",       # Emerald Green
    "IP Transport & Routing": "#f59e0b",           # Amber
    "Optical & Transport (DWDM/OTN)": "#14b8a6",   # Teal
    "4G EPC & Signaling": "#6366f1",               # Indigo
    "IMS & VoNR/VoLTE": "#ec4899",                 # Pink
    "Cloud NFVI & Facilities": "#8b5cf6",          # Purple
    "CRM & Customer Experience": "#ef4444",        # Rose / Red
    "OSS & Fault Management": "#06b6d4",           # Cyan
    "OCS & Charging": "#eab308",                   # Yellow
    "External Interconnect & Roaming": "#f97316",   # Orange
}

# Domain Cluster Anchors (Centers of Gravity in 2D space)
DOMAIN_CENTERS = {
    "Mobile Core (5G SA)": {"x": 0, "y": 0},
    "Radio Access Network (RAN)": {"x": -420, "y": -200},
    "IP Transport & Routing": {"x": -380, "y": 180},
    "Optical & Transport (DWDM/OTN)": {"x": -560, "y": -20},
    "4G EPC & Signaling": {"x": -180, "y": -320},
    "IMS & VoNR/VoLTE": {"x": 200, "y": -320},
    "Cloud NFVI & Facilities": {"x": -180, "y": 340},
    "CRM & Customer Experience": {"x": 200, "y": 340},
    "OSS & Fault Management": {"x": 460, "y": 0},
    "OCS & Charging": {"x": 0, "y": 380},
    "External Interconnect & Roaming": {"x": -580, "y": 240},
}

# Pre-compiled scenario catalog mapped directly to inventory slugs
SCENARIOS_CATALOG = [
    {
        "id": "baseline",
        "name": "Baseline Nominal State",
        "badge": "NOMINAL",
        "category": "Steady State",
        "description": "Steady-state carrier operations. All 132 entities nominal with zero active alarm delegations.",
        "root_cause": None,
        "affected_nodes": {},
        "active_links": []
    },
    {
        "id": "h1-sgi-mtu",
        "name": "Incident H1: SGi Throughput Degradation (MTU Mismatch)",
        "badge": "CRITICAL",
        "category": "Inter-Domain Incident",
        "description": "MTU mismatch and packet fragmentation on sgi-edge-01 propagates to UPF/PGW throughput drop, NAT session exhaustion, and customer ticket surge.",
        "root_cause": "domains/transport/functions/sgi-edge-01",
        "propagation_path": [
            "domains/transport/functions/sgi-edge-01",
            "domains/mobile-core/networks/ps/functions/nat-fw-01",
            "domains/mobile-core/networks/ps/functions/pgw-01",
            "domains/mobile-core/networks/ps/service-procedures/sgi-data-forwarding",
            "mobile-core/services/sgi-data",
            "incidents/mobile-core/sgi-data-a154bb7a3997859c"
        ],
        "affected_nodes": {
            "domains/transport/functions/sgi-edge-01": {"severity": "ROOT_CAUSE", "status": "MTU Mismatch / Buffer Overrun"},
            "mobile-core/network-functions/transport-sgi-edge-01": {"severity": "ROOT_CAUSE", "status": "MTU Mismatch / Buffer Overrun"},
            "domains/mobile-core/networks/ps/functions/nat-fw-01": {"severity": "MAJOR", "status": "NAT Session Exhaustion"},
            "mobile-core/network-functions/gi-lan-nat-fw-01": {"severity": "MAJOR", "status": "NAT Session Exhaustion"},
            "domains/mobile-core/networks/ps/functions/pgw-01": {"severity": "CRITICAL", "status": "PDU Session Rate Drop / Packet Discard"},
            "mobile-core/network-functions/mobile-core-user-plane-pgw-01": {"severity": "CRITICAL", "status": "PDU Session Rate Drop / Packet Discard"},
            "mobile-core/services/sgi-data": {"severity": "CRITICAL", "status": "SLA Throughput Threshold Breached"},
            "domains/mobile-core/networks/ps/service-procedures/sgi-data-forwarding": {"severity": "CRITICAL", "status": "Forwarding Stalled"},
            "incidents/mobile-core/sgi-data-a154bb7a3997859c": {"severity": "CRITICAL", "status": "Active Triage Incident"},
            "mobile-core/incidents/sgi-data-a154bb7a3997859c": {"severity": "CRITICAL", "status": "Active Triage Incident"},
            "correlation/mobile-core/clusters/a154bb7a3997859c": {"severity": "MAJOR", "status": "Correlation Cluster Formed"},
            "correlation/mobile-core/hypotheses/a154bb7a3997859c": {"severity": "MAJOR", "status": "Hypothesis Validated"},
            "mobile-core/hypotheses/correlation-a154bb7a3997859c": {"severity": "MAJOR", "status": "Hypothesis Validated"},
            "correlation/mobile-core/decisions/a154bb7a3997859c": {"severity": "MINOR", "status": "Mitigation Decision Pending"},
            "grafana/alerts/grafana-alert-sgi-transport-001": {"severity": "MAJOR", "status": "INTERFACE_DISCARDS_HIGH"},
            "grafana/alerts/grafana-alert-sgi-gilan-001": {"severity": "MAJOR", "status": "NAT_SESSION_TABLE_HIGH"},
            "grafana/alerts/grafana-alert-sgi-pgw-001": {"severity": "CRITICAL", "status": "SGI_THROUGHPUT_DROP"},
            "grafana/metrics/grafana-prom-sgi-001": {"severity": "CRITICAL", "status": "Throughput < Committed Intent"},
            "grafana/logs/grafana-loki-sgi-001": {"severity": "MINOR", "status": "NAT allocation warning logs"},
            "grafana/traces/grafana-tempo-sgi-001": {"severity": "MINOR", "status": "PGW latency spike trace"},
            "incidents/mobile-core/kpi-events/grafana-prom-sgi-001": {"severity": "CRITICAL", "status": "Throughput Breach Event"},
            "mobile-core/kpi-events/grafana-prom-sgi-001": {"severity": "CRITICAL", "status": "Throughput Breach Event"},
            "knowledge/mobile-core/kpis/sgi-throughput": {"severity": "CRITICAL", "status": "KPI Degraded"},
            "mobile-core/kpis/sgi-throughput": {"severity": "CRITICAL", "status": "KPI Degraded"},
            "assets/mobile-core/playbooks/sgi-data-failure-triage": {"severity": "MINOR", "status": "Playbook Invoked"},
            "learning/mobile-core/notes/sgi-data-a154bb7a3997859c": {"severity": "MINOR", "status": "Learning Note Linked"},
            "storytelling/mobile-core/stories/sgi-data-a154bb7a3997859c": {"severity": "MINOR", "status": "Incident Story Generated"}
        }
    },
    {
        "id": "h2-lte-attach",
        "name": "Incident H2: LTE Attach Failure & Diameter Stalling",
        "badge": "CRITICAL",
        "category": "Cross-Domain Signaling",
        "description": "HSS Diameter authentication timeout cascaded across MME-01 and eNodeB-17, resulting in complete 4G LTE attach failure spikes.",
        "root_cause": "domains/mobile-core/networks/lte/functions/hss-01",
        "propagation_path": [
            "domains/mobile-core/networks/lte/functions/hss-01",
            "domains/mobile-core/networks/lte/functions/mme-01",
            "domains/ran/functions/enodeb-17",
            "domains/mobile-core/networks/lte/service-procedures/lte-attach",
            "mobile-core/services/lte-attach",
            "incidents/mobile-core/lte-attach-54db6ef325fbf758"
        ],
        "affected_nodes": {
            "domains/mobile-core/networks/lte/functions/hss-01": {"severity": "ROOT_CAUSE", "status": "HSS Diameter Authentication Stalled"},
            "mobile-core/network-functions/signaling-hss-01": {"severity": "ROOT_CAUSE", "status": "HSS Diameter Authentication Stalled"},
            "domains/mobile-core/networks/lte/functions/mme-01": {"severity": "CRITICAL", "status": "MME S1-AP Procedure Timeout"},
            "mobile-core/network-functions/mobile-core-control-plane-mme-01": {"severity": "CRITICAL", "status": "MME S1-AP Procedure Timeout"},
            "domains/ran/functions/enodeb-17": {"severity": "MAJOR", "status": "eNodeB RRC Rejection Surge"},
            "mobile-core/network-functions/ran-enodeb-17": {"severity": "MAJOR", "status": "eNodeB RRC Rejection Surge"},
            "mobile-core/services/lte-attach": {"severity": "CRITICAL", "status": "Attach Success Rate Dropped"},
            "domains/mobile-core/networks/lte/service-procedures/lte-attach": {"severity": "CRITICAL", "status": "Procedure Failed"},
            "incidents/mobile-core/lte-attach-54db6ef325fbf758": {"severity": "CRITICAL", "status": "Active Inter-Domain Incident"},
            "mobile-core/incidents/lte-attach-54db6ef325fbf758": {"severity": "CRITICAL", "status": "Active Inter-Domain Incident"},
            "correlation/mobile-core/clusters/54db6ef325fbf758": {"severity": "MAJOR", "status": "Correlation Cluster Formed"},
            "correlation/mobile-core/hypotheses/54db6ef325fbf758": {"severity": "MAJOR", "status": "Hypothesis Validated"},
            "mobile-core/hypotheses/correlation-54db6ef325fbf758": {"severity": "MAJOR", "status": "Hypothesis Validated"},
            "correlation/mobile-core/decisions/54db6ef325fbf758": {"severity": "MINOR", "status": "Decision Generated"},
            "grafana/alerts/grafana-alert-attach-hss-001": {"severity": "CRITICAL", "status": "DIAMETER_AUTH_TIMEOUT"},
            "grafana/alerts/grafana-alert-attach-mme-001": {"severity": "MAJOR", "status": "MME_ATTACH_DROP"},
            "grafana/alerts/grafana-alert-attach-ran-001": {"severity": "MAJOR", "status": "RAN_RRC_FAIL_HIGH"},
            "grafana/metrics/grafana-prom-attach-001": {"severity": "CRITICAL", "status": "Attach Rate < 70%"},
            "grafana/logs/grafana-loki-attach-001": {"severity": "MINOR", "status": "Diameter 3004 error logs"},
            "incidents/mobile-core/kpi-events/grafana-prom-attach-001": {"severity": "CRITICAL", "status": "KPI Event Triggered"},
            "mobile-core/kpi-events/grafana-prom-attach-001": {"severity": "CRITICAL", "status": "KPI Event Triggered"},
            "assets/mobile-core/playbooks/lte-attach-failure-triage": {"severity": "MINOR", "status": "Playbook Invoked"},
            "learning/mobile-core/notes/lte-attach-54db6ef325fbf758": {"severity": "MINOR", "status": "Learning Note Linked"},
            "storytelling/mobile-core/stories/lte-attach-54db6ef325fbf758": {"severity": "MINOR", "status": "Story Created"}
        }
    },
    {
        "id": "h3-voice-cssr",
        "name": "Incident H3: Voice Call Setup Failure & Backhaul Jitter",
        "badge": "MAJOR",
        "category": "VoNR / IMS Multi-Domain",
        "description": "Transport voice-backhaul-01 jitter and packet drops impair P-CSCF SIP INVITE handshakes and eNodeB-22 call accessibility (CSSR drop).",
        "root_cause": "domains/transport/functions/voice-backhaul-01",
        "propagation_path": [
            "domains/transport/functions/voice-backhaul-01",
            "domains/mobile-core/networks/ims/functions/pcscf-01",
            "domains/ran/functions/enodeb-22",
            "domains/mobile-core/networks/ims/service-procedures/voice-call-setup",
            "mobile-core/services/voice-call-setup",
            "incidents/mobile-core/voice-call-setup-05841af2e3f4f430"
        ],
        "affected_nodes": {
            "domains/transport/functions/voice-backhaul-01": {"severity": "ROOT_CAUSE", "status": "Backhaul Fiber Jitter & Discard"},
            "mobile-core/network-functions/transport-voice-backhaul-01": {"severity": "ROOT_CAUSE", "status": "Backhaul Fiber Jitter & Discard"},
            "domains/mobile-core/networks/ims/functions/pcscf-01": {"severity": "MAJOR", "status": "SIP INVITE 408 Request Timeout"},
            "mobile-core/network-functions/ims-pcscf-01": {"severity": "MAJOR", "status": "SIP INVITE 408 Request Timeout"},
            "domains/ran/functions/enodeb-22": {"severity": "MAJOR", "status": "Voice Dedicated Bearer Setup Failed"},
            "mobile-core/network-functions/ran-enodeb-22": {"severity": "MAJOR", "status": "Voice Dedicated Bearer Setup Failed"},
            "mobile-core/services/voice-call-setup": {"severity": "MAJOR", "status": "Call Setup Success Rate (CSSR) Breached"},
            "domains/mobile-core/networks/ims/service-procedures/voice-call-setup": {"severity": "MAJOR", "status": "SIP Procedure Degraded"},
            "incidents/mobile-core/voice-call-setup-05841af2e3f4f430": {"severity": "MAJOR", "status": "Active Inter-Domain Incident"},
            "mobile-core/incidents/voice-call-setup-05841af2e3f4f430": {"severity": "MAJOR", "status": "Active Inter-Domain Incident"},
            "correlation/mobile-core/clusters/05841af2e3f4f430": {"severity": "MAJOR", "status": "Correlation Cluster Formed"},
            "correlation/mobile-core/hypotheses/05841af2e3f4f430": {"severity": "MAJOR", "status": "Hypothesis Validated"},
            "mobile-core/hypotheses/correlation-05841af2e3f4f430": {"severity": "MAJOR", "status": "Hypothesis Validated"},
            "correlation/mobile-core/decisions/05841af2e3f4f430": {"severity": "MINOR", "status": "Remediation Candidate Active"},
            "grafana/alerts/grafana-alert-cssr-transport-001": {"severity": "MAJOR", "status": "BACKHAUL_JITTER_HIGH"},
            "grafana/alerts/grafana-alert-cssr-ims-001": {"severity": "MAJOR", "status": "SIP_TRANSACTION_TIMEOUT"},
            "grafana/alerts/grafana-alert-cssr-ran-001": {"severity": "MAJOR", "status": "BEARER_SETUP_FAILURE"},
            "grafana/metrics/grafana-prom-cssr-001": {"severity": "MAJOR", "status": "CSSR < 95%"},
            "grafana/logs/grafana-loki-cssr-001": {"severity": "MINOR", "status": "SIP 504 Gateway Timeout logs"},
            "incidents/mobile-core/kpi-events/grafana-prom-cssr-001": {"severity": "MAJOR", "status": "CSSR Drop Event Triggered"},
            "mobile-core/kpi-events/grafana-prom-cssr-001": {"severity": "MAJOR", "status": "CSSR Drop Event Triggered"},
            "assets/mobile-core/playbooks/voice-call-setup-failure-triage": {"severity": "MINOR", "status": "Playbook Triggered"},
            "learning/mobile-core/notes/voice-call-setup-05841af2e3f4f430": {"severity": "MINOR", "status": "Learning Note Linked"},
            "storytelling/mobile-core/stories/voice-call-setup-05841af2e3f4f430": {"severity": "MINOR", "status": "Story Created"}
        }
    },
    {
        "id": "h4-ue-registration",
        "name": "Incident H4: 5G UE Registration Burst & AMF Overload",
        "badge": "MAJOR",
        "category": "5G SA Signaling",
        "description": "Mass 5G registration storm across transport aggregation switch agg-sw-03 and gNodeB-17 causes AMF-01 CPU saturation and registration failures.",
        "root_cause": "mobile-core/network-functions/transport-transport-agg-sw-03",
        "propagation_path": [
            "mobile-core/network-functions/transport-transport-agg-sw-03",
            "mobile-core/network-functions/ran-ran-gnodeb-17",
            "mobile-core/network-functions/mobile-core-core-amf-01",
            "mobile-core/services/ue-registration",
            "mobile-core/incidents/ue-registration-1fe005ed908a3f26"
        ],
        "affected_nodes": {
            "mobile-core/network-functions/transport-transport-agg-sw-03": {"severity": "ROOT_CAUSE", "status": "Queue Drop / Micro-burst Overrun"},
            "mobile-core/network-functions/ran-ran-gnodeb-17": {"severity": "MAJOR", "status": "NGAP Association Instability"},
            "mobile-core/network-functions/mobile-core-core-amf-01": {"severity": "CRITICAL", "status": "AMF-01 CPU Saturation & Drop"},
            "mobile-core/services/ue-registration": {"severity": "CRITICAL", "status": "Registration Success Rate Drop"},
            "mobile-core/incidents/ue-registration-1fe005ed908a3f26": {"severity": "CRITICAL", "status": "Active Inter-Domain Incident"},
            "mobile-core/hypotheses/correlation-1fe005ed908a3f26": {"severity": "MAJOR", "status": "AMF Signaling Storm Correlated"},
            "mobile-core/evidence/alarm-1fe005ed908a3f26-0": {"severity": "CRITICAL", "status": "AMF_CPU_OVERLOAD"},
            "mobile-core/evidence/alarm-1fe005ed908a3f26-1": {"severity": "MAJOR", "status": "NGAP_COMM_LOSS"},
            "mobile-core/evidence/alarm-1fe005ed908a3f26-2": {"severity": "MAJOR", "status": "SWITCH_BUFFER_OVERFLOW"},
            "mobile-core/evidence/kpi-1fe005ed908a3f26-0": {"severity": "CRITICAL", "status": "Registration Latency Exceeded"},
            "mobile-core/evidence/ticket-1fe005ed908a3f26-1": {"severity": "MAJOR", "status": "Customer Trouble Ticket Surging"},
            "mobile-core/kpi-events/kpi-registration-001": {"severity": "CRITICAL", "status": "Registration Success Rate Degraded"}
        }
    },
    {
        "id": "h5-site-power",
        "name": "Incident H5: Physical Site Power & UPS Battery Alarm",
        "badge": "MINOR",
        "category": "Facilities / Infrastructure",
        "description": "DC power rectifier and UPS-77 failure causing power bus fluctuation, impacting site stability and operational telemetry.",
        "root_cause": "mobile-core/network-functions/power-power-ups-77",
        "propagation_path": [
            "mobile-core/network-functions/power-power-ups-77",
            "mobile-core/evidence/alarm-81cec920e94d3a59-0",
            "mobile-core/hypotheses/correlation-81cec920e94d3a59",
            "mobile-core/services/site-power",
            "mobile-core/incidents/site-power-81cec920e94d3a59"
        ],
        "affected_nodes": {
            "mobile-core/network-functions/power-power-ups-77": {"severity": "ROOT_CAUSE", "status": "DC Rectifier Trip / Battery Discharge"},
            "mobile-core/services/site-power": {"severity": "MAJOR", "status": "Redundant Power Feeder Lost"},
            "mobile-core/incidents/site-power-81cec920e94d3a59": {"severity": "MAJOR", "status": "Site Power Facility Incident"},
            "mobile-core/hypotheses/correlation-81cec920e94d3a59": {"severity": "MINOR", "status": "Hypothesis Generated"},
            "mobile-core/evidence/alarm-81cec920e94d3a59-0": {"severity": "MAJOR", "status": "UPS_ON_BATTERY_CRITICAL"}
        }
    }
]


def map_telecom_domain(e: dict) -> str:
    """Maps an entity into one of the 11 granular telecom operational domains."""
    slug = e.get("slug", "").lower()
    etype = e.get("type", "").lower()
    orig_dom = e.get("domain", "")

    # 1. Optical / Backhaul Transport
    if "dwdm" in slug or "optical" in slug or "otn" in slug or "voice-backhaul" in slug:
        return "Optical & Transport (DWDM/OTN)"
    # 2. IP Transport & Routing
    if orig_dom == "Transport" or "transport" in slug or "sgi-edge" in slug or "agg-sw" in slug or "router" in slug:
        return "IP Transport & Routing"
    # 3. Cloud NFVI & Facilities
    if "power" in slug or "ups" in slug or "nfvi" in slug or "k8s" in slug or "facility" in slug or "rectifier" in slug:
        return "Cloud NFVI & Facilities"
    # 4. CRM & Customer Experience
    if "ticket" in slug or "tt-" in slug or "crm" in slug or "customer" in slug or etype == "ticket-journey":
        return "CRM & Customer Experience"
    # 5. Radio Access Network (RAN)
    if orig_dom == "RAN" or "/ran/" in slug or "ran-" in slug or "enodeb" in slug or "gnodeb" in slug or "rrc" in slug:
        return "Radio Access Network (RAN)"
    # 6. OCS & Charging
    if "ocs" in slug or "chf" in slug or "charging" in slug:
        return "OCS & Charging"
    # 7. External Interconnect & Roaming
    if "roaming" in slug or "sepp" in slug or "ipx" in slug:
        return "External Interconnect & Roaming"
    # 8. IMS & VoNR/VoLTE
    if "ims" in slug or "pcscf" in slug or "scscf" in slug or "voice" in slug or "sip" in slug:
        return "IMS & VoNR/VoLTE"
    # 9. 4G EPC & Signaling
    if "lte" in slug or "mme" in slug or "hss" in slug or "dra" in slug or "diameter" in slug:
        return "4G EPC & Signaling"
    # 10. OSS & Fault Management
    if any(k in slug for k in ["grafana", "promql", "alert", "metric", "loki", "tempo", "log", "trace", "playbook", "runbook", "pipeline", "matrix", "rtr", "story", "note", "hypothesis", "decision", "cluster", "kpi"]):
        return "OSS & Fault Management"
    # 11. Mobile Core (5G SA)
    return "Mobile Core (5G SA)"


def precalculate_layout(entities: list[dict], links: list[dict], domain_centers: dict) -> list[tuple[float, float]]:
    """Precalculates resting equilibrium positions for nodes inside their domain clusters."""
    by_dom: dict[str, list[int]] = {}
    for i, e in enumerate(entities):
        by_dom.setdefault(e["domain"], []).append(i)

    pos = [None] * len(entities)
    # Initialize in Archimedean spiral around each domain center
    for dom, indices in by_dom.items():
        c = domain_centers.get(dom, {"x": 0, "y": 0})
        for order, idx in enumerate(indices):
            golden_angle = 2.39996
            r = 26.0 + 13.0 * math.sqrt(order)
            theta = order * golden_angle
            pos[idx] = {
                "x": c["x"] + math.cos(theta) * r,
                "y": c["y"] + math.sin(theta) * r,
                "vx": 0.0,
                "vy": 0.0,
                "domain": dom,
            }

    slug_to_idx = {e.get("slug", ""): i for i, e in enumerate(entities)}
    edge_indices = []
    for l in links:
        s = l.get("from_slug")
        t = l.get("to_slug")
        if s in slug_to_idx and t in slug_to_idx:
            edge_indices.append((slug_to_idx[s], slug_to_idx[t]))

    # Controlled relaxation: bounded forces & domain gravity
    for frame in range(150):
        temp = max(0.1, 1.0 - frame / 150.0)
        # Collision avoidance
        for i in range(len(pos)):
            p1 = pos[i]
            for j in range(i + 1, len(pos)):
                p2 = pos[j]
                dx = p2["x"] - p1["x"]
                dy = p2["y"] - p1["y"]
                dist2 = dx * dx + dy * dy
                if 0.1 < dist2 < 60 * 60:
                    dist = math.sqrt(dist2)
                    force = min(3.5, 450.0 / (dist2 + 50.0)) * temp
                    fx = (dx / dist) * force
                    fy = (dy / dist) * force
                    p1["vx"] -= fx
                    p1["vy"] -= fy
                    p2["vx"] += fx
                    p2["vy"] += fy

        # Intra-domain springs
        for s_idx, t_idx in edge_indices:
            p1 = pos[s_idx]
            p2 = pos[t_idx]
            isIntra = (p1["domain"] == p2["domain"])
            springLen = 45.0 if isIntra else 180.0
            springK = 0.045 if isIntra else 0.006
            dx = p2["x"] - p1["x"]
            dy = p2["y"] - p1["y"]
            dist = math.sqrt(dx * dx + dy * dy) or 1
            delta = dist - springLen
            force = min(2.5, delta * springK) * temp
            fx = (dx / dist) * force
            fy = (dy / dist) * force
            p1["vx"] -= fx
            p1["vy"] -= fy
            p2["vx"] += fx
            p2["vy"] += fy

        # Domain Anchor Gravity & Leash
        for p in pos:
            c = domain_centers.get(p["domain"], {"x": 0, "y": 0})
            dx = c["x"] - p["x"]
            dy = c["y"] - p["y"]
            distToCenter = math.hypot(dx, dy)
            count = len(by_dom.get(p["domain"], []))
            maxAllowed = 45.0 + math.sqrt(count) * 14.0

            gravity = 0.05
            if distToCenter > maxAllowed:
                gravity += (distToCenter - maxAllowed) * 0.008

            p["vx"] += dx * gravity
            p["vy"] += dy * gravity
            p["vx"] *= 0.76
            p["vy"] *= 0.76
            v = math.hypot(p["vx"], p["vy"])
            if v > 3.0:
                p["vx"] = (p["vx"] / v) * 3.0
                p["vy"] = (p["vy"] / v) * 3.0
            p["x"] += p["vx"]
            p["y"] += p["vy"]

    return [(round(p["x"], 1), round(p["y"], 1)) for p in pos]


def build_knowledge_graph(repo_root: Path, output_file: Path) -> dict:
    """Ingests artifacts/knowledge-inventory/knowledge-inventory.json and builds the unified explorer."""
    inv_path = repo_root / "artifacts/knowledge-inventory/knowledge-inventory.json"
    if not inv_path.is_file():
        candidates = list(repo_root.glob("**/knowledge-inventory.json"))
        if candidates:
            inv_path = candidates[0]
        else:
            raise FileNotFoundError(f"Could not locate knowledge-inventory.json in {repo_root}")

    with open(inv_path, "r", encoding="utf-8") as fp:
        inventory = json.load(fp)

    raw_entities = inventory.get("entities", [])
    raw_links = inventory.get("unique_links", [])

    for e in raw_entities:
        e["domain"] = map_telecom_domain(e)

    coords = precalculate_layout(raw_entities, raw_links, DOMAIN_CENTERS)

    nodes = []
    for i, e in enumerate(raw_entities):
        slug = e.get("slug", "")
        domain = e["domain"]
        title = e.get("title", slug)
        etype = e.get("type", "entity")
        color = DOMAIN_COLORS.get(domain, "#94a3b8")
        px, py = coords[i]

        nodes.append({
            "id": slug,
            "label": title,
            "domain": domain,
            "type": etype,
            "x": px,
            "y": py,
            "knowledge_state": e.get("knowledge_state", "CONFIRMED"),
            "in_degree": e.get("in_degree", 0),
            "out_degree": e.get("out_degree", 0),
            "evidence_count": e.get("evidence_count", 0),
            "color": color,
            "description": f"[{domain} &middot; {etype}] {title} (slug: {slug})",
        })

    links = []
    for l in raw_links:
        links.append({
            "source": l["from_slug"],
            "target": l["to_slug"],
            "link_type": l.get("link_type", "relates_to"),
            "human_link_type": l.get("human_link_type", l.get("link_type", "relates_to")),
            "source_domain": l.get("source_domain", ""),
            "target_domain": l.get("target_domain", ""),
            "is_cross_domain": l.get("is_cross_domain", False),
        })

    payload = {
        "title": "FikraCore Unified Telecom Knowledge Graph",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "brain": inventory.get("brain", "telecombrain"),
        "coverage_pct": inventory.get("summary", {}).get("overall_coverage_pct", 73.5),
        "nodes": nodes,
        "links": links,
        "domains": list(DOMAIN_COLORS.keys()),
        "domain_colors": DOMAIN_COLORS,
        "domain_centers": DOMAIN_CENTERS,
        "scenarios": SCENARIOS_CATALOG,
    }

    html_content = generate_html_viewer(payload)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as fp:
        fp.write(html_content)

    return {
        "output_file": str(output_file),
        "total_nodes": len(nodes),
        "total_links": len(links),
        "total_domains": len(payload["domains"]),
        "total_scenarios": len(SCENARIOS_CATALOG),
        "coverage_pct": payload["coverage_pct"],
        "timestamp": payload["timestamp"],
    }


def generate_html_viewer(data: dict) -> str:
    serialized_data = json.dumps(data, indent=2)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FikraCore Telecom Knowledge Graph | Unified Ontology & Scenario Projection</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    :root {{
      --bg-canvas: #090d16;
      --bg-panel: #0f172a;
      --border-panel: #1e293b;
      --accent-blue: #3b82f6;
      --accent-cyan: #06b6d4;
    }}
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg-canvas);
      color: #e2e8f0;
      overflow: hidden;
    }}
    .font-mono {{ font-family: 'JetBrains Mono', monospace; }}
    ::-webkit-scrollbar {{ width: 5px; height: 5px; }}
    ::-webkit-scrollbar-track {{ background: rgba(15, 23, 42, 0.6); }}
    ::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 4px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: #475569; }}
    #canvas-container {{
      background-size: 32px 32px;
      background-image: radial-gradient(circle, rgba(255, 255, 255, 0.08) 1px, transparent 1px);
    }}
    .glass-panel {{
      background: rgba(15, 23, 42, 0.88);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5);
    }}
    .glass-pill {{
      background: rgba(30, 41, 59, 0.6);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.06);
    }}
    .scenario-card.active {{
      border-color: rgba(59, 130, 246, 0.6);
      background: rgba(30, 58, 138, 0.25);
      box-shadow: 0 0 15px rgba(59, 130, 246, 0.2);
    }}
  </style>
</head>
<body class="w-screen h-screen flex flex-col antialiased select-none">
  <!-- Top Navigation Header -->
  <header class="h-14 bg-slate-900/90 border-b border-slate-800 px-5 flex items-center justify-between z-30 shrink-0">
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 via-indigo-500 to-cyan-400 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
        <i class="fa-solid fa-network-wired text-sm"></i>
      </div>
      <div>
        <div class="flex items-center gap-2">
          <span class="font-bold tracking-tight text-white text-base">FikraCore</span>
          <span class="text-xs px-2 py-0.5 rounded-full font-mono bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">TelecomBrain Knowledge Graph</span>
          <span class="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
            Live Verified &middot; Unified Twin
          </span>
        </div>
      </div>
    </div>

    <!-- Live Statistics Strip -->
    <div class="hidden lg:flex items-center gap-6 text-xs text-slate-400 font-mono">
      <div class="flex items-center gap-2"><i class="fa-solid fa-cube text-blue-400"></i><span><strong class="text-white">{len(data['nodes'])}</strong> Entities</span></div>
      <div class="w-px h-3 bg-slate-800"></div>
      <div class="flex items-center gap-2"><i class="fa-solid fa-arrow-right-arrow-left text-cyan-400"></i><span><strong class="text-white">{len(data['links'])}</strong> Causal Links</span></div>
      <div class="w-px h-3 bg-slate-800"></div>
      <div class="flex items-center gap-2"><i class="fa-solid fa-layer-group text-purple-400"></i><span><strong class="text-white">{len(data['domains'])}</strong> Telecom Domains</span></div>
      <div class="w-px h-3 bg-slate-800"></div>
      <div class="flex items-center gap-2"><i class="fa-solid fa-shield-halved text-emerald-400"></i><span>Coverage: <strong class="text-emerald-300">{data['coverage_pct']}%</strong></span></div>
      <div class="w-px h-3 bg-slate-800"></div>
      <div class="flex items-center gap-2"><i class="fa-solid fa-clock text-slate-500"></i><span>Synced: {data['timestamp'][:19]}Z</span></div>
    </div>

    <div class="flex items-center gap-2">
      <!-- Panel Visibility Controls for Visualization Real Estate -->
      <button onclick="toggleLeftPanel()" id="btn-header-left" class="px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition flex items-center gap-1.5" title="Toggle Controls Sidebar [Hotkey: '[']">
        <i class="fa-solid fa-table-columns text-slate-400"></i> <span class="hidden md:inline">Sidebar</span>
      </button>
      <button onclick="toggleRightPanel()" id="btn-header-right" class="px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition flex items-center gap-1.5" title="Toggle Entity Inspector [Hotkey: ']']">
        <i class="fa-solid fa-circle-info text-slate-400"></i> <span class="hidden md:inline">Inspector</span>
      </button>
      <div class="w-px h-4 bg-slate-700 mx-0.5"></div>
      <button onclick="resetCamera()" class="px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition flex items-center gap-1.5" title="Fit View to Screen [Hotkey: 'f']"><i class="fa-solid fa-compress text-slate-400"></i> Fit View</button>
      <button onclick="togglePhysics()" id="btn-physics" class="px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition flex items-center gap-1.5" title="Toggle Simulation Physics [Hotkey: 'p']"><i class="fa-solid fa-pause text-slate-400"></i> Pin Nodes</button>
    </div>
  </header>

  <div class="flex-1 flex overflow-hidden relative">
    <!-- Left Sidebar: Search, Domain Filtering & Scenario Selection (Collapsible) -->
    <aside id="leftSidebar" class="w-84 bg-slate-900/95 border-r border-slate-800 flex flex-col z-20 shrink-0 transition-all duration-300 overflow-hidden" style="width: 22rem;">
      <!-- Search Input + Collapse Button -->
      <div class="p-3 border-b border-slate-800 flex items-center gap-2">
        <div class="relative flex-1">
          <i class="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs"></i>
          <input type="text" id="searchInput" oninput="handleSearch(this.value)" placeholder="Search entity, slug, protocol..." class="w-full pl-9 pr-8 py-1.5 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition font-mono">
          <button id="clearSearchBtn" onclick="clearSearch()" class="hidden absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"><i class="fa-solid fa-xmark text-xs"></i></button>
        </div>
        <button onclick="toggleLeftPanel()" class="w-8 h-8 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700/60 transition flex items-center justify-center shrink-0" title="Hide Sidebar [Hotkey: '[']">
          <i class="fa-solid fa-chevron-left text-xs"></i>
        </button>
      </div>

      <!-- Incident & Scenario Projection Panel Header -->
      <div class="p-3 border-b border-slate-800 bg-slate-950/40 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <i class="fa-solid fa-bolt-lightning text-amber-400 text-xs"></i>
          <span class="text-xs font-semibold uppercase tracking-wider text-slate-300">Scenario Projection</span>
        </div>
        <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30 font-semibold" id="activeScenarioBadge">BASELINE</span>
      </div>

      <!-- Scenario Selector Drawer List -->
      <div class="p-2 border-b border-slate-800 space-y-1.5 max-h-56 overflow-y-auto" id="scenariosList">
        <!-- Rendered via JS -->
      </div>

      <!-- Domain Filters Header -->
      <div class="p-3 border-b border-slate-800 flex items-center justify-between bg-slate-900">
        <span class="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5"><i class="fa-solid fa-filter text-[10px]"></i> Telecom Domains</span>
        <button onclick="toggleAllDomains()" id="toggleAllDomainsBtn" class="text-[11px] text-blue-400 hover:text-blue-300 transition font-mono">Deselect All</button>
      </div>

      <!-- Domains List -->
      <div id="domainsList" class="flex-1 overflow-y-auto p-2 space-y-1"></div>

      <!-- Live Alarm Severity Legend -->
      <div class="p-3 border-t border-slate-800 bg-slate-950/70 text-[11px] font-mono space-y-1">
        <span class="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">Discrete 3GPP Alarm State</span>
        <div class="grid grid-cols-2 gap-1 text-[10px]">
          <div class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></span><span class="text-red-300 font-semibold">Root Cause</span></div>
          <div class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-red-400"></span><span class="text-red-200">Critical (3GPP)</span></div>
          <div class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-amber-400"></span><span class="text-amber-200">Major</span></div>
          <div class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-yellow-400"></span><span class="text-yellow-200">Minor / Warning</span></div>
        </div>
      </div>
    </aside>

    <!-- Main Canvas Viewport -->
    <main id="canvas-container" class="flex-1 h-full relative cursor-grab active:cursor-grabbing overflow-hidden">
      <canvas id="graphCanvas" class="w-full h-full block"></canvas>

      <!-- Floating Open Sidebar Pill (Visible when Left Sidebar is collapsed) -->
      <button id="btn-open-left" onclick="toggleLeftPanel()" class="hidden absolute top-4 left-4 z-20 px-3 py-2 glass-panel rounded-xl text-xs font-medium text-slate-200 hover:text-white transition flex items-center gap-2 shadow-xl hover:bg-slate-800" title="Show Sidebar [Hotkey: '[']">
        <i class="fa-solid fa-chevron-right text-xs text-blue-400"></i>
        <span class="font-semibold text-xs">Show Controls</span>
      </button>

      <!-- Floating Open Inspector Pill (Visible when Inspector is collapsed) -->
      <button id="btn-open-right" onclick="toggleRightPanel()" class="hidden absolute top-4 right-4 z-20 px-3 py-2 glass-panel rounded-xl text-xs font-medium text-slate-200 hover:text-white transition flex items-center gap-2 shadow-xl hover:bg-slate-800" title="Show Inspector [Hotkey: ']']">
        <i class="fa-solid fa-circle-info text-xs text-cyan-400"></i>
        <span class="font-semibold text-xs">Show Inspector</span>
      </button>

      <!-- Overlay HUD: Active Scenario Banner -->
      <div id="hudContainer" class="absolute top-4 left-4 z-10 pointer-events-none flex flex-col gap-2 transition-all duration-300">
        <div class="glass-panel px-3.5 py-2 rounded-xl text-xs flex items-center gap-3">
          <div class="w-2.5 h-2.5 rounded-full" id="hudStatusDot" style="background-color: #10b981;"></div>
          <div>
            <div class="font-bold text-white flex items-center gap-2" id="hudScenarioTitle">Baseline Steady-State</div>
            <div class="text-[11px] text-slate-400 font-mono mt-0.5" id="hudScenarioDesc">132 entities nominal &middot; 0 active fault injections</div>
          </div>
        </div>
      </div>

      <!-- Floating Canvas Camera Controls -->
      <div class="absolute bottom-5 left-5 z-20 flex items-center gap-1.5 p-1 glass-panel rounded-xl">
        <button onclick="zoomIn()" class="w-8 h-8 rounded-lg hover:bg-slate-800 flex items-center justify-center text-slate-300 hover:text-white transition" title="Zoom In"><i class="fa-solid fa-plus text-xs"></i></button>
        <button onclick="zoomOut()" class="w-8 h-8 rounded-lg hover:bg-slate-800 flex items-center justify-center text-slate-300 hover:text-white transition" title="Zoom Out"><i class="fa-solid fa-minus text-xs"></i></button>
        <button onclick="resetCamera()" class="w-8 h-8 rounded-lg hover:bg-slate-800 flex items-center justify-center text-slate-300 hover:text-white transition" title="Fit to Screen [Hotkey: 'f']"><i class="fa-solid fa-expand text-xs"></i></button>
        <div class="w-px h-4 bg-slate-700 mx-1"></div>
        <button onclick="toggleLabels()" id="btn-labels" class="px-2.5 h-8 rounded-lg hover:bg-slate-800 flex items-center justify-center text-xs text-slate-300 hover:text-white transition" title="Toggle Node Labels [Hotkey: 'l']"><i class="fa-solid fa-font mr-1.5 text-[10px]"></i> Labels</button>
        <button onclick="isolateActiveBlastRadius()" id="btn-blast" class="px-2.5 h-8 rounded-lg hover:bg-slate-800 flex items-center justify-center text-xs text-amber-400 hover:text-amber-300 transition" title="Isolate Active Blast Radius"><i class="fa-solid fa-crosshairs mr-1.5 text-[10px]"></i> Focus Impact</button>
      </div>
    </main>

    <!-- Right Sidebar: Entity Inspector & Blast Radius Diagnostic (Collapsible) -->
    <aside id="inspectorPanel" class="w-96 bg-slate-900/95 border-l border-slate-800 flex flex-col z-20 shrink-0 transition-all duration-300 overflow-hidden">
      <div class="p-4 border-b border-slate-800 flex items-center justify-between">
        <div class="flex items-center gap-2 min-w-0">
          <span class="w-2.5 h-2.5 rounded-full bg-blue-500 shrink-0" id="insp-header-dot"></span>
          <span class="font-bold text-slate-200 text-sm truncate" id="insp-header-title">Entity Inspector</span>
        </div>
        <div class="flex items-center gap-1 shrink-0">
          <button onclick="toggleRightPanel()" class="w-7 h-7 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition flex items-center justify-center" title="Hide Inspector [Hotkey: ']']">
            <i class="fa-solid fa-chevron-right text-xs"></i>
          </button>
          <button onclick="deselectNode()" class="w-7 h-7 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition flex items-center justify-center" title="Clear Selection">
            <i class="fa-solid fa-xmark text-sm"></i>
          </button>
        </div>
      </div>

      <div id="inspectorContent" class="flex-1 overflow-y-auto p-4 space-y-4">
        <div class="text-center py-16 text-slate-500">
          <i class="fa-solid fa-arrow-pointer text-2xl mb-3 opacity-40"></i>
          <p class="text-xs max-w-xs mx-auto leading-relaxed">Select any entity on the knowledge canvas or pick an incident scenario to inspect active 3GPP alarm propagation, incoming root causes, and downstream impact.</p>
        </div>
      </div>
    </aside>
  </div>

  <script>
    const GRAPH_DATA = {serialized_data};
    let nodes = [];
    let links = [];
    let activeDomains = new Set(GRAPH_DATA.domains);
    let selectedNode = null;
    let hoveredNode = null;
    let highlightedNodes = new Set();
    let currentScenario = GRAPH_DATA.scenarios[0];
    let showAllLabels = true;
    let isPhysicsActive = true;
    let camera = {{ x: 0, y: 0, zoom: 0.85 }};
    let isDragging = false;
    let dragStart = {{ x: 0, y: 0 }};
    let draggedNode = null;
    let mouseWorldPos = {{ x: 0, y: 0 }};
    let pulseTime = 0;

    const canvas = document.getElementById('graphCanvas');
    const ctx = canvas.getContext('2d');

    // Precalculate counts per domain for dynamic gravity tethering
    const DOMAIN_COUNTS = {{}};
    GRAPH_DATA.nodes.forEach(n => {{
      DOMAIN_COUNTS[n.domain] = (DOMAIN_COUNTS[n.domain] || 0) + 1;
    }});

    function initData() {{
      nodes = GRAPH_DATA.nodes.map(n => {{
        let radius = 12;
        if (n.type === 'service' || n.id.includes('sgi-data') || n.id.includes('lte-attach')) radius = 18;
        else if (n.type === 'incident' || n.type === 'incident-alias') radius = 16;
        else if (n.type === 'network-function' || n.type === 'domain-function') radius = 15;
        else if (n.type === 'hypothesis' || n.type === 'correlation-cluster') radius = 14;

        return {{
          ...n,
          x: n.x,
          y: n.y,
          vx: 0,
          vy: 0,
          radius: radius,
          alarmSeverity: 'NOMINAL',
          alarmStatus: 'Normal Operation',
        }};
      }});

      links = GRAPH_DATA.links.map(l => {{
        const sourceNode = nodes.find(n => n.id === l.source);
        const targetNode = nodes.find(n => n.id === l.target);
        return {{ ...l, sourceNode, targetNode }};
      }}).filter(l => l.sourceNode && l.targetNode);

      renderScenarioList();
      renderDomainList();
      applyScenario('baseline');
    }}

    function resizeCanvas() {{
      const rect = canvas.parentElement.getBoundingClientRect();
      canvas.width = rect.width * window.devicePixelRatio;
      canvas.height = rect.height * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    }}

    window.addEventListener('resize', resizeCanvas);

    // Collapsible Panels Logic
    function toggleLeftPanel() {{
      const left = document.getElementById('leftSidebar');
      const btnOpen = document.getElementById('btn-open-left');
      const btnHeader = document.getElementById('btn-header-left');
      const hud = document.getElementById('hudContainer');

      const isHidden = left.classList.toggle('hidden');
      if (btnOpen) btnOpen.classList.toggle('hidden', !isHidden);
      if (btnHeader) {{
        btnHeader.classList.toggle('bg-blue-600/30', !isHidden);
        btnHeader.classList.toggle('border-blue-500/50', !isHidden);
      }}
      if (hud) {{
        hud.style.left = isHidden ? '8.5rem' : '1rem';
      }}
      setTimeout(() => {{
        resizeCanvas();
      }}, 50);
    }}

    function toggleRightPanel() {{
      const right = document.getElementById('inspectorPanel');
      const btnOpen = document.getElementById('btn-open-right');
      const btnHeader = document.getElementById('btn-header-right');

      const isHidden = right.classList.toggle('hidden');
      if (btnOpen) btnOpen.classList.toggle('hidden', !isHidden);
      if (btnHeader) {{
        btnHeader.classList.toggle('bg-blue-600/30', !isHidden);
        btnHeader.classList.toggle('border-blue-500/50', !isHidden);
      }}
      setTimeout(() => {{
        resizeCanvas();
      }}, 50);
    }}

    // Global keyboard shortcuts for productivity
    window.addEventListener('keydown', e => {{
      if (e.target.tagName === 'INPUT') return;
      if (e.key === '[') toggleLeftPanel();
      else if (e.key === ']') toggleRightPanel();
      else if (e.key === 'f' || e.key === 'F') resetCamera();
      else if (e.key === 'p' || e.key === 'P') togglePhysics();
      else if (e.key === 'l' || e.key === 'L') toggleLabels();
      else if (e.key === 'Escape') deselectNode();
    }});

    function renderScenarioList() {{
      const container = document.getElementById('scenariosList');
      container.innerHTML = '';
      GRAPH_DATA.scenarios.forEach(scn => {{
        const isActive = currentScenario && currentScenario.id === scn.id;
        const card = document.createElement('div');
        card.className = `scenario-card p-2 rounded-lg cursor-pointer transition border text-xs ${{
          isActive
            ? 'active border-blue-500/60 bg-blue-950/30'
            : 'border-slate-800/80 bg-slate-950/40 hover:bg-slate-800/60 hover:border-slate-700'
        }}`;
        card.onclick = () => applyScenario(scn.id);

        const badgeColor =
          scn.badge === 'CRITICAL' ? 'bg-red-500/20 text-red-300 border-red-500/40' :
          scn.badge === 'MAJOR' ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' :
          scn.badge === 'MINOR' ? 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40' :
          'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';

        card.innerHTML = `
          <div class="flex items-center justify-between gap-1">
            <span class="font-semibold text-slate-200 truncate">${{scn.name}}</span>
            <span class="text-[9px] font-mono px-1.5 py-0.5 rounded border ${{badgeColor}} shrink-0">${{scn.badge}}</span>
          </div>
          <p class="text-[10px] text-slate-400 mt-1 line-clamp-1">${{scn.description}}</p>
        `;
        container.appendChild(card);
      }});
    }}

    function applyScenario(scenarioId) {{
      const scn = GRAPH_DATA.scenarios.find(s => s.id === scenarioId) || GRAPH_DATA.scenarios[0];
      currentScenario = scn;

      // Update HUD
      document.getElementById('activeScenarioBadge').innerText = scn.badge;
      document.getElementById('hudScenarioTitle').innerText = scn.name;
      document.getElementById('hudScenarioDesc').innerText = scn.description;
      const dot = document.getElementById('hudStatusDot');
      dot.style.backgroundColor =
        scn.badge === 'CRITICAL' ? '#ef4444' :
        scn.badge === 'MAJOR' ? '#f59e0b' :
        scn.badge === 'MINOR' ? '#eab308' : '#10b981';

      // Update Node alarm states
      highlightedNodes.clear();
      nodes.forEach(n => {{
        if (scn.affected_nodes && scn.affected_nodes[n.id]) {{
          const aff = scn.affected_nodes[n.id];
          n.alarmSeverity = aff.severity;
          n.alarmStatus = aff.status;
          highlightedNodes.add(n.id);
        }} else {{
          n.alarmSeverity = 'NOMINAL';
          n.alarmStatus = 'Normal Operation';
        }}
      }});

      renderScenarioList();

      if (scn.root_cause) {{
        const rootNode = nodes.find(n => n.id === scn.root_cause);
        if (rootNode) {{
          activeDomains.add(rootNode.domain);
          selectNode(rootNode);
        }}
      }} else {{
        deselectNode();
      }}
    }}

    function isolateActiveBlastRadius() {{
      if (highlightedNodes.size === 0) return;
      const affected = nodes.filter(n => highlightedNodes.has(n.id));
      if (affected.length === 0) return;

      const avgX = affected.reduce((acc, n) => acc + n.x, 0) / affected.length;
      const avgY = affected.reduce((acc, n) => acc + n.y, 0) / affected.length;
      camera.x = -avgX * camera.zoom;
      camera.y = -avgY * camera.zoom;
      camera.zoom = 1.15;
    }}

    // Domain Node Stickiness & Center Gravity Simulation
    function stepPhysics() {{
      if (!isPhysicsActive && !draggedNode) return;

      const centers = GRAPH_DATA.domain_centers;
      const activeNodeList = nodes.filter(n => activeDomains.has(n.domain));

      // 1. Short-range collision avoidance (prevents node overlap within clusters)
      for (let i = 0; i < activeNodeList.length; i++) {{
        const n1 = activeNodeList[i];
        for (let j = i + 1; j < activeNodeList.length; j++) {{
          const n2 = activeNodeList[j];
          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;
          const dist2 = dx * dx + dy * dy;
          if (dist2 < 60 * 60 && dist2 > 0.01) {{
            const dist = Math.sqrt(dist2);
            const force = Math.min(3.5, 450.0 / (dist2 + 50.0));
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            if (n1 !== draggedNode) {{ n1.vx -= fx; n1.vy -= fy; }}
            if (n2 !== draggedNode) {{ n2.vx += fx; n2.vy += fy; }}
          }}
        }}
      }}

      // 2. Springs: Strong intra-domain stickiness, gentle cross-domain links
      for (const link of links) {{
        if (!activeDomains.has(link.sourceNode.domain) || !activeDomains.has(link.targetNode.domain)) continue;
        const n1 = link.sourceNode;
        const n2 = link.targetNode;
        const isIntra = (n1.domain === n2.domain);
        const springLen = isIntra ? 45.0 : 180.0;
        const springK = isIntra ? 0.045 : 0.006;

        const dx = n2.x - n1.x;
        const dy = n2.y - n1.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const delta = dist - springLen;
        const force = Math.min(2.5, delta * springK);
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        if (n1 !== draggedNode) {{ n1.vx -= fx; n1.vy -= fy; }}
        if (n2 !== draggedNode) {{ n2.vx += fx; n2.vy += fy; }}
      }}

      // 3. Domain Center Gravitational Pull & Elastic Boundary Tethering
      for (const n of activeNodeList) {{
        if (n === draggedNode) {{
          n.x = mouseWorldPos.x;
          n.y = mouseWorldPos.y;
          n.vx = 0;
          n.vy = 0;
          continue;
        }}

        const center = centers[n.domain] || {{ x: 0, y: 0 }};
        const dx = center.x - n.x;
        const dy = center.y - n.y;
        const distToCenter = Math.hypot(dx, dy);
        const count = DOMAIN_COUNTS[n.domain] || 5;
        const maxAllowed = 45.0 + Math.sqrt(count) * 14.0;

        let gravity = 0.05;
        if (distToCenter > maxAllowed) {{
          // Elastic restoring tether pulling node back into its domain bubble
          gravity += (distToCenter - maxAllowed) * 0.008;
        }}

        n.vx += dx * gravity;
        n.vy += dy * gravity;

        n.vx *= 0.76;
        n.vy *= 0.76;
        const v = Math.hypot(n.vx, n.vy);
        if (v > 3.0) {{
          n.vx = (n.vx / v) * 3.0;
          n.vy = (n.vy / v) * 3.0;
        }}
        n.x += n.vx;
        n.y += n.vy;
      }}
    }}

    function draw() {{
      stepPhysics();
      pulseTime += 0.025;

      const rect = canvas.getBoundingClientRect();
      ctx.clearRect(0, 0, rect.width, rect.height);
      ctx.save();
      ctx.translate(rect.width / 2 + camera.x, rect.height / 2 + camera.y);
      ctx.scale(camera.zoom, camera.zoom);

      // 0. Draw Domain Cluster Boundaries (Soft Enclosure + Dashed Demarcation Ring + Header Tag)
      for (const [domName, center] of Object.entries(GRAPH_DATA.domain_centers)) {{
        if (!activeDomains.has(domName)) continue;
        const domNodes = nodes.filter(n => n.domain === domName);
        if (domNodes.length === 0) continue;

        const color = GRAPH_DATA.domain_colors[domName] || "#3b82f6";
        let maxR = 60;
        for (const dn of domNodes) {{
          const d = Math.hypot(dn.x - center.x, dn.y - center.y);
          if (d + dn.radius + 35 > maxR) maxR = d + dn.radius + 35;
        }}

        // Soft Cluster Aura
        ctx.beginPath();
        ctx.arc(center.x, center.y, maxR, 0, Math.PI * 2);
        ctx.fillStyle = color + "0d"; // 5% opacity
        ctx.fill();
        ctx.lineWidth = 1.2;
        ctx.setLineDash([4, 4]);
        ctx.strokeStyle = color + "38"; // 22% opacity
        ctx.stroke();
        ctx.setLineDash([]);

        // Cluster Header Tag
        ctx.fillStyle = color + "cc";
        ctx.font = "600 11px Inter, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(domName.toUpperCase(), center.x, center.y - maxR + 14);
      }}

      // 1. Draw Links
      for (const link of links) {{
        if (!activeDomains.has(link.sourceNode.domain) || !activeDomains.has(link.targetNode.domain)) continue;
        const isImpactedLink = highlightedNodes.has(link.sourceNode.id) && highlightedNodes.has(link.targetNode.id);
        const isConnectedToSelected = selectedNode && (link.sourceNode.id === selectedNode.id || link.targetNode.id === selectedNode.id);

        ctx.beginPath();
        ctx.moveTo(link.sourceNode.x, link.sourceNode.y);
        ctx.lineTo(link.targetNode.x, link.targetNode.y);

        if (isImpactedLink) {{
          ctx.lineWidth = 3.0;
          ctx.strokeStyle = '#ef4444';
        }} else if (isConnectedToSelected) {{
          ctx.lineWidth = 2.5;
          ctx.strokeStyle = '#38bdf8';
        }} else if (selectedNode || highlightedNodes.size > 0) {{
          ctx.lineWidth = 1;
          ctx.strokeStyle = 'rgba(71, 85, 105, 0.2)';
        }} else {{
          ctx.lineWidth = 1.2;
          ctx.strokeStyle = link.is_cross_domain ? 'rgba(245, 158, 11, 0.35)' : 'rgba(100, 116, 139, 0.3)';
        }}
        ctx.stroke();

        // Directional Arrow
        drawArrow(link.sourceNode.x, link.sourceNode.y, link.targetNode.x, link.targetNode.y, link.targetNode.radius, isImpactedLink || isConnectedToSelected);

        // Animated Particle on Active Causal Edges
        if (isImpactedLink) {{
          const t = (pulseTime * 1.5) % 1.0;
          const px = link.sourceNode.x + (link.targetNode.x - link.sourceNode.x) * t;
          const py = link.sourceNode.y + (link.targetNode.y - link.sourceNode.y) * t;
          ctx.beginPath();
          ctx.arc(px, py, 3.5, 0, Math.PI * 2);
          ctx.fillStyle = '#f87171';
          ctx.shadowColor = '#ef4444';
          ctx.shadowBlur = 8;
          ctx.fill();
          ctx.shadowBlur = 0;
        }}

        // Label on inspect or hover
        if (isConnectedToSelected || (hoveredNode && (hoveredNode.id === link.sourceNode.id || hoveredNode.id === link.targetNode.id))) {{
          const mx = (link.sourceNode.x + link.targetNode.x) / 2;
          const my = (link.sourceNode.y + link.targetNode.y) / 2;
          ctx.fillStyle = isImpactedLink ? '#fca5a5' : '#94a3b8';
          ctx.font = '500 10px JetBrains Mono, monospace';
          ctx.textAlign = 'center';
          ctx.fillText(link.human_link_type || link.link_type, mx, my - 6);
        }}
      }}

      // 2. Draw Nodes
      for (const n of nodes) {{
        if (!activeDomains.has(n.domain)) continue;
        const isSelected = selectedNode && selectedNode.id === n.id;
        const isHovered = hoveredNode && hoveredNode.id === n.id;
        const isImpacted = highlightedNodes.has(n.id);
        const isDimmed = (selectedNode || highlightedNodes.size > 0) && !isSelected && !isHovered && !isImpacted && (!selectedNode || !isConnected(selectedNode, n));

        // Discrete 3GPP Alarm State Colors
        let nodeColor = n.color || '#3b82f6';
        let haloColor = null;

        if (n.alarmSeverity === 'ROOT_CAUSE') {{
          nodeColor = '#ef4444';
          haloColor = 'rgba(239, 68, 68, 0.4)';
        }} else if (n.alarmSeverity === 'CRITICAL') {{
          nodeColor = '#f87171';
          haloColor = 'rgba(248, 113, 113, 0.3)';
        }} else if (n.alarmSeverity === 'MAJOR') {{
          nodeColor = '#f59e0b';
          haloColor = 'rgba(245, 158, 11, 0.3)';
        }} else if (n.alarmSeverity === 'MINOR') {{
          nodeColor = '#eab308';
          haloColor = 'rgba(234, 179, 8, 0.25)';
        }}

        // Halo for Root Cause, Selected, or Hovered
        if (isSelected || haloColor) {{
          const haloRadius = n.radius + (n.alarmSeverity === 'ROOT_CAUSE' ? 10 + Math.sin(pulseTime * 4) * 4 : 7);
          ctx.beginPath();
          ctx.arc(n.x, n.y, haloRadius, 0, Math.PI * 2);
          ctx.fillStyle = haloColor || 'rgba(59, 130, 246, 0.28)';
          ctx.fill();
        }}

        // Main Node Body
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
        ctx.fillStyle = isDimmed ? 'rgba(30, 41, 59, 0.5)' : nodeColor;
        ctx.fill();
        ctx.lineWidth = isSelected ? 3 : (isHovered ? 2.5 : 1.5);
        ctx.strokeStyle = isSelected ? '#ffffff' : (isHovered ? '#e2e8f0' : (isDimmed ? '#334155' : nodeColor));
        ctx.stroke();

        // Inner Core Pip
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius * 0.35, 0, Math.PI * 2);
        ctx.fillStyle = isDimmed ? '#475569' : '#ffffff';
        ctx.fill();

        // Node Labels
        if (showAllLabels || isSelected || isHovered || isImpacted) {{
          ctx.fillStyle = isDimmed ? '#64748b' : '#f1f5f9';
          ctx.font = isSelected || isImpacted ? '600 11px Inter, sans-serif' : '500 10px Inter, sans-serif';
          ctx.textAlign = 'center';

          const cleanLabel = n.label.length > 28 ? n.label.slice(0, 26) + '…' : n.label;
          ctx.fillText(cleanLabel, n.x, n.y + n.radius + 13);

          if (n.alarmSeverity !== 'NOMINAL') {{
            ctx.fillStyle = n.alarmSeverity === 'ROOT_CAUSE' ? '#f87171' : '#fcd34d';
            ctx.font = '600 9px JetBrains Mono, monospace';
            ctx.fillText(`[${{n.alarmSeverity}}]`, n.x, n.y + n.radius + 24);
          }}
        }}
      }}

      ctx.restore();
      requestAnimationFrame(draw);
    }}

    function drawArrow(x1, y1, x2, y2, targetRadius, isActive) {{
      const angle = Math.atan2(y2 - y1, x2 - x1);
      const edgeDist = targetRadius + 3;
      const arrowX = x2 - Math.cos(angle) * edgeDist;
      const arrowY = y2 - Math.sin(angle) * edgeDist;
      const arrowSize = isActive ? 7 : 5;
      ctx.save();
      ctx.beginPath();
      ctx.translate(arrowX, arrowY);
      ctx.rotate(angle);
      ctx.moveTo(0, 0);
      ctx.lineTo(-arrowSize * 1.5, -arrowSize);
      ctx.lineTo(-arrowSize * 1.5, arrowSize);
      ctx.closePath();
      ctx.fillStyle = isActive ? '#f87171' : 'rgba(148, 163, 184, 0.65)';
      ctx.fill();
      ctx.restore();
    }}

    function isConnected(a, b) {{
      return links.some(l => (l.sourceNode.id === a.id && l.targetNode.id === b.id) || (l.sourceNode.id === b.id && l.targetNode.id === a.id));
    }}

    function screenToWorld(sx, sy) {{
      const rect = canvas.getBoundingClientRect();
      const cx = rect.width / 2;
      const cy = rect.height / 2;
      return {{ x: (sx - cx - camera.x) / camera.zoom, y: (sy - cy - camera.y) / camera.zoom }};
    }}

    canvas.addEventListener('mousedown', e => {{
      const rect = canvas.getBoundingClientRect();
      const mouseWorld = screenToWorld(e.clientX - rect.left, e.clientY - rect.top);
      mouseWorldPos = mouseWorld;
      const clicked = nodes.find(n => {{
        if (!activeDomains.has(n.domain)) return false;
        return Math.hypot(n.x - mouseWorld.x, n.y - mouseWorld.y) <= n.radius + 5;
      }});
      if (clicked) {{
        draggedNode = clicked;
        selectNode(clicked);
      }} else {{
        isDragging = true;
        dragStart = {{ x: e.clientX - camera.x, y: e.clientY - camera.y }};
      }}
    }});

    window.addEventListener('mousemove', e => {{
      const rect = canvas.getBoundingClientRect();
      const mouseWorld = screenToWorld(e.clientX - rect.left, e.clientY - rect.top);
      mouseWorldPos = mouseWorld;
      if (draggedNode) {{
        draggedNode.x = mouseWorld.x;
        draggedNode.y = mouseWorld.y;
        draggedNode.vx = 0;
        draggedNode.vy = 0;
      }} else if (isDragging) {{
        camera.x = e.clientX - dragStart.x;
        camera.y = e.clientY - dragStart.y;
      }} else {{
        const hovered = nodes.find(n => {{
          if (!activeDomains.has(n.domain)) return false;
          return Math.hypot(n.x - mouseWorld.x, n.y - mouseWorld.y) <= n.radius + 5;
        }});
        hoveredNode = hovered || null;
        canvas.style.cursor = hovered ? 'pointer' : (isDragging ? 'grabbing' : 'grab');
      }}
    }});

    window.addEventListener('mouseup', () => {{ draggedNode = null; isDragging = false; }});

    canvas.addEventListener('wheel', e => {{
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
      const newZoom = Math.max(0.2, Math.min(3.5, camera.zoom * zoomFactor));
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left - rect.width / 2;
      const my = e.clientY - rect.top - rect.height / 2;
      camera.x -= (mx - camera.x) * (newZoom / camera.zoom - 1);
      camera.y -= (my - camera.y) * (newZoom / camera.zoom - 1);
      camera.zoom = newZoom;
    }}, {{ passive: false }});

    function renderDomainList() {{
      const container = document.getElementById('domainsList');
      container.innerHTML = '';
      GRAPH_DATA.domains.forEach(dom => {{
        const count = nodes.filter(n => n.domain === dom).length;
        if (count === 0) return;
        const color = GRAPH_DATA.domain_colors[dom] || "#3b82f6";
        const isActive = activeDomains.has(dom);
        const el = document.createElement('div');
        el.className = `flex items-center justify-between p-2 rounded-lg cursor-pointer transition text-xs ${{isActive ? 'bg-slate-800/80 text-slate-200' : 'opacity-40 hover:opacity-75 text-slate-500'}}`;
        el.onclick = () => toggleDomain(dom);
        el.innerHTML = `
          <div class="flex items-center gap-2 overflow-hidden">
            <span class="w-3 h-3 rounded-full shrink-0" style="background-color: ${{color}}"></span>
            <span class="truncate font-medium">${{dom}}</span>
          </div>
          <span class="font-mono text-[11px] px-1.5 py-0.5 rounded bg-slate-900/80 border border-slate-700/50 text-slate-400">${{count}}</span>
        `;
        container.appendChild(el);
      }});
    }}

    function toggleDomain(domain) {{
      if (activeDomains.has(domain)) activeDomains.delete(domain);
      else activeDomains.add(domain);
      renderDomainList();
    }}

    function toggleAllDomains() {{
      const btn = document.getElementById('toggleAllDomainsBtn');
      if (activeDomains.size === GRAPH_DATA.domains.length) {{
        activeDomains.clear(); btn.innerText = 'Select All';
      }} else {{
        activeDomains = new Set(GRAPH_DATA.domains); btn.innerText = 'Deselect All';
      }}
      renderDomainList();
    }}

    function selectNode(node) {{
      selectedNode = node;
      // If inspector is hidden, open it automatically
      const right = document.getElementById('inspectorPanel');
      if (right && right.classList.contains('hidden')) {{
        toggleRightPanel();
      }}

      document.getElementById('insp-header-dot').style.backgroundColor = node.color;
      document.getElementById('insp-header-title').innerText = node.label;

      const outgoing = links.filter(l => l.sourceNode.id === node.id);
      const incoming = links.filter(l => l.targetNode.id === node.id);

      const sevBadge =
        node.alarmSeverity === 'ROOT_CAUSE' ? '<span class="text-[10px] px-2 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/40 font-bold font-mono">ROOT CAUSE</span>' :
        node.alarmSeverity === 'CRITICAL' ? '<span class="text-[10px] px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/40 font-mono">CRITICAL</span>' :
        node.alarmSeverity === 'MAJOR' ? '<span class="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 font-mono">MAJOR</span>' :
        node.alarmSeverity === 'MINOR' ? '<span class="text-[10px] px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-300 border border-yellow-500/40 font-mono">MINOR</span>' :
        '<span class="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-mono">NOMINAL</span>';

      const panel = document.getElementById('inspectorContent');
      panel.innerHTML = `
        <div class="space-y-3">
          <div class="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-mono text-slate-400 uppercase tracking-wider">3GPP Status</span>
              ${{sevBadge}}
            </div>
            <div class="text-xs font-semibold text-slate-200">${{node.alarmStatus || 'Normal Operation'}}</div>
          </div>

          <div class="p-3 rounded-lg bg-slate-950/40 border border-slate-800/80 space-y-1.5 text-xs">
            <div class="flex justify-between text-slate-400"><span class="font-mono">Domain:</span><span class="text-slate-200 font-medium">${{node.domain}}</span></div>
            <div class="flex justify-between text-slate-400"><span class="font-mono">Type:</span><span class="text-slate-200 font-mono text-[11px]">${{node.type}}</span></div>
            <div class="flex justify-between text-slate-400"><span class="font-mono">Knowledge:</span><span class="text-emerald-400 font-mono text-[11px]">${{node.knowledge_state}}</span></div>
            <div class="flex justify-between text-slate-400"><span class="font-mono">Degree:</span><span class="text-slate-200 font-mono text-[11px]">in: ${{node.in_degree}} &middot; out: ${{node.out_degree}}</span></div>
          </div>

          <div class="space-y-1.5">
            <div class="text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center justify-between">
              <span>Upstream Causal Drivers</span>
              <span class="font-mono text-[10px] text-slate-500">${{incoming.length}}</span>
            </div>
            <div class="space-y-1 max-h-36 overflow-y-auto">
              ${{incoming.length === 0 ? '<div class="text-[11px] text-slate-500 italic p-1">No upstream relationships</div>' :
                incoming.map(l => `
                  <div onclick="selectNodeById('${{l.sourceNode.id}}')" class="p-2 rounded bg-slate-950/40 hover:bg-slate-800 border border-slate-800/60 text-xs cursor-pointer transition flex items-center justify-between">
                    <span class="text-slate-300 truncate">${{l.sourceNode.label}}</span>
                    <span class="text-[10px] font-mono text-cyan-400">${{l.human_link_type || l.link_type}}</span>
                  </div>
                `).join('')}}
            </div>
          </div>

          <div class="space-y-1.5">
            <div class="text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center justify-between">
              <span>Downstream Blast Radius</span>
              <span class="font-mono text-[10px] text-slate-500">${{outgoing.length}}</span>
            </div>
            <div class="space-y-1 max-h-36 overflow-y-auto">
              ${{outgoing.length === 0 ? '<div class="text-[11px] text-slate-500 italic p-1">No downstream targets</div>' :
                outgoing.map(l => `
                  <div onclick="selectNodeById('${{l.targetNode.id}}')" class="p-2 rounded bg-slate-950/40 hover:bg-slate-800 border border-slate-800/60 text-xs cursor-pointer transition flex items-center justify-between">
                    <span class="text-slate-300 truncate">${{l.targetNode.label}}</span>
                    <span class="text-[10px] font-mono text-cyan-400">${{l.human_link_type || l.link_type}}</span>
                  </div>
                `).join('')}}
            </div>
          </div>
        </div>
      `;
    }}

    function selectNodeById(id) {{
      const n = nodes.find(node => node.id === id);
      if (n) {{
        activeDomains.add(n.domain);
        selectNode(n);
        camera.x = -n.x * camera.zoom;
        camera.y = -n.y * camera.zoom;
      }}
    }}

    function deselectNode() {{
      selectedNode = null;
      document.getElementById('insp-header-dot').style.backgroundColor = '#3b82f6';
      document.getElementById('insp-header-title').innerText = 'Entity Inspector';
      document.getElementById('inspectorContent').innerHTML = `
        <div class="text-center py-16 text-slate-500">
          <i class="fa-solid fa-arrow-pointer text-2xl mb-3 opacity-40"></i>
          <p class="text-xs max-w-xs mx-auto leading-relaxed">Select any entity on the knowledge canvas or pick an incident scenario to inspect active 3GPP alarm propagation, incoming root causes, and downstream impact.</p>
        </div>
      `;
    }}

    function handleSearch(query) {{
      const q = query.trim().toLowerCase();
      const clearBtn = document.getElementById('clearSearchBtn');
      if (q) clearBtn.classList.remove('hidden');
      else clearBtn.classList.add('hidden');

      if (!q) {{
        applyScenario(currentScenario.id);
        return;
      }}

      highlightedNodes.clear();
      nodes.forEach(n => {{
        if (n.label.toLowerCase().includes(q) || n.id.toLowerCase().includes(q) || n.domain.toLowerCase().includes(q)) {{
          highlightedNodes.add(n.id);
        }}
      }});

      const firstMatch = nodes.find(n => highlightedNodes.has(n.id));
      if (firstMatch) {{
        activeDomains.add(firstMatch.domain);
        camera.x = -firstMatch.x * camera.zoom;
        camera.y = -firstMatch.y * camera.zoom;
      }}
    }}

    function clearSearch() {{
      document.getElementById('searchInput').value = '';
      document.getElementById('clearSearchBtn').classList.add('hidden');
      applyScenario(currentScenario.id);
    }}

    function zoomIn() {{ camera.zoom = Math.min(3.5, camera.zoom * 1.25); }}
    function zoomOut() {{ camera.zoom = Math.max(0.2, camera.zoom * 0.8); }}
    function resetCamera() {{
      const activeNodeList = nodes.filter(n => activeDomains.has(n.domain));
      if (activeNodeList.length === 0) {{
        camera = {{ x: 0, y: 0, zoom: 0.85 }};
        return;
      }}
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      activeNodeList.forEach(n => {{
        if (n.x < minX) minX = n.x;
        if (n.x > maxX) maxX = n.x;
        if (n.y < minY) minY = n.y;
        if (n.y > maxY) maxY = n.y;
      }});
      const cx = (minX + maxX) / 2;
      const cy = (minY + maxY) / 2;
      const w = maxX - minX + 220;
      const h = maxY - minY + 220;
      const rect = canvas.getBoundingClientRect();
      const zoomX = (rect.width || 1000) / w;
      const zoomY = (rect.height || 700) / h;
      const optimalZoom = Math.max(0.35, Math.min(1.2, Math.min(zoomX, zoomY)));
      camera = {{ x: -cx * optimalZoom, y: -cy * optimalZoom, zoom: optimalZoom }};
    }}

    function togglePhysics() {{
      isPhysicsActive = !isPhysicsActive;
      const btn = document.getElementById('btn-physics');
      btn.innerHTML = isPhysicsActive ? '<i class="fa-solid fa-pause text-slate-400"></i> Pin Nodes' : '<i class="fa-solid fa-play text-slate-400"></i> Free Layout';
    }}

    function toggleLabels() {{
      showAllLabels = !showAllLabels;
      document.getElementById('btn-labels').classList.toggle('bg-blue-600', showAllLabels);
    }}

    initData();
    resizeCanvas();
    resetCamera();
    draw();
  </script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="FikraCore Knowledge Graph & Scenario Projection Builder")
    parser.add_argument("--repo-root", default=".", help="Root repository directory")
    parser.add_argument("--output", default="artifacts/telecom-knowledge-graph.html", help="Target output HTML file")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_path = Path(args.output).resolve()

    res = build_knowledge_graph(repo_root, output_path)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
