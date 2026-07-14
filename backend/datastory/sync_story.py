"""Sync stories.yaml with knowledge_graph_state.yaml.

Detects orphan reassignment_reasons, updates drifted counts, and generates
SOP entries via direct LLM call using existing stories as few-shot examples."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import logging
import yaml

from backend.config import settings

logger = logging.getLogger(__name__)

_HERE = Path(__file__).resolve().parent
_DATA = _HERE / "data"
_STORIES_PATH = _DATA / "stories.yaml"
_KG_STATE_PATH = _DATA / "knowledge_graph_state.yaml"
_WARNINGS_PATH = _DATA / "sync_warnings.yaml"


def _normalize(name: str) -> str:
    return name.strip().lower()


def _load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def _dump_yaml(data: Any, path: Path) -> None:
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


# ---------------------------------------------------------------------------
# Orphan detection
# ---------------------------------------------------------------------------

def _get_kg_reasons() -> list[dict]:
    kg = _load_yaml(_KG_STATE_PATH)
    for col in kg.get("columns", []):
        if col.get("field") == "reassignment_reason":
            return col.get("values", [])
    return []


def _get_stories_issues_by_name() -> dict[str, dict]:
    """Return a flat dict: normalized name -> {issue_info, category, parent}."""
    stories = _load_yaml(_STORIES_PATH)
    result: dict[str, dict] = {}
    for cat in stories.get("sop_framework", {}).get("categories", []):
        for issue in cat.get("issues", []):
            key = _normalize(issue.get("name", ""))
            result[key] = {
                **issue,
                "category": cat["name"],
                "parent_name": None,
                "is_group": "counts" in issue,
            }
            for sub_name in (issue.get("counts") or {}):
                sub_key = _normalize(sub_name)
                result[sub_key] = {
                    "name": issue["name"],
                    "sub_issue": sub_name,
                    "count": issue["counts"][sub_name],
                    "description": issue.get("description", ""),
                    "custops_check": issue.get("custops_check", ""),
                    "caveats": issue.get("caveats", ""),
                    "tie_breaker": issue.get("tie_breaker", ""),
                    "validation_steps": issue.get("validation_steps", []),
                    "handset_cause": issue.get("handset_cause", ""),
                    "category": cat["name"],
                    "parent_name": issue["name"],
                    "is_group": False,
                }
    return result


# ---------------------------------------------------------------------------
# SOP generation via direct LLM
# ---------------------------------------------------------------------------

_FEW_SHOT_EXAMPLES = """
Example 1:
- name: "Device APN issue"
  count: 638
  description: "The User Equipment (UE) is attempting to attach to the network
    using an incorrect or unauthorized Access Point Name (APN), resulting in a
    PGW/SMF rejection."
  custops_check: "Use BO tools to query the subscriber's active session or
    HSS/UDM profile to verify the provisioned APNs versus the APN being requested."
  caveats: "Sometimes the default APN is correct, but a secondary PDP context
    (like IMS or tethering) is failing, masking the primary issue."
  tie_breaker: "If the APN in the BO tool matches the handset exactly, but data
    still fails, the issue is likely a blocked IP pool or firewall rule — escalate
    to Core. If there is a mismatch, the issue is user/device side — do not escalate."
  validation_steps:
    - "Verify APN spelling in UE."
    - "Reset network settings."
    - "Toggle airplane mode to force a new attach request."
  handset_cause: "OS updates (especially iOS carrier bundle updates or Android
    custom ROMs) can overwrite APN settings. Dual-SIM phones frequently assign
    the wrong APN to the secondary SIM."

Example 2:
- name: "Multi SIM not allowed"
  count: 435
  description: "A network rejection occurring because the system detects an
    attempt to register the same MSISDN on a secondary ICCID without a valid
    Multi-SIM or Twin SIM service provisioned in the HSS."
  custops_check: "Verify in the CRM if the Multi-SIM VAS is active and linked
    to the correct secondary ICCID/EID."
  caveats: "Apple Watch cellular activations frequently trigger this if the
    entitlement server fails to properly link the watch's eSIM to the primary
    MSISDN."
  tie_breaker: "If the secondary SIM is not registered in the BO tool, do not
    escalate. Process a SIM swap or add the Multi-SIM VAS."
  validation_steps:
    - "Verify primary and secondary ICCIDs."
    - "Check entitlement server status (for wearables)."
  handset_cause: "The user swapping SIMs between devices too quickly can
    sometimes cause a temporary location update collision in the VLR, though
    this clears automatically."
"""


def _generate_sop_entry(reason_name: str, count: int, category: str) -> dict | None:
    """Call the LLM directly (no CrewAI) to generate a single SOP entry."""
    prompt = f"""You are a senior NOC engineer writing SOP documentation.
Generate a YAML entry for a new network issue following the exact format below.

New issue name: "{reason_name}"
Ticket count: {count}
Category: {category}

