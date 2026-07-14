import os
import re
import json
import logging
from agenticaiops_shared.config import settings
from litellm import completion

logger = logging.getLogger(__name__)

# CrewAI hooks — optional dependency
try:
    from crewai.hooks import before_llm_call, LLMCallHookContext
    _crewai_hooks_available = True
except ImportError:
    _crewai_hooks_available = False
    # Define no-op decorator and type so the rest of the module can still compile
    def before_llm_call(func):
        return func
    LLMCallHookContext = object

# ── Security patterns (aligned with JARVIS SecurityEngine) ──────────
SQL_INJECTION_PATTERNS = [
    r"(?i)union\s+select",
    r"(?i)insert\s+into",
    r"(?i)delete\s+from",
    r"(?i)drop\s+(table|database)",
    r"(?i)truncate\s+table",
    r"(?i)alter\s+table",
    r"(?i)exec\s*\(",
    r"(?i)execute\s*\(",
]

CODE_INJECTION_PATTERNS = [
    r"(?i)eval\s*\(",
    r"(?i)exec\s*\(",
    r"(?i)os\.system\s*\(",
    r"(?i)subprocess\.call\s*\(",
    r"(?i)subprocess\.run\s*\(",
    r"(?i)__import__",
]

PATH_TRAVERSAL_PATTERNS = [
    r"\.\.\/",
    r"\.\.\\",
    r"(?i)/etc/passwd",
    r"(?i)/etc/shadow",
]

SECRET_EXPOSURE_PATTERNS = [
    r"(?i)password\s*=\s*['\"][^'\"]+['\"]",
    r"(?i)secret\s*=\s*['\"][^'\"]+['\"]",
    r"(?i)api[_-]?key\s*=\s*['\"][^'\"]+['\"]",
    r"(?i)aws[_-]?(access|secret)\s*[_-]?key",
]


def check_security_guardrail(text: str) -> tuple[bool, str | None]:
    """Returns (is_safe, rejection_reason). If safe, rejection_reason is None."""
    if any(re.search(p, text) for p in SQL_INJECTION_PATTERNS):
        _log_security_event("sql_injection", text)
        return False, "Input blocked: SQL injection pattern detected."

    if any(re.search(p, text) for p in CODE_INJECTION_PATTERNS):
        _log_security_event("code_injection", text)
        return False, "Input blocked: Code injection pattern detected."

    if any(re.search(p, text) for p in PATH_TRAVERSAL_PATTERNS):
        _log_security_event("path_traversal", text)
        return False, "Input blocked: Path traversal pattern detected."

    if any(re.search(p, text) for p in SECRET_EXPOSURE_PATTERNS):
        _log_security_event("secret_exposure", text)
        return False, "Input blocked: Potential secret exposure detected."

    return True, None


def _log_security_event(event_type: str, text: str) -> None:
    logger.warning("SECURITY_GUARDRAIL=%s text=%.100s", event_type, text)
    try:
        db = SessionLocal()
        db.add(AuditLog(
            method="GUARDRAIL",
            path="internal",
            status_code=403,
            security_event=event_type,
            request_body_preview=text[:200],
            iso_control="A.8.15",
        ))
        db.commit()
    except Exception:
        pass
    finally:
        try:
            db.close()
        except Exception:
            pass

