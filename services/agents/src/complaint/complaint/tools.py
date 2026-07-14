import json
import re
import time
import asyncio
import contextvars
from crewai.tools import tool
from crewai.utilities.streaming import StreamChunk, StreamChunkType
from ...qna.kg_retriever import kg_retriever
from .utils import (
    _get_causal_rules,
    _resolve_target_team_name,
    _hydrate_rule_from_service,
    _normalize_rule_entry,
    _map_node_to_service_id,
    _get_service_artifact,
    _coerce_str
)

active_queues = {}
_TOOL_USAGE_STATE = contextvars.ContextVar("tool_usage_state", default=None)

def _get_tool_usage_state() -> dict:
    state = _TOOL_USAGE_STATE.get()
    if state is None:
        state = {}
        _TOOL_USAGE_STATE.set(state)
    return state

def _log_observation_to_stream(query: str, observation_text: str):
    ctx = active_queues.get(query)
    targets = []
    if ctx is not None:
        targets.append(ctx)
    else:
        targets = list(active_queues.values())

    if not targets:
        return

    chunk = StreamChunk(
        content=observation_text,
        chunk_type=StreamChunkType.TEXT,
        task_id="mcca-01",
        agent_role="Customer Complaint Analyst",
        agent_id="mcca_observation"
    )
    for queue, loop in targets:
        try:
            loop.call_soon_threadsafe(queue.put_nowait, chunk)
        except Exception:
            pass

def _match_telecom_rule(query: str, causal_rules: dict) -> dict | None:
    raw_lower = query.lower()
    for rule in causal_rules.get("telecom_rules", []):
        trigger_kws = rule.get("trigger_keywords", [])
        if any(re.search(r"\b" + re.escape(kw) + r"\b", raw_lower) for kw in trigger_kws):
            target_id = rule.get("escalation_target")
            target_team_info = causal_rules.get("target_teams", {}).get(target_id, {})
            assignment_target = target_team_info.get("name", target_id)
            
            # Resolve prechecks
            precheck_defs = causal_rules.get("precheck_definitions", {})
            mandatory = []
            diag_chk = rule.get("diagnostic_check")
            if diag_chk:
                if diag_chk in precheck_defs:
                    mandatory.append(precheck_defs[diag_chk].get("label", diag_chk))
                else:
                    mandatory.append(diag_chk)
                
            return {
                "matched_node_id": rule.get("id"),
                "matched_label": rule.get("condition", "Operational Rule Match"),
                "match_type": "OperationalRule",
                "match_score": 1.0,
                "mandatory_prechecks": mandatory,
                "depends_on": [],
                "assignment_target": assignment_target,
                "reassignment_category": "Operational Rule",
                "resolution_category": f"Matched {rule.get('id')}",
                "message": rule.get("message", ""),
                "prohibited_routes": [],
                "triplets": [],
                "proxy_pointers": [],
                "ranked_candidates": []
            }
    return None

