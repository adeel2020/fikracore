"""SQLite registry for discoverable incident lifecycle state and audit lineage."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .namespaces import canonicalize_incident_slug, incident_aliases


VALID_ACTIONS = {"open", "acknowledge", "assign", "suppress", "resolve", "reopen", "merge", "split"}


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
        if self.path == "/tmp/kagent-incident-registry.db":
            self.ensure_seeded()

    def ensure_seeded(self) -> None:
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
            if count == 0:
                self.upsert({
                    "incident_id": "mobile-core/incidents/amf-overload-2026-08-09",
                    "tenant_id": "tenant-a",
                    "status": "open",
                    "scope": "intra-domain",
                    "score": 88,
                    "domains": ["5g-core"],
                    "services": ["ue-registration"],
                    "owner": "mark-commander",
                })
                self.upsert({
                    "incident_id": "mobile-core/incidents/sgi-throughput-drop",
                    "tenant_id": "tenant-a",
                    "status": "investigating",
                    "scope": "cross-domain",
                    "score": 74,
                    "domains": ["5g-core", "transport"],
                    "services": ["sgi-throughput"],
                    "owner": "mark-commander",
                })
                self.upsert({
                    "incident_id": "mobile-core/incidents/volte-cssr-degradation",
                    "tenant_id": "tenant-a",
                    "status": "mitigated",
                    "scope": "intra-domain",
                    "score": 65,
                    "domains": ["ims"],
                    "services": ["volte-call-setup"],
                    "owner": "mark-commander",
                })

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
        query += " ORDER BY updated_at DESC LIMIT ?"; args.append(min(limit, 100))
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
