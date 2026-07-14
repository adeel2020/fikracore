from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

from .base import BaseSecOpsAgent, SecOpsFinding

logger = logging.getLogger("secops.policy_enforcer")

REQUIRED_LABELS = {
    "app.kubernetes.io/name": "Application name",
    "app.kubernetes.io/part-of": "Parent application",
}

REQUIRED_PROBES = {"livenessProbe", "readinessProbe"}

FORBIDDEN_CAPABILITIES = {"SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE", "SYS_MODULE", "ALL"}


class PolicyEnforcer(BaseSecOpsAgent):
    def __init__(self):
        super().__init__(name="policy-enforcer", schedule="0 */12 * * *")
        self.repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent

    async def run(self) -> dict:
        logger.info("[PolicyEnforcer] Enforcing cluster policies...")
        self._enforce_label_policy()
        self._enforce_container_policy()
        self._enforce_network_policy()
        self._enforce_rbac_policy()

        logger.info(
            "[PolicyEnforcer] Done. Found %d violations.",
            len(self.findings),
        )
        self.print_report()
        return self.report()

    def _enforce_label_policy(self) -> None:
        for manifest in (self.repo_root / "deploy").rglob("*.yaml"):
            if ".git" in str(manifest) or "__pycache__" in str(manifest):
                continue
            try:
                import yaml
                with open(manifest) as f:
                    for doc in yaml.safe_load_all(f):
                        if doc is None:
                            continue
                        kind = doc.get("kind", "Unknown")
                        labels = doc.get("metadata", {}).get("labels", {})
                        if kind in {"Namespace", "CustomResourceDefinition"}:
                            continue
                        for req_label, desc in REQUIRED_LABELS.items():
                            if req_label not in labels:
                                self.add_finding(SecOpsFinding(
                                    severity="medium",
                                    category="label_violation",
                                    title=f"Missing required label: {req_label}",
                                    description=f"{desc} — required by policy",
                                    resource=f"{kind}/{doc['metadata']['name']}",
                                    recommendation=f"Add {req_label} to metadata.labels.",
                                    iso_control="A.5.1",
                                ))
            except Exception:
                continue

    def _enforce_container_policy(self) -> None:
        for manifest in (self.repo_root / "deploy").rglob("*.yaml"):
            if ".git" in str(manifest) or "__pycache__" in str(manifest):
                continue
            try:
                import yaml
                with open(manifest) as f:
                    for doc in yaml.safe_load_all(f):
                        if doc is None:
                            continue
                        kind = doc.get("kind", "")
                        if kind not in {"Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"}:
                            continue
                        template = doc.get("spec", {}).get("template", {})
                        pod_spec = template.get("spec", {})
                        containers = pod_spec.get("containers", [])

                        pod_labels = template.get("metadata", {}).get("labels", {})
                        for req_label in REQUIRED_LABELS:
                            if req_label not in pod_labels:
                                self.add_finding(SecOpsFinding(
                                    severity="medium",
                                    category="pod_label_violation",
                                    title=f"Pod template missing label: {req_label}",
                                    resource=f"{kind}/{doc['metadata']['name']}",
                                    recommendation=f"Add {req_label} to spec.template.metadata.labels.",
                                    iso_control="A.5.1",
                                ))

                        for c in containers:
                            self._check_container_security(c, kind, doc["metadata"]["name"])
                            has_probes = {p for p in REQUIRED_PROBES if p in c}
                            missing_probes = REQUIRED_PROBES - has_probes
                            if missing_probes:
                                self.add_finding(SecOpsFinding(
                                    severity="medium",
                                    category="missing_probe",
                                    title=f"Container '{c['name']}' missing: {', '.join(missing_probes)}",
                                    resource=f"{kind}/{doc['metadata']['name']}",
                                    recommendation="Add health probes for Kubernetes auto-recovery.",
                                    iso_control="A.12.1",
                                ))

                        security_context = pod_spec.get("securityContext", {})
                        if not security_context.get("runAsNonRoot"):
                            self.add_finding(SecOpsFinding(
                                severity="high",
                                category="pod_security",
                                title=f"Pod missing runAsNonRoot: true",
                                resource=f"{kind}/{doc['metadata']['name']}",
                                recommendation="Set securityContext.runAsNonRoot: true.",
                                iso_control="A.8.29",
                            ))
            except Exception:
                continue

    def _check_container_security(self, c: dict, kind: str, name: str) -> None:
        sec_ctx = c.get("securityContext", {})
        if sec_ctx.get("privileged"):
            self.add_finding(SecOpsFinding(
                severity="critical",
                category="privileged_container",
                title=f"Container '{c['name']}' is privileged",
                resource=f"{kind}/{name}",
                recommendation="Remove privileged: true from container securityContext.",
                iso_control="A.8.29",
            ))
        caps = sec_ctx.get("capabilities", {}).get("add", [])
        for cap in caps:
            if cap in FORBIDDEN_CAPABILITIES:
                self.add_finding(SecOpsFinding(
                    severity="high",
                    category="forbidden_capability",
                    title=f"Container '{c['name']}' adds forbidden capability: {cap}",
                    resource=f"{kind}/{name}",
                    recommendation=f"Remove {cap} from capabilities.add.",
                    iso_control="A.8.29",
                ))
        if c.get("image") and ":latest" in c["image"]:
            self.add_finding(SecOpsFinding(
                severity="medium",
                category="latest_tag",
                title=f"Container '{c['name']}' uses 'latest' tag",
                resource=f"{kind}/{name}",
                recommendation="Pin image to a specific version.",
                iso_control="A.8.29",
            ))

    def _enforce_network_policy(self) -> None:
        np_dir = self.repo_root / "deploy" / "network-policies"
        if not np_dir.exists():
            self.add_finding(SecOpsFinding(
                severity="critical",
                category="network_policy_missing",
                title="No network policies directory",
                recommendation="Create deploy/network-policies/ with tiered policies.",
                iso_control="A.14.1",
            ))
            return

        has_default_deny = False
        for f in np_dir.iterdir():
            if f.suffix not in {".yaml", ".yml"}:
                continue
            try:
                import yaml
                with open(f) as fh:
                    for doc in yaml.safe_load_all(fh):
                        if doc is None:
                            continue
                        if doc.get("kind") == "NetworkPolicy":
                            policy_types = doc.get("spec", {}).get("policyTypes", [])
                            pod_selector = doc.get("spec", {}).get("podSelector", {})
                            if "Ingress" in policy_types and "Egress" in policy_types and pod_selector == {}:
                                has_default_deny = True
            except Exception:
                continue

        if not has_default_deny:
            self.add_finding(SecOpsFinding(
                severity="critical",
                category="missing_default_deny",
                title="No default-deny-all network policy found",
                recommendation="Create a NetworkPolicy with podSelector: {} and policyTypes: [Ingress, Egress].",
                iso_control="A.14.1",
            ))

    def _enforce_rbac_policy(self) -> None:
        rbac_dir = self.repo_root / "deploy" / "rbac" / "kubernetes"
        if not rbac_dir.exists():
            self.add_finding(SecOpsFinding(
                severity="critical",
                category="rbac_missing",
                title="No Kubernetes RBAC manifests found",
                recommendation="Create deploy/rbac/kubernetes/ with least-privilege roles.",
                iso_control="A.5.15",
            ))
            return

        for f in rbac_dir.iterdir():
            if f.suffix not in {".yaml", ".yml"}:
                continue
            content = f.read_text(encoding="utf-8", errors="ignore")

            if "rules:" in content:
                import yaml
                with open(f) as fh:
                    for doc in yaml.safe_load_all(fh):
                        if doc is None:
                            continue
                        if doc.get("kind") in {"Role", "ClusterRole"}:
                            for rule in doc.get("rules", []):
                                resources = [r.lower() for r in rule.get("resources", [])]
                                verbs = [v.lower() for v in rule.get("verbs", [])]

                                if "secrets" in resources and "get" in verbs:
                                    api_groups = rule.get("apiGroups", [])
                                    self.add_finding(SecOpsFinding(
                                        severity="high",
                                        category="rbac_secrets_access",
                                        title=f"Role '{doc['metadata']['name']}' can read secrets",
                                        description=f"Resource: {', '.join(resources)}, Verbs: {', '.join(verbs)}",
                                        resource=str(f.name),
                                        recommendation="Review if secret read access is strictly necessary for this role. Consider narrowing scope.",
                                        iso_control="A.5.15",
                                    ))

                                if "*" in verbs or "create" in verbs or "update" in verbs:
                                    if "*" in resources:
                                        self.add_finding(SecOpsFinding(
                                            severity="high",
                                            category="rbac_overly_broad",
                                            title=f"Role '{doc['metadata']['name']}' has broad permissions",
                                            description=f"Resources: {', '.join(resources)}, Verbs: {', '.join(verbs)}",
                                            resource=str(f.name),
                                            recommendation="Restrict to specific resources and verbs needed.",
                                            iso_control="A.5.15",
                                        ))