def _query_causal_knowledge_graph(query: str) -> str:
    causal_rules = _get_causal_rules()
    
    # 0. Check dynamic telecom operational rules
    rule_match = _match_telecom_rule(query, causal_rules)
    if rule_match:
        return json.dumps(rule_match)

    # 1. Classify the query as IT or Network first
    class_res = kg_retriever.classify_it_or_network(query)
    category = class_res["category"]
    
    # 2. If it's a Tie, return immediately with a clarification prompt
    if category == "Tie":
        return json.dumps({
            "matched_node_id": "tie_clarification",
            "matched_label": "Ambiguous Intent (Tie)",
            "match_type": "Tie",
            "match_score": 0.0,
            "mandatory_prechecks": [],
            "depends_on": [],
            "assignment_target": "pending_user_input",
            "reassignment_category": "Ambiguous",
            "resolution_category": "Pending Clarification",
            "message": "I detected that your issue might be related to activation (IT) or usage (Network). Can you please clarify if you are trying to activate a new service or if you are having issues using an already active service?",
            "prohibited_routes": [],
            "triplets": [],
            "proxy_pointers": [],
            "ranked_candidates": []
        })

    res = kg_retriever.retrieve_intent_and_pointers(query)
    raw_lower = query.lower()
    target_teams = causal_rules.get("target_teams", {})
    
    # Retrieve all ranked candidates from embeddings
    ranked = res.get("ranked_candidates", [])
    primary_candidate = ranked[0] if len(ranked) > 0 else None
    secondary_candidate = ranked[1] if len(ranked) > 1 else None

    primary_match = None
    if primary_candidate:
        p_node = primary_candidate["node"]
        p_id = p_node["id"]
        rule_entry = {}
        if p_node["type"] == "FAQ":
            rule_entry = next((f for f in causal_rules.get("faqs", []) if f["id"] == p_id), {})
        elif p_node["type"] == "Intent":
            rule_entry = causal_rules.get("intents", {}).get(p_id, {})
        rule_entry = _hydrate_rule_from_service(p_id, rule_entry)
        
        primary_match = _normalize_rule_entry({
            "node_id": p_id,
            "label": p_node["label"],
            "type": p_node["type"],
            "score": primary_candidate["score"],
            "mandatory_prechecks": rule_entry.get("mandatory_prechecks", []),
            "depends_on": rule_entry.get("depends_on", rule_entry.get("DependsOn", [])),
            "assignment_target": rule_entry.get("assignment_target", "core_smcs"),
            "prohibited_routes": rule_entry.get("prohibited_routes", []),
            "fallback_domain": rule_entry.get("fallback_domain", "Network")
        })

    secondary_match = None
    if secondary_candidate:
        s_node = secondary_candidate["node"]
        s_id = s_node["id"]
        rule_entry = {}
        if s_node["type"] == "FAQ":
            rule_entry = next((f for f in causal_rules.get("faqs", []) if f["id"] == s_id), {})
        elif s_node["type"] == "Intent":
            rule_entry = causal_rules.get("intents", {}).get(s_id, {})
        rule_entry = _hydrate_rule_from_service(s_id, rule_entry)
        
        secondary_match = _normalize_rule_entry({
            "node_id": s_id,
            "label": s_node["label"],
            "type": s_node["type"],
            "score": secondary_candidate["score"],
            "mandatory_prechecks": rule_entry.get("mandatory_prechecks", []),
            "depends_on": rule_entry.get("depends_on", rule_entry.get("DependsOn", [])),
            "assignment_target": rule_entry.get("assignment_target", "core_smcs"),
            "prohibited_routes": rule_entry.get("prohibited_routes", []),
            "fallback_domain": rule_entry.get("fallback_domain", "Network")
        })

    # Generic fallback domain match using causal_rules (regex with word boundaries)
    fallback_domain = "Network" if category == "Network" else "Provisioning"
    best_count = 0
    for f_domain, f_entry in causal_rules.get("fallbacks", {}).items():
        keywords = f_entry.get("keywords", [])
        count = 0
        for kw in keywords:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, raw_lower):
                count += 1
        if count > best_count:
            best_count = count
            fallback_domain = _resolve_domain_name(f_domain)

    matched_node_id = None
    matched_label = ""
    match_type = "Unresolved"
    match_score = 0.0
    mandatory = []
    depends_on = []
    
    # Defaults based on category
    if category == "IT":
        assignment_target = "IT Provisioning Support"
        reassignment_category = "Activation"
        resolution_category = "Assigned to IT Team"
    else:
        assignment_target = "SOC Mobile Core Support"
        reassignment_category = "Usage"
        resolution_category = "Assigned to Network Team"
        
    prohibited = []
    faq_action = ""
    faq_url = ""
    message = None

    # Confidence Threshold checks
    faq_threshold = 0.70
    intent_threshold = 0.50

    if primary_match:
        p_type = primary_match["type"]
        p_score = primary_match["score"]
        is_confident = (p_type == "FAQ" and p_score >= faq_threshold) or \
                       (p_type == "Intent" and p_score >= intent_threshold)
        if is_confident:
            matched_node_id = primary_match["node_id"]
            matched_label = primary_match["label"]
            match_type = p_type
            match_score = p_score
            mandatory = primary_match["mandatory_prechecks"]
            depends_on = primary_match["depends_on"]
            assignment_target = primary_match["assignment_target"]
            prohibited = primary_match["prohibited_routes"]
            if p_type == "FAQ":
                faq_rules = next((f for f in causal_rules.get("faqs", []) if f["id"] == matched_node_id), {})
                faq_action = faq_rules.get("action", "")
                faq_url = faq_rules.get("url", "")

    if matched_node_id is None:
        matched_node_id = f"fallback_{fallback_domain.lower()}"
        matched_label = f"{fallback_domain} General Domain Fallback"
        match_type = "Unresolved"
        match_score = 0.0
        domain_entry = causal_rules.get("fallbacks", {}).get(fallback_domain, {})
        mandatory = domain_entry.get("mandatory_prechecks", [])
        depends_on = domain_entry.get("depends_on", domain_entry.get("DependsOn", []))
        assignment_target = _resolve_target_team_name(domain_entry.get("assignment_target", "core_smcs"))
        prohibited = domain_entry.get("prohibited_routes", [])

    # Resolve escalation target key to human-readable target team name using target_teams
    team_entry = target_teams.get(assignment_target, {})
    assignment_target = team_entry.get("name", _resolve_target_team_name(assignment_target))

    if category == "IT" or fallback_domain == "Provisioning":
        reassignment_category = "Activation"
        resolution_category = f"Assigned to {assignment_target}"
    else:
        reassignment_category = "Usage"
        resolution_category = f"Assigned to {assignment_target}"

    # Present questionnaire for Network issues that are unresolved / general fallback
    if category == "Network" and matched_node_id.startswith("fallback_"):
        message = (
            "Please answer the following troubleshooting questions to filter the Network issue:\n"
            "1. Are you currently seeing signal bars on your device? (Yes/No)"
        )

    out = {
        "matched_node_id": matched_node_id,
        "matched_label": matched_label,
        "match_type": match_type,
        "match_score": match_score,
        "mandatory_prechecks": mandatory,
        "depends_on": depends_on,
        "assignment_target": assignment_target,
        "reassignment_category": reassignment_category,
        "resolution_category": resolution_category,
        "prohibited_routes": prohibited,
        "faq_action": faq_action,
        "faq_url": faq_url,
        "message": message,
        "triplets": res.get("triplets", []),
        "proxy_pointers": res.get("proxy_pointers", []),
        "ranked_candidates": ranked
    }
    return json.dumps(out)

