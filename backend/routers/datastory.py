"""FastAPI router for the Data Storyteller and Semantic Cloud feature.

Endpoints
---------
POST /api/datastory/upload
    Trigger the semantic decomposition pipeline on the SSoT file in the
    background.

GET  /api/datastory/dashboard-feed
    Return the dual-stream payload (canvas cloud data + AI executive brief).

GET  /api/datastory/knowledge-graph-state
    Return the persisted knowledge-graph column state.

PUT  /api/datastory/knowledge-graph-state
    Persist the knowledge-graph column state.

Registration
------------
Add to ``backend/main.py``::

    from backend.routers import datastory as datastory_router
    app.include_router(datastory_router.router)
"""

from datetime import datetime, timezone
from pathlib import Path

import joblib
import yaml
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from backend.config import settings
from backend.datastory.pipeline.engine import MODEL_PATH, run_semantic_decomposition_engine
from backend.datastory.storyteller_agent import DataStorytellerAgent
from backend.datastory.tools.cache_retriever import DataStoryCacheRetriever

router = APIRouter(prefix="/api/datastory", tags=["Data Storyteller"])

KG_STATE_PATH = Path(__file__).resolve().parent.parent / "datastory" / "data" / "knowledge_graph_state.yaml"


class UploadResponse(BaseModel):
    status: str


class ClusterStory(BaseModel):
    id: int
    theme: str
    volume: str
    dominant_axis: str
    exemplar: str
    anomalies: list[str]
    summary: str
    complaints_count: int
    service_journeys: list[str]
    ticket_queues: list[str]
    reassigned_to: list[str]


class DashboardFeedResponse(BaseModel):
    ui_cloud_data: list[dict]
    ai_executive_brief: str
    cluster_stories: list[ClusterStory]
    eigenvalues: list[float]
    available_fields: list[str]


def _build_cluster_stories(narrative_data: dict) -> list[ClusterStory]:
    """Build per-cluster story cards from the narrative stream data."""
    stories: list[ClusterStory] = []
    axis = narrative_data.get("dominant_operational_axis", "N/A")
    for i, c in enumerate(narrative_data.get("clusters", [])):
        theme = c.get("theme", "Unknown")
        volume = c.get("volume", "0%")
        exemplar = c.get("highest_centrality_example", "")
        anomalies: list[str] = c.get("anomalies_to_investigate", [])
        summary = (
            f"Cluster **{theme}** accounts for **{volume}** "
            f"of all operational tickets under the "
            f"**{axis}** axis.\n\n"
            f"**Most representative ticket:**\n"
            f"`{exemplar}`"
        )
        if anomalies:
            summary += (
                f"\n\n**{len(anomalies)} anomalous ticket(s)** "
                f"flagged for review."
            )
        stories.append(
            ClusterStory(
                id=i,
                theme=theme,
                volume=volume,
                dominant_axis=axis,
                exemplar=exemplar,
                anomalies=anomalies,
                summary=summary,
                complaints_count=c.get("complaints_count", 0),
                service_journeys=c.get("service_journeys", []),
                ticket_queues=c.get("ticket_queues", []),
                reassigned_to=c.get("reassigned_to", []),
            )
        )
    return stories


@router.post("/upload", response_model=UploadResponse)
async def manual_ssot_upload() -> UploadResponse:
    """Trigger the semantic decomposition pipeline synchronously.

    The pipeline reads ``datastory/data/operational_data.xlsx``, computes
    TF-IDF → SVD → KMeans, and persists both the augmented Parquet cache
    and the serialised pipeline model.
    """
    run_semantic_decomposition_engine(None)
    return UploadResponse(status="Ingestion engine completed successfully")


@router.get("/dashboard-feed", response_model=DashboardFeedResponse)
async def get_dashboard_data() -> DashboardFeedResponse:
    """Return the dual-stream payload for the Semantic Cloud dashboard.

    * ``ui_cloud_data`` — per-ticket co-ordinates and metadata for the
      front-end cloud visualisation.
    * ``ai_executive_brief`` — a markdown narrative synthesised by the
      Data Storyteller agent.
    * ``cluster_stories`` — per-cluster story cards for the chat bot.
    """
    try:
        retriever = DataStoryCacheRetriever()
        canvas_data, narrative_data, available_fields = retriever.get_dual_streams()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Load eigenvalues from pipeline state
    eigenvalues: list[float] = []
    if MODEL_PATH.exists():
        try:
            state = joblib.load(MODEL_PATH)
            eigenvalues = state.get("eigenvalues", [])
        except Exception:
            eigenvalues = []

    agent = DataStorytellerAgent()
    executive_story = agent.generate_story(narrative_data)
    cluster_stories = _build_cluster_stories(narrative_data)

    return DashboardFeedResponse(
        ui_cloud_data=canvas_data,
        ai_executive_brief=executive_story,
        cluster_stories=cluster_stories,
        eigenvalues=eigenvalues,
        available_fields=available_fields,
    )


class KGValue(BaseModel):
    value: str
    count: int


class KGColumn(BaseModel):
    field: str
    label: str
    values: list[KGValue]
    x: float | None = None
    y: float | None = None


class KGEdge(BaseModel):
    source_col: str
    source_val: str
    target_col: str
    target_val: str
    weight: int


class KGSavedState(BaseModel):
    columns: list[KGColumn]
    edges: list[KGEdge]


