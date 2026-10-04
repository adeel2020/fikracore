import re

with open('services/agents/src/engine_stack/engines/telecom_brain/simulator/scenario_state_compiler.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if re.match(r'^    def [a-zA-Z_]', line):
        print(f"{i+1}: {line.strip()}")