def gate1_route_complaint(query: str) -> dict:
    import time as _time
    _g1_start = _time.perf_counter()

    # 0. Check dynamic telecom operational rules
    causal_rules = _get_causal_rules()
    target_teams = causal_rules.get("target_teams", {})
    rule_match = _match_telecom_rule(query, causal_rules)
    if rule_match:
        rule_match["confident"] = True
        state = _get_tool_usage_state() or {}
        user_role = state.get("user_role", "Customer_Ops")
        if user_role == "Network_Eng":
            try:
                from ..recommendations import get_historical_recommendations
                recs = get_historical_recommendations(query)
                if recs:
                    rec_lines = ["\n📊 Historical Recommendations (CBR):"]
                    for r in recs:
                        rec_lines.append(f"  - {r['complaint_number']}: '{r['issue_summary']}' -> {r['assignment_target']} ({int(r['score']*100)}% match)")
                    rule_match["message"] = (rule_match.get("message", "") or "") + "\n" + "\n".join(rec_lines)
            except Exception as e:
                print(f"[CBR] Error generating recommendations: {e}")
        return rule_match

    # 1. Classify the query as IT or Network
    class_res = kg_retriever.classify_it_or_network(query)
    category = class_res["category"]

    # 2. If it's a Tie, return immediately with a clarification prompt
    if category == "Tie":
        elapsed = (_time.perf_counter() - _g1_start) * 1000
        print(f"[Gate1] Tie detected, returning clarification ({elapsed:.1f}ms)")
        return {
            "confident": True,
            "issue_summary": "Ambiguous Intent (Tie)",
            "mandatory_prechecks": [],
            "depends_on": [],
            "assignment_target": "pending_user_input",
            "reassignment_category": "Ambiguous",
            "resolution_category": "Pending Clarification",
            "message": "I detected that your issue might be related to activation (IT) or usage (Network). Can you please clarify if you are trying to activate a new service or if you are having issues using an already active service?"
        }

    # 3. Bi-encoder retrieval WITHOUT cross-encoder (fast path)
    res = kg_retriever.retrieve_intent_and_pointers(query, use_cross_encoder=False)
    raw_lower = query.lower()

    # Retrieve top ranked candidates
    ranked = res.get("ranked_candidates", [])
    primary_candidate = ranked[0] if len(ranked) > 0 else None

    primary_match = None
    if primary_candidate:
        p_node = primary_candidate["node"]
        p_id = p_node["id"]
        rule_entry = {}
        if p_node["type"] == "FAQ":
            rule_entry = next((f for f in causal_rules.get("faqs", []) if f["id"] == p_id), {})
        elif p_node["type"] == "Intent":
            rule_entry = causal_rules.get("intents", {}).get(p_id, {})
        rule_entry = _hydrate_rule_from_service(p_id, rule_entry)

        primary_match = _normalize_rule_entry({
            "node_id": p_id,
            "label": p_node["label"],
            "type": p_node["type"],
            "score": primary_candidate["score"],
            "mandatory_prechecks": rule_entry.get("mandatory_prechecks", []),
            "depends_on": rule_entry.get("depends_on", rule_entry.get("DependsOn", [])),
            "assignment_target": rule_entry.get("assignment_target", "core_smcs"),
            "prohibited_routes": rule_entry.get("prohibited_routes", []),
            "fallback_domain": rule_entry.get("fallback_domain", "Network")
        })

    # Generic fallback domain match using causal_rules (regex with word boundaries)
    fallback_domain = "Network" if category == "Network" else "Provisioning"
    best_count = 0
    for f_domain, f_entry in causal_rules.get("fallbacks", {}).items():
        keywords = f_entry.get("keywords", [])
        count = 0
        for kw in keywords:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, raw_lower):
                count += 1
        if count > best_count:
            best_count = count
            fallback_domain = _resolve_domain_name(f_domain)

    matched_node_id = None
    matched_label = ""
    match_score = 0.0
    mandatory = []
    depends_on = []

    # Defaults based on category
    if category == "IT":
        assignment_target = "IT Provisioning Support"
        reassignment_category = "Activation"
        resolution_category = "Assigned to IT Team"
    else:
        assignment_target = "SOC Mobile Core Support"
        reassignment_category = "Usage"
        resolution_category = "Assigned to Network Team"

    message = None

    # Confidence Threshold checks
    faq_threshold = 0.70
    intent_threshold = 0.50

    if primary_match:
        p_type = primary_match["type"]
        p_score = primary_match["score"]
        is_confident = (p_type == "FAQ" and p_score >= faq_threshold) or \
                       (p_type == "Intent" and p_score >= intent_threshold)
        if is_confident:
            matched_node_id = primary_match["node_id"]
            matched_label = primary_match["label"]
            match_score = p_score
            mandatory = primary_match["mandatory_prechecks"]
            depends_on = primary_match["depends_on"]
            assignment_target = primary_match["assignment_target"]

    if matched_node_id is None:
        matched_node_id = f"fallback_{fallback_domain.lower()}"
        matched_label = f"{fallback_domain} General Domain Fallback"
        match_score = 0.0
        domain_entry = causal_rules.get("fallbacks", {}).get(fallback_domain, {})
        mandatory = domain_entry.get("mandatory_prechecks", [])
        depends_on = domain_entry.get("depends_on", domain_entry.get("DependsOn", []))
        assignment_target = _resolve_target_team_name(domain_entry.get("assignment_target", "core_smcs"))

    # Resolve escalation target key to human-readable target team name using target_teams
    team_entry = target_teams.get(assignment_target, {})
    assignment_target = team_entry.get("name", _resolve_target_team_name(assignment_target))

    if category == "IT" or fallback_domain == "Provisioning":
        reassignment_category = "Activation"
        resolution_category = f"Assigned to {assignment_target}"
    else:
        reassignment_category = "Usage"
        resolution_category = f"Assigned to {assignment_target}"

    # Present questionnaire for Network issues that are unresolved / general fallback
    if category == "Network" and matched_node_id.startswith("fallback_"):
        message = (
            "Please answer the following troubleshooting questions to filter the Network issue:\n"
            "1. Are you currently seeing signal bars on your device? (Yes/No)"
        )

    elapsed = (_time.perf_counter() - _g1_start) * 1000
    print(f"[Gate1] Routed to '{assignment_target}' (score={match_score:.2f}, {elapsed:.1f}ms)")

    return {
        "confident": True,
        "matched_node_id": matched_node_id,
        "issue_summary": matched_label,
        "mandatory_prechecks": mandatory,
        "depends_on": depends_on,
        "assignment_target": assignment_target,
        "reassignment_category": reassignment_category,
        "resolution_category": resolution_category,
        "message": message
    }

