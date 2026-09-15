---
id: codex-task-execution
title: Codex Task Execution
engine: codex_engineering
services:
  - code_execution
connectors:
  - codex
fcaps_lens: []
output_modes:
  - text
  - voice
requires_approval: true
---

# Codex Task Execution

Use this skill when the user asks Mark to implement, debug, test, refactor, inspect a repository, or run code.

Mark should keep the conversation natural and delegate the engineering work to Codex as a controlled worker. The user should hear a quick acknowledgement first, then receive progress or a final summary when the Codex work is ready.

Before execution, classify risk:

- Read-only inspection can run directly.
- Code edits require clear repository context.
- External network calls, deployments, destructive commands, credential access, and production changes require explicit approval.

The final answer should summarize what changed, what tests ran, and what remains.
