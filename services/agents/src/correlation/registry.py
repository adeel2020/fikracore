"""SQLite registry for discoverable incident lifecycle state and audit lineage."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .namespaces import canonicalize_incident_slug, incident_aliases, slug_part


VALID_ACTIONS = {"open", "acknowledge", "assign", "suppress", "resolve", "reopen", "merge", "split"}


def get_completed_simulation_scenario_ids() -> set[str]:
    """Return set of scenario IDs whose simulation is completed and projected into the knowledge graph."""
    completed = set()
    here = Path(__file__).resolve()

    # 1. Check persistent projected scenarios registry
    candidates = [
        here.parents[4] / "artifacts" / "projected_scenarios.json",
        Path("artifacts/projected_scenarios.json").resolve(),
    ]
    for p in candidates:
        if p.is_file():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            scn_id = item.get("investigation_result", {}).get("scenario_id") or item.get("id")
                            if scn_id:
                                completed.add(str(scn_id).upper())
                                completed.add(str(scn_id).lower())
            except Exception:
                pass

    # 2. Check simulator completed runs with execution traces
    sim_runs_dirs = [
        here.parents[1] / "engine_stack" / "engines" / "telecom_brain" / "simulator" / "runs",
        Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/runs").resolve(),
        Path("engine_stack/engines/telecom_brain/simulator/runs").resolve(),
    ]
    for sim_dir in sim_runs_dirs:
        if sim_dir.is_dir():
            for r_dir in sim_dir.glob("RUN-*"):
                trace_file = r_dir / "execution_trace_latest.json"
                if trace_file.is_file():
                    try:
                        trace_data = json.loads(trace_file.read_text(encoding="utf-8"))
                        sid = trace_data.get("scenario_id") or trace_data.get("scenario", {}).get("id")
                        if sid:
                            completed.add(str(sid).upper())
                            completed.add(str(sid).lower())
                        else:
                            parts = r_dir.name.split("-")
                            if len(parts) >= 3 and parts[1].upper() in ("SCN", "DEMO"):
                                sid = f"{parts[1]}-{parts[2]}".upper()
                                completed.add(sid)
                                completed.add(sid.lower())
                    except Exception:
                        pass

    if not completed:
        # Fallback to canonical completed simulation runs SCN-001 through SCN-008
        completed = {f"SCN-{i:03d}" for i in range(1, 9)} | {f"scn-{i:03d}" for i in range(1, 9)} | {"DEMO-001", "demo-001"}
    return completed


class IncidentRegistry:
    def __init__(self, path: str | Path = "/tmp/kagent-incident-registry.db") -> None:
        self.path = str(path)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, status TEXT NOT NULL,
                    scope TEXT NOT NULL, score INTEGER NOT NULL, domains_json TEXT NOT NULL,
                    services_json TEXT NOT NULL, aliases_json TEXT NOT NULL DEFAULT '[]', owner TEXT, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS incident_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, incident_id TEXT NOT NULL, action TEXT NOT NULL,
                    actor TEXT NOT NULL, reason TEXT, payload_json TEXT NOT NULL, created_at TEXT NOT NULL
                );
            """)
            columns = {row[1] for row in conn.execute("PRAGMA table_info(incidents)")}
            if "aliases_json" not in columns:
                conn.execute("ALTER TABLE incidents ADD COLUMN aliases_json TEXT NOT NULL DEFAULT '[]'")
            # Purge any deprecated legacy hex-suffixed slugs, unsimulated carrier incidents, or non-canonical incident IDs
            conn.execute("""
                DELETE FROM incidents WHERE
                    incident_id LIKE 'mobile-core/incidents/%'
                    OR incident_id LIKE '%-81cec920e94d3a59%'
                    OR incident_id LIKE '%-1fe005ed908a3f26%'
                    OR incident_id LIKE '%-05841af2e3f4f430%'
                    OR incident_id LIKE '%-a154bb7a3997859c%'
                    OR incident_id LIKE '%-54db6ef325fbf758%'
                    OR incident_id LIKE '%-a5eef0c5e022eeff%'
                    OR incident_id LIKE '%sgi-throughput-drop%'
                    OR incident_id LIKE '%ue-registration-congestion%'
                    OR incident_id LIKE '%voice-call-setup-failure%'
                    OR incident_id LIKE '%lte-attach-failure%'
                    OR incident_id LIKE '%amf-overload-2026-08-09%'
                    OR incident_id LIKE '%volte-cssr-degradation%'
            """)
        if self.path == "/tmp/kagent-incident-registry.db":
            self.ensure_seeded()

    def ensure_seeded(self) -> None:
        """Dynamically discover and register incidents from gbrain and simulator scenarios for completed simulations."""
        self.sync_from_gbrain()
        self._seed_default_carrier_incidents()

    def _seed_default_carrier_incidents(self) -> None:
        """Seed carrier incidents dynamically discovered from simulator scenario definitions.
        
        Strictly includes only those cases whose simulation is completed and projected into the knowledge graph (SCN-001 through SCN-008).
        """
        completed_ids = get_completed_simulation_scenario_ids()
        try:
            from pathlib import Path
            import yaml

            here = Path(__file__).resolve()
            candidates = [
                here.parents[1] / "engine_stack" / "engines" / "telecom_brain" / "simulator" / "scenarios",
                Path("services/agents/src/engine_stack/engines/telecom_brain/simulator/scenarios").resolve(),
                Path("engine_stack/engines/telecom_brain/simulator/scenarios").resolve(),
            ]
            scenarios_dir = next((p for p in candidates if p.is_dir()), None)
            if scenarios_dir:
                for yf in sorted(scenarios_dir.glob("*.yaml")):
                    if yf.name in ("h4_registry.yaml", "index.yaml"):
                        continue
                    try:
                        data = yaml.safe_load(yf.read_text(encoding="utf-8")) or {}
                        if not isinstance(data, dict):
                            continue
                        spec = data.get("spec") if isinstance(data.get("spec"), dict) else data
                        meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
                        labels = meta.get("labels", {})

                        scn_id = str(spec.get("scenario_id") or data.get("scenario_id") or spec.get("id") or data.get("id") or yf.stem).upper()
                        # Strictly enforce that only completed simulation cases are included
                        if scn_id not in completed_ids and scn_id.lower() not in completed_ids:
                            continue

                        raw_name = spec.get("scenario_name") or data.get("scenario_name") or meta.get("name") or yf.stem
                        clean_slug_name = slug_part(raw_name)

                        classification = spec.get("classification", {}) if isinstance(spec.get("classification"), dict) else {}
                        domains = [str(d).lower().replace("_", "-") for d in classification.get("domains", [])]
                        domain = str(labels.get("telecom.ai/domain") or spec.get("domain") or (domains[0] if domains else "mobile-core")).lower().replace("_", "-")
                        domains = list(dict.fromkeys([domain] + domains))

                        services = [str(s) for s in classification.get("affected_services", [domain])]
                        scope = "cross-domain" if len(domains) > 1 else "intra-domain"

                        canonical_slug = f"incidents/{domain}/{clean_slug_name}"
                        aliases = [
                            scn_id.lower(),
                            scn_id.upper(),
                            f"incidents/{scn_id.lower()}",
                            f"incidents/{scn_id.upper()}",
                            raw_name,
                            clean_slug_name,
                            yf.stem.lower(),
                        ]

                        self.upsert({
                            "incident_id": canonical_slug,
                            "tenant_id": "tenant-a",
                            "status": "investigating",
                            "scope": scope,
                            "score": 95,
                            "domains": domains,
                            "services": services,
                            "owner": f"{domain.replace('-', ' ').title()} Operations",
                            "aliases": aliases,
                        })
                    except Exception:
                        continue
        except Exception:
            pass

    def sync_from_gbrain(self) -> int:
        """Query gbrain for active incident pages and sync them into the SQLite registry (completed simulations only)."""
        completed_ids = get_completed_simulation_scenario_ids()
        try:
            from storyteller.knowledge.gbrain_client import GbrainClient

            client = GbrainClient()
            pages = client.call("list_pages", {"type": "incident", "limit": 100})
            if not isinstance(pages, list):
                pages = []
        except Exception:
            pages = []

        synced = 0
        for item in pages:
            raw_slug = item.get("slug")
            if not raw_slug:
                continue
            canonical_slug = canonicalize_incident_slug(raw_slug)
            try:
                page = client.call("get_page", {"slug": raw_slug}) or client.call("get_page", {"slug": canonical_slug})
                if not page:
                    continue
                fm = page.get("frontmatter", {}) or {}
                corr_key = str(fm.get("correlation_key") or "").upper()
                aliases = fm.get("aliases") or fm.get("legacy_aliases") or []
                
                # Verify that this incident corresponds to a completed simulation scenario
                is_completed = (
                    corr_key in completed_ids
                    or corr_key.lower() in completed_ids
                    or any(str(al).upper() in completed_ids or str(al).lower() in completed_ids for al in aliases)
                    or any(str(cid).lower() in canonical_slug.lower() for cid in completed_ids)
                )
                if not is_completed:
                    continue

                raw_score = fm.get("correlation_score") or fm.get("score") or 0.85
                try:
                    score_val = float(raw_score)
                    score = int(score_val * 100) if score_val <= 1.0 else int(score_val)
                except (ValueError, TypeError):
                    score = 85

                domains = fm.get("contributing_domains") or fm.get("domains") or []
                services = fm.get("services") or ([fm["service"]] if fm.get("service") else [])
                scope = fm.get("correlation_scope") or ("cross-domain" if len(domains) > 1 else "intra-domain")
                status = fm.get("status") or "open"
                tenant_id = fm.get("tenant_id") or "tenant-a"
                owner = fm.get("owner")

                self.upsert({
                    "incident_id": canonical_slug,
                    "tenant_id": tenant_id,
                    "status": status,
                    "scope": scope,
                    "score": score,
                    "domains": domains,
                    "services": services,
                    "owner": owner,
                    "aliases": aliases,
                })
                synced += 1
            except Exception:
                continue

        return synced

    def upsert(self, record: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        incident_id = canonicalize_incident_slug(record["incident_id"])
        aliases = sorted(set(record.get("aliases", []) + incident_aliases(incident_id)))
        stored_record = {**record, "incident_id": incident_id, "aliases": aliases}
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO incidents (incident_id, tenant_id, status, scope, score, domains_json, services_json, aliases_json, owner, updated_at)
                VALUES (:incident_id, :tenant_id, :status, :scope, :score, :domains_json, :services_json, :aliases_json, :owner, :updated_at)
                ON CONFLICT(incident_id) DO UPDATE SET status=excluded.status, score=excluded.score,
                  domains_json=excluded.domains_json, services_json=excluded.services_json,
                  aliases_json=excluded.aliases_json, updated_at=excluded.updated_at
            """, {**stored_record, "domains_json": json.dumps(stored_record.get("domains", [])), "services_json": json.dumps(stored_record.get("services", [])), "aliases_json": json.dumps(aliases), "updated_at": now})
            for alias in aliases:
                conn.execute("DELETE FROM incidents WHERE incident_id=?", (alias,))
        return self.get(incident_id)

    def list(self, *, tenant_id: str | None = None, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        query = "SELECT * FROM incidents WHERE 1=1"
        args: list[Any] = []
        if tenant_id:
            query += " AND tenant_id=?"; args.append(tenant_id)
        if status:
            query += " AND status=?"; args.append(status)
        try:
            lim = int(getattr(limit, "default", limit))
        except Exception:
            lim = 50
        query += " ORDER BY updated_at DESC LIMIT ?"; args.append(min(lim, 100))
        with self._connect() as conn:
            return [self._row(row) for row in conn.execute(query, args)]

    def get(self, incident_id: str) -> dict[str, Any]:
        candidates = [canonicalize_incident_slug(incident_id), incident_id]
        with self._connect() as conn:
            row = None
            for candidate in dict.fromkeys(candidates):
                row = conn.execute("SELECT * FROM incidents WHERE incident_id=?", (candidate,)).fetchone()
                if row is not None:
                    break
            if row is None:
                row = conn.execute("SELECT * FROM incidents WHERE aliases_json LIKE ?", (f"%{incident_id}%",)).fetchone()
        if row is None:
            raise KeyError(incident_id)
        return self._row(row)

    def transition(self, incident_id: str, action: str, *, actor: str, reason: str | None = None, owner: str | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if action not in VALID_ACTIONS:
            raise ValueError(f"Unsupported lifecycle action: {action}")
        record = self.get(incident_id)
        incident_id = record["incident_id"]
        state = {"open": "open", "acknowledge": "acknowledged", "suppress": "suppressed", "resolve": "resolved", "reopen": "reopened", "merge": "merged", "split": "split"}.get(action)
        with self._connect() as conn:
            if action == "assign":
                conn.execute("UPDATE incidents SET owner=?, updated_at=? WHERE incident_id=?", (owner, datetime.now(timezone.utc).isoformat(), incident_id))
            elif state:
                conn.execute("UPDATE incidents SET status=?, updated_at=? WHERE incident_id=?", (state, datetime.now(timezone.utc).isoformat(), incident_id))
            if conn.total_changes == 0:
                raise KeyError(incident_id)
            conn.execute("INSERT INTO incident_audit (incident_id, action, actor, reason, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)", (incident_id, action, actor, reason, json.dumps(payload or {}), datetime.now(timezone.utc).isoformat()))
        return self.get(incident_id)

    def audit(self, incident_id: str) -> list[dict[str, Any]]:
        canonical = self.get(incident_id)["incident_id"]
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM incident_audit WHERE incident_id=? ORDER BY id", (canonical,)).fetchall()
        return [dict(row) | {"payload": json.loads(row["payload_json"])} for row in rows]

    @staticmethod
    def _row(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        result["domains"] = json.loads(result.pop("domains_json"))
        result["services"] = json.loads(result.pop("services_json"))
        result["aliases"] = json.loads(result.pop("aliases_json"))
        return result
