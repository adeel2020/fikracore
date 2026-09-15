"""Optional LLM narrative synthesizer.

Layer 2 presentation step: turns a deterministic ``IncidentStory`` into a
natural-language narrative. This is strictly *optional* — correctness lives in
the deterministic ``IncidentStory``, narrative is presentation.

Configuration (env vars, no new client dependencies — uses stdlib urllib):
  - ``STORYTELLER_MODEL`` — model name (default ``""`` = synthesis disabled)
  - ``STORYTELLER_BASE_URL`` — OpenAI-compatible /chat/completions endpoint
  - ``STORYTELLER_API_KEY`` — bearer token

Behavior:
  - If ``STORYTELLER_MODEL`` is unset/empty the synthesizer is disabled and the
    pipeline returns a ``StoryResponse`` with ``narrative=""``,
    ``synthesized=False`` (fully deterministic).
  - On any transport/parse failure the failure is surfaced as a raise by
    default, or (``fail_soft=True``) as a note in ``narrative`` with
    ``synthesized=False``. Never fabricates narrative when the model call fails.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from typing import Any

from .story import IncidentStory

logger = logging.getLogger(__name__)


class StorytellerLLMError(RuntimeError):
    """Raised when the LLM synthesizer cannot produce narrative."""


def _env_model() -> str:
    return os.environ.get("STORYTELLER_MODEL", "").strip()


def _env_base_url() -> str:
    return os.environ.get("STORYTELLER_BASE_URL", "").strip()


def _env_api_key() -> str:
    return os.environ.get("STORYTELLER_API_KEY", "").strip()


def is_synthesis_enabled() -> bool:
    """True when the LLM synthesizer is configured."""
    return bool(_env_model() and _env_base_url() and _env_api_key())


def synthesize_narrative(
    story: IncidentStory,
    *,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    fail_soft: bool = True,
    timeout: int = 60,
) -> tuple[str, str | None]:
    """Generate a narrative for a deterministic story.

    Returns ``(narrative, model)``. When synthesis is disabled or fails and
    ``fail_soft=True``, returns ``("", None)``. When ``fail_soft=False``,
    raises ``StorytellerLLMError``.
    """
    model = model or _env_model()
    base_url = base_url or _env_base_url()
    api_key = api_key or _env_api_key()

    if not (model and base_url and api_key):
        return "", None

    prompt = _build_prompt(story)
    try:
        payload = _chat_completion(base_url, api_key, model, prompt, timeout=timeout)
        return str(payload).strip(), model
    except Exception as exc:  # noqa: BLE001 — surfaced, never swallowed silently
        if fail_soft:
            logger.warning("narrative synthesis failed: %s", exc)
            return "", None
        raise StorytellerLLMError(str(exc)) from exc


def _build_prompt(story: IncidentStory) -> str:
    """Deterministic instruction + JSON snapshot of the story."""
    snapshot = json.dumps(story.to_dict(), default=str, indent=2)
    return (
        "You are a mobile core network incident storyteller. Write a concise, "
        "temporal incident narrative from the structured story below. Base every "
        "claim on the provided facts; do not invent details. Include: what broke, "
        "when, impact, causal chain, what was done to recover, and current status. "
        f"Incident id: {story.incident_id}.\n\n"
        f"STRUCTURED STORY:\n{snapshot}"
    )


def _chat_completion(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    *,
    timeout: int,
) -> Any:
    url = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": "You produce incident narrative text only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise StorytellerLLMError(f"unexpected chat/completions response: {data}") from exc
