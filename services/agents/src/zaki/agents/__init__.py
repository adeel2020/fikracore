"""Agents package for Zaki v1."""

from .manifest import ManifestLoader
from .capability_registry import DomainCapabilityRegistry, default_domain_capability_registry
from .registry import AgentRegistry, default_agent_registry
from .dispatcher import AgentDispatcher, default_agent_dispatcher

__all__ = [
    "ManifestLoader",
    "DomainCapabilityRegistry",
    "default_domain_capability_registry",
    "AgentRegistry",
    "default_agent_registry",
    "AgentDispatcher",
    "default_agent_dispatcher",
]
