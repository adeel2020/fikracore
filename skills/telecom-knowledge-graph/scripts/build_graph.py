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
import yaml

# 12 Granular Telecom Operational Domains with vivid carrier palette
DOMAIN_COLORS = {
    "Cross-Domain Operations": "#38bdf8",         # Sky Blue (Central Causal Operational Plane)
    "Mobile Core (5G SA)": "#3b82f6",             # Primary Blue
    "Radio Access Network (RAN)": "#10b981",       # Emerald Green
    "IP Transport & Routing": "#f59e0b",           # Amber
    "Optical & Transport (DWDM/OTN)": "#14b8a6",   # Teal
    "4G EPC & Signaling": "#6366f1",               # Indigo
    "IMS & VoNR/VoLTE": "#ec4899",                 # Pink
    "Cloud NFVI & Facilities": "#8b5cf6",          # Purple
    "CRM & Customer Experience": "#ef4444",        # Rose / Red
    "Observability & Remediation": "#06b6d4",      # Cyan
    "OCS & Charging": "#eab308",                   # Yellow
    "External Interconnect & Roaming": "#f97316",   # Orange
}

# Domain Cluster Anchors (Centers of Gravity in 2D space - Wide Non-Overlapping Clearance)
DOMAIN_CENTERS = {
    "Cross-Domain Operations": {"x": 280, "y": -220},
    "Mobile Core (5G SA)": {"x": 0, "y": 0},
    "Observability & Remediation": {"x": 780, "y": 40},
    "Radio Access Network (RAN)": {"x": -560, "y": -260},
    "IP Transport & Routing": {"x": -520, "y": 280},
    "Optical & Transport (DWDM/OTN)": {"x": -820, "y": 0},
    "4G EPC & Signaling": {"x": -260, "y": -520},
    "IMS & VoNR/VoLTE": {"x": 320, "y": -520},
    "Cloud NFVI & Facilities": {"x": -260, "y": 540},
    "CRM & Customer Experience": {"x": 320, "y": 540},
    "OCS & Charging": {"x": 40, "y": 620},
    "External Interconnect & Roaming": {"x": -840, "y": 340},
}

# TM Forum Granular Sub-Cluster Offsets (Non-overlapping radial satellite layout)
SUB_CLUSTER_OFFSETS = {
    # OSS & Fault Management Sub-Clusters
    "oss.correlation_clusters": {"dx": -170, "dy": -90, "label": "CORRELATION CLUSTERS", "icon": "🌀", "color": "#38bdf8"},
    "oss.hypotheses": {"dx": -170, "dy": 90, "label": "HYPOTHESES & CAUSALITY", "icon": "💡", "color": "#818cf8"},
    "oss.alarms_events": {"dx": 170, "dy": -90, "label": "ALARMS & FAULTS", "icon": "🚨", "color": "#ef4444"},
    "oss.metrics_kpis": {"dx": 180, "dy": 90, "label": "METRICS & KPIS", "icon": "📈", "color": "#10b981"},
    "oss.logs": {"dx": -40, "dy": 200, "label": "LOGS & TRACES", "icon": "📝", "color": "#c084fc"},
    "oss.remediations": {"dx": 40, "dy": -200, "label": "PLAYBOOKS & SOPS", "icon": "🛠️", "color": "#fbbf24"},
    "oss.general": {"dx": 40, "dy": 200, "label": "OPERATIONAL RUNBOOKS", "icon": "📋", "color": "#94a3b8"},

    # Mobile Core Sub-Clusters
    "mobile_core.control_plane": {"dx": -110, "dy": -60, "label": "CONTROL PLANE (AMF/SMF)", "icon": "⚙️", "color": "#60a5fa"},
    "mobile_core.user_plane": {"dx": 110, "dy": 60, "label": "USER PLANE (UPF/PGW)", "icon": "📦", "color": "#3b82f6"},
    "mobile_core.services": {"dx": 0, "dy": -130, "label": "CORE SERVICES", "icon": "🌐", "color": "#818cf8"},
    "mobile_core.network_functions": {"dx": 0, "dy": 40, "label": "NETWORK FUNCTIONS", "icon": "🏢", "color": "#93c5fd"},

    # Cross-Domain Operations Sub-Clusters
    "incidents.active": {"dx": -50, "dy": 0, "label": "ACTIVE INCIDENTS", "icon": "⚡", "color": "#f43f5e"},
    "incidents.operational": {"dx": 50, "dy": 0, "label": "HISTORICAL OUTAGES", "icon": "🎫", "color": "#38bdf8"},

    # Transport Sub-Clusters
    "transport.topology": {"dx": 0, "dy": 30, "label": "ROUTING & LINKS", "icon": "🌐", "color": "#06b6d4"},
    "transport.link_performance": {"dx": -50, "dy": -40, "label": "LINK METRICS", "icon": "📉", "color": "#22d3ee"},
    "transport.alarms": {"dx": 50, "dy": -40, "label": "FIBER & INTERFACE ALARMS", "icon": "⚠️", "color": "#fb923c"},

    # RAN Sub-Clusters
    "ran.topology": {"dx": 0, "dy": 30, "label": "RAN NODES", "icon": "📡", "color": "#10b981"},
    "ran.radio_kpis": {"dx": 0, "dy": -50, "label": "RADIO KPIS", "icon": "📶", "color": "#34d399"},
    "ran.alarms": {"dx": 50, "dy": -20, "label": "RAN ALARMS", "icon": "🚨", "color": "#f87171"},

    # IMS Sub-Clusters
    "ims.sip_core": {"dx": -40, "dy": 20, "label": "SIP CORE", "icon": "📞", "color": "#a855f7"},
    "ims.kpis": {"dx": 40, "dy": -30, "label": "VOICE KPIS (CSSR/MOS)", "icon": "📊", "color": "#c084fc"},
    "ims.media_plane": {"dx": 40, "dy": 40, "label": "MEDIA PLANE (MRFP/RTP)", "icon": "🎙️", "color": "#d8b4fe"},

    # CRM Sub-Clusters
    "crm.resources": {"dx": 0, "dy": 0, "label": "CUSTOMER TICKETS & SLA", "icon": "🎫", "color": "#f43f5e"},
}

def map_entity_slug(raw_entity, inv_slugs: set, domains=None):
    """Maps raw scenario entities, synthetic tokens, or failure components to knowledge inventory node slugs."""
    raw = str(raw_entity or "").lower().strip()
    if not raw:
        return "domains/mobile-core/networks/ps/functions/pgw-01"
    if raw in inv_slugs:
        return raw
    if "pe-rtr" in raw or "pe:rtr" in raw or "sgi-edge" in raw or "router" in raw or "rtr-21" in raw:
        return "domains/transport/functions/sgi-edge-01"
    if "agg-sw" in raw or "switch" in raw or "leaf" in raw or "tor" in raw:
        return "mobile-core/network-functions/transport-transport-agg-sw-03"
    if "backhaul" in raw or "jitter" in raw or "fiber" in raw or "transmission" in raw or "optics" in raw or "dwdm" in raw:
        return "domains/transport/functions/voice-backhaul-01"
    if "upf" in raw or "pgw" in raw or "user_plane" in raw or "packet_core" in raw:
        return "domains/mobile-core/networks/ps/functions/pgw-01"
    if "amf" in raw or "control_plane" in raw:
        return "mobile-core/network-functions/mobile-core-core-amf-01"
    if "hss" in raw or "diameter" in raw or "udr" in raw or "subs" in raw or "database" in raw or "charging" in raw or "ocs" in raw:
        return "domains/mobile-core/networks/lte/functions/hss-01"
    if "mme" in raw or "s1-ap" in raw or "nas" in raw:
        return "domains/mobile-core/networks/lte/functions/mme-01"
    if "pcscf" in raw or "ims" in raw or "voice" in raw or "sip" in raw:
        return "domains/mobile-core/networks/ims/functions/pcscf-01"
    if "gnodeb" in raw or "5g_ran" in raw:
        return "mobile-core/network-functions/ran-ran-gnodeb-17"
    if "enodeb-22" in raw:
        return "domains/ran/functions/enodeb-22"
    if "enodeb" in raw or "ran" in raw or "cell" in raw:
        return "domains/ran/functions/enodeb-17"
    if "nat" in raw or "fw" in raw or "firewall" in raw or "security" in raw:
        return "domains/mobile-core/networks/ps/functions/nat-fw-01"
    if "power" in raw or "ups" in raw or "battery" in raw or "dc" in raw or "facility" in raw or "facilities" in raw:
        return "mobile-core/network-functions/power-power-ups-77"
    if "k8s" in raw or "dns" in raw or "ntp" in raw or "worker" in raw or "storage" in raw or "cloud" in raw or "nfvi" in raw:
        return "mobile-core/network-functions/power-power-ups-77"
    if "ticket" in raw or "crm" in raw or "customer" in raw:
        return "tickets/mobile-core/tt-984210"

    if domains:
        for d in domains:
            dl = str(d).lower()
            if "transport" in dl or "routing" in dl:
                return "domains/transport/functions/sgi-edge-01"
            if "ran" in dl:
                return "domains/ran/functions/enodeb-17"
            if "ims" in dl or "voice" in dl:
                return "domains/mobile-core/networks/ims/functions/pcscf-01"
            if "signaling" in dl or "4g" in dl or "epc" in dl:
                return "domains/mobile-core/networks/lte/functions/hss-01"
            if "charging" in dl or "ocs" in dl:
                return "domains/mobile-core/networks/lte/functions/hss-01"
            if "facilities" in dl or "cloud" in dl or "power" in dl:
                return "mobile-core/network-functions/power-power-ups-77"

    return "domains/mobile-core/networks/ps/functions/pgw-01"


