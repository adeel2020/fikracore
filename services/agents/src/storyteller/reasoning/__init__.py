"""Layer 2 — Reasoning / Storytelling (deterministic).

Builds a deterministic ``IncidentStory`` from an L1 ``IncidentContext`` and
optionally synthesizes an LLM narrative into a ``StoryResponse``.
"""

from .pipeline import build_incident_story, build_story_response
from .story import CausalChain, CausalStep, HypothesisAssessment, IncidentStory, StoryResponse

__all__ = [
    "CausalChain",
    "CausalStep",
    "HypothesisAssessment",
    "IncidentStory",
    "StoryResponse",
    "build_incident_story",
    "build_story_response",
]
