"""Playbook and runbook recommendation service."""

from __future__ import annotations

from pathlib import Path

from ..engine_context import TelecomContext
from ..models import FCAPSClassification, RecommendedAction, ServiceProcedure, TelecomRequest, TelecomResult, TelecomTrace


class PlaybookRunbookService:
    id = "playbook_runbook"

    DEFAULT_ASSETS = {
        "lte-attach": {
            "playbook": "assets/mobile-core/playbooks/lte-attach-failure-triage",
            "runbooks": [
                "assets/mobile-core/runbooks/check-mme-health",
                "assets/mobile-core/runbooks/check-hss-diameter-peer",
                "assets/mobile-core/runbooks/check-s1-mme-connectivity",
            ],
        },
        "registration": {
            "playbook": "assets/mobile-core/playbooks/ue-registration-failure-triage",
            "runbooks": [
                "assets/mobile-core/runbooks/check-amf-health",
                "assets/mobile-core/runbooks/check-ausf-udm-auth",
            ],
        },
        "volte": {
            "playbook": "assets/mobile-core/playbooks/volte-cssr-triage",
            "runbooks": [
                "assets/mobile-core/runbooks/check-ims-registration",
                "assets/mobile-core/runbooks/check-sbc-health",
            ],
        },
    }

    async def can_handle(self, request: TelecomRequest) -> float:
        query = request.query.lower()
        score = 0.0
        if any(term in query for term in ("playbook", "runbook", "asset", "procedure")):
            score += 0.8
        if any(term in query for term in self.DEFAULT_ASSETS):
            score += 0.25
        if request.service_procedure_refs:
            score += 0.2
        return min(score, 1.0)

    async def handle(self, request: TelecomRequest, context: TelecomContext) -> TelecomResult:
        key = self._resolve_key(request)
        assets = self.DEFAULT_ASSETS.get(key or "")
        present_assets = self._present_assets(assets) if assets else None
        actions = []
        if present_assets:
            actions.append(RecommendedAction(action_type="playbook", description=present_assets["playbook"], requires_approval=False))
            actions.extend(RecommendedAction(action_type="runbook", description=runbook, requires_approval=True) for runbook in present_assets["runbooks"])
            text = self._format(key, present_assets)
        else:
            actions.append(RecommendedAction(action_type="asset gap", description="suggest missing playbook/runbook for reviewed learning", requires_approval=False))
            text = self._format_gap(key, assets)
        return TelecomResult(
            text=text,
            spoken_response=f"Found {len(actions)} approved playbook or runbook assets." if present_assets else "I do not see an approved runbook or playbook asset in this repo for that request. I have marked it as an asset gap.",
            service_id=self.id,
            trace=TelecomTrace(selected_service=self.id, provenance=["capability_registry.skills"], warnings=[] if present_assets else ["No physical playbook/runbook asset was found before recommendation."]),
            recommended_actions=actions,
            fcaps=[FCAPSClassification.FAULT, FCAPSClassification.PERFORMANCE],
            data={"asset_key": key, "assets": present_assets, "configured_assets": assets},
        )

    @classmethod
    def _resolve_key(cls, request: TelecomRequest) -> str | None:
        query = request.query.lower()
        for key in cls.DEFAULT_ASSETS:
            if key in query:
                return key
        for proc in request.service_procedure_refs:
            for key in cls.DEFAULT_ASSETS:
                if key in proc.id.lower() or key in proc.name.lower():
                    return key
        return None

    @staticmethod
    def _format(key: str | None, assets: dict) -> str:
        lines = ["**Playbook/Runbook Assets**", f"- Playbook: {assets['playbook']}"]
        for runbook in assets["runbooks"]:
            lines.append(f"- Runbook: {runbook}")
        return "\n".join(lines)

    @classmethod
    def _format_gap(cls, key: str | None, assets: dict | None) -> str:
        lines = ["**Playbook/Runbook Assets**"]
        if key and assets:
            lines.append(f"- Requested procedure: {key}")
            lines.append("- Approved runbook/playbook files: not present in this repo.")
            lines.append("- Catalog hints exist, but Mark will not treat them as executable runbooks until files are added and reviewed.")
        else:
            lines.append("- No matching approved operational playbook or runbook was found for this request.")
        lines.append("- Recommended next step: create a reviewed runbook/playbook asset before execution.")
        return "\n".join(lines)

    @classmethod
    def _present_assets(cls, assets: dict | None) -> dict | None:
        if not assets:
            return None
        playbook = assets.get("playbook")
        runbooks = assets.get("runbooks") or []
        if not isinstance(playbook, str):
            return None
        present_playbook = cls._resolve_asset(playbook)
        present_runbooks = [resolved for item in runbooks if isinstance(item, str) and (resolved := cls._resolve_asset(item))]
        if present_playbook or present_runbooks:
            return {
                "playbook": present_playbook or playbook,
                "runbooks": present_runbooks,
            }
        return None

    @staticmethod
    def _resolve_asset(asset_id: str) -> str | None:
        root = PlaybookRunbookService._repo_root()
        candidates = [
            root / asset_id,
            root / f"{asset_id}.md",
            root / f"{asset_id}.yaml",
            root / f"{asset_id}.yml",
            root / f"{asset_id}.json",
        ]
        for path in candidates:
            if path.exists() and path.is_file():
                return str(path.relative_to(root))
        return None

    @staticmethod
    def _repo_root() -> Path:
        cur = Path(__file__).resolve()
        for parent in cur.parents:
            if (parent / "docs").exists() and (parent / "services").exists():
                return parent
        return Path.cwd()
