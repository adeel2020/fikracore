"""
JARVIS API Router - RESTful & Streaming Endpoints
Provides HTTP API for JARVIS AI assistant.
"""

from __future__ import annotations

import json
import asyncio
import logging
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.jarvis.core import JARVIS, JARVISConfig

logger = logging.getLogger("jarvis.router")

router = APIRouter(prefix="/jarvis", tags=["JARVIS"])

# ==========================================
# JARVIS SINGLETON
# ==========================================

_jarvis_instance: JARVIS | None = None


async def get_jarvis() -> JARVIS:
    """Get or initialize JARVIS singleton."""
    global _jarvis_instance
    if _jarvis_instance is None:
        _jarvis_instance = JARVISConfig()
        jarvis = JARVIS(_jarvis_instance)
        await jarvis.initialize()
        _jarvis_instance = jarvis
    return _jarvis_instance


# ==========================================
# REQUEST/RESPONSE MODELS
# ==========================================

class JarvisRequest(BaseModel):
    """JARVIS query request."""
    query: str
    session_id: str | None = None
    context: dict | None = None
    stream: bool = False


class JarvisResponse(BaseModel):
    """JARVIS query response."""
    response: str
    status: str
    latency_ms: float
    power_used: str | None = None


class JarvisStatusResponse(BaseModel):
    """JARVIS status response."""
    name: str
    version: str
    status: str
    uptime_seconds: float
    queries_processed: int
    power_ups_active: list[str]
    success_rate: float
    data_residency: str
    neurosol_sync: bool


class VoiceRequest(BaseModel):
    """Voice synthesis request."""
    text: str
    voice: str = "alloy"
    speed: float = 1.0


class CodeRequest(BaseModel):
    """Code generation request."""
    query: str
    language: str = "python"
    context: dict | None = None


# ==========================================
# MAIN JARVIS ENDPOINTS
# ==========================================

@router.post("/query", response_model=JarvisResponse)
async def jarvis_query(req: JarvisRequest):
    """Send a query to JARVIS and get a response."""
    import time
    start = time.time()
    
    jarvis = await get_jarvis()
    
    result = await jarvis.process(
        query=req.query,
        session_id=req.session_id,
        context=req.context,
        stream=False,
    )
    
    latency = (time.time() - start) * 1000
    
    return JarvisResponse(
        response=result,
        status="success",
        latency_ms=latency,
    )


@router.post("/stream")
async def jarvis_stream(req: JarvisRequest):
    """Stream JARVIS response token by token."""
    jarvis = await get_jarvis()
    
    async def generate():
        async for chunk in jarvis.stream(
            query=req.query,
            session_id=req.session_id,
            context=req.context,
        ):
            data = json.dumps({"choices": [{"delta": {"content": chunk}}]})
            yield f"data: {data}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "cache-control": "no-cache",
            "x-accel-buffering": "no",
        },
    )


@router.get("/status", response_model=JarvisStatusResponse)
async def jarvis_status():
    """Get JARVIS system status."""
    jarvis = await get_jarvis()
    status = jarvis.get_status()
    return JarvisStatusResponse(**status)


@router.post("/shutdown")
async def jarvis_shutdown():
    """Gracefully shutdown JARVIS."""
    global _jarvis_instance
    if _jarvis_instance:
        await _jarvis_instance.shutdown()
        _jarvis_instance = None
    return {"status": "shutdown_complete"}


@router.post("/reinitialize")
async def jarvis_reinitialize():
    """Reinitialize JARVIS with fresh state."""
    global _jarvis_instance
    if _jarvis_instance:
        await _jarvis_instance.shutdown()
        _jarvis_instance = None
    
    jarvis = await get_jarvis()
    return {"status": "reinitialized", "powers": jarvis.telemetry.power_ups_active}


# ==========================================
# VOICE ENDPOINTS
# ==========================================

@router.post("/voice/synthesize")
async def voice_synthesize(req: VoiceRequest):
    """Synthesize speech from text."""
    jarvis = await get_jarvis()
    voice_engine = jarvis._superpowers.get("voice")
    
    if voice_engine is None:
        raise HTTPException(status_code=503, detail="Voice engine not available")
    
    audio_data = await voice_engine.synthesize(req.text)
    
    return StreamingResponse(
        iter([audio_data]),
        media_type="audio/wav",
        headers={"Content-Disposition": f"attachment; filename=jarvis_speech.wav"}
    )


@router.post("/voice/transcribe")
async def voice_transcribe(audio: UploadFile = File(...)):
    """Transcribe audio to text."""
    jarvis = await get_jarvis()
    voice_engine = jarvis._superpowers.get("voice")
    
    if voice_engine is None:
        raise HTTPException(status_code=503, detail="Voice engine not available")
    
    audio_data = await audio.read()
    text = await voice_engine.transcribe(audio_data)
    
    return {"transcription": text}


# ==========================================
# VISION ENDPOINTS
# ==========================================

