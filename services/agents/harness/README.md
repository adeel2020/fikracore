Zaki (Mark / Zaki) Harness

What this is
- A deterministic, no-LLM-call smoke harness for your ZakiBridge guardrails.
- It validates that Zaki refuses evaluator/hidden truth, doesn’t guess root cause when evidence is insufficient, stays offline, and doesn’t invent synthetic evidence.

Location
- /Users/adeelarshad/kagent/services/agents/harness/run_zaki_guardrail_checks.py

How to run
1) From the agents repo root:
   cd /Users/adeelarshad/kagent/services/agents

2) Run (note: uses python3.11 and sets PYTHONPATH):
   PYTHONPATH=src python3.11 harness/run_zaki_guardrail_checks.py

Expected output
- PASS lines for each guardrail case
- "All Zaki guardrail checks passed." and exit code 0

Notes
- The script clears common LLM env vars so ZakiBridge doesn’t attempt real network calls.
- If your bridge output format changes (e.g., response is nested under a different key), update the response-extraction logic in the harness.
