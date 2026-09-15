"""Compatibility wrapper for the canonical capability registry loader."""

from capability_registry.loader import REGISTRY_ROOT, RegistryError, RegistryLoader, load_default_registry

__all__ = ["REGISTRY_ROOT", "RegistryError", "RegistryLoader", "load_default_registry"]
