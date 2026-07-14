"""LLM orchestrator that synthesises the semantic narrative into an executive brief.

Uses ``langchain-openai`` (``ChatOpenAI``) under the hood — backed by the same
``OPENAI_API_KEY`` / ``OPENAI_MODEL`` configured in ``backend.config``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from backend.config import settings

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


class DataStorytellerAgent:
    """Generates an executive narrative from the narrative stream JSON.

    Loads the system prompt from ``prompts/executive_narrative.md`` and
    invokes the configured LLM with the narrative stream as context.
    """

    def __init__(self, model: Optional[str] = None, temperature: float = 0.3) -> None:
        self.model = model or settings.openai_model or "gpt-4o-mini"
        self.temperature = temperature
        self._system_prompt: Optional[str] = None

    @property
    def system_prompt(self) -> str:
        if self._system_prompt is None:
            prompt_path = _PROMPTS_DIR / "executive_narrative.md"
            if prompt_path.exists():
                self._system_prompt = prompt_path.read_text(encoding="utf-8")
            else:
                self._system_prompt = "You are a data storyteller. Summarise the data."
        return self._system_prompt

    def generate_story(self, narrative_stream: Dict[str, Any]) -> str:
        """Produce a markdown executive brief from the narrative stream."""
        try:
            return self._invoke_openai(narrative_stream)
        except Exception:
            return self._fallback_summary(narrative_stream)

    # ------------------------------------------------------------------
    # OpenAI (direct client — avoids hard langchain dependency)
    # ------------------------------------------------------------------
    def _invoke_openai(self, narrative_stream: Dict[str, Any]) -> str:
        from openai import OpenAI

        base_url = settings.openai_api_base
        if "11434" in base_url and not base_url.endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"

        client = OpenAI(api_key=settings.openai_api_key or "ollama", base_url=base_url)

        model_name = self.model
        if model_name.startswith("ollama/"):
            model_name = model_name[7:]

        user_prompt = (
            "Here is the semantic narrative stream from the ticket "
            "decomposition engine:\n\n"
            f"{narrative_stream}\n\n"
            "Produce an executive brief according to the system instructions."
        )

        response = client.chat.completions.create(
            model=model_name,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1024,
        )
        content = response.choices[0].message.content
        return content.strip() if content else "No narrative generated."

    # ------------------------------------------------------------------
    # Fallback (no API key / network failure)
    # ------------------------------------------------------------------
    @staticmethod
    def _fallback_summary(narrative_stream: Dict[str, Any]) -> str:
        clusters = narrative_stream.get("clusters", [])
        lines = ["## Executive Brief (offline mode)\n"]
        lines.append(
            f"Dominant axis: {narrative_stream.get('dominant_operational_axis', 'N/A')}  \n"
        )
        lines.append(
            f"Total tickets in semantic cloud: {narrative_stream.get('total_tickets', 'N/A')}  \n"
        )
        lines.append("")
        for c in clusters:
            lines.append(f"### {c.get('theme', 'Unknown')}")
            lines.append(f"- Volume: {c.get('volume', 'N/A')}")
            lines.append(
                f"- Exemplar: {c.get('highest_centrality_example', 'N/A')}"
            )
            anomalies = c.get("anomalies_to_investigate", [])
            if anomalies:
                lines.append(f"- Anomalies: {len(anomalies)} flagged")
                for a in anomalies:
                    lines.append(f"  - {a}")
            lines.append("")
        return "\n".join(lines)
