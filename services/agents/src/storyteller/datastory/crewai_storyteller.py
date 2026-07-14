"""NOC Storyteller — single CrewAI agent with tools for narration, plus
deterministic utility functions for cluster extraction and sync."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

import logging
import yaml
import pandas as pd

from agenticaiops_shared.config import settings

logger = logging.getLogger(__name__)

_HERE = Path(__file__).resolve().parent
_DATA = _HERE / "data"
_STORIES_PATH = _DATA / "stories.yaml"
_KG_STATE_PATH = _DATA / "knowledge_graph_state.yaml"
_DEFAULT_CACHE = _DATA / "semantic_state.parquet"

# ---------------------------------------------------------------------------
# YAML helpers
# ---------------------------------------------------------------------------
_STORIES: dict | None = None
_KG_STATE: dict | None = None


def _load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def _get_stories() -> dict:
    global _STORIES
    if _STORIES is None:
        _STORIES = _load_yaml(_STORIES_PATH)
    return _STORIES


def _get_kg_state() -> dict:
    global _KG_STATE
    if _KG_STATE is None:
        _KG_STATE = _load_yaml(_KG_STATE_PATH)
    return _KG_STATE


def _normalize(name: str) -> str:
    return name.strip().lower().replace("-", " ")


def _find_issue_in_stories(name: str) -> dict | None:
    stories = _get_stories()
    categories = stories.get("sop_framework", {}).get("categories", [])

    def _match(q: str) -> dict | None:
        q_norm = _normalize(q)
        for cat in categories:
            for issue in cat.get("issues", []):
                if _normalize(issue.get("name", "")) == q_norm:
                    return {**issue, "category": cat.get("name", "")}
                for sub_name in (issue.get("counts") or {}):
                    if _normalize(sub_name) == q_norm:
                        return {
                            "name": issue["name"],
                            "sub_issue": sub_name,
                            "count": issue["counts"][sub_name],
                            "description": issue.get("description", ""),
                            "custops_check": issue.get("custops_check", ""),
                            "caveats": issue.get("caveats", ""),
                            "tie_breaker": issue.get("tie_breaker", ""),
                            "validation_steps": issue.get("validation_steps", []),
                            "handset_cause": issue.get("handset_cause", ""),
                            "category": cat.get("name", ""),
                        }
        return None

    result = _match(name)
    if result:
        return result

    # LLM often appends "issue" — try stripping trailing "issue"/"issues"
    stripped = re.sub(r"\s+issues?$", "", name.strip(), flags=re.IGNORECASE)
    if stripped != name:
        result = _match(stripped)
        if result:
            return result

    # Substring fallback — score candidates by keyword-hit count, return best
    _STOPWORDS = {"the", "a", "an", "and", "or", "of", "for", "to", "in", "is", "not", "with", "on"}
    q_norm = _normalize(name)
    keywords = [w for w in q_norm.split() if w not in _STOPWORDS and len(w) > 2]
    if keywords:
        best: tuple[int, dict | None] = (0, None)
        for cat in categories:
            for issue in cat.get("issues", []):
                issue_norm = _normalize(issue.get("name", ""))
                score = sum(1 for kw in keywords if kw in issue_norm)
                if score > best[0]:
                    best = (score, {**issue, "category": cat.get("name", "")})
                for sub_name in (issue.get("counts") or {}):
                    sub_norm = _normalize(sub_name)
                    score = sum(1 for kw in keywords if kw in sub_norm)
                    if score > best[0]:
                        best = (score, {
                            "name": issue["name"],
                            "sub_issue": sub_name,
                            "count": issue["counts"][sub_name],
                            "description": issue.get("description", ""),
                            "custops_check": issue.get("custops_check", ""),
                            "caveats": issue.get("caveats", ""),
                            "tie_breaker": issue.get("tie_breaker", ""),
                            "validation_steps": issue.get("validation_steps", []),
                            "handset_cause": issue.get("handset_cause", ""),
                            "category": cat.get("name", ""),
                        })
        if best[1]:
            return best[1]

    return None


def _find_reassignment_reason(name: str) -> dict | None:
    kg = _get_kg_state()
    for col in kg.get("columns", []):
        if col.get("field") == "reassignment_reason":
            for val in col.get("values", []):
                if _normalize(val.get("value", "")) == _normalize(name):
                    return val
    # Retry with trailing "issue"/"issues" stripped
    stripped = re.sub(r"\s+issues?$", "", name.strip(), flags=re.IGNORECASE)
    if stripped != name:
        for col in kg.get("columns", []):
            if col.get("field") == "reassignment_reason":
                for val in col.get("values", []):
                    if _normalize(val.get("value", "")) == _normalize(stripped):
                        return val
    # Substring fallback — score by keyword-hit count, return best
    _STOPWORDS = {"the", "a", "an", "and", "or", "of", "for", "to", "in", "is", "not", "with", "on"}
    q_norm = _normalize(name)
    keywords = [w for w in q_norm.split() if w not in _STOPWORDS and len(w) > 2]
    if keywords:
        best: tuple[int, dict | None] = (0, None)
        for col in kg.get("columns", []):
            if col.get("field") == "reassignment_reason":
                for val in col.get("values", []):
                    val_norm = _normalize(val.get("value", ""))
                    score = sum(1 for kw in keywords if kw in val_norm)
                    if score > best[0]:
                        best = (score, val)
        if best[1]:
            return best[1]
    return None


def _get_edges_for_reason(name: str) -> list[dict]:
    kg = _get_kg_state()
    edges = kg.get("edges", [])
    result = []
    for edge in edges:
        if edge.get("source_col") == "reassignment_reason" and _normalize(edge.get("source_val", "")) == _normalize(name):
            result.append(edge)
        elif edge.get("target_col") == "reassignment_reason" and _normalize(edge.get("target_val", "")) == _normalize(name):
            result.append(edge)
    return result


# ---------------------------------------------------------------------------
# Tool decorator (compatible fallback when CrewAI absent)
# ---------------------------------------------------------------------------
try:
    from crewai.tools import tool
except ImportError:
    try:
        from langchain.tools import tool
    except ImportError:
        def tool(*args: Any, **kwargs: Any):
            def wrapper(func):
                func.is_tool = True
                return func
            return wrapper


# ---------------------------------------------------------------------------
# CrewAI Tools
# ---------------------------------------------------------------------------

@tool("Lookup Issue")
def lookup_issue(name: str) -> str:
    """Look up a network issue by name. Returns live ticket count from the
    knowledge graph, SOP details from the stories database, and the top
    affected queues.

    Args:
        name: Issue name, e.g. "Device APN issue", "Multi SIM not allowed".

    Returns:
        Structured plain-text payload with count, description, and context.
    """
    issue = _find_issue_in_stories(name)
    reason = _find_reassignment_reason(name)

    lines: list[str] = []
    if issue:
        lines.append(f"Issue: {issue.get('name', name)}")
        if "sub_issue" in issue:
            lines.append(f"  Sub-issue: {issue['sub_issue']} (count: {issue.get('count', '?')})")
        lines.append(f"  Category: {issue.get('category', '?')}")
        lines.append(f"  Description: {issue.get('description', '')}")
        lines.append(f"  CustOps Check: {issue.get('custops_check', '')}")
        lines.append(f"  Caveats: {issue.get('caveats', '')}")
        lines.append(f"  Tie-breaker: {issue.get('tie_breaker', '')}")
        steps = issue.get('validation_steps', [])
        if steps:
            lines.append(f"  Validation steps: {'; '.join(steps)}")
        handset = issue.get('handset_cause', '')
        if handset:
            lines.append(f"  Handset cause: {handset}")
    else:
        lines.append(f"Issue: {name}")

    if reason:
        lines.append(f"Live count: {reason.get('count', '?')}")

    edges = _get_edges_for_reason((reason or {}).get("value", name))
    kg_queues: dict[str, int] = {}
    reassigned_to: list[str] = []
    ticket_statuses: list[str] = []
    for edge in edges:
        if edge.get("source_col") == "ticket_queue":
            kg_queues[edge["source_val"]] = edge["weight"]
        elif edge.get("target_col") == "ticket_queue":
            kg_queues[edge["target_val"]] = edge["weight"]
        elif edge.get("target_col") == "reassigned_to":
            reassigned_to.append(f"{edge['target_val']} ({edge['weight']})")
        elif edge.get("target_col") == "ticket_status":
            ticket_statuses.append(f"{edge['target_val']} ({edge['weight']})")

    if kg_queues:
        sorted_q = sorted(kg_queues.items(), key=lambda x: -x[1])
        lines.append(f"  Ticket queues: {', '.join(f'{q}: {c}' for q, c in sorted_q)}")
    if reassigned_to:
        lines.append(f"  Reassigned to: {', '.join(reassigned_to)}")
    if ticket_statuses:
        lines.append(f"  Status: {', '.join(ticket_statuses)}")

    if not issue and not reason:
        lines.append("No matching issue found.")

    return "\n".join(lines)


@tool("Query Trends")
def query_trends(query: str) -> str:
    """Analyze trends across the knowledge graph — queue volumes,
    top reassignment reasons, issue category distributions, and
    cross-filtered patterns.

    Args:
        query: What to analyze, e.g. "top queues", "top reassignment reasons",
               "issue category breakdown".

    Returns:
        Structured plain-text payload with sorted breakdowns.
    """
    kg = _get_kg_state()
    columns = kg.get("columns", [])
    edges = kg.get("edges", [])
    q_lower = _normalize(query)
    lines: list[str] = []

    if any(kw in q_lower for kw in ("queue", "ticket_queue")):
        for col in columns:
            if col.get("field") == "ticket_queue":
                vals = sorted(col.get("values", []), key=lambda v: -v["count"])
                lines.append("=== Ticket Queue Breakdown ===")
                for v in vals:
                    lines.append(f"  {v['value']}: {v['count']}")

    if any(kw in q_lower for kw in ("reassignment reason", "reassignment_reason", "top issue", "top reason")):
        for col in columns:
            if col.get("field") == "reassignment_reason":
                vals = sorted(col.get("values", []), key=lambda v: -v["count"])
                lines.append("=== Reassignment Reason Breakdown ===")
                for v in vals:
                    lines.append(f"  {v['value']}: {v['count']}")

    if any(kw in q_lower for kw in ("issue category", "issue_category", "category")):
        for col in columns:
            if col.get("field") == "issue_category":
                vals = sorted(col.get("values", []), key=lambda v: -v["count"])
                lines.append("=== Issue Category Breakdown ===")
                for v in vals:
                    lines.append(f"  {v['value']}: {v['count']}")

    if any(kw in q_lower for kw in ("cross", "edge", "connection", "queue.*issue", "issue.*queue")):
        q_to_issue: dict[str, list[tuple[str, int]]] = {}
        for edge in edges:
            if edge.get("source_col") == "ticket_queue" and edge.get("target_col") == "issue_category":
                q_to_issue.setdefault(edge["source_val"], []).append((edge["target_val"], edge["weight"]))
        lines.append("=== Queue × Issue Category (cross-filtered) ===")
        for q, cats in sorted(q_to_issue.items()):
            sorted_cats = sorted(cats, key=lambda x: -x[1])
            lines.append(f"  {q}: {', '.join(f'{c}: {w}' for c, w in sorted_cats[:3])}")

    if not lines:
        lines.append(f"No trend data found for query: {query}")

    return "\n".join(lines)


@tool("Cluster Context")
def extract_cluster_context(cluster_name: str) -> str:
    """Read the semantic Parquet cache and return a curated snapshot of the
    Operational Norm (most representative ticket) and Systemic Friction
    (anomalous or rejected tickets) for a cluster.

    Args:
        cluster_name: Cluster name, e.g. "Device APN issue", "CS - VoLTE".

    Returns:
        Plain-text payload with NORM and FRICTION sections.
    """
    return _extract_cluster_context(cluster_name)


# ---------------------------------------------------------------------------
# Parquet extraction (deterministic, no LLM)
# ---------------------------------------------------------------------------

def _extract_cluster_context(cluster_name: str, cache_path: Path = _DEFAULT_CACHE) -> str:
    if not cache_path.exists():
        return f"[No cache at {cache_path}]"
    df = pd.read_parquet(cache_path)
    cluster_df = df[
        (df["Semantic_Cluster_Theme"] == cluster_name) |
        (df["Issue_Category"] == cluster_name) |
        (df["Reassignment_Reason"] == cluster_name)
    ].copy()
    if cluster_df.empty:
        return f"[No tickets found for cluster '{cluster_name}']"

    norm_idx = cluster_df["Centrality_Score"].idxmax()
    norm_row = cluster_df.loc[norm_idx]
    norm_lines = [
        "=== OPERATIONAL NORM (most representative workflow) ===",
        f"  Queue:          {norm_row.get('Ticket_Queue', 'N/A')}",
        f"  Issue Category: {norm_row.get('Issue_Category', 'N/A')}",
        f"  Status:         {norm_row.get('Ticket_Status', 'N/A')}",
    ]
    rejection = norm_row.get("Rejection_Reason", "")
    if pd.notna(rejection) and str(rejection).strip():
        norm_lines.append(f"  Rejection:      {rejection}")
    desc = norm_row.get("Cleaned_Text", "")
    if pd.notna(desc) and str(desc).strip():
        norm_lines.append(f"  Description:    {desc[:400]}")
    norm_lines.append("")

    friction_mask = (cluster_df["Anomaly_Flag"] == True) | (cluster_df["Ticket_Status"] == "Rejected")
    friction_df = cluster_df[friction_mask]
    friction_lines = [f"=== SYSTEMIC FRICTION ({len(friction_df)} flagged ticket(s)) ==="]
    if friction_df.empty:
        friction_lines.append("  None detected.")
    else:
        for _, row in friction_df.iterrows():
            queue = row.get("Ticket_Queue", "N/A")
            cat = row.get("Issue_Category", "N/A")
            status = row.get("Ticket_Status", "N/A")
            reason = row.get("Rejection_Reason", "")
            friction_lines.append(f"  - Queue: {queue} | Category: {cat} | Status: {status}")
            if pd.notna(reason) and str(reason).strip():
                friction_lines.append(f"    Rejection: {reason}")
    friction_lines.append("")

    return "\n".join([
        f"Cluster: {cluster_name}",
        f"Total tickets in this cluster: {len(cluster_df)}",
        "",
        *norm_lines,
        *friction_lines,
    ])


def run_cluster_story(cluster_name: str, cache_path: Path = _DEFAULT_CACHE) -> str:
    """Deterministic 3-sentence NOC summary from Parquet data. No LLM call."""
    return _fallback_text_summary(cluster_name, cache_path)


def _fallback_text_summary(cluster_name: str, cache_path: Path = _DEFAULT_CACHE) -> str:
    payload = _extract_cluster_context(cluster_name, cache_path)
    if payload.startswith("["):
        return f"Cluster '{cluster_name}' has no data available."

    lines = payload.splitlines()
    norm_queue = norm_cat = norm_status = ""
    friction_entries: list[str] = []
    in_norm = in_friction = False
    for line in lines:
        s = line.strip()
        if s.startswith("=== OPERATIONAL NORM"):
            in_norm, in_friction = True, False; continue
        if s.startswith("=== SYSTEMIC FRICTION"):
            in_norm, in_friction = False, True; continue
        if in_norm:
            if s.startswith("Queue:"): norm_queue = s.split(":", 1)[1].strip()
            elif s.startswith("Issue Category:"): norm_cat = s.split(":", 1)[1].strip()
            elif s.startswith("Status:"): norm_status = s.split(":", 1)[1].strip()
        if in_friction and s.startswith("- Queue:"):
            friction_entries.append(s)

    s1 = (f"The {norm_queue} queue is successfully processing '{cluster_name}' "
          f"tickets within the {norm_cat} category, maintaining a status of "
          f"'{norm_status}' with no escalations." if norm_queue
          else f"The '{cluster_name}' cluster is operating with no active escalations.")
    s2 = (f"However, {len(friction_entries)} ticket(s) show systemic friction "
          f"related to '{cluster_name}', involving "
          f"{', '.join(friction_entries[:3])}." if friction_entries
          else f"No systemic friction was detected for '{cluster_name}'.")
    s3 = (f"Continue monitoring the affected queues and validate the resolution "
          f"of '{cluster_name}' issues before the next maintenance window."
          if friction_entries
          else f"No immediate action required for '{cluster_name}'; standard monitoring is sufficient.")
    return f"{s1}\n{s2}\n{s3}"


# ---------------------------------------------------------------------------
# Storyteller Agent (singleton)
# ---------------------------------------------------------------------------
STORYTELLER_CONFIG = {
    "role": "NOC Storyteller",
    "goal": (
        "Answer the CURRENT user query about network issues using live ticket data "
        "and SOP descriptions. Always call your tools — never invent facts. "
        "Provide concise, conversational responses suitable for voice output. "
        "If the user says 'tell me more' or 'explain', call the tool again "
        "and narrate the deeper details (custops_check, tie_breaker, steps)."
    ),
    "backstory": (
        "You are a senior NOC operator with 15 years of telecom experience. "
        "You have access to the live knowledge graph, SOP database, and ticket "
        "cluster data. You speak like a shift lead briefing the team — clear, "
        "authoritative, conversational. Keep responses under 60 words."
    ),
    "allow_delegation": False,
    "verbose": False,
}

NARRATION_TASK_CONFIG = {
    "description": (
        "{history_section}"
        "Current query: \"{query}\"\n\n"
        "Use your tools to answer based on real data. "
        "Answer the current query only. "
        "Keep your response under 60 words and conversational."
    ),
    "expected_output": (
        "A concise, conversational response (under 60 words) suitable for TTS."
    ),
}


_storyteller_agent: Any = None


def init_storyteller(model: Optional[str] = None, temperature: float = 0.3) -> Any:
    """Create and return the singleton Storyteller Agent."""
    global _storyteller_agent
    if _storyteller_agent is not None:
        return _storyteller_agent
    try:
        from crewai import Agent, LLM
    except ImportError:
        logger.warning("CrewAI not installed — storyteller agent unavailable")
        return None
    llm_obj = LLM(
        model=model or settings.openai_model or "gpt-4o-mini",
        base_url=settings.openai_api_base,
        api_key=settings.openai_api_key or "ollama",
    )
    _storyteller_agent = Agent(
        role=STORYTELLER_CONFIG["role"],
        goal=STORYTELLER_CONFIG["goal"],
        backstory=STORYTELLER_CONFIG["backstory"],
        allow_delegation=STORYTELLER_CONFIG["allow_delegation"],
        verbose=STORYTELLER_CONFIG["verbose"],
        llm=llm_obj,
        temperature=temperature,
        tools=[lookup_issue, query_trends, extract_cluster_context],
    )
    logger.info("Storyteller agent initialized")
    return _storyteller_agent


def run_storyteller(query: str, history: Optional[list[dict]] = None) -> str:
    """Run the NOC Storyteller with a user query and optional conversation
    history. Returns a narrated string."""

    # --- Guardrail pre-check (bypasses CrewAI + LLM entirely if rejected) ---
    from agenticaiops_shared.guardrails import check_guardrail_standalone
    rejection = check_guardrail_standalone(query)
    if rejection:
        logger.info("Guardrail rejected: '%.100s'", rejection)
        return rejection

    # Build history section — clearly delineated so LLM doesn't confuse it with current query
    history_section = ""
    if history:
        entries = []
        for h in history[-5:]:
            q = h.get("q", "")
            a = h.get("a", "")
            entries.append(f"- Asked: {q}")
            if a:
                entries.append(f"  Answered: {a[:100]}")
        if entries:
            history_section = "=== PAST CONVERSATION (for context only) ===\n" + "\n".join(entries) + "\n\n"

    try:
        from crewai import Task, Crew
    except ImportError:
        return _fallback_narration(query)

    agent = init_storyteller()
    if agent is None:
        return _fallback_narration(query)

    try:
        task = Task(
            description=NARRATION_TASK_CONFIG["description"],
            expected_output=NARRATION_TASK_CONFIG["expected_output"],
            agent=agent,
        )
        crew = Crew(agents=[agent], tasks=[task], verbose=False, memory=False)
        result = crew.kickoff(inputs={
            "query": query,
            "history_section": history_section,
        })
        if hasattr(result, "raw"):
            return str(result.raw).strip()
        return str(result).strip()
    except Exception as exc:
        logger.warning("Storyteller failed: %s", exc)
        return _fallback_narration(query)


def _fallback_narration(query: str) -> str:
    """Deterministic fallback — reads YAML directly, no LLM call."""
    q_lower = _normalize(query)
    issue = _find_issue_in_stories(query)
    reason = _find_reassignment_reason(query)

    if issue and reason:
        count = reason.get("count", issue.get("count", "?"))
        desc = issue.get("description", "")
        return (
            f"There are {count} tickets for {issue.get('name', query)}. "
            f"{desc[:200]} "
            f"The top queues handling this are CS and PS."
        )
    if reason:
        return (
            f"Live count for {reason.get('value', query)} is {reason.get('count', '?')}."
        )

    if any(kw in q_lower for kw in ("top", "biggest", "most common")):
        kg = _get_kg_state()
        for col in kg.get("columns", []):
            if col.get("field") == "reassignment_reason":
                vals = sorted(col.get("values", []), key=lambda v: -v["count"])
                top = vals[0]
                return f"The most common issue is {top['value']} with {top['count']} tickets."

    return (
        f"I don't have data matching '{query}' in the knowledge graph. "
        f"Try asking about a specific issue like Device APN issue or "
        f"Multi SIM not allowed."
    )