@tool("query_causal_knowledge_graph", max_usage_count=1)
def query_causal_knowledge_graph(query: str) -> str:
    """Queries the Causal Knowledge Graph (CKG) for the closest matched Intent or FAQ.
    Returns matched node ID, node label, match type, match score, and adjacent triplets.
    """
    query = _coerce_str(query)
    state = _get_tool_usage_state()
    cache_key = ("query_causal_knowledge_graph", query)
    if cache_key in state:
        return state[cache_key]
    res = _query_causal_knowledge_graph(query)
    state[cache_key] = res
    _log_observation_to_stream(query, f"\nObservation: {res}\n\n")
    return res

def _evaluate_prechecks(query: str, matched_node_id: str) -> str:
    causal_rules = _get_causal_rules()
    mandatory = []
    assignment_target = _resolve_target_team_name("core_smcs")
    
    # Check FAQs
    faq_entry = next((f for f in causal_rules.get("faqs", []) if f["id"] == matched_node_id), None)
    if faq_entry:
        mandatory = faq_entry.get("mandatory_prechecks", [])
        assignment_target = _resolve_target_team_name(faq_entry.get("assignment_target", "core_smcs"))
    else:
        # Check Intents
        intent_entry = causal_rules.get("intents", {}).get(matched_node_id)
        if intent_entry:
            mandatory = intent_entry.get("mandatory_prechecks", [])
            assignment_target = _resolve_target_team_name(intent_entry.get("assignment_target", "core_smcs"))
        else:
            # Check Fallbacks
            fallback_domain = "Network"
            if "fallback_" in matched_node_id:
                fallback_domain = matched_node_id.replace("fallback_", "").capitalize()
            domain_entry = causal_rules.get("fallbacks", {}).get(fallback_domain)
            if domain_entry:
                mandatory = domain_entry.get("mandatory_prechecks", [])
                assignment_target = _resolve_target_team_name(domain_entry.get("assignment_target", "core_smcs"))
            else:
                mandatory = ["Check BSS profile status"]
                assignment_target = _resolve_target_team_name("core_smcs")

    completed = []
    raw_lower = query.lower()
    precheck_rules = causal_rules.get("precheck_rules", {})
    for precheck_str, keywords in precheck_rules.items():
        if precheck_str in mandatory:
            for kw in keywords:
                if kw in raw_lower:
                    completed.append(precheck_str)
                    break

    missing = [m for m in mandatory if m not in completed]
    
    precheck_defs = causal_rules.get("precheck_definitions", {})
    def get_label(item):
        service_id = _map_node_to_service_id(matched_node_id)
        if service_id:
            service = _get_service_artifact(service_id)
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
        return item

    mandatory_labels = [get_label(m) for m in mandatory]
    completed_labels = [get_label(c) for c in completed]
    missing_labels = [get_label(m) for m in missing]

    resource_status = _evaluate_resource_dependency(query, matched_node_id)

    return json.dumps({
        "mandatory_prechecks": mandatory_labels,
        "completed": completed_labels,
        "missing": missing_labels,
        "resource_status": resource_status,
    })