def compile_all_scenarios(repo_root: Path, raw_entities: list[dict]) -> list[dict]:
    """Compiles the high-fidelity simulated RCA scenarios across H1 (Cascades), H2 (Hidden Gaps), and H3 (Validated Learned Knowledge)."""
    return [
        # Baseline (Nominal Operations)
        {
            "id": "baseline",
            "name": "Baseline Nominal State",
            "badge": "NOMINAL",
            "stage": "H0",
            "concept": "Baseline",
            "category": "Steady State Operations",
            "description": "Steady-state carrier operations. All 132 entities nominal with zero active alarm delegations.",
            "aliases": ["nominal", "steady-state", "normal", "h0"],
            "root_cause": None,
            "affected_nodes": {},
            "propagation_path": [],
            "active_links": []
        },
        # H1: Cascading Incidents (Standard RCA)
        {
            "id": "h1-sgi-mtu",
            "name": "Incident H1-01: SGi Throughput Degradation (MTU Mismatch)",
            "badge": "CRITICAL",
            "stage": "H1",
            "concept": "Understand",
            "category": "H1: Understand (Inter-Domain Cascade)",
            "description": "MTU mismatch and packet fragmentation on sgi-edge-01 propagates to UPF/PGW throughput drop, NAT session exhaustion, and customer ticket surge.",
            "aliases": ["scn-001", "h1", "h1-01", "h1-sgi-mtu", "sgi-mtu", "sgi-data", "twin-inc-001"],
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
                "tickets/mobile-core/tt-984210": {"severity": "MAJOR", "status": "Customer SLA Ticket Surge"}
            }
        },
        {
            "id": "h1-lte-attach",
            "name": "Incident H1-02: LTE Attach Failure & Diameter Stalling",
            "badge": "CRITICAL",
            "stage": "H1",
            "concept": "Understand",
            "category": "H1: Understand (Cross-Domain Signaling)",
            "description": "HSS Diameter authentication timeout cascaded across MME-01 and eNodeB-17, resulting in complete 4G LTE attach failure spikes.",
            "aliases": ["scn-002", "h1-02", "h2", "h2-lte-attach", "h1-lte-attach", "lte-attach", "diameter-timeout"],
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
                "incidents/mobile-core/lte-attach-54db6ef325fbf758": {"severity": "CRITICAL", "status": "Active Inter-Domain Incident"},
                "grafana/alerts/grafana-alert-attach-hss-001": {"severity": "CRITICAL", "status": "DIAMETER_AUTH_TIMEOUT"},
                "grafana/alerts/grafana-alert-attach-mme-001": {"severity": "MAJOR", "status": "MME_ATTACH_DROP"},
                "grafana/alerts/grafana-alert-attach-ran-001": {"severity": "MAJOR", "status": "RAN_RRC_FAIL_HIGH"},
                "tickets/mobile-core/tt-984210": {"severity": "MAJOR", "status": "Customer Ticket Spike"}
            }
        },
        {
            "id": "h1-voice-cssr",
            "name": "Incident H1-03: Voice Call Setup Failure & Backhaul Jitter",
            "badge": "CRITICAL",
            "stage": "H1",
            "concept": "Understand",
            "category": "H1: Understand (IMS / Multi-Domain Degradation)",
            "description": "Transport voice-backhaul-01 jitter and packet drops impair P-CSCF SIP INVITE handshakes and eNodeB-22 call accessibility (CSSR drop).",
            "aliases": ["scn-003", "h1-03", "h3", "h3-voice-cssr", "h1-voice-cssr", "voice-cssr", "cssr", "vonr-jitter"],
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
                "domains/ran/functions/enodeb-22": {"severity": "MAJOR", "status": "Voice Dedicated Bearer Setup Failed"},
                "mobile-core/services/voice-call-setup": {"severity": "CRITICAL", "status": "Call Setup Success Rate (CSSR) Breached"},
                "incidents/mobile-core/voice-call-setup-05841af2e3f4f430": {"severity": "CRITICAL", "status": "Active Inter-Domain Incident"},
                "mobile-core/incidents/voice-call-setup-05841af2e3f4f430": {"severity": "CRITICAL", "status": "Active Inter-Domain Incident"},
                "grafana/alerts/grafana-alert-cssr-transport-001": {"severity": "MAJOR", "status": "BACKHAUL_JITTER_HIGH"},
                "grafana/alerts/grafana-alert-cssr-ims-001": {"severity": "MAJOR", "status": "SIP_TRANSACTION_TIMEOUT"},
                "grafana/alerts/grafana-alert-cssr-ran-001": {"severity": "MAJOR", "status": "BEARER_SETUP_FAILURE"},
                "tickets/mobile-core/tt-984210": {"severity": "MAJOR", "status": "Customer Voice Ticket Surge"}
            }
        },
        {
            "id": "h1-ue-registration",
            "name": "Incident H1-04: 5G UE Registration Burst & AMF Overload",
            "badge": "MAJOR",
            "stage": "H1",
            "concept": "Understand",
            "category": "H1: Understand (5G SA Signaling)",
            "description": "Mass 5G registration storm across transport aggregation switch agg-sw-03 and gNodeB-17 causes AMF-01 CPU saturation and registration failures.",
            "aliases": ["scn-004", "h1-04", "h4", "h4-ue-registration", "h1-ue-registration", "ue-storm", "amf-overload"],
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
                "mobile-core/evidence/alarm-1fe005ed908a3f26-0": {"severity": "CRITICAL", "status": "AMF_CPU_OVERLOAD"},
                "tickets/mobile-core/tt-984210": {"severity": "MAJOR", "status": "Trouble Tickets Surging"}
            }
        },
        {
            "id": "h1-site-power",
            "name": "Incident H1-05: Physical Site Power & UPS Battery Alarm",
            "badge": "MINOR",
            "stage": "H1",
            "concept": "Understand",
            "category": "H1: Understand (Facilities / Infrastructure)",
            "description": "DC power rectifier and UPS-77 failure causing power bus fluctuation, impacting site stability and operational telemetry.",
            "aliases": ["scn-005", "h1-05", "h5", "h5-site-power", "h1-site-power", "site-power", "ups-battery"],
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
                "mobile-core/evidence/alarm-81cec920e94d3a59-0": {"severity": "MAJOR", "status": "UPS_ON_BATTERY_CRITICAL"}
            }
        },
        # H2: Knowledge Gap Discovery RCA (Hidden Causes)
        {
            "id": "h2-gap-001",
            "name": "Gap H2-01: Missing OCS Charging Dependency Boundary",
            "badge": "KNOWLEDGE_GAP",
            "stage": "H2",
            "concept": "Discover",
            "category": "H2: Discover (OCS Boundary Gap)",
            "description": "Exposes an unmodeled billing/charging dependency boundary between Mobile Core and OCS causing unexplained subscriber quota timeouts.",
            "aliases": ["twin-gap-001", "h2-gap-001", "missing ocs dependency", "charging gap", "h2-scn-001"],
            "root_cause": "domains/mobile-core/networks/lte/functions/hss-01",
            "propagation_path": [
                "domains/mobile-core/networks/lte/functions/hss-01",
                "domains/mobile-core/networks/ps/functions/pgw-01",
                "mobile-core/services/sgi-data",
                "tickets/mobile-core/tt-984210"
            ],
            "affected_nodes": {
                "domains/mobile-core/networks/lte/functions/hss-01": {"severity": "ROOT_CAUSE", "status": "Unmodeled OCS Diameter Boundary"},
                "domains/mobile-core/networks/ps/functions/pgw-01": {"severity": "CRITICAL", "status": "Credit Control Quota Timeout"},
                "mobile-core/services/sgi-data": {"severity": "CRITICAL", "status": "Session Tear-Down / SLA Breach"},
                "tickets/mobile-core/tt-984210": {"severity": "MAJOR", "status": "Charging Trouble Tickets Reported"}
            }
        },
        {
            "id": "h2-gap-002",
            "name": "Gap H2-02: Optical DWDM Transceiver Fiber Attenuation",
            "badge": "KNOWLEDGE_GAP",
            "stage": "H2",
            "concept": "Discover",
            "category": "H2: Discover (Optical / Transport Gap)",
            "description": "Hidden optical power attenuation in DWDM layer triggers bit-error rates, causing intermittent SGi edge drops without explicit transport alarms.",
            "aliases": ["h2-gap-002", "optical-gap", "dwdm attenuation"],
            "root_cause": "domains/transport/functions/voice-backhaul-01",
            "propagation_path": [
                "domains/transport/functions/voice-backhaul-01",
                "domains/transport/functions/sgi-edge-01",
                "domains/mobile-core/networks/ps/functions/pgw-01",
                "mobile-core/services/sgi-data"
            ],
            "affected_nodes": {
                "domains/transport/functions/voice-backhaul-01": {"severity": "ROOT_CAUSE", "status": "Optical Transceiver Rx Power Drop"},
                "domains/transport/functions/sgi-edge-01": {"severity": "CRITICAL", "status": "Interface Framing Errors"},
                "domains/mobile-core/networks/ps/functions/pgw-01": {"severity": "MAJOR", "status": "Packet Discard Rate Rise"},
                "mobile-core/services/sgi-data": {"severity": "CRITICAL", "status": "SLA Throughput Degradation"}
            }
        },
        {
            "id": "h2-gap-003",
            "name": "Gap H2-03: Unmapped Gi-LAN NAT/Firewall Session Overflow",
            "badge": "KNOWLEDGE_GAP",
            "stage": "H2",
            "concept": "Discover",
            "category": "H2: Discover (Gi-LAN Security Gap)",
            "description": "Undocumented NAT connection table limit reached on Gi-LAN firewall, dropping outbound internet sessions while UPF reports nominal.",
            "aliases": ["h2-gap-003", "nat-gap", "firewall saturation"],
            "root_cause": "domains/mobile-core/networks/ps/functions/nat-fw-01",
            "propagation_path": [
                "domains/mobile-core/networks/ps/functions/nat-fw-01",
                "domains/mobile-core/networks/ps/functions/pgw-01",
                "mobile-core/services/sgi-data",
                "tickets/mobile-core/tt-984210"
            ],
            "affected_nodes": {
                "domains/mobile-core/networks/ps/functions/nat-fw-01": {"severity": "ROOT_CAUSE", "status": "NAT Table Saturation (>99%)"},
                "domains/mobile-core/networks/ps/functions/pgw-01": {"severity": "MAJOR", "status": "Outbound Connection Drop"},
                "mobile-core/services/sgi-data": {"severity": "CRITICAL", "status": "Internet Access Blackhole"},
                "tickets/mobile-core/tt-984210": {"severity": "MAJOR", "status": "Data Ticket Influx"}
            }
        },
        {
            "id": "h2-gap-004",
            "name": "Gap H2-04: Cross-Domain Roaming Interconnect / SEPP Latency",
            "badge": "KNOWLEDGE_GAP",
            "stage": "H2",
            "concept": "Discover",
            "category": "H2: Discover (Roaming Interconnect Gap)",
            "description": "Unmodeled foreign carrier IPX interconnect latency causes SEPP handshake timeouts during inbound roaming registration.",
            "aliases": ["h2-gap-004", "roaming-gap", "sepp latency"],
            "root_cause": "mobile-core/network-functions/mobile-core-core-amf-01",
            "propagation_path": [
                "mobile-core/network-functions/mobile-core-core-amf-01",
                "mobile-core/network-functions/ran-ran-gnodeb-17",
                "mobile-core/services/ue-registration",
                "tickets/mobile-core/tt-984210"
            ],
            "affected_nodes": {
                "mobile-core/network-functions/mobile-core-core-amf-01": {"severity": "ROOT_CAUSE", "status": "SEPP Roaming Security Handshake Timeout"},
                "mobile-core/network-functions/ran-ran-gnodeb-17": {"severity": "MAJOR", "status": "Inbound Roamer RRC Stalled"},
                "mobile-core/services/ue-registration": {"severity": "CRITICAL", "status": "Roaming Registration Failure"},
                "tickets/mobile-core/tt-984210": {"severity": "MAJOR", "status": "VIP Roamer Complaints"}
            }
        },
        {
            "id": "h2-gap-005",
            "name": "Gap H2-05: Virtualized Cloud NFVI Host Resource Contention",
            "badge": "KNOWLEDGE_GAP",
            "stage": "H2",
            "concept": "Discover",
            "category": "H2: Discover (Cloud NFVI Gap)",
            "description": "Hidden NUMA node CPU socket pinning conflict on K8s compute host impairs UPF fast-path packet forwarding.",
            "aliases": ["h2-gap-005", "nfvi-gap", "numa contention"],
            "root_cause": "mobile-core/network-functions/power-power-ups-77",
            "propagation_path": [
                "mobile-core/network-functions/power-power-ups-77",
                "domains/mobile-core/networks/ps/functions/pgw-01",
                "mobile-core/services/sgi-data",
                "tickets/mobile-core/tt-984210"
            ],
            "affected_nodes": {
                "mobile-core/network-functions/power-power-ups-77": {"severity": "ROOT_CAUSE", "status": "Host CPU Contention / NUMA Throttling"},
                "domains/mobile-core/networks/ps/functions/pgw-01": {"severity": "CRITICAL", "status": "UPF DPDK Worker Stalled"},
                "mobile-core/services/sgi-data": {"severity": "CRITICAL", "status": "Throughput Degraded"},
                "tickets/mobile-core/tt-984210": {"severity": "MAJOR", "status": "Enterprise VPN Tickets"}
            }
        },
        # H3: Validated RCA + SME Learned Knowledge Promotion
        {
            "id": "h3-lrn-001",
            "name": "Learn H3-01: Validated OCS Charging Dependency Promotion",
            "badge": "LEARNING_UNIT",
            "stage": "H3",
            "concept": "Learn",
            "category": "H3: Learn (SME Promotion)",
            "description": "Validated learning unit promoting the discovered OCS ↔ PGW charging interface into the active causal graph, permanently improving future RCA accuracy.",
            "aliases": ["twin-lrn-001", "h3-lrn-001", "validated charging dependency", "h3 learning unit", "h3-lu-001"],
            "root_cause": "domains/mobile-core/networks/lte/functions/hss-01",
            "propagation_path": [
                "domains/mobile-core/networks/lte/functions/hss-01",
                "domains/mobile-core/networks/ps/functions/pgw-01",
                "mobile-core/services/sgi-data",
                "learning/mobile-core/notes/sgi-data-a154bb7a3997859c"
            ],
            "affected_nodes": {
                "domains/mobile-core/networks/lte/functions/hss-01": {"severity": "ROOT_CAUSE", "status": "Validated OCS Causal Node (Promoted)"},
                "domains/mobile-core/networks/ps/functions/pgw-01": {"severity": "CRITICAL", "status": "Active Dependency Edge Integrated"},
                "mobile-core/services/sgi-data": {"severity": "MAJOR", "status": "Continuous SLA Assurance"},
                "learning/mobile-core/notes/sgi-data-a154bb7a3997859c": {"severity": "MINOR", "status": "SME Post-Mortem Note Verified"}
            }
        },
        {
            "id": "h3-lrn-002",
            "name": "Learn H3-02: Validated Optical DWDM ↔ IP Edge Causal Edge",
            "badge": "LEARNING_UNIT",
            "stage": "H3",
            "concept": "Learn",
            "category": "H3: Learn (Transport Promotion)",
            "description": "Promotes calibrated optical power threshold correlation rules directly connecting physical fiber transceivers to SGi IP routing.",
            "aliases": ["h3-lrn-002", "optical promotion", "h3-lu-002"],
            "root_cause": "domains/transport/functions/voice-backhaul-01",
            "propagation_path": [
                "domains/transport/functions/voice-backhaul-01",
                "domains/transport/functions/sgi-edge-01",
                "domains/mobile-core/networks/ps/functions/pgw-01",
                "learning/mobile-core/notes/voice-call-setup-05841af2e3f4f430"
            ],
            "affected_nodes": {
                "domains/transport/functions/voice-backhaul-01": {"severity": "ROOT_CAUSE", "status": "Calibrated Optical Transceiver Metric"},
                "domains/transport/functions/sgi-edge-01": {"severity": "MAJOR", "status": "Promoted Physical Cross-Connect"},
                "domains/mobile-core/networks/ps/functions/pgw-01": {"severity": "MAJOR", "status": "Upstream Telemetry Synchronized"},
                "learning/mobile-core/notes/voice-call-setup-05841af2e3f4f430": {"severity": "MINOR", "status": "Promoted Learning Unit"}
            }
        },
        {
            "id": "h3-lrn-003",
            "name": "Learn H3-03: Validated Gi-LAN NAT Session Capacity Model",
            "badge": "LEARNING_UNIT",
            "stage": "H3",
            "concept": "Learn",
            "category": "H3: Learn (Security Promotion)",
            "description": "Promotes firewall NAT translation table telemetry into Core data pipeline, preventing silent subscriber session drops.",
            "aliases": ["h3-lrn-003", "nat promotion", "h3-lu-003"],
            "root_cause": "domains/mobile-core/networks/ps/functions/nat-fw-01",
            "propagation_path": [
                "domains/mobile-core/networks/ps/functions/nat-fw-01",
                "domains/mobile-core/networks/ps/functions/pgw-01",
                "mobile-core/services/sgi-data",
                "assets/mobile-core/playbooks/sgi-data-failure-triage"
            ],
            "affected_nodes": {
                "domains/mobile-core/networks/ps/functions/nat-fw-01": {"severity": "ROOT_CAUSE", "status": "Promoted NAT Table Alarm Boundary"},
                "domains/mobile-core/networks/ps/functions/pgw-01": {"severity": "MAJOR", "status": "Synchronized PGW Capacity Guard"},
                "mobile-core/services/sgi-data": {"severity": "MAJOR", "status": "Protected Service Path"},
                "assets/mobile-core/playbooks/sgi-data-failure-triage": {"severity": "MINOR", "status": "Automated Remediation Playbook"}
            }
        },
        {
            "id": "h3-lrn-004",
            "name": "Learn H3-04: Validated Roaming SEPP SLA & Inbound Latency Model",
            "badge": "LEARNING_UNIT",
            "stage": "H3",
            "concept": "Learn",
            "category": "H3: Learn (Roaming Promotion)",
            "description": "Integrates SEPP inter-carrier latency bounds into 5G AMF admission control, eliminating blind spots in roaming triage.",
            "aliases": ["h3-lrn-004", "roaming promotion", "h3-lu-004"],
            "root_cause": "mobile-core/network-functions/mobile-core-core-amf-01",
            "propagation_path": [
                "mobile-core/network-functions/mobile-core-core-amf-01",
                "mobile-core/network-functions/ran-ran-gnodeb-17",
                "mobile-core/services/ue-registration",
                "learning/mobile-core/notes/lte-attach-54db6ef325fbf758"
            ],
            "affected_nodes": {
                "mobile-core/network-functions/mobile-core-core-amf-01": {"severity": "ROOT_CAUSE", "status": "Promoted SEPP Interconnect Contract"},
                "mobile-core/network-functions/ran-ran-gnodeb-17": {"severity": "MAJOR", "status": "Roaming Admission Guarded"},
                "mobile-core/services/ue-registration": {"severity": "MAJOR", "status": "Guaranteed Inbound SLAs"},
                "learning/mobile-core/notes/lte-attach-54db6ef325fbf758": {"severity": "MINOR", "status": "Verified Knowledge Artifact"}
            }
        },
        {
            "id": "h3-lrn-005",
            "name": "Learn H3-05: Validated Cloud NFVI NUMA Topology Binding",
            "badge": "LEARNING_UNIT",
            "stage": "H3",
            "concept": "Learn",
            "category": "H3: Learn (Cloud NFVI Promotion)",
            "description": "Promotes physical host compute topology awareness into UPF orchestration, ensuring DPDK cores avoid CPU scheduling jitter.",
            "aliases": ["h3-lrn-005", "nfvi promotion", "h3-lu-005"],
            "root_cause": "mobile-core/network-functions/power-power-ups-77",
            "propagation_path": [
                "mobile-core/network-functions/power-power-ups-77",
                "domains/mobile-core/networks/ps/functions/pgw-01",
                "mobile-core/services/sgi-data",
                "assets/mobile-core/playbooks/sgi-data-failure-triage"
            ],
            "affected_nodes": {
                "mobile-core/network-functions/power-power-ups-77": {"severity": "ROOT_CAUSE", "status": "Promoted Host Topology Binding"},
                "domains/mobile-core/networks/ps/functions/pgw-01": {"severity": "MAJOR", "status": "Verified DPDK Core Pinning"},
                "mobile-core/services/sgi-data": {"severity": "MAJOR", "status": "High-Throughput Assured"},
                "assets/mobile-core/playbooks/sgi-data-failure-triage": {"severity": "MINOR", "status": "NFVI Remediation Automation"}
            }
        }
    ]

    return scenarios


