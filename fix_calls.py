import re
import ast

with open('services/agents/src/engine_stack/engines/telecom_brain/simulator/scenario_state_compiler.py.tmp', 'r') as f:
    source = f.read()

extraction_plan = {
    'telemetry_loader.py': ['_load_operational_telemetry_lifecycle'],
    'reasoning_map_builder.py': ['_build_reasoning_map', '_build_causal_path', '_build_operational_edges', '_build_hypothesis_paths', '_build_evidence_clusters'],
    'hypothesis_builder.py': ['_build_hypotheses', '_generate_hypothesis_names'],
    'topology_builder.py': ['_build_topology'],
    'zaki_builder.py': ['_build_zaki'],
    'stage_watchdog.py': ['_build_stage_watchdog', '_disclosure_policy_for_stage', '_compute_stage_values', '_build_stages', '_build_frontiers', '_build_search_space', '_build_reasoning_focus']
}

methods_info = {} # from previous analysis, we need to know what self_attrs each method took.
# I'll just hardcode them based on earlier get_deps output to be safe.
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

new_source = source
for old_name, req_attrs in deps.items():
    new_name = old_name[1:] if old_name.startswith('_') else old_name
    
    # We need to replace `self.old_name(...)` with `new_name(..., req_attr1=self.req_attr1, req_attr2=self.req_attr2)`
    # Because of multi-line arguments, a simple regex is tough. Let's see if we can do string replacement.
    # Actually, ast.NodeTransformer is the perfect tool for this!
    pass

class CallTransformer(ast.NodeTransformer):
    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'self':
            old_name = node.func.attr
            if old_name in deps:
                new_name = old_name[1:] if old_name.startswith('_') else old_name
                req_attrs = deps[old_name]
                
                # Replace self.old_name with new_name
                node.func = ast.Name(id=new_name, ctx=ast.Load())
                
                # Append keyword arguments for required attributes
                for attr in req_attrs:
                    keyword = ast.keyword(arg=attr, value=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=attr, ctx=ast.Load()))
                    node.keywords.append(keyword)
        return node

tree = ast.parse(source)
transformer = CallTransformer()
new_tree = transformer.visit(tree)
ast.fix_missing_locations(new_tree)
print(ast.unparse(new_tree))
