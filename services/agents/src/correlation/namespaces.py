"""Canonical gbrain namespace helpers for telecom-brain objects."""

from __future__ import annotations

import re


LEGACY_INCIDENT_PREFIX = "mobile-core/incidents"
CANONICAL_INCIDENT_PREFIX = "incidents/mobile-core"


def slug_part(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return slug or "unknown"


def incident_slug(service_id: str, correlation_key: str) -> str:
    return f"{CANONICAL_INCIDENT_PREFIX}/{slug_part(service_id)}-{slug_part(correlation_key)}"


def legacy_incident_slug(service_id: str, correlation_key: str) -> str:
    return f"{LEGACY_INCIDENT_PREFIX}/{slug_part(service_id)}-{slug_part(correlation_key)}"


def incident_aliases(canonical_slug: str) -> list[str]:
    if canonical_slug.startswith(f"{CANONICAL_INCIDENT_PREFIX}/"):
        suffix = canonical_slug.removeprefix(f"{CANONICAL_INCIDENT_PREFIX}/")
        return [f"{LEGACY_INCIDENT_PREFIX}/{suffix}"]
    if canonical_slug.startswith(f"{LEGACY_INCIDENT_PREFIX}/"):
        suffix = canonical_slug.removeprefix(f"{LEGACY_INCIDENT_PREFIX}/")
        return [f"{CANONICAL_INCIDENT_PREFIX}/{suffix}"]
    match = re.fullmatch(r"incidents/([a-z0-9_-]+)/(.+)", canonical_slug)
    if match:
        domain, suffix = match.groups()
        return [f"{domain}/incidents/{suffix}"]
    match = re.fullmatch(r"([a-z0-9_-]+)/incidents/(.+)", canonical_slug)
    if match:
        domain, suffix = match.groups()
        return [f"incidents/{domain}/{suffix}"]
    return []


def canonicalize_incident_slug(slug: str) -> str:
    if slug.startswith(f"{LEGACY_INCIDENT_PREFIX}/"):
        suffix = slug.removeprefix(f"{LEGACY_INCIDENT_PREFIX}/")
        return f"{CANONICAL_INCIDENT_PREFIX}/{suffix}"
    match = re.fullmatch(r"([a-z0-9_-]+)/incidents/(.+)", slug)
    if match:
        domain, suffix = match.groups()
        return f"incidents/{domain}/{suffix}"
    return slug


def correlation_cluster_slug(correlation_key: str) -> str:
    return f"correlation/mobile-core/clusters/{slug_part(correlation_key)}"


def correlation_decision_slug(correlation_key: str) -> str:
    return f"correlation/mobile-core/decisions/{slug_part(correlation_key)}"


def correlation_hypothesis_slug(correlation_key: str) -> str:
    return f"correlation/mobile-core/hypotheses/{slug_part(correlation_key)}"


def story_slug(incident_id: str) -> str:
    suffix = canonicalize_incident_slug(incident_id).removeprefix(f"{CANONICAL_INCIDENT_PREFIX}/")
    return f"storytelling/mobile-core/stories/{slug_part(suffix)}"


def story_run_slug(incident_id: str, correlation_key: str) -> str:
    suffix = canonicalize_incident_slug(incident_id).removeprefix(f"{CANONICAL_INCIDENT_PREFIX}/")
    return f"storytelling/mobile-core/story-runs/{slug_part(suffix)}-{slug_part(correlation_key)}"
