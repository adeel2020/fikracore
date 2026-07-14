# Two-Gate Knowledge Graph Optimization Plan (Revised)

## Progress Summary

### ✅ Completed — `kg_retriever.py` Performance Layer

| Change | Status | What was done |
|--------|--------|---------------|
| Pre-compute adjacency list at init | ✅ Done | `self.adj` built as `dict[str, set]` during `initialize()`. `trace_causal_chain()` now uses `self.adj` instead of rebuilding per call |
| Pre-compute label map at init | ✅ Done | `self.label_map` built during `initialize()`. `trace_causal_chain()` uses `self.label_map.get(n, n)` instead of `self.node_map.get(n, {}).get("label", n)` |
| Embedding LRU cache | ✅ Done | Global `_EMBEDDING_CACHE` dict wraps `get_embedding()`. Identical queries hit cache instantly (0ms) instead of calling OpenAI/SentenceTransformer again |
| Cross-encoder toggle | ✅ Done | `retrieve_intent_and_pointers(use_cross_encoder=True)` — Gate 1 can call with `False` to skip the 300-1500ms CPU inference |
| Deduplicated DFS paths | ✅ Done | `path_copy` uniqueness check prevents duplicate paths in trace output |
| `force_local` embedding parameter | ✅ Done | Ensures query vector and node vectors use the same embedding space when mixing OpenAI + local models |

### ⬜ Remaining — `complaint_analyst.py` Gate Architecture

| Change | Status | What needs to be done |
|--------|--------|----------------------|
| `gate1_route_complaint()` function | ⬜ Todo | Extract routing logic from `_query_causal_knowledge_graph()` into a standalone deterministic function |
| Merged `diagnose_complaint` tool | ⬜ Todo | Combine `query_causal_knowledge_graph` + `trace_causal_chain` tools into one |
| `stream_analyze()` Gate 1 bypass | ⬜ Todo | Call Gate 1 before CrewAI agent; emit structured response directly if confident |

---

## Architecture

```
[Incoming Query]
       │
       ▼
 ┌───────────────────────────────────────────────────┐
 │  GATE 1 — Deterministic Routing  (<5ms)           │
 │  NOT an LLM tool. Runs as pre-processing.         │
 │                                                   │
 │  1. Keyword match from causal_rules.yaml          │
 │  2. Bi-encoder fallback (dot product, 38 cached   │
 │     vectors, use_cross_encoder=False)              │
 │  3. Coverage / Slowness / Device overrides        │
 │  4. Resolve assignment_target from target_teams   │
 │  5. Populate structured response directly         │
 └───────────────────────┬───────────────────────────┘
                         │
                         ▼
               Structured Response Card
               (issue_summary, assignment_target,
                reassignment_category, etc.)
                         │
     ┌───────────────────┴───────────────────┐
     │                                       │
     ▼                                       ▼
 [End Flow]                          [Operator requests RCA]
 Default for customer ops            "Deep Diagnosis" trigger
                                             │
                                             ▼
                          ┌──────────────────────────────┐
                          │  GATE 2 — RCA Diagnosis       │
                          │  Single LLM tool call (~1-2s) │
                          │                               │
                          │  1. Bi-encoder + Cross-encoder│
                          │     (use_cross_encoder=True)  │
                          │  2. Match CKG intent node     │
                          │  3. Evaluate prechecks        │
                          │  4. DFS trace_causal_chain()  │
                          │  5. Resource dependency check │
                          └──────────────────────────────┘
```

## LLM Round-Trip Savings

| Scenario | Before | After |
|----------|--------|-------|
| Customer routing query | 2 LLM tool calls | **0 tool calls** |
| Operator RCA diagnosis | 2 LLM tool calls | **1 tool call** |
| Savings on CPU Llama 3 | — | **30-120s per eliminated round-trip** |

---

## Remaining Changes

### Task 1: `gate1_route_complaint()` — Deterministic Router

#### [MODIFY] complaint_analyst.py

**New function: `gate1_route_complaint(query: str) -> dict`**

Extracts the deterministic routing logic from `_query_causal_knowledge_graph()` (lines ~166-406) into a standalone function that runs **without any LLM**.

```python
def gate1_route_complaint(query: str) -> dict:
    """
    Deterministic routing — no LLM, no tool call.
    Returns a fully populated structured response dict.
    """
    raw_lower = query.lower()
    causal_rules = _get_causal_rules()

    # Step 1: IT/Network classification via bi-encoder (reuses cached embedding)
    class_res = kg_retriever.classify_it_or_network(query)
    category = class_res["category"]

    # Step 2: If Tie, return clarification prompt immediately
    if category == "Tie":
        return {
            "confident": True,
            "issue_summary": "Ambiguous Intent",
            "assignment_target": "pending_user_input",
            "reassignment_category": "Ambiguous",
            "resolution_category": "Pending Clarification",
            "mandatory_prechecks": [],
            "depends_on": [],
            "message": "I detected that your issue might be related to activation (IT) or usage (Network)..."
        }

    # Step 3: Bi-encoder retrieval WITHOUT cross-encoder (fast path)
    res = kg_retriever.retrieve_intent_and_pointers(query, use_cross_encoder=False)
    # ... existing keyword matching, coverage/slowness overrides,
    #     assignment_target resolution logic from _query_causal_knowledge_graph() ...

    # Step 4: Build structured response
    return {
        "confident": True,
        "issue_summary": matched_label,
        "mandatory_prechecks": mandatory,
        "depends_on": depends_on,
        "assignment_target": assignment_target,
        "reassignment_category": reassignment_category,
        "resolution_category": resolution_category,
        "message": message
    }
```

