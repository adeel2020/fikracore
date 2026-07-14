from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    session_id: str | None = None
    user_role: str | None = "Customer_Ops"


class Telemetry(BaseModel):
    memory_pct: int = Field(ge=0, le=100)
    token_cache_pct: int = Field(ge=0, le=100)
    context_window: str
    latency_ms: int = Field(ge=0)
    message_count: int = Field(ge=0)
    estimated_tokens: int = Field(ge=0)
    tokens_consumed: int = Field(default=0, ge=0)
    token_cost: float = Field(default=0.0, ge=0)
    tokens_per_second: float = Field(default=0.0, ge=0)


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    messages: list[ChatMessage]
    telemetry: Telemetry


class TelemetryResponse(BaseModel):
    session_id: str
    telemetry: Telemetry


class HealthResponse(BaseModel):
    status: str
    agent_mode: str


# ------------------------------------------------------------------
# SSE streaming event payloads
# ------------------------------------------------------------------
class SSEStatusEvent(BaseModel):
    """Emitted when a new agent starts working on a task."""
    type: Literal["status"] = "status"
    agent: str
    task: str
    task_index: int


class SSETokenEvent(BaseModel):
    """Emitted for each token/chunk of generated text."""
    type: Literal["token"] = "token"
    content: str
    agent: str


class SSEToolCallEvent(BaseModel):
    """Emitted when an agent invokes a tool."""
    type: Literal["tool_call"] = "tool_call"
    tool: str
    agent: str


class SSEDoneEvent(BaseModel):
    """Emitted when the crew finishes execution."""
    type: Literal["done"] = "done"
    session_id: str
    full_reply: str


class SSEErrorEvent(BaseModel):
    """Emitted when an error occurs during execution."""
    type: Literal["error"] = "error"
    message: str
