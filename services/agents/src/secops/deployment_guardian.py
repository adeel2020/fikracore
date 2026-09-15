from __future__ import annotations

import json
import logging
import subprocess
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from secops.base import BaseSecOpsAgent, SecOpsFinding

logger = logging.getLogger("secops.deployment_guardian")


class DeploymentGuardian(BaseSecOpsAgent):
    def __init__(self):
        super().__init__(name="deployment-guardian", schedule="*/5 * * * *")
        self.repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        self.argocd_server = os.getenv("ARGOCD_SERVER", "argocd-server.argocd.svc.cluster.local:443")
        self.kubectl_available = False

    async def run(self) -> dict:
        logger.info("[DeploymentGuardian] Monitoring deployments...")
        self._check_kubectl()

        if self.kubectl_available:
            self._check_pod_health()
            self._check_deployment_health()
            self._check_rollout_history()

        self._validate_manifests()

        logger.info(
            "[DeploymentGuardian] Done. Found %d findings.",
            len(self.findings),
        )
        self.print_report()
        return self.report()

    def _check_kubectl(self) -> None:
        try:
            result = subprocess.run(
                ["kubectl", "version", "--client"],
                capture_output=True, text=True, timeout=10,
            )
            self.kubectl_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.kubectl_available = False
        logger.info("  kubectl available: %s", self.kubectl_available)

    def _check_pod_health(self) -> None:
        try:
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", "agents-prod",
                 "--field-selector=status.phase!=Running,status.phase!=Succeeded",
                 "-o", "json"],
                capture_output=True, text=True, timeout=30,
            )
            if result.stdout:
                data = json.loads(result.stdout)
                for pod in data.get("items", []):
                    name = pod["metadata"]["name"]
                    phase = pod["status"]["phase"]
                    self.add_finding(SecOpsFinding(
                        severity="critical" if phase == "Failed" else "high",
                        category="unhealthy_pod",
                        title=f"Pod {name} in phase {phase}",
                        resource=f"agents-prod/{name}",
                        recommendation="Check pod logs and events for failure reason.",
                        iso_control="A.12.1",
                    ))
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            logger.warning("  Pod health check failed: %s", e)

    def _check_deployment_health(self) -> None:
        try:
            result = subprocess.run(
                ["kubectl", "get", "deployments", "-n", "agents-prod",
                 "-o", "json"],
                capture_output=True, text=True, timeout=30,
            )
            if result.stdout:
                data = json.loads(result.stdout)
                for dep in data.get("items", []):
                    name = dep["metadata"]["name"]
                    status = dep.get("status", {})
                    available = status.get("availableReplicas", 0)
                    desired = status.get("replicas", 0)
                    if desired > 0 and available < desired:
                        self.add_finding(SecOpsFinding(
                            severity="critical",
                            category="deployment_unhealthy",
                            title=f"Deployment {name}: {available}/{desired} pods available",
                            resource=f"agents-prod/deploy/{name}",
                            recommendation="Check deployment events and pod status.",
                            iso_control="A.12.1",
                        ))
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            logger.warning("  Deployment health check failed: %s", e)

    def _check_rollout_history(self) -> None:
        result = subprocess.run(
            ["kubectl", "rollout", "history", "deployment",
             "-n", "agents-prod", "--all"],
            capture_output=True, text=True, timeout=30,
        )
        # Log any rollback events
        if "REVISION" in result.stdout:
            revisions = result.stdout.strip().split("\n\n")
            if len(revisions) > 1:
                logger.info("  Rollout history available for %d deployments", len(revisions))

    def _validate_manifests(self) -> None:
        deploy_dir = self.repo_root / "deploy"
        for manifest in deploy_dir.rglob("*.yaml"):
            if ".git" in str(manifest) or "__pycache__" in str(manifest):
                continue
            try:
                import yaml
                with open(manifest) as f:
                    docs = list(yaml.safe_load_all(f))
                for doc in docs:
                    if doc is None:
                        continue
                    kind = doc.get("kind", "Unknown")
                    if not doc.get("apiVersion"):
                        self.add_finding(SecOpsFinding(
                            severity="medium", category="manifest_validation",
                            title=f"Manifest missing apiVersion: {manifest.name}",
                            resource=str(manifest.relative_to(self.repo_root)),
                            recommendation=f"Add apiVersion field to {manifest.name}.",
                            iso_control="A.8.29",
                        ))
                    if kind == "Deployment" or kind == "StatefulSet":
                        containers = (
                            doc.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
                        )
                        for c in containers:
                            if "image" in c and "latest" in c["image"]:
                                self.add_finding(SecOpsFinding(
                                    severity="medium",
                                    category="deployment_risk",
                                    title=f"Container uses 'latest' tag: {c['image']}",
                                    resource=f"{kind}/{doc['metadata']['name']}",
                                    recommendation="Pin to a specific version tag.",
                                    iso_control="A.8.29",
                                ))
                            resources = c.get("resources", {})
                            if not resources.get("requests") or not resources.get("limits"):
                                self.add_finding(SecOpsFinding(
                                    severity="low",
                                    category="deployment_risk",
                                    title=f"Missing resource requests/limits: {c['name']}",
                                    resource=f"{kind}/{doc['metadata']['name']}",
                                    recommendation="Add resource requests and limits.",
                                    iso_control="A.12.1",
                                ))
            except Exception as e:
                logger.debug("  Skipping %s: %s", manifest, e)
