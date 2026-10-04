"""
Behavior & Safety Governance Contracts
======================================
This module defines the BehaviorContract governing how Zaki and domain specialist
agents reason, interact, and execute in telecommunications operations.

Guardrail Architecture:
1. Truth-Blind Diagnostic Integrity: Agents are strictly prohibited from referencing
   or inferring hidden simulation ground truth. All deductions must be grounded in
   admitted telemetry and topology.
2. Causal Discrimination Rigor: Agents must never declare root cause without active
   discrimination testing between competing hypotheses. "Similar != same" is enforced.
3. Remediation Safety Ceilings: Destructive actions strictly require verified preconditions,
   explicit rollback procedures, and human-in-the-loop (HITL) approval.
4. Voice / Speech Pacing: Simulation stage advancement must hold until speech synthesis
   and audio playback complete (`speech_completion_barrier_required = True`).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
from pydantic import Field

from ..contracts.base import BaseContract
from ..contracts.prosody import ProsodyContract


class BehaviorContract(BaseContract):
    """
    Behavioral governance policy defining cognitive and execution guardrails for Zaki and agents.

    Attributes:
        api_version: Schema version identifier ('zaki.ai/v1').
        kind: Contract kind ('BehaviorContract').
        behavior_id: Unique policy configuration identifier.
        prosody: Prosodic vocal acoustic policy governing voice synthesis, breathing, and anti-readout.
        enforce_truth_blindness: Prohibits accessing or hallucinating hidden ground truth.
        enforce_similar_not_same: Mandates active discrimination even if historical pattern similarity is high.
        enforce_mandatory_preconditions: Requires all playbook preconditions to be satisfied before execution.
        enforce_reversibility: Prohibits executing actions that lack defined rollback procedures.
        enforce_hitl_approval_tier: Minimum ActionSafetyTier requiring human SME sign-off.
        speech_completion_barrier_required: Halts simulation stage progression until audio playback finishes.
        max_active_hypotheses: Upper bound on concurrent competing hypotheses tracked during Step 2.
        allowed_authority_level: Maximum permissible authority tier granted to autonomous agents.
        prohibited_tool_actions: Blacklist of dangerous commands (e.g. ['factory_reset', 'reload_unconditional']).
        governance_notes: Compliance and regulatory audit notes.
        created_at: Policy instantiation timestamp.
    """
    api_version: str = Field(default="zaki.ai/v1", description="Contract API schema version")
    kind: str = Field(default="BehaviorContract", description="Contract kind identifier")
    behavior_id: str = Field(
        default_factory=lambda: f"BEH-{int(datetime.now(timezone.utc).timestamp())}",
        description="Unique behavior governance policy identifier"
    )
    enforce_truth_blindness: bool = Field(
        default=True,
        description="Strictly isolates agents from evaluator-only hidden ground truth"
    )
    enforce_similar_not_same: bool = Field(
        default=True,
        description="Mandates active discrimination testing; rejects blind pattern reuse"
    )
    enforce_mandatory_preconditions: bool = Field(
        default=True,
        description="Blocks playbook execution until all operational preconditions evaluate to True"
    )
    enforce_reversibility: bool = Field(
        default=True,
        description="Requires verified rollback steps for all mutation commands"
    )
    enforce_hitl_approval_tier: str = Field(
        default="CONTROLLED_REVERSIBLE",
        description="Safety tier requiring human SME digital approval (CONTROLLED_REVERSIBLE, DISRUPTIVE)"
    )
    speech_completion_barrier_required: bool = Field(
        default=True,
        description="Blocks simulation stage advancement until speech audio playback finishes"
    )
    max_active_hypotheses: int = Field(
        default=5,
        description="Maximum number of competing explanations concurrently tracked"
    )
    allowed_authority_level: str = Field(
        default="LEVEL_2_DIAGNOSE",
        description="Ceiling on automated agent execution (LEVEL_1_ANALYZE, LEVEL_2_DIAGNOSE, LEVEL_3_EXECUTE)"
    )
    prohibited_tool_actions: List[str] = Field(
        default_factory=lambda: ["erase_startup_config", "format_flash", "reload_unconditional"],
        description="Dangerous command patterns strictly blocked by governance"
    )
    governance_notes: str = Field(
        default="NOC SME Tier-1 Autonomous Governance Guardrails",
        description="Human-readable audit notes describing policy rationale"
    )
    prosody: ProsodyContract = Field(
        default_factory=ProsodyContract,
        description="Prosodic and vocal acoustic policy governing voice synthesis and anti-readout"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when policy was enacted"
    )

    def curate_spoken_response(self, text: str, query: str = "") -> str:
        """Curate text into spoken output governed strictly by this contract's prosody policy."""
        return self.prosody.curate_speech(text, query=query)

    def to_voice_directive(self) -> str:
        """Return system prompt instructions for voice generation."""
        return self.prosody.to_prompt_directive()

