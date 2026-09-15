"""Report Capability for FikraCore (§235).

Generate benchmark and analysis reports in JSON or Markdown.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .registry import CapabilityDefinition, ExecutionContext, RolePermission, CapabilityError


def _find_dir(rel_path: str) -> Path:
    p = Path(rel_path)
    if p.exists():
        return p
    cur = Path(__file__).resolve().parent
    while cur != cur.parent:
        candidate = cur / rel_path
        if candidate.exists():
            return candidate
        cur = cur.parent
    return p


def report_handler(inputs: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
    """Handler retrieving or formatting reports."""
    stage = str(inputs.get("stage", "h4")).lower()
    fmt = str(inputs.get("format", "json")).lower()

    if stage == "h4":
        bm_dir = _find_dir(inputs.get("benchmark_dir") or "artifacts/hypothesis/h4")
        if fmt == "markdown":
            rf = bm_dir / "final-h4-report.md"
            if not rf.exists():
                raise CapabilityError("REPORT_NOT_FOUND", f"Report not found at {rf}")
            return {"format": "markdown", "content": rf.read_text(encoding="utf-8")}
        else:
            rf = bm_dir / "aggregate-report.json"
            if not rf.exists():
                raise CapabilityError("REPORT_NOT_FOUND", f"Report not found at {rf}")
            with open(rf, "r", encoding="utf-8") as f:
                return {"format": "json", "content": json.load(f)}

    elif stage == "h3":
        bm_dir = _find_dir(inputs.get("benchmark_dir") or "artifacts/hypothesis/h3")
        if fmt == "markdown":
            rf = bm_dir / "final-h3-report.md"
            if not rf.exists():
                raise CapabilityError("REPORT_NOT_FOUND", f"Report not found at {rf}")
            return {"format": "markdown", "content": rf.read_text(encoding="utf-8")}
        else:
            rf = bm_dir / "aggregate-report.json"
            if not rf.exists():
                raise CapabilityError("REPORT_NOT_FOUND", f"Report not found at {rf}")
            with open(rf, "r", encoding="utf-8") as f:
                return {"format": "json", "content": json.load(f)}

    elif stage == "h2":
        bm_dir = _find_dir(inputs.get("benchmark_dir") or "artifacts/hypothesis/h2")
        rf = bm_dir / "aggregate-report.json"
        if not rf.exists():
            raise CapabilityError("REPORT_NOT_FOUND", f"Report not found at {rf}")
        with open(rf, "r", encoding="utf-8") as f:
            return {"format": "json", "content": json.load(f)}

    elif stage in ("knowledge", "inventory"):
        out_dir = _find_dir(inputs.get("benchmark_dir") or "artifacts/knowledge-inventory")
        rf = out_dir / "inventory-report.md"
        if rf.exists() and fmt == "markdown":
            return {"format": "markdown", "content": rf.read_text(encoding="utf-8")}
        rf_json = out_dir / "telecombrain-inventory.json"
        if rf_json.exists():
            with open(rf_json, "r", encoding="utf-8") as f:
                return {"format": "json", "content": json.load(f)}
        raise CapabilityError("REPORT_NOT_FOUND", f"Knowledge inventory report not found at {out_dir}")

    else:
        raise CapabilityError("UNSUPPORTED_STAGE", f"Report not supported for stage '{stage}'")


report_capability = CapabilityDefinition(
    name="report",
    description="Generate benchmark and analysis reports",
    input_schema={
        "type": "object",
        "properties": {
            "stage": {"type": "string", "enum": ["h2", "h3", "h4", "knowledge"]},
            "benchmark_dir": {"type": "string"},
            "format": {"type": "string", "enum": ["json", "markdown"], "default": "json"},
        },
    },
    output_schema={"type": "object", "description": "Formatted report content"},
    permissions=[RolePermission.VIEWER, RolePermission.OPERATOR, RolePermission.SME_VALIDATOR, RolePermission.ADMIN],
    supports_cli=True,
    supports_ui=True,
    supports_zaki=False,
    supports_demo=False,
    supports_api=True,
    read_only=True,
    handler=report_handler,
)
