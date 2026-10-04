from typing import Any, Optional, Callable
from pathlib import Path
from datetime import datetime
import json

def build_topology(
    
    entities: list[dict[str, Any]],
    trigger_entity: str,
    cohort: str,
    affected_service: str,
    stage_vals: dict[str, Any],
    stage_index: int,
    scenario_id: str | None = None,
 *, load_scenario_manifest: Any) -> dict[str, Any]:
    """Build topology from entities with stage-aware causal-path disclosure."""
    # Group entities by domain
    domain_groups: dict[str, list[dict[str, Any]]] = {}
    for ent in entities:
        domain = ent.get("domain", "UNKNOWN")
        if domain not in domain_groups:
            domain_groups[domain] = []
        domain_groups[domain].append(ent)

    # Build domain list
    domain_display_map = {
        "RAN": ("RAN", "Radio Access Network"),
        "IP_TRANSPORT": ("TRANSPORT", "IP / Optical"),
        "TRANSMISSION": ("TRANSPORT", "IP / Optical"),
        "EPC_4G": ("MOBILE CORE", "EPC / 5GC"),
        "SA_5G_CORE": ("MOBILE CORE", "5G SA Core"),
        "CS_CORE": ("MOBILE CORE", "Circuit Core"),
        "MOBILE_IMS": ("IMS", "Voice / Video"),
        "FIXED_IMS": ("IMS", "Voice / Video"),
        "CRM": ("CUSTOMER", "Services"),
        "BSS": ("OSS / BSS", "Charging / OSS"),
        "OSS": ("OSS / BSS", "Operations"),
        "CHARGING": ("OSS / BSS", "Charging / OSS"),
        "IT_CLOUD_INFRA": ("INFRA", "Cloud Infrastructure"),
        "EXTERNAL": ("EXTERNAL", "External"),
    }

    domains = []
    seen_domain_names = set()
    for domain_key, domain_entities in domain_groups.items():
        display_name, subtitle = domain_display_map.get(domain_key, (domain_key, domain_key))
        if display_name in seen_domain_names:
            # Merge into existing domain
            for d in domains:
                if d["name"] == display_name:
                    d["entities"].extend(domain_entities)
                    break
            continue
        seen_domain_names.add(display_name)
        domains.append({
            "name": display_name,
            "subtitle": subtitle,
            "entities": domain_entities,
        })

    # Add customer impact domain only after impact has at least been observed.
    has_customer = any(d["name"] == "CUSTOMER IMPACT" for d in domains)
    if not has_customer and stage_index >= 1:
        degradation = stage_vals["throughput_pct"]
        users_affected = stage_vals["users_affected"]
        domains.append({
            "name": "CUSTOMER IMPACT",
            "subtitle": "Services",
            "entities": [
                {
                    "id": affected_service.lower().replace(" ", "-"),
                    "display_name": affected_service,
                    "subtitle": "Degradation observed" if degradation is None else f"Degraded ({degradation}%)",
                    "state": "SYMPTOM",
                    "icon": "users",
                },
                {
                    "id": "enterprise-users",
                    "display_name": "Enterprise Users",
                    "subtitle": "Scope unknown" if users_affected is None else f"Affected (~{users_affected // 1000}k users)",
                    "state": "SYMPTOM" if stage_index < 5 else "IMPACTED",
                    "icon": "users",
                },
            ],
        })

    causal_path = []
    manifest = load_scenario_manifest(scenario_id) if scenario_id else None
    chain = manifest.get("causal_chain", []) if manifest else []

    if stage_index >= 2 and len(chain) >= 2:
        for idx in range(len(chain) - 1):
            from_id = chain[idx]
            to_id = chain[idx + 1]
            causal_path.append({
                "from": from_id,
                "to": to_id,
                "status": "CONFIRMED" if stage_index >= 7 else ("LEADING" if stage_index >= 4 else "CANDIDATE"),
                "relation": "PROPAGATES_TO" if idx > 0 else "CAUSES",
            })
    elif stage_index >= 4 and len(entities) >= 2:
        trigger_ent = next((e for e in entities if e["id"] == trigger_entity), None)
        symptom_ent = next((e for e in entities if e["state"] == "SYMPTOM"), None)
        if trigger_ent and symptom_ent:
            causal_path.append({
                "from": trigger_ent["id"],
                "to": symptom_ent["id"],
                "status": "CONFIRMED" if stage_index >= 7 else ("LEADING" if stage_index >= 4 else "CANDIDATE"),
                "relation": "CAUSES",
            })

    if stage_index >= 7 and causal_path:
        path_parts = []
        for edge in causal_path:
            src = next((e["display_name"] for e in entities if e["id"] == edge["from"]), edge["from"])
            dst = next((e["display_name"] for e in entities if e["id"] == edge["to"]), edge["to"])
            path_parts.append(f"{src} → {dst}")
        confirmed_label = "Confirmed Causal Path: " + " → ".join(path_parts)
    elif stage_index >= 4 and causal_path:
        path_parts = []
        for edge in causal_path:
            src = next((e["display_name"] for e in entities if e["id"] == edge["from"]), edge["from"])
            dst = next((e["display_name"] for e in entities if e["id"] == edge["to"]), edge["to"])
            path_parts.append(f"{src} → {dst}")
        confirmed_label = "Leading Causal Path: " + " → ".join(path_parts)
    else:
        confirmed_label = "Awaiting causal path analysis"

    return {
        "domains": domains,
        "causal_path": causal_path,
        "confirmed_path_label": confirmed_label,
        "path_confidence": stage_vals["confidence"] if causal_path else 0,
    }


