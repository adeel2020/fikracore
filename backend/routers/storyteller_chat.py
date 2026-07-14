"""OpenAI-compatible /v1/chat/completions endpoint wrapping run_storyteller().

HF S2S uses this as its LLM backend (--llm_backend chat-completions).

Receives Chat Completions POSTs with user speech transcripts,
delegates to the NOC Storyteller CrewAI agent, and streams the
narration as SSE delta chunks.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str | None = None


class ChatRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    stream: bool = True


async def _call_storyteller(query: str, history: list[dict]) -> str:
    """Run run_storyteller in a thread so the async event loop is not blocked."""
    loop = asyncio.get_event_loop()

    def _run():
        from backend.datastory.crewai_storyteller import run_storyteller
        return run_storyteller(query, history=history)

    return await loop.run_in_executor(None, _run)


def _sentence_chunks(text: str) -> list[str]:
    """Split text at sentence boundaries so HF S2S can stream TTS early."""
    import re
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p for p in parts if p]


async def _stream_chunks(query: str, history: list[dict]) -> AsyncGenerator[str, None]:
    response = await _call_storyteller(query, history)
    for sentence in _sentence_chunks(response):
        chunk = {"choices": [{"delta": {"content": sentence + " "}}]}
        yield f"data: {json.dumps(chunk)}\n\n"
    yield "data: [DONE]\n\n"


@router.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    """OpenAI-compatible streaming chat completions endpoint.

    Only the last ``user`` message is treated as the current query.
    Previous ``user`` messages are injected into the agent's conversation
    history.
    """
    user_messages = [m for m in req.messages if m.role == "user"]
    if not user_messages:
        fallback = {"choices": [{"delta": {"content": "I didn't catch that – could you repeat it?"}}]}
        return StreamingResponse(
            iter([f"data: {json.dumps(fallback)}\n\ndata: [DONE]\n\n"]),
            media_type="text/event-stream",
        )

    query = user_messages[-1].content or ""
    history = [
        {"q": m.content or ""} for m in user_messages[:-1]
    ]

    return StreamingResponse(
        _stream_chunks(query, history),
        media_type="text/event-stream",
        headers={
            "cache-control": "no-cache",
            "x-accel-buffering": "no",
        },
    )
