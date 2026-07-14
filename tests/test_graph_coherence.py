import os
import yaml
import json
import pytest

def test_graph_coherence():
    from backend.agent.complaint_analyst import _get_causal_rules
    rules = _get_causal_rules()

    # 1. Collect all declared Node IDs
    declared_nodes = set()
    
    # Core intents
    declared_nodes.update(rules.get("intents", {}).keys())
    
    # FAQs
    declared_nodes.update(faq.get("id") for faq in rules.get("faqs", []) if faq.get("id"))
    
    # Other CKG nodes (components, resources, error types)
    declared_nodes.update(rules.get("other_nodes", {}).keys())
    
    # Fallback nodes (represented as fallback_<domain_lower>)
    for fid in rules.get("fallbacks", {}).keys():
        declared_nodes.add(f"fallback_{fid.lower()}")

    # Target teams as nodes
    declared_nodes.update(rules.get("target_teams", {}).keys())

    # Target teams
    target_teams = set(rules.get("target_teams", {}).keys())

    # Precheck definitions
    precheck_defs = set(rules.get("precheck_definitions", {}).keys())

    # 2. Check each intent's references
    for iid, entry in rules.get("intents", {}).items():
        # Check prechecks
        for chk in entry.get("mandatory_prechecks", []):
            assert chk in precheck_defs, f"Intent '{iid}' references undefined precheck '{chk}'"
        
        # Check escalation target
        esc = entry.get("escalation_target")
        assert esc in target_teams, f"Intent '{iid}' references undefined target team '{esc}'"

    # 3. Check each FAQ's references
    for faq in rules.get("faqs", []):
        fid = faq.get("id", "unknown_faq")
        for chk in faq.get("mandatory_prechecks", []):
            assert chk in precheck_defs, f"FAQ '{fid}' references undefined precheck '{chk}'"
        
        esc = faq.get("escalation_target")
        assert esc in target_teams, f"FAQ '{fid}' references undefined target team '{esc}'"

    # 4. Check each Fallback's references
    for fid, entry in rules.get("fallbacks", {}).items():
        for chk in entry.get("mandatory_prechecks", []):
            assert chk in precheck_defs, f"Fallback '{fid}' references undefined precheck '{chk}'"
        
        esc = entry.get("escalation_target")
        assert esc in target_teams, f"Fallback '{fid}' references undefined target team '{esc}'"

    # 5. Check for broken links (relationships)
    broken_links = []
    for rel in rules.get("relationships", []):
        src = rel.get("source")
        tgt = rel.get("target")
        if src not in declared_nodes:
            broken_links.append(f"Source node '{src}' in relationship {src} -> {tgt} is not declared in nodes/intents/faqs.")
        if tgt not in declared_nodes:
            broken_links.append(f"Target node '{tgt}' in relationship {src} -> {tgt} is not declared in nodes/intents/faqs.")

    assert not broken_links, "Broken graph links detected:\n" + "\n".join(broken_links)

    # 6. Verify compilation watcher runs and builds trace_graph.json
    from backend.agent.kg_retriever import kg_retriever
    kg_retriever.initialize()
    
    trace_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "../trace_graph.json"
    ))
    assert os.path.exists(trace_path), f"trace_graph.json not found after initialization"
    
    with open(trace_path, "r") as f:
        compiled = json.load(f)
        
    compiled_node_ids = {n["id"] for n in compiled.get("nodes", [])}
    for nid in declared_nodes:
        assert nid in compiled_node_ids, f"Declared node '{nid}' missing in trace_graph.json compiled output"

    print("✅ All graph validations passed successfully.")

if __name__ == "__main__":
    test_graph_coherence()
