import re

with open('services/agents/src/engine_stack/engines/telecom_brain/simulator/scenario_state_compiler.py', 'r') as f:
    text = f.read()

self_attrs = set(re.findall(r'self\.([a-zA-Z_]\w*)', text))
print("Self attributes:", self_attrs)
