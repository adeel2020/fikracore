import json
from pydantic import BaseModel
from typing import List
from complaint.complaint.utils import _get_causal_rules, _get_service_artifact, _map_node_to_service_id

class AgentResponse(BaseModel):
    issue_summary: str
    mandatory_prechecks: List[str]
    depends_on: List[str]
    assignment_target: str
    reassignment_category: str
    resolution_category: str
    message: str | None = None

def _agent_response_to_dict(value) -> dict:
    if value is None:
        return {}
    if isinstance(value, AgentResponse):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump()
        except Exception:
            pass
    if hasattr(value, "dict"):
        try:
            return value.dict()
        except Exception:
            pass
    return {}

def _format_structured_event(payload: dict, query: str = None) -> str:
    message = payload.get("message", "")
    is_tie = str(payload.get("matched_node_id")) == "tie_clarification" or "clarify" in str(payload.get("resolution_category", "")).lower()
    is_questionnaire = (
        str(payload.get("matched_node_id")).startswith("fallback_") or
        "troubleshooting questions" in str(message).lower()
    )
    if is_tie or is_questionnaire:
        return f"final answer: {message}\n"

    # Load causal rules to resolve placeholders to descriptive labels
    causal_rules = _get_causal_rules()
    precheck_defs = causal_rules.get("precheck_definitions", {})
    other_nodes = causal_rules.get("other_nodes", {})
    target_teams = causal_rules.get("target_teams", {})
    intents = causal_rules.get("intents", {})
    fallbacks = causal_rules.get("fallbacks", {})

    service_id = _map_node_to_service_id(payload.get("matched_node_id", ""))
    service = _get_service_artifact(service_id) if service_id else None

    def get_rich_precheck(item):
        if service:
            for chk in service.get("mandatory_prechecks", []):
                if chk.get("id") == item or chk.get("label") == item:
                    label = chk.get("label", "")
                    suffix = "" if label.strip().lower().endswith("status") else " status"
                    return f"Verify the {label}{suffix} (Execute Core Command: '{chk.get('command')}')"

        if item in precheck_defs:
            entry = precheck_defs[item]
            label = entry.get("label", "")
            suffix = "" if label.strip().lower().endswith("status") else " status"
            return f"Verify the {label}{suffix} (Execute Core Command: '{entry.get('command')}')"
        for k, entry in precheck_defs.items():
            if entry.get("label") == item or f"Verify the {entry.get('label')} status" in item:
                label = entry.get("label", "")
                suffix = "" if label.strip().lower().endswith("status") else " status"
                return f"Verify the {label}{suffix} (Execute Core Command: '{entry.get('command')}')"
        return item

    def get_rich_dependency(item):
        if service:
            for dep in service.get("dependencies", []):
                if dep.get("node") == item or dep.get("label") == item:
                    return f"{dep.get('label')} ({dep.get('description')})"

        if item in other_nodes:
            entry = other_nodes[item]
            return f"{entry.get('label')} ({entry.get('description')})"
        for k, entry in other_nodes.items():
            if entry.get("label") == item or entry.get("label") in item:
                return f"{entry.get('label')} ({entry.get('description')})"
        
        if item in target_teams:
            return f"{target_teams[item].get('name', item)} Team"

        if item in intents:
            return intents[item].get('label', item)
        if item.replace("fallback_", "").capitalize() in fallbacks:
            return f"{item.replace('fallback_', '').capitalize()} Domain settings"
        return item

    lines = ["__STRUCTURED_EVENT__"]
    lines.append(f"issue_summary: {payload.get('issue_summary', '')}")
    prechecks = payload.get("mandatory_prechecks", []) or []
    depends_on = payload.get("depends_on", []) or []
    
    lines.append("mandatory_prechecks:")
    for item in prechecks:
        lines.append(f"- {get_rich_precheck(item)}")
        
    lines.append("depends_on:")
    for item in depends_on:
        lines.append(f"- {get_rich_dependency(item)}")
    lines.append(f"assignment_target: {payload.get('assignment_target', '')}")
    lines.append(f"reassignment_category: {payload.get('reassignment_category', '')}")
    lines.append(f"resolution_category: {payload.get('resolution_category', '')}")
    if message:
        lines.append(f"message: {message}")
    lines.append("__END_STRUCTURED_EVENT__")
    return "\n".join(lines) + "\n"
