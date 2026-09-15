"""
Action classifier for M.A.R.K.

Two-Pass Hybrid Architecture:
1. Pass 1: Ultra-fast deterministic rule matcher (<0.5ms) using precompiled ACTION_RULES.
2. Pass 2: Semantic LLM fallback using session history for casual, ambiguous, or conversational turns.

Maintains strict two-layer disambiguation:
- UserAction: Assistant-tier cognitive operation.
- NetworkServiceIntent: 3GPP autonomic SLA objective.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Any

from storyteller.conversation.service import extract_incident_ref
from .user_actions import NetworkServiceIntent, SERVICE_INTENT_ALIASES, UserAction

logger = logging.getLogger("assistant.mark.action_classifier")


@dataclass
class ClassifiedAction:
    action: UserAction
    confidence: float
    engine_id: str
    extracted_incident_id: str | None = None
    target_service_intent: NetworkServiceIntent | None = None
    target_intent: str | None = None
    reason: str = ""


@dataclass(frozen=True)
class ActionRule:
    """Precompiled rule mapping regular expressions to cognitive actions."""
    action: UserAction
    engine_id: str
    pattern: re.Pattern
    target_intent: str | None = None
    confidence: float = 0.90
    requires_session_context: bool = False
    reason: str = ""


# =====================================================================
# DECLARATIVE PRECOMPILED RULE REGISTRY (Replaces scattered variables)
# =====================================================================

ACTION_RULES: tuple[ActionRule, ...] = (
    # 0a. Mobile Core RTR Customer Ticket Journey (Priority matching for TT tokens & ticket journeys)
    ActionRule(
        action=UserAction.CUSTOMER_TICKET_JOURNEY,
        engine_id="telecom_brain",
        pattern=re.compile(
            r"\b(tt-\d+|ticket\s*journey|customer\s*ticket|trace\s*ticket|walk\s*me\s*through\s*(the\s*)?ticket|journey\s*of\s*(the\s*)?ticket)\b"
            r"|\b(trouble\s*ticket\s*journey|ticket\s*hops?|ticket\s*dwell|aola|ola)\b",
            re.IGNORECASE,
        ),
        confidence=0.98,
        reason="Customer ticket journey diagnostic request",
    ),

    # 0b. Mobile Core RTR Shift Curated Summary
    ActionRule(
        action=UserAction.RTR_SHIFT_SUMMARY,
        engine_id="telecom_brain",
        pattern=re.compile(
            r"\b(rtr\s*shift\s*summary|curated\s*summary\s*of\s*(the\s*)?(customer\s*)?tickets?|tickets?\s*in\s*rtr\s*queues?)\b"
            r"|\b(rtr\s*tickets?\s*summary|summary\s*of\s*(all\s*)?tickets?\s*handled\s*by\s*rtr|tickets?\s*handled\s*by\s*rtr)\b",
            re.IGNORECASE,
        ),
        confidence=0.96,
        reason="RTR shift curated ticket summary request",
    ),

    # 1. Collaboration Engine
    ActionRule(
        action=UserAction.DRAFT_COMMUNICATION,
        engine_id="collaboration",
        pattern=re.compile(
            r"\b(draft|send|compose|write|prepare)\s+(an?\s+)?(email|e-mail|message|whatsapp|teams\s+message|update)\b"
            r"|\b(stakeholder\s+update|shift\s+handover|customer\s+update)\b",
            re.IGNORECASE,
        ),
        reason="Collaboration / communication draft request",
    ),

    # 2. Calendar Engine
    ActionRule(
        action=UserAction.MANAGE_CALENDAR,
        engine_id="calendar",
        pattern=re.compile(
            r"\b(schedule|book|setup|set\s+up)\s+(an?\s+)?(meeting|bridge|incident\s+bridge|sync)\b"
            r"|\b(maintenance\s+window|create\s+reminder|check\s+calendar)\b",
            re.IGNORECASE,
        ),
        reason="Calendar or maintenance window coordination",
    ),

    # 3. Codex Engineering Engine
    ActionRule(
        action=UserAction.EXECUTE_CODE,
        engine_id="codex_engineering",
        pattern=re.compile(
            r"\b(write\s+code|generate\s+code|python\s+script|write\s+a\s+class|implement\s+a\s+function|refactor\s+code|create\s+patch|run\s+tests|debug\s+code)\b",
            re.IGNORECASE,
        ),
        reason="Code generation or debugging request",
    ),

    # 4. Automation Engine
    ActionRule(
        action=UserAction.RUN_AUTOMATION,
        engine_id="automation",
        pattern=re.compile(
            r"\b(run|execute)\s+(a\s+)?(health\s*check|pre\s*check|diagnostics?|precheck)\b"
            r"|\b(propose\s+remediation|automated\s+check)\b",
            re.IGNORECASE,
        ),
        reason="Automation diagnostics or precheck request",
    ),

    # 5. Assistant Capabilities
    ActionRule(
        action=UserAction.INSPECT_CAPABILITIES,
        engine_id="assistant",
        pattern=re.compile(
            r"\b(how\s+many|what|which|list|show)\b.*\b(engines|brain\s+engines|skills|connectors|capabilities|services)\b"
            r"|\b(engines|skills|connectors|capabilities|services)\b.*\b(do\s+you\s+have|available|registered)\b"
            r"|\b(what\s+can\s+you\s+do|help\s+me)\b",
            re.IGNORECASE,
        ),
        reason="Capability inspection request",
    ),

    # 6. Conversational Follow-Ups (Elaboration / Evidence / Remediation / Timeline)
    ActionRule(
        action=UserAction.EXPLAIN_INCIDENT,
        engine_id="telecom_brain",
        pattern=re.compile(
            r"\b(tell\s+me\s+more|can\s+you\s+elaborate|elaborate(\s+on\s+that)?|give\s+me\s+more\s+details?|go\s+deeper|explain\s+(that\s+)?further|more\s+insights?|tell\s+more)\b",
            re.IGNORECASE,
        ),
        target_intent="technical",
        confidence=0.92,
        requires_session_context=True,
        reason="Contextual elaboration follow-up",
    ),
    ActionRule(
        action=UserAction.EXPLAIN_INCIDENT,
        engine_id="telecom_brain",
        pattern=re.compile(
            r"\b(what\s+evidence|evidence|proof|what\s+supports?(\s+this|\s+that)?|supporting\s+data|where\s+did\s+you\s+see\s+that|supporting\s+proof)\b",
            re.IGNORECASE,
        ),
        target_intent="evidence",
        confidence=0.92,
        requires_session_context=True,
        reason="Contextual evidence drilling follow-up",
    ),
    ActionRule(
        action=UserAction.INSPECT_RUNBOOK,
        engine_id="telecom_brain",
        pattern=re.compile(
            r"\b(how\s+did\s+we\s+fix\s+(it|this|that)|what\s+was\s+the\s+fix|what\s+was\s+the\s+mitigation|how\s+was\s+it\s+resolved|what\s+action\s+was\s+taken|how\s+to\s+fix)\b",
            re.IGNORECASE,
        ),
        target_intent="remediation",
        confidence=0.92,
        requires_session_context=True,
        reason="Contextual remediation inquiry follow-up",
    ),
    ActionRule(
        action=UserAction.EXPLAIN_INCIDENT,
        engine_id="telecom_brain",
        pattern=re.compile(
            r"\b(what\s+was\s+the\s+timeline|timeline\s+of\s+events|when\s+did\s+it\s+start|sequence\s+of\s+events)\b",
            re.IGNORECASE,
        ),
        target_intent="timeline",
        confidence=0.92,
        requires_session_context=True,
        reason="Contextual timeline inquiry follow-up",
    ),
    ActionRule(
        action=UserAction.INSPECT_TOPOLOGY,
        engine_id="telecom_brain",
        pattern=re.compile(
            r"\b(who\s+(was|is)\s+impacted|what\s+is\s+the\s+blast\s+radius|affected\s+subscribers?|what\s+else\s+failed)\b",
            re.IGNORECASE,
        ),
        target_intent="impact",
        confidence=0.92,
        requires_session_context=True,
        reason="Contextual blast radius / impact follow-up",
    ),

    # 7. Incident Registry / Queue (Matched before storytelling)
    ActionRule(
        action=UserAction.LIST_INCIDENTS,
        engine_id="telecom_brain",
        pattern=re.compile(
            r"\b(list|show|get|all|current|active|open|recent)\b.*\bincidents?\b"
            r"|\bincidents?\b.*\b(list|queue|status|registry|open|active|overview|summary|current)\b"
            r"|\b(what|which)\s+(are\s+the\s+)?(current\s+|active\s+|open\s+)?incidents?\b"
            r"|\b(incident\s+registry|registry\s+status|incident\s+queue|incident\s+list)\b",
            re.IGNORECASE,
        ),
        confidence=0.95,
        reason="Incident registry listing query",
    ),

    # 8. Storytelling & Incident Narrative
    ActionRule(
        action=UserAction.EXPLAIN_INCIDENT,
        engine_id="telecom_brain",
        pattern=re.compile(
            r"\b(tell\s+me\s+(about\s+)?(a|any)?\s*story)\b"
            r"|\b(story|narrative|timeline|chronology)\b"
            r"|\b(what\s+happened|what\s+occurred|walk\s+me\s+through)\b"
            r"|\b(explain|describe)\s+(the\s+)?(incident|outage|failure|degradation)\b"
            r"|\b(post\s*incident\s*review|pir|executive\s*brief|noc\s*brief)\b",
            re.IGNORECASE,
        ),
        target_intent="story",
        confidence=0.90,
        reason="Storytelling or incident narrative request",
    ),

    # 9. Root Cause Analysis (RCA)
    ActionRule(
        action=UserAction.DIAGNOSE_RCA,
        engine_id="telecom_brain",
        pattern=re.compile(
            r"\b(root\s*cause|rca|what\s+caused|why\s+did|why\s+is|reason\s+for)\b"
            r"|\b(hypothesis|hypotheses|diagnostic|triage|missing\s+proof)\b"
            r"|\b(failure\s+analysis|leading\s+cause)\b",
            re.IGNORECASE,
        ),
        target_intent="root_cause",
        confidence=0.90,
        reason="Root cause or failure diagnostic query",
    ),

    # 10. Topology & Blast Radius
    ActionRule(
        action=UserAction.INSPECT_TOPOLOGY,
        engine_id="telecom_brain",
        pattern=re.compile(
            r"\b(topology|dependency(\s+path)?|blast\s+radius|affected\s+components)\b"
            r"|\b(network\s+functions?|amf|smf|upf|gnb|gnodeb|mme|hss)\b"
            r"|\b(network\s+inventory|logical\s+topology)\b",
            re.IGNORECASE,
        ),
        confidence=0.85,
        reason="Topology or blast radius query",
    ),

    # 11. Alarm Correlation
    ActionRule(
        action=UserAction.CORRELATE_ALARMS,
        engine_id="telecom_brain",
        pattern=re.compile(
            r"\b(correlation|correlate|alarm\s+storm|cross-domain|correlated\s+events)\b",
            re.IGNORECASE,
        ),
        confidence=0.85,
        reason="Alarm correlation query",
    ),

    # 12. Network Health & Telemetry
    ActionRule(
        action=UserAction.CHECK_NETWORK_HEALTH,
        engine_id="telecom_brain",
        pattern=re.compile(
            r"\b(kpi|telemetry|grafana|health|throughput|latency|packet\s+loss)\b",
            re.IGNORECASE,
        ),
        confidence=0.85,
        reason="Network health or KPI telemetry query",
    ),

    # 13. Runbook / MOP / Playbook
    ActionRule(
        action=UserAction.INSPECT_RUNBOOK,
        engine_id="telecom_brain",
        pattern=re.compile(
            r"\b(runbook|playbook|mop|remediation|mitigation|standard\s+operating\s+procedure)\b",
            re.IGNORECASE,
        ),
        confidence=0.85,
        reason="Playbook or remediation query",
    ),

    # 14. FCAPS Domain Lens
    ActionRule(
        action=UserAction.FCAPS_ANALYSIS,
        engine_id="telecom_brain",
        pattern=re.compile(r"\bfcaps\b", re.IGNORECASE),
        confidence=0.85,
        reason="FCAPS domain lens query",
    ),

    # 15. Architecture Docs
    ActionRule(
        action=UserAction.ARCHITECTURE_DOCS,
        engine_id="telecom_brain",
        pattern=re.compile(
            r"\b(architecture|architectural|design\s+doc|questionnaire|reference|hld|lld|how\s+.*built)\b"
            r"|\b(telecom\s+brain\s+architecture|documentation)\b",
            re.IGNORECASE,
        ),
        confidence=0.85,
        reason="Telecom Brain architecture document query",
    ),
)


# =====================================================================
# PASS 1: FAST-PATH DETERMINISTIC MATCHER (<0.5ms)
# =====================================================================

def _fast_path_classify(
    query: str,
    context: dict[str, Any] | None,
    session: Any | None,
) -> ClassifiedAction | None:
    """Sub-millisecond rule-based classifier for real-time voice and obvious commands."""
    clean_q = query.strip().lower()
    incident_id = (
        extract_incident_ref(query)
        or (context.get("incident_id") if context else None)
        or (getattr(session, "active_incident_id", None) if session else None)
    )

    # 1. Conversational pleasantries & audio checks
    if any(re.search(p, clean_q) for p in (
        r"\b(can you|could you)\s+(hear|listen|understand)\b",
        r"\b(are you there|you there|can you hear me|can you listen)\b",
        r"\b(test|check)\s+(voice|audio|microphone|mic)\b",
    )):
        return ClassifiedAction(
            action=UserAction.CONVERSE,
            confidence=0.95,
            engine_id="assistant",
            reason="Voice or mic check",
        )

    if any(re.search(p, clean_q) for p in (
        r"\b(how\s+are\s+you|how\s+r\s+u|how\s+are\s+things|how('s|\s+is)\s+it\s+going|how\s+do\s+you\s+do)\b",
        r"\b(i('m|\s+am)\s+(fine|good|great|doing\s+well|well|all\s+right|okay))\b",
        r"\b(doing\s+(good|well|great|fine))\b",
        r"\b(good\s+(morning|afternoon|evening|day))\b",
        r"\b(thanks|thank\s+you|thx|appreciate\s+it)\b",
    )):
        return ClassifiedAction(
            action=UserAction.CONVERSE,
            confidence=0.95,
            engine_id="assistant",
            reason="Conversational pleasantry",
        )

    # 2. Exact greetings & identity
    if any(re.search(p, clean_q) for p in (
        r"^(hi|hello|hey|greetings|welcome)(\s+there)?(\s+mark)?[\s!.]*$",
        r"\b(who\s+are\s+you|what\s+is\s+your\s+name|introduce\s+yourself)\b",
    )):
        return ClassifiedAction(
            action=UserAction.GREETING,
            confidence=1.0,
            engine_id="assistant",
            reason="Exact greeting / identity match",
        )

    # 3. Voice & Vision superpowers
    if any(kw in clean_q for kw in ["speak aloud", "voice output", "read aloud", "enable voice"]):
        return ClassifiedAction(
            action=UserAction.VOICE_COMMAND,
            confidence=0.95,
            engine_id="superpower.voice",
            reason="Explicit voice command",
        )

    if any(kw in clean_q for kw in ["analyze image", "look at screenshot", "read document image", "run ocr"]) or (context and context.get("has_image")):
        return ClassifiedAction(
            action=UserAction.VISION_TASK,
            confidence=0.95,
            engine_id="superpower.vision",
            reason="Vision request",
        )

    # 4. Service Intent Lookup (3GPP / SLA tier)
    target_service_intent = _detect_service_intent(clean_q)
    if any(re.search(p, clean_q) for p in (
        r"\b(what|list|show|which|get|describe|display|explain|catalog|all|tell\s+me\s+about)\b.*\b(intents?|service intents?|operational intents?|slas?)\b",
        r"\b(intents?|service intents?|operational intents?)\b.*\b(available|registered|track|support|list|have|exist|monitor|defined|breach|violation|impact)\b",
        r"\b(ue[_-]?registration|data[_-]?session|sgi[_-]?throughput|lte[_-]?attach|volte[_-]?cssr|ims[_-]?registration)\b",
    )):
        return ClassifiedAction(
            action=UserAction.CHECK_SERVICE_INTENTS,
            confidence=0.95,
            engine_id="telecom_brain",
            target_service_intent=target_service_intent,
            reason="Operator querying 3GPP network service intents / SLAs",
        )

    # 5. Negative story intent / Story opt-out (user explicitly refuses a story)
    if any(re.search(p, clean_q) for p in (
        r"\b(do\s*n['o]?t|no|stop|never|without|not\s+need|don'?t\s+need|don'?t\s+want|dislike|skip)\b.*\b(story|stories|narrative)\b",
        r"\b(story|stories|narrative)\b.*\b(not\s+needed|unnecessary|not\s+wanted)\b",
    )):
        return ClassifiedAction(
            action=UserAction.CONVERSE,
            confidence=0.98,
            engine_id="assistant",
            reason="User opted out of incident story",
        )

    # 6. Compiled Action Rule Registry Match
    has_active_context = bool(incident_id or (session and getattr(session, "turns", None)))
    for rule in ACTION_RULES:
        if rule.requires_session_context and not has_active_context:
            continue
        if rule.pattern.search(clean_q):
            return ClassifiedAction(
                action=rule.action,
                confidence=rule.confidence,
                engine_id=rule.engine_id,
                extracted_incident_id=incident_id,
                target_intent=rule.target_intent,
                reason=rule.reason,
            )

    # 7. Fallback only if an incident ID was explicitly present in the query itself
    explicit_in_query = extract_incident_ref(query)
    if explicit_in_query:
        return ClassifiedAction(
            action=UserAction.EXPLAIN_INCIDENT,
            confidence=0.80,
            engine_id="telecom_brain",
            extracted_incident_id=explicit_in_query,
            reason="Defaulting to incident explanation with explicit in-query incident reference",
        )

    return None


def _detect_service_intent(clean_q: str) -> NetworkServiceIntent | None:
    """Declarative lookup of 3GPP service intent using SERVICE_INTENT_ALIASES."""
    for intent, aliases in SERVICE_INTENT_ALIASES.items():
        if any(alias in clean_q for alias in aliases):
            return intent
    return None


# =====================================================================
# PASS 2: SEMANTIC INTENT FALLBACK (LLM with Session History)
# =====================================================================

def _semantic_fallback_classify(
    query: str,
    context: dict[str, Any] | None,
    session: Any | None,
) -> ClassifiedAction:
    """
    Semantic classifier fallback for complex natural phrasing.
    Uses OpenAI (gpt-4o-mini) when available, grounding decisions with dialogue history.
    """
    incident_id = (
        extract_incident_ref(query)
        or (context.get("incident_id") if context else None)
        or (getattr(session, "active_incident_id", None) if session else None)
    )

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Offline fallback: if incident active, explain incident; otherwise general converse
        return _deterministic_fallback(query, incident_id, session)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        recent_turns_text = ""
        if session and hasattr(session, "get_recent_turns"):
            recent_turns = session.get_recent_turns(3)
            if recent_turns:
                turns_lines = [f"User: {t.user_query}\nMark: {t.assistant_reply[:120]}..." for t in recent_turns]
                recent_turns_text = "Recent Dialogue:\n" + "\n".join(turns_lines)

        prompt = (
            "You are the intent router for MARK, a telecom incident operations assistant.\n"
            f"Active Incident: {incident_id or 'None'}\n"
            f"{recent_turns_text}\n\n"
            f"User Query: \"{query}\"\n\n"
            "Classify this query into one of these actions:\n"
            "- telecom_brain.explain_incident (incident overview, story, timeline, evidence, technical details)\n"
            "- telecom_brain.diagnose_rca (root cause, failure analysis, hypotheses)\n"
            "- telecom_brain.inspect_runbook (fixes, remediation, scaling, mitigation)\n"
            "- telecom_brain.inspect_topology (blast radius, impacted components, subscribers)\n"
            "- telecom_brain.check_service_intents (3GPP SLAs like ue_registration, data_session, sgi_throughput)\n"
            "- collaboration.draft_communication (draft emails, updates, whatsapp)\n"
            "- assistant.converse (general casual chat, pleasantry)\n\n"
            "Return JSON format:\n"
            "{\"action\": \"<action_name>\", \"intent\": \"<story|technical|evidence|remediation|timeline|impact|none>\", \"reason\": \"<brief_explanation>\"}"
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=150,
            timeout=2.0,
        )

        import json
        raw = response.choices[0].message.content or "{}"
        parsed = json.loads(raw)
        action_str = parsed.get("action", UserAction.CONVERSE.value)
        target_intent = parsed.get("intent")
        reason = parsed.get("reason", "Semantic classification")

        try:
            action = UserAction(action_str)
        except ValueError:
            action = UserAction.CONVERSE

        engine_id = action.value.split(".")[0]
        return ClassifiedAction(
            action=action,
            confidence=0.88,
            engine_id=engine_id,
            extracted_incident_id=incident_id,
            target_intent=target_intent if target_intent != "none" else None,
            reason=f"Semantic fallback: {reason}",
        )

    except Exception as exc:
        logger.debug("[ActionClassifier] Semantic fallback skipped: %s", exc)
        return _deterministic_fallback(query, incident_id, session)


_OPERATIONAL_KEYWORDS = (
    "5g", "5gc", "4g", "lte", "volte", "ims", "ran", "core", "telecom", "network",
    "incident", "alarm", "alert", "kpi", "telemetry", "topology", "gbrain", "grafana",
    "fcaps", "rca", "root cause", "blast radius", "runbook", "playbook", "amf", "smf",
    "upf", "mme", "hss", "outage", "degradation", "latency", "throughput", "packet",
    "failure", "subscriber", "ue", "pdu", "attach", "registration", "status", "health",
)


def _deterministic_fallback(query: str, incident_id: str | None, session: Any | None) -> ClassifiedAction:
    """Graceful deterministic default when semantic fallback is offline."""
    clean_q = query.strip().lower()
    has_op_context = any(k in clean_q for k in _OPERATIONAL_KEYWORDS)
    if incident_id and has_op_context:
        return ClassifiedAction(
            action=UserAction.EXPLAIN_INCIDENT,
            confidence=0.75,
            engine_id="telecom_brain",
            extracted_incident_id=incident_id,
            reason="Active incident context preserved for operational inquiry",
        )
    return ClassifiedAction(
        action=UserAction.CONVERSE,
        confidence=0.50,
        engine_id="assistant",
        reason="Default conversational turn",
    )


# =====================================================================
# COORDINATOR: TWO-PASS CLASSIFIER ENTRYPOINT
# =====================================================================

def classify_action(
    query: str,
    context: dict[str, Any] | None = None,
    session: Any | None = None,
) -> ClassifiedAction:
    """
    Two-Pass Hybrid Classifier:
    1. Runs sub-millisecond fast-path rule matcher (<0.5ms).
    2. If matched with confidence >= 0.85, returns immediately (voice speed).
    3. Otherwise, invokes semantic fallback with session context.
    """
    fast_match = _fast_path_classify(query, context, session)
    if fast_match and fast_match.confidence >= 0.85:
        return fast_match

    # Pass 2: Semantic fallback
    return _semantic_fallback_classify(query, context, session)
