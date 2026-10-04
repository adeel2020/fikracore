import ast
import re
import os

source_file = 'services/agents/src/engine_stack/engines/telecom_brain/simulator/scenario_state_compiler.py'
with open(source_file, 'r') as f:
    source = f.read()

tree = ast.parse(source)

# Mapping of builder file to methods to extract
extraction_plan = {
    'telemetry_loader.py': ['_load_operational_telemetry_lifecycle'],
    'reasoning_map_builder.py': ['_build_reasoning_map', '_build_causal_path', '_build_operational_edges', '_build_hypothesis_paths', '_build_evidence_clusters'],
    'hypothesis_builder.py': ['_build_hypotheses', '_generate_hypothesis_names'],
    'topology_builder.py': ['_build_topology'],
    'zaki_builder.py': ['_build_zaki'],
    'stage_watchdog.py': ['_build_stage_watchdog', '_disclosure_policy_for_stage', '_compute_stage_values', '_build_stages', '_build_frontiers', '_build_search_space', '_build_reasoning_focus']
}

class SelfVisitor(ast.NodeVisitor):
    def __init__(self):
        self.self_attrs = set()
    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id == 'self':
            self.self_attrs.add(node.attr)
        self.generic_visit(node)

# Collect method information
methods_info = {}
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        visitor = SelfVisitor()
        visitor.visit(node)
        methods_info[node.name] = {
            'node': node,
            'self_attrs': sorted(list(visitor.self_attrs))
        }

# Read lines for string manipulation
lines = source.split('\n')

# Prepare new files
out_dir = 'services/agents/src/engine_stack/engines/telecom_brain/simulator/compiler'
os.makedirs(out_dir, exist_ok=True)

# Common imports for the new files
common_imports = """from typing import Any, Optional, Callable
from pathlib import Path
from datetime import datetime
import json
"""

# To modify the main file
lines_to_remove = []
imports_to_add = []

for filename, methods in extraction_plan.items():
    file_content = [common_imports]
    
    for method in methods:
        info = methods_info[method]
        node = info['node']
        self_attrs = info['self_attrs']
        
        # Determine the line range to extract
        start = node.lineno - 1
        if node.decorator_list:
            start = node.decorator_list[0].lineno - 1
        end = node.end_lineno
        
        # Expand end to include trailing empty lines or closing parens
        while end < len(lines) and (lines[end].startswith('        ') or lines[end].strip() == '' or lines[end].startswith('    )')):
            end += 1
            
        method_lines = lines[start:end]
        
        # Mark for removal in the main file
        for i in range(start, end):
            lines_to_remove.append(i)
            
        # Process the method lines
        new_method_lines = []
        is_signature = True
        for line in method_lines:
            # unindent
            if line.startswith('    '):
                l = line[4:]
            else:
                l = line
                
            if is_signature:
                # Remove @staticmethod
                if l.startswith('@staticmethod'):
                    continue
                # Remove self from arguments
                l = re.sub(r'\bself,\s*', '', l)
                l = re.sub(r'\bself\b', '', l)
                
                # Rename function
                if l.startswith('def ' + method):
                    new_name = method[1:] if method.startswith('_') else method
                    l = l.replace('def ' + method, 'def ' + new_name, 1)
                    imports_to_add.append((filename, new_name))
                
                # Add self_attrs to signature
                if self_attrs and l.strip().endswith('):') or l.strip().endswith(') ->'):
                    # This is tricky for multi-line signatures.
                    pass # We will do a regex replacement on the whole joined signature instead!

            # Replace self.X with X
            for attr in self_attrs:
                l = re.sub(r'\bself\.' + attr + r'\b', attr, l)
                
            new_method_lines.append(l)
            
        # Join lines to fix the signature
        method_code = '\n'.join(new_method_lines)
        
        # Inject parameters to the signature
        if self_attrs:
            params_str = ', '.join([f"{attr}: Callable" if attr.startswith('_') else f"{attr}: Any" for attr in self_attrs])
            # Find the closing parenthesis of the def
            # This is complex, let's just insert before the final ')' of the def
            def_match = re.search(r'def\s+[a-zA-Z_]\w*\s*\((.*?)\)\s*(->.*?)?:', method_code, re.DOTALL)
            if def_match:
                sig_inner = def_match.group(1)
                if sig_inner.strip():
                    new_sig_inner = sig_inner + f", *, {params_str}"
                else:
                    new_sig_inner = f"*, {params_str}"
                
                # Replace the old signature inner
                method_code = method_code[:def_match.start(1)] + new_sig_inner + method_code[def_match.end(1):]

        file_content.append(method_code)
        file_content.append('\n')

    with open(os.path.join(out_dir, filename), 'w') as f:
        f.write('\n'.join(file_content))

# Generate __init__.py
init_lines = []
for filename, new_name in imports_to_add:
    module = filename[:-3]
    init_lines.append(f"from .{module} import {new_name}")
with open(os.path.join(out_dir, '__init__.py'), 'w') as f:
    f.write('\n'.join(init_lines))

# Now modify the main file
new_main_lines = []
for i, line in enumerate(lines):
    if i not in lines_to_remove:
        new_main_lines.append(line)

# Add imports to the main file, somewhere near the top after other imports
main_source = '\n'.join(new_main_lines)
import_block = []
for filename, new_name in imports_to_add:
    module = filename[:-3]
    import_block.append(f"from .compiler.{module} import {new_name}")

# find a good place to insert imports
# right after 'from pathlib import Path' or similar
insert_idx = 0
lines = main_source.split('\n')
for i, line in enumerate(lines):
    if line.startswith('class ScenarioStateCompiler'):
        insert_idx = i - 1
        break

lines.insert(insert_idx, '\n' + '\n'.join(import_block) + '\n')

# Now we need to update the method calls inside the main file to pass the extra parameters
# Wait! Instead of a complex regex, we can just rewrite the calls where these methods are used inside ScenarioStateCompiler!
# Since we know what we extracted, and we know they now take `new_name` instead of `self.method`,
# and they might require extra parameters (like `_entity_domain=self._entity_domain`), we should inject them.

# Let's save the intermediate main file first and do a second pass for call injection.
with open(source_file + '.tmp', 'w') as f:
    f.write('\n'.join(lines))

print("Extraction completed. Run python to verify.")
