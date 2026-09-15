"""Agents Service — FastAPI application entry point. Runs on port 8001."""

import asyncio
import logging
import os
import sys
from pathlib import Path

if sys.platform == "darwin":
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ.setdefault("OMP_NUM_THREADS", "1")

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agenticaiops_shared.config import settings
from agenticaiops_shared.guardrails import setup_guardrails
from agenticaiops_shared.audit import AuditMiddleware

from core import auth as auth_router
from core import history as history_router
from qna import router as qna_router
from complaint import router as complaint_router
from storyteller import router as storyteller_router
from storyteller.conversation.router import router as incident_conversation_router
from correlation.router import router as incident_registry_router
from rag import router as rag_router
from jarvis import router as jarvis_router
from core import audit as audit_router
from engine_stack.engines.telecom_brain.api import capability_router

logger = logging.getLogger(__name__)

setup_guardrails()

app = FastAPI(title="AgenticAIOPs Agents Service", version="0.1.0")

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(auth_router.router)
app.include_router(history_router.router)
app.include_router(qna_router.router)
app.include_router(complaint_router.router)
app.include_router(storyteller_router.router)
app.include_router(incident_conversation_router)
app.include_router(incident_registry_router)
app.include_router(rag_router.router)
app.include_router(jarvis_router.router)
app.include_router(audit_router.router)
app.include_router(capability_router)

app.add_middleware(AuditMiddleware)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "agents", "version": "0.1.0"}


async def _init_background():
    from agenticaiops_shared.database.db import init_db
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database init skipped: {e}")

    from qna.kg_retriever import kg_retriever
    try:
        await asyncio.to_thread(kg_retriever.initialize)
        logger.info("KG Retriever initialized")
    except Exception as e:
        logger.error(f"KG Retriever init failed: {e}")

    from storyteller.datastory.crewai_storyteller import init_storyteller
    try:
        agent = init_storyteller()
        if agent:
            logger.info("Storyteller agent ready")
    except Exception as e:
        logger.warning(f"Storyteller not available: {e}")

    from jarvis.core import JARVIS
    try:
        jarvis = JARVIS()
        await jarvis.initialize()
        logger.info("JARVIS initialized")
    except Exception as e:
        logger.error(f"JARVIS init failed: {e}")


@app.on_event("startup")
async def startup():
    asyncio.create_task(_init_background())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, log_level="info")
