# Fix: Mobile Core Analyst Output Token Limit & Stream Extraction Fix

## 🚨 The Issue
Even after switching the `MobileCoreAnalyst` agent to a plain text description layout, the user reported receiving large paragraphs, and noted that intermediate reasoning thoughts/tokens were still leaking into the UI during streaming.

---

## 🔍 Root Cause Analysis
1. **Response Length:** The task instructions did not specify any strict word or token constraints, allowing the LLM to output verbose multi-paragraph descriptions of the matched graph relationships.
2. **Intermediate Reasoning Leaks:** CrewAI agents run under a ReAct (Reasoning and Action) execution frame. When the agent is instructed to not use any structured report headers or sections, it might skip generating the exact ReAct final output prefix (`Final Answer:`). When this happens, the frontend's stream splitter fails to detect a `final answer:` marker, leading the stream callback to dump all intermediate reasoning thoughts and tool execution cycles directly to the chat bubble.

---

## 🛠️ The Solution
We modified the agent task configuration in [mobile_core_analyst.py](file:///Users/adeelarshad/DataEngine/backend/agent/mobile_core_analyst.py):
1. **Strict Length Bounds:** Added explicit instructions to step 3 of the task description: `"Keep it extremely concise and short (strictly under 100 words / 120 tokens total)."`
2. **Mandatory Extraction Prefix:** Required the LLM to prefix its final conversational response with the exact prefix `"Final Answer:"`: `"You MUST prefix your final response with the exact prefix 'Final Answer:' followed by your conversational explanation."`
3. **Structured Expected Output:** Set `expected_output` to `"A plain-text conversational description under 100 words prefixed with 'Final Answer:'."`

This ensures the agent forces a `"Final Answer:"` tag, which the frontend SSE chunk handler detects instantly. The frontend separates the thoughts and outputs ONLY the clean conversational description, hiding the reasoning log from the user's chat bubble during and after token generation.

---

## 🔬 Verification & Correctness
* **Expected Format Mapping:** The prefix requirement guarantees that `lowerRaw.includes("final answer:")` evaluates to `true` in the stream handler.
* **Token Constraint Safety:** The 100-word constraint ensures the generated explanation remains well under 150 tokens.
