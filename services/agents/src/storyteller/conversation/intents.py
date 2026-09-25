"""Intent definitions, keyword classification, and deterministic renderers.

Phase 3A: the conversational storyteller answers are *deterministic* — every
intent renderer produces text from the structured ``IncidentStory`` (the source
of truth). An LLM may optionally synthesize prose (see ``llm.py``), but the
structured story is never replaced by model output.
"""

from __future__ import annotations

import re
from typing import Callable

from ..reasoning.story import IncidentStory

# Supported intents (the agreed Phase 3A vocabulary).
INTENTS = (
    "story",
    "short",
    "technical",
    "executive",
    "root_cause",
    "evidence",
    "timeline",
    "remediation",
    "recovery",
    "similar",
    "impact",
    "why",
    "noc_brief",
    "rca_lead_brief",
    "customer_update",
    "post_incident_review",
)

# Deterministic keyword classifier. Order matters: most specific intents first,
# ``story`` is the catch-all default.
_KEYWORDS: dict[str, tuple[str, ...]] = {
    "root_cause": ("root cause", "root-cause", "what caused it"),
    "why": ("why", "reason for", "explain"),
    "evidence": ("evidence", "proof", "supporting data", "what supports", "what evidence", "supporting proof"),
    "timeline": ("timeline", "sequence", "chronolog", "when did", "order of events", "timeline of events", "when did it start"),
    "remediation": ("remediation", "fix", "mitigation", "what was done", "action taken", "how did we fix", "what was the fix"),
    "recovery": ("recovery", "recovered", "restored", "back up", "resolved"),
    "similar": ("similar", "related incident", "repeat", "previous incident", "recurrence"),
    "impact": ("impact", "affected", "who was hit", "blast radius", "downtime", "who is impacted", "who was impacted"),
    "technical": ("technical", "details", "detail", "deep dive", "packet", "kpi", "signal", "elaborate", "tell me more", "go deeper", "insights"),
    "executive": ("executive", "stakeholder", "board", "business impact", "executive brief", "executive summary"),
    "noc_brief": ("noc", "noc engineer", "engineer brief", "operations brief", "shift handover"),
    "rca_lead_brief": ("rca lead", "rca owner", "root cause lead", "investigation lead"),
    "customer_update": ("customer update", "stakeholder update", "external update", "customer message"),
    "post_incident_review": ("post incident", "post-incident", "pir", "postmortem", "review report"),
    "short": ("short", "tl;dr", "tl;dr", "summary", "one line", "concise"),
}


_SLUG_STRIP_RE = re.compile(
    r"(?:incidents/[A-Za-z0-9_-]+|[A-Za-z0-9_-]+/incidents)/[A-Za-z0-9._\-]+|\b(?:SCN|DEMO|INC|TWIN|H[1-4])[-_]\d+\b",
    re.IGNORECASE,
)


def classify_intent(message: str) -> str:
    """Determine the intent from free text. ``story`` is the default."""
    cleaned = _SLUG_STRIP_RE.sub("", message)
    lowered = cleaned.lower()

    # If the user specifically requested the overall incident story, prioritize "story"
    # unless an audience-specific qualifier like executive/technical/noc was explicitly requested.
    if re.search(r"\b(?:incident\s+story|tell\s+(?:the\s+)?story|full\s+story|story)\b", lowered):
        for spec_intent in ("executive", "noc_brief", "rca_lead_brief", "technical", "short"):
            if any(re.search(rf"\b{re.escape(kw)}\b", lowered) for kw in _KEYWORDS[spec_intent]):
                return spec_intent
        return "story"

    for intent, keywords in _KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(kw)}\b", lowered) for kw in keywords):
            return intent
    return "story"


# ---------------------------------------------------------------------------
# Deterministic renderers — every one reads only from the IncidentStory.
# ---------------------------------------------------------------------------
def _fmt_fact(value, fallback: str = "not recorded") -> str:
    return str(value) if value not in (None, "") else fallback


def _correlation_line(story: IncidentStory) -> str | None:
    meta = story.correlation_metadata or {}
    if not meta:
        return None
    scope = meta.get("correlation_scope", "unclassified")
    domains = meta.get("contributing_domains") or []
    score = meta.get("correlation_score")
    intent_status = meta.get("intent_status")
    pieces = [str(scope)]
    if domains:
        pieces.append("domains: " + ", ".join(str(domain) for domain in domains))
    if score is not None:
        pieces.append(f"score: {score}")
    if intent_status:
        pieces.append(f"intent: {intent_status}")
    return "; ".join(pieces)


