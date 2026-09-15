"""
Script to create/publish all Mobile Core RTR slugs into the live running gbrain
via its MCP HTTP endpoint (http://localhost:3131/mcp) with OAuth Bearer Token.
"""

import os
import json
import urllib.request
from pathlib import Path

MCP_URL = "http://localhost:3131/mcp"
TOKEN = "gbrain_55cd2909625c9094a70cb84d7bf9422a40927974993ed95501d089cbff005c34"

SLUGS_DIR = Path("/Users/adeelarshad/kagent/gbrain/domains/mobile-core/roles/mobile-rtr")

PAGES = [
    {
        "slug": "domains/mobile-core/roles/mobile-rtr/pipeline",
        "file": SLUGS_DIR / "pipeline.md",
        "title": "Mobile RTR Multi-Stage Investigation & Troubleshooting Pipeline",
        "type": "procedure",
        "frontmatter": {
            "domain": "Mobile Core",
            "role": "Mobile RTR",
            "stages": 7,
            "governance": "Read-only Core RTR, IT Provisioning handoff with BSS Order ID",
        },
    },
    {
        "slug": "domains/mobile-core/roles/mobile-rtr/concern-findings-matrix",
        "file": SLUGS_DIR / "concern-findings-matrix.md",
        "title": "Concern-Findings Matrix: Customer Complaints to Protocol Root Causes",
        "type": "matrix",
        "frontmatter": {
            "domain": "Mobile Core",
            "role": "Mobile RTR",
        },
    },
    {
        "slug": "domains/mobile-core/roles/mobile-rtr/services-and-tools-catalog",
        "file": SLUGS_DIR / "services-and-tools-catalog.md",
        "title": "Specialized Services & Diagnostic Tools Catalog",
        "type": "catalog",
        "frontmatter": {
            "domain": "Mobile Core",
            "role": "Mobile RTR",
            "services_count": 10,
            "tools_count": 9,
        },
    },
    {
        "slug": "domains/mobile-core/roles/mobile-rtr/huawei-mml-runbooks",
        "file": SLUGS_DIR / "huawei-mml-runbooks.md",
        "title": "Huawei MML Runbooks: Read-Only Audit vs IT Provisioning Remediation",
        "type": "runbook",
        "frontmatter": {
            "domain": "Mobile Core",
            "role": "Mobile RTR",
            "vendor": "Huawei",
            "tool": "iMaster NCE / LMT",
        },
    },
    {
        "slug": "domains/mobile-core/roles/mobile-rtr/customer-ticket-journey",
        "file": SLUGS_DIR / "customer-ticket-journey.md",
        "title": "Customer Trouble Ticket Journey: Schema, SLA Hierarchy & Bouncing Rules",
        "type": "procedure",
        "frontmatter": {
            "domain": "Mobile Core",
            "role": "Mobile RTR",
            "aola_target_hours": 2.0,
            "ola_target_hours": 6.0,
            "sla_target_hours": 48.0,
        },
    },
    {
        "slug": "domains/mobile-core/roles/mobile-rtr/queue-topology",
        "file": SLUGS_DIR / "queue-topology.md",
        "title": "Mobile Core RTR Queue Topology & Reassignment Matrix",
        "type": "topology",
        "frontmatter": {
            "domain": "Mobile Core",
            "role": "Mobile RTR",
        },
    },
    {
        "slug": "domains/mobile-core/roles/mobile-rtr/rtr-curated-summary",
        "file": SLUGS_DIR / "rtr-curated-summary.md",
        "title": "Mobile Core RTR Shift-Level Curated Ticket Summary",
        "type": "summary",
        "frontmatter": {
            "domain": "Mobile Core",
            "role": "Mobile RTR",
        },
    },
]

LINKS = [
    ("domains/mobile-core/roles/mobile-rtr/pipeline", "domains/mobile-core/roles/mobile-rtr/concern-findings-matrix", "classifies-with"),
    ("domains/mobile-core/roles/mobile-rtr/pipeline", "domains/mobile-core/roles/mobile-rtr/services-and-tools-catalog", "diagnoses"),
    ("domains/mobile-core/roles/mobile-rtr/pipeline", "domains/mobile-core/roles/mobile-rtr/huawei-mml-runbooks", "executes-with"),
    ("domains/mobile-core/roles/mobile-rtr/pipeline", "domains/mobile-core/roles/mobile-rtr/customer-ticket-journey", "structures-journey"),
    ("domains/mobile-core/roles/mobile-rtr/customer-ticket-journey", "domains/mobile-core/roles/mobile-rtr/queue-topology", "routes-through"),
    ("domains/mobile-core/roles/mobile-rtr/customer-ticket-journey", "domains/mobile-core/roles/mobile-rtr/rtr-curated-summary", "aggregated-by"),
]

def mcp_call(tool: str, args: dict, req_id: int):
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": tool, "arguments": args},
        "id": req_id
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {TOKEN}"
    }
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req) as resp:
        body = resp.read().decode("utf-8")
        for line in body.splitlines():
            if line.startswith("data: "):
                return json.loads(line[6:])
    return {}

def main():
    print(f"Connecting to gbrain MCP at {MCP_URL}...")
    req_id = 1
    
    # 1. Push all pages via put_page
    for page in PAGES:
        content = page["file"].read_text(encoding="utf-8")
        args = {
            "slug": page["slug"],
            "title": page["title"],
            "type": page["type"],
            "frontmatter": page["frontmatter"],
            "content": content
        }
        res = mcp_call("put_page", args, req_id)
        req_id += 1
        print(f"✓ Created/Updated gbrain slug: {page['slug']}")

    # 2. Add relational links via add_link
    for from_slug, to_slug, link_type in LINKS:
        args = {
            "from": from_slug,
            "to": to_slug,
            "link_type": link_type
        }
        try:
            mcp_call("add_link", args, req_id)
            req_id += 1
            print(f"✓ Linked [{from_slug}] --({link_type})--> [{to_slug}]")
        except Exception as e:
            print(f"  Note linking {from_slug} -> {to_slug}: {e}")

    print("\nAll Mobile Core RTR slugs and links successfully created in live gbrain via MCP!")

if __name__ == "__main__":
    main()
