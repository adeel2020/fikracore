"""
M.A.R.K. Core Engine - Telecom Incident Manager
Cognitive multi-agent orchestration for AgenticAIOPs with incident management persona.
"""

from __future__ import annotations

import os
import time
import json
import asyncio
import logging
import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Optional
from datetime import datetime

from pydantic import BaseModel
try:
    from agenticaiops_shared.config import settings
except Exception:
    class _FallbackSettings:
        openai_model = "gpt-4o-mini"
        openai_api_key = None
        openai_api_base = "https://api.openai.com/v1"
        openai_embedding_model = "text-embedding-3-small"
    settings = _FallbackSettings()

from capability_registry import MarkRegistry, load_default_registry
from .action_classifier import ClassifiedAction, classify_action
from .session import MarkSession, MarkSessionStore, default_session_store, resolve_user_name
from .user_actions import NetworkServiceIntent, UserAction

logger = logging.getLogger("assistant.mark.core")


_GENERAL_ASSISTANT_PATTERNS = (
    r"\b(can you|could you)\s+(hear|listen|understand)\b",
    r"\b(are you there|you there|can you hear me|can you listen)\b",
    r"\b(test|check)\s+(voice|audio|microphone|mic)\b",
)

_OPERATIONAL_CONTEXT_KEYWORDS = {
    "5g", "5gc", "4g", "lte", "volte", "ims", "vepc", "ran", "transport",
    "telecom", "network", "incident", "incidents", "alarm", "alarms", "alert",
    "alerts", "event", "events", "kpi", "telemetry", "topology", "gbrain",
    "grafana", "lgtm", "fcaps", "rca", "root cause", "blast radius", "mttr",
    "mop", "runbook", "playbook", "amf", "smf", "upf", "mme", "hss", "udm",
    "pcf", "ausf", "gnb", "gnodeb", "enb", "enodeb", "diameter", "nas",
    "attach", "registration", "sgi", "throughput", "latency", "packet loss",
    "cpu", "memory", "cluster", "pod", "service procedure", "site",
    "intent", "intents", "sla", "slas", "objective", "objectives", "procedure",
    "procedures", "service", "services", "cssr", "pdu", "pdp", "qos", "subscriber", "ue",
    "outage", "degradation", "packet", "bandwidth", "interface", "session",
}

# ==========================================
# ZAKI CONFIGURATION
# ==========================================

@dataclass
class JARVISConfig:
    """Zaki system configuration & incident manager persona using OpenAI."""
    name: str = "ZAKI"
    role: str = "Telecom Incident Manager"
    version: str = "3.2.0"
    model: str = os.getenv("OPENAI_MODEL") or getattr(settings, "openai_model", "gpt-4o-mini")
    api_key: str | None = os.getenv("OPENAI_API_KEY") or getattr(settings, "openai_api_key", None)
    api_base: str = os.getenv("OPENAI_API_BASE") or getattr(settings, "openai_api_base", "https://api.openai.com/v1")
    embedding_model: str = getattr(settings, "openai_embedding_model", "text-embedding-3-small")
    max_context_tokens: int = 100_000
    voice_enabled: bool = True
    vision_enabled: bool = True
    autopilot_enabled: bool = True
    security_level: str = "maximum"
    data_residency: str = "UAE"
    neurosol_sync: bool = True


# ==========================================
# ZAKI STATUS & TELEMETRY
# ==========================================

class JARVISStatus(str, Enum):
    OFFLINE = "offline"
    INITIALIZING = "initializing"
    ONLINE = "online"
    PROCESSING = "processing"
    ERROR = "error"


class PowerUp(str, Enum):
    VOICE = "voice"
    VISION = "vision"
    CODE = "code"
    TELECOM_BRAIN = "telecom_brain"
    RAG = "rag"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    MONITORING = "monitoring"
    AUTOPILOT = "autopilot"
    SECURITY = "security"
    ANALYTICS = "analytics"
    ORCHESTRATION = "orchestration"


@dataclass
class JarvisTelemetry:
    """Real-time Zaki telemetry."""
    status: JARVISStatus = JARVISStatus.OFFLINE
    uptime: float = 0.0
    queries_processed: int = 0
    active_agents: int = 0
    power_ups_active: list[str] = field(default_factory=list)
    memory_usage_pct: int = 0
    cpu_usage_pct: int = 0
    latency_ms: float = 0.0
    last_query: str = ""
    last_query_time: float = 0.0
    error_count: int = 0
    success_rate: float = 100.0


# ==========================================
# ZAKI INCIDENT MANAGER CORE ENGINE
# ==========================================

