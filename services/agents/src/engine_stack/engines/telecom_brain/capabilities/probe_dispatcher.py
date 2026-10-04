"""
Discrimination Probe Dispatcher (Step 3 Active Hypothesis Testing)
==================================================================
This module implements active hypothesis discrimination using DomainToolRegistry.

Role & Architectural Boundary:
- Dispatched during Step 3 of investigation when multiple competing hypotheses exist
  (e.g., SUSPECTED or UNDER_VALIDATION).
- Identifies differentiating telemetry signals and entities separating candidate causes.
- Selects and executes non-disruptive diagnostic probes (READ_ONLY_DIAGNOSTIC).
- Evaluates probe execution telemetry and generates Tier-3 ValidatedEvidenceContract
  with explicit verdicts (SUPPORTS, CONTRADICTS, CONFIRMS, RULES_OUT).
- Enforces 100% epistemic integrity: never references hidden simulator ground truth.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from ..investigation.contracts.evidence import ValidatedEvidenceContract
from ..investigation.contracts.domain import DomainCode
from ..investigation.contracts.hypothesis import InvestigationHypothesis
from .tool_registry import (
    ActionSafetyTier,
    AuthorityLevel,
    DomainToolDefinition,
    DomainToolRegistry,
)

# Shared default instance
_default_tool_registry = DomainToolRegistry()


class DiscriminationProbeDispatcher:
    """
    Orchestrates targeted diagnostic probes to discriminate between competing causal hypotheses.
    """

    def __init__(self, tool_registry: Optional[DomainToolRegistry] = None) -> None:
        self.registry = tool_registry or _default_tool_registry

    def identify_discriminating_probes(
        self, hypotheses: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify candidate diagnostic probes that can discriminate between top hypotheses.

        Args:
            hypotheses: List of active hypotheses (InvestigationHypothesis, RankedHypothesisItem, or dicts).

        Returns:
            List of candidate probe recommendations with target entity, tool_id, and rationale.
        """
        if not hypotheses:
            return []

        # Extract root entities, domains, and missing probes
        candidates: List[Dict[str, Any]] = []
        registered_tools = self.registry.list_tools(safety_tier=ActionSafetyTier.READ_ONLY_DIAGNOSTIC)

        for h in hypotheses:
            h_id = getattr(h, "hypothesis_id", None) or (h.get("hypothesis_id") if isinstance(h, dict) else "unknown")
            entity = (
                getattr(h, "canonical_root_entity", None)
                or getattr(h, "candidate_root_entity", None)
                or getattr(h, "root_entity", None)
                or (h.get("root_entity") if isinstance(h, dict) else "")
            )
            domain = (
                getattr(h, "candidate_root_domain", None)
                or getattr(h, "domain", None)
                or (h.get("candidate_root_domain") if isinstance(h, dict) else None)
                or (h.get("domain") if isinstance(h, dict) else "unknown")
            )
            missing = (
                getattr(h, "missing_evidence", None)
                or getattr(h, "missing_probes", None)
                or (h.get("missing_evidence") if isinstance(h, dict) else [])
            )

            # Match registered diagnostic tools for domain or explicit missing probes
            matched_tools: List[DomainToolDefinition] = []
            for tool in registered_tools:
                tool_domain = tool.domain.value if hasattr(tool.domain, "value") else str(tool.domain)
                if any(tool.tool_id in str(m) for m in (missing or [])) or (domain and (domain.upper() in tool_domain.upper() or tool_domain.upper() in domain.upper())):
                    matched_tools.append(tool)

            for tool in matched_tools:
                candidates.append({
                    "probe_id": tool.tool_id,
                    "display_name": tool.display_name,
                    "target_entity": entity,
                    "domain": domain,
                    "hypothesis_id": h_id,
                    "safety_tier": tool.safety_tier.value,
                    "rationale": f"Probe {tool.display_name} targets {entity} to test hypothesis {h_id}",
                })

        return candidates

    def dispatch_probe(
        self,
        probe_id: str,
        parameters: Dict[str, Any],
        caller_authority: AuthorityLevel = AuthorityLevel.LEVEL_1_ANALYZE,
        hitl_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a diagnostic probe through DomainToolRegistry with safety boundary enforcement.
        """
        return self.registry.execute_tool(
            tool_id=probe_id,
            parameters=parameters,
            caller_authority=caller_authority,
            hitl_token=hitl_token,
        )

    def evaluate_probe_result(
        self,
        probe_result: Dict[str, Any],
        hypotheses: List[Any],
        target_entity: str,
        domain: str,
        evaluating_agent: str = "probe_dispatcher",
    ) -> ValidatedEvidenceContract:
        """
        Evaluate a probe result against candidate hypotheses and generate ValidatedEvidenceContract.

        Args:
            probe_result: Execution output payload from the probe.
            hypotheses: Candidate hypotheses evaluated by this probe.
            target_entity: Entity interrogated by the probe.
            domain: Operational domain jurisdiction.
            evaluating_agent: Agent or subsystem signing the verdict.

        Returns:
            ValidatedEvidenceContract with explicit polarity verdict (SUPPORTS, CONTRADICTS, etc.)
        """
        status = probe_result.get("status", "SUCCESS")
        output = str(probe_result.get("output", "")).lower()
        tool_id = probe_result.get("tool_id", "probe.generic")

        # Determine verdict based on probe findings
        is_abnormal = any(term in output for term in ("drop", "error", "down", "failure", "timeout", "breach", "fail"))
        is_healthy = any(term in output for term in ("healthy", "up", "normal", "0 errors", "zero drops", "stable"))

        affected_hypo_ids = []
        for h in hypotheses:
            h_id = getattr(h, "hypothesis_id", None) or (h.get("hypothesis_id") if isinstance(h, dict) else "unknown")
            h_entity = getattr(h, "canonical_root_entity", None) or getattr(h, "root_entity", None) or (h.get("root_entity") if isinstance(h, dict) else "")
            if target_entity and (target_entity in h_entity or h_entity in target_entity):
                affected_hypo_ids.append(h_id)

        if not affected_hypo_ids and hypotheses:
            first_h = hypotheses[0]
            affected_hypo_ids.append(getattr(first_h, "hypothesis_id", "unknown") if not isinstance(first_h, dict) else first_h.get("hypothesis_id", "unknown"))

        if is_abnormal:
            verdict = "CONFIRMS" if "severe" in output or "critical" in output else "SUPPORTS"
            confidence = 0.95 if verdict == "CONFIRMS" else 0.85
        elif is_healthy:
            verdict = "RULES_OUT" if "zero" in output or "normal" in output else "CONTRADICTS"
            confidence = 0.90
        else:
            verdict = "SUPPORTS"
            confidence = 0.70

        return ValidatedEvidenceContract(
            evidence_id=f"VAL-EVD-{tool_id.replace('.', '_')}-{int(datetime.now(timezone.utc).timestamp())}",
            canonical_entity=target_entity or "network-entity",
            domain=domain,
            verdict=verdict,
            corroborating_hypotheses=affected_hypo_ids,
            confidence=confidence,
            validated_by_agent=evaluating_agent,
            timestamp=datetime.now(timezone.utc),
        )

    def run_discrimination_cycle(
        self,
        hypotheses: List[Any],
        max_probes: int = 2,
        evaluating_agent: str = "zaki_discrimination_dispatcher",
    ) -> Dict[str, Any]:
        """
        Execute an automated active discrimination cycle across candidate hypotheses.

        Returns:
            Dictionary containing dispatched probes, validated evidence records,
            and updated hypothesis confidence adjustments.
        """
        candidate_probes = self.identify_discriminating_probes(hypotheses)
        if not candidate_probes:
            return {
                "probes_dispatched": [],
                "validated_evidence": [],
                "discrimination_status": "NO_DISCRIMINATING_PROBES_FOUND",
            }

        dispatched = []
        validated_records: List[ValidatedEvidenceContract] = []

        # Execute top candidate probes
        for probe_spec in candidate_probes[:max_probes]:
            probe_id = probe_spec["probe_id"]
            entity = probe_spec["target_entity"]
            domain = probe_spec["domain"]

            try:
                res = self.dispatch_probe(
                    probe_id=probe_id,
                    parameters={"target_entity": entity, "interface": "auto"},
                    caller_authority=AuthorityLevel.LEVEL_1_ANALYZE,
                )
                dispatched.append(res)

                val_ev = self.evaluate_probe_result(
                    probe_result=res,
                    hypotheses=hypotheses,
                    target_entity=entity,
                    domain=domain,
                    evaluating_agent=evaluating_agent,
                )
                validated_records.append(val_ev)
            except Exception as e:
                dispatched.append({
                    "status": "ERROR",
                    "tool_id": probe_id,
                    "error": str(e),
                })

        return {
            "probes_dispatched": dispatched,
            "validated_evidence": [v.model_dump(mode="python") for v in validated_records],
            "discrimination_status": "COMPLETED",
        }


default_probe_dispatcher = DiscriminationProbeDispatcher()
