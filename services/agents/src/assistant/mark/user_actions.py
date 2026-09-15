"""
Action and Intent taxonomies for M.A.R.K.

Maintains a strict architectural two-layer separation:
1. UserAction: Cognitive task requested by the human operator (Assistant / Orchestration tier).
2. NetworkServiceIntent: 3GPP autonomic network service objective / SLA (Domain / Telemetry tier).
"""

from __future__ import annotations

from enum import Enum


class UserAction(str, Enum):
    """
    Tier 1: Cognitive User Action (Assistant / Orchestrator Level).
    Represents what the human operator wants MARK to perform.
    """
    # Telecom Brain Engine actions
    EXPLAIN_INCIDENT = "telecom_brain.explain_incident"
    DIAGNOSE_RCA = "telecom_brain.diagnose_rca"
    CORRELATE_ALARMS = "telecom_brain.correlate_alarms"
    LIST_INCIDENTS = "telecom_brain.list_incidents"
    GET_INCIDENT = "telecom_brain.get_incident"
    INSPECT_TOPOLOGY = "telecom_brain.inspect_topology"
    CHECK_SERVICE_INTENTS = "telecom_brain.check_service_intents"
    CHECK_NETWORK_HEALTH = "telecom_brain.check_network_health"
    INSPECT_RUNBOOK = "telecom_brain.inspect_runbook"
    FCAPS_ANALYSIS = "telecom_brain.fcaps_analysis"
    ARCHITECTURE_DOCS = "telecom_brain.architecture_docs"
    CUSTOMER_TICKET_JOURNEY = "telecom_brain.customer_ticket_journey"
    RTR_SHIFT_SUMMARY = "telecom_brain.rtr_shift_summary"

    # Collaboration Engine actions
    DRAFT_COMMUNICATION = "collaboration.draft_communication"

    # Knowledge Base Engine actions
    QUERY_DOCUMENTS = "knowledge_base.query_documents"

    # Calendar Engine actions
    MANAGE_CALENDAR = "calendar.manage_schedule"

    # Codex Engineering Engine actions
    EXECUTE_CODE = "codex_engineering.execute_code"

    # Automation Engine actions
    RUN_AUTOMATION = "automation.run_diagnostics"

    # Multimodal Superpower actions
    VOICE_COMMAND = "superpower.voice"
    VISION_TASK = "superpower.vision"

    # Assistant Persona actions
    INSPECT_CAPABILITIES = "assistant.capabilities"
    GREETING = "assistant.greeting"
    CONVERSE = "assistant.converse"


class NetworkServiceIntent(str, Enum):
    """
    Tier 2: Network Service Intent (3GPP / Autonomic Network Tier).
    Represents operational service objectives and SLAs evaluated in
    multi-domain alarm correlation and telemetry scoring.
    """
    UE_REGISTRATION = "ue_registration"
    DATA_SESSION_ESTABLISHMENT = "data_session_establishment"
    SGI_THROUGHPUT = "sgi_throughput"
    LTE_ATTACH_SR = "lte_attach_sr"
    VOLTE_CSSR = "volte_cssr"
    IMS_REGISTRATION = "ims_registration"


SERVICE_INTENT_ALIASES: dict[NetworkServiceIntent, tuple[str, ...]] = {
    NetworkServiceIntent.UE_REGISTRATION: (
        "ue_registration", "ue registration", "registration failure", "5g-aka",
        "ue attach", "5g registration", "nas reject",
    ),
    NetworkServiceIntent.DATA_SESSION_ESTABLISHMENT: (
        "data_session_establishment", "data_session", "data session", "pdu session",
        "pdu establishment", "session establishment",
    ),
    NetworkServiceIntent.SGI_THROUGHPUT: (
        "sgi_throughput", "sgi throughput", "user plane throughput", "sgi interface",
        "n6 throughput", "data throughput",
    ),
    NetworkServiceIntent.LTE_ATTACH_SR: (
        "lte_attach_sr", "lte_attach", "lte attach", "initial attach",
        "s1-mme attach", "4g attach",
    ),
    NetworkServiceIntent.VOLTE_CSSR: (
        "volte_cssr", "volte", "cssr", "call setup success rate",
        "voice call setup", "sip invite",
    ),
    NetworkServiceIntent.IMS_REGISTRATION: (
        "ims_registration", "ims registration", "sip registration",
        "ims core", "p-cscf registration",
    ),
}
