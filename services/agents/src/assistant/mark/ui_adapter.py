"""UI-facing helpers for exposing Mark capabilities."""

from __future__ import annotations

from typing import Any

from capability_registry import MarkRegistry, load_default_registry


def capability_payload(registry: MarkRegistry | None = None) -> dict[str, Any]:
    """Return registry capabilities in the stable UI/debug API shape."""
    return (registry or load_default_registry()).to_capabilities()


__all__ = ["capability_payload"]