@router.post("/vision/analyze")
async def vision_analyze(
    query: str = Form("Analyze this image"),
    image: UploadFile = File(...),
):
    """Analyze an image."""
    jarvis = await get_jarvis()
    vision_engine = jarvis._superpowers.get("vision")
    
    if vision_engine is None:
        raise HTTPException(status_code=503, detail="Vision engine not available")
    
    # Save image temporarily
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        content = await image.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        result = await vision_engine.process(
            query,
            context={"image_path": tmp_path}
        )
        return {"analysis": result}
    finally:
        os.unlink(tmp_path)


@router.post("/vision/ocr")
async def vision_ocr(file: UploadFile = File(...)):
    """Extract text from image/document."""
    jarvis = await get_jarvis()
    vision_engine = jarvis._superpowers.get("vision")
    
    if vision_engine is None:
        raise HTTPException(status_code=503, detail="Vision engine not available")
    
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        text = await vision_engine.extract_text(tmp_path)
        return {"text": text}
    finally:
        os.unlink(tmp_path)


# ==========================================
# CODE ENDPOINTS
# ==========================================

@router.post("/code/generate")
async def code_generate(req: CodeRequest):
    """Generate code from natural language."""
    jarvis = await get_jarvis()
    code_engine = jarvis._superpowers.get("code")
    
    if code_engine is None:
        raise HTTPException(status_code=503, detail="Code engine not available")
    
    result = await code_engine.generate_code(req.query, req.context)
    return {"code": result}


@router.post("/code/review")
async def code_review(req: CodeRequest):
    """Review code for issues."""
    jarvis = await get_jarvis()
    code_engine = jarvis._superpowers.get("code")
    
    if code_engine is None:
        raise HTTPException(status_code=503, detail="Code engine not available")
    
    result = await code_engine.review_code(req.query, req.context)
    return {"review": result}


@router.post("/code/debug")
async def code_debug(req: CodeRequest):
    """Debug code issues."""
    jarvis = await get_jarvis()
    code_engine = jarvis._superpowers.get("code")
    
    if code_engine is None:
        raise HTTPException(status_code=503, detail="Code engine not available")
    
    result = await code_engine.debug_code(req.query, req.context)
    return {"solution": result}


# ==========================================
# MONITORING ENDPOINTS
# ==========================================

@router.get("/monitoring/health")
async def monitoring_health():
    """Get system health."""
    jarvis = await get_jarvis()
    monitoring = jarvis._superpowers.get("monitoring")
    
    if monitoring is None:
        raise HTTPException(status_code=503, detail="Monitoring engine not available")
    
    result = await monitoring.get_system_health()
    return {"health": result}


@router.get("/monitoring/cpu")
async def monitoring_cpu():
    """Get CPU metrics."""
    jarvis = await get_jarvis()
    monitoring = jarvis._superpowers.get("monitoring")
    
    if monitoring is None:
        raise HTTPException(status_code=503, detail="Monitoring engine not available")
    
    result = await monitoring.get_cpu_metrics()
    return {"cpu": result}


@router.get("/monitoring/memory")
async def monitoring_memory():
    """Get memory metrics."""
    jarvis = await get_jarvis()
    monitoring = jarvis._superpowers.get("monitoring")
    
    if monitoring is None:
        raise HTTPException(status_code=503, detail="Monitoring engine not available")
    
    result = await monitoring.get_memory_metrics()
    return {"memory": result}


@router.get("/monitoring/dashboard")
async def monitoring_dashboard():
    """Get monitoring dashboard."""
    jarvis = await get_jarvis()
    monitoring = jarvis._superpowers.get("monitoring")
    
    if monitoring is None:
        raise HTTPException(status_code=503, detail="Monitoring engine not available")
    
    result = await monitoring.get_dashboard()
    return {"dashboard": result}


# ==========================================
# KNOWLEDGE GRAPH ENDPOINTS
# ==========================================

@router.post("/kg/query")
async def kg_query(entity: str = Form(...)):
    """Query knowledge graph entity."""
    jarvis = await get_jarvis()
    kg_engine = jarvis._superpowers.get("knowledge_graph")
    
    if kg_engine is None:
        raise HTTPException(status_code=503, detail="Knowledge graph engine not available")
    
    result = await kg_engine.query_entity(entity)
    return {"entity": entity, "data": result}


@router.get("/kg/stats")
async def kg_stats():
    """Get knowledge graph statistics."""
    jarvis = await get_jarvis()
    kg_engine = jarvis._superpowers.get("knowledge_graph")
    
    if kg_engine is None:
        raise HTTPException(status_code=503, detail="Knowledge graph engine not available")
    
    result = await kg_engine.get_graph_stats()
    return {"stats": result}


# ==========================================
# SECURITY ENDPOINTS
# ==========================================

@router.get("/security/status")
async def security_status():
    """Get security status."""
    jarvis = await get_jarvis()
    security = jarvis._superpowers.get("security")
    
    if security is None:
        raise HTTPException(status_code=503, detail="Security engine not available")
    
    return {"security": security.get_security_status()}


@router.post("/security/validate")
async def security_validate(query: str = Form(...)):
    """Validate query for security."""
    jarvis = await get_jarvis()
    security = jarvis._superpowers.get("security")
    
    if security is None:
        raise HTTPException(status_code=503, detail="Security engine not available")
    
    is_safe = await security.validate_query(query)
    return {"query": query, "is_safe": is_safe}
