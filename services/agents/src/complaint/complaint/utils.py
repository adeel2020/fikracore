import os
import yaml
import re
from agenticaiops_shared.config import settings

_causal_rules_cache = None
_causal_rules_mtime = 0

def _coerce_str(value) -> str:
    """Coerce a value to a plain string.
    
    CrewAI's ReAct loop sometimes passes tool arguments as schema dicts
    (e.g. {"description": "...", "type": "str"}) instead of plain strings.
    This helper extracts the actual string value defensively.
    """
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("description", "value", "query", "input", "text"):
            if key in value and isinstance(value[key], str):
                return value[key]
        for v in value.values():
            if isinstance(v, str) and v != "str":
                return v
    return str(value)


def _get_causal_rules():
    global _causal_rules_cache, _causal_rules_mtime
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "causal_rules.yaml"
    ))
    try:
        mtime = os.path.getmtime(path)
        if _causal_rules_cache is None or mtime > _causal_rules_mtime:
            with open(path, "r") as f:
                raw_rules = yaml.safe_load(f) or {}
            
            # Follow file references in rules dictionary dynamically
            compiled_rules = {}
            for section_name, items in raw_rules.items():
                if isinstance(items, dict):
                    compiled_rules[section_name] = {}
                    for item_id, path_or_val in items.items():
                        if isinstance(path_or_val, str) and "artifact_store/" in path_or_val:
                            if "#" in path_or_val:
                                file_rel, key = path_or_val.split("#", 1)
                            else:
                                file_rel, key = path_or_val, None
                                
                            artifact_path = os.path.abspath(os.path.join(
                                os.path.dirname(__file__), "..", file_rel
                            ))
                            if os.path.exists(artifact_path):
                                with open(artifact_path, "r") as art_f:
                                    full_data = yaml.safe_load(art_f) or {}
                                    if key:
                                        entry_val = full_data.get(key)
                                        if isinstance(entry_val, dict):
                                            entry_val = entry_val.copy()
                                            entry_val["id"] = key
                                        compiled_rules[section_name][item_id] = entry_val
                                    else:
                                        compiled_rules[section_name][item_id] = full_data
                            else:
                                compiled_rules[section_name][item_id] = path_or_val
                        else:
                            compiled_rules[section_name][item_id] = path_or_val
                elif isinstance(items, list):
                    compiled_rules[section_name] = []
                    for item in items:
                        if isinstance(item, str) and item.startswith("artifact_store/"):
                            artifact_path = os.path.abspath(os.path.join(
                                os.path.dirname(__file__), "..", item
                            ))
                            if os.path.exists(artifact_path):
                                with open(artifact_path, "r") as art_f:
                                    compiled_rules[section_name].append(yaml.safe_load(art_f))
                            else:
                                compiled_rules[section_name].append(item)
                        else:
                            compiled_rules[section_name].append(item)
                else:
                    compiled_rules[section_name] = items
            
            # Merge nodes, resources, and constraints into in-memory other_nodes for backwards compatibility
            other_nodes = {}
            for sec in ["nodes", "resources", "constraints"]:
                if sec in compiled_rules:
                    other_nodes.update(compiled_rules[sec])
            compiled_rules["other_nodes"] = other_nodes

            _causal_rules_cache = compiled_rules
            _causal_rules_mtime = mtime
    except Exception as e:
        print(f"[Causal Rules] Error compiling master index: {e}")
        if _causal_rules_cache is None:
            _causal_rules_cache = {}
    return _causal_rules_cache

