import re

with open('services/agents/src/engine_stack/engines/telecom_brain/simulator/scenario_state_compiler.py', 'r') as f:
    text = f.read()

# Replace sequence of whitespace and comma that follows a comma
# E.g. ",\n        ," -> ",\n        "
# Use a regex loop
while True:
    new_text = re.sub(r',(\s*),', r',\1', text)
    if new_text == text:
        break
    text = new_text

# Also remove trailing comma before closing parens, just in case, or rather fix ( , -> (
text = re.sub(r'\(\s*,', '(', text)

with open('services/agents/src/engine_stack/engines/telecom_brain/simulator/scenario_state_compiler.py', 'w') as f:
    f.write(text)
