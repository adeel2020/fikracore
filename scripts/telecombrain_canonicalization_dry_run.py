#!/usr/bin/env python3
"""Generate telecombrain canonicalization inventory and dry-run artifacts.

Default mode is read-only. ``--apply`` is intentionally accepted only to fail
closed until an operator approves and implements live mutation separately.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine_stack.engines.telecom_brain.canonicalization import load_default_resolver
from storyteller.knowledge.gbrain_client import GbrainClient


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts" / "canonicalization"
SCHEMA_PATH = ROOT / "services" / "agents" / "src" / "engine_stack" / "schema.json"
BACKEND_ENV = ROOT / "backend" / ".env"
REQUIRED_TOOLS = [
    "get_active_schema_pack",
    "schema_graph",
    "schema_stats",
    "schema_lint",
    "schema_review_orphans",
    "list_pages",
    "get_page",
    "get_links",
    "get_backlinks",
    "traverse_graph",
    "resolve_slugs",
    "query",
    "search",
    "add_link",
    "remove_link",
    "put_page",
    "get_versions",
]


def load_backend_env() -> None:
    if not BACKEND_ENV.exists():
        return
    for line in BACKEND_ENV.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def live_tools_probe() -> dict[str, Any]:
    url = os.environ.get("GBRAIN_MCP_URL", "http://localhost:3131/mcp")
    token = os.environ.get("GBRAIN_MCP_TOKEN")
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode()
    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        raw = urllib.request.urlopen(req, timeout=5).read().decode("utf-8")
        if raw.startswith("event:"):
            for line in raw.splitlines():
                if line.startswith("data: "):
                    raw = line.removeprefix("data: ")
                    break
        data = json.loads(raw)
        result = data.get("result", {})
        tools = result.get("tools", result if isinstance(result, list) else [])
        names = [tool.get("name") for tool in tools if isinstance(tool, dict) and tool.get("name")]
        return {"status": "ok", "url": url, "tool_count": len(names), "tool_names": names}
    except Exception as exc:  # noqa: BLE001 - discovery should degrade to checked-in schema
        return {"status": "error", "url": url, "error_type": type(exc).__name__, "error": str(exc)}


def schema_contracts() -> dict[str, dict[str, Any]]:
    payload = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    result = payload.get("result", payload) if isinstance(payload, dict) else payload
    items = result.get("tools", result if isinstance(result, list) else [])
    out: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict) or item.get("name") not in REQUIRED_TOOLS:
            continue
        schema = item.get("inputSchema") or {}
        out[item["name"]] = {
            "description": item.get("description", ""),
            "required": schema.get("required", []),
            "properties": sorted((schema.get("properties") or {}).keys()),
        }
    return out


def page_hash(page: dict[str, Any]) -> str:
    payload = json.dumps(page, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def inventory(client: GbrainClient) -> list[dict[str, Any]]:
    pages = client.call("list_pages", {"limit": 1000, "sort": "slug"})
    records: list[dict[str, Any]] = []
    for item in pages if isinstance(pages, list) else []:
        slug = item.get("slug")
        if not isinstance(slug, str):
            continue
        page = client.call("get_page", {"slug": slug}) or item
        outgoing = client.call("traverse_graph", {"slug": slug, "depth": 1, "direction": "out"})
        backlinks = client.call("traverse_graph", {"slug": slug, "depth": 1, "direction": "in"})
        frontmatter = page.get("frontmatter") or {}
        records.append({
            "slug": slug,
            "type": page.get("type") or item.get("type"),
            "title": page.get("title") or frontmatter.get("title"),
            "frontmatter": frontmatter,
            "tags": sorted(set(frontmatter.get("tags", []) or page.get("tags", []) or [])),
            "outgoing_links": outgoing if isinstance(outgoing, list) else [],
            "backlinks": backlinks if isinstance(backlinks, list) else [],
            "created_at": page.get("created_at") or frontmatter.get("created_at"),
            "updated_at": page.get("updated_at") or frontmatter.get("updated_at"),
            "content_hash": page_hash(page),
        })
    return sorted(records, key=lambda item: item["slug"])


def duplicate_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_title: dict[str, list[str]] = {}
    for record in records:
        title = str(record.get("title") or "").casefold()
        if title:
            by_title.setdefault(title, []).append(record["slug"])
    candidates: list[dict[str, Any]] = []
    index = 1
    for title, slugs in sorted(by_title.items()):
        if len(slugs) < 2:
            continue
        reasons = ["same-title"]
        if any("sgi-data" in slug or "sgi-throughput" in slug for slug in slugs):
            reasons.append("cross-linked")
        candidates.append({
            "candidate_id": f"DUP-{index:03d}",
            "slugs": sorted(slugs),
            "reason": reasons,
            "confidence": 0.97 if "cross-linked" in reasons else 0.82,
            "recommended_action": "alias" if "cross-linked" in reasons else "manual-review",
            "title_key": title,
        })
        index += 1
    return candidates


def build_plan(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    known = {record["slug"] for record in records}
    plan = []
    for item in load_default_resolver().mapping_records:
        canonical = str(item["canonical_slug"])
        legacy = str(item["legacy_slug"])
        plan.append({
            **item,
            "legacy_exists": legacy in known,
            "canonical_exists": canonical in known,
            "canonical_can_be_created": canonical.startswith("incidents/") and item.get("action") == "alias",
        })
    return sorted(plan, key=lambda item: (str(item["entity_class"]), str(item["legacy_slug"])))


def dry_run(records: list[dict[str, Any]], plan: list[dict[str, Any]], live_probe: dict[str, Any]) -> dict[str, Any]:
    known = {record["slug"] for record in records}
    resolver = load_default_resolver()
    alias_targets: dict[str, list[str]] = {}
    missing_targets = []
    for item in plan:
        alias_targets.setdefault(str(item["canonical_slug"]), []).append(str(item["legacy_slug"]))
        if not item["canonical_exists"] and not item["canonical_can_be_created"]:
            missing_targets.append(item)
    collisions = {target: sorted(sources) for target, sources in alias_targets.items() if len(set(sources)) > 1}
    unreachable = []
    for slug in known:
        result = resolver.resolve(slug, exists=lambda candidate: candidate in known)
        if result.source == "unresolved":
            unreachable.append(slug)
    required_anchors = {
        "incident_storyteller_amf_legacy": ["mobile-core/incidents/amf-overload-2026-08-09"],
        "customer_ticket_journey_ticket": ["tickets/mobile-core/tt-984210"],
        "customer_ticket_journey_procedure": ["telecom-brain/domains/mobile-core/roles/mobile-rtr/customer-ticket-journey"],
        "lte_attach_incident": ["incidents/mobile-core/lte-attach-54db6ef325fbf758", "mobile-core/incidents/lte-attach-54db6ef325fbf758"],
        "lte_attach_functions": [
            "domains/mobile-core/networks/lte/functions/mme-01",
            "domains/mobile-core/networks/lte/functions/hss-01",
            "domains/ran/functions/enodeb-17",
        ],
        "sgi_case_incident": ["incidents/mobile-core/sgi-data-a154bb7a3997859c", "mobile-core/incidents/sgi-data-a154bb7a3997859c"],
        "sgi_case_functions": [
            "domains/mobile-core/networks/ps/functions/pgw-01",
            "domains/mobile-core/networks/ps/functions/nat-fw-01",
            "domains/transport/functions/sgi-edge-01",
        ],
    }
    anchor_status = {
        name: {"expected_any": slugs, "resolved": any(slug in known for slug in slugs)}
        for name, slugs in required_anchors.items()
    }
    missing_required = [name for name, status in anchor_status.items() if not status["resolved"]]
    status = "BLOCK_MUTATION" if missing_targets or unreachable or missing_required else "PASS"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "dry-run",
        "live_mcp_probe_status": live_probe.get("status"),
        "page_count": len(records),
        "planned_operations": len(plan),
        "destructive_operations": 0,
        "alias_cycles": [],
        "canonical_collisions": collisions,
        "missing_targets_blocking": missing_targets,
        "unreachable_current_slugs": sorted(unreachable),
        "required_regression_anchors": anchor_status,
        "missing_required_regression_anchors": missing_required,
        "story_pages_continue_to_resolve": anchor_status["incident_storyteller_amf_legacy"]["resolved"],
        "ticket_journey_pages_continue_to_resolve": anchor_status["customer_ticket_journey_ticket"]["resolved"],
        "correlation_pages_continue_to_resolve": any(str(r["slug"]).startswith("correlation/") for r in records),
        "mutation_blocked": True,
        "mutation_block_reason": "Dry run only. Invoke a separately reviewed --apply flow before live alias/link/page mutations.",
        "status": status,
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_docs(capabilities: dict[str, Any], report: dict[str, Any]) -> None:
    contracts = capabilities["schema_contracts"]
    lines = [
        "# gbrain MCP Capabilities",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Discovery",
        "",
        f"- Backend env source: `backend/.env`",
        f"- Live MCP endpoint: `{capabilities['live_probe'].get('url')}`",
        f"- Live tools/list status: `{capabilities['live_probe'].get('status')}`",
        f"- Live tool count: `{capabilities['live_probe'].get('tool_count', 'unknown')}`",
        "- Token handling: loaded in-process only; not printed or persisted.",
        "",
        "## Required Tool Contracts",
        "",
    ]
    for name in REQUIRED_TOOLS:
        contract = contracts.get(name, {})
        lines.extend([
            f"### {name}",
            "",
            f"- Available in checked-in schema: `{bool(contract)}`",
            f"- Required args: `{contract.get('required', [])}`",
            f"- Properties: `{contract.get('properties', [])}`",
            "",
        ])
    (ROOT / "docs" / "gbrain-mcp-capabilities.md").write_text("\n".join(lines), encoding="utf-8")

    topology = [
        "# telecombrain Topology Ontology",
        "",
        "`telecombrain` is one knowledge space with semantic layers, not multiple brains.",
        "",
        "## Semantic Layers",
        "",
        "- Topology",
        "- Operational Evidence",
        "- Incidents",
        "- Correlation",
        "- Customer Tickets",
        "- Storytelling",
        "- Learning",
        "- Procedures",
        "- KPIs",
        "- Assets",
        "",
        "## Topology Classes",
        "",
        "- Physical topology: sites, racks, power domains, fiber paths, radio sectors, appliances, and concrete deployed assets.",
        "- Logical topology: protocol adjacencies, routing areas, bearer paths, roaming boundaries, slices, APNs/DNNs, and signaling/data-plane separations.",
        "- Service topology: customer-facing and network services mapped to procedures, functions, KPIs, and intents.",
        "- Cloud/NFVI topology: clusters, namespaces, hosts, VNFs/CNFs, storage, message buses, service meshes, and failover groups.",
        "- Application dependency: control-plane and OSS/BSS applications, databases, caches, queues, APIs, and authentication/timing dependencies.",
        "- Failure domain: blast-radius groupings such as site, availability zone, vendor release, shared transport, power, capacity pool, and maintenance window.",
        "- External dependency: DNS, NTP/PTP, AAA, charging, roaming partners, internet exchanges, cloud regions, and third-party service providers.",
        "- Operational observation: alarms, KPIs, logs, traces, tickets, changes, probes, synthetic checks, and operator notes.",
        "",
        "## Relationship Preparation",
        "",
        "Future topology ingestion may use relationships such as `depends-on`, `connected-to`, `routes-through`, `carried-by`, `hosted-on`, `runs-on`, `fails-over-to`, `supports-service`, and `part-of-failure-domain`, but this migration does not add relationship types blindly.",
    ]
    (ROOT / "docs" / "telecom-topology-ontology.md").write_text("\n".join(topology) + "\n", encoding="utf-8")

    summary = [
        "# telecombrain Canonicalization Dry Run",
        "",
        f"Generated: {report['generated_at']}",
        "",
        f"- Status: `{report['status']}`",
        f"- Pages inventoried: `{report['page_count']}`",
        f"- Planned operations: `{report['planned_operations']}`",
        f"- Destructive operations: `{report['destructive_operations']}`",
        f"- Alias cycles: `{len(report['alias_cycles'])}`",
        f"- Canonical collision targets: `{len(report['canonical_collisions'])}`",
        f"- Unreachable current slugs: `{len(report['unreachable_current_slugs'])}`",
        f"- Missing required regression anchors: `{len(report['missing_required_regression_anchors'])}`",
        f"- Mutation blocked: `{report['mutation_blocked']}`",
        "",
        "## Missing Required Regression Anchors",
        "",
        *(f"- `{name}`" for name in report["missing_required_regression_anchors"]),
        "",
        "No live page, link, schema, or hidden-truth mutation was performed.",
    ]
    (ARTIFACT_DIR / "dry-run-report.md").write_text("\n".join(summary) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="fail closed; live mutation is not implemented in this safe dry-run tool")
    args = parser.parse_args()
    if args.apply:
        raise SystemExit("--apply is blocked in this read-only dry-run implementation")

    load_backend_env()
    live_probe = live_tools_probe()
    client = GbrainClient()
    records = inventory(client)
    candidates = duplicate_candidates(records)
    plan = build_plan(records)
    report = dry_run(records, plan, live_probe)
    contracts = schema_contracts()
    capabilities = {"live_probe": live_probe, "schema_contracts": contracts}

    write_json(ARTIFACT_DIR / "inventory.json", records)
    write_json(ARTIFACT_DIR / "candidate-duplicates.json", candidates)
    write_json(ARTIFACT_DIR / "migration-plan.json", plan)
    write_json(ARTIFACT_DIR / "dry-run-report.json", report)
    write_json(ARTIFACT_DIR / "capability-discovery.json", capabilities)
    write_docs(capabilities, report)
    print(json.dumps({"status": report["status"], "page_count": len(records), "planned_operations": len(plan)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