def _hypothesis_evidence(story: IncidentStory, limit: int = 5) -> list[str]:
    evidence: list[str] = []
    for h in story.hypotheses:
        for item in h.evidence:
            evidence.append(_fmt_fact(item.value))
            if len(evidence) >= limit:
                return evidence
    return evidence


def _timeline_value(value) -> str:
    text = _fmt_fact(value)
    return text[2:].strip() if text.startswith("- ") else text


def _clean_timeline(raw_timeline: list) -> list[str]:
    """Filter out bare timestamps and remove empty or duplicate lines."""
    cleaned = []
    seen = set()
    for t in raw_timeline:
        val = _timeline_value(t.value if hasattr(t, "value") else t).strip()
        # Drop bare ISO timestamps with no explanatory text
        if re.match(r"^\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(\.\d+)?Z?$", val):
            continue
        if not val or val in seen:
            continue
        seen.add(val)
        cleaned.append(val)
    return cleaned


def _friendly_incident_title(story: IncidentStory) -> str:
    """Derive a human-friendly, professional incident name without raw slugs, IDs, or file paths."""
    service = _spoken_service(story) if hasattr(story, "services") else ""
    raw_id = (story.incident_id or "").split("/")[-1]
    clean_slug = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", raw_id)
    clean_slug = re.sub(r"-[0-9a-f]{8,}$", "", clean_slug)
    words = [
        w.capitalize() if w.lower() not in ("and", "of", "the", "in", "to", "for", "on", "across") else w.lower()
        for w in clean_slug.replace("-", " ").replace("_", " ").split()
    ]
    slug_title = " ".join(words)
    acronyms = {"Amf": "AMF", "Smf": "SMF", "Upf": "UPF", "Ran": "RAN", "Ue": "UE", "Kpi": "KPI", "Rca": "RCA"}
    for k, v in acronyms.items():
        slug_title = re.sub(rf"\b{k}\b", v, slug_title)

    if slug_title and len(slug_title) > 3:
        return slug_title
    if service and service != "the affected service":
        return f"{service} Degradation"
    return "Telecom Incident"


def render_story(story: IncidentStory) -> str:
    friendly_title = _friendly_incident_title(story)
    status_str = (story.status or "unknown").upper()
    sev_str = (story.severity or "unknown").upper()

    lines = [
        f"# Incident story — {friendly_title}",
        f"> 🏷️ **Incident ID:** `{story.incident_id}` &nbsp;|&nbsp; ⚡ **Status:** `{status_str}` &nbsp;|&nbsp; 🔴 **Severity:** `{sev_str}`",
        "",
        "### 📋 Executive Summary",
        story.summary or "No summary available.",
    ]
    if story.services or story.network_functions:
        lines += ["", "### 🌐 Impacted Topology & Blast Radius", "**Impact:**"]
        for svc in story.services:
            lines.append(f"- **Service:** {_fmt_fact(svc.value)}")
        for nf in story.network_functions:
            nf_val = _fmt_fact(nf.value)
            nf_slug = getattr(nf, "slug", "") or ""
            slug_name = nf_slug.split("/")[-1].upper() if "/" in nf_slug else nf_slug.upper()
            if slug_name and slug_name.lower() not in nf_val.lower():
                lines.append(f"- **Component:** `{slug_name}` — {nf_val}")
            else:
                lines.append(f"- **Component:** {nf_val}")
    if story.root_cause:
        lines += ["", "### 🔍 Root Cause Analysis (RCA)", f"**Confirmed root cause:** {story.root_cause.value}"]
    elif story.hypotheses:
        top = story.hypotheses[0]
        lines += ["", "### 🔍 Root Cause Analysis (RCA)", f"**Leading hypothesis:** {top.hypothesis.value} (status: {top.status})"]
    correlation = _correlation_line(story)
    if correlation:
        lines += ["", f"**Correlation:** {correlation}"]
        reasons = story.correlation_metadata.get("correlation_reasons") or []
        if reasons:
            lines += ["", "**Why these alarms were grouped:**"]
            lines += [f"- {reason}" for reason in reasons]
    if story.causal_chain and story.causal_chain.steps:
        lines += ["", "### ⛓️ Causal Chain", "**Causal chain:**"]
        for step in story.causal_chain.steps:
            fact_desc = f" ──► {step.fact.value}" if step.fact and step.fact.value else ""
            lines.append(f"- **{step.label}**{fact_desc} *({step.claim_type})*")
    evidence = _hypothesis_evidence(story)
    if evidence:
        lines += ["", "### 📊 Correlated Evidence", "**Supporting evidence:**"]
        lines += [f"- {item}" for item in evidence]
    if story.timeline:
        clean_tl = _clean_timeline(story.timeline)
        if clean_tl:
            lines += ["", "### ⏱️ Timeline & Chronology", "**Timeline:**"]
            for item in clean_tl:
                lines.append(f"- {item}")
    if story.remediations:
        lines += ["", "### 🛠️ Remediation & Actions", "**Remediation:**"] + [f"- {_fmt_fact(r.value)}" for r in story.remediations]
    if story.recovery_events:
        lines += ["", "### 🔄 Recovery Verification", "**Recovery:**"] + [f"- {_fmt_fact(r.value)}" for r in story.recovery_events]
    if story.unresolved_questions:
        lines += ["", "### ❓ Open Inquiries", "**Still open:**"] + [f"- {q}" for q in story.unresolved_questions]
    return "\n".join(lines)


