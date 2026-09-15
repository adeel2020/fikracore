from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agenticaiops_shared.guardrails import check_guardrail_standalone

from storyteller.datastory.crewai_storyteller import run_storyteller

logger = logging.getLogger("storyteller.router")
router = APIRouter(prefix="/api/storyteller", tags=["storyteller"])


class StorytellerRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    session_id: str | None = None


class StorytellerResponse(BaseModel):
    session_id: str
    reply: str


@router.post("/ask")
async def ask(req: StorytellerRequest) -> StorytellerResponse:
    rejection = check_guardrail_standalone(req.message, agent_role="NOC Storyteller", agent_goal="Narrate network operations data")
    if rejection:
        raise HTTPException(status_code=400, detail=rejection)
    try:
        reply = await asyncio.to_thread(run_storyteller, req.message, None)
        return StorytellerResponse(session_id=req.session_id or "default", reply=reply)
    except Exception as e:
        logger.error("Storyteller execution failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/ask/stream")
async def ask_stream(req: StorytellerRequest) -> StreamingResponse:
    rejection = check_guardrail_standalone(req.message, agent_role="NOC Storyteller", agent_goal="Narrate network operations data")
    if rejection:
        raise HTTPException(status_code=400, detail=rejection)

    async def event_stream() -> AsyncIterator[str]:
        yield "event: status\ndata: " + json.dumps({"agent": "storyteller", "task": "generating narrative"}) + "\n\n"
        try:
            reply = await asyncio.to_thread(run_storyteller, req.message, None)
            for chunk_text in [reply[i:i+50] for i in range(0, len(reply), 50)]:
                yield "event: token\ndata: " + json.dumps({"content": chunk_text, "agent": "storyteller"}) + "\n\n"
                await asyncio.sleep(0.02)
            yield "event: done\ndata: " + json.dumps({"session_id": req.session_id or "default"}) + "\n\n"
        except Exception as e:
            yield "event: error\ndata: " + json.dumps({"message": str(e)}) + "\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
