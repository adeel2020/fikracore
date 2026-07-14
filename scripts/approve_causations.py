import os
import json
import yaml
import subprocess
import sys

def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def approve_causations():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend/agent"))
    rules_path = os.path.join(base_dir, "causal_rules.yaml")
    candidates_path = os.path.join(base_dir, "candidate_causations.json")
    trends_path = os.path.join(base_dir, "emerging_trends.json")

    candidates = load_json(candidates_path)
    trends = load_json(trends_path)

    if not candidates and not trends:
        print("No pending candidates or trends found for approval.")
        return

    # Load current rules
    with open(rules_path, "r") as f:
        rules = yaml.safe_load(f) or {}

    updated = False

    # Process candidates (Mobile Core Team learning)
    if candidates:
        print(f"\n--- Processing {len(candidates)} Mobile Core Causal Candidates ---")
        remaining_candidates = []
        for idx, cand in enumerate(candidates):
            print(f"\n[{idx+1}/{len(candidates)}] Candidate Query: '{cand['query']}'")
            print(f"  Proposed Relation: ({cand['suggested_source']}) --[relates_to]--> ({cand['suggested_target']})")
            
            choice = input("Approve relation? [y/n/e] (yes/no/edit): ").strip().lower()
            if choice == "y":
                # Create the new Symptom node if it's a new symptom
                symptom_id = f"symptom_learned_{int(cand['timestamp'])}"
                rules.setdefault("other_nodes", {})[symptom_id] = {
                    "label": cand["suggested_source"],
                    "type": "Symptom",
                    "description": f"Learned symptom from query: '{cand['query']}'"
                }
                # Create the relationship link
                rules.setdefault("relationships", []).append({
                    "source": symptom_id,
                    "target": cand["suggested_target"],
                    "label": cand["suggested_label"]
                })
                updated = True
                print("✅ Approved and staged.")
            elif choice == "e":
                src = input(f"Enter source label [{cand['suggested_source']}]: ").strip() or cand['suggested_source']
                tgt = input(f"Enter target node ID [{cand['suggested_target']}]: ").strip() or cand['suggested_target']
                lbl = input(f"Enter relationship label [{cand['suggested_label']}]: ").strip() or cand['suggested_label']
                
                symptom_id = f"symptom_learned_{int(cand['timestamp'])}"
                rules.setdefault("other_nodes", {})[symptom_id] = {
                    "label": src,
                    "type": "Symptom",
                    "description": f"Learned symptom from query: '{cand['query']}'"
                }
                rules.setdefault("relationships", []).append({
                    "source": symptom_id,
                    "target": tgt,
                    "label": lbl
                })
                updated = True
                print("✅ Custom relation approved and staged.")
            else:
                print("❌ Candidate rejected.")

        save_json(candidates_path, remaining_candidates)

    # Process trends (Customer Operations trends)
    if trends:
        print(f"\n--- Processing {len(trends)} Customer Ops Emerging Trends ---")
        remaining_trends = []
        for idx, trend in enumerate(trends):
            print(f"\n[{idx+1}/{len(trends)}] Emerging Trend: '{trend['trend']}' ({trend['occurrences']} queries)")
            print(f"  Sample Queries:")
            for q in trend["sample_queries"]:
                print(f"    - {q}")
            
            choice = input("Map this trend to causal graph? [y/n/e] (yes/no/edit): ").strip().lower()
            if choice == "y":
                # Add as FAQ or Intent node
                symptom_id = f"symptom_trend_{int(trend['timestamp'])}"
                rules.setdefault("other_nodes", {})[symptom_id] = {
                    "label": trend["trend"],
                    "type": "Symptom",
                    "description": f"Emerging trend cluster: {', '.join(trend['sample_queries'])}"
                }
                # Link to suggested escalation queue
                rules.setdefault("relationships", []).append({
                    "source": symptom_id,
                    "target": trend["suggested_escalation"],
                    "label": "escalates_to"
                })
                updated = True
                print("✅ Trend mapped and staged.")
            elif choice == "e":
                lbl = input(f"Enter trend label [{trend['trend']}]: ").strip() or trend['trend']
                tgt = input(f"Enter target queue/component ID [{trend['suggested_escalation']}]: ").strip() or trend['suggested_escalation']
                
                symptom_id = f"symptom_trend_{int(trend['timestamp'])}"
                rules.setdefault("other_nodes", {})[symptom_id] = {
                    "label": lbl,
                    "type": "Symptom",
                    "description": f"Emerging trend cluster: {', '.join(trend['sample_queries'])}"
                }
                rules.setdefault("relationships", []).append({
                    "source": symptom_id,
                    "target": tgt,
                    "label": "escalates_to"
                })
                updated = True
                print("✅ Custom trend mapped and staged.")
            else:
                print("❌ Trend rejected.")

        save_json(trends_path, remaining_trends)

    if updated:
        # Write back to causal_rules.yaml
        with open(rules_path, "w") as f:
            yaml.safe_dump(rules, f, sort_keys=False)
        print("\n💾 Saved updates to causal_rules.yaml.")

        # Run validation test to verify compilation safety
        print("\n🧪 Running graph coherence validation test...")
        res = subprocess.run(["uv", "run", "pytest", "tests/test_graph_coherence.py"], capture_output=True, text=True)
        if res.returncode == 0:
            print("🎉 Validation passed. CKG synchronized successfully to trace_graph.json!")
        else:
            print("⚠️ Validation failed! Please inspect compilation error output:")
            print(res.stderr or res.stdout)
            sys.exit(1)

if __name__ == "__main__":
    approve_causations()
