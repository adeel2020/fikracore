from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agenticaiops_shared.guardrails import check_guardrail_standalone

logger = logging.getLogger("jarvis.router")
router = APIRouter(prefix="/api/jarvis", tags=["jarvis"])

_jarvis_instance = None


async def _get_jarvis():
    global _jarvis_instance
    if _jarvis_instance is None:
        from .core import JARVIS
        j = JARVIS()
        await j.initialize()
        _jarvis_instance = j
    return _jarvis_instance


class JarvisRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    session_id: str | None = None


class JarvisResponse(BaseModel):
    session_id: str
    reply: str


@router.post("/process")
async def process(req: JarvisRequest) -> JarvisResponse:
    rejection = check_guardrail_standalone(req.message, agent_role="JARVIS Assistant", agent_goal="Assist with telecom operations")
    if rejection:
        raise HTTPException(status_code=400, detail=rejection)
    try:
        jarvis = await _get_jarvis()
        reply = await jarvis.process(req.message, req.session_id)
        return JarvisResponse(session_id=req.session_id or "default", reply=str(reply))
    except Exception as e:
        logger.error("JARVIS process failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/process/stream")
async def process_stream(req: JarvisRequest) -> StreamingResponse:
    rejection = check_guardrail_standalone(req.message, agent_role="JARVIS Assistant", agent_goal="Assist with telecom operations")
    if rejection:
        raise HTTPException(status_code=400, detail=rejection)

    async def event_stream() -> AsyncIterator[str]:
        yield "event: status\ndata: " + json.dumps({"agent": "jarvis", "task": "processing"}) + "\n\n"
        try:
            jarvis = await _get_jarvis()
            async for chunk in jarvis.stream(req.message, req.session_id):
                yield "event: token\ndata: " + json.dumps({"content": chunk, "agent": "jarvis"}) + "\n\n"
            yield "event: done\ndata: " + json.dumps({"session_id": req.session_id or "default"}) + "\n\n"
        except Exception as e:
            yield "event: error\ndata: " + json.dumps({"message": str(e)}) + "\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/status")
async def status():
    try:
        jarvis = await _get_jarvis()
        return jarvis.get_status()
    except Exception as e:
        logger.error("JARVIS status failed: %s", e)
        return {"status": "offline", "error": str(e)}