@tool("evaluate_prechecks")
def evaluate_prechecks(query: str, matched_node_id: str) -> str:
    """Evaluates which mandatory network prechecks have been performed based on query context.
    """
    query = _coerce_str(query)
    matched_node_id = _coerce_str(matched_node_id)
    state = _get_tool_usage_state()
    cache_key = ("evaluate_prechecks", query, matched_node_id)
    if cache_key in state:
        return state[cache_key]
    res = _evaluate_prechecks(query, matched_node_id)
    state[cache_key] = res
    _log_observation_to_stream(query, f"\nObservation: {res}\n\n")
    return res

def _trace_causal_chain_internal(query: str, matched_node_id: str, ranked_candidates_json: str = "") -> dict:
    prechecks_json = _evaluate_prechecks(query=query, matched_node_id=matched_node_id)
    prechecks = json.loads(prechecks_json)

    node_score_map = {}
    try:
        if ranked_candidates_json:
            parsed = json.loads(ranked_candidates_json)
            if isinstance(parsed, dict):
                node_score_map = parsed
            elif isinstance(parsed, list):
                for item in parsed:
                    nid = None
                    sc = 0.0
                    if isinstance(item, dict) and "node" in item and "score" in item:
                        nid = item["node"].get("id")
                        sc = item.get("score", 0.0)
                    if nid:
                        node_score_map[nid] = sc
    except Exception:
        node_score_map = {}

    try:
        trace_res = kg_retriever.trace_causal_chain(matched_node_id, node_score_map)
    except Exception as e:
        trace_res = {"error": str(e)}

    return {
        "prechecks": prechecks,
        "trace": trace_res
    }