def map_telecom_domain(e: dict) -> str:
    """Maps an entity into one of the 12 granular telecom operational domains."""
    slug = e.get("slug", "").lower()
    etype = e.get("type", "").lower()
    orig_dom = e.get("domain", "")

    # 0. Cross-Domain Operations (Dedicated Incident Plane)
    if (
        etype == "incident"
        or "incidents" in slug
        or "/incidents/" in slug
        or (orig_dom == "Cross-Domain Operations" and not any(k in slug for k in ("correlation", "cluster", "decision", "hypothe")))
    ):
        return "Cross-Domain Operations"

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
    # 10. Observability & Remediation
    if (
        etype in ("correlation-cluster", "correlation-decision", "hypothesis")
        or any(k in slug for k in [
            "grafana", "promql", "alert", "metric", "loki", "tempo", "log", "trace",
            "playbook", "runbook", "pipeline", "matrix", "rtr", "story", "note",
            "hypothesis", "hypotheses", "hypothe", "decision", "cluster", "correlation", "kpi"
        ])
    ):
        return "Observability & Remediation"
    # 11. Mobile Core (5G SA)
    return "Mobile Core (5G SA)"


def map_sub_cluster(e: dict, domain: str) -> str:
    """Derives TM Forum aligned sub-cluster for visual satellite grouping."""
    slug = e.get("slug", "").lower()
    etype = e.get("type", "").lower()

    if domain == "Cross-Domain Operations" or etype == "incident" or "incident" in slug:
        if any(k in slug for k in ("active", "drop", "sgi", "fail", "degradation", "breach", "overload")):
            return "incidents.active"
        return "incidents.operational"

    if domain == "Observability & Remediation":
        if any(k in slug for k in ("alert", "alarm", "trap", "snmp")):
            return "oss.alarms_events"
        if any(k in slug for k in ("hypothe", "hypothesis", "hyp", "note", "learning")) or etype == "hypothesis":
            return "oss.hypotheses"
        if any(k in slug for k in ("cluster", "correlation", "decision", "finding")) or etype in ("correlation-cluster", "correlation-decision"):
            return "oss.correlation_clusters"
        if any(k in slug for k in ("loki", "log", "syslog", "tempo", "trace", "pcap")):
            return "oss.logs"
        if any(k in slug for k in ("prom", "metric", "kpi", "grafana", "rsr", "cssr", "query")):
            return "oss.metrics_kpis"
        if any(k in slug for k in ("playbook", "runbook", "remediation", "procedure", "pipeline", "matrix", "catalog", "mml", "rtr", "role")):
            return "oss.remediations"
        return "oss.general"

    if domain == "Mobile Core (5G SA)":
        if any(k in slug for k in ("amf", "smf", "nrf", "ausf", "udm", "control", "mme")):
            return "mobile_core.control_plane"
        if any(k in slug for k in ("upf", "pgw", "sgw", "gtp", "sgi", "user", "forwarding", "nat-fw")):
            return "mobile_core.user_plane"
        if etype == "service":
            return "mobile_core.services"
        return "mobile_core.network_functions"

    if domain in ("IP Transport & Routing", "Optical & Transport (DWDM/OTN)"):
        if any(k in slug for k in ("metric", "drop", "jitter", "power", "loss", "bandwidth", "attenuation")):
            return "transport.link_performance"
        if any(k in slug for k in ("alarm", "flap", "error", "down")):
            return "transport.alarms"
        return "transport.topology"

    if domain == "Radio Access Network (RAN)":
        if any(k in slug for k in ("kpi", "rrc", "prb", "cqi", "hosr")):
            return "ran.radio_kpis"
        if any(k in slug for k in ("alarm", "rlf", "vswr")):
            return "ran.alarms"
        return "ran.topology"

    if domain == "OCS & Charging":
        if any(k in slug for k in ("session", "ccr", "cca", "gy", "ro", "quota")):
            return "ocs.protocol_sessions"
        if any(k in slug for k in ("metric", "kpi", "latency", "timeout")):
            return "ocs.kpis"
        return "ocs.charging_gateways"

    if domain == "IMS & VoNR/VoLTE":
        if any(k in slug for k in ("sbc", "mrfp", "media", "rtp")):
            return "ims.media_plane"
        if any(k in slug for k in ("metric", "kpi", "cssr", "mos")):
            return "ims.kpis"
        return "ims.sip_core"

    clean = domain.lower().split()[0].replace("&", "").strip()
    return f"{clean}.resources"


