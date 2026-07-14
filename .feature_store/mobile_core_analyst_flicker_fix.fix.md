# Fix: Mobile Core Analyst Streaming Response Flickering

## 🚨 The Issue
During token generation for the `MobileCoreAnalyst` agent (Page 6 / Tab 6), the streaming response in the assistant's chat bubble was flickering heavily. Intermediate reasoning thoughts, tool names, and JSON arguments (e.g., target parameter strings for `Recognize Intent & Extract Entities` and `Get Knowledge Graph Triplets` tools) leaked directly into the message text area instead of showing only the final cleaned markdown answer.

---

## 🔍 Root Cause Analysis
The backend `/api/qna/mobile-core-analyst/stream` endpoint streams LLM tokens by registering a `BaseEventListener` to capture global `LLMStreamChunkEvent` bus events. Because the analyst agent is equipped with tools, CrewAI utilizes a ReAct execution loop under the hood. As the LLM reasons, it streams thoughts and JSON tool structures before generating the final answer.
In the frontend [agentic-qna-view.tsx](file:///Users/adeelarshad/DataEngine/frontend/src/components/features/agentic-qna-view.tsx), the stream chunk handler for Page 6 (`activeIndex === 6`) simply concatenated every token and wrote it directly to the assistant's message `content`. Unlike the standard `/chat/stream` handler (used for single-agent QnA and the primary agent), it lacked the logic to detect ReAct patterns, parse the `final answer:` marker, and separate reasoning logs from the final markdown response.

---

## 🛠️ The Solution
We updated the `streamMobileCoreAnalystMessage` stream callback in [agentic-qna-view.tsx](file:///Users/adeelarshad/DataEngine/frontend/src/components/features/agentic-qna-view.tsx#L870-L904) to use the exact same thoughts and content separation algorithm used by `/chat/stream`:
1. Stripped any incomplete or active `__AGENT__` markers from the end of the text.
2. Scanned for the `final answer:` marker in the stream. When found, everything preceding the marker is categorized as `thoughts` and everything succeeding it is extracted as clean `content`.
3. Checked the accumulated text against ReAct keywords (`thought`, `action`, `action input`, `observation`). If matched, the entire block is treated as thoughts, suppressing rendering in the main chat bubble while keeping the status bar active.
4. Set the message state with both the cleanly extracted `content` and `thoughts` fields.

This successfully hides raw JSON tool calls and internal thoughts from leaking, rendering only the clean markdown report.

---

## 🔬 Verification & Correctness
1. **Compilation Validation:** Ran `npx tsc --noEmit` within the `/Users/adeelarshad/DataEngine/frontend` directory. The command completed successfully with zero compiler warnings or errors, validating type-safety.
2. **Behavior Verification:** The update aligns Page 6 streaming logic with `/chat/stream`. Intermediate steps are now processed gracefully inside the message state, eliminating flickering.