@tool("trace_causal_chain", max_usage_count=1)
def trace_causal_chain(query: str, matched_node_id: str) -> str:
    """Traces downstream components and relationships affected by the matched CKG node.
    """
    query = _coerce_str(query)
    matched_node_id = _coerce_str(matched_node_id)
    state = _get_tool_usage_state()
    cache_key = ("trace_causal_chain", query, matched_node_id)
    if cache_key in state:
        return state[cache_key]
    res = _trace_causal_chain_internal(query, matched_node_id)
    res_json = json.dumps(res)
    state[cache_key] = res_json
    _log_observation_to_stream(query, f"\nObservation: {res_json}\n\n")
    return res_json

def _evaluate_resource_dependency(query: str, matched_node_id: str) -> str:
    causal_rules = _get_causal_rules()
    intent_rules = causal_rules.get("intents", {}).get(matched_node_id, {})
    depends_on = intent_rules.get("depends_on", intent_rules.get("DependsOn", []))
    
    if not depends_on:
        return "resource_none"

    raw_lower = query.lower()
    depletion_indicators = [
        "suddenly stopped", "consumed", "depleted", "run out", "quota finished", 
        "empty balance", "no credit", "no balance", "exhausted", "used up", "zero balance"
    ]
    has_depletion_indicator = any(indicator in raw_lower for indicator in depletion_indicators)
    
    if has_depletion_indicator:
        resource_rules = causal_rules.get("resource_rules", {})
        for resource_id in depends_on:
            keywords = resource_rules.get(resource_id, [])
            if any(kw in raw_lower for kw in keywords):
                return "resource_depleted"
        return "resource_depleted"
        
    if any(phrase in raw_lower for phrase in ["no issue found", "precheck completed", "device ok", "settings ok"]):
        return "resource_depleted"
        
    return "resource_unverified"

