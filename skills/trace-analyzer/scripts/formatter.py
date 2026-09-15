import os
import re

def find_workspace_root() -> str:
    # Try traversing up from the current working directory to find a common project marker
    curr = os.getcwd()
    for _ in range(4):
        if (os.path.exists(os.path.join(curr, "pyproject.toml")) or 
            os.path.exists(os.path.join(curr, "uv.lock")) or 
            os.path.exists(os.path.join(curr, "skills"))):
            return curr
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
    
    # Fallback: Traverse up from __file__
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
        return workspace_root
    except Exception:
        return os.getcwd()

def extract_rca_and_mermaid(report_content: str) -> str:
    lines = report_content.splitlines()
    
    # 1. Parse out the Mermaid sequence diagram block
    mermaid_lines = []
    in_mermaid = False
    for line in lines:
        if "```mermaid" in line:
            in_mermaid = True
            mermaid_lines.append("```mermaid")
            continue
        if in_mermaid:
            if "```" in line:
                mermaid_lines.append("```")
                in_mermaid = False
                break
            mermaid_lines.append(line)
            
    mermaid_block = "\n".join(mermaid_lines).strip()
    
    # 2. Analyze the report to dynamically generate the RCA
    report_lower = report_content.lower()
    
    if "no supported packets parsed successfully" in report_lower or "no parsed signaling packets" in report_lower:
        # Extract diagnostic details from the report if present
        diag_lines = []
        capture = False
        for line in lines:
            if "pcap diagnostics" in line.lower():
                capture = True
                continue
            if capture and line.strip().startswith("#"):
                break
            if capture and line.strip():
                diag_lines.append(line.strip())
        diag_block = "\n".join(diag_lines) if diag_lines else ""

        return (
            "### ❌ No Parsed Signaling Packets\n\n"
            "The trace file did not contain any recognized signaling packets matching "
            "our protocol dissectors (5G Core SBA, Diameter CC, RANAP, GTP, GSM MAP, TCAP, SIP, RTP, etc.).\n\n"
            "Review your trace file structure or verify that it contains supported control-plane or media packets."
            + (f"\n\n**Pcap Diagnostics:**\n{diag_block}" if diag_block else "")
        )

    session_type = "Multi-Protocol Network Session"
    outcome = "Session completed successfully"
    failure_rca = "No failures detected. Transactions completed successfully."
    details = "The network trace shows normal signaling interactions across active nodes."
    
    detected_protos = []
    for p in ["5g sa sba", "diameter", "ranap", "gtp", "sip", "sigtran", "camel", "map", "tcap", "sccp", "m2pa", "m3ua", "m2ua", "rtp", "sdp", "tcp", "udp"]:
        if p in report_lower:
            name = p.upper()
            if name == "5G SA SBA":
                name = "5G Core (SBA)"
            elif name == "MAP":
                name = "GSM MAP"
            if name not in detected_protos:
                detected_protos.append(name)
            
    if detected_protos:
        session_type = f"{' / '.join(detected_protos)} Signaling Session"
        
    failures = []
    
    if "routeselectfailure" in report_lower:
        failures.append("TCAP Route Selection Failure (`routeSelectFailure` in EventReportBCSM)")
    if "abort" in report_lower:
        failures.append("TCAP Transaction Abort detected")
    if "releasecall" in report_lower:
        session_type = "Signaling Session Teardown"
        outcome = "Call Terminated / Released"
        failure_rca = "Call released by signaling node (ReleaseCall)."
        details = "The session was terminated by a core ReleaseCall signaling component."
        
    if "diameter" in report_lower:
        import re
        res_codes = re.findall(r"result(?:_code)?[:=]\s*`?([3-5]\d{3})", report_lower)
        if res_codes:
            failures.append(f"Diameter Transaction Failure (Result-Code {res_codes[0]})")
            
    if "ranap" in report_lower:
        if "relocationfailure" in report_lower:
            failures.append("RANAP Relocation Failure detected")
        elif "errorindication" in report_lower:
            failures.append("RANAP Error Indication detected")
        elif "unsuccessfuloutcome" in report_lower:
            failures.append("RANAP Unsuccessful Outcome detected")
            
    if "sip" in report_lower:
        import re
        sip_errors = re.findall(r"sip\s+([4-6]\d{2}\s+[a-zA-Z\s]+)", report_lower)
        if sip_errors:
            failures.append(f"SIP Signaling Error ({sip_errors[0].strip()})")
            
    if failures:
        outcome = "Session completed with signaling failures/errors"
        failure_rca = "; ".join(failures)
        details = (
            f"The signaling analyzer detected one or more protocol-level errors during the session: "
            f"**{failure_rca}**. Review the call flow diagram to locate the exact transaction point."
        )
    elif not failures and "releasecall" not in report_lower:
        details = (
            f"All transaction legs in this {session_type} completed normally. "
            f"No signaling errors or session resets were detected."
        )
        
    rca_summary = (
        "### 🔎 Root Cause Analysis (RCA) Summary\n"
        f"- **Session Type**: {session_type}\n"
        f"- **Call Outcome**: {outcome}\n"
        f"- **Failure / Root Cause**: {failure_rca}\n\n"
        f"**RCA Details**:\n{details}"
    )
    
    # 3. Combine Call Flow and RCA only! Exclude summary table!
    sections = []
    if mermaid_block:
        sections.append("### 🔄 Call Flow Diagram\n" + mermaid_block)
    sections.append(rca_summary)
    
    return "\n\n---\n\n".join(sections)


