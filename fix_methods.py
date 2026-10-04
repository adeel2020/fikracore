import re
import os

out_dir = 'services/agents/src/engine_stack/engines/telecom_brain/simulator/compiler'

# We can just replace `.\b([_a-zA-Z]\w*)` with `\1` when it was mistakenly replaced from `self.X`
# Wait! Instead of guessing, we know exactly what self attributes are used.
deps = {
    '_parse_runtime_timestamp', '_resolve_stage_name', '_derive_impact_scope', 
    '_format_natural_evidence_observation', '_entity_domain', '_generate_hypothesis_names', 
    'load_scenario_manifest', '_derive_domains', '_ref_entities', '_ref_relationships', '_ref_network'
}

for fname in os.listdir(out_dir):
    if not fname.endswith('.py'): continue
    path = os.path.join(out_dir, fname)
    with open(path, 'r') as f:
        text = f.read()
    
    # fix the issue where `self.` was removed but `.` remained!
    # wait, the issue was: `self._parse` -> `._parse`
    # because I did `re.sub(r'\bself\b', '', l)` which replaced `self`, leaving `.`
    # So we just need to find `\.` followed by one of the deps, preceded by whitespace or non-word.
    # Actually, in the whole builder file, any `\.([_a-zA-Z]\w*)` that matches our deps should just be `\1`.
    
    for dep in deps:
        text = re.sub(r'\.' + dep + r'\b', dep, text)
        
    with open(path, 'w') as f:
        f.write(text)

