import os
import json
import time
from collections import defaultdict

def synthesize_trends():
    unresolved_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "../backend/agent/unresolved_complaints.json"
    ))
    trends_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "../backend/agent/emerging_trends.json"
    ))

    if not os.path.exists(unresolved_path):
        print("No unresolved complaints file found.")
        return

    try:
        with open(unresolved_path, "r") as f:
            drafts = json.load(f)
    except Exception as e:
        print(f"Error reading unresolved complaints: {e}")
        return

    if not drafts:
        print("No unresolved complaints logged yet.")
        return

    # Basic keyword-grouping clustering algorithm to find emerging product/promo trends
    # A real-world production system would use sentence-transformer clustering, but
    # a clean deterministic word-co-occurrence tokenizer provides highly reliable clustering
    # on telecom domains without external LLM inference costs.
    clusters = defaultdict(list)
    stop_words = {"the", "a", "an", "for", "to", "in", "on", "at", "my", "is", "of", "and", "not", "with", "new"}
    
    for draft in drafts:
        query = draft.get("query", "")
        # Clean query words
        words = [w.strip("?,.!") for w in query.lower().split() if w.strip("?,.!") not in stop_words]
        
        # Look for typical promo/offer markers
        promo_words = [w for w in words if w in {"offer", "promo", "promotion", "bundle", "package", "plan", "free", "prime", "amazon"}]
        
        if promo_words:
            # Group by first matched promo-indicator word
            key = f"Emerging Trend: {promo_words[0].capitalize()} Offer"
        else:
            # Fallback to the first two cleaned nouns/words
            key = f"Emerging Topic: {' '.join(words[:2]).capitalize()}"
            
        clusters[key].append(draft)

    # Process and summarize the trends
    emerging_trends = []
    for trend_title, items in clusters.items():
        if len(items) >= 2: # Highlight trends with at least 2 similar complaints
            emerging_trends.append({
                "trend": trend_title,
                "occurrences": len(items),
                "suggested_domain": items[0].get("suggested_domain", "Network"),
                "suggested_escalation": items[0].get("suggested_escalation", "core_smcs"),
                "sample_queries": [item["query"] for item in items[:3]],
                "timestamp": int(time.time()),
                "status": "pending_mapping"
            })

    try:
        with open(trends_path, "w") as f:
            json.dump(emerging_trends, f, indent=2)
        print(f"✅ Synthesized {len(emerging_trends)} emerging trends to emerging_trends.json.")
    except Exception as e:
        print(f"Error saving emerging trends: {e}")

if __name__ == "__main__":
    synthesize_trends()