def format_output(arguments: list[str], stdout: str, stderr: str) -> str:
    """Resolve the analyzed pcap filename, read the report, and extract the Call Flow & RCA.
    If no file argument is specified, return a gorgeous, informative help prompt with available traces.
    """
    # 1. Reject empty inputs and show help message
    if not arguments:
        workspace_root = find_workspace_root()
        # Dynamically discover any available traces in current directory or target workspace
        possible_dirs = [
            os.path.join(workspace_root, "traces"),
            os.path.join(workspace_root, ".tmp", "data", "traces"),
            workspace_root,
            os.path.join(os.getcwd(), "traces"),
            os.path.join(os.getcwd(), ".tmp", "data", "traces"),
            os.getcwd()
        ]
        pcap_files = []
        for d in possible_dirs:
            if os.path.exists(d) and os.path.isdir(d):
                for f in os.listdir(d):
                    if f.endswith(".pcap") or f.endswith(".pcapng"):
                        if f not in pcap_files:
                            pcap_files.append(f)
                            
        available_str = ""
        if pcap_files:
            available_str = "\n\n**Available traces in your workspace:**\n" + "\n".join([f"- `{f}`" for f in sorted(pcap_files)])
        else:
            available_str = "\n\n*(No trace files found in your current workspace directory)*"

        return (
            "### 📊 Trace Analyzer Help\n\n"
            "Please specify the name of the packet capture file (`.pcap` or `.pcapng`) you wish to analyze.\n\n"
            "**Usage:**\n"
            "`/trace-analyzer [pcap-file-name]`\n\n"
            "**Example:**\n"
            "`/trace-analyzer camel2.pcap`" + available_str
        )

    # 2. Resolve PCAP filename
    pcap_file = arguments[0]
    base_name = os.path.splitext(os.path.basename(pcap_file))[0]
    
    workspace_root = find_workspace_root()
    possible_paths = [
        os.path.join(workspace_root, f"{base_name}_report.md"),
        os.path.join(workspace_root, "traces", f"{base_name}_report.md"),
        os.path.join(os.getcwd(), f"{base_name}_report.md"),
        os.path.join(os.getcwd(), "traces", f"{base_name}_report.md"),
        os.path.join(os.path.dirname(pcap_file), f"{base_name}_report.md") if os.path.isabs(pcap_file) else None,
    ]
    
    report_path = possible_paths[0]
    for path in possible_paths:
        if path and os.path.exists(path):
            report_path = path
            break
    
    # 3. Read report and extract key sections if file exists
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                raw_report = f.read()
            return extract_rca_and_mermaid(raw_report)
        except Exception as e:
            return f"### ❌ Error Reading Report\n\nAn error occurred while loading the report for `{pcap_file}`: {str(e)}"
            
    # 4. Handle failure / file not found
    script_error = stdout.strip() or stderr.strip()
    return f"### ❌ File Not Found\n\n{script_error or f'The trace file **{pcap_file}** could not be found or analyzed.'}\n\n*Please ensure the trace file is located in the current directory or your workspace.*"