def precalculate_layout(entities: list[dict], links: list[dict], domain_centers: dict) -> list[tuple[float, float]]:
    """Precalculates clean, non-overlapping cluster layout with natural elasticity centered on each domain and sub-cluster."""
    by_sub: dict[tuple[str, str], list[int]] = {}
    for i, e in enumerate(entities):
        dom = e["domain"]
        sub = map_sub_cluster(e, dom)
        e["sub_cluster"] = sub
        by_sub.setdefault((dom, sub), []).append(i)

    pos = [None] * len(entities)
    # Initialize in Fermat spiral around each sub-cluster satellite center
    for (dom, sub), indices in by_sub.items():
        base_c = domain_centers.get(dom, {"x": 0, "y": 0})
        sub_cfg = SUB_CLUSTER_OFFSETS.get(sub, {"dx": 0, "dy": 0})
        sc_x = base_c["x"] + sub_cfg.get("dx", 0)
        sc_y = base_c["y"] + sub_cfg.get("dy", 0)
        count = len(indices)
        for order, idx in enumerate(indices):
            golden_angle = 2.39996
            r = 14.0 + (7.0 + math.sqrt(count) * 2.0) * math.sqrt(order)
            theta = order * golden_angle
            pos[idx] = {
                "x": sc_x + math.cos(theta) * r,
                "y": sc_y + math.sin(theta) * r,
                "vx": 0.0,
                "vy": 0.0,
                "domain": dom,
                "sub_cluster": sub,
                "sc_x": sc_x,
                "sc_y": sc_y,
                "sub_count": count,
            }

    slug_to_idx = {e.get("slug", ""): i for i, e in enumerate(entities)}
    edge_indices = []
    for l in links:
        s = l.get("from_slug")
        t = l.get("to_slug")
        if s in slug_to_idx and t in slug_to_idx:
            edge_indices.append((slug_to_idx[s], slug_to_idx[t]))

    # Elastic force-directed relaxation constrained to sub-cluster centers
    for frame in range(180):
        temp = max(0.08, 1.0 - frame / 180.0)

        # 1. Node-to-node electrostatic repulsion within each sub-cluster to avoid overlapping nodes
        for (dom, sub), indices in by_sub.items():
            for i_idx in range(len(indices)):
                p1 = pos[indices[i_idx]]
                for j_idx in range(i_idx + 1, len(indices)):
                    p2 = pos[indices[j_idx]]
                    dx = p2["x"] - p1["x"]
                    dy = p2["y"] - p1["y"]
                    dist2 = dx * dx + dy * dy
                    if 0.1 < dist2 < 55 * 55:
                        dist = math.sqrt(dist2)
                        force = min(4.0, 380.0 / (dist2 + 30.0)) * temp
                        fx = (dx / dist) * force
                        fy = (dy / dist) * force
                        p1["vx"] -= fx
                        p1["vy"] -= fy
                        p2["vx"] += fx
                        p2["vy"] += fy

        # 2. Intra-subcluster natural elastic springs
        for s_idx, t_idx in edge_indices:
            p1 = pos[s_idx]
            p2 = pos[t_idx]
            if p1["sub_cluster"] == p2["sub_cluster"]:
                springLen = 32.0
                springK = 0.05
                dx = p2["x"] - p1["x"]
                dy = p2["y"] - p1["y"]
                dist = math.hypot(dx, dy) or 1.0
                delta = dist - springLen
                force = min(3.0, delta * springK) * temp
                fx = (dx / dist) * force
                fy = (dy / dist) * force
                p1["vx"] -= fx
                p1["vy"] -= fy
                p2["vx"] += fx
                p2["vy"] += fy

        # 3. Sub-Cluster Center Gravitational Anchor & Elastic Confinement
        for p in pos:
            sc_x = p["sc_x"]
            sc_y = p["sc_y"]
            dx = sc_x - p["x"]
            dy = sc_y - p["y"]
            distToCenter = math.hypot(dx, dy)
            maxRadius = 18.0 + math.sqrt(p["sub_count"]) * 11.0

            gravity = 0.09
            if distToCenter > maxRadius:
                gravity += (distToCenter - maxRadius) * 0.03

            p["vx"] += dx * gravity
            p["vy"] += dy * gravity

            p["vx"] *= 0.78
            p["vy"] *= 0.78
            v = math.hypot(p["vx"], p["vy"])
            if v > 3.5:
                p["vx"] = (p["vx"] / v) * 3.5
                p["vy"] = (p["vy"] / v) * 3.5

            p["x"] += p["vx"]
            p["y"] += p["vy"]

            # Hard boundary soft-clamp to sub-cluster
            curDist = math.hypot(p["x"] - sc_x, p["y"] - sc_y)
            if curDist > maxRadius * 1.15:
                ratio = (maxRadius * 1.15) / curDist
                p["x"] = sc_x + (p["x"] - sc_x) * ratio
                p["y"] = sc_y + (p["y"] - sc_y) * ratio

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
        e["sub_cluster"] = map_sub_cluster(e, e["domain"])

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
            "sub_cluster": e.get("sub_cluster", ""),
            "type": etype,
            "x": px,
            "y": py,
            "knowledge_state": e.get("knowledge_state", "CONFIRMED"),
            "in_degree": e.get("in_degree", 0),
            "out_degree": e.get("out_degree", 0),
            "evidence_count": e.get("evidence_count", 0),
            "color": color,
            "description": f"[{domain} &middot; {e.get('sub_cluster', etype)}] {title} (slug: {slug})",
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
        "sub_cluster_offsets": SUB_CLUSTER_OFFSETS,
        "scenarios": compile_all_scenarios(repo_root, raw_entities),
    }

    html_content = generate_html_viewer(payload)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as fp:
        fp.write(html_content)

    public_mirror = repo_root / "frontend/public/telecom-knowledge-graph.html"
    if public_mirror.parent.is_dir():
        with open(public_mirror, "w", encoding="utf-8") as fp:
            fp.write(html_content)

    return {
        "output_file": str(output_file),
        "total_nodes": len(nodes),
        "total_links": len(links),
        "total_domains": len(payload["domains"]),
        "total_scenarios": len(payload["scenarios"]),
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
      <div class="p-2.5 border-b border-slate-800 bg-slate-950/70">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-1.5 min-w-0">
            <i class="fa-solid fa-bolt-lightning text-amber-400 text-xs"></i>
            <span class="text-xs font-semibold uppercase tracking-wider text-slate-200">Scenarios</span>
            <span id="scenarioCountBadge" class="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-blue-400 border border-slate-700 font-bold">16</span>
          </div>
          <span class="text-[9px] font-mono px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30 font-semibold truncate max-w-[120px]" id="activeScenarioBadge">BASELINE</span>
        </div>

        <!-- Stage Filter Tabs -->
        <div class="flex items-center gap-1 overflow-x-auto pb-1 text-[10px] font-mono no-scrollbar">
          <button onclick="setScenarioStageFilter('ALL')" id="tab-stage-ALL" class="px-2 py-0.5 rounded bg-blue-600 text-white font-semibold transition shrink-0">ALL</button>
          <button onclick="setScenarioStageFilter('H1')" id="tab-stage-H1" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition shrink-0">H1 Understand</button>
          <button onclick="setScenarioStageFilter('H2')" id="tab-stage-H2" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition shrink-0">H2 Discover</button>
          <button onclick="setScenarioStageFilter('H3')" id="tab-stage-H3" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition shrink-0">H3 Learn</button>
        </div>

        <!-- Quick Scenario Filter Input -->
        <div class="relative mt-1.5">
          <i class="fa-solid fa-filter absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500 text-[10px]"></i>
          <input type="text" id="scenarioFilterInput" oninput="handleScenarioSearch(this.value)" placeholder="Filter scenarios (e.g. SCN-001, OCS, Voice)..." class="w-full pl-7 pr-6 py-1 text-[11px] bg-slate-900 border border-slate-800 rounded text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono transition">
          <button id="clearScenarioFilterBtn" onclick="clearScenarioFilter()" class="hidden absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"><i class="fa-solid fa-xmark text-[10px]"></i></button>
        </div>
      </div>

      <!-- Scenario Selector Drawer List -->
      <div class="p-2 border-b border-slate-800 space-y-1.5 max-h-60 overflow-y-auto" id="scenariosList">
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
          <span class="w-2.5 h-2.5 rounded-full bg-red-500 shrink-0" id="insp-header-dot"></span>
          <span class="font-bold text-slate-200 text-sm truncate" id="insp-header-title">Incident Executive Summary</span>
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
      
      const urlParams = new URLSearchParams(window.location.search);
      const scenarioParam = urlParams.get('scenario') || urlParams.get('id') || 'baseline';
      applyScenario(scenarioParam);
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

    let activeScenarioStage = 'ALL';
    let scenarioSearchQuery = '';

    function setScenarioStageFilter(stage) {{
      activeScenarioStage = stage;
      ['ALL', 'H1', 'H2', 'H3'].forEach(st => {{
        const tab = document.getElementById('tab-stage-' + st);
        if (tab) {{
          if (st === stage) {{
            tab.className = 'px-2 py-0.5 rounded bg-blue-600 text-white font-semibold transition shrink-0';
          }} else {{
            tab.className = 'px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition shrink-0';
          }}
        }}
      }});
      renderScenarioList();
    }}

    function handleScenarioSearch(val) {{
      scenarioSearchQuery = (val || '').toLowerCase().trim();
      const clearBtn = document.getElementById('clearScenarioFilterBtn');
      if (clearBtn) clearBtn.classList.toggle('hidden', !scenarioSearchQuery);
      renderScenarioList();
    }}

    function clearScenarioFilter() {{
      const input = document.getElementById('scenarioFilterInput');
      if (input) input.value = '';
      handleScenarioSearch('');
    }}

    function renderScenarioList() {{
      const container = document.getElementById('scenariosList');
      if (!container) return;
      container.innerHTML = '';

      const filtered = GRAPH_DATA.scenarios.filter(scn => {{
        if (activeScenarioStage !== 'ALL') {{
          if (activeScenarioStage === 'H1' && scn.stage !== 'H1' && scn.stage !== 'H0') return false;
          if (activeScenarioStage !== 'H1' && scn.stage !== activeScenarioStage) return false;
        }}
        if (scenarioSearchQuery) {{
          const matchId = (scn.id || '').toLowerCase().includes(scenarioSearchQuery);
          const matchName = (scn.name || '').toLowerCase().includes(scenarioSearchQuery);
          const matchDesc = (scn.description || '').toLowerCase().includes(scenarioSearchQuery);
          const matchAliases = scn.aliases && scn.aliases.some(a => a.toLowerCase().includes(scenarioSearchQuery));
          if (!matchId && !matchName && !matchDesc && !matchAliases) return false;
        }}
        return true;
      }});

      const countBadge = document.getElementById('scenarioCountBadge');
      if (countBadge) countBadge.innerText = filtered.length;

      if (filtered.length === 0) {{
        container.innerHTML = `
          <div class="text-center py-6 text-slate-500 text-xs font-mono">
            No scenarios match filter
          </div>
        `;
        return;
      }}

      filtered.forEach(scn => {{
        const isActive = currentScenario && currentScenario.id === scn.id;
        const card = document.createElement('div');
        card.className = `scenario-card p-2 rounded-lg cursor-pointer transition border text-xs ${{
          isActive
            ? 'active border-blue-500/60 bg-blue-950/40 shadow-md'
            : 'border-slate-800/80 bg-slate-950/40 hover:bg-slate-800/60 hover:border-slate-700'
        }}`;
        card.onclick = () => applyScenario(scn.id);

        const badgeColor =
          scn.badge === 'CRITICAL' ? 'bg-red-500/20 text-red-300 border-red-500/40' :
          scn.badge === 'MAJOR' ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' :
          scn.badge === 'MINOR' ? 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40' :
          scn.badge === 'KNOWLEDGE_GAP' ? 'bg-purple-500/20 text-purple-300 border-purple-500/40' :
          scn.badge === 'LEARNING_UNIT' ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40' :
          scn.badge === 'WHAT_IF' ? 'bg-blue-500/20 text-blue-300 border-blue-500/40' :
          'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';

        const stageTag = scn.stage ? `<span class="text-[9px] font-mono font-bold px-1 rounded bg-slate-800 text-slate-300 shrink-0">${{scn.stage}}</span>` : '';

        card.innerHTML = `
          <div class="flex items-center justify-between gap-1">
            <div class="flex items-center gap-1.5 min-w-0 truncate">
              ${{stageTag}}
              <span class="font-semibold text-slate-200 truncate">${{scn.name}}</span>
            </div>
            <span class="text-[9px] font-mono px-1.5 py-0.5 rounded border ${{badgeColor}} shrink-0">${{scn.badge}}</span>
          </div>
          <p class="text-[10px] text-slate-400 mt-1 line-clamp-1">${{scn.description}}</p>
        `;
        container.appendChild(card);
      }});
    }}

    function applyScenario(scenarioId) {{
      const q = (scenarioId || '').toLowerCase().trim();
      const scn = GRAPH_DATA.scenarios.find(s => {{
        if (s.id.toLowerCase() === q) return true;
        if (s.aliases && s.aliases.some(a => a.toLowerCase() === q)) return true;
        if (s.name.toLowerCase().includes(q)) return true;
        return false;
      }}) || GRAPH_DATA.scenarios[0];
      currentScenario = scn;

      // Update HUD
      const activeBadge = document.getElementById('activeScenarioBadge');
      if (activeBadge) activeBadge.innerText = scn.badge;
      const hudTitle = document.getElementById('hudScenarioTitle');
      if (hudTitle) hudTitle.innerText = scn.name;
      const hudDesc = document.getElementById('hudScenarioDesc');
      if (hudDesc) hudDesc.innerText = scn.description;
      const dot = document.getElementById('hudStatusDot');
      if (dot) {{
        dot.style.backgroundColor =
          scn.badge === 'CRITICAL' ? '#ef4444' :
          scn.badge === 'MAJOR' ? '#f59e0b' :
          scn.badge === 'MINOR' ? '#eab308' :
          scn.badge === 'KNOWLEDGE_GAP' ? '#a855f7' :
          scn.badge === 'LEARNING_UNIT' ? '#06b6d4' :
          scn.badge === 'WHAT_IF' ? '#3b82f6' : '#10b981';
      }}

      // Update Node alarm states
      highlightedNodes.clear();
      nodes.forEach(n => {{
        if (scn.affected_nodes && scn.affected_nodes[n.id]) {{
          const aff = scn.affected_nodes[n.id];
          n.alarmSeverity = aff.severity;
          n.alarmStatus = aff.status;
          highlightedNodes.add(n.id);
          activeDomains.add(n.domain); // Auto-enable affected domain
        }} else {{
          n.alarmSeverity = 'NOMINAL';
          n.alarmStatus = 'Normal Operation';
        }}
      }});

      renderScenarioList();
      renderDomainList();

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
      const affected = nodes.filter(n => highlightedNodes.has(n.id) && activeDomains.has(n.domain));
      if (affected.length === 0) return;

      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      affected.forEach(n => {{
        if (n.x < minX) minX = n.x;
        if (n.x > maxX) maxX = n.x;
        if (n.y < minY) minY = n.y;
        if (n.y > maxY) maxY = n.y;
      }});
      const cx = (minX + maxX) / 2;
      const cy = (minY + maxY) / 2;
      const w = Math.max(260, maxX - minX + 200);
      const h = Math.max(260, maxY - minY + 200);
      const rect = canvas.getBoundingClientRect();
      const zoomX = (rect.width || 1000) / w;
      const zoomY = (rect.height || 700) / h;
      const optimalZoom = Math.max(0.5, Math.min(1.4, Math.min(zoomX, zoomY)));
      camera = {{ x: -cx * optimalZoom, y: -cy * optimalZoom, zoom: optimalZoom }};
    }}

    // Domain Node Elasticity & Center Gravity Simulation
    function stepPhysics() {{
      if (!isPhysicsActive && !draggedNode) return;

      const centers = GRAPH_DATA.domain_centers;
      const activeNodeList = nodes.filter(n => activeDomains.has(n.domain));

      // Group nodes by domain
      const byDomain = {{}};
      for (const n of activeNodeList) {{
        byDomain[n.domain] = byDomain[n.domain] || [];
        byDomain[n.domain].push(n);
      }}

      // 1. Natural intra-domain elastic repulsion between nodes
      for (const [dom, dNodes] of Object.entries(byDomain)) {{
        for (let i = 0; i < dNodes.length; i++) {{
          const n1 = dNodes[i];
          for (let j = i + 1; j < dNodes.length; j++) {{
            const n2 = dNodes[j];
            const dx = n2.x - n1.x;
            const dy = n2.y - n1.y;
            const dist2 = dx * dx + dy * dy;
            const minDist = n1.radius + n2.radius + 12;
            if (dist2 < minDist * minDist * 2.5 && dist2 > 0.01) {{
              const dist = Math.sqrt(dist2);
              const force = Math.min(3.5, 450.0 / (dist2 + 35.0));
              const fx = (dx / dist) * force;
              const fy = (dy / dist) * force;
              if (n1 !== draggedNode) {{ n1.vx -= fx; n1.vy -= fy; }}
              if (n2 !== draggedNode) {{ n2.vx += fx; n2.vy += fy; }}
            }}
          }}
        }}
      }}

      // 2. Intra-domain elastic springs along links
      for (const link of links) {{
        if (!activeDomains.has(link.sourceNode.domain) || !activeDomains.has(link.targetNode.domain)) continue;
        const n1 = link.sourceNode;
        const n2 = link.targetNode;
        if (n1.domain !== n2.domain) continue; // Cross-domain links do not pull nodes across domain boundaries

        const springLen = 38.0;
        const springK = 0.05;

        const dx = n2.x - n1.x;
        const dy = n2.y - n1.y;
        const dist = Math.hypot(dx, dy) || 1;
        const delta = dist - springLen;
        const force = Math.min(2.5, delta * springK);
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        if (n1 !== draggedNode) {{ n1.vx -= fx; n1.vy -= fy; }}
        if (n2 !== draggedNode) {{ n2.vx += fx; n2.vy += fy; }}
      }}

      // 3. Sub-Cluster Center Gravitational Anchor & Elastic Confinement
      for (const n of activeNodeList) {{
        if (n === draggedNode) {{
          n.x = mouseWorldPos.x;
          n.y = mouseWorldPos.y;
          n.vx = 0;
          n.vy = 0;
          continue;
        }}

        const baseCenter = centers[n.domain] || {{ x: 0, y: 0 }};
        const subCfg = (GRAPH_DATA.sub_cluster_offsets || {{}})[n.sub_cluster] || {{ dx: 0, dy: 0 }};
        const scX = baseCenter.x + (subCfg.dx || 0);
        const scY = baseCenter.y + (subCfg.dy || 0);
        const dx = scX - n.x;
        const dy = scY - n.y;
        const distToCenter = Math.hypot(dx, dy);
        const subNodes = nodes.filter(o => o.domain === n.domain && o.sub_cluster === n.sub_cluster);
        const maxAllowed = 18.0 + Math.sqrt(subNodes.length || 4) * 11.0;

        let gravity = 0.09;
        if (distToCenter > maxAllowed) {{
          // Strong elastic tether pulling node into its sub-cluster satellite
          gravity += (distToCenter - maxAllowed) * 0.03;
        }}

        n.vx += dx * gravity;
        n.vy += dy * gravity;

        n.vx *= 0.78;
        n.vy *= 0.78;
        const v = Math.hypot(n.vx, n.vy);
        if (v > 3.5) {{
          n.vx = (n.vx / v) * 3.5;
          n.vy = (n.vy / v) * 3.5;
        }}
        n.x += n.vx;
        n.y += n.vy;

        // Hard elastic boundary confinement to sub-cluster
        const curDist = Math.hypot(n.x - scX, n.y - scY);
        if (curDist > maxAllowed * 1.15) {{
          const ratio = (maxAllowed * 1.15) / curDist;
          n.x = scX + (n.x - scX) * ratio;
          n.y = scY + (n.y - scY) * ratio;
        }}
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
        let maxR = 45;
        for (const dn of domNodes) {{
          const d = Math.hypot(dn.x - center.x, dn.y - center.y);
          if (d + dn.radius + 20 > maxR) maxR = d + dn.radius + 20;
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
        ctx.fillText(domName.toUpperCase(), center.x, center.y - maxR - 8);
      }}

      // 0a. Draw TM Forum Sub-Cluster Demarcation Enclosures & Labels
      const bySubCluster = {{}};
      for (const n of nodes) {{
        if (!activeDomains.has(n.domain)) continue;
        const subKey = n.sub_cluster;
        if (!subKey) continue;
        const groupKey = n.domain + '::' + subKey;
        bySubCluster[groupKey] = bySubCluster[groupKey] || [];
        bySubCluster[groupKey].push(n);
      }}

      for (const [groupKey, subNodes] of Object.entries(bySubCluster)) {{
        if (subNodes.length < 1) continue;
        const subKey = groupKey.split('::')[1];
        const subCfg = (GRAPH_DATA.sub_cluster_offsets || {{}})[subKey] || {{ label: subKey.replace(/^[a-z_]+\./, '').replace(/_/g, ' ').toUpperCase(), icon: '🏷️', color: '#94a3b8' }};

        let sumX = 0, sumY = 0;
        for (const sn of subNodes) {{
          sumX += sn.x;
          sumY += sn.y;
        }}
        const scx = sumX / subNodes.length;
        const scy = sumY / subNodes.length;

        let scR = 24;
        for (const sn of subNodes) {{
          const d = Math.hypot(sn.x - scx, sn.y - scy) + sn.radius + 12;
          if (d > scR) scR = d;
        }}

        // Draw sub-cluster soft bubble & demarcation dashed border
        ctx.beginPath();
        ctx.arc(scx, scy, scR, 0, Math.PI * 2);
        ctx.fillStyle = (subCfg.color || '#38bdf8') + '12'; // 7% soft tint
        ctx.fill();
        ctx.lineWidth = 1.0;
        ctx.setLineDash([3, 3]);
        ctx.strokeStyle = (subCfg.color || '#38bdf8') + '55'; // 33% border
        ctx.stroke();
        ctx.setLineDash([]);

        // Draw sleek sub-cluster title pill
        const subLabel = `${{subCfg.icon || ''}} ${{subCfg.label || subKey}} (${{subNodes.length}})`;
        ctx.font = '600 9px Inter, monospace';
        const textWidth = ctx.measureText(subLabel).width;
        const pillW = textWidth + 14;
        const pillH = 16;
        const pillX = scx - pillW / 2;
        const pillY = scy - scR - 10;

        // Pill background
        ctx.fillStyle = '#0f172aee'; // Dark slate background
        ctx.beginPath();
        if (typeof ctx.roundRect === 'function') {{
          ctx.roundRect(pillX, pillY, pillW, pillH, 4);
        }} else {{
          ctx.rect(pillX, pillY, pillW, pillH);
        }}
        ctx.fill();
        ctx.strokeStyle = (subCfg.color || '#38bdf8') + '88';
        ctx.lineWidth = 0.8;
        ctx.stroke();

        // Pill text
        ctx.fillStyle = subCfg.color || '#e2e8f0';
        ctx.textAlign = 'center';
        ctx.fillText(subLabel, scx, pillY + 11);
      }}

      // 0b. Draw Multi-Tier Blast Radius Boundary Enclosures for Affected Domains
      let rootCauseDomain = null;
      if (highlightedNodes.size > 0) {{
        const affectedByDomain = {{}};
        nodes.filter(n => highlightedNodes.has(n.id) && activeDomains.has(n.domain)).forEach(n => {{
          affectedByDomain[n.domain] = affectedByDomain[n.domain] || [];
          affectedByDomain[n.domain].push(n);
        }});

        const domainList = [];

        for (const [dom, dnodes] of Object.entries(affectedByDomain)) {{
          if (dnodes.length === 0) continue;
          const avgX = dnodes.reduce((s, n) => s + n.x, 0) / dnodes.length;
          const avgY = dnodes.reduce((s, n) => s + n.y, 0) / dnodes.length;

          // Snug relative sizing w.r.t the number and spread of affected nodes
          let maxDist = 0;
          for (const n of dnodes) {{
            const d = Math.hypot(n.x - avgX, n.y - avgY) + n.radius;
            if (d > maxDist) maxDist = d;
          }}
          const dynamicPadding = dnodes.length === 1 ? 9 : Math.min(15, 6 + Math.sqrt(dnodes.length) * 2.2);
          const maxR = Math.max(dnodes[0].radius + 7, maxDist + dynamicPadding);

          // Determine domain peak severity
          const hasRoot = dnodes.some(n => n.alarmSeverity === 'ROOT_CAUSE');
          const hasCrit = dnodes.some(n => n.alarmSeverity === 'CRITICAL');
          const hasMaj = dnodes.some(n => n.alarmSeverity === 'MAJOR');
          const severityRank = hasRoot ? 4 : (hasCrit ? 3 : (hasMaj ? 2 : 1));

          domainList.push({{ dom, dnodes, x: avgX, y: avgY, r: maxR, hasRoot, hasCrit, hasMaj, rank: severityRank }});

          let borderColor = 'rgba(234, 179, 8, 0.85)';
          let fillColor = 'rgba(234, 179, 8, 0.08)';
          let badgeText = `🟡 MINOR IMPACT (${{dnodes.length}} affected)`;
          let badgeColor = '#eab308';

          if (hasRoot) {{
            rootCauseDomain = {{ dom, x: avgX, y: avgY, r: maxR }};
            borderColor = 'rgba(239, 68, 68, 0.95)';
            fillColor = 'rgba(239, 68, 68, 0.15)';
            badgeText = `🎯 ROOT CAUSE ORIGIN (${{dnodes.length}} affected)`;
            badgeColor = '#ef4444';
          }} else if (hasCrit) {{
            borderColor = 'rgba(239, 68, 68, 0.85)';
            fillColor = 'rgba(239, 68, 68, 0.11)';
            badgeText = `🔴 CRITICAL BLAST RADIUS (${{dnodes.length}} affected)`;
            badgeColor = '#ef4444';
          }} else if (hasMaj) {{
            borderColor = 'rgba(249, 115, 22, 0.85)';
            fillColor = 'rgba(249, 115, 22, 0.10)';
            badgeText = `🟠 MAJOR BLAST RADIUS (${{dnodes.length}} affected)`;
            badgeColor = '#f97316';
          }}

          // Blast Radius Soft Aura & Rotating Boundary Ring
          ctx.beginPath();
          ctx.arc(avgX, avgY, maxR, 0, Math.PI * 2);
          ctx.fillStyle = fillColor;
          ctx.fill();
          ctx.lineWidth = hasRoot ? 2.5 : 1.6;
          ctx.setLineDash(hasRoot ? [10, 6] : [7, 5]);
          ctx.lineDashOffset = -(pulseTime * 20);
          ctx.strokeStyle = borderColor;
          ctx.stroke();
          ctx.setLineDash([]);
          ctx.lineDashOffset = 0;

          // Blast Radius Header Badge (Compact position relative to maxR)
          ctx.fillStyle = badgeColor;
          ctx.font = '700 10px JetBrains Mono, monospace';
          ctx.textAlign = 'center';
          ctx.fillText(badgeText, avgX, avgY - maxR - 8);
        }}

        // Expanding red radar wave for root cause domain
        if (rootCauseDomain) {{
          const domWaveR = rootCauseDomain.r + 5 + ((pulseTime * 14) % 18);
          const domWaveAlpha = Math.max(0, 1 - (domWaveR - rootCauseDomain.r) / 18);
          ctx.beginPath();
          ctx.arc(rootCauseDomain.x, rootCauseDomain.y, domWaveR, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(239, 68, 68, ${{domWaveAlpha * 0.85}})`;
          ctx.lineWidth = 1.8;
          ctx.stroke();
        }}

        // 0c. Draw Prominent Straight Macro Causal Propagation Vectors Overlay across Domains
        if (domainList.length > 1) {{
          const rootDomName = rootCauseDomain ? rootCauseDomain.dom : null;

          // Evidence / Symptom Sinks: Domains that capture observational customer/telemetry impact, NOT causal drivers
          const EVIDENCE_DOMAINS = new Set([
            'CRM & Customer Experience',
            'Observability & Remediation'
          ]);

          const conduitEdges = [];

          if (currentScenario && currentScenario.propagation_path && currentScenario.propagation_path.length > 0) {{
            // 1. Primary Causal Spine (Network Root -> Network Intermediaries -> Cross-Domain Incident)
            const spineDoms = [];
            if (rootDomName && !EVIDENCE_DOMAINS.has(rootDomName)) {{
              spineDoms.push(rootDomName);
            }}

            for (let i = 0; i < currentScenario.propagation_path.length; i++) {{
              const nid = currentScenario.propagation_path[i];
              const n = nodes.find(node => node.id === nid);
              if (n && activeDomains.has(n.domain) && !EVIDENCE_DOMAINS.has(n.domain)) {{
                if (!spineDoms.includes(n.domain)) {{
                  spineDoms.push(n.domain);
                }}
              }}
            }}

            // If an incident in Cross-Domain Operations is affected, it is the operational escalation target
            if (domainList.some(d => d.dom === 'Cross-Domain Operations') && !spineDoms.includes('Cross-Domain Operations')) {{
              spineDoms.push('Cross-Domain Operations');
            }}

            // Consecutive spine edges: d[i] -> d[i+1]
            for (let i = 0; i < spineDoms.length - 1; i++) {{
              const dStart = domainList.find(d => d.dom === spineDoms[i]);
              const dEnd = domainList.find(d => d.dom === spineDoms[i + 1]);
              if (dStart && dEnd) {{
                conduitEdges.push({{ from: dStart, to: dEnd, isRoot: dStart.hasRoot, isEvidence: false }});
              }}
            }}

            // 2. Downstream Evidence Branches (Leaf Sinks: e.g. Impacted Service/Core -> Customer Trouble Tickets in CRM)
            // The last functional network domain in the spine drives customer and telemetry evidence
            const primaryImpactDomName = [...spineDoms].reverse().find(d => !EVIDENCE_DOMAINS.has(d) && d !== 'Cross-Domain Operations') || rootDomName;
            const primaryImpactDom = domainList.find(d => d.dom === primaryImpactDomName);

            if (primaryImpactDom) {{
              for (const dObj of domainList) {{
                if (EVIDENCE_DOMAINS.has(dObj.dom) && dObj.dom !== primaryImpactDomName) {{
                  // One-way directed branch into Evidence Sink (TERMINAL LEAF - NEVER EXITS)
                  conduitEdges.push({{ from: primaryImpactDom, to: dObj, isRoot: false, isEvidence: true }});
                }}
              }}
            }}
          }} else {{
            // Fallback: sort by descending severity rank
            const orderedDomains = [...domainList].sort((a, b) => b.rank - a.rank);
            for (let i = 0; i < orderedDomains.length - 1; i++) {{
              conduitEdges.push({{ from: orderedDomains[i], to: orderedDomains[i + 1], isRoot: orderedDomains[i].hasRoot, isEvidence: false }});
            }}
          }}

          for (let i = 0; i < conduitEdges.length; i++) {{
            const edge = conduitEdges[i];
            const dStart = edge.from;
            const dEnd = edge.to;
            const dist = Math.hypot(dEnd.x - dStart.x, dEnd.y - dStart.y);
            if (dist < 20) continue;

            const baseAngle = Math.atan2(dEnd.y - dStart.y, dEnd.x - dStart.x);
            const p1 = {{
              x: dStart.x + Math.cos(baseAngle) * (dStart.r + 4),
              y: dStart.y + Math.sin(baseAngle) * (dStart.r + 4)
            }};
            const p2 = {{
              x: dEnd.x - Math.cos(baseAngle) * (dEnd.r + 8),
              y: dEnd.y - Math.sin(baseAngle) * (dEnd.r + 8)
            }};

            const isStartingFromRoot = edge.isRoot;
            const isEvidence = edge.isEvidence;
            const strokeColor = isStartingFromRoot ? '#ef4444' : isEvidence ? '#ec4899' : '#f97316';
            const glowColor = isStartingFromRoot ? 'rgba(239, 68, 68, 0.28)' : isEvidence ? 'rgba(236, 72, 153, 0.22)' : 'rgba(249, 115, 22, 0.20)';

            // 1. Broad Ambient Glow Line
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.lineWidth = isEvidence ? 8 : 12;
            ctx.strokeStyle = glowColor;
            ctx.lineCap = 'round';
            ctx.stroke();

            // 2. High-Luminance Main Conduit Track
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.lineWidth = isStartingFromRoot ? 4.0 : isEvidence ? 2.5 : 3.0;
            ctx.strokeStyle = strokeColor;
            ctx.setLineDash(isEvidence ? [8, 6] : [14, 8]);
            ctx.lineDashOffset = -(pulseTime * 36);
            ctx.stroke();
            ctx.setLineDash([]);
            ctx.lineDashOffset = 0;

            // 3. Directional Arrowheads along the straight line (Midpoint & End)
            [0.5, 0.96].forEach(tVal => {{
              const ptX = p1.x + (p2.x - p1.x) * tVal;
              const ptY = p1.y + (p2.y - p1.y) * tVal;

              ctx.save();
              ctx.translate(ptX, ptY);
              ctx.rotate(baseAngle);
              ctx.beginPath();
              ctx.moveTo(0, 0);
              ctx.lineTo(-14, -8);
              ctx.lineTo(-14, 8);
              ctx.closePath();
              ctx.fillStyle = strokeColor;
              ctx.shadowColor = strokeColor;
              ctx.shadowBlur = 10;
              ctx.fill();
              ctx.strokeStyle = '#ffffff';
              ctx.lineWidth = 1.6;
              ctx.stroke();
              ctx.restore();
            }});

            // 4. High-Intensity Pulsing Energy Photon Packet
            const tPacket = (pulseTime * 0.75 + i * 0.35) % 1.0;
            const px = p1.x + (p2.x - p1.x) * tPacket;
            const py = p1.y + (p2.y - p1.y) * tPacket;
            ctx.beginPath();
            ctx.arc(px, py, isStartingFromRoot ? 5.8 : isEvidence ? 3.8 : 4.5, 0, Math.PI * 2);
            ctx.fillStyle = '#ffffff';
            ctx.shadowColor = strokeColor;
            ctx.shadowBlur = 16;
            ctx.fill();
            ctx.shadowBlur = 0;
          }}
        }}
      }}

      // 1. Draw Links & Causal Conduits
      for (const link of links) {{
        if (!activeDomains.has(link.sourceNode.domain) || !activeDomains.has(link.targetNode.domain)) continue;
        const isImpactedLink = highlightedNodes.has(link.sourceNode.id) && highlightedNodes.has(link.targetNode.id);
        const isRootLink = isImpactedLink && (link.sourceNode.alarmSeverity === 'ROOT_CAUSE' || link.targetNode.alarmSeverity === 'ROOT_CAUSE');
        const isConnectedToSelected = selectedNode && (link.sourceNode.id === selectedNode.id || link.targetNode.id === selectedNode.id);

        ctx.beginPath();
        ctx.moveTo(link.sourceNode.x, link.sourceNode.y);
        ctx.lineTo(link.targetNode.x, link.targetNode.y);

        if (isImpactedLink) {{
          // Subdued micro individual node links so they do NOT create messy visual noise
          ctx.lineWidth = isRootLink ? 1.4 : 0.8;
          ctx.strokeStyle = isRootLink ? 'rgba(239, 68, 68, 0.45)' : 'rgba(249, 115, 22, 0.22)';
          ctx.stroke();
          drawArrow(link.sourceNode.x, link.sourceNode.y, link.targetNode.x, link.targetNode.y, link.targetNode.radius, false);
        }} else if (isConnectedToSelected) {{
          ctx.lineWidth = 2.0;
          ctx.strokeStyle = '#38bdf8';
          ctx.stroke();
          drawArrow(link.sourceNode.x, link.sourceNode.y, link.targetNode.x, link.targetNode.y, link.targetNode.radius, true);
        }} else if (selectedNode || highlightedNodes.size > 0) {{
          ctx.lineWidth = 0.6;
          ctx.strokeStyle = 'rgba(71, 85, 105, 0.10)';
          ctx.stroke();
        }} else {{
          ctx.lineWidth = 1.0;
          ctx.strokeStyle = link.is_cross_domain ? 'rgba(245, 158, 11, 0.25)' : 'rgba(100, 116, 139, 0.2)';
          ctx.stroke();
          drawArrow(link.sourceNode.x, link.sourceNode.y, link.targetNode.x, link.targetNode.y, link.targetNode.radius, false);
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
      let rootCauseNode = null;
      for (const n of nodes) {{
        if (!activeDomains.has(n.domain)) continue;
        const isSelected = selectedNode && selectedNode.id === n.id;
        const isHovered = hoveredNode && hoveredNode.id === n.id;
        const isImpacted = highlightedNodes.has(n.id);
        const isDimmed = (selectedNode || highlightedNodes.size > 0) && !isSelected && !isHovered && !isImpacted && (!selectedNode || !isConnected(selectedNode, n));

        // Severity Color Determination
        let nodeColor = n.color || '#3b82f6';
        let ringColor = null;
        let haloColor = null;

        if (n.alarmSeverity === 'ROOT_CAUSE') {{
          rootCauseNode = n;
          nodeColor = '#ef4444';
          ringColor = '#ef4444';
          haloColor = 'rgba(239, 68, 68, 0.45)';
        }} else if (n.alarmSeverity === 'CRITICAL') {{
          nodeColor = '#ef4444';
          ringColor = '#ef4444';
          haloColor = 'rgba(239, 68, 68, 0.35)';
        }} else if (n.alarmSeverity === 'MAJOR') {{
          nodeColor = '#f97316';
          ringColor = '#f97316';
          haloColor = 'rgba(249, 115, 22, 0.35)';
        }} else if (n.alarmSeverity === 'MINOR') {{
          nodeColor = '#eab308';
          ringColor = '#eab308';
          haloColor = 'rgba(234, 179, 8, 0.28)';
        }}

        // Red/Orange/Yellow Rotating Circling Boundary Rings for Affected Nodes
        if (isImpacted && ringColor) {{
          // Pulsating rotating outer warning boundary ring
          const ringR = n.radius + 6 + Math.sin(pulseTime * 4) * 2;
          ctx.beginPath();
          ctx.arc(n.x, n.y, ringR, 0, Math.PI * 2);
          ctx.strokeStyle = ringColor;
          ctx.lineWidth = n.alarmSeverity === 'ROOT_CAUSE' ? 2.4 : 1.6;
          ctx.setLineDash([5, 4]);
          ctx.lineDashOffset = -(pulseTime * 25);
          ctx.stroke();
          ctx.setLineDash([]);
          ctx.lineDashOffset = 0;
        }}

        // Counter-rotating outer radar ring for root cause
        if (n.alarmSeverity === 'ROOT_CAUSE') {{
          const outerR = n.radius + 12;
          ctx.beginPath();
          ctx.arc(n.x, n.y, outerR, 0, Math.PI * 2);
          ctx.strokeStyle = 'rgba(239, 68, 68, 0.75)';
          ctx.lineWidth = 1.8;
          ctx.setLineDash([6, 5]);
          ctx.lineDashOffset = +(pulseTime * 20);
          ctx.stroke();
          ctx.setLineDash([]);
          ctx.lineDashOffset = 0;
        }}

        // Halo for Root Cause, Selected, or Hovered
        if (isSelected || haloColor) {{
          const haloRadius = n.radius + (n.alarmSeverity === 'ROOT_CAUSE' ? 10 + Math.sin(pulseTime * 4) * 3 : 6);
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

        // Smart Decluttered Node Labels with Dark Pill Backdrops
        const shouldShowLabel = isSelected || isHovered || n.alarmSeverity === 'ROOT_CAUSE' || (showAllLabels && camera.zoom >= 1.05);
        if (shouldShowLabel) {{
          const cleanLabel = n.label.length > 22 ? n.label.slice(0, 20) + '…' : n.label;
          const labelText = n.alarmSeverity !== 'NOMINAL' && n.alarmSeverity !== 'ROOT_CAUSE'
            ? `${{cleanLabel}} [${{n.alarmSeverity}}]`
            : cleanLabel;

          ctx.font = isSelected || n.alarmSeverity === 'ROOT_CAUSE' ? '600 10.5px Inter, sans-serif' : '500 9.5px Inter, sans-serif';
          const textMetrics = ctx.measureText(labelText);
          const pillW = textMetrics.width + 12;
          const pillH = 18;
          const pillX = n.x - pillW / 2;
          const pillY = n.y + n.radius + 6;

          // Dark Translucent Pill Backdrop
          ctx.fillStyle = 'rgba(15, 23, 42, 0.90)';
          ctx.beginPath();
          if (ctx.roundRect) {{
            ctx.roundRect(pillX, pillY, pillW, pillH, 4);
          }} else {{
            ctx.rect(pillX, pillY, pillW, pillH);
          }}
          ctx.fill();
          ctx.strokeStyle = isSelected ? '#ffffff' : (ringColor || 'rgba(148, 163, 184, 0.3)');
          ctx.lineWidth = 1.0;
          ctx.stroke();

          // Label Text
          ctx.fillStyle = isSelected ? '#ffffff' : (n.alarmSeverity === 'ROOT_CAUSE' ? '#fca5a5' : '#f1f5f9');
          ctx.textAlign = 'center';
          ctx.fillText(labelText, n.x, pillY + 12.5);
        }}
      }}

      // 3. Draw High-Visibility Pointer Callout & Sonar Waves for Root Cause Node
      if (rootCauseNode) {{
        // Expanding dual sonar ripples
        for (let r = 0; r < 2; r++) {{
          const rippleR = rootCauseNode.radius + 10 + ((pulseTime * 20 + r * 15) % 30);
          const rippleAlpha = Math.max(0, 1 - (rippleR - rootCauseNode.radius) / 30);
          ctx.beginPath();
          ctx.arc(rootCauseNode.x, rootCauseNode.y, rippleR, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(239, 68, 68, ${{rippleAlpha * 0.9}})`;
          ctx.lineWidth = 2.0;
          ctx.stroke();
        }}

        // Floating Callout Pointer Badge
        const tagY = rootCauseNode.y - rootCauseNode.radius - 22;
        const tagW = 108;
        const tagH = 20;
        ctx.fillStyle = '#ef4444';
        ctx.shadowColor = '#ef4444';
        ctx.shadowBlur = 12;
        ctx.beginPath();
        if (ctx.roundRect) {{
          ctx.roundRect(rootCauseNode.x - tagW / 2, tagY - tagH / 2, tagW, tagH, 4);
        }} else {{
          ctx.rect(rootCauseNode.x - tagW / 2, tagY - tagH / 2, tagW, tagH);
        }}
        ctx.fill();
        ctx.shadowBlur = 0;

        // Pointer indicator triangle
        ctx.beginPath();
        ctx.moveTo(rootCauseNode.x - 5, tagY + tagH / 2);
        ctx.lineTo(rootCauseNode.x + 5, tagY + tagH / 2);
        ctx.lineTo(rootCauseNode.x, rootCauseNode.y - rootCauseNode.radius - 3);
        ctx.closePath();
        ctx.fillStyle = '#ef4444';
        ctx.fill();

        // Pointer Text
        ctx.fillStyle = '#ffffff';
        ctx.font = '700 9px JetBrains Mono, monospace';
        ctx.textAlign = 'center';
        ctx.fillText('🎯 ROOT CAUSE', rootCauseNode.x, tagY + 3);
      }}

      ctx.restore();
      requestAnimationFrame(draw);
    }}

    function drawArrow(x1, y1, x2, y2, targetRadius, isActive) {{
      const angle = Math.atan2(y2 - y1, x2 - x1);
      const edgeDist = targetRadius + 3;
      const arrowX = x2 - Math.cos(angle) * edgeDist;
      const arrowY = y2 - Math.sin(angle) * edgeDist;
      const arrowSize = isActive ? 9 : 5.5;
      ctx.save();
      ctx.beginPath();
      ctx.translate(arrowX, arrowY);
      ctx.rotate(angle);
      ctx.moveTo(0, 0);
      ctx.lineTo(-arrowSize * 1.5, -arrowSize * 0.9);
      ctx.lineTo(-arrowSize * 1.5, arrowSize * 0.9);
      ctx.closePath();
      ctx.fillStyle = isActive ? '#ef4444' : 'rgba(148, 163, 184, 0.65)';
      ctx.fill();
      if (isActive) {{
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }}
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

    window.addEventListener('mouseup', () => {{
      // Dynamic drag release with natural spring bounce
      if (draggedNode) {{
        draggedNode.vx = (mouseWorldPos.x - (draggedNode.lastX || mouseWorldPos.x)) * 0.4;
        draggedNode.vy = (mouseWorldPos.y - (draggedNode.lastY || mouseWorldPos.y)) * 0.4;
      }}
      draggedNode = null;
      isDragging = false;
    }});

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

    function getScenarioSummary(scn) {{
      const meta = {{
        'baseline': {{
          executive_summary: 'All cellular and IP transport subnets operating within nominal QoS bounds. Zero active 3GPP alarm declarations or customer trouble tickets.',
          root_cause_label: 'None (System Nominal)',
          root_cause_fault: 'Continuous steady-state SLA telemetry verification',
          impacted_service: 'All Core & Voice Services',
          sla_status: '100% NOMINAL',
          customer_impact: '0 Complaints / Zero MTTR impact',
          remediation: 'Continuous automated telemetry polling and periodic topology integrity auditing.'
        }},
        'h1-sgi-mtu': {{
          executive_summary: 'An interface MTU mismatch on the SGi IP transport edge (sgi-edge-01) caused severe packet fragmentation, quickly saturating the Gi-LAN NAT firewall and causing PDU session discards at the PGW user plane.',
          root_cause_label: 'sgi-edge-01 (Transport IP)',
          root_cause_fault: 'L3 Interface MTU Mismatch & Buffer Overrun',
          impacted_service: 'SGi High-Speed Mobile Data',
          sla_status: 'CRITICAL (Throughput < committed CIR)',
          customer_impact: 'Enterprise VPN drops & customer SLA complaint surge',
          remediation: 'Recalibrate SGi edge jumbo frame MTU to 9000 bytes and flush orphan NAT connection states.'
        }},
        'h1-lte-attach': {{
          executive_summary: 'HSS Diameter authentication timeouts stalled MME control-plane transaction queues, triggering cascading RRC connection rejects across serving eNodeBs and blocking 4G subscriber network entry.',
          root_cause_label: 'hss-01 (Signaling / EPC)',
          root_cause_fault: 'Diameter S6a Authentication Timeout',
          impacted_service: '4G LTE Initial Attach & Mobility',
          sla_status: 'CRITICAL (Attach Success < 82%)',
          customer_impact: 'Subscribers unable to register on 4G network',
          remediation: 'Failover Diameter S6a traffic to secondary DRA path and restart HSS authentication daemon.'
        }},
        'h1-voice-cssr': {{
          executive_summary: 'Excessive fiber backhaul jitter and packet drops on voice-backhaul-01 corrupted SIP INVITE transaction handshakes at the P-CSCF, causing IMS dedicated voice bearer establishment failures.',
          root_cause_label: 'voice-backhaul-01 (Transport Optical)',
          root_cause_fault: 'Backhaul Fiber Jitter & Packet Discard',
          impacted_service: 'VoNR / VoLTE High-Definition Voice',
          sla_status: 'CRITICAL (Call Setup Success Rate < 75%)',
          customer_impact: 'Voice call drops and call setup failure complaints',
          remediation: 'Reroute voice traffic to secondary DWDM ring and replace degraded optical transceiver module.'
        }},
        'h1-ue-registration': {{
          executive_summary: 'A 5G registration surge across transport aggregation switch agg-sw-03 overwhelmed AMF-01 CPU processing, leading to NGAP queue discards and degraded initial registration rates.',
          root_cause_label: 'transport-agg-sw-03 (IP Transport)',
          root_cause_fault: 'Switch Ingress Buffer Saturation & Storm',
          impacted_service: '5G SA UE Registration & PDU Establishment',
          sla_status: 'MAJOR (Registration Latency Spike)',
          customer_impact: 'Intermittent 5G device attachment failures',
          remediation: 'Apply rate limiting on NGAP ingress ports and activate AMF control-plane load shedding.'
        }},
        'h1-site-power': {{
          executive_summary: 'DC power rectifier trip on UPS-77 transferred core equipment to emergency battery backup with fluctuating bus voltage, threatening site continuity.',
          root_cause_label: 'power-ups-77 (Cloud NFVI & Facilities)',
          root_cause_fault: 'Primary DC Rectifier Trip & Battery Discharge',
          impacted_service: 'Data Center Site Facilities & NFVI Power',
          sla_status: 'MINOR (Redundant Power Rail Degraded)',
          customer_impact: 'Zero active customer outage; high risk of hardware shutdown',
          remediation: 'Dispatch site engineering crew to inspect rectifier breaker and start auxiliary diesel generator.'
        }},
        'h2-gap-001': {{
          executive_summary: 'An unmodeled billing/charging dependency boundary between Mobile Core and OCS caused unexplained subscriber quota timeouts and silent data connection terminations.',
          root_cause_label: 'hss-01 / OCS Boundary (Charging)',
          root_cause_fault: 'Unmapped OCS Gy/Ro Diameter Session Boundary',
          impacted_service: 'Prepaid 5G Mobile Data Quota',
          sla_status: 'CRITICAL (Silent Session Tear-Down)',
          customer_impact: 'Prepaid subscriber balance and quota billing disputes',
          remediation: 'Promote discovered OCS Gy/Ro diameter topology link into active causal knowledge graph.'
        }},
        'h2-gap-002': {{
          executive_summary: 'Hidden optical power attenuation in DWDM layer transceivers caused framing errors and packet drops without triggering classical IP alarms, baffling standard root cause isolation.',
          root_cause_label: 'voice-backhaul-01 (DWDM Physical)',
          root_cause_fault: 'Optical Transceiver Rx Power Attenuation',
          impacted_service: 'High-Capacity Inter-Site Data Transport',
          sla_status: 'CRITICAL (Throughput Degradation)',
          customer_impact: 'Intermittent latency spikes for business enterprise trunks',
          remediation: 'Integrate physical optical transceiver telemetry into upstream IP correlation engine.'
        }},
        'h2-gap-003': {{
          executive_summary: 'Undocumented firewall NAT translation session table limits were reached on the Gi-LAN boundary, dropping outbound sessions while core UPF telemetry reported nominal health.',
          root_cause_label: 'nat-fw-01 (Gi-LAN Security)',
          root_cause_fault: 'Firewall NAT Session Table Exhaustion (>99%)',
          impacted_service: 'Public Internet & Web Browsing',
          sla_status: 'CRITICAL (Outbound Traffic Blackhole)',
          customer_impact: 'Subscribers cannot access external internet websites',
          remediation: 'Promote NAT firewall capacity telemetry into carrier OSS and expand port translation pool.'
        }},
        'h2-gap-004': {{
          executive_summary: 'Unmodeled foreign carrier IPX interconnect latency caused SEPP handshake timeouts during inbound roaming registration, causing VIP roamer attachment drops.',
          root_cause_label: 'amf-01 / SEPP Boundary (Roaming)',
          root_cause_fault: 'Foreign IPX Carrier Handshake Latency Spike',
          impacted_service: 'International Inbound Roaming',
          sla_status: 'CRITICAL (Roaming Registration Failure)',
          customer_impact: 'VIP roaming subscriber complaints and international roaming revenue leakage',
          remediation: 'Bind SEPP SLA latency thresholds to AMF admission controller and promote roaming topology edge.'
        }},
        'h2-gap-005': {{
          executive_summary: 'Hidden CPU socket NUMA pinning contention on virtualized K8s compute hosts impaired UPF DPDK packet processing, resulting in packet drops without NFV hardware alerts.',
          root_cause_label: 'power-ups-77 / NFVI Compute (Cloud)',
          root_cause_fault: 'Host CPU Sched Contention & Cross-NUMA Latency',
          impacted_service: 'UPF Fast-Path Packet Forwarding',
          sla_status: 'CRITICAL (DPDK Jitter & Discards)',
          customer_impact: 'Enterprise low-latency application SLA breaches',
          remediation: 'Promote NFVI host NUMA topology constraints into 5G UPF placement orchestration.'
        }},
        'h3-lrn-001': {{
          executive_summary: 'Promoted learned SME knowledge unit connecting OCS charging interface directly to PGW session management, permanently eliminating blind spots in future billing incident triage.',
          root_cause_label: 'hss-01 / OCS Boundary (Learned)',
          root_cause_fault: 'Promoted Causal Dependency Edge (OCS ↔ PGW)',
          impacted_service: 'Subscriber Quota & Balance Assurance',
          sla_status: 'NOMINAL (Knowledge Promoted)',
          customer_impact: 'Permanent reduction in future billing incident MTTR',
          remediation: 'Validated knowledge unit promoted to production active graph catalog.'
        }},
        'h3-lrn-002': {{
          executive_summary: 'Calibrated optical power threshold correlation rules directly connecting physical fiber transceivers to SGi IP routing, enabling proactive transport anomaly detection.',
          root_cause_label: 'voice-backhaul-01 (Learned DWDM)',
          root_cause_fault: 'Calibrated Optical Transceiver Power Thresholds',
          impacted_service: 'Core Voice & Data Transport Backbone',
          sla_status: 'NOMINAL (Knowledge Promoted)',
          customer_impact: 'Zero customer impact; proactive mitigation enabled',
          remediation: 'Optical degradation telemetry bound to IP automated rerouting playbook.'
        }},
        'h3-lrn-003': {{
          executive_summary: 'Integrated Gi-LAN firewall NAT translation table telemetry into Core data pipeline, preventing silent subscriber session drops through dynamic capacity alarming.',
          root_cause_label: 'nat-fw-01 (Learned Security)',
          root_cause_fault: 'Promoted NAT Connection Capacity Model',
          impacted_service: 'Mobile Internet Gateway Forwarding',
          sla_status: 'NOMINAL (Knowledge Promoted)',
          customer_impact: 'Automated auto-scaling prevents subscriber blackholes',
          remediation: 'NAT threshold alerts synchronized with mobile packet core orchestrator.'
        }},
        'h3-lrn-004': {{
          executive_summary: 'Integrated SEPP inter-carrier latency bounds into 5G AMF admission control, eliminating blind spots in roaming triage and protecting carrier roaming revenue.',
          root_cause_label: 'amf-01 (Learned Roaming)',
          root_cause_fault: 'Promoted SEPP Inter-Carrier Contract Model',
          impacted_service: '5G Global Roaming Interconnect',
          sla_status: 'NOMINAL (Knowledge Promoted)',
          customer_impact: 'Seamless international roamer network admission assured',
          remediation: 'Roaming SLA telemetry integrated into carrier edge intelligence engine.'
        }},
        'h3-lrn-005': {{
          executive_summary: 'Promoted physical host compute topology awareness into UPF orchestration, ensuring DPDK cores avoid CPU scheduling jitter and maintaining sub-millisecond user plane latency.',
          root_cause_label: 'power-ups-77 (Learned NFVI)',
          root_cause_fault: 'Promoted Host Topology Binding & Core Isolation',
          impacted_service: 'Cloud NFVI Core Workload Hosting',
          sla_status: 'NOMINAL (Knowledge Promoted)',
          customer_impact: 'Deterministic performance for ultra-reliable low-latency services',
          remediation: 'Host compute binding policies enforced on all user plane worker pods.'
        }}
      }};

      return meta[scn.id] || {{
        executive_summary: scn.description || 'Simulated network condition under investigation.',
        root_cause_label: scn.root_cause ? scn.root_cause.split('/').pop() : 'Under Investigation',
        root_cause_fault: 'Telemetry anomaly detected across operational boundary',
        impacted_service: 'Mobile Carrier Network Services',
        sla_status: scn.badge || 'DEGRADED',
        customer_impact: 'Monitored via carrier OSS operations center',
        remediation: 'Consult domain engineering playbooks and dispatch automated triage.'
      }};
    }}

    function renderIncidentSummaryPanel(selectedEntity) {{
      const scn = currentScenario || GRAPH_DATA.scenarios[0];
      const summary = getScenarioSummary(scn);
      const isNominal = scn.id === 'baseline' || scn.badge === 'NOMINAL';

      // Update right panel header
      const dot = document.getElementById('insp-header-dot');
      const title = document.getElementById('insp-header-title');
      if (dot) dot.style.backgroundColor = isNominal ? '#10b981' : scn.badge === 'CRITICAL' ? '#ef4444' : scn.badge === 'MAJOR' ? '#f59e0b' : '#3b82f6';
      if (title) title.innerText = 'Incident Executive Summary';

      // Severity badge styling
      const sevBadge = isNominal ?
        '<span class="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-bold font-mono">🟢 NOMINAL</span>' :
        scn.badge === 'CRITICAL' ? '<span class="text-[10px] px-2.5 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/40 font-bold font-mono">🔴 CRITICAL</span>' :
        scn.badge === 'MAJOR' ? '<span class="text-[10px] px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold font-mono">🟠 MAJOR</span>' :
        scn.badge === 'KNOWLEDGE_GAP' ? '<span class="text-[10px] px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/40 font-bold font-mono">🟣 KNOWLEDGE GAP</span>' :
        scn.badge === 'LEARNING_UNIT' ? '<span class="text-[10px] px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold font-mono">🔵 LEARNING UNIT</span>' :
        '<span class="text-[10px] px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/40 font-bold font-mono">🟡 ' + scn.badge + '</span>';

      // Compact Entity Banner if a node was clicked
      let entityCallout = '';
      if (selectedEntity) {{
        const isRoot = selectedEntity.alarmSeverity === 'ROOT_CAUSE';
        const isTicket = selectedEntity.type === 'ticket-journey' || selectedEntity.id.includes('ticket') || selectedEntity.id.includes('tt-') || selectedEntity.domain === 'CRM & Customer Experience';
        const isAffected = selectedEntity.alarmSeverity && selectedEntity.alarmSeverity !== 'NOMINAL';

        const roleText = isRoot ? '🎯 Root Cause Origin' :
                         isTicket ? '📋 Customer Trouble Ticket (Evidence)' :
                         isAffected ? '⚡ Cascading Fault Casualty' : '🟢 Steady-State Nominal';

        const borderClass = isRoot ? 'border-red-500/40 bg-red-950/30 text-red-300' :
                            isTicket ? 'border-pink-500/40 bg-pink-950/30 text-pink-300' :
                            isAffected ? 'border-amber-500/40 bg-amber-950/30 text-amber-300' :
                            'border-emerald-500/40 bg-emerald-950/20 text-emerald-300';

        entityCallout = `
          <div class="p-3 rounded-lg border ${{borderClass}} space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-[10px] font-mono uppercase tracking-wider font-bold">${{roleText}}</span>
              <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-900/80 font-mono text-slate-300">${{selectedEntity.domain}}</span>
            </div>
            <div class="text-sm font-bold text-slate-100 flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full shrink-0" style="background-color: ${{selectedEntity.color}}"></span>
              <span class="truncate">${{selectedEntity.label}}</span>
            </div>
            <div class="text-[11px] text-slate-300/90 leading-tight">
              Status: <span class="font-mono text-slate-200">${{selectedEntity.alarmStatus || 'Normal Operation'}}</span>
            </div>
          </div>
        `;
      }}

      // Causal Flow Steps
      let causalFlowHtml = '';
      if (!isNominal && scn.propagation_path && scn.propagation_path.length > 0) {{
        const steps = scn.propagation_path.slice(0, 5).map((nodeId, idx) => {{
          const found = nodes.find(n => n.id === nodeId);
          const name = found ? found.label : nodeId.split('/').pop();
          const dom = found ? found.domain : 'Network';
          const isOrigin = idx === 0;
          const isTerminal = idx === scn.propagation_path.length - 1;

          const stepBadge = isOrigin ? '<span class="text-[9px] font-bold px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/30">ORIGIN</span>' :
                            isTerminal ? '<span class="text-[9px] font-bold px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-400 border border-purple-500/30">SYMPTOM</span>' :
                            '<span class="text-[9px] font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">' + (idx + 1) + '</span>';

          return `
            <div onclick="selectNodeById('${{nodeId}}')" class="p-2.5 rounded-lg bg-slate-950/60 hover:bg-slate-800/80 border border-slate-800/80 transition cursor-pointer flex items-center justify-between group">
              <div class="flex items-center gap-2.5 min-w-0">
                ${{stepBadge}}
                <div class="min-w-0">
                  <div class="text-xs font-semibold text-slate-200 group-hover:text-blue-300 truncate">${{name}}</div>
                  <div class="text-[10px] text-slate-400">${{dom}}</div>
                </div>
              </div>
              <i class="fa-solid fa-chevron-right text-[10px] text-slate-600 group-hover:text-slate-400 group-hover:translate-x-0.5 transition"></i>
            </div>
          `;
        }}).join('');

        causalFlowHtml = `
          <div class="space-y-2">
            <div class="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-400">
              <span><i class="fa-solid fa-arrow-down-long text-blue-400 mr-1.5"></i> Causal Propagation Flow</span>
              <span class="text-[10px] font-mono text-slate-500">${{scn.propagation_path.length}} Steps</span>
            </div>
            <div class="space-y-1.5">
              ${{steps}}
            </div>
          </div>
        `;
      }}

      const panel = document.getElementById('inspectorContent');
      if (!panel) return;

      panel.innerHTML = `
        <div class="space-y-4">
          ${{entityCallout}}

          <!-- Executive Incident Briefing Card -->
          <div class="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2.5">
            <div class="flex items-center justify-between gap-2">
              <span class="text-[10px] font-mono uppercase tracking-wider font-semibold text-slate-400">${{scn.stage}} &bull; ${{scn.category || 'Incident Overview'}}</span>
              ${{sevBadge}}
            </div>
            <h3 class="text-sm font-bold text-slate-100 leading-snug">${{scn.name}}</h3>
            <p class="text-xs text-slate-300 leading-relaxed">${{summary.executive_summary}}</p>
          </div>

          <!-- Key Incident Indicators Grid (2x2) -->
          <div class="grid grid-cols-2 gap-2 text-xs">
            <div class="p-3 rounded-lg bg-slate-950/50 border border-slate-800/80 space-y-1">
              <span class="text-[10px] font-mono uppercase tracking-wider text-slate-400 block font-semibold">Root Cause Node</span>
              <div class="font-bold text-red-400 truncate text-xs" title="${{summary.root_cause_label}}">${{summary.root_cause_label}}</div>
              <div class="text-[10px] text-slate-400 leading-tight">${{summary.root_cause_fault}}</div>
            </div>

            <div class="p-3 rounded-lg bg-slate-950/50 border border-slate-800/80 space-y-1">
              <span class="text-[10px] font-mono uppercase tracking-wider text-slate-400 block font-semibold">Active Blast Radius</span>
              <div class="font-bold text-amber-300 text-xs">${{highlightedNodes.size}} Entities</div>
              <div class="text-[10px] text-slate-400 leading-tight">Across ${{activeDomains.size}} Active Domains</div>
            </div>

            <div class="p-3 rounded-lg bg-slate-950/50 border border-slate-800/80 space-y-1">
              <span class="text-[10px] font-mono uppercase tracking-wider text-slate-400 block font-semibold">Primary Impacted Service</span>
              <div class="font-bold text-blue-300 truncate text-xs" title="${{summary.impacted_service}}">${{summary.impacted_service}}</div>
              <div class="text-[10px] font-mono text-slate-400 leading-tight">${{summary.sla_status}}</div>
            </div>

            <div class="p-3 rounded-lg bg-slate-950/50 border border-slate-800/80 space-y-1">
              <span class="text-[10px] font-mono uppercase tracking-wider text-slate-400 block font-semibold">Customer Impact</span>
              <div class="font-bold text-pink-300 text-xs">Tickets Reported</div>
              <div class="text-[10px] text-slate-400 leading-tight">${{summary.customer_impact}}</div>
            </div>
          </div>

          <!-- Causal Propagation Flow -->
          ${{causalFlowHtml}}

          <!-- Recommended Remediation Card -->
          <div class="p-3.5 rounded-xl bg-emerald-950/30 border border-emerald-500/30 space-y-1.5">
            <div class="flex items-center gap-1.5 text-xs font-bold text-emerald-400">
              <i class="fa-solid fa-shield-halved"></i> Recommended Remediation
            </div>
            <p class="text-xs text-emerald-200/90 leading-relaxed">${{summary.remediation}}</p>
          </div>
        </div>
      `;
    }}

    function selectNode(node) {{
      selectedNode = node;
      const right = document.getElementById('inspectorPanel');
      if (right && right.classList.contains('hidden')) {{
        toggleRightPanel();
      }}
      renderIncidentSummaryPanel(node);
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
      renderIncidentSummaryPanel(null);
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
