"""Presentation layer for FikraCore Telecom Brain."""

from .naming import (
    PresentationNamingResolver,
    default_naming_resolver,
    KNOWN_ACRONYMS,
    RELATIONSHIP_DISPLAY_NAMES,
    EVIDENCE_DISPLAY_NAMES,
)
from .ui_adapter import build_ui_presentation_model
from .zaki_bridge import ZakiBridge

__all__ = [
    "PresentationNamingResolver",
    "default_naming_resolver",
    "KNOWN_ACRONYMS",
    "RELATIONSHIP_DISPLAY_NAMES",
    "EVIDENCE_DISPLAY_NAMES",
    "build_ui_presentation_model",
    "ZakiBridge",
]
