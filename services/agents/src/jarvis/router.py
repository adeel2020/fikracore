from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from capability_registry import load_default_registry
from mcp_hub import MCPPolicyError, get_default_mcp_client_hub
from jarvis.superpowers.voice import VoiceEngine, ELEVENLABS_VOICES

logger = logging.getLogger("jarvis.router")
router = APIRouter(prefix="/api/jarvis", tags=["jarvis"])

_jarvis_instance = None
_voice_engine = None

async def _get_jarvis():
    global _jarvis_instance
    if _jarvis_instance is None:
        from assistant.mark import JARVIS
        j = JARVIS()
        await j.initialize()
        _jarvis_instance = j
    return _jarvis_instance


async def _get_voice_engine():
    global _voice_engine
    if _voice_engine is None:
        _voice_engine = VoiceEngine()
        await _voice_engine.initialize()
    return _voice_engine


def _get_mcp_hub():
    return get_default_mcp_client_hub()


class JarvisRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    session_id: str | None = None
    user_name: str | None = None
    incident_id: str | None = None


class JarvisResponse(BaseModel):
    session_id: str
    reply: str
    spoken_reply: str | None = None
    incident_id: str | None = None
    narrative: dict | None = None
    visual_explanation: dict | None = None
    telemetry_evidence: list[dict] | None = None
    rtr_journey: dict | None = None


class SpeakRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    voice: str | None = "jarvis"


class MCPToolCallRequest(BaseModel):
    tool_name: str = Field(..., min_length=1, max_length=200)
    arguments: dict[str, object] = Field(default_factory=dict)
    approval_granted: bool = False
    require_approval: bool | None = None


@router.post("/process")
async def process(req: JarvisRequest) -> JarvisResponse:
    # Guardrails bypassed for general conversation as requested
    try:
        jarvis = await _get_jarvis()
        context = {
            key: value
            for key, value in {
                "user_name": req.user_name,
                "incident_id": req.incident_id,
            }.items()
            if value
        }
        reply = await jarvis.process(req.message, req.session_id, context=context or None)
        session = jarvis.session_store.get(req.session_id or "default")
        from storyteller.conversation.intents import curate_spoken_text
        spoken_reply = getattr(reply, "spoken_reply", None) or curate_spoken_text(str(reply))
        return JarvisResponse(
            session_id=req.session_id or "default",
            reply=str(reply),
            spoken_reply=spoken_reply,
            incident_id=session.active_incident_id if session else req.incident_id,
            **getattr(reply, "presentation", {}),
        )
    except Exception as e:
        logger.error("MARK process failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/process/stream")
async def process_stream(req: JarvisRequest) -> StreamingResponse:
    # Guardrails bypassed for general conversation as requested
    async def event_stream() -> AsyncIterator[str]:
        yield "event: status\ndata: " + json.dumps({"agent": "mark", "task": "incident_analysis"}) + "\n\n"
        try:
            jarvis = await _get_jarvis()
            stream_coro = (
                jarvis.stream(req.message, req.session_id, context={"user_name": req.user_name})
                if req.user_name
                else jarvis.stream(req.message, req.session_id)
            )
            async for chunk in stream_coro:
                text = str(chunk)
                if len(text) > 30:
                    import re
                    words = re.findall(r"\S+\s*|\n+", text)
                    for w in words:
                        yield "event: token\ndata: " + json.dumps({"content": w, "agent": "mark"}) + "\n\n"
                        await asyncio.sleep(0.015)
                else:
                    yield "event: token\ndata: " + json.dumps({"content": text, "agent": "mark"}) + "\n\n"
            yield "event: done\ndata: " + json.dumps({"session_id": req.session_id or "default"}) + "\n\n"
        except Exception as e:
            yield "event: error\ndata: " + json.dumps({"message": str(e)}) + "\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/speak")
async def speak(req: SpeakRequest):
    """Synthesize speech using ElevenLabs neural voice."""
    try:
        voice = await _get_voice_engine()
        audio_bytes = await voice.synthesize(req.text, req.voice)
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="ElevenLabs speech synthesis failed")
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        logger.error("MARK speak endpoint failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/status")
async def status():
    try:
        jarvis = await _get_jarvis()
        status_data = jarvis.get_status()
        status_data["voice_provider"] = "ElevenLabs"
        status_data["voices_available"] = list(ELEVENLABS_VOICES.keys())
        return status_data
    except Exception as e:
        logger.error("MARK status failed: %s", e)
        return {"status": "offline", "error": str(e)}


@router.get("/capabilities")
async def capabilities():
    """Return MARK's engine/service/connector/skill capability registry."""
    try:
        return load_default_registry().to_capabilities()
    except Exception as e:
        logger.error("MARK capability registry failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/connectors/status")
async def connector_status():
    """Return configured status for every MCP-managed connector."""
    return _get_mcp_hub().connector_status()


@router.get("/connectors/traces")
async def connector_traces(limit: int = 20):
    """Return recent outbound MCP connector traces."""
    return {"traces": _get_mcp_hub().latest_traces(limit=max(1, min(limit, 100)))}


@router.get("/connectors/{connector_id}/tools")
async def connector_tools(connector_id: str):
    """List tools exposed by a configured downstream MCP connector."""
    try:
        return {"connector_id": connector_id, "tools": await _get_mcp_hub().list_tools(connector_id)}
    except Exception as e:
        logger.error("MARK connector tool discovery failed: %s", e)
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.post("/connectors/{connector_id}/call")
async def connector_call(connector_id: str, req: MCPToolCallRequest):
    """Call a downstream MCP connector tool through the shared MCP client hub."""
    try:
        result = await _get_mcp_hub().call_tool(
            connector_id,
            req.tool_name,
            dict(req.arguments),
            require_approval=req.require_approval,
            approval_granted=req.approval_granted,
        )
        return {"connector_id": connector_id, "tool_name": req.tool_name, "result": result}
    except MCPPolicyError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except Exception as e:
        logger.error("MARK connector call failed: %s", e)
        raise HTTPException(status_code=502, detail=str(e)) from e
