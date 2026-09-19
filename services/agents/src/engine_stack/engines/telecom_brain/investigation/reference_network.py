"""Reference network provider that loads from reference_synthetic_network.yaml."""

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from .contracts import Relationship
from .evidence import reject_truth

_DEFAULT_YAML = Path(__file__).parent.parent / "simulator" / "operator_model" / "reference_synthetic_network.yaml"


class ReferenceNetworkProvider:
    """Knowledge provider backed by the reference_synthetic_network.yaml SSOT.

    Converts YAML entities/relationships into pages/relationships compatible
    with the InMemoryKnowledgeProvider interface.
    """

    def __init__(self, yaml_path: Path | str | None = None, version: str | None = None):
        path = Path(yaml_path) if yaml_path else _DEFAULT_YAML
        if not path.exists():
            raise FileNotFoundError(f"Reference network YAML not found: {path}")

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.network_id = data.get("network_id", "REF-MDO-001")
        self.network_name = data.get("name", "Reference Synthetic Network")
        self._version = version or f"ref-{data.get('version', '1.0')}"

        # Build pages from entities
        self.pages: dict[str, dict] = {}
        for ent in data.get("entities", []):
            eid = ent.get("entity_id", "")
            if not eid:
                continue
            page = {
                "slug": eid,
                "title": ent.get("canonical_name", eid),
                "type": ent.get("entity_type", "network-function"),
                "frontmatter": {
                    "entity_type": ent.get("entity_type", "network-function"),
                    "domain": ent.get("domain", ""),
                    "site": ent.get("site", ""),
                    "region": ent.get("region", ""),
                    "canonical_name": ent.get("canonical_name", eid),
                },
            }
            if ent.get("failure_domains"):
                page["frontmatter"]["failure_domains"] = ent["failure_domains"]
            if ent.get("vendor_profile"):
                page["frontmatter"]["vendor_profile"] = ent["vendor_profile"]
            self.pages[eid] = page

        # Also index sites, regions, domains as pages
        for site in data.get("sites", []):
            sid = site.get("site_id", "")
            if sid:
                self.pages[sid] = {
                    "slug": sid,
                    "title": site.get("name", sid),
                    "type": "site",
                    "frontmatter": {
                        "entity_type": "site",
                        "region": site.get("region", ""),
                        "site_type": site.get("site_type", ""),
                    },
                }
        for region in data.get("regions", []):
            rid = region.get("region_id", "")
            if rid:
                self.pages[rid] = {
                    "slug": rid,
                    "title": region.get("name", rid),
                    "type": "region",
                    "frontmatter": {"entity_type": "region"},
                }

        # Build relationships
        self.relationships: list[dict] = []
        for rel in data.get("relationships", []):
            rid = rel.get("relationship_id", "")
            src = rel.get("source_entity", "")
            tgt = rel.get("target_entity", "")
            ltype = (rel.get("relationship_type", "depends-on")).lower().replace("_", "-")
            if rid and src and tgt:
                self.relationships.append({
                    "relationship_id": rid,
                    "source": src,
                    "target": tgt,
                    "link_type": ltype,
                    "state": rel.get("status", "CONFIRMED"),
                    "confidence": rel.get("confidence", 1.0),
                    "provenance": "reference-operator-model",
                })

        reject_truth(list(self.pages.values()))
        reject_truth(self.relationships)

        self.metadata = {
            "knowledge_provider_type": type(self).__name__,
            "brain": "telecombrain",
            "snapshot_version": self._version,
            "consistency": "reference-network-ssot",
            "network_id": self.network_id,
            "network_name": self.network_name,
            "entity_count": len(self.pages),
            "relationship_count": len(self.relationships),
        }

    def get_page(self, slug: str) -> dict | None:
        return deepcopy(self.pages.get(slug))

    def get_links(self, slug: str) -> list[dict]:
        return deepcopy([edge for edge in self.relationships if edge["source"] == slug])

    def get_backlinks(self, slug: str) -> list[dict]:
        return deepcopy([edge for edge in self.relationships if edge["target"] == slug])

    def traverse(self, slug: str, depth: int, direction: str = "both", link_type: str | None = None) -> list[dict]:
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

    def search(self, query: str) -> list[dict]:
        q = query.lower()
        return deepcopy([page for page in self.pages.values() if q in json.dumps(page).lower()])

    def query(self, query: str) -> list[dict]:
        return self.search(query)


# Lazy import for search method
import json  # noqa: E402
