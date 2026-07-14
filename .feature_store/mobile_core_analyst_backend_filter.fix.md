# Fix: Mobile Core Analyst Aligned Streaming Output

## 🚨 The Issue
Raw ReAct thoughts and tool JSON tokens were previously leaking and causing flickering on every token generation for the `MobileCoreAnalyst` agent (Page 6 / Tab 6) in the frontend QnA interface.

---

## 🔍 Root Cause Analysis
1. **Frontend Streaming Callback:** The Page 6 streaming listener in the frontend (`agentic-qna-view.tsx`) was not using the thoughts/content splitting parser that the standard `/chat/stream` endpoint was using.
2. **Missing Token Bounds:** The agent task lacked strict limits, generating large multi-paragraph reports.

---

## 🛠️ The Solution
Instead of writing custom backend-level buffering filters, we aligned both the frontend and backend streams to use the exact patterns already tested and implemented in `/chat/stream` and `qna_agent.py`:
1. **Frontend Splitter Alignment:** Updated Page 6's streaming chunk callback in [agentic-qna-view.tsx](file:///Users/adeelarshad/DataEngine/frontend/src/components/features/agentic-qna-view.tsx#L870-L904) to use the identical `final answer:` marker search and ReAct keyword checks used by `/chat/stream`.
2. **Standard Backend Streaming Route:** Kept `/mobile-core-analyst/stream` in [api_router.py](file:///Users/adeelarshad/DataEngine/backend/routers/api_router.py) mapped to the simple, tested, and standard chunk yielding loop matching `/chat/stream` exactly.
3. **Conversational Length Constraints:** Instructed the agent tasks in [mobile_core_analyst.py](file:///Users/adeelarshad/DataEngine/backend/agent/mobile_core_analyst.py) to write a plain conversational response of under 100 words (strictly under 150 tokens) and prefix the final explanation with `"Final Answer:"`.

This allows the frontend's tested splitting mechanism to extract and stream only the clean final conversational response, hiding intermediate reasoning steps and preventing flickering.