> **IMPORTANT:** The existing `_query_causal_knowledge_graph()` and its `@tool` wrapper stay in place as a fallback. Gate 1 is a **new parallel path** — not a replacement.

---

### Task 2: Merged `diagnose_complaint` Tool (Gate 2)

#### [MODIFY] complaint_analyst.py

**Add a single merged tool for Gate 2 RCA:**

```python
@tool("diagnose_complaint", max_usage_count=1)
def diagnose_complaint(query: str) -> str:
    """
    Runs full root-cause analysis on a telecom complaint.
    Combines intent matching (with cross-encoder re-ranking),
    precheck evaluation, and causal chain traversal
    into a single diagnostic pass.

    Example: {"query": "eSIM activation failure with SM-DP+ mismatch"}
    """
    # 1. Full retrieval with cross-encoder
    res = kg_retriever.retrieve_intent_and_pointers(query, use_cross_encoder=True)
    matched_node_id = res["intent_node"]["id"] if res["intent_node"] else ""

    # 2. Evaluate prechecks + resource dependency
    prechecks = _trace_causal_chain_internal(query, matched_node_id, "")

    # 3. DFS trace
    trace = kg_retriever.trace_causal_chain(matched_node_id)

    return json.dumps({
        "prechecks": prechecks.get("prechecks", {}),
        "trace": trace,
        "matched_intent": res["intent_node"]["label"] if res["intent_node"] else "Unknown",
        "confidence": res["intent_score"]
    })
```

**In `_build_agent_and_crew()`**, replace the two-tool list:
```diff
- tools=[query_causal_knowledge_graph, trace_causal_chain],
+ tools=[diagnose_complaint],
```

Update the task prompt to reference a single tool call instead of two sequential ones.

---

### Task 3: `stream_analyze()` Gate 1 Bypass

#### [MODIFY] complaint_analyst.py

**Insert Gate 1 check before CrewAI invocation:**

```python
async def stream_analyze(self, raw_complaint: str):
    # ... existing validation checks ...

    # Gate 1: Deterministic routing (< 5ms)
    gate1_result = gate1_route_complaint(raw_complaint)

    if gate1_result.get("confident", True):
        # Emit structured response directly — no LLM needed
        structured_event = _format_structured_event(gate1_result)
        yield StreamChunk(
            content=structured_event,
            chunk_type=StreamChunkType.TEXT,
            task_id="complaint_analysis_task",
            agent_role="Customer Complaint Analyst",
            agent_id="mcca_structured",
        )
        return

    # Gate 2: Fall through to existing CrewAI agent flow
    # ... existing code unchanged ...
```

> **NOTE:** `_format_structured_event()` already exists and produces the `__STRUCTURED_EVENT__` format that the frontend expects. No frontend changes needed.

---

## File Change Summary

| File | Change | Status |
|------|--------|--------|
| kg_retriever.py | Pre-compute `self.adj`, `self.label_map`; add `_EMBEDDING_CACHE`; `use_cross_encoder` toggle | ✅ Done |
| complaint_analyst.py | Add `gate1_route_complaint()`; add `diagnose_complaint` tool; update `stream_analyze()` | ⬜ Todo |

> **IMPORTANT:** No frontend changes needed. The `__STRUCTURED_EVENT__` format stays identical — the frontend doesn't know or care whether the response came from Gate 1 (deterministic) or Gate 2 (LLM-driven).

---

## Verification Plan

### Automated Tests
```bash
# Test Gate 1 routing (should complete in <5ms)
python3 -c "
import time
from backend.agent.complaint_analyst import gate1_route_complaint
start = time.perf_counter()
result = gate1_route_complaint('eSIM activation failure')
elapsed = (time.perf_counter() - start) * 1000
print(f'Gate 1 latency: {elapsed:.1f}ms')
print(f'Target: {result[\"assignment_target\"]}')
"

# Test Gate 2 merged tool (should complete in <2s)
python3 -c "
import time
from backend.agent.complaint_analyst import diagnose_complaint
start = time.perf_counter()
result = diagnose_complaint('eSIM activation failure')
elapsed = (time.perf_counter() - start) * 1000
print(f'Gate 2 latency: {elapsed:.1f}ms')
"
```

### Manual Verification
- Submit "eSIM activation failure" → should get instant structured card (Gate 1, <5ms)
- Submit ambiguous query like "my phone doesn't work" → should route correctly via bi-encoder fallback
- Verify structured response card renders identically in frontend for both gates
- Trigger RCA deep diagnosis → should use single `diagnose_complaint` tool (1 LLM round-trip)
