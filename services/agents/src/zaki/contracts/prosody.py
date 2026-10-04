"""
Prosody Governance Contract
===========================
This module defines the ProsodyContract governing vocal acoustics, emotional cadence,
conversational brevity, and anti-readout restrictions for Zaki's voice channel.

Guardrails:
1. Anti-Readout Ceiling: Verbatim readout of structured markdown, tables, JSON, UUIDs,
   or telemetry dumps is strictly prohibited.
2. Brevity & Pacing: Spoken briefings are capped at 2 sentences (~35 words) with
   prosodic breathing pauses (`...`) to sound natural, collegial, and human.
3. Acoustic Demeanor: Calm, empathetic Senior Telecom NOC Lead persona delivery.
4. Phonetic Expansion: Technical acronyms (UPF, SCTP, PE-RTR, Gbps) are normalized
   into spoken-friendly pronunciations.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, List
from pydantic import Field

from .base import BaseContract


class ProsodyContract(BaseContract):
    """
    Prosodic and vocal acoustic governance contract for Zaki voice generation.

    Attributes:
        api_version: Schema version identifier ('zaki.ai/v1').
        kind: Contract kind ('ProsodyContract').
        prosody_id: Unique policy configuration identifier.
        persona_name: Vocal persona identity ('SENIOR_TELECOM_NOC_LEAD').
        tone_profile: Emotional demeanor ('EMPATHETIC_COLLEGIAL').
        speaking_rate_wpm: Target speaking rate in words per minute (default: 155).
        readout_prohibited: Prohibits reading markdown tables/telemetry dumps verbatim.
        max_sentences: Maximum spoken sentences (default: 2).
        max_words: Maximum spoken words (default: 35).
        breathing_pauses_enabled: Injects acoustic pauses (...) between clauses.
        phonetic_expansion_enabled: Expands network acronyms to natural speech.
        tts_voice_id: Kokoro or neural TTS voice identifier (default: 'bm_george').
        pitch_adjustment_semitones: Pitch offset for warmth (default: 0.0).
        ui_sync_handshake: Appends standard display transition cue.
    """
    api_version: str = Field(default="zaki.ai/v1", description="Contract API schema version")
    kind: str = Field(default="ProsodyContract", description="Contract kind identifier")
    prosody_id: str = Field(
        default_factory=lambda: f"PROS-{int(datetime.now(timezone.utc).timestamp())}",
        description="Unique prosody policy configuration identifier"
    )
    persona_name: str = Field(
        default="SENIOR_TELECOM_NOC_LEAD",
        description="Vocal persona identity (e.g. SENIOR_TELECOM_NOC_LEAD, INCIDENT_COMMANDER)"
    )
    tone_profile: str = Field(
        default="EMPATHETIC_COLLEGIAL",
        description="Emotional and tonal demeanor (EMPATHETIC_COLLEGIAL, CALM_AUTHORITY, EXECUTIVE_CONCISE)"
    )
    speaking_rate_wpm: int = Field(
        default=155,
        description="Target speaking rate in words per minute"
    )
    readout_prohibited: bool = Field(
        default=True,
        description="Strictly prohibits verbatim readout of markdown, tables, IDs, or telemetry logs"
    )
    max_sentences: int = Field(
        default=2,
        description="Maximum spoken sentences before yielding to UI display"
    )
    max_words: int = Field(
        default=35,
        description="Maximum spoken words per voice turn"
    )
    breathing_pauses_enabled: bool = Field(
        default=True,
        description="Injects prosodic breathing pauses (...) between conversational clauses"
    )
    phonetic_expansion_enabled: bool = Field(
        default=True,
        description="Expands acronyms (UPF, SCTP, PE-RTR, Gbps) into natural spoken forms"
    )
    tts_voice_id: str = Field(
        default="bm_george",
        description="Neural TTS voice profile identifier (Kokoro / edge TTS)"
    )
    pitch_adjustment_semitones: float = Field(
        default=0.0,
        description="Pitch inflection offset for conversational warmth"
    )
    emphasis_level: str = Field(
        default="MODERATE",
        description="Acoustic emphasis intensity on critical anchors (NONE, MODERATE, STRONG)"
    )
    emphasis_style: str = Field(
        default="ACOUSTIC_MICROPAUSE",
        description="Mechanism for emphasis: ACOUSTIC_MICROPAUSE (natural cadence/commas), SSML (<emphasis>), or LEXICAL_INTONATION"
    )
    emphasize_key_entities: bool = Field(
        default=True,
        description="Stresses failing nodes, root causes, and safety thresholds with prosodic focus"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when prosody policy was enacted"
    )

    def to_prompt_directive(self) -> str:
        """Generate system prompt guidance enforcing this prosody contract during LLM generation."""
        emphasis_cue = (
            f"Vocal Emphasis: {self.emphasis_level}. Acoustically emphasize critical node names and root-cause findings with micro-pauses."
            if self.emphasize_key_entities
            else ""
        )
        return (
            f"VOICE SPOKEN CONTRACT: Persona is {self.persona_name} ({self.tone_profile}). "
            f"Never read out technical documents, tables, markdown syntax, or raw telemetry logs. "
            f"Keep spoken briefing under {self.max_sentences} short conversational sentences ({self.max_words} words max) "
            f"with natural pauses. {emphasis_cue} Refer the operator to their screen for full details."
        )

    def apply_emphasis(self, text: str) -> str:
        """Apply prosodic emphasis to key telemetry tokens and network nodes."""
        if not self.emphasize_key_entities or self.emphasis_level == "NONE":
            return text

        if self.emphasis_style == "SSML":
            tag = f'<emphasis level="{self.emphasis_level.lower()}">'
            # Wrap prominent entities in SSML tags
            res = re.sub(
                r"\b(Provider Edge Router \d+|U-P-F \d+|buffer congestion|ninety-four percent)\b",
                rf"{tag}\1</emphasis>",
                text,
            )
            return res

        # Default: ACOUSTIC_MICROPAUSE - ensure commas/micro-pauses highlight critical focal points
        res = re.sub(
            r"\s*\b(Provider Edge Router \d+|U-P-F \d+)\b\s*",
            r", \1, ",
            text,
        )
        res = re.sub(r"\s*,\s*", ", ", res)
        res = re.sub(r"(?:,\s*){2,}", ", ", res)
        res = re.sub(r"\b(on|at|in|to|for|via|from),\s+", r"\1 ", res, flags=re.IGNORECASE)
        res = re.sub(r"\s+", " ", res).strip(" ,")
        return res

    def curate_speech(self, text: str, query: str = "") -> str:
        """Curate free text into spoken audio text strictly compliant with this prosody contract."""
        if not text or not text.strip():
            return ""

        q_clean = (query or "").strip().lower()

        # Handle casual greetings and pleasantries
        if re.search(r"\b(hey|hello|hi|how are you|how're you|how r u|good morning|good afternoon|good evening)\b", q_clean):
            return "Hello! I'm Zaki, your operations co-pilot. I'm actively tracking network telemetry and ready to assist. How can I help you today?"

        # General Anti-Readout Sanitization: curate the ACTUAL text
        t = text
        if self.readout_prohibited:
            t = re.sub(r"```[\s\S]*?```", "", t)
            t = re.sub(r"\|[^\n]+\|\n?", "", t)
            t = re.sub(r"^#{1,6}\s+.*$", "", t, flags=re.MULTILINE)
            t = re.sub(r"^[*-•]\s+", "", t, flags=re.MULTILINE)
            t = re.sub(r"^\d+\.\s+", "", t, flags=re.MULTILINE)
            t = re.sub(r"^>\s+", "", t, flags=re.MULTILINE)
            t = re.sub(r"\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(\.\d+)?Z?\b", "", t)
            t = re.sub(r"\b\d{1,2}:\d{2}(:\d{2})?\s*(AM|PM|am|pm|UTC|GMT|Z)?\b", "", t)
            t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
            t = re.sub(r"\*([^*]+)\*", r"\1", t)
            t = re.sub(r"__([^_]+)__", r"\1", t)
            t = re.sub(r"`([^`]+)`", r"\1", t)
            t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
            t = re.sub(r"\b(?:observations/|knowledge/|incidents/|mobile-core/incidents/)[\w/.-]+", "", t)
            t = re.sub(r"\b(Status|Severity|Correlation|KPIs|Hypotheses|Causal chain|Timeline|Remediation|Recovery):\s*", "", t, flags=re.IGNORECASE)

        # 3. Phonetic Expansion
        if self.phonetic_expansion_enabled:
            t = re.sub(r"\bPE-RTR-0?(\d+)\b", r"Provider Edge Router \1", t)
            t = re.sub(r"\bUPF-0?(\d+)\b", r"U-P-F \1", t)
            t = re.sub(r"\bSCN-0?(\d+)\b", r"Scenario \1", t)
            t = re.sub(r"\b(\d+(?:\.\d+)?)\s*Gbps\b", r"\1 gigabits per second", t)
            t = re.sub(r"\b(\d+(?:\.\d+)?)\s*Mbps\b", r"\1 megabits per second", t)

        t = re.sub(r"\s+", " ", t).strip()

        # 4. Brevity & Sentence Capping
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", t) if s.strip() and len(s.strip()) > 10]
        if not sentences:
            pause = "... " if self.breathing_pauses_enabled else " "
            return f"Telemetry synchronized{pause}I've updated the diagnostic details on your display."

        brief = " ".join(sentences[:self.max_sentences])
        words = brief.split()
        if len(words) > self.max_words:
            brief = " ".join(words[:self.max_words - 3]) + "..."

        pause = "... " if self.breathing_pauses_enabled else " "
        final_text = f"{brief}{pause}I've laid out the complete details on your screen."
        return self.apply_emphasis(final_text)

