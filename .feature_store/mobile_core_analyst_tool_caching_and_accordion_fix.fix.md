# Fix: Mobile Core Analyst Tool Caching and Accordion Auto-Expansion

## 🚨 The Issue
1. **Duplicate Final Answers / Raw JSON Output in UI**:
   The assistant text bubble for the `Mobile Core Analyst` persona was displaying raw JSON blocks or duplicate final answers during streaming.
2. **Intermediate Observation Leakage**:
   Intermediate agent thoughts, tool calls, and observations were leaking into the main message bubble instead of staying inside the thoughts accordion.
3. **Accordion Collapsing**:
   The thoughts accordion stayed collapsed during streaming and when loading historical chat sessions.
4. **Missing Tool Calls (Caching Issue)**:
   On subsequent prompt requests, the agent made only one tool call (`query_causal_knowledge_graph`) instead of two. The second tool call (`trace_causal_chain`) was skipped because of thread-leaking cache hits.
5. **Skipped Second Tool Call (eSIM / Specific Queries)**:
   For specific prompts (like `"unable to use eSIM"`), the agent skipped `trace_causal_chain` entirely because the tool description was unclear, and the parameters expected a wrapped `tool_input` rather than explicit arguments.

---

## 🔍 Root Cause Analysis
1. **Response Bubble Rendering**:
   The conditional check `!(isAssistant && persona === "Mobile Core Analyst")` in `MessageItem.tsx` had been removed, which allowed the raw JSON streaming buffer representing the Pydantic final response model to render inside the main chat bubble. Since all intermediate reasoning belongs in the thoughts accordion and the final response goes in the structured response card, the text bubble must be suppressed for this persona.
2. **Stalled Accordion**:
   The `ThoughtsAccordion` element in `MessageItem.tsx` only triggered its open logic when `loading` went from `false` to `true` at the very beginning of a prompt. When streaming thoughts delayed or when historical messages loaded, `loading` was already `true` or `false` respectively, preventing the accordion from expanding automatically.
3. **Thread-Leaking Cache**:
   The `trace_causal_chain` tool in `complaint_analyst.py` cached its execution results inside a shared ContextVar dictionary using a static string key `"trace_causal_chain_result"`. Because CrewAI worker threads reuse the same OS threads in the background thread pool, this static cache key leaked cache state across concurrent or subsequent requests. On the second prompt, the tool hit the static cache of the first prompt and returned immediately, skipping execution and preventing the observation from being logged to the stream.
4. **Implicit Tool Schema & Wrapper Docstring**:
   The `trace_causal_chain` tool's docstring described it as a "Flexible wrapper for tracing causal chains" (implementation details) rather than outlining its functional purpose to the LLM. Furthermore, the tool signature expected a wrapped `tool_input: object | None` parameter, causing LLMs to get confused or choose to skip calling it when matched intent fields were already present in the first observation.

---

## 🛠️ The Solution
1. **Suppress Message Bubble**:
   Restored the conditional check in [MessageItem.tsx](file:///Users/adeelarshad/AgenticAIOPs/frontend/src/components/features/agentic-qna-view/components/MessageItem.tsx#L495) to suppress the chat bubble for the `Mobile Core Analyst` persona, ensuring a clean visual separation.
2. **Accordion Keyed on Thoughts and Loading**:
   Rewrote the `ThoughtsAccordion` `useEffect` hook in [MessageItem.tsx](file:///Users/adeelarshad/AgenticAIOPs/frontend/src/components/features/agentic-qna-view/components/MessageItem.tsx#L62-L73) to watch both `loading` and `thoughts`. It automatically expands during active streaming to show thoughts in real-time, and automatically collapses as soon as loading completes and the final response card appears. It also defaults to collapsed when loading historical chat sessions, while still allowing the user to manually expand it.
3. **Query-Specific Cache Key**:
   Modified `trace_causal_chain` in [complaint_analyst.py](file:///Users/adeelarshad/AgenticAIOPs/backend/agent/complaint_analyst.py#L566-L572) to parse the unique prompt query and node ID, using them as part of a compound cache key:
   ```python
   cache_key = ("trace_causal_chain", query, matched_node_id)
   ```
   This isolates cache lookups per request and prevents stale hits on reused background threads.
4. **Enhanced Tool Docstring & Signature**:
   Upgraded `trace_causal_chain` to accept explicit `**kwargs` keyword parameters (like `trace_causal_chain(query="...", matched_node_id="...")`) alongside wrapped `tool_input`. Rewrote its docstring to clearly explain what the tool does, what it returns, and instruct the LLM that it MUST call it after `query_causal_knowledge_graph` to get diagnostic details.

---

## 🔬 Verification & Correctness
1. **TypeScript Verification**:
   Ran `npx -p typescript tsc --noEmit --project frontend/tsconfig.json` to verify that there are no type errors.
2. **Next.js Production Build**:
   Successfully compiled the frontend via `npm run build --prefix frontend`.
3. **Backend Tests**:
   Ran the Pytest suite for the analyst:
   ```bash
   PYTHONPATH=. ./.venv/bin/pytest backend/agent/test_mobile_core_analyst.py
   ```
   All tests passed successfully.
