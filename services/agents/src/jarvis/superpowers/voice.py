"""
JARVIS Voice Engine - Speech Synthesis & Recognition with ElevenLabs.
Handles voice commands, text-to-speech with natural neural voices, and speech-to-text.
"""

from __future__ import annotations

import os
import asyncio
import logging
from typing import Any, AsyncIterator
import httpx

from agenticaiops_shared.config import settings

logger = logging.getLogger("jarvis.voice")

# ElevenLabs voice options
ELEVENLABS_VOICES = {
    "jarvis": "JBFqnCBsd6RMkjVDRZzb",   # George - Warm, British, refined (Classic JARVIS)
    "adam": "pNInz6obpgDQGcFmaJgB",     # Adam - Deep, clear narrator
    "rachel": "21m00Tcm4TlvDq8ikWAM",   # Rachel - Calm, articulate assistant
    "antoni": "ErXwobaYiN019PkySvjV",   # Antoni - Crisp, confident
}


class VoiceEngine:
    """JARVIS voice superpower - ElevenLabs neural TTS / STT."""

    def __init__(self, config=None):
        self.config = config
        self.api_key = (
            os.getenv("ELEVENLABS_API_KEY")
        )
        self.voice_id = (
            getattr(settings, "elevenlabs_voice_id", None)
            or ELEVENLABS_VOICES["jarvis"]
        )
        self.model_id = (
            getattr(settings, "elevenlabs_model", None)
            or "eleven_turbo_v2_5"
        )
        self._http_client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        """Initialize HTTP client for ElevenLabs TTS."""
        self._http_client = httpx.AsyncClient(timeout=30.0)
        if self.api_key:
            logger.info(f"[VoiceEngine] ElevenLabs TTS initialized with Voice ID: {self.voice_id}")
        else:
            logger.warning("[VoiceEngine] No ELEVENLABS_API_KEY found, fallback modes will be used.")

    async def synthesize(self, text: str, voice: str | None = None) -> bytes:
        """Convert text to speech using ElevenLabs API."""
        if not text.strip():
            return b""

        target_voice_id = ELEVENLABS_VOICES.get(voice or "", voice or self.voice_id)
        api_key = (
            os.getenv("ELEVENLABS_API_KEY")
            or getattr(settings, "elevenlabs_api_key", None)
            or self.api_key
        )

        if not api_key:
            logger.warning("[VoiceEngine] ElevenLabs API key missing, returning empty audio.")
            return b""

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{target_voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.55,
                "similarity_boost": 0.8,
                "style": 0.15,
                "use_speaker_boost": True,
            },
        }

        try:
            client = self._http_client or httpx.AsyncClient(timeout=30.0)
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                logger.info(f"[VoiceEngine] Synthesized {len(response.content)} bytes of ElevenLabs audio for: {text[:40]}...")
                return response.content
            else:
                logger.error(f"[VoiceEngine] ElevenLabs error ({response.status_code}): {response.text}")
                return b""
        except Exception as e:
            logger.error(f"[VoiceEngine] Synthesis request failed: {e}")
            return b""

    async def process(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Process voice query."""
        clean_query = query.replace("speak", "").replace("say aloud", "").strip()
        audio = await self.synthesize(clean_query)
        return f"Voice synthesis completed: {len(audio)} audio bytes generated."

    async def transcribe(self, audio_data: bytes) -> str:
        """Convert speech to text."""
        return "STT handled via Web Speech API and backend audio bridge."

    async def shutdown(self) -> None:
        """Cleanup HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
        logger.info("[VoiceEngine] Shutdown complete.")
