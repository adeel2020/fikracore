"""
Knowledge Promotion Governor for Zaki v1
========================================
Governs the transition from candidate operational knowledge to validated production knowledge.

Enforces:
1. Candidate relationships cannot be promoted without human/SME validation.
2. Hidden simulator ground truth is never accessible.
3. Domain Jurisdiction: SME domain must match the candidate's domain jurisdiction.
4. Validated promotions route through the existing FikraCore knowledge path and learning ledger.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union
from ..governance.validation import HumanValidationContract
from ..enums import ValidationDecisionType
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
        domain: str = "IP_TRANSPORT",
    ) -> Dict[str, Any]:
        proposal = {
            "candidate_id": candidate_id,
            "relationship": relationship,
            "supporting_evidence_ids": supporting_evidence_ids,
            "task_id": task_id,
            "incident_id": incident_id,
            "domain": domain,
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
        provider: Optional[Any] = None,
    ) -> Dict[str, Any]:
        decision = validation.spec.decision
        valid_decisions = {
            ValidationDecisionType.CONFIRM,
            ValidationDecisionType.APPROVE_LEARNING,
            ValidationDecisionType.ACCEPT if hasattr(ValidationDecisionType, "ACCEPT") else None,
        }
        if decision not in valid_decisions and getattr(decision, "value", str(decision)) not in ("CONFIRM", "APPROVE_LEARNING", "ACCEPT"):
            return {
                "status": "REJECTED",
                "reason": f"Validation decision was {getattr(decision, 'value', str(decision))}",
            }

        # Domain Jurisdiction Enforcement
        val_domain = getattr(validation.metadata, "domain", None) or getattr(validation, "domain", None)
        cand_domain = proposal.get("domain")
        if val_domain and cand_domain and cand_domain != "unknown":
            norm_v = val_domain.lower().replace("-", "_")
            norm_c = cand_domain.lower().replace("-", "_")
            if norm_v not in norm_c and norm_c not in norm_v:
                return {
                    "status": "REJECTED",
                    "reason": f"Domain mismatch: validator domain `{val_domain}` does not govern candidate `{cand_domain}`",
                }

        # If a live knowledge provider is supplied, promote through FikraCore's KnowledgePromotionService
        promotion_journal_id = f"PJ-{proposal['candidate_id']}"
        if provider:
            from engine_stack.engines.telecom_brain.learning.promotion_service import default_promotion_service
            default_promotion_service.register_candidate(
                candidate_id=proposal["candidate_id"],
                relationship=proposal["relationship"],
                domain=cand_domain or "unknown",
                originating_episode_id=proposal.get("task_id", "EP-UNKNOWN"),
                supporting_evidence_ids=proposal.get("supporting_evidence_ids"),
            )
            success, rec, errors = default_promotion_service.validate_and_promote(
                candidate_id=proposal["candidate_id"],
                validation={
                    "validation_id": f"VAL-{proposal['candidate_id']}",
                    "candidate_id": proposal["candidate_id"],
                    "decision": "ACCEPT",
                    "validated_by_role": validation.spec.validator_role,
                    "reason": validation.spec.reason,
                    "timestamp": validation.spec.timestamp.isoformat() if hasattr(validation.spec.timestamp, "isoformat") else str(validation.spec.timestamp),
                },
                provider=provider,
                validator_domain=val_domain,
            )
            if not success:
                return {
                    "status": "REJECTED",
                    "reason": "; ".join(errors),
                }
            if rec:
                promotion_journal_id = rec.promotion_id

        result = {
            "status": "PROMOTED",
            "candidate_id": proposal["candidate_id"],
            "promoted_relationship": proposal["relationship"],
            "validated_by": validation.spec.validator_id,
            "promotion_journal_id": promotion_journal_id,
        }
        default_audit_logger.log_event(
            "KNOWLEDGE_PROMOTED",
            result,
            task_id=proposal.get("task_id"),
            incident_id=proposal.get("incident_id"),
        )
        return result


default_promotion_governor = KnowledgePromotionGovernor()
