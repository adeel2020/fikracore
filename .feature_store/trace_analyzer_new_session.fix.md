# Fix: Trace Analyzer Session Persona, Leakage Resolution, and Local Call Flow Scrolling

## 🚨 The Issue
Several issues were identified in the chat messaging view:
1. **JSON Event Leakage during Streaming**: Just before the structured response card rendered, the raw `__STRUCTURED_EVENT__` payload and its JSON keys leaked into the chat message bubble. This created a visual flicker where raw text was shown during streaming and then vanished when the stream finished and the card appeared.
2. **Loss of Persona on Reload/Refresh**: If a user ran `/trace-analyzer` and refreshed the page, the loaded message's persona fell back to `"Data Storyteller"`. The correct skill persona (e.g. `"Senior Telecom Signaling Analyst"`) was not preserved.
3. **Thought/Action Keyword Flicker**: Intermediate LLM responses (e.g. partial thoughts and raw Pydantic JSON blocks) leaked into the main text content bubble for a split second before matching ReAct keywords (like `Thought:`, `Action:`, etc.), causing severe visual flickering.
4. **Blank Assignment Target**: When `escalation_target` was renamed to `assignment_target` in `MessageItem.tsx` and `complaint_analyst.py`, the Assignment Target field became blank because the type schemas and parser (`extractStructuredPayload` in `useAgenticQna.ts`) were still looking for the old `escalation_target` string keys.
5. **Excessive Vertically Scrolling on Large PCAPs**: When processing large signaling traces with many steps, the Mermaid call flow diagram expanded to a very large vertical height, pushing the page scrollbar to the bottom and forcing the user to scroll extensively to view the rest of the response message.

---

## 🔍 Root Cause Analysis
1. **Incomplete Block Filtering**: The helper `extractStructuredPayload` only parsed and stripped the structured payload block if *both* `__STRUCTURED_EVENT__` and `__END_STRUCTURED_EVENT__` markers were present in the text. While streaming was in progress, the end marker was missing, so the function returned the raw accumulating text (including the start marker and keys) as normal content, which leaked into the text bubble.
2. **Database Schema Constraints & Fallbacks**: The SQLite/PostgreSQL `chat_messages` table does not have a `persona` column. When a session is loaded from the backend, `loadSession` reconstructs the persona dynamically. If no structured data is present (as is the case with `/trace-analyzer` reports), it fell back to calling `classifyQuery(prevUserMsg)`. Since `/trace-analyzer` is not categorized as a mobile core or interrogative query, it defaulted to `"Data Storyteller"`.
3. **Keyword Matching Latency**: Raw ReAct chunks and Pydantic schema keys were rendered in the message bubble because they did not immediately contain standard keywords like `thought:`, `action:`, or `observation:`. Consequently, `isReasoning` evaluated to `false`, dumping the text into `contentPart` (which renders the text bubble) until the next keyword appeared.
4. **Different Persona and Agent Naming Conventions**: The backend streams chunks under the role `"Customer Complaint Analyst"`, while the frontend maps this persona to `"Mobile Core Analyst"`. The previous check was matching `activeAgent === "Mobile Core Analyst"`, which evaluated to `false` since the backend streams `"Customer Complaint Analyst"`. This allowed intermediate thoughts and JSON keys to leak directly into the message bubble during the stream.
5. **Mismatched Key Parsing**: The frontend parser `extractStructuredPayload` looked for `escalation_target:` and saved it into `structured.escalation_target`. The backend sent `assignment_target: ...` and the frontend UI printed `payload.assignment_target`, causing an undefined/blank lookup.
6. **Lack of Local Vertical Constraints**: The sequence diagram component (`RenderSequenceDiagram` in `MessageItem.tsx`) had no vertical bounding box constraint or scrollbar. Consequently, any diagram with a large number of transaction steps expanded to its full height, altering the container layout flow and forcing page-level scrolling.

---

## 🛠️ The Solution

1. **Strip Incomplete Structured Payloads during Streaming**:
   Modified `extractStructuredPayload` in `useAgenticQna.ts` to actively check for the presence of the `startMarker`. If it is present but the `endMarker` is missing (meaning streaming is currently in progress), the function trims the text from `startIndex` onwards, preventing it from leaking into the text bubble.

2. **Hook-Level Skill Persona Resolution on Session Reload**:
   - Promoted `getSkillRole` to the hook level in `useAgenticQna.ts`.
   - Updated `loadSession` to verify if the previous user message starts with `/` (a slash command), resolving its role using `getSkillRole(prevUserMsg)` before falling back to `classifyQuery`.

3. **Force Reasoning Class for all Mobile Core Analyst Roles**:
   Modified the `isReasoning` logic in both stream handlers in `useAgenticQna.ts` to treat all intermediate text as thoughts/reasoning if the resolved persona is `"Mobile Core Analyst"` or if the streaming agent role is `"Mobile Core Analyst"` or `"Customer Complaint Analyst"`.

4. **Permanent Text Content Block in Render**:
   Re-implemented the conditional check in `MessageItem.tsx` to completely hide the raw text content bubble for the `"Mobile Core Analyst"` persona.

5. **Assignment Target Naming Alignment**:
   - Updated `ChatMessage` API type definition in `frontend/src/lib/api/qna.ts` to replace `escalation_target` with `assignment_target`.
   - Modified the parser `extractStructuredPayload` in `useAgenticQna.ts` to parse `assignment_target:` keys instead of `escalation_target:` keys.

6. **Local Call Flow Scroll Container & Matching Scrollbar Design**:
   - Wrapped the sequence diagram steps container in `RenderSequenceDiagram` inside a scrollable container constrained to `max-h-[380px] overflow-y-auto overflow-x-hidden`.
   - Structured the layout so that the participant headers (`gsmSSF` / `gsmSCF`) remain outside the vertical scroll container. This locks the headers to the top of the call flow area while allowing horizontal scrolling to remain unified.
   - Styled the local scrollbar using custom CSS classes matching the chat panel design:
     ```typescript
     className="max-h-[380px] overflow-y-auto overflow-x-hidden pr-1 [&::-webkit-scrollbar]:w-[3px] [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-white/15 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-white/30 [scrollbar-width:thin] [scrollbar-color:rgba(255,255,255,0.15)_transparent]"
     ```

---

## 🔬 Verification & Correctness
1. **TypeScript Type Safety**: Ran `npx tsc --noEmit` inside the `frontend/` directory, confirming that no type conflicts or errors were introduced.
2. **Knowledge Graph Topology**: Synced the graph structure using `graphify update .` to include all hook and helper changes.
