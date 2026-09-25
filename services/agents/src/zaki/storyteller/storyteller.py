"""Zaki Incident Storyteller Service."""

from __future__ import annotations

from typing import Any, Dict, Optional
from ..domain.contracts.story import IncidentStoryContract
from ..domain.enums import PresentationDepth
from .presentation import PresentationProjector


class ZakiStoryteller:
    """Provides human-readable and operator narratives grounded in FikraCore state."""

    def format_story_for_cli(self, story: IncidentStoryContract) -> str:
        depth = story.presentation_depth
        lines = []
        lines.append(f"\n{'='*70}")
        lines.append(f"  ZAKI INCIDENT STORY  [{depth.value} VIEW]")
        lines.append(f"{'='*70}\n")
        lines.append(f"INCIDENT: {story.title}")
        lines.append(f"RUN ID:   {story.run_id}\n")
        lines.append(f"SUMMARY:\n  {story.summary}\n")

        if story.leading_hypothesis:
            lh = story.leading_hypothesis
            lines.append("CURRENT LEADING HYPOTHESIS:")
            lines.append(f"  Root Entity: {lh.get('root_entity')} ({lh.get('domain')})")
            lines.append(f"  Confidence:  {lh.get('score')}  [{lh.get('role')}]")
            lines.append(f"  Statement:   {lh.get('statement')}")
            lines.append(f"  Supporting:  {len(lh.get('supporting_evidence', []))} signals")
            lines.append(f"  Contradicting: {len(lh.get('contradicting_evidence', []))} signals\n")

        if depth in (PresentationDepth.OPERATOR, PresentationDepth.DEEP_TECHNICAL):
            if story.competing_hypotheses:
                lines.append(f"COMPETING HYPOTHESES ({len(story.competing_hypotheses)}):")
                for ch in story.competing_hypotheses[:3]:
                    lines.append(f"  • #{ch.get('rank')} {ch.get('root_entity')} ({ch.get('domain')}): score {ch.get('score')} [{ch.get('role')}]")
                lines.append("")

            lines.append("PROVENANCE-BACKED TIMELINE:")
            for stmt in story.timeline_statements:
                lines.append(f"  [{stmt.provenance.value}] {stmt.text}")
            lines.append("")

        if depth == PresentationDepth.DEEP_TECHNICAL and story.technical_details:
            lines.append("12-FACTOR SYNTHESIS CORE BREAKDOWN:")
            for dim, val in story.technical_details.get("score_dimensions", {}).items():
                lines.append(f"  - {dim}: {val}")
            lines.append("")

        lines.append(f"NEXT RECOMMENDED ACTION:\n  {story.next_best_action}\n")
        lines.append(f"{'='*70}\n")
        return "\n".join(lines)


default_storyteller = ZakiStoryteller()
