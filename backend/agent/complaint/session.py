import os
import json
import time
from backend.agent.complaint.utils import _get_causal_rules, _resolve_target_team_name

def _route_diagnostics(original_query: str, diagnostics: dict) -> dict:
    signal = diagnostics.get("signal", True)
    others_affected = diagnostics.get("others_affected", True)
    restarted = diagnostics.get("restarted", True)
    
    if not signal:
        target = "ran_support"
        msg = "User reported no signal bars. Escalated to RAN Support for local coverage investigation."
    elif others_affected:
        target = "ran_support"
        msg = "Multiple users in the location are affected. Escalated to RAN Support to check for local cell site outage."
    elif not restarted:
        target = "device_support"
        msg = "User has not restarted the device. Escalated to VoLTE Device Support; operator advised user to perform a soft device reset."
    else:
        target = "core_smcs"
        msg = "Individual subscriber service issue (Signal OK, Device restarted). Escalated to SOC Mobile Core Support for core network profile trace."
        
    causal_rules = _get_causal_rules()
    target_teams = causal_rules.get("target_teams", {})
    team_name = target_teams.get(target, {}).get("name", "SOC Mobile Core Support")
    
    return {
        "confident": True,
        "matched_node_id": "network_diagnostics_resolved",
        "issue_summary": f"Refined Network Complaint: {original_query}",
        "mandatory_prechecks": ["Check VLR Latching & Mobile Core Status"],
        "depends_on": [],
        "assignment_target": team_name,
        "reassignment_category": "Usage",
        "resolution_category": f"Assigned to {team_name}",
        "message": msg
    }

def _reconstruct_session_state(session_id: str) -> dict:
    state = {"status": "START", "pending_query": None, "question_index": 1, "answers": []}
    if not session_id:
        return state
        
    try:
        from backend.database.db import SessionLocal
        from backend.database.models import ChatMessage as ChatMessageModel
        
        with SessionLocal() as db:
            messages = db.query(ChatMessageModel).filter_by(session_id=session_id).order_by(ChatMessageModel.created_at.asc()).all()
            if not messages:
                return state
                
            user_msgs = [m for m in messages if m.role == "user"]
            assistant_msgs = [m for m in messages if m.role == "assistant"]
            
            # Find original complaint query
            short_responses = {"yes", "no", "it", "network", "usage", "activation", "prepaid", "postpaid", "1", "2", "3", "y", "n"}
            original_query = None
            for u_msg in reversed(user_msgs):
                clean_txt = u_msg.content.strip().lower().translate(str.maketrans("", "", '!?.,-'))
                if clean_txt not in short_responses and len(clean_txt) > 5:
                    original_query = u_msg.content
                    break
                    
            if not original_query and user_msgs:
                original_query = user_msgs[0].content
                
            state["pending_query"] = original_query
            
            if assistant_msgs:
                last_assistant_text = assistant_msgs[-1].content
                
                # Check for Intent Classification prompt
                if "related to activation (IT) or usage (Network)" in last_assistant_text:
                    state["status"] = "INTENT_CLASSIFICATION"
                    return state
                    
                # Check for Network Diagnostics questions
                if "Are you currently seeing signal bars" in last_assistant_text:
                    state["status"] = "NETWORK_DIAGNOSTICS"
                    state["question_index"] = 1
                    
                    q1_ans = True
                    if user_msgs:
                        ans_txt = user_msgs[-1].content.strip().lower()
                        if ans_txt in ["no", "n", "false", "f", "0"]:
                            q1_ans = False
                    state["answers"] = [q1_ans]
                    return state
                    
                elif "Are other users in your immediate location" in last_assistant_text:
                    state["status"] = "NETWORK_DIAGNOSTICS"
                    state["question_index"] = 2
                    
                    q1_ans = True
                    q2_ans = True
                    if len(user_msgs) >= 2:
                        ans1 = user_msgs[-2].content.strip().lower()
                        ans2 = user_msgs[-1].content.strip().lower()
                        if ans1 in ["no", "n", "false", "f", "0"]:
                            q1_ans = False
                        if ans2 in ["no", "n", "false", "f", "0"]:
                            q2_ans = False
                    elif len(user_msgs) == 1:
                        ans2 = user_msgs[-1].content.strip().lower()
                        if ans2 in ["no", "n", "false", "f", "0"]:
                            q2_ans = False
                            
                    state["answers"] = [q1_ans, q2_ans]
                    return state
                    
                elif "Have you restarted your device" in last_assistant_text:
                    state["status"] = "NETWORK_DIAGNOSTICS"
                    state["question_index"] = 3
                    
                    q1_ans = True
                    q2_ans = True
                    q3_ans = True
                    if len(user_msgs) >= 3:
                        ans1 = user_msgs[-3].content.strip().lower()
                        ans2 = user_msgs[-2].content.strip().lower()
                        ans3 = user_msgs[-1].content.strip().lower()
                        if ans1 in ["no", "n", "false", "f", "0"]:
                            q1_ans = False
                        if ans2 in ["no", "n", "false", "f", "0"]:
                            q2_ans = False
                        if ans3 in ["no", "n", "false", "f", "0"]:
                            q3_ans = False
                    elif len(user_msgs) == 2:
                        ans2 = user_msgs[-2].content.strip().lower()
                        ans3 = user_msgs[-1].content.strip().lower()
                        if ans2 in ["no", "n", "false", "f", "0"]:
                            q2_ans = False
                        if ans3 in ["no", "n", "false", "f", "0"]:
                            q3_ans = False
                    elif len(user_msgs) == 1:
                        ans3 = user_msgs[-1].content.strip().lower()
                        if ans3 in ["no", "n", "false", "f", "0"]:
                            q3_ans = False
                            
                    state["answers"] = [q1_ans, q2_ans, q3_ans]
                    return state
                    
    except Exception as e:
        print(f"[State Reconstruction] Error: {e}")
        
    return state

def _parse_network_diagnostics(user_response: str) -> dict:
    res = {"signal": True, "others_affected": True, "restarted": True}
    try:
        from litellm import completion
        from backend.config import settings
        system_prompt = (
            "Parse the user's answers to these three troubleshooting questions:\n"
            "1. Signal bars? (Yes/No)\n"
            "2. Other users affected? (Yes/No)\n"
            "3. Device restarted/Airplane toggled? (Yes/No)\n\n"
            "Extract the boolean values (true for Yes, false for No). If unclear, default to true.\n"
            "Return ONLY a JSON object: {\"signal\": true/false, \"others_affected\": true/false, \"restarted\": true/false}"
        )
        response = completion(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_response}
            ],
            temperature=0.0,
            api_key=settings.openai_api_key or "ollama",
            base_url=settings.openai_api_base,
        )
        data = json.loads(response.choices[0].message.content.strip())
        res.update(data)
    except Exception as e:
        print(f"[Diagnostics Parser] Error: {e}")
        
    return res