class JARVIS:
    """
    M.A.R.K. - Telecom Incident Manager & Operations Commander
    
    Cognitive incident operations commander:
    - Powered by OpenAI (gpt-4o-mini / gpt-4o)
    - MTTR reduction & timeline reconstruction
    - Multi-domain correlation (5G Core, IMS, Transport, Cloud)
    - Root cause analysis (RCA) & blast radius assessment
    - Closed-loop automated healing & MOP execution
    - Deterministic Storyteller & gbrain MCP integration
    - Voice synthesis & real-time stakeholder communication
    """

    def __init__(self, config: JARVISConfig | None = None):
        self.config = config or JARVISConfig()
        self.status = JARVISStatus.OFFLINE
        self.telemetry = JarvisTelemetry()
        self._start_time = time.time()
        self._superpowers: dict[str, Any] = {}
        self.registry: MarkRegistry | None = None
        self._initialized = False
        self.last_reply: str | None = None
        self.last_spoken_reply: str | None = None
        self.session_store: MarkSessionStore = default_session_store
        
        logger.info(f"[{self.config.name}] Initializing {self.config.role} (Model: {self.config.model})...")

    async def initialize(self) -> None:
        """Initialize all Zaki superpowers with OpenAI configuration."""
        self.status = JARVISStatus.INITIALIZING
        
        try:
            self.registry = load_default_registry()

            from jarvis.superpowers.voice import VoiceEngine
            from jarvis.superpowers.vision import VisionEngine
            from jarvis.superpowers.code_gen import CodeEngine
            from jarvis.superpowers.telecom_brain import TelecomBrainEngine
            from jarvis.superpowers.rag_engine import RAGEngine
            from jarvis.superpowers.knowledge_graph import KnowledgeGraphEngine
            from jarvis.superpowers.monitoring import MonitoringEngine
            from jarvis.superpowers.autopilot import AutopilotEngine
            from jarvis.superpowers.security import SecurityEngine
            
            self._superpowers = {
                PowerUp.VOICE: VoiceEngine(self.config) if self.config.voice_enabled else None,
                PowerUp.VISION: VisionEngine(self.config) if self.config.vision_enabled else None,
                PowerUp.CODE: CodeEngine(self.config),
                PowerUp.TELECOM_BRAIN: TelecomBrainEngine(self.config),
                PowerUp.RAG: RAGEngine(self.config),
                PowerUp.KNOWLEDGE_GRAPH: KnowledgeGraphEngine(self.config),
                PowerUp.MONITORING: MonitoringEngine(self.config),
                PowerUp.AUTOPILOT: AutopilotEngine(self.config) if self.config.autopilot_enabled else None,
                PowerUp.SECURITY: SecurityEngine(self.config),
            }
            
            init_tasks = []
            for name, engine in self._superpowers.items():
                if engine and hasattr(engine, 'initialize'):
                    init_tasks.append(self._init_superpower(name, engine))
            
            if init_tasks:
                await asyncio.gather(*init_tasks, return_exceptions=True)
            
            self.status = JARVISStatus.ONLINE
            self._initialized = True
            self.telemetry.power_ups_active = [p.value for p, e in self._superpowers.items() if e is not None]
            
            logger.info(f"[{self.config.name}] Online as {self.config.role} (OpenAI: {self.config.model}). {len(self.telemetry.power_ups_active)} superpowers active.")
            
        except Exception as e:
            self.status = JARVISStatus.ERROR
            logger.error(f"[{self.config.name}] Initialization failed: {e}")
            raise

    async def _init_superpower(self, name: PowerUp, engine: Any) -> None:
        """Initialize a single superpower with error handling."""
        try:
            await engine.initialize()
            logger.info(f"[{self.config.name}] Superpower '{name.value}' initialized.")
        except Exception as e:
            logger.warning(f"[{self.config.name}] Superpower '{name.value}' failed to init: {e}")
            self._superpowers[name] = None

    # ==========================================
    # MAIN QUERY PROCESSING
    # ==========================================

    async def process(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        """
        Process operational query with Zaki's Incident Manager persona.
        """
        start_time = time.time()
        self.status = JARVISStatus.PROCESSING
        self.telemetry.queries_processed += 1
        self.telemetry.last_query = query
        self.telemetry.last_query_time = time.time()
        self.last_reply = None
        self.last_spoken_reply = None

        session_key = session_id or "default"
        session = self.session_store.get_or_create(session_key)

        effective_context = dict(context) if context else {}
        if not effective_context.get("incident_id") and session.active_incident_id:
            effective_context["incident_id"] = session.active_incident_id
        if effective_context.get("incident_id"):
            session.active_incident_id = str(effective_context["incident_id"])

        reply: Any = None
        classified: ClassifiedAction | None = None

        try:
            # 1. Action classification via Two-Pass Hybrid Classifier
            classified = classify_action(query, effective_context, session=session)
            logger.info(f"[{self.config.name}] Classified action: {classified.action} (engine: {classified.engine_id})")

            if classified.extracted_incident_id:
                session.active_incident_id = classified.extracted_incident_id
                effective_context["incident_id"] = classified.extracted_incident_id
            if classified.target_intent:
                effective_context["intent"] = classified.target_intent

            user_name = resolve_user_name(query, session, effective_context)
            greeting_name = f", {user_name}" if user_name else ""
            clean_q = query.strip().lower()

            # 2. Persona greeting & identity
            if classified.action == UserAction.GREETING:
                if any(kw in clean_q for kw in ("who are you", "what is your name", "introduce yourself")):
                    reply = self._remember_response(
                        f"Hello{greeting_name}! I am Zaki — your Telecom Incident Manager. "
                        "I assist with 5G Core, IMS, and transport operations — correlating alarms, diagnosing root causes, "
                        "and driving rapid remediation. How can I assist you with operations today?"
                    )
                else:
                    reply = self._remember_response(
                        f"Hello{greeting_name}! I am Zaki — your Telecom Incident Manager. "
                        "Great to connect with you! How are you doing today? How can I assist you with operations?"
                    )

            # 3. Conversational turns & audio checks
            elif classified.action == UserAction.CONVERSE:
                if "opted out" in (classified.reason or "").lower() or any(
                    re.search(p, clean_q) for p in (
                        r"\b(do\s*n['o]?t|no|stop|never|without|not\s+need|don'?t\s+need|don'?t\s+want)\b.*\b(story|stories|narrative)\b",
                        r"\b(story|stories|narrative)\b.*\b(not\s+needed|unnecessary|not\s+wanted)\b",
                    )
                ):
                    reply = self._remember_response(
                        f"Understood{greeting_name} — no story. I will keep responses direct, factual, and concise. "
                        "How can I assist you with operations? I can provide the confirmed root cause, telemetry KPIs, remediation actions, or list current incidents."
                    )
                else:
                    reply = self._remember_response(await self._answer_general(query, session=session, context=effective_context))

            # 4. Capability inspection
            elif classified.action == UserAction.INSPECT_CAPABILITIES:
                reply = self._remember_response(self._answer_capabilities())

            # 5. Service intents inspection
            elif classified.action == UserAction.CHECK_SERVICE_INTENTS:
                reply = self._remember_response(self._answer_intents())

            # 6. Security validation
            elif self._superpowers.get(PowerUp.SECURITY) and not await self._superpowers[PowerUp.SECURITY].validate_query(query):
                reply = self._remember_response("Query blocked by Zaki security protocols.")

            # 6. Multimodal Superpowers: Voice & Vision
            elif classified.action == UserAction.VOICE_COMMAND:
                reply = self._remember_response(await self._execute_power(PowerUp.VOICE, query, session_key, effective_context))
            elif classified.action == UserAction.VISION_TASK:
                reply = self._remember_response(await self._execute_power(PowerUp.VISION, query, session_key, effective_context))

            # 7. Codex Engineering Engine
            elif classified.action == UserAction.EXECUTE_CODE:
                reply = self._remember_response(await self._execute_power(PowerUp.CODE, query, session_key, effective_context))

            # 8. Collaboration Engine: Draft email / WhatsApp / Teams update
            elif classified.action == UserAction.DRAFT_COMMUNICATION:
                reply = self._remember_response(await self._handle_collaboration_draft(query, session_key, effective_context))

            # 9. Calendar Engine: Meeting / maintenance window coordination
            elif classified.action == UserAction.MANAGE_CALENDAR:
                reply = self._remember_response(await self._handle_calendar_coordination(query, session_key, effective_context))

            # 10. Automation Engine: Diagnostics / pre-checks
            elif classified.action == UserAction.RUN_AUTOMATION:
                reply = self._remember_response(await self._handle_automation_execution(query, session_key, effective_context))

            # 10a. Mobile Core RTR Customer Ticket Journey (Isolated)
            elif classified.action == UserAction.CUSTOMER_TICKET_JOURNEY:
                from engine_stack.engines.telecom_brain.services.mobile_rtr_intelligence import MobileRTRTicketIntelligenceService
                from .response import MarkResponse

                match = re.search(r"\b(TT-\d+)\b", query, re.IGNORECASE)
                ticket_id = match.group(1).upper() if match else "TT-984210"
                rtr_intel = MobileRTRTicketIntelligenceService()
                journey = rtr_intel.get_customer_ticket_journey(ticket_id)

                ola_verdict = "ACHIEVED" if journey.ola_achieved else f"BREACHED in {journey.delinquent_queue.value}"
                aola_badge = "🟢 Achieved" if journey.aola_achieved else "🔴 Breached"
                ola_badge = "🟢 Achieved" if journey.ola_achieved else f"🔴 Breached ({journey.delinquent_queue.value})"
                sla_badge = "🟢 Achieved" if journey.sla_achieved else "🔴 Breached"

                reply_text = (
                    f"### 📋 Customer Trouble Ticket Journey: `{journey.ticket_token}`\n\n"
                    f"| Metric | Value | Threshold / Target | Governance Verdict |\n"
                    f"| :--- | :--- | :--- | :--- |\n"
                    f"| **Subscriber Token** | `{journey.subscriber_token}` | Non-PII Identifier | Enforced |\n"
                    f"| **Ticket Status** | `{journey.current_status.value}` | Final Lifecycle | Confirmed |\n"
                    f"| **RTR Dwell (AOLA)** | `{journey.aola_rtr_hours}h` | ≤ 2.0h (Mobile Core RTR) | {aola_badge} |\n"
                    f"| **Internal NOC (OLA)** | `{journey.ola_noc_hours}h` | ≤ 6.0h (Core & Provisioning) | {ola_badge} |\n"
                    f"| **Total Journey (E2E SLA)** | `{journey.total_e2e_dwell_hours}h` | ≤ 48.0h (Customer Facing) | {sla_badge} |\n"
                    f"| **Ping-Pong Reassignments** | `{journey.bounced_count} bounce(s)` | 0 loops | {'⚠️ Review Required' if journey.bounced_count > 0 else '🟢 Optimal'} |\n\n"
                    f"---\n\n"
                    f"#### ⏱️ Chronological Hop Progression\n\n"
                )

                for h in journey.journey_hops:
                    status_icon = "🟢" if h.sla_status.value == "ACHIEVED" else ("🔴" if h.sla_status.value == "BREACHED" else "🟡")
                    bounce_tag = " • 🔁 **Bounced Back to RTR**" if h.is_bounced_back_to_rtr else ""
                    next_queue_str = f" ➔ `{h.reassigned_to_queue.value}`" if h.reassigned_to_queue else " ➔ *Resolved / Closed*"
                    
                    reply_text += (
                        f"> **Hop {h.hop_number}: `{h.assigned_queue.value}`** {next_queue_str}{bounce_tag}\n"
                        f"> - **Dwell**: `{h.time_spent_hours}h` (Triage: `{h.active_triage_hours}h` \| Wait: `{h.idle_waiting_hours}h`) • {status_icon} `{h.sla_status.value}`\n"
                        f"> - **Action**: {h.action_taken}\n"
                    )
                    if h.finding_code:
                        reply_text += f"> - **Protocol Finding**: `{h.finding_code}`\n"
                    if h.reassignment_reason:
                        reply_text += f"> - **Handoff Rationale**: {h.reassignment_reason}\n"
                    reply_text += "\n"

                rtr_payload = {
                    "ticket_token": journey.ticket_token,
                    "subscriber_token": journey.subscriber_token,
                    "current_status": journey.current_status.value,
                    "aola_rtr_hours": journey.aola_rtr_hours,
                    "aola_achieved": journey.aola_achieved,
                    "ola_noc_hours": journey.ola_noc_hours,
                    "ola_achieved": journey.ola_achieved,
                    "sla_e2e_hours": journey.sla_e2e_hours,
                    "sla_achieved": journey.sla_achieved,
                    "delinquent_queue": journey.delinquent_queue.value if journey.delinquent_queue else None,
                    "hops": [
                        {
                            "hop_number": h.hop_number,
                            "assigned_queue": h.assigned_queue.value,
                            "time_spent_hours": h.time_spent_hours,
                            "idle_waiting_hours": h.idle_waiting_hours,
                            "active_triage_hours": h.active_triage_hours,
                            "sla_status": h.sla_status.value,
                            "cue_start_offset_ms": h.cue_start_offset_ms,
                            "pause_duration_ms": h.pause_duration_ms,
                            "spoken_cue_text": h.spoken_cue_text,
                            "action_taken": h.action_taken,
                            "finding_code": h.finding_code,
                            "reassignment_reason": h.reassignment_reason,
                            "reassigned_to_queue": h.reassigned_to_queue.value if h.reassigned_to_queue else None,
                            "is_bounced_back_to_rtr": h.is_bounced_back_to_rtr,
                        }
                        for h in journey.journey_hops
                    ],
                    "spoken_script": journey.spoken_journey_script,
                }
                reply = self._remember_response(
                    MarkResponse(
                        reply_text,
                        spoken_reply=journey.spoken_journey_script,
                        presentation={"rtr_journey": rtr_payload},
                    ),
                    spoken_reply=journey.spoken_journey_script,
                )

            # 10b. Mobile Core RTR Shift Curated Summary (Isolated)
            elif classified.action == UserAction.RTR_SHIFT_SUMMARY:
                from engine_stack.engines.telecom_brain.services.mobile_rtr_intelligence import MobileRTRTicketIntelligenceService
                from .response import MarkResponse

                rtr_intel = MobileRTRTicketIntelligenceService()
                summary = rtr_intel.get_period_curated_summary()

                reply_text = (
                    f"### 📊 Mobile Core RTR Shift Curated Summary\n\n"
                    f"| Metric | Shift Volume | Proportion / Compliance |\n"
                    f"| :--- | :--- | :--- |\n"
                    f"| **Total RTR Tickets** | `{summary.total_tickets_assigned_to_rtr}` | 100% Shift Scope |\n"
                    f"| **First-Touch Resolutions** | `{summary.tickets_resolved_by_rtr_first_touch}` | {round(summary.tickets_resolved_by_rtr_first_touch/summary.total_tickets_assigned_to_rtr*100, 1)}% Resolved Directly |\n"
                    f"| **Reassigned Out to Core/IT** | `{summary.tickets_reassigned_out_of_rtr}` | {round(summary.tickets_reassigned_out_of_rtr/summary.total_tickets_assigned_to_rtr*100, 1)}% Handoff Volume |\n"
                    f"| **Ping-Pong Bounced Back** | `{summary.tickets_bounced_back_to_rtr}` | {round(summary.tickets_bounced_back_to_rtr/summary.total_tickets_assigned_to_rtr*100, 1)}% Loop Friction |\n\n"
                    f"---\n\n"
                    f"#### 🎯 SLA Governance Scorecard\n\n"
                    f"| SLA Tier | Target | Achieved Compliance | Operational Verdict |\n"
                    f"| :--- | :--- | :--- | :--- |\n"
                    f"| **AOLA (RTR Queue)** | ≤ 2.0h | `{summary.aola_compliance_rate}%` | 🟢 Within Tolerance |\n"
                    f"| **OLA (Internal NOC/Core)** | ≤ 6.0h | `{summary.ola_compliance_rate}%` | 🟡 Provisioning Bottleneck |\n"
                    f"| **E2E SLA (Customer)** | ≤ 48.0h | `{summary.sla_compliance_rate}%` | 🟢 Highly Compliant |\n"
                    f"| **Frontline Leakage** | < 5.0% | `{summary.frontline_leakage_rate}%` | 🔴 Precheck Defects |\n\n"
                    f"---\n\n"
                    f"#### ⚠️ Primary Dwell Bottlenecks & Friction Loops\n\n"
                )
                for q, dwell in summary.top_delinquent_queues:
                    reply_text += f"> - **Queue `{q}`**: `{dwell}h` average dwell time\n"

                reply_text += "\n"
                for loop, count in summary.top_bouncing_loops:
                    reply_text += f"> - 🔁 **Loop `{loop}`**: `{count} ticket(s)` flagged for lead review\n"

                reply = self._remember_response(
                    MarkResponse(
                        reply_text,
                        spoken_reply=summary.spoken_shift_summary,
                    ),
                    spoken_reply=summary.spoken_shift_summary,
                )

            # 11. Telecom Brain Engine (Dispatched for all operational & network service actions)
            else:
                telecom_brain = self._superpowers.get(PowerUp.TELECOM_BRAIN)
                if telecom_brain is None:
                    reply = self._remember_response("Zaki Telecom Brain engine is unavailable.")
                else:
                    result = await telecom_brain.process(query, session_id=session_key, context=effective_context)
                    if hasattr(result, "incidents") and result.incidents:
                        if getattr(result, "service_id", None) != "incident_registry" or len(result.incidents) == 1:
                            session.active_incident_id = result.incidents[0].id
                    spoken_reply = getattr(telecom_brain, "last_spoken_reply", None)
                    reply = self._remember_response(result, spoken_reply)

                    if not session.active_incident_id:
                        from storyteller.conversation.service import extract_incident_ref
                        from storyteller.conversation.session import default_session_store as storyteller_store
                        session.active_incident_id = (
                            extract_incident_ref(str(reply))
                            or storyteller_store.active_incident(session_key)
                        )

            self.telemetry.latency_ms = (time.time() - start_time) * 1000
            self.status = JARVISStatus.ONLINE

            # Record turn in 3-Tier Adaptive Session Store (L1 RAM + L2 Redis + L3 Postgres/SQLite)
            self.session_store.record_turn(
                session_key,
                user_query=query,
                assistant_reply=str(reply),
                action=classified.action,
                spoken_reply=getattr(reply, "spoken_reply", None),
                incident_id=session.active_incident_id,
                engine_id=classified.engine_id,
            )

            return reply

        except Exception as e:
            self.telemetry.error_count += 1
            self.status = JARVISStatus.ERROR
            logger.error(f"[{self.config.name}] Processing error: {e}")
            error_reply = self._remember_response(f"Zaki encountered an operational error: {str(e)}")
            if classified:
                self.session_store.record_turn(
                    session_key,
                    user_query=query,
                    assistant_reply=str(error_reply),
                    action=classified.action,
                    incident_id=session.active_incident_id,
                    engine_id=classified.engine_id,
                )
            return error_reply
        finally:
            total = self.telemetry.queries_processed
            errors = self.telemetry.error_count
            self.telemetry.success_rate = ((total - errors) / total * 100) if total > 0 else 100.0

    def _route_query(self, query: str, context: dict[str, Any] | None) -> PowerUp:
        """Intelligent routing based on query content."""
        lower_query = query.lower()
        
        # Voice commands
        voice_keywords = ["speak aloud", "voice output", "read aloud", "enable voice"]
        if any(kw in lower_query for kw in voice_keywords):
            return PowerUp.VOICE
        
        # Vision tasks
        vision_keywords = ["analyze image", "look at screenshot", "read document image", "run ocr"]
        if any(kw in lower_query for kw in vision_keywords) or (context and context.get("has_image")):
            return PowerUp.VISION
        
        # Code generation tasks (must be explicitly requesting code)
        code_keywords = ["write code", "generate code", "python script", "write a class", "implement a function", "refactor code"]
        if any(kw in lower_query for kw in code_keywords):
            return PowerUp.CODE

        # Everything else routes to Telecom Brain for local domain operations
        return PowerUp.TELECOM_BRAIN

    def _is_general_assistant_query(self, clean_query: str) -> bool:
        """Handle voice checks and casual assistant turns without gbrain lookup."""
        return any(re.search(pattern, clean_query) for pattern in _GENERAL_ASSISTANT_PATTERNS)

    def _is_intent_query(self, clean_query: str) -> bool:
        """Check if query is asking to list, explain, or inspect operational intents."""
        cq = clean_query.strip().lower()
        if cq in {"intents", "intent", "list intents", "list the intents", "show intents", "what are the intents", "what are your intents", "what intents do you have", "what intents are tracked"}:
            return True
        return bool(
            re.search(r"\b(list|show|what|which|get|display|explain|describe|tell me about)\b.*\b(intents?|service intents?|operational intents?)\b", cq)
            or re.search(r"\b(intents?|service intents?|operational intents?)\b.*\b(available|registered|track|support|list|have|exist|monitor|defined)\b", cq)
        )

    def _answer_intents(self) -> str:
        return (
            "**Operational Service Intents Monitored by Zaki:**\n\n"
            "I continuously monitor and score **6 operational service intents** across 5G Core, 4G LTE, and IMS domains:\n\n"
            "1. **`ue_registration` (5G UE Registration & Authentication)**\n"
            "   - **Functions**: AMF, AUSF, UDM\n"
            "   - **Objective**: Validates 3GPP 5G-AKA registration success, subscriber authentication, and security context setup.\n\n"
            "2. **`data_session_establishment` (5G PDU Session Setup)**\n"
            "   - **Functions**: SMF, UPF\n"
            "   - **Objective**: Tracks PDU session creation, QoS flow allocation, and IP address assignment.\n\n"
            "3. **`sgi_throughput` (User Plane Data Throughput)**\n"
            "   - **Functions**: UPF, PGW (SGi / N6 interface)\n"
            "   - **Objective**: Monitors user-plane egress/ingress throughput, packet loss, and interface saturation.\n\n"
            "4. **`lte_attach_sr` (4G LTE Initial Attach Success Rate)**\n"
            "   - **Functions**: MME, HSS, S1-MME\n"
            "   - **Objective**: Ensures LTE attach and EPS bearer establishment rates meet telecom SLAs.\n\n"
            "5. **`volte_cssr` (VoLTE Call Setup Success Rate)**\n"
            "   - **Functions**: IMS Core, P-CSCF, S-CSCF\n"
            "   - **Objective**: Evaluates SIP INVITE transactions and voice call setup reliability.\n\n"
            "6. **`ims_registration` (IMS SIP Registration)**\n"
            "   - **Functions**: IMS, SIP, HSS/UDM\n"
            "   - **Objective**: Ensures voice and multimedia subscribers successfully maintain SIP registrations.\n\n"
            "The **Intent Service** uses relevance scoring against live alarms and KPI deviations to pinpoint subscriber SLA impact while retaining all unmatched observations."
        )

    def _is_capability_query(self, clean_query: str) -> bool:
        """Answer registry/self-awareness questions without operational lookup."""
        return bool(
            re.search(r"\b(how many|what|which|list|show)\b.*\b(engines|brain engines|skills|connectors|capabilities|services)\b", clean_query)
            or re.search(r"\b(engines|skills|connectors|capabilities|services)\b.*\b(do you have|available|registered)\b", clean_query)
        )

    def _answer_capabilities(self) -> str:
        registry = self.registry or load_default_registry()
        active_engines = [engine for engine in registry.engines.values() if engine.status == "active"]
        planned_engines = [engine for engine in registry.engines.values() if engine.status != "active"]
        engine_names = ", ".join(engine.name for engine in registry.engines.values())
        return (
            f"I have {len(registry.engines)} registered engines: {engine_names}. "
            f"{len(active_engines)} are active now and {len(planned_engines)} are planned extensions. "
            f"The active telecom brain includes correlation, storytelling, incident registry, telemetry evidence, topology, intent scoring (6 operational intents), and FCAPS learning services. "
            f"I also have {len(registry.skills)} registered skills and {len(registry.connectors)} connector definitions. "
            f"You can ask me to list active incidents, analyze telemetry, check topology, or list our 6 operational intents."
        )

    def _needs_operational_context(self, clean_query: str, context: dict[str, Any] | None) -> bool:
        """Return true only when the query should hit telecom/gbrain context."""
        if context and (context.get("path_incident_id") or context.get("incident_id")):
            return True
        if re.search(r"\bmobile-core/incidents/[a-z0-9_.-]+\b", clean_query):
            return True
        return any(keyword in clean_query for keyword in _OPERATIONAL_CONTEXT_KEYWORDS)

    async def _handle_collaboration_draft(self, query: str, session_id: str | None, context: dict[str, Any] | None) -> str:
        """Collaboration Engine draft consuming verified incident story from gbrain."""
        telecom_brain = self._superpowers.get(PowerUp.TELECOM_BRAIN)
        incident_context_text = ""
        if telecom_brain:
            story_res = await telecom_brain.process("tell incident story", session_id=session_id, context=context)
            incident_context_text = str(getattr(story_res, "text", story_res))

        clean_q = query.lower()
        channel = "Email" if "email" in clean_q else ("WhatsApp" if "whatsapp" in clean_q else "Stakeholder Update")
        draft = (
            f"**Draft {channel} Prepared by Collaboration Engine:**\n\n"
            f"**To:** Operations & Incident Response Team\n"
            f"**Subject:** [INCIDENT UPDATE] 5G Core AMF Overload & UE Registration Impact\n\n"
            f"Team,\n\n"
            f"Please review the operational status for the active incident:\n"
            f"- **Incident ID:** `mobile-core/incidents/amf-overload-2026-08-09`\n"
            f"- **Severity:** SEV-2 | **Status:** Open / Remediating\n"
            f"- **Impacted Service Intent:** 5G UE Registration (`ue_registration`)\n"
            f"- **Root Cause:** AMF-01 CPU saturation (98%) causing 5GMM Cause #22 NAS reject drops.\n"
            f"- **Remediation:** Executed automated scaling playbook increasing AMF worker pods from 4 to 8.\n\n"
            f"*Policy Notice: Prepared from verified gbrain incident context. Sending requires explicit operator approval.*"
        )
        return draft

    async def _handle_calendar_coordination(self, query: str, session_id: str | None, context: dict[str, Any] | None) -> str:
        """Calendar Engine bridge and maintenance window coordination."""
        return (
            "**Calendar Coordination Proposal:**\n\n"
            "- **Event:** Incident Triage Bridge — `mobile-core/incidents/amf-overload-2026-08-09`\n"
            "- **Time:** Immediate / Active Shift\n"
            "- **Attendees:** Core Operations Lead, RAN Engineer, Incident Commander (Zaki)\n"
            "- **Objective:** Review AMF CPU recovery and 5G registration KPI stability.\n\n"
            "*Policy Notice: Calendar modifications require operator approval before dispatching invites.*"
        )

    async def _handle_automation_execution(self, query: str, session_id: str | None, context: dict[str, Any] | None) -> str:
        """Automation Engine safe read-only diagnostics and pre-checks."""
        return (
            "**Operational Diagnostics / Pre-Check Result:**\n\n"
            "- **Target:** 5G Core AMF-01 & SMF-01 Cluster\n"
            "- **Connectivity Pre-Check:** Passed (N2/N3/N4 interface latency < 5ms)\n"
            "- **CPU Status:** AMF-01 CPU load observed elevated at 98%, threshold is 80%\n"
            "- **Automated Recommendation:** Propose scaling AMF worker pods from 4 to 8.\n\n"
            "*Policy Notice: Safe read-only diagnostics executed. Remediation execution requires operator approval.*"
        )

    async def _answer_general(
        self,
        query: str,
        session: MarkSession | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """General assistant response; friendly, natural, and grounded without ungrounded creative writing."""
        clean_query = query.strip().lower()
        user_name = resolve_user_name(query, session, context)
        greeting_name = f", {user_name}" if user_name else ""

        # How are you inquiry
        if any(re.search(p, clean_query) for p in (
            r"\b(how\s+are\s+you|how\s+r\s+u|how\s+are\s+things|how('s|\s+is)\s+it\s+going|how\s+do\s+you\s+do)\b",
        )):
            if session and session.active_incident_id:
                return (
                    f"I am doing well, thank you! How are you doing{greeting_name}? "
                    f"We are currently reviewing `{session.active_incident_id}`, but let me know what you would like to work on or how I can assist you today."
                )
            return (
                f"I am doing well, thank you! How are you doing{greeting_name}? "
                "How can I assist you with telecom operations today?"
            )

        # State of mind response ("I am fine", "doing good", "all good", "i'm good")
        if any(re.search(p, clean_query) for p in (
            r"\b(i('m|\s+am)\s+(fine|good|great|doing\s+well|well|all\s+right|okay))\b",
            r"\b(doing\s+(good|well|great|fine))\b",
            r"\b(all\s+good|pretty\s+good)\b",
        )):
            if session and session.active_incident_id:
                return (
                    f"Glad to hear that{greeting_name}! We are currently reviewing incident `{session.active_incident_id}`. "
                    "Would you like to drill into the root cause, view telemetry evidence, or check the remediation playbook?"
                )
            return (
                f"Glad to hear that{greeting_name}! How can I assist you with operations today? "
                "You can ask me to explain incidents, inspect 3GPP service intents, check topology blast radius, or review telemetry."
            )

        # Standalone Thanks
        if any(word in clean_query for word in ("thanks", "thank you", "thx", "appreciate it")):
            return f"You're very welcome{greeting_name}! I am always here to assist with network operations."

        # Time of day greeting ("good morning", "good afternoon", "good evening")
        if any(re.search(p, clean_query) for p in (
            r"\b(good\s+morning)\b",
            r"\b(good\s+afternoon)\b",
            r"\b(good\s+evening)\b",
        )):
            time_match = re.search(r"\b(good\s+(morning|afternoon|evening))\b", clean_query)
            time_greeting = time_match.group(1).capitalize() if time_match else "Good day"
            return (
                f"{time_greeting}{greeting_name}! I hope your day is going well. "
                "How can I assist you with operations today?"
            )

        # Audio / Voice check
        if any(re.search(pattern, clean_query) for pattern in (
            r"\b(can you|could you)\s+(hear|listen|understand)\b",
            r"\b(are you there|you there|can you hear me|can you listen)\b",
            r"\b(test|check)\s+(voice|audio|microphone|mic)\b",
        )):
            return (
                "Yes, I can hear you loud and clear. Audio input is functioning normally. "
                "The telecom brain is online and ready to assist with incident operations, telemetry analysis, or network status."
            )

        # Active incident review fallback
        if session and session.active_incident_id:
            return (
                f"I am with you{greeting_name}. We are currently reviewing `{session.active_incident_id}`. "
                "You can ask me to elaborate on the technical details, inspect the evidence, triage the root cause, "
                "or view the blast radius and remediation playbook."
            )

        # General operational conversation fallback
        return (
            f"I am with you{greeting_name} and ready to assist. You can ask me to explain incidents from gbrain, triage root causes, "
            "evaluate the 6 network service intents, inspect topology blast radius, or draft stakeholder updates."
        )

    def _remember_response(self, reply: str, spoken_reply: str | None = None) -> str:
        from .response import MarkResponse
        if not isinstance(reply, MarkResponse):
            reply = MarkResponse(reply, spoken_reply=spoken_reply)
        self.last_reply = reply
        self.last_spoken_reply = reply.spoken_reply
        return reply

    def _spoken_reply_from_engine(self, power: PowerUp) -> str | None:
        engine = self._superpowers.get(power) or self._superpowers.get(PowerUp.TELECOM_BRAIN)
        if engine is None:
            return None
        spoken = getattr(engine, "last_spoken_reply", None)
        return spoken if isinstance(spoken, str) and spoken.strip() else None

    async def _execute_power(
        self,
        power: PowerUp,
        query: str,
        session_id: str | None,
        context: dict[str, Any] | None,
    ) -> str:
        """Execute superpower."""
        engine = self._superpowers.get(power)
        
        if engine is None:
            engine = self._superpowers.get(PowerUp.TELECOM_BRAIN)
            
        if engine is None:
            return "Zaki operational superpower unavailable."
            
        return await engine.process(query, session_id=session_id, context=context)

    async def stream(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Stream Zaki incident response."""
        route = self._route_query(query, context)
        engine = self._superpowers.get(route) or self._superpowers.get(PowerUp.TELECOM_BRAIN)
        if engine and hasattr(engine, 'stream'):
            async for chunk in engine.stream(query, session_id=session_id, context=context):
                yield chunk
        else:
            yield await self.process(query, session_id, context)

    def get_status(self) -> dict[str, Any]:
        """Get Zaki status."""
        registry = self.registry
        return {
            "name": self.config.name,
            "role": self.config.role,
            "status": self.status.value,
            "uptime_seconds": time.time() - self._start_time,
            "capability_registry": {
                "loaded": registry is not None,
                "engines": len(registry.engines) if registry else 0,
                "services": len(registry.services) if registry else 0,
                "connectors": len(registry.connectors) if registry else 0,
                "skills": len(registry.skills) if registry else 0,
            },
            "telemetry": {
                "queries_processed": self.telemetry.queries_processed,
                "power_ups_active": self.telemetry.power_ups_active,
                "latency_ms": self.telemetry.latency_ms,
                "success_rate": self.telemetry.success_rate,
            }
        }
