import ast
import re

with open('services/agents/src/engine_stack/engines/telecom_brain/simulator/scenario_state_compiler.py', 'r') as f:
    source = f.read()

tree = ast.parse(source)

methods_to_extract = {
    'telemetry_loader': ['_load_operational_telemetry_lifecycle'],
    'reasoning_map_builder': ['_build_reasoning_map', '_build_causal_path', '_build_operational_edges', '_build_hypothesis_paths', '_build_evidence_clusters'],
    'hypothesis_builder': ['_build_hypotheses', '_generate_hypothesis_names'],
    'topology_builder': ['_build_topology'],
    'zaki_builder': ['_build_zaki'],
    'stage_watchdog': ['_build_stage_watchdog', '_disclosure_policy_for_stage', '_compute_stage_values', '_build_stages', '_build_frontiers', '_build_search_space', '_build_reasoning_focus']
}

class SelfVisitor(ast.NodeVisitor):
    def __init__(self):
        self.self_attrs = set()
    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id == 'self':
            self.self_attrs.add(node.attr)
        self.generic_visit(node)

extractor = {}
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name in [m for ms in methods_to_extract.values() for m in ms]:
        visitor = SelfVisitor()
        visitor.visit(node)
        print(f"{node.name} uses: {visitor.self_attrs}")
