"""
J.A.R.V.I.S. Core Engine - The Brain
Multi-agent orchestration with superpowers for AgenticAIOPs.
"""

from __future__ import annotations

import os
import time
import json
import asyncio
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Optional
from datetime import datetime

from pydantic import BaseModel

logger = logging.getLogger("jarvis.core")

# ==========================================
# JARVIS CONFIGURATION
# ==========================================

@dataclass
class JARVISConfig:
    """JARVIS system configuration."""
    name: str = "JARVIS"
    version: str = "3.0.0"
    model: str = "ollama/llama3.1:8b"
    api_key: str | None = None
    api_base: str = "http://localhost:11434"
    embedding_model: str = "text-embedding-3-small"
    max_context_tokens: int = 100_000
    voice_enabled: bool = True
    vision_enabled: bool = True
    autopilot_enabled: bool = True
    security_level: str = "maximum"  # maximum, high, standard
    data_residency: str = "UAE"  # UAE data residency compliance
    neurosol_sync: bool = True  # UAE sovereign AI sync


# ==========================================
# JARVIS STATUS & TELEMETRY
# ==========================================

class JARVISStatus(str, Enum):
    OFFLINE = "offline"
    INITIALIZING = "initializing"
    ONLINE = "online"
    PROCESSING = "processing"
    ERROR = "error"


class PowerUp(str, Enum):
    VOICE = "voice"
    VISION = "vision"
    CODE = "code"
    RAG = "rag"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    MONITORING = "monitoring"
    AUTOPILOT = "autopilot"
    SECURITY = "security"
    ANALYTICS = "analytics"
    ORCHESTRATION = "orchestration"


@dataclass
class JarvisTelemetry:
    """Real-time JARVIS telemetry."""
    status: JARVISStatus = JARVISStatus.OFFLINE
    uptime: float = 0.0
    queries_processed: int = 0
    active_agents: int = 0
    power_ups_active: list[str] = field(default_factory=list)
    memory_usage_pct: int = 0
    cpu_usage_pct: int = 0
    latency_ms: float = 0.0
    last_query: str = ""
    last_query_time: float = 0.0
    error_count: int = 0
    success_rate: float = 100.0


# ==========================================
# JARVIS CORE ENGINE
# ==========================================

