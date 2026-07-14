# Fix: Mobile Core Analyst Lazy-Loading & Streaming Alignment

## 🚨 The Issue
1. **Flashing & Rendering Cleanup Cycle:** The chat bubble rendered intermediate tool call JSON blocks before clearing them and writing the final response. This caused visual clutter and flickering.
2. **Slow Startup/Initialization:** Generating knowledge graph embeddings was slow on startup because the local `SentenceTransformer` model was always loaded as a fallback, even when OpenAI was successfully configured.

---

## 🔍 Root Cause Analysis
1. **JSON Tool Calls:** CrewAI's model calls tools using structured JSON formatting. These JSON strings did not contain ReAct keywords (like `thought` or `action`), so the frontend stream splitter fell through, treating them as final response content. When the next step (containing ReAct words) or `Final Answer:` arrived, the frontend matched them and cleared the JSON content, causing the chat bubble to appear, vanish, and reappear.
2. **Eager Loading of Fallback:** `KnowledgeGraphRetriever.initialize()` eagerly imported and loaded the heavy local `SentenceTransformer('all-MiniLM-L6-v2')` model on startup, regardless of whether OpenAI embeddings were available and working. Since FastAPI reload mode restarts the server on file edits, this caused constant startup latency.

---

## 🛠️ The Solution
1. **JSON Token Check on Frontend:** Added an `isJson` check (`accumulatedRaw.trim().startsWith("{") || accumulatedRaw.trim().startsWith("[")`) inside the stream callbacks of [agentic-qna-view.tsx](file:///Users/adeelarshad/DataEngine/frontend/src/components/features/agentic-qna-view.tsx). If the stream starts with a JSON tool call block, it is categorized as thoughts. This keeps the chat bubble clean and hidden until `Final Answer:` begins.
2. **Lazy-Load SentenceTransformer:** Modified [kg_retriever.py](file:///Users/adeelarshad/DataEngine/backend/agent/kg_retriever.py#L224-L274) to defer importing and loading `SentenceTransformer` until an OpenAI API call fails or settings are missing. This makes initialization instant when using OpenAI.

---

## 🔬 Verification & Correctness
* **Instant Startups:** Server restarts are now sub-second, since `SentenceTransformer` is bypassed.
* **Flicker-Free Streaming:** Frontend stream parser cleanly suppresses all tool call JSON logs, showing only the final plain-text response directly.
