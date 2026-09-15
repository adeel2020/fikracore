"""Canonical MARK assistant package."""

from .core import JARVIS, JARVISConfig, JARVISStatus, JarvisTelemetry, PowerUp

MarkAssistant = JARVIS
MarkConfig = JARVISConfig
MarkStatus = JARVISStatus
MarkTelemetry = JarvisTelemetry

__all__ = [
    "JARVIS",
    "JARVISConfig",
    "JARVISStatus",
    "JarvisTelemetry",
    "MarkAssistant",
    "MarkConfig",
    "MarkStatus",
    "MarkTelemetry",
    "PowerUp",
]
