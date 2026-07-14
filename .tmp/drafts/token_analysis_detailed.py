#!/usr/bin/env python3
import sys
import json

sys.path.insert(0, 'backend')

try:
    import tiktoken
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tiktoken", "-q"])
    import tiktoken

enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

# Analyze components that consume tokens
analysis = {}

# 1. Agent role and backstory
agent_role = "Customer Complaint Analyst"
agent_backstory = "You are an expert Customer Complaint Analyst. You use the causal knowledge graph to analyze telecom complaints and guide operators."
agent_goal = "Identify the customer's intent, query the telecom causal knowledge graph once, validate prechecks, verify safety routes, and guide the customer operator."

role_tokens = len(enc.encode(agent_role))
backstory_tokens = len(enc.encode(agent_backstory))
goal_tokens = len(enc.encode(agent_goal))

analysis['agent_config'] = {
    "role": {"tokens": role_tokens, "chars": len(agent_role)},
    "backstory": {"tokens": backstory_tokens, "chars": len(agent_backstory)},
    "goal": {"tokens": goal_tokens, "chars": len(agent_goal)},
    "total_agent_tokens": role_tokens + backstory_tokens + goal_tokens
}

# 2. Task prompt (this is the big one - embedded query makes it grow)
task_prompt_template = """You are a Customer Complaint Analyst.
    Analyze the user's raw complaint: "{query}"


    1. Query the Causal Knowledge Graph using tool `query_causal_knowledge_graph` extract the causal reasoning chain.
    2. Analyze the causal chain using tool call  `trace_causal_chain`
    3. Analyze the result of tool call `trace_causal_chain` share the diagnostic reasoning in your thoughts to connect the dots for final answering.
    4. Return the final answer  after the analysis or step 3 is completed, without expecting additional tool support.

    Provide a friendly conversational routing advice under 100 words, plain text, with no markdown formatting. Construct the response dynamically as follows:
    1. Mention missing prechecks: e.g., "Please check [Precheck Name] (missing)."
    2. Mention completed prechecks: e.g., "[Precheck Name] check is completed."
    3. Look up the "depends_on" resources list returned by the knowledge graph query. For each resource, specify its to check status (e.g., "Sufficient Benefits available on OCS/IN").
    4. Recommend the escalation path using the dynamic "escalation_target": "If all checks pass, escalate to [escalation_target]."

    You MUST prefix your final response with 'Final Answer: '.
    """

# Sample queries
sample_queries = [
    "My voice calls keep dropping randomly",
    "I cannot access my prepaid account balance and I am unable to check my available balance on the app portal. The error message says forbidden"
]

task_base_tokens = len(enc.encode(task_prompt_template.replace('"{query}"', '')))
analysis['task_prompt'] = {
    "template_tokens": task_base_tokens,
    "template_chars": len(task_prompt_template.replace('"{query}"', '')),
    "with_queries": []
}

for query in sample_queries:
    full_prompt = task_prompt_template.format(query=query)
    prompt_tokens = len(enc.encode(full_prompt))
    analysis['task_prompt']['with_queries'].append({
        "query": query,
        "query_tokens": len(enc.encode(query)),
        "full_prompt_tokens": prompt_tokens,
        "query_chars": len(query)
    })

# 3. Tool outputs (samples)
sample_tool_output = {
    "matched_node_id": "intent_volte_call_drop",
    "matched_label": "VoLTE Call Drop Issue",
    "match_type": "Intent",
    "match_score": 0.85,
    "mandatory_prechecks": ["Check Network Status", "Verify Device Compatibility", "Check Signal Strength"],
    "depends_on": ["OCS_Benefits", "IN_Services"],
    "escalation_target": "Network Operations L2",
    "triplets": [f"triple_{i}" for i in range(40)],  # Capped at 40
    "ranked_candidates": [{"node": {"id": f"cand_{i}", "label": f"Candidate {i}"}, "score": 0.8 - i*0.01} for i in range(10)]
}

tool_output_json = json.dumps(sample_tool_output)
tool_output_tokens = len(enc.encode(tool_output_json))

analysis['sample_tool_output'] = {
    "tokens": tool_output_tokens,
    "chars": len(tool_output_json),
    "output_preview": str(sample_tool_output)[:200] + "..."
}

# 4. Estimate cumulative for one run
print("Token Analysis Summary")
print("=" * 60)
print(json.dumps(analysis, indent=2))

print("\n\nToken Consumption Breakdown for Single Run:")
print("-" * 60)
print(f"Agent Config (role+backstory+goal): {analysis['agent_config']['total_agent_tokens']} tokens")
print(f"Task Prompt Template: {analysis['task_prompt']['template_tokens']} tokens")
query_len = analysis['task_prompt']['with_queries'][1]['query_tokens']  # Longer query
full_prompt_len = analysis['task_prompt']['with_queries'][1]['full_prompt_tokens']
print(f"Task Prompt with 40-char query: +{query_len} tokens => {full_prompt_len} total")
print(f"One Tool Output (sample): {analysis['sample_tool_output']['tokens']} tokens")
print(f"\nMinimum per-run: ~{analysis['agent_config']['total_agent_tokens'] + full_prompt_len + analysis['sample_tool_output']['tokens']*2} tokens (agent + prompt + 2 tool outputs)")
print(f"With verbose logging/reasoning: Could multiply by 5-10x")
