---
name: trace-analyzer
description: Analyzes SIGTRAN M2UA/M3UA PCAP network traces and generates a beautifully formatted call flow report with a Mermaid sequence diagram.
role: Senior Telecom Signaling Analyst
argument-hint: ["[pcap-file-name-or-path]", "[output-markdown-path]"]
---

# /trace-analyzer

Analyze standard PCAP network trace files containing SIGTRAN signaling traffic (M2UA, M3UA, SCCP, TCAP, and CAMEL/MAP protocols) to produce interactive visual sequence diagrams and deep protocol breakdowns.

## Execution Path

The trace analyzer uses a project-local Python-based signaling parser located at:
`./skills/trace-analyzer/scripts/analyze_trace.py`

## Argument Details

1. **PCAP File Name or Path (Required):** The filename (e.g., `camel2.pcap`), absolute path, or relative path to the `.pcap` or `.pcapng` file to analyze. The tool intelligently searches the current working directory, the workspace root, and the workspace `traces` directory if just a filename is provided.
2. **Output Markdown Path (Optional):** The target file path to write the markdown report. Defaults to `[trace_file_name]_report.md` in the current directory if not specified.

## How to Invoke the Skill

Run the python analyzer using your `run_command` tool:

```bash
python3 "./skills/trace-analyzer/scripts/analyze_trace.py" "[pcap-file-name-or-path]" "[output-markdown-path]"
```

For example:
```bash
python3 "./skills/trace-analyzer/scripts/analyze_trace.py" "camel2.pcap"
```

## Action Steps for the Agent

1. **Identify Traces:** Search the workspace for any `.pcap` or `.pcapng` trace files.
2. **Execute Parser:** Propose running the Python parser script on the identified trace file using the command format above.
3. **Display Output directly in the Chat:** Upon successful generation, you must read the generated Markdown report using the `view_file` tool to understand the call flow details. **You must then print the visual call flow and Root Cause Analysis (RCA) directly into the chat window.** Do not print complex packet-wise detailed analyses. Your response must include:
   - **Visual Mermaid Sequence Flow Diagram:** Fully rendered inline using Mermaid syntax.
   - **Root Cause Analysis (RCA) Summary:** A highly focused analysis of the signaling session, including:
     - **Session Type:** (e.g., Call Rejected, Normal Call Setup with Charging, etc.)
     - **Call Outcome:** Clear verdict on the transaction status.
     - **Failure/Root Cause Analysis:** Specific step, cause value (e.g. `routeSelectFailure`, cause code details) and packet ID where any error or teardown occurred.
