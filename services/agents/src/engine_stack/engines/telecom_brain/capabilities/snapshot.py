"""Snapshot Capability for FikraCore (§18, §19, §47).

Export, inspect, load, and list operational knowledge snapshots.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .registry import CapabilityDefinition, ExecutionContext, RolePermission, CapabilityError
from ..investigation.snapshot import default_snapshot_manager


def snapshot_handler(inputs: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
    """Handler managing FikraCore knowledge snapshots."""
    action = str(inputs.get("action") or "list").lower()
    target = inputs.get("target") or inputs.get("path") or inputs.get("snapshot")

    if action in ("list", "ls"):
        snapshots = default_snapshot_manager.list_snapshots()
        return {
            "status": "success",
            "action": "list",
            "total_snapshots": len(snapshots),
            "snapshots": [s.to_dict() for s in snapshots],
        }

    elif action in ("inspect", "show", "info"):
        if not target:
            raise CapabilityError("MISSING_ARGUMENT", "Target snapshot path or name is required for inspect.")
        try:
            info = default_snapshot_manager.inspect_snapshot(target)
            return {"status": "success", "action": "inspect", "snapshot": info}
        except FileNotFoundError as e:
            raise CapabilityError("SNAPSHOT_NOT_FOUND", str(e))
        except Exception as e:
            raise CapabilityError("INSPECTION_FAILED", f"Failed to inspect snapshot: {e}")

    elif action in ("create", "export", "take"):
        out_path = inputs.get("output") or target
        version = inputs.get("version")
        from ..investigation.knowledge import GbrainTelecomBrainProvider
        try:
            provider = None
            try:
                provider = GbrainTelecomBrainProvider()
            except Exception:
                provider = None

            path, meta = default_snapshot_manager.create_snapshot(
                provider=provider,
                output_path=out_path,
                version_tag=version,
            )
            return {"status": "success", "action": "create", "details": meta}
        except Exception as e:
            raise CapabilityError("SNAPSHOT_CREATION_FAILED", f"Failed to create snapshot: {e}")

    else:
        raise CapabilityError("INVALID_ACTION", f"Unknown snapshot action '{action}'. Valid actions: list, inspect, create.")


snapshot_capability = CapabilityDefinition(
    name="snapshot",
    description="Export, inspect, and list operational knowledge snapshots",
    input_schema={
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["list", "inspect", "create"]},
            "target": {"type": "string"},
            "output": {"type": "string"},
            "version": {"type": "string"},
        },
    },
    output_schema={"type": "object", "description": "Snapshot operation results"},
    permissions=[RolePermission.OPERATOR, RolePermission.SME_VALIDATOR, RolePermission.ADMIN],
    supports_cli=True,
    supports_ui=True,
    supports_zaki=False,
    supports_demo=False,
    supports_api=True,
    read_only=False,
    handler=snapshot_handler,
)
