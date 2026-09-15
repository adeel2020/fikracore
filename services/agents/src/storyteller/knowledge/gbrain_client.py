"""gbrain transport client — talks to the running gbrain brain.

Layer 1 (Knowledge / Retrieval) transport. Backends:

1. ``http`` — HTTP MCP endpoint (``GBRAIN_MCP_URL`` + optional
   ``GBRAIN_MCP_TOKEN``), JSON-RPC 2.0 POST to ``<url>/mcp``. This is the
   primary storyteller transport and works while a ``gbrain serve --http``
   process owns the brain.

2. ``subprocess`` — legacy fallback for direct ``gbrain call <tool> '<json>'``
   dispatch when ``cli`` is explicitly specified and CLI binary is found on PATH.

3. ``embedded`` — in-memory mobile-core graph & fixture knowledge base. When
   neither the gbrain HTTP MCP server nor CLI is available, this transport
   serves all schema operations (``get_page``, ``traverse_graph``, ``list_pages``,
   ``query``) to ensure continuous, resilient operations.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MCP_URL = "http://localhost:3131"


class GbrainError(RuntimeError):
    """Raised when gbrain returns an error envelope or the transport fails."""


def _read_dotenv_value(path: str, key: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                if name.strip() != key:
                    continue
                return value.strip().strip("'\"")
    except OSError:
        return None
    return None


def _env_value(key: str) -> str | None:
    value = os.environ.get(key)
    if value:
        return value

    here = os.path.abspath(__file__)
    candidates: list[str] = []
    cur = os.path.dirname(here)
    while True:
        candidates.append(os.path.join(cur, ".env"))
        candidates.append(os.path.join(cur, "backend", ".env"))
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent

    cwd = os.getcwd()
    candidates.append(os.path.join(cwd, ".env"))
    candidates.append(os.path.join(cwd, "backend", ".env"))

    seen: set[str] = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        value = _read_dotenv_value(path, key)
        if value:
            return value
    return None


def _normalize_result(payload: Any) -> Any:
    """gbrain ops may return an ``{error: ...}`` envelope — raise on it."""
    if isinstance(payload, dict) and "error" in payload and isinstance(payload["error"], str):
        raise GbrainError(payload["error"])
    return payload


# ---------------------------------------------------------------------------
# Embedded Knowledge Graph & Fixture Catalog
# ---------------------------------------------------------------------------
_EMBEDDED_PAGES: dict[str, dict[str, Any]] = {
    "mobile-core/incidents/amf-overload-2026-08-09": {
        "slug": "mobile-core/incidents/amf-overload-2026-08-09",
        "type": "incident",
        "title": "AMF-01 overload and high registration rejection",
        "frontmatter": {
            "severity": "SEV-2",
            "status": "resolved",
            "started_at": "2026-08-09T06:14:00Z",
            "resolved_at": "2026-08-09T07:05:00Z",
            "correlation_key": "amf-core-overload-01",
            "correlation_score": 0.94,
        },
        "compiled_truth": (
            "# AMF-01 overload and high registration rejection\n\n"
            "## Summary\nCritical registration failure burst in Dubai Core DC-1 triggered by CPU saturation on AMF-01.\n\n"
            "## Timeline\n"
            "- **06:14:00Z** — RSR (Registration Success Rate) dropped below threshold to 94.7%.\n"
            "- **06:22:15Z** — Correlated alarm candidate formed with 98% CPU saturation.\n"
            "- **06:45:00Z** — Automated remediation added AMF-01 capacity.\n"
            "- **07:05:00Z** — RSR recovered to 99.9%.\n"
        ),
    },
    "incidents/mobile-core/sgi-throughput-drop": {
        "slug": "incidents/mobile-core/sgi-throughput-drop",
        "type": "incident",
        "title": "SGi Data Forwarding Throughput Drop",
        "frontmatter": {
            "severity": "SEV-1",
            "status": "investigating",
            "started_at": "2026-08-31T07:10:00Z",
            "correlation_key": "a154bb7a3997859c",
            "correlation_score": 0.95,
            "canonical_slug": "incidents/mobile-core/sgi-data-a154bb7a3997859c",
            "legacy_aliases": ["mobile-core/incidents/sgi-throughput-drop", "mobile-core/incidents/sgi-data-a154bb7a3997859c"],
            "contributing_domains": ["mobile-core", "transport"],
        },
        "compiled_truth": (
            "# SGi Data Forwarding Throughput Drop\n\n"
            "## Summary\nSevere throughput degradation and packet discards across SGi egress interface and GiLAN firewall.\n\n"
            "## Timeline\n"
            "- **07:10:00Z** — SGI_THROUGHPUT_DROP critical alarm on pgw-01.\n"
            "- **07:12:00Z** — NAT_SESSION_TABLE_HIGH major alarm on nat-fw-01.\n"
            "- **07:14:00Z** — INTERFACE_DISCARDS_HIGH on transport edge router sgi-edge-01.\n"
            "- **07:15:00Z** — SGi Throughput fell below committed service intent threshold.\n"
        ),
    },
    "incidents/mobile-core/sgi-data-a154bb7a3997859c": {
        "slug": "incidents/mobile-core/sgi-data-a154bb7a3997859c",
        "type": "incident",
        "title": "SGi Data Forwarding Throughput Drop",
        "frontmatter": {
            "severity": "SEV-1",
            "status": "investigating",
            "started_at": "2026-08-31T07:10:00Z",
            "correlation_key": "a154bb7a3997859c",
            "correlation_score": 0.95,
            "canonical_slug": "incidents/mobile-core/sgi-data-a154bb7a3997859c",
            "legacy_aliases": ["mobile-core/incidents/sgi-throughput-drop", "incidents/mobile-core/sgi-throughput-drop"],
            "contributing_domains": ["mobile-core", "transport"],
        },
        "compiled_truth": (
            "# SGi Data Forwarding Throughput Drop\n\n"
            "## Summary\nSevere throughput degradation and packet discards across SGi egress interface and GiLAN firewall.\n\n"
            "## Timeline\n"
            "- **07:10:00Z** — SGI_THROUGHPUT_DROP critical alarm on pgw-01.\n"
            "- **07:12:00Z** — NAT_SESSION_TABLE_HIGH major alarm on nat-fw-01.\n"
            "- **07:14:00Z** — INTERFACE_DISCARDS_HIGH on transport edge router sgi-edge-01.\n"
            "- **07:15:00Z** — SGi Throughput fell below committed service intent threshold.\n"
        ),
    },
    "incidents/mobile-core/lte-attach-54db6ef325fbf758": {
        "slug": "incidents/mobile-core/lte-attach-54db6ef325fbf758",
        "type": "incident",
        "title": "LTE Attach Failure & S1-MME Path Degradation",
        "frontmatter": {
            "severity": "SEV-1",
            "status": "investigating",
            "started_at": "2026-08-31T11:00:00Z",
            "correlation_key": "lte-attach-54db6ef325fbf758",
            "correlation_score": 0.91,
        },
        "compiled_truth": (
            "# LTE Attach Failure\n\n"
            "## Summary\nIntermittent LTE attach failures affecting 14,200 subscribers across Dubai North eNodeBs.\n\n"
            "## Timeline\n"
            "- **11:00:00Z** — 4G_Attach_SR KPI fell to 88.2%.\n"
            "- **11:04:37Z** — High latency detected on S1-MME transport link.\n"
        ),
    },
    "network-functions/amf": {
        "slug": "network-functions/amf",
        "type": "network-function",
        "title": "Access and Mobility Management Function (AMF-01)",
        "frontmatter": {"summary": "Core 5GC control plane function handling registration, reachability, and mobility management."},
        "compiled_truth": "AMF handles UE registration, connection management, NAS signaling, and mobility management in 5G Core.",
    },
    "network-functions/upf": {
        "slug": "network-functions/upf",
        "type": "network-function",
        "title": "User Plane Function (UPF Core Pod 3)",
        "frontmatter": {"summary": "Core 5GC user plane function performing packet routing, QoS enforcement, and uplink/downlink forwarding."},
        "compiled_truth": "UPF handles packet routing and forwarding, data buffering, and QoS enforcement between gNodeB and Data Networks (DN).",
    },
    "network-functions/smf": {
        "slug": "network-functions/smf",
        "type": "network-function",
        "title": "Session Management Function (SMF-01)",
        "frontmatter": {"summary": "Core 5GC control plane function managing PDU session lifecycle, IP address allocation, and UPF selection."},
        "compiled_truth": "SMF establishes, modifies, and releases PDU sessions, and controls UPF forwarding policies.",
    },
    "network-functions/gnb": {
        "slug": "network-functions/gnb",
        "type": "network-function",
        "title": "Next Generation NodeB (gNodeB / RAN Site 42)",
        "frontmatter": {"summary": "5G NR Radio Access Network base station providing radio connectivity to user equipment."},
        "compiled_truth": "gNodeB connects mobile devices over NR-Uu interface and connects to AMF via N2 and UPF via N3.",
    },
    "kpi/rsr": {
        "slug": "kpi/rsr",
        "type": "kpi",
        "title": "Registration Success Rate (RSR)",
        "frontmatter": {"unit": "percent", "threshold": "98.5%"},
        "compiled_truth": "RSR measures the ratio of successful initial registration procedures against total attempts.",
    },
    "kpi-event/rsr-breach": {
        "slug": "kpi-event/rsr-breach",
        "type": "kpi-event",
        "title": "RSR Critical Breach (94.7% at 06:14)",
        "frontmatter": {"value": 94.7, "unit": "percent", "event_type": "alarm", "threshold": "critical", "observed_at": "2026-08-09T06:14:00Z"},
        "compiled_truth": "Observed severe degradation in registration success rate across DC-1.",
    },
    "symptom/reg-fail-spike": {
        "slug": "symptom/reg-fail-spike",
        "type": "symptom",
        "title": "Registration Failure Burst Spike",
        "frontmatter": {},
        "compiled_truth": "Bursts of 5G NAS Registration Reject messages with Cause 22 (Congestion).",
    },
    "hyp/amf-cpu-sat": {
        "slug": "hyp/amf-cpu-sat",
        "type": "hypothesis",
        "title": "AMF-01 CPU saturation from registration load",
        "frontmatter": {"status": "confirmed", "confidence": 0.94},
        "compiled_truth": "AMF-01 worker processes reached 98% CPU utilization causing NAS buffer drops.",
    },
    "ev/cpu-98": {
        "slug": "ev/cpu-98",
        "type": "evidence",
        "title": "AMF-01 CPU utilization metric pegged at 98%",
        "frontmatter": {"source": "prometheus/dc1-amf", "observed_at": "2026-08-09T06:18:00Z"},
        "compiled_truth": "Prometheus metric node_cpu_seconds_total indicated sustained saturation.",
    },
    "ev/nas-reject": {
        "slug": "ev/nas-reject",
        "type": "evidence",
        "title": "NAS REGISTRATION REJECT 'congestion' cause in trace logs",
        "frontmatter": {"source": "pcaps/sgi-core", "observed_at": "2026-08-09T06:20:00Z"},
        "compiled_truth": "Packet traces captured repeated 5GMM Cause #22 returned to UEs.",
    },
    "rem/capacity": {
        "slug": "rem/capacity",
        "type": "remediation",
        "title": "Scale AMF-01 Pod Replicas & Add Capacity MOP",
        "frontmatter": {},
        "compiled_truth": "Executed automated scaling playbook increasing AMF worker pods from 4 to 8.",
    },
    "rec/rsr-recovered": {
        "slug": "rec/rsr-recovered",
        "type": "kpi-event",
        "title": "RSR Recovered to 99.9% at 07:05",
        "frontmatter": {"value": 99.9, "unit": "percent", "observed_at": "2026-08-09T07:05:00Z"},
        "compiled_truth": "Telemetry confirms stable RSR above SLA threshold.",
    },
    "services/ue-registration": {
        "slug": "services/ue-registration",
        "type": "service",
        "title": "5G Initial UE Registration & Mobility",
        "frontmatter": {},
        "compiled_truth": "End-to-end subscriber access service connecting UE to 5G Core.",
    },
    "telecom-brain/domains/mobile-core/roles/mobile-rtr/pipeline": {
        "slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/pipeline",
        "type": "procedure",
        "title": "Mobile RTR Multi-Stage Investigation & Troubleshooting Pipeline",
        "frontmatter": {
            "engine": "telecom_brain",
            "domain": "Mobile Core",
            "role": "Mobile RTR",
            "stages": 7,
            "governance": "Read-only Core RTR, IT Provisioning handoff with BSS Order ID",
        },
        "compiled_truth": (
            "# Mobile RTR Multi-Stage Investigation Pipeline\n\n"
            "## Architecture Overview\n"
            "Mobile Core RTR is the primary anchor for all customer trouble tickets arriving from Customer Operations. "
            "Every ticket progresses through a strict, multi-domain pipeline with checkpoint gates:\n\n"
            "### STAGE 0: Ingestion & Frontline Precheck Validation Gate\n"
            "- Validates mandatory ticket attributes: MSISDN, IMSI, Timestamp within 48h, Location/Cell, Service Concern.\n"
            "- Verifies Frontline prechecks: CRM active line status, overdue bill suspension, handset capability.\n"
            "- Checkpoint Gate 0: Rejection on missing info or skipped frontline prechecks.\n\n"
            "### STAGE 1: Customer Location Discovery & Core Profile Audit\n"
            "- Location Discovery: 3G VLR GT, 4G USN/MME-FQDN, 5G AMF-UE-NGAP-ID/GUTI.\n"
            "- Profile Inspection: UDM / HSS / IMSS / DYNSUB / PCF / OSIX probe.\n"
            "- Checkpoint Gate 1: If Core profile mismatches BSS plan (~70% of tickets), package with BSS Activation Order ID and remediation MML, then hand off to IT Provisioning.\n\n"
            "### STAGE 2: Multi-Domain Checklist for IT Profile & Subscriptions\n"
            "- BSS / OCS / IN Checks: Active bundles, FUP throttling (64/128kbps), credit/CLR, CUG.\n"
            "- Diameter Gy MSCC Rating-Group (AVP 432) quota validation; Smart CDR inspection on CSRD.\n"
            "- Checkpoint Gate 2: Commercial FUP / Overdue suspension rejection, or OCS L2 escalation on Diameter 5031.\n\n"
            "### STAGE 3: Roaming Domain Specific Checklist (When Roaming)\n"
            "- Bypassed if subscriber is domestic (MCC/MNC matches Home Operator).\n"
            "- Roaming Checks: Preferred partners (SoR), 3G sunset / missing S8HR VoLTE, IR profile, Enterprise OIG barring.\n"
            "- Checkpoint Gate 3: Escalate to Roaming Support Team or package BSS order for missing S8HR VoLTE.\n\n"
            "### STAGE 4: Active Troubleshooting & Device Recovery\n"
            "- Active Procedures: Core node CDR validation (SGW/PGW/UPF/GMSC/IMS), release cause extraction, customer screenshot review.\n"
            "- Handset resets: APN 'wap' -> 'internet', data roaming toggle, VoLTE switch.\n"
            "- Node cleanup: Clear stuck PDP/EPS bearer session via SET GPRSLOCK: UNLOCK; power-cycle restart advisory.\n"
            "- Checkpoint Gate 4: Resolve Tier-1 device/session issues.\n\n"
            "### STAGE 5: Deeper Multi-Protocol Signaling Trace Diagnostics (Last 1-2 Days)\n"
            "- Protocol Traces: CAP ERBCSM routeSelectFailure (Leg 2), SIP 500/487/488/486, ISUP CV-1/16/17/21/34/38/41/127, "
            "Diameter Gx/Gy/Ro via SPS/DRA, GTPv2 Cause 8 cross-correlation with Gx CCA UAF, HTTP/2 SBI (N7/N10/N11), NGAP Cause 22, S1AP/SGsAP.\n"
            "- Checkpoint Gate 5: Classify finding as System-Level vs. User/Device-Level.\n\n"
            "### STAGE 6: Two-Tier Escalation Hierarchy & Disposition Lifecycle\n"
            "- Core Defect: CS/PS/VAS Core L2 Operations -> Vendor (Ericsson/Nokia/Huawei) Case (Tier 2 last resort).\n"
            "- IT/BSS Defect: IT/BSS/OCS/IN L2 Operations -> Dev Team PDI (Problem Defect Investigation, Tier 2 last resort).\n"
            "- Roaming Partner Defect: Roaming Support Team.\n"
            "- User / Frontline: Feedback advisory to Customer Operations.\n"
        ),
    },
    "telecom-brain/domains/mobile-core/roles/mobile-rtr/concern-findings-matrix": {
        "slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/concern-findings-matrix",
        "type": "knowledge-matrix",
        "title": "Mobile RTR Service Concern vs Technical Findings & Telemetry Matrix",
        "frontmatter": {
            "engine": "telecom_brain",
            "primary_volume": "Provisioning/Activation (~70%)",
        },
        "compiled_truth": (
            "# Mobile RTR Service Concern vs Technical Findings & Telemetry Matrix\n\n"
            "## Reporting Methodology\n"
            "Ticket categories are based on customer concerns, while technical errors and cause values serve as investigative findings.\n\n"
            "| Service Concern | Typical Disposition | Reason / Resolution Code | Technical Findings | Target Action |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            "| Provisioning & Activation | REASSIGNED (~70%) | PROV_MISMATCH_CORE_BSS | BSS Order COMPLETED but UDM missing APN profile or S-NSSAI slice; SPS/DRA Gx CCA UAF. | IT Provisioning Handoff with BSS Order ID & Remediation MML |\n"
            "| MNP Definition & Routing | REASSIGNED (~5%) | SPS_MNP_ROUTING_MISMATCH | Ported-in number missing RN prefix in SPS/DRA routing table; calls route to donor. | SPS / Signaling Operations Team |\n"
            "| Voice / VoLTE Call Failure | REASSIGNED / RESOLVED | CORE_ROUTING_DEFECT / RES_VOLTE_ENABLED | CAP ERBCSM Leg 2 routeSelectFailure (DP 4); SIP 500 / 488; IMSS profile missing. | Core IMS L2 or Handset VoLTE toggle reset |\n"
            "| Data Slowness & Speed | REJECTED / RESOLVED | COMMERCIAL_FUP_THROTTLED / RES_APN_CORRECTED | Gy Rating-Group 432 quota exhausted (throttled to 64k); Handset APN set to 'wap'. | Top-Up Guidance or Correct APN to 'internet' |\n"
            "| Barring & Latch Issues | RESOLVED / REJECTED | RES_STUCK_SESSION_UNLOCKED / COMMERCIAL_SUSPENDED | Stuck PDP session on USN (SET GPRSLOCK: UNLOCK); Line suspended for overdue bill. | Core RTR Session Unlock or Frontline Rejection |\n"
            "| Missing Frontline Prechecks | REJECTED | MISSING_FRONTLINE_PRECHECKS | Customer Operations skipped active CRM check or line suspension status. | Frontline Training Notice |\n"
            "| Missing Mandatory Info | REJECTED | MISSING_MANDATORY_INFO | Ticket missing MSISDN, event timestamp within 48h, or specific symptom. | Frontline Resubmission Request |\n"
            "| Roaming / Inaccessibility | REASSIGNED | ROAMING_PARTNER_DEFECT | Visited network 3G sunset + missing S8HR VoLTE; SoR anti-steering reject; CV-38 carrier drop. | Roaming Support Team / Carrier Wholesale |\n"
        ),
    },
    "telecom-brain/domains/mobile-core/roles/mobile-rtr/services-and-tools-catalog": {
        "slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/services-and-tools-catalog",
        "type": "catalog",
        "title": "Mobile RTR Telecom Services Portfolio and Diagnostic Tools Catalog",
        "frontmatter": {
            "engine": "telecom_brain",
            "coverage": "Basic & Extended Telecom Services",
        },
        "compiled_truth": (
            "# Mobile RTR Services Portfolio & Diagnostic Tools Catalog\n\n"
            "## Telecom Services Coverage\n"
            "1. Multi-Device / Multi-SIM: OneNumber pairing, Entitlement Server (TS.43), UDM multi-SIM pairing, IMS SIP INVITE forking.\n"
            "2. POS Devices & IoT: Dedicated static APN (pos.bank), USN GPRSLOCK, GTPv2 Cause 27/73, CSRD CDR data check.\n"
            "3. Corporate Private APNs: Radius/AAA server authentication, IPSec/GRE enterprise data center tunnel, UDM SUBAPN.\n"
            "4. eSIM Profile Services: Remote SIM Provisioning via SM-DP+, EID validation, customer screenshot review.\n"
            "5. VMS (Voice Mail System): Diversion routing, Message Waiting Indication (MWI SIP NOTIFY / SMS), VMS trunk saturation (CV-34).\n"
            "6. MCN (Missed Call Notification): CAMEL T-CSI trigger to MCN platform, SMSC submit-SM queue monitoring.\n"
            "7. Call Forwarding (CF): CFU/CFB/CFNRY/CFNRC, Enterprise OIG international barring, forwarding loop detection.\n"
            "8. CNAP (Calling Name Presentation): CNAP database sync, SIP P-Asserted-Identity display name verification.\n"
            "9. Hashtag (#Tag) / USSD: Interactive USSD self-care routing on USSD Gateway, MAP ProcessUnstructuredSS.\n"
            "10. Toll-Free Numbers (TFN 800): Reverse charging via IN/OCS SCP, CAMEL/CAP translation to target number.\n\n"
            "## Diagnostic Tools Portfolio\n"
            "- Entitlement Server GUI (TS.43 smartwatch pairing)\n"
            "- SM-DP+ Portal (eSIM profile lifecycle)\n"
            "- Radius / AAA Logs (Corporate APN access authentication)\n"
            "- USSD Gateway Console (#Tag and self-care codes)\n"
            "- IN / OCS SCP Care Portal (TFN 800 translation and reverse rating)\n"
            "- OSIX Signaling Probe (Multi-protocol real-time tracing)\n"
            "- CSRD (Call Detail Records & CDR usage auditing)\n"
            "- Huawei iMaster NCE / LMT (Core node MML inspection)\n"
            "- SPS / DRA Portal (Diameter routing and MNP table lookup)\n"
        ),
    },
    "telecom-brain/domains/mobile-core/roles/mobile-rtr/huawei-mml-runbooks": {
        "slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/huawei-mml-runbooks",
        "type": "runbook",
        "title": "Mobile Core RTR Huawei MML Runbooks: Read-Only Audit vs IT Provisioning Remediation",
        "frontmatter": {
            "engine": "telecom_brain",
            "vendor": "Huawei",
            "tool": "iMaster NCE / LMT",
        },
        "compiled_truth": (
            "# Huawei MML Runbook Governance for Mobile Core RTR\n\n"
            "## Operational Authority Model\n"
            "Core RTR engineers execute read-only queries and transient session cleanups. "
            "Write commands altering commercial/subscriber entitlements are packaged with BSS Order IDs for IT Provisioning.\n\n"
            "### 1. Core RTR Read-Only Inspection MML\n"
            "```text\n"
            "DSP SUBAPN: MSISDN=\"97150xxxxxxx\";\n"
            "LST APN: APN=\"internet\";\n"
            "DSP UDM5GSUB: MSISDN=\"97150xxxxxxx\", SNSSAI=1-010203;\n"
            "DSP PCFPOLICY: SUBSCRIBERID=\"97150xxxxxxx\";\n"
            "CHK 5GSUBALIGN: MSISDN=\"97150xxxxxxx\";\n"
            "DSP SUBCSI: MSISDN=\"97150xxxxxxx\";\n"
            "DSP SUBBAR: MSISDN=\"97150xxxxxxx\";\n"
            "DSP ROAMPOLICY: MSISDN=\"97150xxxxxxx\", MCC=310, MNC=410;\n"
            "DSP EPSSUB: MSISDN=\"97150xxxxxxx\";\n"
            "DSP GPRSLOCK: MSISDN=\"97150xxxxxxx\";\n"
            "```\n\n"
            "### 2. IT Provisioning Remediation MML (Packaged with BSS Activation Order ID)\n"
            "```text\n"
            "-- Correlated BSS Activation Order ID: ORD-20260907-883921\n"
            "MOD SUBAPN: MSISDN=\"97150xxxxxxx\", APN=\"internet\", MAXBITRATEUL=100000, MAXBITRATEDL=300000;\n"
            "MOD UDM5GSUB: MSISDN=\"97150xxxxxxx\", SNSSAI=1-010203, SST=1, SD=\"010203\", DEFAULTDNN=\"internet\";\n"
            "MOD PCFPOLICY: SUBSCRIBERID=\"97150xxxxxxx\", SERVICENAME=\"5G_SA_MOBILE_BB\", SLICERULE=ALLOW;\n"
            "MOD SUBCSI: MSISDN=\"97150xxxxxxx\", CSITYPE=OCSI, GSMSCFGT=\"97150xxxxxxx\", DEFCALLHANDLING=CONTINUE;\n"
            "MOD SUBBAR: MSISDN=\"97150xxxxxxx\", BAOC=NO, BAIC=NO, BOIC=NO, BICROAM=NO, BOCROAM=NO;\n"
            "MOD EPSSUB: MSISDN=\"97150xxxxxxx\", ROAMALLOW=YES, COMBINEDATTACH=YES, DEFAPN=\"internet\";\n"
            "```\n\n"
            "### 3. Core RTR Transient Stale Latch Cleanup Commands\n"
            "```text\n"
            "PURGE MS: MSISDN=\"97150xxxxxxx\", IMSI=\"42402xxxxxxxxxx\";\n"
            "CANCEL LOC: MSISDN=\"97150xxxxxxx\", VLRID=VLR_DUBAI_01;\n"
            "SET GPRSLOCK: MSISDN=\"97150xxxxxxx\", STATUS=UNLOCK;\n"
            "```\n"
        ),
    },
    "telecom-brain/domains/mobile-core/roles/mobile-rtr/customer-ticket-journey": {
        "slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/customer-ticket-journey",
        "type": "procedure",
        "title": "Customer Trouble Ticket Journey: Schema, SLA Hierarchy & Bouncing Rules",
        "frontmatter": {
            "engine": "telecom_brain",
            "domain": "Mobile Core",
            "role": "Mobile RTR",
            "aola_target_hours": 2.0,
            "ola_target_hours": 6.0,
            "sla_target_hours": 48.0,
        },
        "compiled_truth": (
            "# Customer Trouble Ticket Journey\n\n"
            "## SLA Hierarchy\n"
            "- AOLA: <= 2.0 hours inside RTR queues (RTR_Mobile_Core).\n"
            "- OLA: <= 6.0 hours across all internal Core/NOC queues.\n"
            "- E2E SLA: <= 48.0 hours from CRM creation to customer resolution.\n\n"
            "## Zero-PII Mandate\n"
            "Customer identities must be pseudonymized using ticket_token and subscriber_token.\n"
        ),
    },
    "telecom-brain/domains/mobile-core/roles/mobile-rtr/queue-topology": {
        "slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/queue-topology",
        "type": "topology",
        "title": "Mobile Core RTR Queue Topology & Reassignment Matrix",
        "frontmatter": {
            "engine": "telecom_brain",
            "domain": "Mobile Core",
            "role": "Mobile RTR",
        },
        "compiled_truth": (
            "# Mobile Core RTR Queue Topology\n\n"
            "Queues: RTR_Mobile_Core, HPSA, Billing, OCS, IN, CS_L2, PS_L2, VAS_L2, BSS, SRO, CS, PS, VAS, IREG, Core_IMEI, SD, IW, CRM_Frontline.\n"
            "Rules: Direct ingestion allowed from CRM/SD. Handoff to HPSA/Billing requires BSS Activation Order ID.\n"
        ),
    },
    "telecom-brain/domains/mobile-core/roles/mobile-rtr/rtr-curated-summary": {
        "slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/rtr-curated-summary",
        "type": "summary",
        "title": "Mobile Core RTR Shift-Level Curated Ticket Summary",
        "frontmatter": {
            "engine": "telecom_brain",
            "domain": "Mobile Core",
            "role": "Mobile RTR",
        },
        "compiled_truth": (
            "# Mobile Core RTR Shift Curated Summary\n\n"
            "Aggregates ticket volume, first-touch resolutions, AOLA/OLA compliance, top delinquent dwell queues, and frontline leakage rates.\n"
        ),
    },
}

_EMBEDDED_EDGES: list[dict[str, str]] = [
    {"from_slug": "incidents/mobile-core/sgi-throughput-drop", "to_slug": "incidents/mobile-core/sgi-data-a154bb7a3997859c", "link_type": "canonical"},
    {"from_slug": "incidents/mobile-core/sgi-throughput-drop", "to_slug": "services/sgi-data", "link_type": "affects"},
    {"from_slug": "incidents/mobile-core/sgi-throughput-drop", "to_slug": "network-functions/upf", "link_type": "involves"},
    {"from_slug": "incidents/mobile-core/sgi-data-a154bb7a3997859c", "to_slug": "services/sgi-data", "link_type": "affects"},
    {"from_slug": "incidents/mobile-core/sgi-data-a154bb7a3997859c", "to_slug": "network-functions/upf", "link_type": "involves"},
    {"from_slug": "mobile-core/incidents/amf-overload-2026-08-09", "to_slug": "kpi-event/rsr-breach", "link_type": "detected-by"},
    {"from_slug": "kpi-event/rsr-breach", "to_slug": "kpi/rsr", "link_type": "measures"},
    {"from_slug": "mobile-core/incidents/amf-overload-2026-08-09", "to_slug": "network-functions/amf", "link_type": "involves"},
    {"from_slug": "mobile-core/incidents/amf-overload-2026-08-09", "to_slug": "network-functions/smf", "link_type": "involves"},
    {"from_slug": "mobile-core/incidents/amf-overload-2026-08-09", "to_slug": "services/ue-registration", "link_type": "affects"},
    {"from_slug": "mobile-core/incidents/amf-overload-2026-08-09", "to_slug": "symptom/reg-fail-spike", "link_type": "has-symptom"},
    {"from_slug": "mobile-core/incidents/amf-overload-2026-08-09", "to_slug": "hyp/amf-cpu-sat", "link_type": "has-hypothesis"},
    {"from_slug": "hyp/amf-cpu-sat", "to_slug": "ev/cpu-98", "link_type": "supported-by"},
    {"from_slug": "hyp/amf-cpu-sat", "to_slug": "ev/nas-reject", "link_type": "supported-by"},
    {"from_slug": "mobile-core/incidents/amf-overload-2026-08-09", "to_slug": "rem/capacity", "link_type": "has-remediation"},
    {"from_slug": "rem/capacity", "to_slug": "network-functions/amf", "link_type": "targets"},
    {"from_slug": "rem/capacity", "to_slug": "rec/rsr-recovered", "link_type": "verified-by"},
    {"from_slug": "network-functions/amf", "to_slug": "network-functions/smf", "link_type": "connected-to"},
    {"from_slug": "network-functions/smf", "to_slug": "network-functions/upf", "link_type": "connected-to"},
    {"from_slug": "network-functions/gnb", "to_slug": "network-functions/amf", "link_type": "connected-to"},
    {"from_slug": "network-functions/gnb", "to_slug": "network-functions/upf", "link_type": "connected-to"},
    {"from_slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/pipeline", "to_slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/concern-findings-matrix", "link_type": "classifies-with"},
    {"from_slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/pipeline", "to_slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/services-and-tools-catalog", "link_type": "diagnoses"},
    {"from_slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/pipeline", "to_slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/huawei-mml-runbooks", "link_type": "executes-with"},
    {"from_slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/pipeline", "to_slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/customer-ticket-journey", "link_type": "structures-journey"},
    {"from_slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/customer-ticket-journey", "to_slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/queue-topology", "link_type": "routes-through"},
    {"from_slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/customer-ticket-journey", "to_slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/rtr-curated-summary", "link_type": "aggregated-by"},
    {"from_slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/pipeline", "to_slug": "network-functions/amf", "link_type": "audits"},
    {"from_slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/pipeline", "to_slug": "network-functions/smf", "link_type": "audits"},
    {"from_slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/pipeline", "to_slug": "network-functions/upf", "link_type": "audits"},
]


class GbrainClient:
    """Minimal op-dispatch client over gbrain through MARK's MCP hub with legacy fallbacks."""

    _cached_http_available: bool | None = None
    _cached_cli_available: bool | None = None

    def __init__(
        self,
        *,
        mcp_url: str | None = None,
        mcp_token: str | None = None,
        cli: str | None = None,
    ) -> None:
        os_mcp_url = os.environ.get("GBRAIN_MCP_URL")
        file_mcp_url = None if cli is not None else _env_value("GBRAIN_MCP_URL")
        env_mcp_url = os_mcp_url or file_mcp_url
        self.mcp_url = mcp_url or env_mcp_url or DEFAULT_MCP_URL
        self.mcp_token = mcp_token or _env_value("GBRAIN_MCP_TOKEN")
        self._explicit_cli = cli is not None
        self.cli = cli or _env_value("GBRAIN_CLI") or "gbrain"
        if GbrainClient._cached_http_available is False:
            self._http_mode = False
        else:
            self._http_mode = bool(self.mcp_url and (cli is None or mcp_url is not None or os_mcp_url is not None))

    def call(self, tool: str, params: dict[str, Any] | None = None) -> Any:
        """Dispatch a gbrain op by name through MCP hub first, then legacy fallbacks."""
        params = params or {}
        if self._http_mode and GbrainClient._cached_http_available is not False:
            try:
                res = self._call_mcp_hub(tool, params)
                GbrainClient._cached_http_available = True
                return res
            except Exception as e:
                logger.debug("gbrain MCP hub call failed (%s), trying legacy transports...", e)
                try:
                    res = self._call_http(tool, params)
                    GbrainClient._cached_http_available = True
                    return res
                except Exception as http_e:
                    logger.debug("gbrain HTTP MCP failed (%s), falling back to CLI/embedded...", http_e)
                    self._http_mode = False
                    GbrainClient._cached_http_available = False

        if self.cli == "embedded":
            return self._call_embedded_graph(tool, params)

        if GbrainClient._cached_cli_available is not False:
            try:
                res = self._call_subprocess(tool, params)
                GbrainClient._cached_cli_available = True
                return res
            except Exception:
                GbrainClient._cached_cli_available = False
                if self._explicit_cli:
                    raise

        return self._call_embedded_graph(tool, params)

    def _call_mcp_hub(self, tool: str, params: dict[str, Any]) -> Any:
        """Route gbrain MCP traffic through the shared MARK MCP Client Hub."""
        from mcp_hub import get_default_mcp_client_hub

        return _normalize_result(get_default_mcp_client_hub().call_tool_sync("gbrain", tool, params))

    # ------------------------------------------------------------------
    # Subprocess backend: `gbrain call <tool> '<json>'`
    # ------------------------------------------------------------------
    def _call_subprocess(self, tool: str, params: dict[str, Any]) -> Any:
        binary = shutil.which(self.cli)
        if not binary:
            raise GbrainError(f"gbrain CLI not found on PATH: '{self.cli}'")
        argv = [binary, "call", tool, json.dumps(params)]
        try:
            proc = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise GbrainError(f"gbrain call '{tool}' timed out") from exc

        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip()
            raise GbrainError(f"gbrain call '{tool}' failed ({proc.returncode}): {err[:500]}")

        payload = _extract_json(proc.stdout)
        return _normalize_result(payload)

    # ------------------------------------------------------------------
    # HTTP MCP backend: JSON-RPC 2.0 POST to <url>/mcp
    # ------------------------------------------------------------------
    def _call_http(self, tool: str, params: dict[str, Any]) -> Any:
        base_url = self.mcp_url.rstrip("/")
        url = base_url if base_url.endswith("/mcp") else base_url + "/mcp"
        body = json.dumps(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": params}}
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            },
        )
        if self.mcp_token:
            req.add_header("Authorization", f"Bearer {self.mcp_token}")

        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read().decode("utf-8")
            data = _extract_mcp_payload(raw, resp.headers.get("Content-Type", ""))

        if "error" in data:
            raise GbrainError(f"gbrain op '{tool}' error: {data['error']}")
        result = data.get("result", {})
        content = result.get("content", [])
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                return _normalize_result(_extract_json(item.get("text", "")))
        return _normalize_result(result)

    # ------------------------------------------------------------------
    # Embedded fallback graph backend
    # ------------------------------------------------------------------
    def _call_embedded_graph(self, tool: str, params: dict[str, Any]) -> Any:
        """Handle gbrain tool ops from embedded knowledge base."""
        slug = params.get("slug", "")

        if tool == "get_page":
            if slug in _EMBEDDED_PAGES:
                return _EMBEDDED_PAGES[slug]
            for p_slug, page in _EMBEDDED_PAGES.items():
                if slug in p_slug or p_slug in slug or slug.split("/")[-1] == p_slug.split("/")[-1]:
                    return page
            return None

        elif tool == "traverse_graph":
            link_type = params.get("link_type")
            direction = params.get("direction", "out")
            matching_edges = []
            for edge in _EMBEDDED_EDGES:
                match_from = (edge["from_slug"] == slug or slug in edge["from_slug"])
                match_to = (edge["to_slug"] == slug or slug in edge["to_slug"])
                if direction == "out" and match_from:
                    if not link_type or edge["link_type"] == link_type:
                        matching_edges.append(edge)
                elif direction == "in" and match_to:
                    if not link_type or edge["link_type"] == link_type:
                        matching_edges.append(edge)
            return matching_edges

        elif tool == "list_pages":
            page_type = params.get("type")
            limit = int(params.get("limit", 20))
            pages = []
            for p in _EMBEDDED_PAGES.values():
                if not page_type or p.get("type") == page_type:
                    pages.append({"slug": p["slug"], "title": p.get("title"), "type": p.get("type")})
            return pages[:limit]

        elif tool == "query":
            q = (params.get("query") or params.get("question") or "").lower()
            results = []
            for p in _EMBEDDED_PAGES.values():
                haystack = f"{p['slug']} {p.get('title', '')} {p.get('compiled_truth', '')}".lower()
                if any(word in haystack for word in q.split() if len(word) > 2):
                    results.append({"slug": p["slug"], "title": p.get("title"), "type": p.get("type")})
            return {"results": results[: params.get("limit", 5)]}

        return {}


def _extract_json(text: str) -> Any:
    """Pull the first JSON value (object or array) out of mixed stdout."""
    text = text.strip()
    for i, ch in enumerate(text):
        if ch in "{[":
            start = i
            try:
                return json.loads(text[start:])
            except json.JSONDecodeError:
                break
    raise GbrainError(f"No JSON payload in gbrain output: {text[:300]}")


def _extract_mcp_payload(text: str, content_type: str = "") -> Any:
    """Extract the JSON-RPC payload from JSON or MCP SSE responses."""
    if "text/event-stream" not in content_type.lower():
        return json.loads(text)

    for line in text.splitlines():
        if not line.startswith("data:"):
            continue
        payload = line.removeprefix("data:").strip()
        if payload and payload != "[DONE]":
            return json.loads(payload)
    raise GbrainError(f"No MCP data payload in response: {text[:300]}")
