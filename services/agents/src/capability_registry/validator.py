from __future__ import annotations

from .loader import RegistryLoader


def validate_default_registry() -> None:
    """Raise if the bundled MARK registry is inconsistent."""
    RegistryLoader().load()
