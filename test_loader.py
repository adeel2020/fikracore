import re
with open('services/agents/src/engine_stack/engines/telecom_brain/simulator/scenario_state_compiler.py', 'r') as f:
    text = f.read()

def extract_method(text, method_name):
    lines = text.split('\n')
    start = -1
    for i, line in enumerate(lines):
        if line.startswith(f"    def {method_name}("):
            start = i
            break
    if start == -1: return None
    end = start + 1
    while end < len(lines) and (lines[end].startswith('        ') or lines[end].strip() == '' or lines[end].startswith('    )')):
        end += 1
    return '\n'.join(lines[start:end])

code = extract_method(text, '_load_operational_telemetry_lifecycle')
for line in code.split('\n'):
    if 'self.' in line:
        print(line.strip())