class JARVIS:
    """
    J.A.R.V.I.S. - Just A Rather Very Intelligent System
    
    The ultimate AI assistant with superpowers:
    - Voice synthesis & recognition
    - Vision & document analysis
    - Code generation & debugging
    - RAG (Retrieval Augmented Generation)
    - Knowledge Graph traversal
    - Real-time monitoring
    - Autopilot mode
    - Security guardrails
    - Multi-agent orchestration
    - UAE sovereign AI compliance
    """

    def __init__(self, config: JARVISConfig | None = None):
        self.config = config or JARVISConfig()
        self.status = JARVISStatus.OFFLINE
        self.telemetry = JarvisTelemetry()
        self._start_time = time.time()
        self._superpowers: dict[str, Any] = {}
        self._initialized = False
        
        logger.info(f"[{self.config.name}] Initializing v{self.config.version}...")

    async def initialize(self) -> None:
        """Initialize all JARVIS superpowers."""
        self.status = JARVISStatus.INITIALIZING
        
        try:
            # Initialize superpowers in parallel
            from ..jarvis.superpowers.voice import VoiceEngine
            from ..jarvis.superpowers.vision import VisionEngine
            from ..jarvis.superpowers.code_gen import CodeEngine
            from ..jarvis.superpowers.rag_engine import RAGEngine
            from ..jarvis.superpowers.knowledge_graph import KnowledgeGraphEngine
            from ..jarvis.superpowers.monitoring import MonitoringEngine
            from ..jarvis.superpowers.autopilot import AutopilotEngine
            from ..jarvis.superpowers.security import SecurityEngine
            
            self._superpowers = {
                PowerUp.VOICE: VoiceEngine(self.config) if self.config.voice_enabled else None,
                PowerUp.VISION: VisionEngine(self.config) if self.config.vision_enabled else None,
                PowerUp.CODE: CodeEngine(self.config),
                PowerUp.RAG: RAGEngine(self.config),
                PowerUp.KNOWLEDGE_GRAPH: KnowledgeGraphEngine(self.config),
                PowerUp.MONITORING: MonitoringEngine(self.config),
                PowerUp.AUTOPILOT: AutopilotEngine(self.config) if self.config.autopilot_enabled else None,
                PowerUp.SECURITY: SecurityEngine(self.config),
            }
            
            # Initialize each superpower
            init_tasks = []
            for name, engine in self._superpowers.items():
                if engine and hasattr(engine, 'initialize'):
                    init_tasks.append(self._init_superpower(name, engine))
            
            if init_tasks:
                await asyncio.gather(*init_tasks, return_exceptions=True)
            
            self.status = JARVISStatus.ONLINE
            self._initialized = True
            self.telemetry.power_ups_active = [p.value for p, e in self._superpowers.items() if e is not None]
            
            logger.info(f"[{self.config.name}] Online. {len(self.telemetry.power_ups_active)} superpowers active.")
            
        except Exception as e:
            self.status = JARVISStatus.ERROR
            logger.error(f"[{self.config.name}] Initialization failed: {e}")
            raise

    async def _init_superpower(self, name: PowerUp, engine: Any) -> None:
        """Initialize a single superpower with error handling."""
        try:
            await engine.initialize()
            logger.info(f"[{self.config.name}] Superpower '{name.value}' initialized.")
        except Exception as e:
            logger.warning(f"[{self.config.name}] Superpower '{name.value}' failed to init: {e}")
            self._superpowers[name] = None

    # ==========================================
    # MAIN QUERY PROCESSING
    # ==========================================

    async def process(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        """
        Process a user query through JARVIS superpowers.
        
        Routes to appropriate superpowers based on query intent:
        - Voice commands -> VoiceEngine
        - Image/file analysis -> VisionEngine
        - Code requests -> CodeEngine
        - Knowledge queries -> RAGEngine + KnowledgeGraphEngine
        - System monitoring -> MonitoringEngine
        - Complex tasks -> AutopilotEngine (multi-agent)
        """
        start_time = time.time()
        self.status = JARVISStatus.PROCESSING
        self.telemetry.queries_processed += 1
        self.telemetry.last_query = query
        self.telemetry.last_query_time = time.time()
        
        try:
            # Security check first
            security = self._superpowers.get(PowerUp.SECURITY)
            if security:
                is_safe = await security.validate_query(query)
                if not is_safe:
                    return "Query blocked by JARVIS security protocols."
            
            # Route to appropriate superpower
            route = self._route_query(query, context)
            logger.info(f"[{self.config.name}] Routing to: {route}")
            
            # Execute with the routed superpower
            result = await self._execute_power(route, query, session_id, context)
            
            self.telemetry.latency_ms = (time.time() - start_time) * 1000
            self.status = JARVISStatus.ONLINE
            
            return result
            
        except Exception as e:
            self.telemetry.error_count += 1
            self.status = JARVISStatus.ERROR
            logger.error(f"[{self.config.name}] Processing error: {e}")
            return f"JARVIS encountered an error: {str(e)}"
        finally:
            # Update success rate
            total = self.telemetry.queries_processed
            errors = self.telemetry.error_count
            self.telemetry.success_rate = ((total - errors) / total * 100) if total > 0 else 100.0

    def _route_query(self, query: str, context: dict[str, Any] | None) -> PowerUp:
        """Intelligent routing based on query content."""
        lower_query = query.lower()
        
        # Voice commands
        voice_keywords = ["speak", "say aloud", "voice", "audio", "listen"]
        if any(kw in lower_query for kw in voice_keywords):
            return PowerUp.VOICE
        
        # Vision tasks
        vision_keywords = ["analyze image", "look at", "screenshot", "document", "pdf", "ocr"]
        if any(kw in lower_query for kw in vision_keywords) or (context and context.get("has_image")):
            return PowerUp.VISION
        
        # Code tasks
        code_keywords = ["write code", "debug", "function", "class", "script", "implement", "refactor"]
        if any(kw in lower_query for kw in code_keywords):
            return PowerUp.CODE
        
        # Monitoring
        monitor_keywords = ["status", "health", "metrics", "monitor", "dashboard", "telemetry"]
        if any(kw in lower_query for kw in monitor_keywords):
            return PowerUp.MONITORING
        
        # Knowledge graph
        kg_keywords = ["graph", "relationship", "entity", "connection", "network"]
        if any(kw in lower_query for kw in kg_keywords):
            return PowerUp.KNOWLEDGE_GRAPH
        
        # Complex multi-step tasks
        complex_keywords = ["plan", "orchestrate", "multi-agent", "complex", "workflow"]
        if any(kw in lower_query for kw in complex_keywords):
            return PowerUp.AUTOPILOT
        
        # Default to RAG for knowledge queries
        return PowerUp.RAG

    async def _execute_power(
        self,
        power: PowerUp,
        query: str,
        session_id: str | None,
        context: dict[str, Any] | None,
    ) -> str:
        """Execute a superpower."""
        engine = self._superpowers.get(power)
        
        if engine is None:
            # Fallback to RAG
            engine = self._superpowers.get(PowerUp.RAG)
            if engine is None:
                return "JARVIS is not fully initialized. Please try again."
        
        return await engine.process(query, session_id=session_id, context=context)

    # ==========================================
    # STREAMING PROCESSING
    # ==========================================

    async def stream(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Stream JARVIS responses token by token."""
        self.status = JARVISStatus.PROCESSING
        
        try:
            # Check if any superpower supports streaming
            power = self._route_query(query, context)
            engine = self._superpowers.get(power)
            
            if engine and hasattr(engine, 'stream'):
                async for chunk in engine.stream(query, session_id=session_id, context=context):
                    yield chunk
            else:
                # Fallback: yield complete response
                result = await self.process(query, session_id, context)
                yield result
                
        except Exception as e:
            yield f"JARVIS streaming error: {str(e)}"
        finally:
            self.status = JARVISStatus.ONLINE

    # ==========================================
    # SYSTEM STATUS & CONTROL
    # ==========================================

    def get_status(self) -> dict[str, Any]:
        """Get comprehensive JARVIS status."""
        self.telemetry.uptime = time.time() - self._start_time
        return {
            "name": self.config.name,
            "version": self.config.version,
            "status": self.status.value,
            "uptime_seconds": self.telemetry.uptime,
            "queries_processed": self.telemetry.queries_processed,
            "active_agents": self.telemetry.active_agents,
            "power_ups_active": self.telemetry.power_ups_active,
            "memory_usage_pct": self.telemetry.memory_usage_pct,
            "latency_ms": self.telemetry.latency_ms,
            "success_rate": self.telemetry.success_rate,
            "error_count": self.telemetry.error_count,
            "data_residency": self.config.data_residency,
            "neurosol_sync": self.config.neurosol_sync,
        }

    async def shutdown(self) -> None:
        """Gracefully shutdown JARVIS."""
        logger.info(f"[{self.config.name}] Shutting down...")
        self.status = JARVISStatus.OFFLINE
        
        # Shutdown all superpowers
        for name, engine in self._superpowers.items():
            if engine and hasattr(engine, 'shutdown'):
                try:
                    await engine.shutdown()
                except Exception as e:
                    logger.warning(f"[{self.config.name}] Error shutting down {name.value}: {e}")
        
        logger.info(f"[{self.config.name}] Offline.")
