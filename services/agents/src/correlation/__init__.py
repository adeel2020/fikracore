"""Incident-agnostic alarm correlation and incident lifecycle support."""

from .engine import CorrelationEngine
from .registry import IncidentRegistry

__all__ = ["CorrelationEngine", "IncidentRegistry"]
