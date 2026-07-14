# Fix: Mobile Core Analyst Plain-Text Conversational Description

## 🚨 The Issue
The user requested that the `MobileCoreAnalyst` agent describe the issue based on pattern matches with the telecom knowledge graph in a plain conversational format, rather than generating a structured markdown report or a concise technical layout.

---

## 🔍 Root Cause Analysis
The task instructions in [mobile_core_analyst.py](file:///Users/adeelarshad/DataEngine/backend/agent/mobile_core_analyst.py) explicitly directed the agent's LLM to:
1. "write a concise, technical, and data-grounded markdown description detailing: Nature of the Issue, Recognized Intent, Root Cause & Affected Services, Diagnostic Paths..."
2. Set the task's expected output format to: `"A structured markdown report describing the customer's issue and diagnostic context grounded in the knowledge graph triplets."`

This structured markdown template output forced the agent to generate formal technical headings and list blocks rather than explaining the mapped graph patterns in plain conversational text.

---

## 🛠️ The Solution
We updated both the synchronous and streaming task definitions in [mobile_core_analyst.py](file:///Users/adeelarshad/DataEngine/backend/agent/mobile_core_analyst.py):
1. **Instruction Modification**: Replaced the step detailing markdown structures with a requirement to write a plain conversational description explaining the customer's issue.
2. **Plain Text Grounding**: Explicitly instructed the agent to explain how the user's issue maps to the identified intent, services, root cause errors, and target support platforms, without formatting the response as a structured markdown report (e.g., avoiding headings like `###`, list asterisks, or bold text).
3. **Updated Expected Output**: Changed the task's `expected_output` to: `"A plain-text conversational description of the issue based on the matched knowledge graph patterns."`

---

## 🔬 Verification & Correctness
* **Instruction Validity:** The task description updates in [mobile_core_analyst.py](file:///Users/adeelarshad/DataEngine/backend/agent/mobile_core_analyst.py#L79-L94) and [mobile_core_analyst.py](file:///Users/adeelarshad/DataEngine/backend/agent/mobile_core_analyst.py#L147-L162) correctly enforce plain text generation.
* **Frontend Rendering Safety:** Checked that `renderMessageContent` in `agentic-qna-view.tsx` safely processes plain-text inputs as standard paragraphs without trying to parse headings or markdown lists.