@before_llm_call
def validate_agent_input(context: LLMCallHookContext):
    # Retrieve agent's role and goal dynamically
    agent_role = context.agent.role
    agent_goal = context.agent.goal

    # Skip system or helper agents that do not have roles/goals defined
    if not agent_role or not agent_goal:
        return None

    # Extract the user prompt from messages
    user_prompt = ""
    for msg in reversed(context.messages):
        if msg.get("role") == "user":
            user_prompt = msg.get("content", "")
            break

    if not user_prompt:
        return None

    # Parse task description if it is wrapped in CrewAI task layout
    task_desc = user_prompt
    if "Current Task:" in user_prompt:
        match = re.search(r"Current Task:\s*(.*?)(?:\n\nThis is the expected criteria|\Z)", user_prompt, re.DOTALL)
        if match:
            task_desc = match.group(1).strip()
    # Also handle custom "The user said: '...'" template used by the storyteller
    # (might be inside a "Current Task:" wrapper, so check both paths)
    while "The user said:" in task_desc:
        # Match the query between quotes, but only if the closing quote is
        # followed by a newline (avoids breaking on apostrophes in the query)
        match = re.search(r"The user said:\s*'(.*?)'\n", task_desc, re.DOTALL)
        if not match:
            match = re.search(r'The user said:\s*"(.*?)"\n', task_desc, re.DOTALL)
        if match:
            task_desc = match.group(1).strip()
            if task_desc:
                break  # extracted successfully
        # fallback
        task_desc = user_prompt
        break

    # Skip validation if it's a slash command (direct skill invocations)
    if task_desc.startswith("/"):
        return None

    # 0. Security guardrail — injection, traversal, secret exposure
    safe, rejection = check_security_guardrail(task_desc)
    if not safe:
        logger.warning(
            "Security guardrail triggered for '%s': %s",
            agent_role, rejection,
        )
        _redirect_llm(context, rejection or "Input blocked by security guardrail.")
        return None

    # 1. Local heuristic check for gibberish/keyboard smashing
    cleaned_words_str = re.sub(r"[^a-zA-Z\s]", "", task_desc).strip()
    is_gibberish = False
    if cleaned_words_str:
        words = cleaned_words_str.split()
        for word in words:
            w_len = len(word)
            if w_len >= 5:
                if re.search(r"(.)\1\1", word.lower()):
                    is_gibberish = True
                    break
                vowels = set("aeiouyAEIOUY")
                v_count = sum(1 for c in word if c in vowels)
                if v_count == 0:
                    is_gibberish = True
                    break
                if w_len >= 8 and (v_count / w_len) < 0.15:
                    if word.lower() not in {"strengths", "lengths"}:
                        is_gibberish = True
                        break
                consecutive_consonants = 0
                max_consecutive = 0
                for c in word.lower():
                    if c not in vowels and c.isalpha():
                        consecutive_consonants += 1
                        if consecutive_consonants > max_consecutive:
                            max_consecutive = consecutive_consonants
                    else:
                        consecutive_consonants = 0
                if max_consecutive >= 5 and word.lower() not in {"lengths", "strengths", "angstrom"}:
                    is_gibberish = True
                    break

    if is_gibberish:
        logger.warning(
            "Gibberish heuristic triggered for '%s': word='%s', text='%.100s'",
            agent_role, word, task_desc,
        )
        redirect_message = (
            f"The request is invalid or contains gibberish. As a {agent_role}, "
            f"my goal is: {agent_goal}. Please provide a valid, coherent query."
        )
        _redirect_llm(context, redirect_message)
        return None

    # 2. LLM Semantic Relevance Validation
    try:
        system_prompt = (
            "You are an input validation guardrail system for an AI Agent in a Telecom Operations platform.\n"
            f"Active Agent Role: {agent_role}\n"
            f"Active Agent Goal: {agent_goal}\n\n"
            "Your task is to determine if the user's prompt matches the role and goal of this agent.\n"
            "Set valid to true if the prompt is related to the agent's role, goal, or tasks that such an agent would perform.\n"
            "This includes any telecom, network, cloud infrastructure (e.g. PCF, AWS, Azure), ticket, queue, "
            "reassignment, SOP, alert, incident, or monitoring related queries.\n"
            "Valid examples: \"device apn issue\", \"data allocation\", \"bundles\", \"volte not active\", "
            "\"pcf mismatch\", \"top queues\", \"multi sim\", \"esim\", \"5GSA\", \"roaming\", \"bundle throttling\".\n"
            "Set valid to false ONLY if the prompt is completely unrelated (e.g., cooking recipes, writing general essays, "
            "unrelated jokes, coding a social network, sports scores, movie recommendations).\n"
            "Do NOT reject for vagueness, incomplete queries, or unclear wording. The agent's tools have fuzzy matching and substring search — they can handle short or partial queries.\n"
            "When in doubt, prefer valid:true — let the agent decide if it can answer with its tools.\n\n"
            "Answer ONLY in JSON format: {\"valid\": true} or {\"valid\": false, \"reason\": \"<friendly explanation of why the query is off-topic for this specific agent's role and goal, and a redirection to what this agent actually does>\"}."
        )

        response = completion(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task_desc}
            ],
            temperature=0.0,
            api_key=settings.openai_api_key or "ollama",
            base_url=settings.openai_api_base,
        )

        res_content = response.choices[0].message.content
        res_json = json.loads(res_content)
        if not res_json.get("valid", True):
            redirect_message = res_json.get("reason", f"The query is off-topic for my role as a {agent_role}.")
            logger.warning(
                "LLM relevance guardrail triggered for '%s': reason='%s'",
                agent_role, redirect_message,
            )
            _redirect_llm(context, redirect_message)
    except Exception as e:
        print(f"[Agent Guardrail] Validation check skipped due to error: {e}")

    return None

def _redirect_llm(context: LLMCallHookContext, redirect_message: str):
    logger.info("Redirecting LLM for agent '%s'", context.agent.role)
    context.messages.clear()
    context.messages.append({
        "role": "user",
        "content": (
            f"The task/query is off-topic for your role. You MUST immediately reply with the "
            f"following exact text and nothing else, without calling any tools or doing anything else: "
            f"{redirect_message}"
        )
    })

