from __future__ import annotations

from engine_stack.engines.automation import AutomationEngine
from engine_stack.engines.calendar import CalendarEngine
from engine_stack.engines.codex_engineering import CodexEngineeringEngine
from engine_stack.engines.collaboration import CollaborationEngine
from engine_stack.engines.knowledge_base import KnowledgeBaseEngine
from engine_stack.engines.telecom_brain import TelecomBrainEngine as NormalizedTelecomBrainEngine
from engine_stack.router import EngineRouter
from engine_stack.telecom_brain import TelecomBrainEngine as CanonicalTelecomBrainEngine
from mcp_hub.policy import requires_approval
from mcp_hub.stdio import MCPStdioSession
from mcp_hub.trace import MCPCallTrace


def test_normalized_telecom_import_points_to_canonical_engine() -> None:
    assert NormalizedTelecomBrainEngine.__name__ == CanonicalTelecomBrainEngine.__name__
    assert [service.id for service in NormalizedTelecomBrainEngine().services] == [
        service.id for service in CanonicalTelecomBrainEngine().services
    ]


def test_registered_engine_shells_expose_manifests() -> None:
    assert KnowledgeBaseEngine().manifest.id == "knowledge_base"
    assert CollaborationEngine().manifest.id == "collaboration"
    assert CalendarEngine().manifest.id == "calendar"
    assert CodexEngineeringEngine().manifest.id == "codex_engineering"
    assert AutomationEngine().manifest.id == "automation"


def test_engine_router_uses_capability_registry() -> None:
    engine, trace = EngineRouter().route("summarize the telecom incident and alarm correlation")

    assert engine is not None
    assert engine.id == "telecom_brain"
    assert trace.selected_engine == "telecom_brain"


def test_mcp_hub_split_modules_reexport_current_contracts() -> None:
    assert MCPStdioSession.__name__ == "MCPStdioSession"
    assert MCPCallTrace.__name__ == "MCPCallTrace"
    assert requires_approval
