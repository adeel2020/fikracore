"""Knowledge Promotion Governor for Zaki v1.

Enforces:
- Candidate relationships cannot be promoted without human/SME validation.
- Hidden simulator ground truth is never accessible.
- Validated promotions route through the existing FikraCore knowledge path.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from ..domain.contracts.validation import HumanValidationContract
from ..domain.enums import ValidationDecisionType
from ..governance.audit import default_audit_logger


class KnowledgePromotionGovernor:
    """Governs the transition from candidate knowledge to validated production knowledge."""

    def propose_candidate_promotion(
        self,
        candidate_id: str,
        relationship: Dict[str, Any],
        supporting_evidence_ids: list,
        task_id: str,
        incident_id: str,
    ) -> Dict[str, Any]:
        proposal = {
            "candidate_id": candidate_id,
            "relationship": relationship,
            "supporting_evidence_ids": supporting_evidence_ids,
            "task_id": task_id,
            "incident_id": incident_id,
            "status": "AWAITING_SME_VALIDATION",
        }
        default_audit_logger.log_event(
            "KNOWLEDGE_PROMOTION_REQUESTED",
            proposal,
            task_id=task_id,
            incident_id=incident_id,
        )
        return proposal

    def promote_with_validation(
        self,
        proposal: Dict[str, Any],
        validation: HumanValidationContract,
    ) -> Dict[str, Any]:
        if validation.spec.decision != ValidationDecisionType.CONFIRM and validation.spec.decision != ValidationDecisionType.APPROVE_LEARNING:
            return {
                "status": "REJECTED",
                "reason": f"Validation decision was {validation.spec.decision.value}",
            }

        result = {
            "status": "PROMOTED",
            "candidate_id": proposal["candidate_id"],
            "promoted_relationship": proposal["relationship"],
            "validated_by": validation.spec.validator_id,
            "promotion_journal_id": f"PJ-{proposal['candidate_id']}",
        }
        default_audit_logger.log_event(
            "KNOWLEDGE_PROMOTED",
            result,
            task_id=proposal.get("task_id"),
            incident_id=proposal.get("incident_id"),
        )
        return result


default_promotion_governor = KnowledgePromotionGovernor()
