import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routers import api_router, analytics, history, sft, whatsapp_router
from backend.routers import datastory as datastory_router
from backend.rag.routers import rag as rag_router
from backend.routers.tts import router as tts_router
from backend.routers.storyteller_chat import router as storyteller_chat_router
from backend.routers.realtime_protocol import router as realtime_router
from backend.agent.guardrails import setup_guardrails
from backend.jarvis.router import router as jarvis_router

logger = logging.getLogger(__name__)

setup_guardrails()

app = FastAPI(
    title="Data Storyteller API",
    description="Backend services for the Data Storyteller platform",
    version="0.1.0",
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router.router)
app.include_router(analytics.router)
app.include_router(history.router)
app.include_router(sft.router)
app.include_router(whatsapp_router.router)
app.include_router(rag_router.router)
app.include_router(datastory_router.router)
app.include_router(tts_router)
app.include_router(storyteller_chat_router)
app.include_router(realtime_router)
app.include_router(jarvis_router)


@app.get("/health")
async def root_health() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
async def startup():
    from backend.datastory.crewai_storyteller import init_storyteller
    from backend.datastory.sync_watcher import watch_kg_state
    from backend.routers.realtime_protocol import warmup_models

    agent = init_storyteller()
    if agent is not None:
        logger.info("Storyteller agent ready")
    else:
        logger.warning("Storyteller agent not available (CrewAI missing?)")

    asyncio.create_task(watch_kg_state())

    # Pre-warm Whisper and Kokoro so first utterance has no model-load delay
    asyncio.create_task(warmup_models())
    
    # Pre-initialize Knowledge Graph Retriever and embeddings
    try:
        from backend.agent.kg_retriever import kg_retriever
        logger.info("Pre-initializing Knowledge Graph Retriever...")
        await asyncio.to_thread(kg_retriever.initialize)
        logger.info("Knowledge Graph Retriever pre-initialized successfully")
    except Exception as e:
        logger.error(f"Failed to pre-initialize Knowledge Graph Retriever: {e}")

    # Initialize JARVIS
    from backend.jarvis.core import JARVIS
    jarvis = JARVIS()
    await jarvis.initialize()
    logger.info("JARVIS initialized and ready")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
