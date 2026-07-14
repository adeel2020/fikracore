"""
Orchestrator — The Intelligence Gateway.

Uses OpenAI chat completions to classify user queries into one of two
routes. When the OpenAI API key is unavailable, it falls back to a
lightweight keyword / phrase matcher for storyteller vs QnA routing.
"""

from __future__ import annotations

import re
from agenticaiops_shared.config import settings


# ------------------------------------------------------------------
# 1. Route definitions (10+ high-quality utterances each)
# ------------------------------------------------------------------
ROUTES: dict[str, list[str]] = {
    "storyteller_workflow": [
        # Report / analysis requests
        "Build me a comprehensive report on Q4 revenue trends",
        "Run a deep-dive analysis across all datasets",
        "Create an executive dashboard with business and technical insights",
        "I need a full multi-agent analysis of customer churn patterns",
        "Analyze churn risk across all segments and write a detailed report",
        "Give me a complete business plus technical analysis of our Q4 performance",
        "Create a comprehensive visualization report with actionable recommendations",
        "I want a long-form narrative combining business metrics and system health",
        # Data story requests (the gap that caused misrouting)
        "Generate a blog-style data story from the sales data",
        "Share the data story for the inventory snapshot dataset",
        "Show me the datastory for revenue data",
        "Tell me a data story about customer churn",
        "Create a datastory for the inventory snapshot",
        "Give me the data story on the revenue dataset",
        "Write a data story covering the warehouse inventory data",
        "Share insights and a narrative for the customer segments dataset",
        # Crew / synthesis requests
        "Synthesize insights from every data source into a single narrative",
        "Produce an end-to-end breakdown of customer segments and their value",
        "Run the storyteller crew on the inventory and revenue datasets",
        "Run the storyteller on the customer churn data",
        "Generate a narrative report for the inventory snapshot",
        "Produce a story from the revenue trends data",
    ],
    "qna_workflow": [
        "What was the churn rate last quarter?",
        "How many SKUs need reordering right now?",
        "What did we discuss yesterday about EMEA revenue?",
        "Remind me what the correlation between lifetime value and churn risk was",
        "What is the average revenue per enterprise customer?",
        "Which warehouse has the lowest inventory count?",
        "Can you pull up the findings from my last session?",
        "What is the top-line number for Q4 sales?",
        "Give me a quick stat on customer lifetime value",
        "Summarize what we talked about in session abc-123",
        "How does NA revenue compare to APAC this quarter?",
        "What percentage of customers are in the Champions segment?",
    ],
}

# Keyword sets for fallback classification (no API needed)
_STORYTELLER_KEYWORDS = {
    "comprehensive", "report", "deep-dive", "dashboard", "narrative",
    "synthesize", "synthesis", "story", "blog", "end-to-end", "breakdown",
    "multi-agent", "crew", "detailed", "analysis", "analyze", "full",
    "long-form", "visualization", "actionable",
    # Data-story specific terms
    "datastory", "storyteller", "insights", "generate", "produce",
    "write", "create", "build", "share", "run",
}
_QNA_KEYWORDS = {
    "what", "how", "which", "who", "when", "where", "why",
    "quick", "stat", "number", "compare", "percentage", "average",
    "remind", "summarize", "pull up", "last session", "discuss",
}

_STORYTELLER_PHRASES = {
    "data story", "datastory", "storyteller crew", "run the storyteller",
    "run storyteller", "share the datastory", "create a datastory",
    "generate a narrative", "write a data story",
}


# ------------------------------------------------------------------
# 2. LLM supervisor (replaces embedding-based classification)
# ------------------------------------------------------------------
_openai_client = None


def _get_openai_client():
    """Lazy-init the OpenAI client."""
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI

        base_url = settings.openai_api_base
        if "11434" in base_url and not base_url.endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"

        _openai_client = OpenAI(api_key=settings.openai_api_key or "ollama", base_url=base_url)
    return _openai_client


def _llm_supervise(query: str) -> str:
    """Ask a small LLM to choose the target route for a query.

    Returns one of: "storyteller_workflow" or "qna_workflow".
    Falls back to keyword classification if the model's reply is unexpected.
    """
    client = _get_openai_client()

    system = (
        "You are a routing classifier. Given a user query, respond with EXACTLY "
        "one of these three tokens: storyteller_workflow, qna_workflow, or cognitive_workflow.\n\n"
        "STORYTELLER_WORKFLOW — choose this when the user wants to:\n"
        "  • Generate, create, build, write, share, or produce a data story, datastory, or narrative\n"
        "  • Run a deep-dive, comprehensive, or multi-dataset analysis or report\n"
        "  • Trigger the storyteller crew / agent on any dataset\n"
        "  • Get insights, executive dashboards, or visualisation reports\n"
        "  • Any imperative request about a specific dataset that asks for generation of content\n"
        "  Examples: 'share the datastory for inventory snapshot', 'run the storyteller on revenue data', "
        "'generate a narrative for customer churn', 'create a report on Q4 trends'\n\n"
        "COGNITIVE_WORKFLOW — choose this when the user wants to:\n"
        "  • Write code, develop a script, refactor, debug, or solve a general coding/programming task\n"
        "  • Create or modify workspace files, run shell commands, or plan a feature implementation\n"
        "  • Address developer issues or talk to Cognitive Operation & Customer Center directly\n"
        "  Examples: 'write a python script to parse traces', 'create a new agent configuration file', "
        "'plan the new frontend page layout', 'debug the api endpoint'\n\n"
        "QNA_WORKFLOW — choose this when the user wants to:\n"
        "  • Ask a direct factual question (what, how, which, who, when)\n"
        "  • Get a single metric, stat, or quick number\n"
        "  • Recall something from a previous session or conversation\n"
        "  • Compare two values or ask about correlations\n"
        "  Examples: 'what was the churn rate last quarter?', 'how many SKUs need reordering?', "
        "'what percentage of customers are Champions?'\n\n"
        "Respond with exactly one token. Do not explain."
    )

    user_msg = f"Query: {query}"

    model_name = settings.openai_model
    if model_name.startswith("ollama/"):
        model_name = model_name[7:]

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
        temperature=0.0,
        max_tokens=10,
    )

    text = "".join([choice.message.content for choice in response.choices]).strip().lower()
    if "storyteller_workflow" in text:
        return "storyteller_workflow"
    if "cognitive_workflow" in text:
        return "cognitive_workflow"
    if "qna_workflow" in text:
        return "qna_workflow"

    raise ValueError(f"Unexpected routing response from LLM: {text}")


