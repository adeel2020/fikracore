"""Learn Capability for FikraCore (§26, §27, §28, §229).

Validate, promote, rollback and manage learned knowledge (H3 - Learn / Reuse).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import yaml

from .registry import CapabilityDefinition, ExecutionContext, RolePermission, CapabilityError
from ..investigation.knowledge import InMemoryKnowledgeProvider
from ..learning.promotion import PromotionEngine
from ..learning.h3_validator import validate_all_h3_units
from ..simulator.h3_generator import generate_all_h3_learning_units


def learn_handler(inputs: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
    """Handler executing the H3 validated learning lifecycle."""
    action = inputs.get("action", "inspect").lower()

    if action in ("promote", "rollback") and context.caller_role not in (
        RolePermission.SME_VALIDATOR,
        RolePermission.ADMIN,
    ):
        raise CapabilityError(
            "PERMISSION_DENIED",
            f"Action '{action}' requires SME_VALIDATOR or ADMIN permission (current: {context.caller_role.value}).",
        )

    if action == "promote":
        cand_data = inputs.get("candidate_data")
        val_data = inputs.get("validation_data")

        if not cand_data and inputs.get("candidate_file"):
            with open(inputs["candidate_file"], "r", encoding="utf-8") as f:
                cand_data = yaml.safe_load(f)
        if not val_data and inputs.get("validation_file"):
            with open(inputs["validation_file"], "r", encoding="utf-8") as f:
                val_data = yaml.safe_load(f)

        if not cand_data or not val_data:
            raise CapabilityError("INVALID_INPUT", "Promotion requires candidate and validation data.")

        prov = InMemoryKnowledgeProvider(pages=[], relationships=[], version="h3-learn-prov")
        engine = PromotionEngine()
        dry_run = inputs.get("dry_run", False)
        success, rec, errs = engine.promote_candidate(cand_data, val_data, prov, dry_run=dry_run)

        return {
            "action": "promote",
            "success": success,
            "promotion_record": rec.model_dump(mode="json") if rec else None,
            "errors": errs,
            "dry_run": dry_run,
        }

    elif action == "rollback":
        promotion_id = inputs.get("promotion_id")
        if not promotion_id:
            raise CapabilityError("INVALID_INPUT", "Rollback requires promotion_id.")
        prov = InMemoryKnowledgeProvider(pages=[], relationships=[], version="h3-learn-prov")
        engine = PromotionEngine()
        success, err = engine.rollback_promotion(promotion_id, prov)
        return {
            "action": "rollback",
            "success": success,
            "promotion_id": promotion_id,
            "error": err,
        }

    elif action == "validate":
        units_dir = inputs.get("units_dir") or Path(__file__).parent.parent / "simulator" / "h3_runs"
        val_results = validate_all_h3_units(Path(units_dir))
        return {
            "action": "validate",
            "report": val_results,
        }

    elif action == "generate":
        out_dir = inputs.get("output_dir") or Path(__file__).parent.parent / "simulator" / "h3_runs"
        units = generate_all_h3_learning_units(Path(out_dir))
        return {
            "action": "generate",
            "status": "SUCCESS",
            "units_generated": len(units),
            "output_dir": str(out_dir),
        }

    elif action == "inspect":
        unit_id = inputs.get("unit_id") or inputs.get("scenario") or "H3-LU-001"
        units_dir = Path(inputs.get("units_dir") or Path(__file__).parent.parent / "simulator" / "h3_runs")
        target_dir = units_dir / str(unit_id)
        if not target_dir.exists():
            # Search partial
            matches = [d for d in units_dir.iterdir() if d.is_dir() and str(unit_id) in d.name]
            if matches:
                target_dir = matches[0]

        if not target_dir.exists():
            raise CapabilityError("UNIT_NOT_FOUND", f"Learning unit '{unit_id}' not found in {units_dir}")

        manifest_file = target_dir / "learning_unit_manifest.yaml"
        cand_file = target_dir / "candidate_knowledge.yaml"
        val_file = target_dir / "validation_decision.yaml"

        manifest, cand, val = {}, {}, {}
        if manifest_file.exists():
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = yaml.safe_load(f)
        if cand_file.exists():
            with open(cand_file, "r", encoding="utf-8") as f:
                cand = yaml.safe_load(f)
        if val_file.exists():
            with open(val_file, "r", encoding="utf-8") as f:
                val = yaml.safe_load(f)

        return {
            "action": "inspect",
            "unit_id": str(unit_id),
            "manifest": manifest,
            "candidate_knowledge": cand,
            "validation_decision": val,
            "learning_lifecycle_status": val.get("decision", "NEEDS_REVIEW"),
        }

    else:
        raise CapabilityError("UNKNOWN_ACTION", f"Unknown learn action '{action}'")


learn_capability = CapabilityDefinition(
    name="learn",
    description="Validate, promote and manage learned knowledge (H3 - Learn / Reuse)",
    input_schema={
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["inspect", "validate", "promote", "rollback", "generate"]},
            "unit_id": {"type": "string"},
            "candidate_file": {"type": "string"},
            "validation_file": {"type": "string"},
            "promotion_id": {"type": "string"},
            "dry_run": {"type": "boolean"},
        },
    },
    output_schema={"type": "object", "description": "Learning lifecycle result"},
    permissions=[RolePermission.VIEWER, RolePermission.OPERATOR, RolePermission.SME_VALIDATOR, RolePermission.ADMIN],
    supports_cli=True,
    supports_ui=True,
    supports_zaki=True,
    supports_demo=True,
    supports_api=True,
    read_only=False,
    handler=learn_handler,
)
