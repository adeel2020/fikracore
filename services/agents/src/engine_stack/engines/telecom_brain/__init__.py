"""TelecomBrainEngine canonical package."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import TelecomBrainEngine
    from .engine_context import TelecomContext, create_default_context
    from .models import TelecomRequest, TelecomResult

__all__ = [
    "TelecomBrainEngine",
    "TelecomContext",
    "TelecomRequest",
    "TelecomResult",
    "create_default_context",
]


def __getattr__(name: str):
    if name == "TelecomBrainEngine":
        from .engine import TelecomBrainEngine

        return TelecomBrainEngine
    if name in {"TelecomContext", "create_default_context"}:
        from .engine_context import TelecomContext, create_default_context

        return {"TelecomContext": TelecomContext, "create_default_context": create_default_context}[name]
    if name in {"TelecomRequest", "TelecomResult"}:
        from .models import TelecomRequest, TelecomResult

        return {"TelecomRequest": TelecomRequest, "TelecomResult": TelecomResult}[name]
    raise AttributeError(name)
