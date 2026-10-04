import ast
import re

with open('services/agents/src/engine_stack/engines/telecom_brain/simulator/scenario_state_compiler.py', 'r') as f:
    source = f.read()

class MethodExtractor(ast.NodeVisitor):
    def __init__(self):
        self.methods = {}
    
    def visit_FunctionDef(self, node):
        self.methods[node.name] = node
        self.generic_visit(node)

tree = ast.parse(source)
extractor = MethodExtractor()
extractor.visit(tree)

def get_method_source(name):
    node = extractor.methods[name]
    lines = source.split('\n')
    # node.lineno is 1-based, lines is 0-based
    # Need to include decorators if any
    start = node.lineno - 1
    if node.decorator_list:
        start = node.decorator_list[0].lineno - 1
    end = node.end_lineno
    return '\n'.join(lines[start:end])

print(get_method_source('_build_stages'))
