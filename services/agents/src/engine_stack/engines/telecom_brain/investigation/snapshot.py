"""Authoritative Snapshot Manager for FikraCore (§18, §19, §47).

Responsible for:
- Exporting / taking live knowledge snapshots from telecombrain (MCP or in-memory)
- Loading, verifying and validating frozen snapshot files
- Listing existing snapshots in the repository
- Inspecting snapshot metadata and stats
Strictly isolates hidden evaluator truth from operational snapshots.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .contracts import Relationship
from .evidence import reject_truth
from .knowledge import FrozenTelecomBrainProvider

logger = logging.getLogger("fikracore.snapshot")

def find_repo_root() -> Path:
    """Locate the root directory of the kagent repository."""
    cur = Path(__file__).resolve().parent
    while cur != cur.parent:
        if (cur / ".git").exists() or ((cur / "services").exists() and (cur / "artifacts").exists()):
            return cur
        cur = cur.parent

    cur = Path.cwd().resolve()
    while cur != cur.parent:
        if (cur / ".git").exists() or ((cur / "services").exists() and (cur / "artifacts").exists()):
            return cur
        cur = cur.parent

    return Path.cwd().resolve()


CANONICAL_REPO_ROOT = find_repo_root()
DEFAULT_SNAPSHOTS_DIR = (CANONICAL_REPO_ROOT / "artifacts" / "snapshots").resolve()


class SnapshotMetadata:
    """Lightweight metadata descriptor for a discovered snapshot."""

    def __init__(
        self,
        path: Path,
        brain: str,
        snapshot_version: str,
        page_count: int,
        relationship_count: int,
        size_bytes: int,
        sha256: str,
        mtime: float = 0.0,
    ) -> None:
        self.path = path
        self.brain = brain
        self.snapshot_version = snapshot_version
        self.page_count = page_count
        self.relationship_count = relationship_count
        self.size_bytes = size_bytes
        self.sha256 = sha256
        self.mtime = mtime
        self.created_at = (
            datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
            if mtime
            else ""
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "filename": self.path.name,
            "brain": self.brain,
            "snapshot_version": self.snapshot_version,
            "pages": self.page_count,
            "relationships": self.relationship_count,
            "size_kb": round(self.size_bytes / 1024, 1),
            "sha256": self.sha256[:12] + "...",
            "created_at": self.created_at,
            "mtime": self.mtime,
        }


class SnapshotManager:
    """Authoritative service for taking, loading, listing, and verifying FikraCore snapshots."""

    def __init__(self, snapshots_dir: Optional[Path] = None) -> None:
        if snapshots_dir:
            self.snapshots_dir = Path(snapshots_dir).resolve()
        else:
            self.snapshots_dir = DEFAULT_SNAPSHOTS_DIR

    def resolve_snapshot_path(self, identifier_or_path: str | Path) -> Path:
        """Resolve a snapshot file by exact path, relative path, or filename prefix."""
        p_str = str(identifier_or_path).strip()
        # Clean any accidental nested artifacts/snapshots prefixes
        if "artifacts/snapshots" in p_str:
            idx = p_str.rfind("artifacts/snapshots") + len("artifacts/snapshots")
            cleaned = p_str[idx:].lstrip("/\\")
            if cleaned:
                p_str = cleaned

        p = Path(p_str)
        if p.exists() and p.is_file():
            return p.resolve()

        # Check in snapshots_dir
        in_snapshots = (self.snapshots_dir / p.name).resolve()
        if in_snapshots.exists() and in_snapshots.is_file():
            return in_snapshots

        target_str = p.name.lower().strip()
        if target_str in ("latest", "last"):
            snapshots = self.list_snapshots()
            for s in snapshots:
                if s.path.name != "gbrain-snapshot-active.json":
                    return s.path.resolve()
            if snapshots:
                return snapshots[0].path.resolve()

        matches = []
        if self.snapshots_dir.exists():
            for f in sorted(self.snapshots_dir.glob("*.json")):
                if target_str in f.name.lower():
                    if f.resolve() not in matches:
                        matches.append(f.resolve())

        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            raise ValueError(
                f"Ambiguous snapshot name '{identifier_or_path}'. Matches: {[m.name for m in matches]}"
            )

        raise FileNotFoundError(f"Snapshot file not found matching '{identifier_or_path}' in {self.snapshots_dir}")

    def load_provider(self, snapshot_path: str | Path) -> FrozenTelecomBrainProvider:
        """Loads and validates a frozen operational snapshot provider."""
        resolved = self.resolve_snapshot_path(snapshot_path)
        return FrozenTelecomBrainProvider(resolved)

    def list_snapshots(self) -> List[SnapshotMetadata]:
        """Discover and summarize all operational snapshot files (sorted newest first)."""
        if not self.snapshots_dir.exists():
            return []

        seen_paths = set()
        results: List[SnapshotMetadata] = []
        candidate_files = sorted(
            self.snapshots_dir.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        for file_path in candidate_files:
            if file_path.resolve() in seen_paths or file_path.name.startswith("."):
                continue
            seen_paths.add(file_path.resolve())
            try:
                stat = file_path.stat()
                raw = file_path.read_bytes()
                data = json.loads(raw)
                if isinstance(data, dict) and data.get("brain") == "telecombrain":
                    meta = SnapshotMetadata(
                        path=file_path,
                        brain=data.get("brain", "telecombrain"),
                        snapshot_version=data.get("snapshot_version", "unknown"),
                        page_count=len(data.get("pages", [])),
                        relationship_count=len(data.get("relationships", [])),
                        size_bytes=len(raw),
                        sha256=hashlib.sha256(raw).hexdigest(),
                        mtime=stat.st_mtime,
                    )
                    results.append(meta)
            except Exception as e:
                logger.debug(f"Skipping invalid snapshot candidate {file_path}: {e}")

        return results

    def inspect_snapshot(self, snapshot_path: str | Path) -> Dict[str, Any]:
        """Deep inspection of an operational snapshot without modifying state."""
        resolved = self.resolve_snapshot_path(snapshot_path)
        raw = resolved.read_bytes()
        data = json.loads(raw)
        reject_truth(data)

        pages = data.get("pages", [])
        rels = data.get("relationships", [])

        domain_counts: Dict[str, int] = {}
        type_counts: Dict[str, int] = {}
        for p in pages:
            dom = p.get("domain", "Unknown")
            ptype = p.get("type", "concept")
            domain_counts[dom] = domain_counts.get(dom, 0) + 1
            type_counts[ptype] = type_counts.get(ptype, 0) + 1

        rel_type_counts: Dict[str, int] = {}
        for r in rels:
            ltype = r.get("link_type", "depends-on")
            rel_type_counts[ltype] = rel_type_counts.get(ltype, 0) + 1

        return {
            "path": str(resolved),
            "filename": resolved.name,
            "brain": data.get("brain"),
            "snapshot_version": data.get("snapshot_version"),
            "total_pages": len(pages),
            "total_relationships": len(rels),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "domains": domain_counts,
            "page_types": type_counts,
            "relationship_types": rel_type_counts,
        }

    def create_snapshot(
        self,
        provider: Any = None,
        output_path: Optional[str | Path] = None,
        version_tag: Optional[str] = None,
    ) -> Tuple[Path, Dict[str, Any]]:
        """Takes a fresh frozen operational snapshot from an active provider or topology baseline."""
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        version = version_tag or f"v1.0.0-snapshot-{timestamp_str}"

        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        if not output_path:
            target = self.snapshots_dir / f"gbrain-snapshot-{timestamp_str}.json"
        else:
            p_str = str(output_path).strip()
            if "artifacts/snapshots" in p_str:
                idx = p_str.rfind("artifacts/snapshots") + len("artifacts/snapshots")
                clean_name = p_str[idx:].lstrip("/\\")
                target = self.snapshots_dir / (clean_name or f"gbrain-snapshot-{timestamp_str}.json")
            else:
                p = Path(p_str)
                if p.is_absolute() and not str(p).startswith(str(self.snapshots_dir)):
                    target = p
                else:
                    target = self.snapshots_dir / p.name
            target.parent.mkdir(parents=True, exist_ok=True)

        pages: List[Dict[str, Any]] = []
        relationships: List[Dict[str, Any]] = []

        # 1. Check if provider has explicit in-memory pages and relationships
        if provider is not None:
            if hasattr(provider, "pages") and isinstance(provider.pages, dict):
                pages = list(provider.pages.values())
            elif hasattr(provider, "pages") and isinstance(provider.pages, list):
                pages = list(provider.pages)
            if hasattr(provider, "relationships") and isinstance(provider.relationships, list):
                relationships = list(provider.relationships)

            # 2. If provider is an MCP client (e.g. GbrainTelecomBrainProvider), harvest via MCP ops
            if not pages and hasattr(provider, "_call"):
                try:
                    offset = 0
                    limit = 100
                    while True:
                        batch = provider._call("list_pages", {"offset": offset, "limit": limit})
                        if not batch or not isinstance(batch, list):
                            break
                        pages.extend(batch)
                        if len(batch) < limit:
                            break
                        offset += len(batch)

                    for p in pages:
                        slug = p.get("slug")
                        if slug:
                            try:
                                links = provider._call("get_links", {"slug": slug}) or []
                                if isinstance(links, list):
                                    for link in links:
                                        norm_link = dict(link)
                                        if "from_slug" in norm_link and "source" not in norm_link:
                                            norm_link["source"] = norm_link["from_slug"]
                                        if "to_slug" in norm_link and "target" not in norm_link:
                                            norm_link["target"] = norm_link["to_slug"]
                                        relationships.append(norm_link)
                            except Exception as link_err:
                                logger.debug(f"Failed to get_links for {slug}: {link_err}")
                except Exception as mcp_err:
                    logger.debug(f"MCP snapshot harvesting failed or incomplete: {mcp_err}")

        # 3. If no pages gathered, fall back to authoritative reference topology ingestor
        if not pages:
            try:
                from .topology_ingestor import ingest_reference_topology
                candidate_paths = [
                    Path(__file__).parents[1] / "simulator" / "operator_model" / "reference_synthetic_network.yaml",
                    Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/operator_model/reference_synthetic_network.yaml"),
                    Path.cwd() / "services/agents/src/engine_stack/engines/telecom_brain/simulator/operator_model/reference_synthetic_network.yaml",
                ]
                ref_path = None
                for cp in candidate_paths:
                    if cp.exists():
                        ref_path = cp.resolve()
                        break

                if ref_path:
                    ingested = ingest_reference_topology(ref_path, version_label=version)
                    pages = ingested.get("pages", [])
                    relationships = ingested.get("relationships", [])
            except Exception as topo_err:
                logger.warning(f"Fallback to reference topology ingestion failed: {topo_err}")

        # Strictly enforce safety boundary: reject hidden evaluator secrets
        reject_truth(pages)
        reject_truth(relationships)

        payload = {
            "brain": "telecombrain",
            "snapshot_version": version,
            "pages": pages,
            "relationships": relationships,
        }

        raw = json.dumps(payload, indent=2).encode("utf-8")
        target.write_bytes(raw)

        return target, {
            "target": str(target),
            "version": version,
            "pages": len(pages),
            "relationships": len(relationships),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }

    def restore_snapshot(
        self,
        snapshot_path: str | Path,
        *,
        mcp_url: Optional[str] = None,
        mcp_token: Optional[str] = None,
        set_as_active: bool = True,
        clean: bool = True,
    ) -> Dict[str, Any]:
        """Restores an operational snapshot into gbrain (live MCP/CLI) and FikraCore active runtime."""
        resolved = self.resolve_snapshot_path(snapshot_path)
        raw = resolved.read_bytes()
        data = json.loads(raw)
        reject_truth(data)

        pages = data.get("pages", [])
        relationships = data.get("relationships", [])
        version = data.get("snapshot_version", resolved.stem)

        mcp_success_pages = 0
        mcp_success_links = 0
        mcp_cleaned_pages = 0
        live_mcp_used = False

        if not mcp_token:
            try:
                from storyteller.knowledge.gbrain_client import _env_value
                mcp_token = _env_value("GBRAIN_MCP_TOKEN")
            except Exception:
                pass
            if not mcp_token:
                mcp_token = "gbrain_55cd2909625c9094a70cb84d7bf9422a40927974993ed95501d089cbff005c34"

        # 1. Attempt restore to live gbrain via MCP if reachable
        try:
            from .knowledge import GbrainTelecomBrainProvider
            provider = GbrainTelecomBrainProvider(url=mcp_url, token=mcp_token)
            if hasattr(provider, "_call"):
                live_mcp_used = True

                # Step 1A: Clean obsolete pages if requested
                if clean and "list_pages" in provider.contracts and "delete_page" in provider.contracts:
                    try:
                        existing_slugs = set()
                        offset = 0
                        limit = 100
                        while True:
                            batch = provider._call("list_pages", {"offset": offset, "limit": limit})
                            if not batch or not isinstance(batch, list):
                                break
                            for item in batch:
                                s = item.get("slug")
                                if s:
                                    existing_slugs.add(s)
                            if len(batch) < limit:
                                break
                            offset += len(batch)

                        target_slugs = {p.get("slug") for p in pages if p.get("slug")}
                        obsolete_slugs = existing_slugs - target_slugs
                        for obs in obsolete_slugs:
                            try:
                                provider._call("delete_page", {"slug": obs})
                                mcp_cleaned_pages += 1
                            except Exception as del_err:
                                logger.debug(f"Failed to delete obsolete page {obs}: {del_err}")
                    except Exception as clean_err:
                        logger.warning(f"Snapshot cleanup phase encountered error: {clean_err}")

                # Step 1B: Upsert all pages with proper markdown + YAML frontmatter
                import yaml
                for p in pages:
                    slug = p.get("slug")
                    if not slug:
                        continue

                    # Compile frontmatter
                    fm = dict(p.get("frontmatter") or {})
                    for field in ["title", "type", "domain", "plane", "sub_cluster", "tmforum_layer"]:
                        if p.get(field) is not None and field not in fm:
                            fm[field] = p[field]

                    raw_content = p.get("compiled_truth") or p.get("content") or f"# {p.get('title', slug)}\n\nRestored from snapshot {version}"
                    if raw_content.startswith("---"):
                        content = raw_content
                    else:
                        fm_str = yaml.dump(fm, sort_keys=False).strip()
                        content = f"---\n{fm_str}\n---\n\n{raw_content}"

                    args = {
                        "slug": slug,
                        "content": content,
                    }
                    try:
                        provider._call("put_page", args)
                        mcp_success_pages += 1
                    except Exception as err:
                        logger.warning(f"Failed to put_page {slug}: {err}")

                # Step 1C: Link topology relationships
                for r in relationships:
                    from_slug = str(r.get("source") or r.get("from_slug") or "").strip().lower()
                    to_slug = str(r.get("target") or r.get("to_slug") or "").strip().lower()
                    l_type = r.get("link_type", "depends-on")
                    if from_slug and to_slug:
                        try:
                            provider._call("add_link", {"from": from_slug, "to": to_slug, "link_type": l_type})
                            mcp_success_links += 1
                        except Exception as err:
                            logger.warning(f"Failed to add_link {from_slug} -> {to_slug}: {err}")
        except Exception as e:
            logger.debug(f"Live gbrain restore skipped/failed: {e}")
            live_mcp_used = False

        # 2. Update active runtime snapshot so downstream pipelines immediately reflect it
        active_target = self.snapshots_dir / "gbrain-snapshot-active.json"
        if set_as_active:
            try:
                self.snapshots_dir.mkdir(parents=True, exist_ok=True)
                active_target.write_bytes(raw)
            except Exception as e:
                logger.debug(f"Failed to set active snapshot: {e}")

        return {
            "status": "success",
            "snapshot_path": str(resolved),
            "filename": resolved.name,
            "version": version,
            "total_pages": len(pages),
            "total_relationships": len(relationships),
            "live_mcp_restored": live_mcp_used,
            "mcp_cleaned_pages": mcp_cleaned_pages,
            "mcp_restored_pages": mcp_success_pages,
            "mcp_restored_links": mcp_success_links,
            "active_runtime_snapshot": str(active_target) if set_as_active else None,
        }


default_snapshot_manager = SnapshotManager()
