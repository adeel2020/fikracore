from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ConnectorManifest:
    id: str
    name: str
    kind: str
    transport: str = "mcp"
    managed_by: str = "mcp_client_hub"
    owner_engine: str | None = None
    description: str = ""
    env: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    fallback_transports: list[str] = field(default_factory=list)
    status: str = "planned"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ServiceManifest:
    id: str
    name: str
    engine: str
    description: str = ""
    connectors: list[str] = field(default_factory=list)
    consumes: list[str] = field(default_factory=list)
    produces: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    status: str = "planned"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EngineManifest:
    id: str
    name: str
    description: str = ""
    routing_intents: list[str] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    connectors: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    status: str = "planned"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SkillDocument:
    id: str
    title: str
    engine: str
    services: list[str] = field(default_factory=list)
    connectors: list[str] = field(default_factory=list)
    fcaps_lens: list[str] = field(default_factory=list)
    output_modes: list[str] = field(default_factory=list)
    requires_approval: bool = False
    body: str = ""
    path: str = ""
    raw_frontmatter: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MarkRegistry:
    id: str
    name: str
    version: str
    description: str
    engines: dict[str, EngineManifest]
    services: dict[str, ServiceManifest]
    connectors: dict[str, ConnectorManifest]
    skills: dict[str, SkillDocument]
    principles: list[str] = field(default_factory=list)
    runtime: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_capabilities(self) -> dict[str, Any]:
        """Return a stable API shape for UI/debug capability discovery."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "principles": self.principles,
            "runtime": self.runtime,
            "engines": [
                {
                    "id": engine.id,
                    "name": engine.name,
                    "description": engine.description,
                    "routing_intents": engine.routing_intents,
                    "services": engine.services,
                    "connectors": engine.connectors,
                    "skills": engine.skills,
                    "permissions": engine.permissions,
                    "status": engine.status,
                }
                for engine in self.engines.values()
            ],
            "services": [
                {
                    "id": service.id,
                    "name": service.name,
                    "engine": service.engine,
                    "description": service.description,
                    "connectors": service.connectors,
                    "consumes": service.consumes,
                    "produces": service.produces,
                    "permissions": service.permissions,
                    "status": service.status,
                }
                for service in self.services.values()
            ],
            "connectors": [
                {
                    "id": connector.id,
                    "name": connector.name,
                    "kind": connector.kind,
                    "transport": connector.transport,
                    "managed_by": connector.managed_by,
                    "owner_engine": connector.owner_engine,
                    "description": connector.description,
                    "env": connector.env,
                    "capabilities": connector.capabilities,
                    "permissions": connector.permissions,
                    "fallback_transports": connector.fallback_transports,
                    "status": connector.status,
                }
                for connector in self.connectors.values()
            ],
            "skills": [
                {
                    "id": skill.id,
                    "title": skill.title,
                    "engine": skill.engine,
                    "services": skill.services,
                    "connectors": skill.connectors,
                    "fcaps_lens": skill.fcaps_lens,
                    "output_modes": skill.output_modes,
                    "requires_approval": skill.requires_approval,
                    "path": skill.path,
                }
                for skill in self.skills.values()
            ],
        }
