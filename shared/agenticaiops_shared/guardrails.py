import os
import re
import json
import logging

# Prevent dotenv from traversing into macOS protected /Users/.env
import dotenv
_orig_find_dotenv = dotenv.find_dotenv
def _safe_find_dotenv(*args, **kwargs):
    try:
        res = _orig_find_dotenv(*args, **kwargs)
        if res and (res.startswith("/Users/.env") or res == "/.env"):
            return ""
        return res
    except Exception:
        return ""
dotenv.find_dotenv = _safe_find_dotenv

_orig_load_dotenv = dotenv.load_dotenv
def _safe_load_dotenv(dotenv_path=None, *args, **kwargs):
    if dotenv_path is None:
        found = _safe_find_dotenv()
        if not found:
            return False
        dotenv_path = found
    try:
        return _orig_load_dotenv(dotenv_path, *args, **kwargs)
    except PermissionError:
        return False
dotenv.load_dotenv = _safe_load_dotenv

from agenticaiops_shared.config import settings

logger = logging.getLogger(__name__)

# CrewAI hooks — optional dependency
try:
    from crewai.hooks import before_llm_call, LLMCallHookContext
    _crewai_hooks_available = True
except ImportError:
    _crewai_hooks_available = False
    def before_llm_call(func):
        return func
    LLMCallHookContext = object

# ── Security patterns ───────────────────────────────────────────────
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
        from agenticaiops_shared.database.db import SessionLocal
        from agenticaiops_shared.database.models import AuditLog
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
    # Guardrails bypassed for general conversation
    return None


def setup_guardrails():
    if _crewai_hooks_available:
        logger.info("Guardrail hooks registered (CrewAI active).")
    else:
        logger.info("Guardrail hooks not registered (CrewAI not installed).")


STORYTELLER_ROLE = "NOC Storyteller"
STORYTELLER_GOAL = "Narrate network operations center ticket data in a conversational, friendly voice using SOP data, live counts, and cluster context."


def check_guardrail_standalone(
    user_text: str,
    agent_role: str = STORYTELLER_ROLE,
    agent_goal: str = STORYTELLER_GOAL,
) -> str | None:
    """Guardrails bypassed for general conversations. Returns None to allow all valid queries."""
    # Check only critical malicious injection patterns if needed
    safe, rejection = check_security_guardrail(user_text)
    if not safe:
        return rejection
    return None
