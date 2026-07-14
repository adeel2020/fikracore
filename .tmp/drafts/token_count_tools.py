#!/usr/bin/env python3
import sys
import json

sys.path.insert(0, 'backend')

try:
    import tiktoken
except ImportError:
    print("Installing tiktoken...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tiktoken", "-q"])
    import tiktoken

from backend.agent import complaint_analyst

# Initialize tokenizer for gpt-3.5-turbo
enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

tools = [
    complaint_analyst.query_causal_knowledge_graph,
    complaint_analyst.trace_causal_chain,
]

token_analysis = []
total_all = 0

for tool in tools:
    tool_name = tool.name
    tool_desc = tool.description or ""
    tool_schema = str(tool.args_schema) if hasattr(tool, 'args_schema') else ""
    
    name_tokens = len(enc.encode(tool_name))
    desc_tokens = len(enc.encode(tool_desc))
    schema_tokens = len(enc.encode(tool_schema))
    total_tokens = name_tokens + desc_tokens + schema_tokens
    total_all += total_tokens
    
    token_analysis.append({
        "tool_name": tool_name,
        "name_tokens": name_tokens,
        "description_tokens": desc_tokens,
        "description_chars": len(tool_desc),
        "schema_tokens": schema_tokens,
        "schema_chars": len(tool_schema),
        "total_tokens": total_tokens
    })

result = {
    "total_all_tools_tokens": total_all,
    "tools": token_analysis
}

print(json.dumps(result, indent=2))