Here are two existing entries as format reference:
{_FEW_SHOT_EXAMPLES}

Generate ONLY the YAML content for the new issue. Include: name, count,
description, custops_check, caveats, tie_breaker, validation_steps (as a list),
and handset_cause. Match the style, tone, and level of detail of the examples."""

    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key or "ollama", base_url=settings.openai_api_base)
        resp = client.chat.completions.create(
            model=settings.openai_model or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You output valid YAML only. No preamble, no markdown."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=600,
        )
        text = resp.choices[0].message.content.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0].strip()
        parsed = yaml.safe_load(text)
        if isinstance(parsed, dict):
            parsed.setdefault("count", count)
            return parsed
        elif isinstance(parsed, list):
            entry = parsed[0]
            entry.setdefault("count", count)
            return entry
        logger.warning("LLM returned non-dict YAML for %s: %s", reason_name, text)
        return None
    except Exception as exc:
        logger.warning("SOP generation failed for %s: %s", reason_name, exc)
        return None


# ---------------------------------------------------------------------------
# Find the best category for an orphan
# ---------------------------------------------------------------------------

def _infer_category(reason_name: str, stories: dict) -> str:
    """Try to assign an orphan to an existing category based on name similarity."""
    q = _normalize(reason_name)
    for cat in stories.get("sop_framework", {}).get("categories", []):
        for issue in cat.get("issues", []):
            if q == _normalize(issue.get("name", "")):
                return cat["name"]
    # Fallback
    return "SIM & Provisioning Issues"


# ---------------------------------------------------------------------------
# Main sync function
# ---------------------------------------------------------------------------

def sync_story() -> list[dict]:
    """Compare KG reassignment_reasons against stories.yaml.

    - Detects orphans (KG reasons not in stories)
    - Detects count drifts (mismatched counts)
    - For orphan reasons: generates SOP via LLM and appends to stories.yaml
    - Updates drifted counts
    - Returns a list of warning dicts describing what was changed.

    Returns:
        List of dicts with keys: type (orphan/drift), reason, count, action.
    """
    warnings: list[dict] = []
    kg_reasons = _get_kg_reasons()
    stories = _load_yaml(_STORIES_PATH)
    issues_by_name = _get_stories_issues_by_name()

    kg_by_name: dict[str, dict] = {}
    for r in kg_reasons:
        kg_by_name[_normalize(r["value"])] = r

    orphans: list[dict] = []
    for r in kg_reasons:
        key = _normalize(r["value"])
        if key not in issues_by_name:
            orphans.append(r)
            warnings.append({
                "type": "orphan",
                "reason": r["value"],
                "count": r["count"],
                "timestamp": datetime.utcnow().isoformat(),
            })

    # Generate SOP for orphans
    for orphan in orphans:
        category = _infer_category(orphan["value"], stories)
        logger.info("Generating SOP for orphan: %s", orphan["value"])
        entry = _generate_sop_entry(orphan["value"], orphan["count"], category)
        if entry is None:
            continue
        # Append to the right category
        for cat in stories.get("sop_framework", {}).get("categories", []):
            if cat["name"] == category:
                cat.setdefault("issues", []).append(entry)
                break
        else:
            # Category not found — create a new one
            stories.setdefault("sop_framework", {}).setdefault("categories", []).append({
                "name": category,
                "issues": [entry],
            })
        warnings[-1]["action"] = f"Generated SOP and appended to category '{category}'"
        _dump_yaml(stories, _STORIES_PATH)

    # Update counts for existing issues that drifted
    stories_by_name = _get_stories_issues_by_name()
    for r in kg_reasons:
        key = _normalize(r["value"])
        existing = stories_by_name.get(key)
        if existing is None:
            continue
        # Check if count differs
        existing_count = existing.get("count")
        if existing_count is not None and existing_count != r["count"]:
            # Update in the YAML structure
            for cat in stories.get("sop_framework", {}).get("categories", []):
                for issue in cat.get("issues", []):
                    if _normalize(issue.get("name", "")) == key:
                        issue["count"] = r["count"]
                        warnings.append({
                            "type": "drift",
                            "reason": r["value"],
                            "old_count": existing_count,
                            "new_count": r["count"],
                            "timestamp": datetime.utcnow().isoformat(),
                            "action": "Count updated",
                        })
                    elif "counts" in issue:
                        for sub_name in issue["counts"]:
                            if _normalize(sub_name) == key:
                                issue["counts"][sub_name] = r["count"]
                                warnings.append({
                                    "type": "drift",
                                    "reason": sub_name,
                                    "old_count": existing_count,
                                    "new_count": r["count"],
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "action": "Sub-count updated",
                                })

    if warnings:
        _dump_yaml(stories, _STORIES_PATH)
        _dump_yaml({"sync_warnings": warnings}, _WARNINGS_PATH)
        logger.info("sync_story: %d changes applied", len(warnings))
    else:
        logger.info("sync_story: no changes needed")

    return warnings