def _deduplicate_sentences(text: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    seen = set()
    unique = []
    for s in sentences:
        s_clean = s.strip().lower()
        if s_clean not in seen and len(s_clean) > 0:
            seen.add(s_clean)
            unique.append(s.strip())
    return " ".join(unique)

def _generate_dynamic_agent_intro(query: str, matched_label: str) -> str:
    try:
        from litellm import completion
        system_prompt = (
            "You are a Senior Telecom Analyst. Write exactly one short, natural, professional, and friendly introductory sentence "
            "stating that you have analyzed the customer query and mapped it to the appropriate resolution target. "
            "Do not write multiple sentences. Do not repeat yourself. Do not mention any JSON or internal technical terms."
        )
        user_prompt = f"Complaint: '{query}'\nMatched Area: '{matched_label}'"
        response = completion(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            api_key=settings.openai_api_key or "ollama",
            base_url=settings.openai_api_base,
        )
        raw_text = response.choices[0].message.content.strip()
        return _deduplicate_sentences(raw_text)
    except Exception as e:
        print(f"[Dynamic Intro] Error generating intro: {e}")
        return f"I have analyzed your request regarding {matched_label} and identified the required diagnostics."

def _generate_dynamic_agent_outro(target_team: str) -> str:
    try:
        from litellm import completion
        system_prompt = (
            "You are a Senior Telecom Analyst. Write exactly one short instruction sentence advising the user to perform "
            "the mandatory prechecks listed above before proceeding with the escalation to the target team. "
            "Do not write multiple sentences. Do not repeat yourself. Do not include introductory filler."
        )
        user_prompt = f"Target Team: {target_team}"
        response = completion(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            api_key=settings.openai_api_key or "ollama",
            base_url=settings.openai_api_base,
        )
        raw_text = response.choices[0].message.content.strip()
        return _deduplicate_sentences(raw_text)
    except Exception as e:
        print(f"[Dynamic Outro] Error generating outro: {e}")
        return f"Please complete the mandatory prechecks before escalating this ticket."

def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")

def _resolve_domain_name(domain_key: str) -> str:
    causal_rules = _get_causal_rules()
    domains = causal_rules.get("domains", []) or []
    if domain_key in domains:
        return domain_key
    normalized = _normalize_key(domain_key)
    for domain in domains:
        if _normalize_key(str(domain)) == normalized:
            return str(domain)
    return str(domain_key)

def _resolve_target_team_name(team_key_or_name: str) -> str:
    causal_rules = _get_causal_rules()
    target_teams = causal_rules.get("target_teams", {})
    if team_key_or_name in target_teams:
        return target_teams[team_key_or_name].get("name", team_key_or_name)
    normalized = _normalize_key(team_key_or_name)
    for tid, entry in target_teams.items():
        if tid == normalized or _normalize_key(entry.get("name", "")) == normalized:
            return entry.get("name", team_key_or_name)
    return team_key_or_name

def _resolve_team(team_key_or_name: str) -> dict:
    causal_rules = _get_causal_rules()
    target_teams = causal_rules.get("target_teams", {})
    if team_key_or_name in target_teams:
        team_entry = target_teams[team_key_or_name].copy()
        team_entry["key"] = team_key_or_name
        return team_entry
    normalized = _normalize_key(team_key_or_name)
    for tid, entry in target_teams.items():
        if tid == normalized or _normalize_key(entry.get("name", "")) == normalized:
            team_entry = entry.copy()
            team_entry["key"] = tid
            return team_entry
    return {"name": team_key_or_name, "key": team_key_or_name}

def _resolve_target_team(team_key_or_name: str) -> dict:
    return _resolve_team(team_key_or_name)

def _resolve_rule_domain(fallback_domain: str | None) -> str:
    if not fallback_domain:
        return _resolve_domain_name("Network")
    return _resolve_domain_name(fallback_domain)

def _normalize_rule_entry(entry: dict, default_domain: str = "Network") -> dict:
    domain_name = _resolve_rule_domain(entry.get("fallback_domain", default_domain))
    team_key = entry.get("assignment_target", "")
    team = _resolve_target_team(team_key)
    return {
        **entry,
        "depends_on": entry.get("depends_on", entry.get("DependsOn", [])) or [],
        "assignment_target": team.get("name", team_key),
        "assignment_target_key": team.get("key", team_key),
        "fallback_domain": domain_name,
        "prohibited_routes": entry.get("prohibited_routes", []) or [],
    }

_service_artifacts_cache = {}

def _get_service_artifact(service_id: str) -> dict | None:
    global _service_artifacts_cache
    if service_id in _service_artifacts_cache:
        return _service_artifacts_cache[service_id]
        
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "artifact_store", "services_artifact", f"{service_id}.yaml"
    ))
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                _service_artifacts_cache[service_id] = data
                return data
        except Exception as e:
            print(f"[Service Artifact] Error loading {service_id}: {e}")
    return None

def _map_node_to_service_id(node_id: str) -> str | None:
    causal_rules = _get_causal_rules()
    
    # 1. Check Intents
    intents = causal_rules.get("intents", {})
    if node_id in intents:
        return intents[node_id].get("service_id")
        
    # 2. Check FAQs
    faqs = causal_rules.get("faqs", [])
    for faq in faqs:
        if faq.get("id") == node_id:
            return faq.get("service_id")
            
    # 3. Check general rules mapping or defaults
    return None

def _hydrate_rule_from_service(node_id: str, rule_entry: dict) -> dict:
    service_id = _map_node_to_service_id(node_id)
    if not service_id:
        return rule_entry
        
    service = _get_service_artifact(service_id)
    if not service:
        return rule_entry
        
    hydrated = rule_entry.copy()
    
    # Map service attributes back
    if "owning_team" in service:
        hydrated["assignment_target"] = service["owning_team"]
        
    if "mandatory_prechecks" in service:
        prechecks = []
        for chk in service["mandatory_prechecks"]:
            if isinstance(chk, dict) and "id" in chk:
                prechecks.append(chk["id"])
            elif isinstance(chk, str):
                prechecks.append(chk)
        hydrated["mandatory_prechecks"] = prechecks
        
    if "dependencies" in service:
        deps = []
        for dep in service["dependencies"]:
            if isinstance(dep, dict) and "node" in dep:
                deps.append(dep["node"])
            elif isinstance(dep, str):
                deps.append(dep)
        hydrated["depends_on"] = deps
        
    return hydrated
