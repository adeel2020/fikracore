"""Canonical gbrain namespace helpers for telecom-brain objects."""

from __future__ import annotations

import re


LEGACY_INCIDENT_PREFIX = "mobile-core/incidents"
CANONICAL_INCIDENT_PREFIX = "incidents/mobile-core"


DEPRECATED_HEX_MAPPINGS: dict[str, str] = {
    "site-power-81cec920e94d3a59": "incidents/power/power-grid-trip-ran-transport",
    "ue-registration-1fe005ed908a3f26": "incidents/mobile-core/ue-registration-congestion",
    "voice-call-setup-05841af2e3f4f430": "incidents/mobile-core/voice-call-setup-failure",
    "sgi-data-a154bb7a3997859c": "incidents/mobile-core/sgi-throughput-drop",
    "lte-attach-54db6ef325fbf758": "incidents/mobile-core/lte-attach-failure",
    "unmapped-service-a5eef0c5e022eeff": "incidents/mobile-core/unmapped-service-anomaly",
}

_DYNAMIC_SCENARIOS_CACHE: dict[str, str] = {}
_DYNAMIC_SCENARIOS_REVERSE: dict[str, list[str]] = {}
_DYNAMIC_SCENARIOS_LOADED: bool = False


def get_dynamic_scenario_mappings() -> tuple[dict[str, str], dict[str, list[str]]]:
    """Dynamically discover carrier scenario IDs, titles, and canonical incident slugs from declarative YAMLs."""
    global _DYNAMIC_SCENARIOS_CACHE, _DYNAMIC_SCENARIOS_REVERSE, _DYNAMIC_SCENARIOS_LOADED
    if _DYNAMIC_SCENARIOS_LOADED:
        return _DYNAMIC_SCENARIOS_CACHE, _DYNAMIC_SCENARIOS_REVERSE

    try:
        from pathlib import Path
        import yaml

        here = Path(__file__).resolve()
        candidates = [
            here.parents[2] / "engine_stack" / "engines" / "telecom_brain" / "simulator" / "scenarios",
            Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/scenarios").resolve(),
            Path("engine_stack/engines/telecom_brain/simulator/scenarios").resolve(),
        ]
        scenarios_dir = next((p for p in candidates if p.is_dir()), None)
        if scenarios_dir:
            for yf in sorted(scenarios_dir.glob("*.yaml")):
                if yf.name in ("h4_registry.yaml", "index.yaml"):
                    continue
                try:
                    data = yaml.safe_load(yf.read_text(encoding="utf-8")) or {}
                    if not isinstance(data, dict):
                        continue
                    spec = data.get("spec") if isinstance(data.get("spec"), dict) else data
                    meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
                    labels = meta.get("labels", {})

                    scn_id = str(spec.get("scenario_id") or data.get("scenario_id") or spec.get("id") or data.get("id") or yf.stem).upper()
                    raw_name = spec.get("scenario_name") or data.get("scenario_name") or meta.get("name") or yf.stem
                    clean_slug_name = slug_part(raw_name)

                    classification = spec.get("classification", {}) if isinstance(spec.get("classification"), dict) else {}
                    domains = [str(d).lower().replace("_", "-") for d in classification.get("domains", [])]
                    domain = str(labels.get("telecom.ai/domain") or spec.get("domain") or (domains[0] if domains else "mobile-core")).lower().replace("_", "-")

                    canonical_slug = f"incidents/{domain}/{clean_slug_name}"
                    clean_meta = clean_slug_name.replace("-outage", "")
                    short_name = clean_meta
                    for pfx in (
                        f"{domain}-", "5g-core-", "mobile-core-", "core-", "transport-",
                        "cloud-infra-", "cloud-", "database-", "power-", "sync-",
                        "synchronization-", "storage-", "cloud-storage-", "security-", "crm-",
                    ):
                        if short_name.startswith(pfx):
                            short_name = short_name[len(pfx):]

                    lookup_keys = [
                        scn_id.lower(),
                        scn_id.upper(),
                        f"incidents/{scn_id.lower()}",
                        f"incidents/{scn_id.upper()}",
                        raw_name.lower(),
                        clean_slug_name.lower(),
                        clean_meta.lower(),
                        short_name.lower(),
                        yf.stem.lower(),
                        yf.stem.upper(),
                        f"incidents/{domain}/{clean_slug_name.lower()}",
                        f"incidents/{domain}/{clean_meta.lower()}",
                        f"incidents/{domain}/{short_name.lower()}",
                        f"{domain}/incidents/{clean_slug_name.lower()}",
                        f"{domain}/incidents/{clean_meta.lower()}",
                        f"{domain}/incidents/{short_name.lower()}",
                    ]

                    for k in lookup_keys:
                        if k and k != canonical_slug:
                            _DYNAMIC_SCENARIOS_CACHE[k] = canonical_slug

                    if canonical_slug not in _DYNAMIC_SCENARIOS_REVERSE:
                        _DYNAMIC_SCENARIOS_REVERSE[canonical_slug] = []
                    _DYNAMIC_SCENARIOS_REVERSE[canonical_slug].extend(lookup_keys)
                except Exception:
                    continue
    except Exception:
        pass

    _DYNAMIC_SCENARIOS_LOADED = True
    return _DYNAMIC_SCENARIOS_CACHE, _DYNAMIC_SCENARIOS_REVERSE


