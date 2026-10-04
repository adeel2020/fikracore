import ast

with open('services/agents/src/engine_stack/engines/telecom_brain/simulator/scenario_state_compiler.py', 'r') as f:
    source = f.read()

tree = ast.parse(source)

class SelfVisitor(ast.NodeVisitor):
    def __init__(self):
        self.self_attrs = set()
    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id == 'self':
            self.self_attrs.add(node.attr)
        self.generic_visit(node)

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        visitor = SelfVisitor()
        visitor.visit(node)
        if len(visitor.self_attrs) > 0:
            print(f"{node.name} uses: {visitor.self_attrs}")
        else:
            print(f"{node.name} uses nothing")
