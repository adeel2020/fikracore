"""Read-only telecombrain adapters with canonical-first access and no fallback."""

import hashlib
import json
import urllib.request
from copy import deepcopy
from pathlib import Path
from typing import Any, Protocol

from ..canonicalization import load_default_resolver
from .contracts import Relationship
from .evidence import reject_truth


class ProviderError(RuntimeError):
    pass


class KnowledgeProvider(Protocol):
    metadata: dict

    def get_page(self, slug: str) -> dict | None: ...
    def get_links(self, slug: str) -> list[dict]: ...
    def get_backlinks(self, slug: str) -> list[dict]: ...
    def traverse(self, slug: str, depth: int, direction: str = "both", link_type: str | None = None) -> list[dict]: ...
    def search(self, query: str) -> list[dict]: ...
    def query(self, query: str) -> list[dict]: ...


class GbrainTelecomBrainProvider:
    """Strict HTTP MCP reads. Existing Storyteller fallback behavior is untouched."""

    REQUIRED = {"get_page", "get_links", "get_backlinks", "traverse_graph", "search", "query"}

    def __init__(self, url: str | None = None, token: str | None = None):
        from storyteller.knowledge.gbrain_client import _env_value
        self.url = (url or _env_value("GBRAIN_MCP_URL") or "http://localhost:3131").rstrip("/")
        if not self.url.endswith("/mcp"):
            self.url += "/mcp"
        self._token = token or _env_value("GBRAIN_MCP_TOKEN")
        tools = []
        cursor = None
        while True:
            result = self._rpc("tools/list", {"cursor": cursor} if cursor else {})
            tools.extend(result["tools"])
            following = result.get("nextCursor")
            if not following:
                break
            if following == cursor:
                raise ProviderError("MCP tool pagination did not advance")
            cursor = following
        self.contracts = {tool["name"]: tool["inputSchema"] for tool in tools}
        missing = self.REQUIRED - self.contracts.keys()
        if missing:
            raise ProviderError(f"Missing required MCP capabilities: {sorted(missing)}")
        self.metadata = {"knowledge_provider_type": type(self).__name__, "brain": "telecombrain",
                         "snapshot_version": None, "consistency": "live; may evolve during investigation"}
        if "get_active_schema_pack" in self.contracts:
            self.metadata["schema_identity"] = self._call("get_active_schema_pack", {})

    def _rpc(self, method: str, params: dict) -> Any:
        from storyteller.knowledge.gbrain_client import _extract_mcp_payload
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self._token:
            headers["Authorization"] = "Bearer " + self._token
        request = urllib.request.Request(self.url, headers=headers, data=json.dumps(
            {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode())
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                result = _extract_mcp_payload(response.read().decode(), response.headers.get("Content-Type", ""))
            if "error" in result:
                raise ProviderError("gbrain returned a JSON-RPC error")
            return result["result"]
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"gbrain request failed ({type(exc).__name__}); no substitute knowledge used") from None

    def _call(self, name: str, arguments: dict) -> Any:
        if name not in self.contracts:
            raise ProviderError(f"Unsupported gbrain operation: {name}")
        schema = self.contracts[name]
        if arguments.keys() - schema.get("properties", {}).keys():
            raise ProviderError("Arguments do not match discovered MCP contract")
        if set(schema.get("required", [])) - arguments.keys():
            raise ProviderError("Missing required MCP arguments")
        result = self._rpc("tools/call", {"name": name, "arguments": arguments})
        if "structuredContent" in result:
            data = result["structuredContent"]
        else:
            content = [block["text"] for block in result.get("content", []) if block.get("type") == "text"]
            if len(content) != 1:
                raise ProviderError("Expected one structured MCP result")
            try:
                data = json.loads(content[0])
            except ValueError:
                raise ProviderError("MCP result was not JSON") from None
        if name == "get_page" and isinstance(data, dict) and data.get("error") == "page_not_found":
            return None
        if result.get("isError") or (isinstance(data, dict) and data.get("error")):
            raise ProviderError(f"gbrain tool returned an error: {name}")
        reject_truth(data)
        return data

    def get_page(self, slug):
        return self._call("get_page", {"slug": slug})

    def get_links(self, slug):
        return self._call("get_links", {"slug": slug})

    def get_backlinks(self, slug):
        return self._call("get_backlinks", {"slug": slug})

    def traverse(self, slug, depth, direction="both", link_type=None):
        args = {"slug": slug, "depth": depth, "direction": direction}
        if link_type:
            args["link_type"] = link_type
        return self._call("traverse_graph", args)

    def search(self, query):
        return self._call("search", {"query": query})

    def query(self, query):
        return self._call("query", {"query": query})


class InMemoryKnowledgeProvider:
    """Explicit deterministic test adapter, never an automatic production fallback."""

    def __init__(self, pages: list[dict], relationships: list[dict], version="test-v1"):
        reject_truth(pages)
        reject_truth(relationships)
        self.pages = {page["slug"]: deepcopy(page) for page in pages}
        self.relationships = [Relationship.model_validate(edge).model_dump(mode="json") for edge in relationships]
        self.metadata = {"knowledge_provider_type": type(self).__name__, "brain": "telecombrain",
                         "snapshot_version": version, "consistency": "frozen test data"}

    def get_page(self, slug):
        return deepcopy(self.pages.get(slug))

    def get_links(self, slug):
        return deepcopy([edge for edge in self.relationships if edge["source"] == slug])

    def get_backlinks(self, slug):
        return deepcopy([edge for edge in self.relationships if edge["target"] == slug])

    def traverse(self, slug, depth, direction="both", link_type=None):
        if direction not in {"in", "out", "both"} or not 0 <= depth <= 10:
            raise ValueError("Invalid traversal direction or depth")
        frontier, seen, edges = {slug}, {slug}, {}
        for _ in range(depth):
            following = set()
            for edge in self.relationships:
                if link_type and edge["link_type"] != link_type:
                    continue
                if ((direction != "in" and edge["source"] in frontier) or
                        (direction != "out" and edge["target"] in frontier)):
                    edges[edge["relationship_id"]] = edge
                    following.update((edge["source"], edge["target"]))
            frontier = following - seen
            seen.update(frontier)
        return deepcopy([edges[key] for key in sorted(edges)])

    def search(self, query):
        return deepcopy([page for page in self.pages.values() if query.lower() in json.dumps(page).lower()])

    def query(self, query):
        return self.search(query)


class FrozenTelecomBrainProvider(InMemoryKnowledgeProvider):
    def __init__(self, path: Path):
        if "hidden" in path.resolve().parts:
            raise ValueError("Hidden simulator data is not an operational snapshot")
        raw = path.read_bytes()
        data = json.loads(raw)
        reject_truth(data)
        if set(data) != {"brain", "snapshot_version", "pages", "relationships"} or data["brain"] != "telecombrain":
            raise ValueError("Expected an explicit telecombrain operational snapshot")
        super().__init__(data["pages"], data["relationships"], data["snapshot_version"])
        self.metadata["snapshot_sha256"] = hashlib.sha256(raw).hexdigest()


class CanonicalKnowledge:
    """Canonical identity is stable even when only a legacy physical page exists."""

    def __init__(self, provider: KnowledgeProvider, resolver=None):
        self.provider = provider
        self.resolver = resolver or load_default_resolver()
        self.failures: set[str] = set()
        self.reads: dict[str, dict] = {}
        self._pages = {}
        self._physical = {}

    @property
    def mapping_version(self):
        return hashlib.sha256(json.dumps(self.resolver.mapping_records, sort_keys=True).encode()).hexdigest()

    def canonical(self, slug):
        return self.resolver.canonical_slug(slug)

    def get_page(self, slug):
        canonical = self.canonical(slug)
        if canonical not in self._pages:
            candidates = list(dict.fromkeys([canonical, *self.resolver.candidates(slug)]))
            page = None
            for physical in candidates:
                page = self.provider.get_page(physical)
                if page:
                    reject_truth(page)
                    if page.get("slug") != physical:
                        raise ProviderError("Provider returned a different entity for an exact lookup")
                    self._physical[canonical] = physical
                    break
            self._pages[canonical] = page
            if not page or physical != canonical:
                self.failures.add(canonical)
            self.reads[canonical] = {"canonical_slug": canonical,
                "physical_slug": self._physical.get(canonical), "missing_canonical_target": not page or physical != canonical,
                "content_sha256": hashlib.sha256(json.dumps(page, sort_keys=True).encode()).hexdigest()}
        return deepcopy(self._pages[canonical])

    def resolve_entity(self, slug, native=None):
        if self.get_page(slug):
            return self.canonical(slug)
        # Exact aliases only. A matching leaf/title is not sufficient to merge identities.
        matches = []
        for page in self.provider.search(native or slug):
            reject_truth(page)
            aliases = page.get("aliases", page.get("frontmatter", {}).get("aliases", []))
            if (native or slug) in aliases:
                matches.append(page["slug"])
        if len(set(matches)) == 1:
            return self.canonical(matches[0])
        return self.canonical(slug)

    def _edges(self, slug, operation, **kwargs):
        canonical = self.canonical(slug)
        if not self.get_page(slug):
            return []
        records = getattr(self.provider, operation)(self._physical[canonical], **kwargs)
        if not isinstance(records, list):
            raise ProviderError("Expected a list of operational relationships")
        result = []
        for raw in records:
            reject_truth(raw)
            source = raw.get("source", raw.get("from_slug"))
            target = raw.get("target", raw.get("to_slug"))
            kind = raw.get("link_type", raw.get("type"))
            if not all(isinstance(value, str) for value in (source, target, kind)):
                raise ProviderError("Unsupported operational edge representation")
            source, target = self.canonical(source), self.canonical(target)
            state = str(raw.get("state", raw.get("status", "UNKNOWN"))).upper()
            result.append(Relationship(
                relationship_id=str(raw.get("relationship_id", raw.get("id", f"{source}|{kind}|{target}"))),
                source=source, target=target, link_type=kind.lower().replace("_", "-"),
                state=state, confidence=raw.get("confidence", .5), provenance=raw.get("provenance", "telecombrain"),
            ))
        return result

    def get_links(self, slug):
        return self._edges(slug, "get_links")

    def get_backlinks(self, slug):
        return self._edges(slug, "get_backlinks")

    def traverse(self, slug, depth=4, direction="both", link_type=None):
        return self._edges(slug, "traverse", depth=depth, direction=direction, link_type=link_type)