def slug_part(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return slug or "unknown"


def incident_slug(service_id: str, correlation_key: str) -> str:
    clean_key = re.sub(r"^[0-9a-f]{16}$", "", str(correlation_key).strip())
    if clean_key:
        return f"{CANONICAL_INCIDENT_PREFIX}/{slug_part(service_id)}-{slug_part(clean_key)}"
    return f"{CANONICAL_INCIDENT_PREFIX}/{slug_part(service_id)}"


def legacy_incident_slug(service_id: str, correlation_key: str) -> str:
    return f"{LEGACY_INCIDENT_PREFIX}/{slug_part(service_id)}-{slug_part(correlation_key)}"


def incident_aliases(canonical_slug: str) -> list[str]:
    aliases: list[str] = []
    # Reverse lookup for any deprecated hex slugs mapping to this canonical slug
    for legacy_key, canon_val in DEPRECATED_HEX_MAPPINGS.items():
        if canonical_slug == canon_val or canonical_slug.endswith(canon_val):
            aliases.extend([
                f"{CANONICAL_INCIDENT_PREFIX}/{legacy_key}",
                f"{LEGACY_INCIDENT_PREFIX}/{legacy_key}",
                f"incidents/mobile-core/{legacy_key}",
                f"incidents/power/{legacy_key}",
                legacy_key,
            ])

    # Dynamic scenario aliases discovered from scenario YAMLs
    _, reverse_map = get_dynamic_scenario_mappings()
    if canonical_slug in reverse_map:
        aliases.extend(reverse_map[canonical_slug])
    else:
        # Check domain-stripped matches
        for target_slug, scn_aliases in reverse_map.items():
            if target_slug.endswith(canonical_slug) or canonical_slug.endswith(target_slug.split("/")[-1]):
                aliases.extend(scn_aliases)

    if canonical_slug.startswith(f"{CANONICAL_INCIDENT_PREFIX}/"):
        suffix = canonical_slug.removeprefix(f"{CANONICAL_INCIDENT_PREFIX}/")
        aliases.extend([f"{LEGACY_INCIDENT_PREFIX}/{suffix}", f"incidents/{suffix}"])
    elif canonical_slug.startswith(f"{LEGACY_INCIDENT_PREFIX}/"):
        suffix = canonical_slug.removeprefix(f"{LEGACY_INCIDENT_PREFIX}/")
        aliases.extend([f"{CANONICAL_INCIDENT_PREFIX}/{suffix}", f"incidents/{suffix}"])

    match = re.fullmatch(r"incidents/([a-z0-9_-]+)/(.+)", canonical_slug)
    if match:
        domain, suffix = match.groups()
        aliases.extend([f"{domain}/incidents/{suffix}", f"{domain}/{suffix}", suffix])
    match = re.fullmatch(r"([a-z0-9_-]+)/incidents/(.+)", canonical_slug)
    if match:
        domain, suffix = match.groups()
        aliases.extend([f"incidents/{domain}/{suffix}", f"{domain}/{suffix}", suffix])

    return list(dict.fromkeys(a for a in aliases if a != canonical_slug))


def canonicalize_incident_slug(slug: str) -> str:
    if not slug:
        return slug
    clean_slug = slug.strip().strip("/")

    # Dynamic scenario mapping (SCN-001 ... SCN-100, etc.)
    scenario_map, _ = get_dynamic_scenario_mappings()
    if clean_slug.lower() in scenario_map:
        return scenario_map[clean_slug.lower()]
    clean_slug_no_prefix = clean_slug.removeprefix("incidents/").lower()
    if clean_slug_no_prefix in scenario_map:
        return scenario_map[clean_slug_no_prefix]

    # Check explicit hex mapping dictionary
    for legacy_key, canon_val in DEPRECATED_HEX_MAPPINGS.items():
        if clean_slug == legacy_key or clean_slug.endswith(f"/{legacy_key}") or clean_slug == f"{LEGACY_INCIDENT_PREFIX}/{legacy_key}":
            return canon_val

    # Strip legacy mobile-core/incidents/ prefix
    if clean_slug.startswith(f"{LEGACY_INCIDENT_PREFIX}/"):
        suffix = clean_slug.removeprefix(f"{LEGACY_INCIDENT_PREFIX}/")
        clean_slug = f"{CANONICAL_INCIDENT_PREFIX}/{suffix}"
    elif match := re.fullmatch(r"([a-z0-9_-]+)/incidents/(.+)", clean_slug):
        domain, suffix = match.groups()
        clean_slug = f"incidents/{domain}/{suffix}"

    # Strip dangling hex hash suffixes like -81cec920e94d3a59 or -1fe005ed908a3f26
    clean_slug = re.sub(r"-[0-9a-f]{16}$", "", clean_slug)
    clean_slug = re.sub(r"-[0-9a-f]{8}$", "", clean_slug)

    # Re-check explicit mapping after stripping
    for legacy_key, canon_val in DEPRECATED_HEX_MAPPINGS.items():
        if clean_slug == legacy_key or clean_slug.endswith(f"/{legacy_key}"):
            return canon_val

    return clean_slug


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
