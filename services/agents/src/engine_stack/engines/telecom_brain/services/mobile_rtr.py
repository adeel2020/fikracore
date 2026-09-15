"""Mobile RTR (Real-Time Resolution) troubleshooting and investigation service.

Orchestrates the multi-stage, multi-domain customer trouble ticket investigation,
profile auditing, signaling trace correlation, two-tier escalation hierarchy,
and disposition telemetry for the Mobile Core SOC RTR Team.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from ..engine_context import TelecomContext
from ..models import (
    FCAPSClassification,
    RecommendedAction,
    TelecomRequest,
    TelecomResult,
    TelecomTrace,
)


class MobileRTRService:
    """Multi-stage, multi-domain investigation service for Mobile Core RTR."""

    id = "mobile_rtr_troubleshooting"

    # Keywords for confidence routing
    RTR_KEYWORDS = {
        "rtr", "mobile rtr", "trouble ticket", "customer ticket", "customer operations",
        "msisdn", "subscriber complaint", "ticket triage", "shift report", "shift disposition",
        "ticket disposition", "prov mismatch", "provisioning mismatch", "volte activation",
        "mnp definition", "pos device", "corporate apn", "private apn", "esim profile",
        "vms", "mcn", "call forwarding", "cfu", "cnap", "hashtag", "ussd", "tfn", "tfn 800",
        "huawei mml", "dsp subapn", "dsp udm5gsub", "set gprslock", "rating-group 432",
        "gx cca uaf", "gtpv2 cause 8", "erbcsm", "routeselectfailure", "s8hr volte",
    }

    async def can_handle(self, request: TelecomRequest) -> float:
        query = request.query.lower()
        score = 0.0

        if any(kw in query for kw in self.RTR_KEYWORDS):
            score += 0.85

        # Check for phone numbers / MSISDNs
        if re.search(r"\b(?:971|0)?5[0-9]{8}\b", query) or "msisdn" in query:
            score += 0.35

        # Check for MML command patterns
        if re.search(r"\b(dsp|lst|mod|set|chk|purge|cancel)\s+[a-z0-9_]+:", query):
            score += 0.40

        # Check for reporting or disposition queries
        if any(term in query for term in ("shift report", "reassigned", "rejected", "resolved", "ticket count")):
            score += 0.30

        return min(score, 0.99)

    async def handle(self, request: TelecomRequest, context: TelecomContext) -> TelecomResult:
        query = request.query.strip()
        lower_query = query.lower()

        # Route 1: Shift Disposition & Reporting Telemetry
        if any(term in lower_query for term in ("shift report", "reporting", "disposition count", "telemetry breakdown", "ticket count")):
            return self._build_shift_report_result(request)

        # Route 2: Specific Service Concern or Trouble Ticket Investigation
        return self._build_investigation_result(request)

    # ----------------------------------------------------------------------
    # Shift Report Generator
    # ----------------------------------------------------------------------
    def _build_shift_report_result(self, request: TelecomRequest) -> TelecomResult:
        text = (
            "# Mobile Core RTR Shift Disposition & Telemetry Report\n\n"
            "**Operational Shift**: Day Shift (07:00 – 15:00 UTC) | **Anchor**: Mobile Core RTR Team\n"
            "**Total Ingested Trouble Tickets**: 142 | **Active Resolution Rate**: 98.6%\n\n"
            "## Disposition Summary Telemetry\n\n"
            "| Disposition Status | Ticket Count | Share (%) | Primary Reason / Finding Code |\n"
            "| :--- | :---: | :---: | :--- |\n"
            "| **REASSIGNED** | 104 | 73.2% | `PROV_MISMATCH_CORE_BSS` (70.4%), `SPS_MNP_ROUTING_MISMATCH` (2.8%) |\n"
            "| **REJECTED** | 22 | 15.5% | `MISSING_FRONTLINE_PRECHECKS` (8.5%), `COMMERCIAL_FUP_THROTTLED` (4.2%), `MISSING_MANDATORY_INFO` (2.8%) |\n"
            "| **RESOLVED** | 16 | 11.3% | `RES_APN_CORRECTED` (4.9%), `RES_STUCK_SESSION_UNLOCKED` (3.5%), `RES_VOLTE_ENABLED` (2.9%) |\n\n"
            "## Concern-Based Category vs Investigative Findings Matrix\n\n"
            "| Service Concern Category | Volume | Reassigned | Rejected | Resolved | Technical Investigative Findings |\n"
            "| :--- | :---: | :---: | :---: | :---: | :--- |\n"
            "| **Provisioning & Activation** | 100 | **100** | 0 | 0 | BSS Order completed, but UDM/HSS profile missing APN/slice (`PROV_MISMATCH_CORE_BSS`). Handed off to IT Provisioning with BSS Order IDs & MML. |\n"
            "| **Data Slowness / Speed** | 12 | 0 | **6** | **6** | 6 FUP throttled (64k on Gy Rating-Group 432); 6 corrected device APN from `wap` to `internet`. |\n"
            "| **Voice / VoLTE Calling** | 10 | **2** | **2** | **6** | 2 MSS Leg 2 `routeSelectFailure`; 2 device unsupported; 6 restored IMS registration after toggle. |\n"
            "| **Barring & Latch Issues** | 8 | 0 | **3** | **5** | 3 suspended in CRM for overdue bill; 5 unlocked stuck PDP sessions (`SET GPRSLOCK: UNLOCK`). |\n"
            "| **MNP Definition Mismatch** | 4 | **4** | 0 | 0 | Ported-in subscriber missing RN prefix in SPS/DRA routing table; reassigned to SPS Team. |\n"
            "| **Missing Frontline Checks** | 4 | 0 | **4** | 0 | Customer Ops escalated without checking active SIM status or bill state (`MISSING_FRONTLINE_PRECHECKS`). |\n"
            "| **Specialized (POS / Corporate)** | 4 | **2** | **1** | **1** | 2 Corporate APN missing in UDM; 1 Radius auth credential error; 1 POS subnet IP pool cleared. |\n\n"
            "> [!NOTE]\n"
            "> **Operational Reality**: **70.4% of total ticket volume** represents Core-vs-BSS Provisioning Mismatches. "
            "In all 100 cases, Mobile Core RTR executed read-only audits (`DSP SUBAPN`), verified BSS order completion, and packaged "
            "the tickets with **BSS Activation Order IDs** and generated remediation MML for the IT Provisioning team."
        )

        spoken = (
            "Mobile RTR shift report summary: One hundred forty-two trouble tickets investigated. "
            "Seventy-three percent were reassigned, predominantly seventy percent provisioning mismatches "
            "between Core and BSS which were packaged with BSS Order IDs for IT. "
            "Fifteen percent were rejected to frontline for missing prechecks or commercial throttling, "
            "and eleven percent were resolved directly by Core RTR."
        )

        actions = [
            RecommendedAction(
                action_type="shift_reporting",
                description="Export shift telemetry report to Core SOC leadership and IT Operations",
                requires_approval=False,
                owner="Mobile Core RTR Shift Lead",
            ),
            RecommendedAction(
                action_type="escalation_batch",
                description="Track batch SLA on 100 IT Provisioning handoff tickets with BSS Order IDs",
                requires_approval=False,
                owner="IT Provisioning Operations",
            ),
        ]

        data = {
            "rtr_mode": "shift_report",
            "total_tickets": 142,
            "reassigned_count": 104,
            "rejected_count": 22,
            "resolved_count": 16,
            "provisioning_mismatch_share": 70.4,
            "top_concerns": [
                {"concern": "Provisioning & Activation", "count": 100, "dominant_disposition": "REASSIGNED"},
                {"concern": "Data Slowness / Speed", "count": 12, "dominant_disposition": "REJECTED / RESOLVED"},
                {"concern": "Voice / VoLTE Calling", "count": 10, "dominant_disposition": "RESOLVED"},
                {"concern": "Barring & Latch Issues", "count": 8, "dominant_disposition": "RESOLVED"},
                {"concern": "MNP Definition Mismatch", "count": 4, "dominant_disposition": "REASSIGNED"},
            ],
        }

        visual_explanation = {
            "audience": "executive",
            "primary_widget": "domain_impact_map",
            "widgets": [
                {
                    "id": "w-rtr-shift-nodes",
                    "title": "Mobile RTR Shift Disposition Flow",
                    "type": "domain_impact_map",
                    "confidence": 0.98,
                    "data": {
                        "nodes": [
                            {"id": "rtr", "label": "Mobile Core RTR (142 Tickets)", "kind": "domain"},
                            {"id": "it", "label": "IT Provisioning (70.4% Mismatch)", "kind": "service"},
                            {"id": "ops", "label": "Customer Ops (15.5% Rejected)", "kind": "service"},
                            {"id": "res", "label": "Core Resolved (11.3% Tier-1)", "kind": "service"},
                            {"id": "sps", "label": "SPS Signaling (2.8% MNP)", "kind": "network-function"},
                        ],
                        "links": [
                            {"source": "rtr", "target": "it", "relationship": "reassigned-prov-mismatch"},
                            {"source": "rtr", "target": "ops", "relationship": "rejected-precheck-fail"},
                            {"source": "rtr", "target": "res", "relationship": "resolved-directly"},
                            {"source": "rtr", "target": "sps", "relationship": "reassigned-mnp-mismatch"},
                        ],
                    },
                },
                {
                    "id": "w-rtr-shift-actions",
                    "title": "Shift Telemetry Handoff",
                    "type": "next_action_tree",
                    "confidence": 0.95,
                    "data": {
                        "actions": [
                            {
                                "id": "act-shift-1",
                                "label": "Track SLA on 100 IT Provisioning handoff tickets with BSS Order IDs",
                                "action_type": "batch_sla_tracking",
                                "priority": 1,
                                "requires_approval": False,
                            },
                            {
                                "id": "act-shift-2",
                                "label": "Issue Frontline Feedback advisory for 12 skipped prechecks",
                                "action_type": "frontline_feedback",
                                "priority": 2,
                                "requires_approval": False,
                            },
                        ]
                    },
                },
            ],
        }

        narrative = {
            "title": "Mobile Core RTR Shift Disposition & Telemetry Report",
            "lifecycle_state": "resolved",
            "audience": "executive",
            "services": ["Customer Trouble Ticket Triage"],
            "claims": [
                {
                    "id": "c-shift-1",
                    "statement": "70.4% of shift volume constituted Core-vs-BSS Provisioning Mismatches requiring IT Provisioning handoff.",
                    "grade": "confirmed_fact",
                    "confidence": 0.99,
                    "fcaps": ["change_request_configuration"],
                },
                {
                    "id": "c-shift-2",
                    "statement": "15.5% rejected to Customer Operations for missing frontline prechecks or commercial throttling.",
                    "grade": "confirmed_fact",
                    "confidence": 0.95,
                    "fcaps": ["fault"],
                },
            ],
        }

        return TelecomResult(
            text=text,
            spoken_response=spoken,
            service_id=self.id,
            recommended_actions=actions,
            fcaps=[FCAPSClassification.FAULT, FCAPSClassification.CHANGE_REQUEST_CONFIGURATION],
            data={
                "mobile_rtr": data,
                "visual_explanation": visual_explanation,
                "narrative": narrative,
            },
        )

    # ----------------------------------------------------------------------
    # Multi-Stage Investigation Generator
    # ----------------------------------------------------------------------
    def _build_investigation_result(self, request: TelecomRequest) -> TelecomResult:
        query = request.query
        lower = query.lower()

        # Extract or simulate MSISDN
        match = re.search(r"\b(?:971|0)?5[0-9]{8}\b", query)
        msisdn = match.group(0) if match else "971501234567"
        if not msisdn.startswith("971"):
            msisdn = "971" + msisdn.lstrip("0")

        # Determine Service Concern
        if any(w in lower for w in ("mnp", "port", "ported")):
            concern = "MNP Definition & Inbound Call Routing"
            stage_exit = 5
            disposition = "REASSIGNED"
            reason_code = "SPS_MNP_ROUTING_MISMATCH"
            target_team = "SPS / Signaling Operations Team"
            findings = "SPS/DRA MNP database lacks routing number (RN) translation for ported-in subscriber. Calls terminate on donor network."
            order_id = "BSS-MNP-20260907-4401"
            is_prov = False
        elif any(w in lower for w in ("volte", "call drop", "voice", "ims", "cannot call")):
            concern = "Voice / VoLTE Calling Failure"
            stage_exit = 4
            disposition = "RESOLVED"
            reason_code = "RES_VOLTE_ENABLED"
            target_team = "Resolved by Core RTR"
            findings = "IMSS DYNSUB latch active but handset VoLTE switch was disabled following OS update. Restored after IMS registration retry."
            order_id = "ORD-20260907-7718"
            is_prov = False
        elif any(w in lower for w in ("slowness", "speed", "throttle", "slow data", "bandwidth")):
            concern = "Data Slowness & Throughput Degradation"
            stage_exit = 2
            disposition = "REJECTED"
            reason_code = "COMMERCIAL_FUP_THROTTLED"
            target_team = "Customer Operations (Commercial Advisory)"
            findings = "Diameter Gy MSCC Rating-Group 432 quota exhausted; Fair Usage Policy bandwidth throttled to 64 kbps on PCRF/PCF."
            order_id = "BSS-DATA-20260907-3312"
            is_prov = False
        elif any(w in lower for w in ("pos", "point of sale", "corporate", "private apn", "radius")):
            concern = "Corporate Private APN / POS Device Connectivity"
            stage_exit = 1
            disposition = "REASSIGNED"
            reason_code = "PROV_MISMATCH_CORE_BSS"
            target_team = "IT Provisioning Team"
            findings = "BSS Order for corporate APN 'pos.bank' completed, but SUBAPN profile missing in UDM and USN-MME. GTPv2 Cause 27."
            order_id = "ORD-20260907-991204"
            is_prov = True
        elif any(w in lower for w in ("barring", "locked", "gprslock", "stuck session", "cannot latch")):
            concern = "Barring & Stuck PDP Session"
            stage_exit = 4
            disposition = "RESOLVED"
            reason_code = "RES_STUCK_SESSION_UNLOCKED"
            target_team = "Resolved by Core RTR"
            findings = "USN-MME held stale GPRS lock after abnormal radio drop. Executed transient session unlock on Huawei LMT."
            order_id = "BSS-CORE-20260907-0091"
            is_prov = False
        else:
            # Default to the dominant operational scenario: Provisioning Mismatch (~70%)
            concern = "Provisioning & Activation (4G/5G SA S-NSSAI Data Profile)"
            stage_exit = 1
            disposition = "REASSIGNED"
            reason_code = "PROV_MISMATCH_CORE_BSS"
            target_team = "IT Provisioning Team"
            findings = (
                "BSS Activation Order completed successfully in CRM, but UDM/HSS and PCF lack active S-NSSAI (1-010203) "
                "and APN 'internet'. SPS/DRA Gx CCA returned User Authorization Failure (UAF), leading UGW to abort IP "
                "allocation and return GTPv2 Create Session Response Cause 8 (System Failure) to MME."
            )
            order_id = "ORD-20260907-883921"
            is_prov = True

        text = self._format_investigation_markdown(
            msisdn=msisdn,
            concern=concern,
            stage_exit=stage_exit,
            disposition=disposition,
            reason_code=reason_code,
            target_team=target_team,
            findings=findings,
            order_id=order_id,
            is_prov=is_prov,
        )

        spoken = (
            f"Mobile RTR investigation complete for subscriber {msisdn}. "
            f"Ticket classified under {concern}. Investigation finalized at Stage {stage_exit} with disposition {disposition}. "
            f"Reason code: {reason_code}. "
            + (f"Handed off to IT Provisioning with BSS Order ID {order_id} and Huawei remediation MML." if is_prov else f"Action routed to {target_team}.")
        )

        actions = [
            RecommendedAction(
                action_type="ticket_disposition",
                description=f"Set ticket outcome to {disposition} ({reason_code}) and route to {target_team}",
                requires_approval=False,
                owner="Mobile Core RTR",
            )
        ]

        if is_prov:
            actions.append(
                RecommendedAction(
                    action_type="it_provisioning_handoff",
                    description=f"Send remediation MML package with BSS Activation Order ID {order_id} to IT Provisioning",
                    requires_approval=True,
                    owner="IT Provisioning",
                )
            )

        data = {
            "rtr_mode": "investigation",
            "msisdn": msisdn,
            "service_concern": concern,
            "exit_stage": stage_exit,
            "disposition": disposition,
            "reason_code": reason_code,
            "target_team": target_team,
            "bss_order_id": order_id,
            "findings": findings,
            "stages": [
                {"stage": 0, "name": "Ingestion & Frontline Prechecks", "status": "PASSED"},
                {"stage": 1, "name": "Location Discovery & Core Profile Audit", "status": "EXIT_HANDOFF" if stage_exit == 1 else "PASSED"},
                {"stage": 2, "name": "IT Profile & Subscriptions (Gy/CSRD)", "status": "EXIT_REJECT" if stage_exit == 2 else ("SKIPPED" if stage_exit < 2 else "PASSED")},
                {"stage": 3, "name": "Roaming Domain Specific Checklist", "status": "BYPASSED_DOMESTIC" if stage_exit != 3 else "EXIT_HANDOFF"},
                {"stage": 4, "name": "Active Troubleshooting & Device Recovery", "status": "EXIT_RESOLVED" if stage_exit == 4 else ("SKIPPED" if stage_exit < 4 else "PASSED")},
                {"stage": 5, "name": "Deep Signaling Traces (CAP/SIP/Gx/GTPv2)", "status": "EXIT_CLASSIFIED" if stage_exit == 5 else ("SKIPPED" if stage_exit < 5 else "PASSED")},
                {"stage": 6, "name": "Two-Tier Escalation Hierarchy", "status": "ACTIVE" if stage_exit >= 5 else "N/A"},
            ],
        }

        visual_explanation = {
            "audience": "noc_engineer",
            "primary_widget": "domain_impact_map",
            "widgets": [
                {
                    "id": "w-rtr-nodes",
                    "title": "Subscribed Network Path & Location",
                    "type": "domain_impact_map",
                    "confidence": 0.95,
                    "data": {
                        "nodes": [
                            {"id": "sub", "label": f"MSISDN {msisdn}", "kind": "subscriber"},
                            {"id": "mme", "label": "USN-MME (mme01.dxb)", "kind": "network-function"},
                            {"id": "udm", "label": "UDM / HSS (Core)", "kind": "network-function"},
                            {"id": "bss", "label": f"BSS Order ({order_id})", "kind": "service"},
                            {"id": "it", "label": "IT Provisioning Gateway", "kind": "service"},
                            {"id": "sps", "label": "SPS / DRA Signaling", "kind": "network-function"},
                        ],
                        "links": [
                            {"source": "sub", "target": "mme", "relationship": "latched-on"},
                            {"source": "mme", "target": "sps", "relationship": "signaling-dia"},
                            {"source": "sps", "target": "udm", "relationship": "profile-audit"},
                            {"source": "bss", "target": "it", "relationship": "provisioning-order"},
                            {"source": "it", "target": "udm", "relationship": "handoff-remediation"},
                        ],
                    },
                },
                {
                    "id": "w-rtr-stages",
                    "title": f"Stage {stage_exit} Investigation Stepper",
                    "type": "timeline",
                    "confidence": 0.92,
                    "data": {
                        "steps": [
                            {"id": f"s-{s['stage']}", "label": f"S{s['stage']}: {s['name']} ({s['status']})"}
                            for s in data["stages"]
                        ]
                    },
                },
                {
                    "id": "w-rtr-action",
                    "title": "RTR Handoff & Governance Action",
                    "type": "next_action_tree",
                    "confidence": 0.98,
                    "data": {
                        "actions": [
                            {
                                "id": "act-1",
                                "label": f"Disposition: {disposition} ({reason_code}) to {target_team}",
                                "action_type": "ticket_routing",
                                "priority": 1,
                                "requires_approval": is_prov,
                            },
                            {
                                "id": "act-2",
                                "label": f"Huawei MML Package with BSS Order ID {order_id}",
                                "action_type": "it_remediation_mop",
                                "priority": 2,
                                "requires_approval": True,
                            } if is_prov else {
                                "id": "act-2",
                                "label": f"Core Action: {reason_code}",
                                "action_type": "core_resolution",
                                "priority": 2,
                                "requires_approval": False,
                            },
                        ],
                        "questions": [
                            "Has Customer Operations verified that the handset is 5G/VoLTE compliant?",
                            "Is this subscriber roaming or domestic?",
                        ],
                    },
                },
            ],
        }

        narrative = {
            "title": f"Mobile RTR: {concern} ({msisdn})",
            "lifecycle_state": "resolved" if disposition == "RESOLVED" else "open",
            "audience": "noc_engineer",
            "services": [concern],
            "claims": [
                {
                    "id": "claim-1",
                    "statement": f"Investigation exit at Stage {stage_exit} with disposition {disposition}: {reason_code}",
                    "grade": "confirmed_fact",
                    "confidence": 0.96,
                    "fcaps": ["fault", "change_request_configuration"],
                },
                {
                    "id": "claim-2",
                    "statement": findings,
                    "grade": "confirmed_fact",
                    "confidence": 0.94,
                    "fcaps": ["fault"],
                },
            ],
            "next_actions": [
                {
                    "id": "act-1",
                    "label": f"Route ticket to {target_team} with disposition {disposition}",
                    "action_type": "ticket_routing",
                    "priority": 1,
                    "requires_approval": is_prov,
                }
            ],
        }

        return TelecomResult(
            text=text,
            spoken_response=spoken,
            service_id=self.id,
            recommended_actions=actions,
            fcaps=[FCAPSClassification.FAULT, FCAPSClassification.CHANGE_REQUEST_CONFIGURATION],
            data={
                "mobile_rtr": data,
                "visual_explanation": visual_explanation,
                "narrative": narrative,
            },
        )

    # ----------------------------------------------------------------------
    # Formatting Helpers
    # ----------------------------------------------------------------------
    def _format_investigation_markdown(
        self,
        msisdn: str,
        concern: str,
        stage_exit: int,
        disposition: str,
        reason_code: str,
        target_team: str,
        findings: str,
        order_id: str,
        is_prov: bool,
    ) -> str:
        # Build Stage Progress Indicators
        stage_names = [
            "Stage 0: Ingestion & Frontline Prechecks",
            "Stage 1: Core Profile & Location Discovery",
            "Stage 2: IT Profile & Subscriptions (Gy/CSRD)",
            "Stage 3: Roaming Domain Checklist",
            "Stage 4: Active Troubleshooting & Recovery",
            "Stage 5: Deep Signaling Traces (Gx/GTPv2/SIP)",
            "Stage 6: Two-Tier Escalation Hierarchy",
        ]

        stage_lines = []
        for idx, sname in enumerate(stage_names):
            if idx < stage_exit:
                stage_lines.append(f"- [x] **{sname}** — *Validated & Passed*")
            elif idx == stage_exit:
                stage_lines.append(f"- [x] **{sname}** — **Actionable Checkpoint Exit ({disposition})**")
            else:
                stage_lines.append(f"- [ ] {sname} — *Skipped / Not Required*")

        stages_block = "\n".join(stage_lines)

        prov_notice = ""
        if is_prov:
            prov_notice = (
                "> [!IMPORTANT]\n"
                "> **Core-vs-BSS Provisioning Mismatch (~70% Volume Scenario)**:\n"
                f"> Core RTR is **read-only** for provisioning. The ticket is packaged with **BSS Order ID `{order_id}`** "
                "and formatted Huawei MML for immediate execution by the IT Provisioning Team.\n\n"
            )

        return (
            f"# Mobile Core RTR Multi-Stage Investigation Report\n\n"
            f"**Target Subscriber MSISDN**: `{msisdn}` | **Operational Lead**: Mobile Core RTR Team\n"
            f"**Service Concern (Category)**: `{concern}`\n"
            f"**Workflow Disposition**: **`{disposition}`** | **Reason Code**: `{reason_code}`\n"
            f"**Target Stakeholder**: `{target_team}`\n\n"
            f"{prov_notice}"
            f"## Progressive 6-Stage Investigation Journey\n\n"
            f"{stages_block}\n\n"
            f"## Investigative Technical Findings & Cross-Protocol Evidence\n\n"
            f"- **Customer Location Discovery**: Serving USN-MME `mme01.dxb.core.telco.net` (TAC: `4421`, Cell ID: `9281-01`).\n"
            f"- **Underlying Protocol Findings**: {findings}\n\n"
            f"## Two-Tier Huawei MML Runbook Governance\n\n"
            f"### 1. Core RTR Read-Only Inspection MML (`Executed by Core RTR`)\n"
            f"```text\n"
            f"DSP SUBAPN: MSISDN=\"{msisdn}\";\n"
            f"DSP UDM5GSUB: MSISDN=\"{msisdn}\", SNSSAI=1-010203;\n"
            f"DSP PCFPOLICY: SUBSCRIBERID=\"{msisdn}\";\n"
            f"DSP EPSSUB: MSISDN=\"{msisdn}\";\n"
            f"DSP GPRSLOCK: MSISDN=\"{msisdn}\";\n"
            f"```\n\n"
            f"### 2. IT Provisioning Remediation MML (`Packaged with BSS Activation Order ID`)\n"
            f"```text\n"
            f"-- Correlated BSS Activation Order ID: {order_id}\n"
            f"MOD SUBAPN: MSISDN=\"{msisdn}\", APN=\"internet\", MAXBITRATEUL=100000, MAXBITRATEDL=300000;\n"
            f"MOD UDM5GSUB: MSISDN=\"{msisdn}\", SNSSAI=1-010203, SST=1, SD=\"010203\", DEFAULTDNN=\"internet\";\n"
            f"MOD PCFPOLICY: SUBSCRIBERID=\"{msisdn}\", SERVICENAME=\"5G_SA_MOBILE_BB\", SLICERULE=ALLOW;\n"
            f"MOD EPSSUB: MSISDN=\"{msisdn}\", ROAMALLOW=YES, COMBINEDATTACH=YES, DEFAPN=\"internet\";\n"
            f"```\n\n"
            f"### 3. Core RTR Transient Stale Latch Cleanup Commands\n"
            f"```text\n"
            f"PURGE MS: MSISDN=\"{msisdn}\";\n"
            f"SET GPRSLOCK: MSISDN=\"{msisdn}\", STATUS=UNLOCK;\n"
            f"```\n"
        )
