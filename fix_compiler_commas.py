import os
import re

out_dir = 'services/agents/src/engine_stack/engines/telecom_brain/simulator/compiler'

for fname in os.listdir(out_dir):
    if not fname.endswith('.py'): continue
    path = os.path.join(out_dir, fname)
    with open(path, 'r') as f:
        text = f.read()
    
    while True:
        new_text = re.sub(r',(\s*),', r',\1', text)
        if new_text == text:
            break
        text = new_text
        
    with open(path, 'w') as f:
        f.write(text)