@router.get("/knowledge-graph-state")
async def get_knowledge_graph_state() -> KGSavedState | dict:
    if not KG_STATE_PATH.exists():
        return KGSavedState(columns=[], edges=[])
    try:
        raw = yaml.safe_load(KG_STATE_PATH.read_text())
        return KGSavedState(**raw)
    except Exception:
        return KGSavedState(columns=[], edges=[])


class ClusterStoryRequest(BaseModel):
    cluster_name: str


class ClusterStoryResponse(BaseModel):
    summary: str


@router.post("/cluster-story", response_model=ClusterStoryResponse)
async def get_cluster_story(req: ClusterStoryRequest) -> ClusterStoryResponse:
    """Generate a strict 3-sentence NOC executive summary for a single
    operational cluster using the CrewAI Data Storyteller pipeline.

    The endpoint:
    1. Reads ``semantic_state.parquet`` and filters to *cluster_name*.
    2. Identifies the Operational Norm (highest Centrality_Score) and
       Systemic Friction (Anomaly_Flag == True | Rejected).
    3. Feeds the curated payload into a CrewAI Agent/Task pipeline.
    4. Returns exactly 3 sentences.

    If CrewAI is unavailable or the LLM call fails, a deterministic
    data-grounded fallback is returned.
    """
    from backend.datastory.crewai_storyteller import run_cluster_story

    summary = run_cluster_story(cluster_name=req.cluster_name)
    return ClusterStoryResponse(summary=summary)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


_STORY_PROMPT = (
    "You are an expert operational storyteller with deep domain knowledge of telecom "
    "ticket management. The user wants you to tell a story about their operational data.\n\n"
    "Here is the semantic narrative context from their ticket system:\n\n"
    "{narrative}\n\n"
    "Here is the executive brief summary:\n\n{executive_brief}\n\n"
    "User question: {message}\n\n"
    "Respond in a storytelling style — use vivid narrative, concrete examples from the data, "
    "and insightful analysis. Write in markdown. Keep responses concise (2-4 paragraphs)."
)


@router.post("/chat", response_model=ChatResponse)
async def chat_with_storyteller(req: ChatRequest) -> ChatResponse:
    """Chat with the Data Storyteller — generates a storytelling response
    grounded in the semantic narrative data."""
    try:
        retriever = DataStoryCacheRetriever()
        _, narrative_data, _ = retriever.get_dual_streams()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    agent = DataStorytellerAgent(temperature=0.7)
    executive_brief = agent.generate_story(narrative_data)

    prompt = _STORY_PROMPT.format(
        narrative=narrative_data,
        executive_brief=executive_brief,
        message=req.message,
    )

    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key or "ollama", base_url=settings.openai_api_base)
        response = client.chat.completions.create(
            model=settings.openai_model or "gpt-4o-mini",
            temperature=0.7,
            messages=[
                {"role": "system", "content": "You are a data storyteller. Respond in markdown."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1024,
        )
        content = response.choices[0].message.content
        return ChatResponse(response=content.strip() if content else "No story generated.")
    except Exception as e:
        return ChatResponse(
            response=f"I'm running in offline mode, but here's what I can tell you:\n\n"
            f"The data contains **{narrative_data.get('total_tickets', 'N/A')}** tickets "
            f"across **{len(narrative_data.get('clusters', []))}** clusters, "
            f"with a dominant axis of **{narrative_data.get('dominant_operational_axis', 'N/A')}**."
        )


@router.put("/knowledge-graph-state")
async def put_knowledge_graph_state(state: KGSavedState) -> dict:
    KG_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with KG_STATE_PATH.open("w") as f:
        yaml.dump(
            state.model_dump() | {"updated_at": datetime.now(timezone.utc).isoformat()},
            f,
            default_flow_style=False,
            sort_keys=False,
        )
    return {"status": "saved"}


class GenerateNarrativeRequest(BaseModel):
    text: str
    instruction: str | None = None


class GenerateNarrativeResponse(BaseModel):
    text: str


@router.post("/generate-narrative", response_model=GenerateNarrativeResponse)
async def generate_narrative(req: GenerateNarrativeRequest) -> GenerateNarrativeResponse:
    """Refine or generate slide narrative text based on the current text and instruction."""
    from openai import OpenAI

    system_prompt = (
        "You are an expert telecom operational data storyteller. "
        "The user wants you to refine or expand a section of their presentation narrative.\n\n"
        "Instructions:\n"
        "1. Write clean, professional, concise, and structured narrative text.\n"
        "2. Use clean markdown formatting (e.g. bold, italics, bullets) when appropriate.\n"
        "3. Keep the output focused, technical, and directly responding to the user's instructions.\n"
        "4. Do NOT wrap your response in markdown code blocks (like ```markdown ... ```). Output the raw formatted text directly."
    )

    user_prompt = f"Current text:\n{req.text}\n\n"
    if req.instruction:
        user_prompt += f"Instruction: {req.instruction}\n\n"
    else:
        user_prompt += "Instruction: Polish this text for clarity and professional tone.\n\n"
        
    user_prompt += "Provide the updated text below:"

    try:
        client = OpenAI(api_key=settings.openai_api_key or "ollama", base_url=settings.openai_api_base)
        response = client.chat.completions.create(
            model=settings.openai_model or "gpt-4o-mini",
            temperature=0.7,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1024,
        )
        content = response.choices[0].message.content
        return GenerateNarrativeResponse(text=content.strip() if content else req.text)
    except Exception as e:
        fallback = req.text
        if req.instruction:
            fallback += f"\n\n[Offline Mode: AI could not execute instruction: '{req.instruction}']"
        return GenerateNarrativeResponse(text=fallback)
