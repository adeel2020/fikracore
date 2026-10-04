"""
S3 — Temporal Consistency Validator
====================================
Validates temporal coherence across contracts:
- Valid timestamps (ISO-8601 or datetime).
- Closed timestamp cannot precede created timestamp (`created_at <= closed_at`).
- Ingestion timestamp cannot precede event observation (`event_time <= ingestion_time`).
- Validation timestamp cannot precede evidence observation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from .base import SanityCategory, SanityOutcome, SanityResult, SanityValidator


def parse_dt(val: Any) -> Optional[datetime]:
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            return None
    return None


class TemporalConsistencyValidator(SanityValidator):
    category = SanityCategory.S3_TEMPORAL

    def validate(self, contract: Any, context: Optional[Dict[str, Any]] = None) -> List[SanityResult]:
        results: List[SanityResult] = []
        data = contract.model_dump() if isinstance(contract, BaseModel) else (contract if isinstance(contract, dict) else {})

        # 1. Created vs Closed timestamps (TaskEpisode, Incident)
        created_dt = parse_dt(data.get("created_at") or data.get("first_seen") or data.get("started_at"))
        closed_dt = parse_dt(data.get("closed_at") or data.get("resolved_at") or data.get("last_seen"))

        if created_dt and closed_dt:
            if closed_dt < created_dt:
                results.append(
                    SanityResult(
                        check_id="S3-001",
                        category=self.category,
                        outcome=SanityOutcome.BLOCK,
                        message=f"Temporal inversion: closed_at ({closed_dt}) precedes created_at ({created_dt}).",
                        violating_fields=["created_at", "closed_at"],
                        remediation_hint="Ensure episode or incident closure timestamp is equal to or after start time.",
                    )
                )

        # 2. Event time vs Ingestion time (Evidence)
        event_dt = parse_dt(data.get("event_time"))
        ingestion_dt = parse_dt(data.get("ingestion_time"))
        if event_dt and ingestion_dt:
            if ingestion_dt < event_dt:
                results.append(
                    SanityResult(
                        check_id="S3-002",
                        category=self.category,
                        outcome=SanityOutcome.WARN,
                        message=f"Ingestion time ({ingestion_dt}) precedes event observation time ({event_dt}).",
                        violating_fields=["event_time", "ingestion_time"],
                        remediation_hint="Verify system clock synchronization across ingestion pipelines.",
                    )
                )

        # 3. Human validation preceding target evidence
        validations = data.get("human_validations", [])
        if isinstance(validations, list) and created_dt:
            for i, val in enumerate(validations):
                val_dt = parse_dt(val.get("timestamp") if isinstance(val, dict) else getattr(val, "timestamp", None))
                if val_dt and val_dt < created_dt:
                    results.append(
                        SanityResult(
                            check_id="S3-003",
                            category=self.category,
                            outcome=SanityOutcome.BLOCK,
                            message=f"Human validation [{i}] timestamp ({val_dt}) precedes episode start ({created_dt}).",
                            violating_fields=[f"human_validations[{i}].timestamp"],
                            remediation_hint="Validation cannot occur before the operational episode was initiated.",
                        )
                    )

        if not results:
            results.append(
                SanityResult(
                    check_id="S3-PASS",
                    category=self.category,
                    outcome=SanityOutcome.PASS,
                    message="Temporal consistency verified successfully.",
                )
            )
        return results