def render_short(story: IncidentStory) -> str:
    return (
        f"{story.status or 'status unknown'} / {story.severity or 'severity unknown'} — "
        f"{story.summary or 'no summary'}"
    )


def render_technical(story: IncidentStory) -> str:
    lines = [f"# Technical brief — {story.incident_id}", ""]
    lines.append("## KPIs")
    for kpi in story.kpis:
        lines.append(f"- {_fmt_fact(kpi.value)} (slug: {_fmt_fact(kpi.slug)})")
    for ev in story.kpi_events:
        extra = f", extra={ev.extra}" if ev.extra else ""
        lines.append(f"- event: {_fmt_fact(ev.value)}{extra}")
    lines.append("")
    lines.append("## Causal chain (claim classification)")
    if story.causal_chain:
        for step in story.causal_chain.steps:
            lines.append(f"- {step.label} [{step.claim_type}]: {step.fact.value if step.fact else ''}")
    else:
        lines.append("- none reconstructed")
    lines.append("")
    lines.append("## Hypotheses")
    for h in story.hypotheses:
        lines.append(f"- {h.hypothesis.value} ({h.status}, score={h.score:.2f})")
        for e in h.evidence:
            lines.append(f"    - evidence: {_fmt_fact(e.value)} (conf={_fmt_fact(e.confidence)})")
    lines.append("")
    lines.append("## Involved components")
    for nf in story.network_functions:
        lines.append(f"- {_fmt_fact(nf.value)}")
    return "\n".join(lines)


def render_executive(story: IncidentStory) -> str:
    lines = [
        f"# Executive summary — {story.incident_id}",
        f"**Status:** {story.status or 'unknown'}  **Severity:** {story.severity or 'unknown'}",
        "",
        story.summary or "No summary available.",
    ]
    if story.root_cause:
        lines.append(f"**Root cause (confirmed):** {story.root_cause.value}")
    elif story.hypotheses:
        lines.append(f"**Root cause:** not yet confirmed; leading hypothesis is '{story.hypotheses[0].hypothesis.value}'")
    correlation = _correlation_line(story)
    if correlation:
        lines.append(f"**Correlation:** {correlation}")
    if story.impact:
        lines.append("**Impacted:** " + ", ".join(_fmt_fact(f.value) for f in story.impact))
    evidence = _hypothesis_evidence(story, limit=3)
    if evidence:
        lines.append("**Evidence:** " + "; ".join(evidence))
    if story.remediations:
        lines.append("**Actions taken:** " + "; ".join(_fmt_fact(r.value) for r in story.remediations))
    elif story.unresolved_questions:
        lines.append("**Open items:** " + "; ".join(story.unresolved_questions[:3]))
    return "\n".join(lines)


def render_root_cause(story: IncidentStory) -> str:
    if story.root_cause:
        return (
            f"**Confirmed root cause:** {story.root_cause.value}\n"
            f"Confidence: {_fmt_fact(story.root_cause.confidence)}  Source: {_fmt_fact(story.root_cause.source)}"
        )
    if story.hypotheses:
        top = story.hypotheses[0]
        return (
            f"**Root cause is not confirmed.** Leading hypothesis: '{top.hypothesis.value}' "
            f"(status: {top.status}). Evidence so far:\n"
            + "\n".join(f"- {_fmt_fact(e.value)}" for e in top.evidence)
        )
    return "**No hypothesis recorded** for this incident; root cause cannot be determined."