def _is_interrogative_query(query: str) -> bool:
    """Detect questions that should go to the QnA workflow."""
    normalized = query.strip().lower()
    if not normalized:
        return False

    interrogative_start = (
        normalized.startswith("what") or
        normalized.startswith("who") or
        normalized.startswith("when") or
        normalized.startswith("where") or
        normalized.startswith("why") or
        normalized.startswith("how") or
        normalized.startswith("is") or
        normalized.startswith("are") or
        normalized.startswith("do") or
        normalized.startswith("does") or
        normalized.startswith("did") or
        normalized.startswith("can") or
        normalized.startswith("could") or
        normalized.startswith("should") or
        normalized.startswith("would")
    )

    return interrogative_start or normalized.endswith("?")


# ------------------------------------------------------------------
# 3. Public API
# ------------------------------------------------------------------
def get_route(query: str, session_id: str | None = None, db = None) -> str:
    """Classify a user query and return the active route name.

    Returns
    -------
    str
        Either ``"storyteller_workflow"``, ``"qna_workflow"``, or ``"signaling_workflow"``.
        Uses LLM supervision when available.
    """
    if query.strip().startswith("/"):
        print(f"[Orchestrator] Slash command detected: {query[:60]}... → skill_workflow")
        return "skill_workflow"

    # Chart/graph intent — always QnA/RAG workflow, never storyteller
    chart_keywords = ["chart", "graph", "plot", "visuali", "trend"]
    if any(kw in query.lower() for kw in chart_keywords):
        print(f"[Orchestrator] Chart/graph intent detected: {query[:60]}... → qna_workflow")
        return "qna_workflow"

    if session_id and db:
        from agenticaiops_shared.database.models import SessionTelemetry
        try:
            latest_tel = (
                db.query(SessionTelemetry)
                .filter(SessionTelemetry.session_id == session_id)
                .filter(SessionTelemetry.agent_name != "System Validator")
                .order_by(SessionTelemetry.created_at.desc())
                .first()
            )
            if latest_tel and latest_tel.agent_name:
                agent_name = latest_tel.agent_name
                if agent_name == "Data Storyteller":
                    print(f"[Orchestrator] Session {session_id} locked to Data Storyteller → storyteller_workflow")
                    return "storyteller_workflow"
                elif agent_name in ("Cognitive Operation & Customer Center", "Core Mobile Network Data Analyst"):
                    print(f"[Orchestrator] Session {session_id} locked to Cognitive Operator → cognitive_workflow")
                    return "cognitive_workflow"
                elif agent_name in ("Conversational Subject Matter Expert", "Customer Complaint Analyst", "QnA Assistant"):
                    print(f"[Orchestrator] Session {session_id} locked to QnA/Complaint Analyst → qna_workflow")
                    return "qna_workflow"
                elif agent_name == "Senior Telecom Signaling Analyst" or agent_name.endswith("Specialist") or agent_name.endswith("Analyst"):
                    print(f"[Orchestrator] Session {session_id} locked to Telecom Signaling/Skill Specialist ({agent_name}) → signaling_workflow")
                    return "signaling_workflow"
        except Exception as e:
            print(f"[Orchestrator] Failed to fetch session history lock: {e}")

    if any(keyword in query.lower() for keyword in ["cognitive operation & customer center", "cognitive operation", "cognitive operator", "customer center", "plan", "write code", "debug", "refactor", "create file", "modify file"]):
        print(f"[Orchestrator] Cognitive workflow query detected: {query[:60]}... → cognitive_workflow")
        return "cognitive_workflow"

    if _is_interrogative_query(query):
        print(f"[Orchestrator] Interrogative query detected: {query[:60]}... → qna_workflow")
        return "qna_workflow"

    try:
        route = _llm_supervise(query)
        print(f"[Orchestrator] LLM supervise: {query[:60]}... → {route}")
        return route
    except Exception as e:
        print(f"[Orchestrator] LLM supervision failed: {e}")
        result = _is_interrogative_query(query)
        print(f"[Orchestrator] Interrogative query fallback: {query[:60]}... → {result}")
        return result
