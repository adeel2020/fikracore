"""Canonical source-object identity and service enrichment for correlation."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json

from .models import AlarmEvent


class IdentityResolver:
    def __init__(self, components: list[dict]) -> None:
        self._components = {
            (item["source_system"], item["source_object_id"]): item
            for item in components
        }

    @classmethod
    def from_file(cls, path: Path) -> "IdentityResolver":
        data = json.loads(path.read_text()) if path.exists() else {"components": []}
        return cls(data.get("components", []))

    def resolve(self, event: AlarmEvent) -> AlarmEvent:
        component = self._components.get((event.source_system, event.object_id))
        if not component:
            return event
        return replace(
            event,
            object_id=component["component_id"],
            component_kind=component.get("component_kind", event.component_kind),
            location=component.get("location", event.location),
            service_ids=tuple(component.get("service_ids", event.service_ids)),
        )