def render_evidence(story: IncidentStory) -> str:
    if not story.hypotheses:
        return "**No evidence recorded** for this incident."
    lines = []
    for h in story.hypotheses:
        lines.append(f"### Hypothesis: {h.hypothesis.value} ({h.status})")
        if h.evidence:
            for e in h.evidence:
                lines.append(f"- {_fmt_fact(e.value)}")
                lines.append(f"    - source: {_fmt_fact(e.source)} | relationship: {_fmt_fact(e.relationship)} | conf: {_fmt_fact(e.confidence)}")
        else:
            lines.append("- no supporting evidence recorded")
    return "\n".join(lines)


def render_timeline(story: IncidentStory) -> str:
    if not story.timeline:
        return "**No timeline recorded** for this incident."
    return "\n".join(f"- {_timeline_value(t.value)}" for t in story.timeline)


def render_remediation(story: IncidentStory) -> str:
    if not story.remediations:
        return "**No remediation recorded** for this incident."
    return "\n".join(f"- {_fmt_fact(r.value)}" for r in story.remediations)


def render_recovery(story: IncidentStory) -> str:
    if not story.recovery_events:
        return "**No recovery events recorded** for this incident."
    return "\n".join(f"- {_fmt_fact(r.value)}" for r in story.recovery_events)


def render_similar(story: IncidentStory) -> str:
    if not story.similar_incidents:
        return "**No similar incidents found** for this incident."
    return "\n".join(f"- {_fmt_fact(s.value)}" for s in story.similar_incidents)


def render_impact(story: IncidentStory) -> str:
    if not story.impact:
        return "**No impacted services or network functions recorded.**"
    return "\n".join(f"- {_fmt_fact(f.value)} ({_fmt_fact(f.relationship)})" for f in story.impact)


def render_why(story: IncidentStory) -> str:
    lines = []
    if story.causal_chain:
        lines.append("**Why it happened (reconstructed causal chain):**")
        for step in story.causal_chain.steps:
            lines.append(f"- {step.label} [{step.claim_type}]: {step.fact.value if step.fact else ''}")
    if story.root_cause:
        lines.append(f"**Confirmed root cause:** {story.root_cause.value}")
    elif story.hypotheses:
        top = story.hypotheses[0]
        lines.append(f"**Root cause not confirmed** — leading hypothesis: '{top.hypothesis.value}'")
    if story.unresolved_questions:
        lines.append("**Unresolved questions:**")
        lines += [f"- {q}" for q in story.unresolved_questions]
    if not lines:
        return "**No causal information recorded** for this incident."
    return "\n".join(lines)


def render_noc_brief(story: IncidentStory) -> str:
    lines = [
        f"# NOC engineer brief — {story.incident_id}",
        f"**Lifecycle:** {story.status or 'unknown'}  **Severity:** {story.severity or 'unknown'}",
        "",
        "**Operational summary:**",
        story.summary or "No confirmed operational summary is available.",
        "",
        "**Affected services/components:**",
    ]
    if story.impact:
        lines += [f"- {_fmt_fact(item.value)} ({_fmt_fact(item.relationship)})" for item in story.impact]
    else:
        lines.append("- no affected service or component recorded")
    lines += ["", "**Evidence to check:**"]
    evidence = _hypothesis_evidence(story, limit=8)
    lines += [f"- {item}" for item in evidence] if evidence else ["- no supporting evidence recorded"]
    lines += ["", "**Immediate actions:**"]
    if story.remediations:
        lines += [f"- verify remediation: {_fmt_fact(item.value)}" for item in story.remediations]
    else:
        lines.append("- confirm alarm/KPI state, collect missing logs, and record mitigation before closure")
    return "\n".join(lines)


