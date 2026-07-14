from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base import BaseSecOpsAgent, SecOpsFinding

logger = logging.getLogger("secops.compliance_auditor")

ISO_9001_CONTROLS: dict[str, dict[str, str]] = {
    "7.1.4": {"title": "Environment for operation of processes", "evidence": "deploy/iso/"},
    "8.4": {"title": "Control of externally provided processes", "evidence": "deploy/rbac/application/roles.yaml"},
    "9.1": {"title": "Monitoring and measurement", "evidence": "deploy/iso/9001/kpi-metrics.yaml"},
    "9.2": {"title": "Internal audit", "evidence": "deploy/iso/evidence/"},
    "10.1": {"title": "Nonconformity and corrective action", "evidence": "deploy/iso/evidence/incident-reports/"},
}

ISO_27001_CONTROLS: dict[str, dict[str, str]] = {
    "A.5.1": {"title": "Information security policy", "evidence": "deploy/iso/27001/scope.yaml"},
    "A.5.15": {"title": "Access control", "evidence": "deploy/rbac/"},
    "A.8.2": {"title": "Information classification", "evidence": "deploy/secrets/"},
    "A.8.8": {"title": "Management of technical vulnerabilities", "evidence": "deploy/ci/github-workflows/ci.yaml"},
    "A.8.15": {"title": "Logging", "evidence": "services/agents/src/secops/audit_logger.py"},
    "A.8.16": {"title": "Monitoring", "evidence": "deploy/monitoring/"},
    "A.8.24": {"title": "Use of cryptography", "evidence": "services/gateway/nginx.conf"},
    "A.8.29": {"title": "Security in development and acceptance", "evidence": "services/agents/Dockerfile"},
    "A.8.31": {"title": "Separation of dev, test and production", "evidence": "deploy/network-policies/"},
    "A.12.1": {"title": "Vulnerability management", "evidence": "deploy/kagent/secops/vulnerability-responder.yaml"},
    "A.14.1": {"title": "Secure communications", "evidence": "deploy/network-policies/tier2-nginx-policy.yaml"},
    "A.18.1": {"title": "Compliance with legal and contractual requirements", "evidence": "deploy/iso/27001/risk-assessment.yaml"},
}


class ComplianceAuditor(BaseSecOpsAgent):
    def __init__(self):
        super().__init__(name="compliance-auditor", schedule="0 6 1 * *")
        self.repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent

    async def run(self) -> dict:
        logger.info("[ComplianceAuditor] Starting compliance audit...")
        self._audit_iso_9001()
        self._audit_iso_27001()
        self._audit_network_policies()
        self._audit_rbac()
        self._audit_secrets()

        logger.info(
            "[ComplianceAuditor] Done. Found %d findings.",
            len(self.findings),
        )
        self.print_report()
        return self.report()

    def _check_evidence(self, path_str: str) -> bool:
        full_path = self.repo_root / path_str
        return full_path.exists()

    def _audit_iso_9001(self) -> None:
        logger.info("  Auditing ISO 9001 controls...")
        for ctrl_id, info in ISO_9001_CONTROLS.items():
            present = self._check_evidence(info["evidence"])
            if not present:
                self.add_finding(SecOpsFinding(
                    severity="medium",
                    category="iso_9001_missing_evidence",
                    title=f"ISO 9001 {ctrl_id}: {info['title']} — evidence missing",
                    description=f"Expected evidence at {info['evidence']} not found.",
                    recommendation=f"Create evidence artifact at {info['evidence']} for control {ctrl_id}.",
                    iso_control=ctrl_id,
                ))

    def _audit_iso_27001(self) -> None:
        logger.info("  Auditing ISO 27001 controls...")
        for ctrl_id, info in ISO_27001_CONTROLS.items():
            present = self._check_evidence(info["evidence"])
            if not present:
                self.add_finding(SecOpsFinding(
                    severity="high",
                    category="iso_27001_missing_evidence",
                    title=f"ISO 27001 {ctrl_id}: {info['title']} — evidence missing",
                    description=f"Expected evidence at {info['evidence']} not found.",
                    recommendation=f"Create evidence artifact at {info['evidence']} for control {ctrl_id}.",
                    iso_control=ctrl_id,
                ))

    def _audit_network_policies(self) -> None:
        logger.info("  Auditing network policies...")
        np_dir = self.repo_root / "deploy" / "network-policies"
        if not np_dir.exists():
            self.add_finding(SecOpsFinding(
                severity="critical", category="network_policy",
                title="Network policies directory missing",
                recommendation="Create deploy/network-policies/ with tier-based policies.",
                iso_control="A.14.1",
            ))
            return

        required_policies = [
            "deny-all-namespaces.yaml",
            "tier2-nginx-policy.yaml",
            "tier3-agents-policy.yaml",
            "tier4-db-policy.yaml",
        ]
        for policy in required_policies:
            if not (np_dir / policy).exists():
                self.add_finding(SecOpsFinding(
                    severity="critical", category="network_policy",
                    title=f"Required network policy missing: {policy}",
                    resource=f"deploy/network-policies/{policy}",
                    recommendation=f"Create {policy} to enforce tier-based segmentation.",
                    iso_control="A.14.1",
                ))

    def _audit_rbac(self) -> None:
        logger.info("  Auditing RBAC...")
        rbac_dirs = [
            "deploy/rbac/kubernetes",
            "deploy/rbac/application",
        ]
        for rdir in rbac_dirs:
            if not (self.repo_root / rdir).exists():
                self.add_finding(SecOpsFinding(
                    severity="high", category="rbac",
                    title=f"RBAC directory missing: {rdir}",
                    recommendation=f"Create {rdir} with least-privilege role definitions.",
                    iso_control="A.5.15",
                ))

    def _audit_secrets(self) -> None:
        logger.info("  Auditing secrets...")
        secrets_dir = self.repo_root / "deploy" / "secrets"
        if not secrets_dir.exists():
            self.add_finding(SecOpsFinding(
                severity="critical", category="secrets",
                title="Secrets directory missing",
                recommendation="Create deploy/secrets/ with Kubernetes Secret manifests.",
                iso_control="A.8.2",
            ))
            return

        for secret_file in secrets_dir.iterdir():
            if secret_file.suffix not in {".yaml", ".yml"}:
                continue
            content = secret_file.read_text(encoding="utf-8", errors="ignore")
            if "REPLACE_ME" in content:
                self.add_finding(SecOpsFinding(
                    severity="high", category="secrets_placeholder",
                    title=f"Secret still has placeholder: {secret_file.name}",
                    resource=f"deploy/secrets/{secret_file.name}",
                    recommendation="Replace REPLACE_ME with actual secret values or configure External Secrets Operator.",
                    iso_control="A.8.2",
                ))
