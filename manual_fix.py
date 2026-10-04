import re

with open('services/agents/src/engine_stack/engines/telecom_brain/simulator/scenario_state_compiler.py.tmp', 'r') as f:
    text = f.read()

deps = {
    '_build_stage_watchdog': ['_resolve_stage_name', '_parse_runtime_timestamp'],
    '_disclosure_policy_for_stage': [],
    '_compute_stage_values': [],
    '_load_operational_telemetry_lifecycle': ['_parse_runtime_timestamp', '_derive_impact_scope', '_format_natural_evidence_observation', '_entity_domain'],
    '_build_hypotheses': ['_generate_hypothesis_names'],
    '_generate_hypothesis_names': [],
    '_build_topology': ['load_scenario_manifest'],
    '_build_stages': [],
    '_build_zaki': [],
    '_build_reasoning_map': ['_derive_domains', '_entity_domain'],
    '_build_causal_path': [],
    '_build_operational_edges': [],
    '_build_hypothesis_paths': [],
    '_build_evidence_clusters': [],
    '_build_frontiers': [],
    '_build_search_space': [],
    '_build_reasoning_focus': []
}

for old_name, attrs in deps.items():
    new_name = old_name[1:] if old_name.startswith('_') else old_name
    
    # We want to replace `self._build_stages(` with `build_stages(`
    # and we want to inject `attr=self.attr` at the end of the arguments.
    # Because arguments can span multiple lines, we can write a tiny parser that tracks parentheses!
    
    idx = 0
    while True:
        target = f"self.{old_name}("
        idx = text.find(target, idx)
        if idx == -1:
            break
            
        # replace `self._old_name` with `new_name`
        text = text[:idx] + new_name + "(" + text[idx+len(target):]
        # current idx is now at the `(` of `new_name(`
        paren_idx = idx + len(new_name)
        
        # find matching closing parenthesis
        depth = 0
        close_idx = -1
        in_string = False
        string_char = ''
        escape = False
        
        for i in range(paren_idx, len(text)):
            c = text[i]
            if escape:
                escape = False
                continue
            if c == '\\':
                escape = True
                continue
            if in_string:
                if c == string_char:
                    in_string = False
                continue
            if c in '"\'':
                in_string = True
                string_char = c
                continue
                
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    close_idx = i
                    break
                    
        if close_idx != -1 and attrs:
            # We found the closing parenthesis!
            # Let's inject `, attr=self.attr` before it
            inject_str = ""
            # check if there are any args by looking backward for non-whitespace non-paren
            has_args = False
            for j in range(close_idx-1, paren_idx, -1):
                if text[j].strip():
                    has_args = True
                    break
            
            if has_args:
                # If there's a trailing comma, we don't need another one.
                # Actually it's safer to just add `, attr=self.attr`
                pass
            
            for attr in attrs:
                inject_str += f", {attr}=self.{attr}"
                
            if not has_args:
                inject_str = inject_str.lstrip(", ")
                
            text = text[:close_idx] + inject_str + text[close_idx:]
            # advance idx
            idx = close_idx + len(inject_str) + 1
        else:
            idx = paren_idx + 1

with open('services/agents/src/engine_stack/engines/telecom_brain/simulator/scenario_state_compiler.py', 'w') as f:
    f.write(text)