def render_rca_lead_brief(story: IncidentStory) -> str:
    lines = [
        f"# RCA lead brief — {story.incident_id}",
        f"**Status:** {story.status or 'unknown'}  **Severity:** {story.severity or 'unknown'}",
        "",
        "**Hypotheses:**",
    ]
    if story.hypotheses:
        for item in story.hypotheses:
            lines.append(f"- {item.hypothesis.value} ({item.status}, score={item.score:.2f})")
            for evidence in item.evidence:
                lines.append(f"  - evidence: {_fmt_fact(evidence.value)}")
    else:
        lines.append("- no hypothesis recorded")
    lines += ["", "**Contradictions / gaps:**"]
    gaps = story.unresolved_questions or ["no unresolved questions recorded"]
    lines += [f"- {gap}" for gap in gaps]
    return "\n".join(lines)


def render_customer_update(story: IncidentStory) -> str:
    service = story.services[0].value if story.services else "the affected service"
    status = story.status or "under investigation"
    severity = story.severity or "severity under assessment"
    recovery = "Service recovery has been observed." if story.recovery_events else "Recovery is still being verified."
    return "\n".join(
        [
            "# Customer update",
            "",
            f"We are managing a {severity} incident affecting {service}. Current state: {status}.",
            recovery,
            "Engineering teams are validating impact, cause, and next actions. We will provide a further update when recovery and root cause are confirmed.",
        ]
    )


def render_post_incident_review(story: IncidentStory) -> str:
    lines = [
        f"# Post-incident review — {story.incident_id}",
        "",
        f"**Summary:** {story.summary or 'No summary available.'}",
        f"**Lifecycle outcome:** {story.status or 'unknown'}",
        f"**Severity:** {story.severity or 'unknown'}",
        "",
        "**Root cause:**",
        story.root_cause.value if story.root_cause else "Not confirmed in available evidence.",
        "",
        "**Timeline:**",
    ]
    lines += [f"- {_timeline_value(item.value)}" for item in story.timeline] if story.timeline else ["- no timeline recorded"]
    lines += ["", "**Corrective / preventive actions:**"]
    lines += [f"- {_fmt_fact(item.value)}" for item in story.remediations] if story.remediations else ["- define corrective actions after RCA confirmation"]
    lines += ["", "**Learning gaps:**"]
    lines += [f"- {item}" for item in (story.unresolved_questions or ["no learning gaps recorded"])]
    return "\n".join(lines)


_RENDERERS: dict[str, Callable[[IncidentStory], str]] = {
    "story": render_story,
    "short": render_short,
    "technical": render_technical,
    "executive": render_executive,
    "root_cause": render_root_cause,
    "evidence": render_evidence,
    "timeline": render_timeline,
    "remediation": render_remediation,
    "recovery": render_recovery,
    "similar": render_similar,
    "impact": render_impact,
    "why": render_why,
    "noc_brief": render_noc_brief,
    "rca_lead_brief": render_rca_lead_brief,
    "customer_update": render_customer_update,
    "post_incident_review": render_post_incident_review,
}


def render_answer(intent: str, story: IncidentStory) -> str:
    """Deterministically render the answer for an intent from the story."""
    renderer = _RENDERERS.get(intent)
    if renderer is None:
        return f"Unknown intent '{intent}'."
    return renderer(story)


