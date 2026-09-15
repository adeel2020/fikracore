"""Compatibility wrapper for the canonical MARK capability registry."""

from capability_registry import (
    ConnectorManifest,
    EngineManifest,
    MarkRegistry,
    RegistryLoader,
    ServiceManifest,
    SkillDocument,
    load_default_registry,
)

__all__ = [
    "ConnectorManifest",
    "EngineManifest",
    "MarkRegistry",
    "RegistryLoader",
    "ServiceManifest",
    "SkillDocument",
    "load_default_registry",
]
