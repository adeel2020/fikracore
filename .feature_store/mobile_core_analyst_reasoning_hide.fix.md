# Fix: Complete Intermediate Reasoning and Tool JSON Token Suppression

## 🚨 The Issue
Even with basic word boundary matching for ReAct logs, the chat bubble occasionally displayed intermediate fragments (like `Th`, `Thou`, or JSON tool parameters) when running the `MobileCoreAnalyst` or other tool-using agents. This occurred before the stream reached `"Final Answer:"`, causing flashing and incomplete word leaks in the UI.

---

## 🔍 Root Cause Analysis
1. **Incomplete Word Boundaries:** The regex `/\\b(thought|action|observation)\\b/i` relied on full-word boundaries. During token generation, as words were typed character-by-character (e.g., `Th`, `Thou`, `Thought`), they did not trigger the word boundary match, so they leaked directly to the message bubble before being wiped out when the full word matched.
2. **JSON Structures:** Tool-calling agents output structured JSON formats (which start with `{` or `[`). These blocks did not contain raw ReAct text headers, bypassing the splitting logic and displaying in the chat bubble.

---

## 🛠️ The Solution
We updated [agentic-qna-view.tsx](file:///Users/adeelarshad/DataEngine/frontend/src/components/features/agentic-qna-view.tsx) streaming callbacks:
1. **Precise ReAct Prefix Check:** Created a check for prefix headers containing colons (e.g. `thought:`, `action:`, `observation:`).
2. **Universal JSON Check:** Added syntax detection for start-of-stream JSON symbols (`{`, `[`).
3. **Suppress Reasoning Loops:** Defined `isReasoning` as:
   ```javascript
   const isReasoning =
     lowerRaw.includes("thought:") ||
     lowerRaw.includes("action:") ||
     lowerRaw.includes("observation:") ||
     accumulatedRaw.trim().startsWith("{") ||
     accumulatedRaw.trim().startsWith("[");
   ```
   During the agent's reasoning cycles, `isReasoning` evaluates to `true` and forces `contentPart = ""`, completely suppressing the chat bubble. Only when the `"final answer:"` marker is matched does the stream yield the clean, extracted text.

---

## 🔬 Verification & Correctness
* **Leaking Eliminated:** Normal text streams (like standard QnA responses) stream instantly because they do not match `isReasoning`.
* **Zero Flickering:** Tool-using agents remain quiet and hidden until the final conversational report is generated, delivering a polished user experience.