def curate_spoken_text(text: str) -> str:
    """Transform long or technical answers into concise, high-value spoken summaries.

    Strips timestamps, markdown tables, raw bullet lists, and technical syntax,
    curating a natural conversational takeaway suitable for audio TTS without micro-reading.
    """
    if not text or not text.strip():
        return ""

    # 1. Remove markdown code blocks (```...```)
    t = re.sub(r"```[\s\S]*?```", "", text)
    # 2. Remove markdown tables (|...|)
    t = re.sub(r"\|[^\n]+\|\n?", "", t)
    # 3. Remove markdown headers, list bullets, and quote prefixes
    t = re.sub(r"^#{1,6}\s+.*$", "", t, flags=re.MULTILINE)
    t = re.sub(r"^[*-]\s+", "", t, flags=re.MULTILINE)
    t = re.sub(r"^\d+\.\s+", "", t, flags=re.MULTILINE)
    t = re.sub(r"^>\s+", "", t, flags=re.MULTILINE)
    # 4. Remove ISO and clock timestamps (e.g. 2026-09-02T14:22:01.000Z, 14:22:01)
    t = re.sub(r"\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(\.\d+)?Z?\b", "", t)
    t = re.sub(r"\b\d{1,2}:\d{2}(:\d{2})?\s*(AM|PM|am|pm|UTC|GMT|Z)?\b", "", t)
    # 5. Remove markdown bold/italic formatting (**word**, *word*, `code`)
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"\*([^*]+)\*", r"\1", t)
    t = re.sub(r"__([^_]+)__", r"\1", t)
    t = re.sub(r"`([^`]+)`", r"\1", t)
    # 6. Remove raw incident slugs, docs paths, and hash symbols
    t = re.sub(r"\b(?:observations/|knowledge/|incidents/|mobile-core/incidents/)[\w/.-]+", "", t)
    t = re.sub(r"\bFrom\s+docs/[^\s:]+(?:\s*/\s*[^:]+)?:\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\bFrom\s+`?[^`:\n]+`?(?:\s*/\s*[^:]+)?:\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(Status|Severity|Correlation|KPIs|Hypotheses|Causal chain|Timeline|Remediation|Recovery):\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"#([a-zA-Z0-9]+)", r"\1", t)

    # 7. Normalize whitespace
    t = re.sub(r"\s+", " ", t).strip()

    # Extract clean sentences (max ~120 words and up to 6 sentences to preserve full storytelling arc)
    sentences = re.split(r"(?<=[.!?])\s+", t)
    selected: list[str] = []
    word_count = 0
    for s in sentences:
        s_clean = s.strip()
        if not s_clean:
            continue
        words = s_clean.split()
        if word_count + len(words) > 120 and selected:
            break
        selected.append(s_clean)
        word_count += len(words)
        if len(selected) >= 6:
            break

    spoken = " ".join(selected).strip()
    return spoken or t[:250]


def _spoken_fact(value, fallback: str = "") -> str:
    """Clean one structured fact for speech without markdown or raw slugs."""
    text = _fmt_fact(value, fallback=fallback).strip()
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"[*_#~>\[\]{}|]", " ", text)
    text = re.sub(r"\b(?:slug|id|incident id)\s*:\s*[\w/.-]+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:observations/|knowledge/|mobile-core/incidents/)[\w/.-]+", "", text)
    text = re.sub(r"\s+", " ", text).strip(" ,.;:-")
    return text or fallback


def _spoken_service(story: IncidentStory) -> str:
    if story.services:
        return _spoken_fact(story.services[0].value, "the affected service")
    summary = story.summary or ""
    match = re.search(r"impacting\s+(.+?)\s+across\b", summary, flags=re.IGNORECASE)
    if match:
        return _spoken_fact(match.group(1), "the affected service")
    return "the affected service"


def _spoken_severity(value: str) -> str:
    text = _spoken_fact(value)
    match = re.fullmatch(r"sev[-_\s]?(\d+)", text, flags=re.IGNORECASE)
    if match:
        return f"severity {match.group(1)}"
    return text


def _spoken_components(story: IncidentStory, *, limit: int = 3) -> list[str]:
    components: list[str] = []
    for nf in story.network_functions[:limit]:
        text = _spoken_fact(nf.value)
        if text:
            components.append(text)
    return components


def _spoken_domains(story: IncidentStory) -> str:
    meta = story.correlation_metadata or {}
    domains = meta.get("contributing_domains") or []
    if not domains:
        return ""
    clean = [_spoken_fact(domain) for domain in domains if _spoken_fact(domain)]
    if not clean:
        return ""
    if len(clean) == 1:
        return clean[0]
    return ", ".join(clean[:-1]) + f", and {clean[-1]}"


def _spoken_hypothesis(story: IncidentStory) -> str:
    if story.root_cause:
        return f"The confirmed root cause is {_spoken_fact(story.root_cause.value)}."
    if story.hypotheses:
        return f"The leading hypothesis is {_spoken_fact(story.hypotheses[0].hypothesis.value)}."
    return "The root cause is still under investigation."


def _spoken_open_items(story: IncidentStory) -> str:
    if story.recovery_events and story.remediations:
        return "Recovery and remediation are recorded."
    open_items: list[str] = []
    if not story.root_cause:
        open_items.append("root cause confirmation")
    if not story.remediations:
        open_items.append("remediation")
    if not story.recovery_events:
        open_items.append("recovery")
    if not open_items:
        return ""
    if len(open_items) == 1:
        return f"Still open: {open_items[0]}."
    return "Still open: " + ", ".join(open_items[:-1]) + f", and {open_items[-1]}."


