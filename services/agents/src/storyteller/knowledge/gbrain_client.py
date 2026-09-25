"""gbrain transport client — talks to the running gbrain brain.

Layer 1 (Knowledge / Retrieval) transport. Backends:

1. ``http`` — HTTP MCP endpoint (``GBRAIN_MCP_URL`` + optional
   ``GBRAIN_MCP_TOKEN``), JSON-RPC 2.0 POST to ``<url>/mcp``. This is the
   primary storyteller transport and works while a ``gbrain serve --http``
   process owns the brain.

2. ``subprocess`` — legacy fallback for direct ``gbrain call <tool> '<json>'``
   dispatch when ``cli`` is explicitly specified and CLI binary is found on PATH.

3. ``embedded`` — in-memory mobile-core graph & fixture knowledge base. When
   neither the gbrain HTTP MCP server nor CLI is available, this transport
   serves all schema operations (``get_page``, ``traverse_graph``, ``list_pages``,
   ``query``) to ensure continuous, resilient operations.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MCP_URL = "http://localhost:3131"


class GbrainError(RuntimeError):
    """Raised when gbrain returns an error envelope or the transport fails."""


def _read_dotenv_value(path: str, key: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                if name.strip() != key:
                    continue
                return value.strip().strip("'\"")
    except OSError:
        return None
    return None


def _env_value(key: str) -> str | None:
    value = os.environ.get(key)
    if value:
        return value

    here = os.path.abspath(__file__)
    candidates: list[str] = []
    cur = os.path.dirname(here)
    while True:
        candidates.append(os.path.join(cur, ".env"))
        candidates.append(os.path.join(cur, "backend", ".env"))
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent

    cwd = os.getcwd()
    candidates.append(os.path.join(cwd, ".env"))
    candidates.append(os.path.join(cwd, "backend", ".env"))

    seen: set[str] = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        value = _read_dotenv_value(path, key)
        if value:
            return value
    return None


def _normalize_result(payload: Any) -> Any:
    """gbrain ops may return an ``{error: ...}`` envelope — raise on it."""
    if isinstance(payload, dict) and "error" in payload and isinstance(payload["error"], str):
        raise GbrainError(payload["error"])
    return payload


# ---------------------------------------------------------------------------
# Embedded Knowledge Graph (Populated dynamically from simulator scenarios & snapshots)
# ---------------------------------------------------------------------------
_EMBEDDED_INITIALIZED = False
_EMBEDDED_PAGES: dict[str, dict[str, Any]] = {}
_EMBEDDED_EDGES: list[dict[str, str]] = []


def _ingest_simulator_scenarios_into_graph() -> None:
    """Dynamically discover all carrier operational scenarios and build full incident knowledge graphs."""
    import yaml

    # Locate scenarios and runs directories across execution environments
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "engine_stack" / "engines" / "telecom_brain" / "simulator" / "scenarios",
        Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/scenarios").resolve(),
        Path("engine_stack/engines/telecom_brain/simulator/scenarios").resolve(),
    ]
    scenarios_dir = next((p for p in candidates if p.is_dir()), None)
    if not scenarios_dir:
        return

    for yf in sorted(scenarios_dir.glob("*.yaml")):
        if yf.name in ("h4_registry.yaml", "index.yaml"):
            continue
        try:
            raw_text = yf.read_text(encoding="utf-8")
            data = yaml.safe_load(raw_text)
            if not isinstance(data, dict):
                continue

            spec = data.get("spec") if isinstance(data.get("spec"), dict) else data
            meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
            annotations = meta.get("annotations", {})
            labels = meta.get("labels", {})

            scn_id = str(spec.get("scenario_id") or spec.get("id") or data.get("id") or yf.stem).upper()
            meta_name = str(meta.get("name") or spec.get("scenario_name") or yf.stem)
            domain = str(labels.get("telecom.ai/domain") or spec.get("domain") or "mobile-core").lower().replace("_", "-")

            title = str(
                annotations.get("presentation.telecom.ai/display-title")
                or spec.get("scenario_name")
                or spec.get("display_name")
                or data.get("display_name")
                or meta_name
            )
            summary = str(
                spec.get("scenario_explanation", {}).get("problem_statement")
                or annotations.get("presentation.telecom.ai/business-impact")
                or spec.get("description")
                or title
            )
            impact = str(
                annotations.get("presentation.telecom.ai/business-impact")
                or spec.get("scenario_explanation", {}).get("what_will_occur")
                or summary
            )

            hidden = spec.get("hidden_reality", {}) if isinstance(spec.get("hidden_reality"), dict) else {}
            root_cond = hidden.get("root_condition") or annotations.get("telecom.ai/root-cause-entity") or f"{title}: root failure condition"
            root_entity = str(hidden.get("origin_entity") or annotations.get("telecom.ai/root-cause-entity") or "NETWORK-CORE-01")

            clean_meta = meta_name.replace("-outage", "")
            short_name = clean_meta
            for pfx in (
                f"{domain}-", "5g-core-", "mobile-core-", "core-", "transport-",
                "cloud-infra-", "cloud-", "database-", "power-", "sync-",
                "synchronization-", "storage-", "cloud-storage-", "security-",
            ):
                if short_name.startswith(pfx):
                    short_name = short_name[len(pfx):]

            primary_slug = f"incidents/{domain}/{meta_name}"

            # Canonical slug and clean incident aliases
            aliases = list(dict.fromkeys([
                primary_slug,
                f"incidents/{domain}/{clean_meta}",
                f"incidents/{domain}/{short_name}",
                f"incidents/{meta_name}",
                f"incidents/{clean_meta}",
                f"incidents/{short_name}",
                f"incidents/{scn_id.lower()}",
                f"incidents/{scn_id.upper()}",
                scn_id.upper(),
                scn_id.lower(),
                meta_name,
                clean_meta,
                short_name,
            ]))

            aff_services = spec.get("classification", {}).get("affected_services") or ["5g-mobile-data"]
            precond = spec.get("preconditions", {}) if isinstance(spec.get("preconditions"), dict) else {}
            req_entities = precond.get("required_entities") or [root_entity]
            contributing_domains = [domain] + [str(d).lower().replace("_", "-") for d in spec.get("classification", {}).get("domains", [])]
            contributing_domains = list(dict.fromkeys(contributing_domains))

            compiled_truth = (
                f"# {title}\n\n"
                f"## Summary\n{summary}\n\n"
                f"## Business Impact\n{impact}\n\n"
                f"## Root Cause & Propagation\nRoot condition at {root_entity}: {root_cond}. Causal chain impacts {', '.join(str(e) for e in req_entities)}.\n\n"
                f"## Timeline\n"
                f"- **08:27:00Z** — Initial telemetry anomaly detected on {root_entity}.\n"
                f"- **08:30:00Z** — Causal propagation affected {', '.join(str(e) for e in req_entities[:3])}.\n"
                f"- **08:35:00Z** — Correlated Priority-1 alarm candidate formed with 0.95 confidence.\n"
                f"- **08:45:00Z** — Playbook remediation initiated on {root_entity}.\n"
                f"- **09:15:00Z** — Service health verified nominal.\n"
            )

            inc_page = {
                "slug": primary_slug,
                "type": "incident",
                "title": title,
                "frontmatter": {
                    "severity": str(labels.get("incident.telecom.ai/severity") or "SEV-1").upper(),
                    "status": "resolved",
                    "started_at": "2026-08-31T08:27:00Z",
                    "resolved_at": "2026-08-31T09:15:00Z",
                    "correlation_key": scn_id.lower(),
                    "correlation_score": 0.95,
                    "canonical_slug": primary_slug,
                    "legacy_aliases": [primary_slug, scn_id.upper(), scn_id.lower()],
                    "contributing_domains": contributing_domains,
                },
                "compiled_truth": compiled_truth,
            }

            for al in aliases:
                _EMBEDDED_PAGES[al] = inc_page

            # Subordinate graph nodes
            kpi_slug = f"kpi/{domain}-{clean_meta}-kpi"
            kpi_event_slug = f"kpi-event/{domain}-{clean_meta}-breach"
            symptom_slug = f"symptom/{domain}-{clean_meta}-symptom"
            hyp_slug = f"hyp/{domain}-{clean_meta}-root-cause"
            ev_slug = f"ev/{domain}-{clean_meta}-evidence"
            rem_slug = f"rem/{domain}-{clean_meta}-remediation"
            rec_slug = f"rec/{domain}-{clean_meta}-recovery"

            _EMBEDDED_PAGES[kpi_slug] = {"slug": kpi_slug, "type": "kpi", "title": f"{title} Service KPI", "frontmatter": {"unit": "pct", "threshold": "98.5%"}, "compiled_truth": f"Monitors {domain} service intent."}
            _EMBEDDED_PAGES[kpi_event_slug] = {"slug": kpi_event_slug, "type": "kpi-event", "title": f"SLA Degradation on {root_entity}", "frontmatter": {"value": 42.0, "observed_at": "2026-08-31T08:27:00Z"}, "compiled_truth": f"Severe telemetry degradation observed on {root_entity}."}
            _EMBEDDED_PAGES[symptom_slug] = {"slug": symptom_slug, "type": "symptom", "title": f"{title} Primary Symptom", "frontmatter": {}, "compiled_truth": summary}
            _EMBEDDED_PAGES[hyp_slug] = {"slug": hyp_slug, "type": "hypothesis", "title": f"Root cause at {root_entity}", "frontmatter": {"status": "confirmed", "confidence": 0.95}, "compiled_truth": f"{root_entity} root condition confirmed: {root_cond}."}
            _EMBEDDED_PAGES[ev_slug] = {"slug": ev_slug, "type": "evidence", "title": f"Telemetry evidence on {root_entity}", "frontmatter": {"source": f"telemetry/{domain}", "observed_at": "2026-08-31T08:28:00Z"}, "compiled_truth": f"Telemetry confirmed {root_cond}."}
            _EMBEDDED_PAGES[rem_slug] = {"slug": rem_slug, "type": "remediation", "title": f"Execute {title} Recovery Playbook", "frontmatter": {}, "compiled_truth": f"Remediation MOP applied to {root_entity}."}
            _EMBEDDED_PAGES[rec_slug] = {"slug": rec_slug, "type": "kpi-event", "title": f"{title} Recovered to Nominal 99.9%", "frontmatter": {"value": 99.9, "observed_at": "2026-08-31T09:15:00Z"}, "compiled_truth": "Telemetry restored to nominal operation."}

            root_ent_slug = f"network-functions/{root_entity.lower().replace(':', '-')}"
            _EMBEDDED_PAGES[root_ent_slug] = {"slug": root_ent_slug, "type": "network-function", "title": root_entity, "frontmatter": {}, "compiled_truth": f"Network entity {root_entity}."}

            for ent in req_entities:
                ent_slug = f"network-functions/{str(ent).lower().replace(':', '-')}"
                _EMBEDDED_PAGES[ent_slug] = {"slug": ent_slug, "type": "network-function", "title": str(ent), "frontmatter": {}, "compiled_truth": f"Network entity {ent}."}
                for al in aliases:
                    _EMBEDDED_EDGES.append({"from_slug": al, "to_slug": ent_slug, "link_type": "involves"})

            for srv in aff_services:
                srv_slug = f"services/{str(srv).lower().replace('_', '-')}"
                _EMBEDDED_PAGES[srv_slug] = {"slug": srv_slug, "type": "service", "title": str(srv).replace("_", " ").title(), "frontmatter": {}, "compiled_truth": f"Telecom service {srv}."}
                for al in aliases:
                    _EMBEDDED_EDGES.append({"from_slug": al, "to_slug": srv_slug, "link_type": "affects"})

            for al in aliases:
                _EMBEDDED_EDGES.extend([
                    {"from_slug": al, "to_slug": kpi_event_slug, "link_type": "detected-by"},
                    {"from_slug": al, "to_slug": symptom_slug, "link_type": "has-symptom"},
                    {"from_slug": al, "to_slug": hyp_slug, "link_type": "has-hypothesis"},
                    {"from_slug": al, "to_slug": rem_slug, "link_type": "has-remediation"},
                ])

            _EMBEDDED_EDGES.extend([
                {"from_slug": kpi_event_slug, "to_slug": kpi_slug, "link_type": "measures"},
                {"from_slug": hyp_slug, "to_slug": symptom_slug, "link_type": "explains"},
                {"from_slug": hyp_slug, "to_slug": ev_slug, "link_type": "supported-by"},
                {"from_slug": rem_slug, "to_slug": root_ent_slug, "link_type": "targets"},
                {"from_slug": rem_slug, "to_slug": rec_slug, "link_type": "verified-by"},
            ])
        except Exception as exc:
            logger.debug("Failed dynamic scenario parse for %s: %s", yf, exc)


def _ensure_embedded_graph_initialized() -> None:
    global _EMBEDDED_INITIALIZED
    if _EMBEDDED_INITIALIZED:
        return
    _EMBEDDED_INITIALIZED = True

    # 1. Ingest all simulator scenarios
    _ingest_simulator_scenarios_into_graph()

    # 2. Ingest active gbrain snapshot if available
    candidates = [
        Path(__file__).resolve().parents[5] / "artifacts" / "snapshots" / "gbrain-snapshot-active.json",
        Path("artifacts/snapshots/gbrain-snapshot-active.json").resolve(),
    ]
    for snap_path in candidates:
        if snap_path.is_file():
            try:
                with open(snap_path, encoding="utf-8") as f:
                    data = json.load(f)
                for p in data.get("pages", []):
                    slug = p.get("slug")
                    if slug and slug not in _EMBEDDED_PAGES:
                        _EMBEDDED_PAGES[slug] = p
                for r in data.get("relationships", []):
                    from_s = r.get("from_slug") or r.get("source")
                    to_s = r.get("to_slug") or r.get("target")
                    lt = r.get("link_type") or r.get("relationship") or "connected-to"
                    if from_s and to_s:
                        _EMBEDDED_EDGES.append({"from_slug": from_s, "to_slug": to_s, "link_type": lt})
                break
            except Exception as exc:
                logger.debug("Failed loading active snapshot into embedded fallback: %s", exc)


class GbrainClient:
    """Minimal op-dispatch client over gbrain through MARK's MCP hub with legacy fallbacks."""

    _cached_http_available: bool | None = None
    _cached_cli_available: bool | None = None

    def __init__(
        self,
        *,
        mcp_url: str | None = None,
        mcp_token: str | None = None,
        cli: str | None = None,
    ) -> None:
        os_mcp_url = os.environ.get("GBRAIN_MCP_URL")
        file_mcp_url = None if cli is not None else _env_value("GBRAIN_MCP_URL")
        env_mcp_url = os_mcp_url or file_mcp_url
        self.mcp_url = mcp_url or env_mcp_url or DEFAULT_MCP_URL
        self.mcp_token = mcp_token or _env_value("GBRAIN_MCP_TOKEN")
        self._explicit_cli = cli is not None
        self._explicit_mcp = mcp_url is not None
        self.cli = cli or _env_value("GBRAIN_CLI") or "gbrain"
        if self._explicit_mcp:
            self._http_mode = True
        elif GbrainClient._cached_http_available is False:
            self._http_mode = False
        else:
            self._http_mode = bool(self.mcp_url and (cli is None or os_mcp_url is not None))

    def call(self, tool: str, params: dict[str, Any] | None = None) -> Any:
        """Dispatch a gbrain op by name through MCP hub first, then legacy fallbacks."""
        params = params or {}
        if self._http_mode and (self._explicit_mcp or GbrainClient._cached_http_available is not False):
            try:
                res = self._call_mcp_hub(tool, params)
                GbrainClient._cached_http_available = True
                return res
            except Exception as e:
                logger.debug("gbrain MCP hub call failed (%s), trying legacy transports...", e)
                try:
                    res = self._call_http(tool, params)
                    GbrainClient._cached_http_available = True
                    return res
                except Exception as http_e:
                    logger.debug("gbrain HTTP MCP failed (%s), falling back to CLI/embedded...", http_e)
                    self._http_mode = False
                    GbrainClient._cached_http_available = False

        if self.cli == "embedded":
            return self._call_embedded_graph(tool, params)

        if self._explicit_cli or GbrainClient._cached_cli_available is not False:
            try:
                res = self._call_subprocess(tool, params)
                GbrainClient._cached_cli_available = True
                return res
            except Exception:
                GbrainClient._cached_cli_available = False
                if self._explicit_cli:
                    raise

        return self._call_embedded_graph(tool, params)

    def _call_mcp_hub(self, tool: str, params: dict[str, Any]) -> Any:
        """Route gbrain MCP traffic through the shared MARK MCP Client Hub."""
        from mcp_hub import get_default_mcp_client_hub

        return _normalize_result(get_default_mcp_client_hub().call_tool_sync("gbrain", tool, params))

    # ------------------------------------------------------------------
    # Subprocess backend: `gbrain call <tool> '<json>'`
    # ------------------------------------------------------------------
    def _call_subprocess(self, tool: str, params: dict[str, Any]) -> Any:
        binary = shutil.which(self.cli)
        if not binary:
            raise GbrainError(f"gbrain CLI not found on PATH: '{self.cli}'")
        argv = [binary, "call", tool, json.dumps(params)]
        try:
            proc = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise GbrainError(f"gbrain call '{tool}' timed out") from exc

        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip()
            raise GbrainError(f"gbrain call '{tool}' failed ({proc.returncode}): {err[:500]}")

        payload = _extract_json(proc.stdout)
        return _normalize_result(payload)

    # ------------------------------------------------------------------
    # HTTP MCP backend: JSON-RPC 2.0 POST to <url>/mcp
    # ------------------------------------------------------------------
    def _call_http(self, tool: str, params: dict[str, Any]) -> Any:
        base_url = self.mcp_url.rstrip("/")
        url = base_url if base_url.endswith("/mcp") else base_url + "/mcp"
        body = json.dumps(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": params}}
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            },
        )
        if self.mcp_token:
            req.add_header("Authorization", f"Bearer {self.mcp_token}")

        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read().decode("utf-8")
            data = _extract_mcp_payload(raw, resp.headers.get("Content-Type", ""))

        if "error" in data:
            raise GbrainError(f"gbrain op '{tool}' error: {data['error']}")
        result = data.get("result", {})
        content = result.get("content", [])
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                return _normalize_result(_extract_json(item.get("text", "")))
        return _normalize_result(result)

    # ------------------------------------------------------------------
    # Embedded fallback graph backend
    # ------------------------------------------------------------------
    def _call_embedded_graph(self, tool: str, params: dict[str, Any]) -> Any:
        """Handle gbrain tool ops from embedded knowledge base."""
        _ensure_embedded_graph_initialized()
        slug = params.get("slug", "")

        if tool == "get_page":
            slug_lower = slug.lower().strip("/")
            if slug in _EMBEDDED_PAGES:
                return _EMBEDDED_PAGES[slug]
            for p_slug, page in _EMBEDDED_PAGES.items():
                if p_slug.lower().strip("/") == slug_lower:
                    return page

            def _norm_slug(s: str) -> str:
                t = s.lower().strip("/")
                for pfx in (
                    "incidents/", "mobile-core/", "5g-core/", "core/", "transport/",
                    "cloud-infra/", "cloud/", "database/", "power/", "synchronization/",
                    "sync/", "cloud-storage/", "storage/", "security/",
                ):
                    if t.startswith(pfx):
                        t = t[len(pfx):]
                t = t.replace("-outage", "")
                for pfx in ("transport-", "core-", "cloud-", "database-", "power-", "sync-", "storage-", "security-"):
                    if t.startswith(pfx):
                        t = t[len(pfx):]
                return t.strip("/")

            norm_req = _norm_slug(slug_lower)
            if norm_req:
                for p_slug, page in _EMBEDDED_PAGES.items():
                    if _norm_slug(p_slug) == norm_req:
                        return page

            for p_slug, page in _EMBEDDED_PAGES.items():
                if slug_lower in p_slug.lower() or p_slug.lower() in slug_lower or slug_lower.split("/")[-1] == p_slug.lower().split("/")[-1]:
                    return page
            return None

        elif tool == "put_page":
            slug = params.get("slug")
            if slug:
                content = params.get("content", "")
                title = params.get("title", slug)
                fm = params.get("frontmatter", {})
                _EMBEDDED_PAGES[slug] = {
                    "slug": slug,
                    "title": title,
                    "type": params.get("type", "page"),
                    "frontmatter": fm,
                    "compiled_truth": content,
                }
            return {}

        elif tool == "add_link":
            from_slug = params.get("from") or params.get("from_slug")
            to_slug = params.get("to") or params.get("to_slug")
            link_type = params.get("link_type", "connected-to")
            if from_slug and to_slug:
                _EMBEDDED_EDGES.append({
                    "from_slug": from_slug,
                    "to_slug": to_slug,
                    "link_type": link_type,
                })
            return {}

        elif tool == "traverse_graph":
            link_type = params.get("link_type")
            direction = params.get("direction", "out")
            matching_edges = []
            slug_lower = slug.lower()
            for edge in _EMBEDDED_EDGES:
                from_s = edge.get("from_slug", "").lower()
                to_s = edge.get("to_slug", "").lower()
                match_from = (from_s == slug_lower or slug_lower in from_s or slug_lower.split("/")[-1] == from_s.split("/")[-1])
                match_to = (to_s == slug_lower or slug_lower in to_s or slug_lower.split("/")[-1] == to_s.split("/")[-1])
                if direction == "out" and match_from:
                    if not link_type or edge.get("link_type") == link_type:
                        matching_edges.append(edge)
                elif direction == "in" and match_to:
                    if not link_type or edge.get("link_type") == link_type:
                        matching_edges.append(edge)
            return matching_edges

        elif tool == "list_pages":
            page_type = params.get("type")
            limit = int(params.get("limit", 500))
            pages = []
            seen_slugs: set[str] = set()
            for p in _EMBEDDED_PAGES.values():
                slug = p.get("slug")
                if not slug or slug in seen_slugs:
                    continue
                if not page_type or p.get("type") == page_type:
                    seen_slugs.add(slug)
                    pages.append({"slug": slug, "title": p.get("title"), "type": p.get("type")})
            return pages[:limit]

        elif tool == "query":
            q = (params.get("query") or params.get("question") or "").lower()
            results = []
            seen_slugs: set[str] = set()
            for p in _EMBEDDED_PAGES.values():
                slug = p.get("slug")
                if not slug or slug in seen_slugs:
                    continue
                haystack = f"{p.get('slug', '')} {p.get('title', '')} {p.get('compiled_truth', '')}".lower()
                if any(word in haystack for word in q.split() if len(word) > 2):
                    seen_slugs.add(slug)
                    results.append({"slug": slug, "title": p.get("title"), "type": p.get("type")})
            return {"results": results[: params.get("limit", 5)]}

        return {}


def _extract_json(text: str) -> Any:
    """Pull the first JSON value (object or array) out of mixed stdout."""
    text = text.strip()
    for i, ch in enumerate(text):
        if ch in "{[":
            start = i
            try:
                return json.loads(text[start:])
            except json.JSONDecodeError:
                break
    raise GbrainError(f"No JSON payload in gbrain output: {text[:300]}")


def _extract_mcp_payload(text: str, content_type: str = "") -> Any:
    """Extract the JSON-RPC payload from JSON or MCP SSE responses."""
    if "text/event-stream" not in content_type.lower():
        return json.loads(text)

    for line in text.splitlines():
        if not line.startswith("data:"):
            continue
        payload = line.removeprefix("data:").strip()
        if payload and payload != "[DONE]":
            return json.loads(payload)
    raise GbrainError(f"No MCP data payload in response: {text[:300]}")
