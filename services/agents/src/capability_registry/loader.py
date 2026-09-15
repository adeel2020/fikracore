from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import (
    ConnectorManifest,
    EngineManifest,
    MarkRegistry,
    ServiceManifest,
    SkillDocument,
)


REGISTRY_ROOT = Path(__file__).resolve().parent


class RegistryError(ValueError):
    """Raised when MARK capability registry data is invalid."""


class RegistryLoader:
    def __init__(self, root: Path | str = REGISTRY_ROOT):
        self.root = Path(root)

    def load(self) -> MarkRegistry:
        top = self._read_yaml(self.root / "mark.manifest.yaml")
        connectors = self._load_connectors()
        services = self._load_services()
        engines = self._load_engines()
        skills = self._load_skills()

        registry = MarkRegistry(
            id=self._require_str(top, "id", "mark.manifest.yaml"),
            name=self._require_str(top, "name", "mark.manifest.yaml"),
            version=str(top.get("version", "0.0.0")),
            description=str(top.get("description", "")),
            principles=list(top.get("principles", [])),
            runtime=dict(top.get("runtime", {})),
            engines=engines,
            services=services,
            connectors=connectors,
            skills=skills,
            raw=top,
        )
        self._validate(registry)
        return registry

    def _load_engines(self) -> dict[str, EngineManifest]:
        engines: dict[str, EngineManifest] = {}
        for path in sorted((self.root / "engines").glob("*.yaml")):
            raw = self._read_yaml(path)
            manifest = EngineManifest(
                id=self._require_str(raw, "id", path.name),
                name=self._require_str(raw, "name", path.name),
                description=str(raw.get("description", "")),
                routing_intents=list(raw.get("routing_intents", [])),
                services=list(raw.get("services", [])),
                connectors=list(raw.get("connectors", [])),
                skills=list(raw.get("skills", [])),
                permissions=list(raw.get("permissions", [])),
                status=str(raw.get("status", "planned")),
                raw=raw,
            )
            self._add_unique(engines, manifest.id, manifest, path)
        return engines

    def _load_services(self) -> dict[str, ServiceManifest]:
        services: dict[str, ServiceManifest] = {}
        for path in sorted((self.root / "services").glob("*.yaml")):
            raw = self._read_yaml(path)
            manifest = ServiceManifest(
                id=self._require_str(raw, "id", path.name),
                name=self._require_str(raw, "name", path.name),
                engine=self._require_str(raw, "engine", path.name),
                description=str(raw.get("description", "")),
                connectors=list(raw.get("connectors", [])),
                consumes=list(raw.get("consumes", [])),
                produces=list(raw.get("produces", [])),
                permissions=list(raw.get("permissions", [])),
                status=str(raw.get("status", "planned")),
                raw=raw,
            )
            self._add_unique(services, manifest.id, manifest, path)
        return services

    def _load_connectors(self) -> dict[str, ConnectorManifest]:
        connectors: dict[str, ConnectorManifest] = {}
        for path in sorted((self.root / "connectors").glob("*.yaml")):
            raw = self._read_yaml(path)
            manifest = ConnectorManifest(
                id=self._require_str(raw, "id", path.name),
                name=self._require_str(raw, "name", path.name),
                kind=self._require_str(raw, "kind", path.name),
                transport=str(raw.get("transport", "mcp")),
                managed_by=str(raw.get("managed_by", "mcp_client_hub")),
                owner_engine=raw.get("owner_engine"),
                description=str(raw.get("description", "")),
                env=list(raw.get("env", [])),
                capabilities=list(raw.get("capabilities", [])),
                permissions=list(raw.get("permissions", [])),
                fallback_transports=list(raw.get("fallback_transports", [])),
                status=str(raw.get("status", "planned")),
                raw=raw,
            )
            self._add_unique(connectors, manifest.id, manifest, path)
        return connectors

    def _load_skills(self) -> dict[str, SkillDocument]:
        skills: dict[str, SkillDocument] = {}
        for path in sorted((self.root / "skills").glob("*.md")):
            frontmatter, body = self._read_skill(path)
            skill = SkillDocument(
                id=self._require_str(frontmatter, "id", path.name),
                title=self._require_str(frontmatter, "title", path.name),
                engine=self._require_str(frontmatter, "engine", path.name),
                services=list(frontmatter.get("services", [])),
                connectors=list(frontmatter.get("connectors", [])),
                fcaps_lens=list(frontmatter.get("fcaps_lens", [])),
                output_modes=list(frontmatter.get("output_modes", [])),
                requires_approval=bool(frontmatter.get("requires_approval", False)),
                body=body,
                path=str(path.relative_to(self.root)),
                raw_frontmatter=frontmatter,
            )
            self._add_unique(skills, skill.id, skill, path)
        return skills

    def _validate(self, registry: MarkRegistry) -> None:
        top_engine_ids = set(registry.raw.get("engines", []))
        missing_top_engines = top_engine_ids - set(registry.engines)
        if missing_top_engines:
            raise RegistryError(f"top-level manifest references missing engines: {sorted(missing_top_engines)}")

        for service in registry.services.values():
            if service.engine not in registry.engines:
                raise RegistryError(f"service {service.id} references missing engine {service.engine}")
            missing_connectors = set(service.connectors) - set(registry.connectors)
            if missing_connectors:
                raise RegistryError(f"service {service.id} references missing connectors: {sorted(missing_connectors)}")

        for engine in registry.engines.values():
            missing_services = set(engine.services) - set(registry.services)
            missing_connectors = set(engine.connectors) - set(registry.connectors)
            missing_skills = set(engine.skills) - set(registry.skills)
            if missing_services:
                raise RegistryError(f"engine {engine.id} references missing services: {sorted(missing_services)}")
            if missing_connectors:
                raise RegistryError(f"engine {engine.id} references missing connectors: {sorted(missing_connectors)}")
            if missing_skills:
                raise RegistryError(f"engine {engine.id} references missing skills: {sorted(missing_skills)}")

        for skill in registry.skills.values():
            if skill.engine not in registry.engines:
                raise RegistryError(f"skill {skill.id} references missing engine {skill.engine}")
            missing_services = set(skill.services) - set(registry.services)
            missing_connectors = set(skill.connectors) - set(registry.connectors)
            if missing_services:
                raise RegistryError(f"skill {skill.id} references missing services: {sorted(missing_services)}")
            if missing_connectors:
                raise RegistryError(f"skill {skill.id} references missing connectors: {sorted(missing_connectors)}")

    def _read_yaml(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise RegistryError(f"missing registry file: {path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise RegistryError(f"registry file must contain a mapping: {path}")
        return data

    def _read_skill(self, path: Path) -> tuple[dict[str, Any], str]:
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            raise RegistryError(f"skill is missing YAML frontmatter: {path}")
        try:
            _, frontmatter_text, body = text.split("---\n", 2)
        except ValueError as exc:
            raise RegistryError(f"skill frontmatter is not closed: {path}") from exc
        frontmatter = yaml.safe_load(frontmatter_text) or {}
        if not isinstance(frontmatter, dict):
            raise RegistryError(f"skill frontmatter must be a mapping: {path}")
        return frontmatter, body.strip()

    @staticmethod
    def _require_str(raw: dict[str, Any], key: str, label: str) -> str:
        value = raw.get(key)
        if not isinstance(value, str) or not value.strip():
            raise RegistryError(f"{label} missing required string field: {key}")
        return value

    @staticmethod
    def _add_unique(target: dict[str, Any], key: str, value: Any, path: Path) -> None:
        if key in target:
            raise RegistryError(f"duplicate registry id {key!r} in {path}")
        target[key] = value


def load_default_registry() -> MarkRegistry:
    return RegistryLoader().load()