def _spoken_incident_story(story: IncidentStory) -> str:
    """Compose a cohesive, executive-grade spoken story covering the full narrative arc:
    Context / Trigger -> Root Cause -> Blast Radius -> Remediation / Posture.
    Avoids reading raw IDs, log timestamps, or micro-level bullet syntax.
    """
    title = _friendly_incident_title(story)
    service = _spoken_service(story)
    status = _spoken_fact(story.status, "active")
    severity = _spoken_severity(_spoken_fact(story.severity))

    parts: list[str] = []
    # 1. Narrative Hook / Setup
    if severity:
        parts.append(f"Here is the story for {title}, currently tracked as a {severity} {status} incident.")
    else:
        parts.append(f"Here is the story for {title}, currently in {status} state.")

    # 2. Root Cause / Primary Mechanism
    if story.root_cause:
        rc = _spoken_fact(story.root_cause.value)
        parts.append(f"The investigation confirmed root cause is {rc}.")
    elif story.hypotheses:
        lead = _spoken_fact(story.hypotheses[0].hypothesis.value)
        parts.append(f"The leading cause identified is {lead}.")
    elif story.causal_chain and story.causal_chain.steps:
        first_step = _spoken_fact(story.causal_chain.steps[0].label)
        parts.append(f"The failure chain was initiated by {first_step}.")
    else:
        parts.append("Teams are actively isolating the primary failure mechanism.")

    # 3. Topology & Blast Radius
    domains = _spoken_domains(story)
    components = _spoken_components(story, limit=3)
    if domains and components:
        comp_str = ", ".join(components)
        parts.append(f"The blast radius spans {domains}, directly impacting {comp_str} and degrading {service}.")
    elif components:
        comp_str = ", ".join(components)
        parts.append(f"Impact is focused on {comp_str}, affecting {service}.")
    elif domains:
        parts.append(f"The correlation extends across {domains}, with {service} experiencing degradation.")
    elif service and service != "the affected service":
        parts.append(f"Operational impact is concentrated on {service}.")

    # 4. Remediation & Current Posture
    if story.remediations:
        rem = _spoken_fact(story.remediations[0].value)
        parts.append(f"Mitigation is underway with {rem}.")
    elif story.recovery_events:
        rec = _spoken_fact(story.recovery_events[0].value)
        parts.append(f"Service recovery has been verified through {rec}.")
    else:
        parts.append("Engineers are executing standard recovery playbooks to restore full stability.")

    return curate_spoken_text(" ".join(parts))


def render_spoken_answer(intent: str, story: IncidentStory) -> str:
    """Render a professional spoken briefing from structured story context."""
    service = _spoken_service(story)

    if intent == "executive":
        severity = _spoken_severity(_spoken_fact(story.severity))
        status = _spoken_fact(story.status, "active")
        hypo = _spoken_hypothesis(story)
        if not story.root_cause:
            open_items = f" {_spoken_open_items(story)}"
            return f"{service} is currently {severity} {status}. {hypo}{open_items}".strip()
        return f"{service} is currently {severity} {status}. {hypo}".strip()

    if intent in ("root_cause", "why"):
        return f"For {service}, {_spoken_hypothesis(story)} {_spoken_open_items(story)}".strip()

    if intent == "technical":
        components = _spoken_components(story, limit=2)
        target = ", ".join(components) if components else "the involved network components"
        return f"Technical analysis points to {target}. I have placed the detailed KPIs and causal chain in the chat."

    if intent == "timeline":
        count = len(story.timeline) if story.timeline else 0
        if count > 0:
            noun = "event" if count == 1 else "events"
            return f"I found {count} timeline {noun} for {service}. The detailed chronology is in the chat."
        return f"No timeline events are recorded yet for {service}."

    if intent == "evidence":
        if story.hypotheses and story.hypotheses[0].evidence:
            evidence = _spoken_fact(story.hypotheses[0].evidence[0].value)
            return f"The strongest evidence is: {evidence}. I have listed the full evidence set in the chat."
        return f"No supporting evidence is recorded yet for {service}."

    if intent in ("remediation", "recovery"):
        if story.remediations:
            return f"The next recorded remediation is {_spoken_fact(story.remediations[0].value)}. The action list is in the chat."
        return f"No remediation action is recorded yet for {service}."

    if intent == "impact":
        if story.impact:
            return f"Impact is observed on {_spoken_fact(story.impact[0].value)}. The detailed blast radius is in the chat."
        return f"No impact data is recorded yet for {service}."

    # General story / executive / short / narrative intents
    return _spoken_incident_story(story)