def setup_guardrails():
    """Initializes the guardrails hook module.
    This ensures that the hooks are globally registered by CrewAI on startup.
    """
    if _crewai_hooks_available:
        logger.info("Guardrail hooks registered (CrewAI active).")
    else:
        logger.info("Guardrail hooks not registered (CrewAI not installed).")


# ---------------------------------------------------------------------------
# Standalone guardrail — run BEFORE invoking the agent to skip the LLM entirely
# when guardrail rejects. Returns rejection text or None (let agent handle it).
# ---------------------------------------------------------------------------

STORYTELLER_ROLE = "NOC Storyteller"
STORYTELLER_GOAL = "Narrate network operations center ticket data in a conversational, friendly voice using SOP data, live counts, and cluster context."


def check_guardrail_standalone(
    user_text: str,
    agent_role: str = STORYTELLER_ROLE,
    agent_goal: str = STORYTELLER_GOAL,
) -> str | None:
    """Returns a rejection message if input fails guardrail, or None if valid."""

    # --- Security guardrail ---
    safe, rejection = check_security_guardrail(user_text)
    if not safe:
        logger.warning("Security guardrail triggered: %s", rejection)
        return rejection

    # --- Gibberish heuristic ---
    cleaned = re.sub(r"[^a-zA-Z\s]", "", user_text).strip()
    if cleaned:
        words = cleaned.split()
        for word in words:
            wlen = len(word)
            if wlen >= 5:
                if re.search(r"(.)\1\1", word.lower()):
                    return (
                        f"The request is invalid or contains gibberish. As a {agent_role}, "
                        f"my goal is: {agent_goal}. Please provide a valid, coherent query."
                    )
                vowels = set("aeiouyAEIOUY")
                vc = sum(1 for c in word if c in vowels)
                if vc == 0:
                    return (
                        f"The request is invalid or contains gibberish. As a {agent_role}, "
                        f"my goal is: {agent_goal}. Please provide a valid, coherent query."
                    )
                if wlen >= 8 and (vc / wlen) < 0.15 and word.lower() not in {"strengths", "lengths"}:
                    return (
                        f"The request is invalid or contains gibberish. As a {agent_role}, "
                        f"my goal is: {agent_goal}. Please provide a valid, coherent query."
                    )
                cons = 0
                maxc = 0
                for c in word.lower():
                    if c not in vowels and c.isalpha():
                        cons += 1
                        if cons > maxc:
                            maxc = cons
                    else:
                        cons = 0
                if maxc >= 5 and word.lower() not in {"lengths", "strengths", "angstrom"}:
                    return (
                        f"The request is invalid or contains gibberish. As a {agent_role}, "
                        f"my goal is: {agent_goal}. Please provide a valid, coherent query."
                    )

    # --- LLM relevance check ---
    try:
        system_prompt = (
            "You are an input validation guardrail system for an AI Agent in a Telecom Operations platform.\n"
            f"Active Agent Role: {agent_role}\n"
            f"Active Agent Goal: {agent_goal}\n\n"
            "Your task is to determine if the user's prompt matches the role and goal of this agent.\n"
            "Set valid to true if the prompt is related to the agent's role, goal, or tasks that such an agent would perform.\n"
            "This includes any telecom, network, cloud infrastructure (e.g. PCF, AWS, Azure), ticket, queue, "
            "reassignment, SOP, alert, incident, or monitoring related queries.\n"
            "Valid examples: \"device apn issue\", \"data allocation\", \"bundles\", \"volte not active\", "
            "\"pcf mismatch\", \"top queues\", \"multi sim\", \"esim\", \"5GSA\", \"roaming\", \"bundle throttling\".\n"
            "Set valid to false ONLY if the prompt is completely unrelated (e.g. cooking, sports, movies, coding a website).\n"
            "Do NOT reject for vagueness, incomplete queries, or unclear wording. The agent's tools have fuzzy matching and substring search — they can handle short or partial queries.\n"
            "When in doubt, prefer valid:true — let the agent decide if it can answer with its tools.\n\n"
            "Answer ONLY in JSON format: {\"valid\": true} or {\"valid\": false, \"reason\": \"<explanation>\"}."
        )

        response = completion(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            temperature=0.0,
            api_key=settings.openai_api_key or "ollama",
            base_url=settings.openai_api_base,
        )

        res = json.loads(response.choices[0].message.content)
        if not res.get("valid", True):
            reason = res.get("reason", f"The query is off-topic for my role as a {agent_role}.")
            logger.warning(
                "LLM relevance guardrail triggered for '%s': reason='%s'",
                agent_role, reason,
            )
            return reason
    except Exception as e:
        logger.warning("Guardrail LLM check skipped: %s", e)

    return None