@tool("diagnose_complaint", max_usage_count=1)
def diagnose_complaint(query: str) -> str:
    """Runs full root-cause analysis on a telecom complaint.
    """
    import time as _time
    _g2_start = _time.perf_counter()

    query = _coerce_str(query)
    state = _get_tool_usage_state()
    cache_key = ("diagnose_complaint", query)
    if cache_key in state:
        cached = state[cache_key]
        _log_observation_to_stream(query, f"\nObservation: {cached}\n\n")
        return cached

    res = kg_retriever.retrieve_intent_and_pointers(query, use_cross_encoder=True)
    intent_node = res.get("intent_node")
    matched_node_id = intent_node["id"] if intent_node else ""

    if not matched_node_id:
        try:
            ckg_res = json.loads(_query_causal_knowledge_graph(query))
            matched_node_id = ckg_res.get("matched_node_id", "")
        except Exception:
            matched_node_id = ""

    trace_result = _trace_causal_chain_internal(query, matched_node_id, "")

    combined = {
        "prechecks": trace_result.get("prechecks", {}),
        "trace": trace_result.get("trace", {}),
        "matched_intent": intent_node["label"] if intent_node else "Unknown",
        "matched_node_id": matched_node_id,
        "confidence": res.get("intent_score", 0.0),
    }

    elapsed = (_time.perf_counter() - _g2_start) * 1000
    print(f"[Gate2] diagnose_complaint completed in {elapsed:.1f}ms")

    res_json = json.dumps(combined)
    state[cache_key] = res_json
    _log_observation_to_stream(query, f"\nObservation: {res_json}\n\n")
    return res_json

def _generate_causal_signature(matched_node_id: str, query: str) -> str:
    causal_rules = _get_causal_rules()
    intent_rules = causal_rules.get("intents", {}).get(matched_node_id, {})
    depends_on = intent_rules.get("depends_on", intent_rules.get("DependsOn", []))
    
    resource_status = _evaluate_resource_dependency(query, matched_node_id)
    prechecks_json = _evaluate_prechecks(query, matched_node_id)
    prechecks = json.loads(prechecks_json)
    
    sig = f"Intent: {matched_node_id} | Prechecks: {prechecks['completed']} | Missing: {prechecks['missing']} | Dependency: {depends_on} ({resource_status})"
    return sig

@tool("generate_causal_signature")
def generate_causal_signature(matched_node_id: str, query: str) -> str:
    """Generates a diagnostic routing signature for escalation targeting.
    """
    matched_node_id = _coerce_str(matched_node_id)
    query = _coerce_str(query)
    res = _generate_causal_signature(matched_node_id, query)
    _log_observation_to_stream(query, f"\nObservation: {res}\n\n")
    return res

def _log_unresolved_complaint(query: str, matched_node_id: str) -> str:
    from agenticaiops_shared.config import settings
    unresolved_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "unresolved_complaints.json"
    ))
    draft_id = f"faq_draft_{int(time.time())}"
    
    causal_rules = _get_causal_rules()
    fallback_domain = "Network"
    if "fallback_" in matched_node_id:
        fallback_domain = matched_node_id.replace("fallback_", "").capitalize()
        
    domain_entry = causal_rules.get("fallbacks", {}).get(fallback_domain, {})
    mandatory = domain_entry.get("mandatory_prechecks", [])
    assignment_target = _resolve_target_team_name(domain_entry.get("assignment_target", "core_smcs"))

    draft = {
        "id": draft_id,
        "label": f"Draft FAQ: {query[:40]}...",
        "query": query,
        "suggested_domain": fallback_domain,
        "suggested_prechecks": mandatory,
        "suggested_escalation": assignment_target,
        "timestamp": int(time.time())
    }
    drafts = []
    if os.path.exists(unresolved_path):
        try:
            with open(unresolved_path, "r") as f:
                drafts = json.load(f)
        except Exception:
            drafts = []
    drafts.append(draft)
    try:
        with open(unresolved_path, "w") as f:
            json.dump(drafts, f, indent=2)
        return f"Logged unresolved query draft: {draft_id}"
    except Exception as e:
        return f"Error logging unresolved query draft: {e}"

@tool("log_unresolved_complaint")
def log_unresolved_complaint(query: str, matched_node_id: str) -> str:
    """Logs an unresolved query to unresolved_complaints.json for admin review.
    """
    query = _coerce_str(query)
    matched_node_id = _coerce_str(matched_node_id)
    res = _log_unresolved_complaint(query, matched_node_id)
    out_dict = {
        "result": res,
        "instructions": "Unresolved complaint logged. Diagnostic steps are complete. You MUST NOT call any more tools. Proceed directly to Step 5 (Final Answer). You MUST state in your final answer that the query is out of scope and has been logged for admin review."
    }
    res_json = json.dumps(out_dict)
    _log_observation_to_stream(query, f"\nObservation: {res_json}\n\n")
    return res_json
