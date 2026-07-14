from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("secops")


class SecOpsFinding:
    severity: str
    category: str
    title: str
    description: str
    resource: str | None
    recommendation: str | None
    iso_control: str | None

    def __init__(
        self,
        severity: str,
        category: str,
        title: str,
        description: str,
        resource: str | None = None,
        recommendation: str | None = None,
        iso_control: str | None = None,
    ):
        self.severity = severity
        self.category = category
        self.title = title
        self.description = description
        self.resource = resource
        self.recommendation = recommendation
        self.iso_control = iso_control

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "resource": self.resource,
            "recommendation": self.recommendation,
            "iso_control": self.iso_control,
        }


class BaseSecOpsAgent:
    name: str
    schedule: str

    def __init__(self, name: str, schedule: str = ""):
        self.name = name
        self.schedule = schedule
        self.findings: list[SecOpsFinding] = []

    def add_finding(self, finding: SecOpsFinding) -> None:
        self.findings.append(finding)
        log_level = {
            "critical": logger.critical,
            "high": logger.error,
            "medium": logger.warning,
            "low": logger.info,
        }.get(finding.severity.lower(), logger.info)
        log_level(
            "[%s] %s: %s | %s",
            finding.severity.upper(),
            finding.category,
            finding.title,
            finding.resource or "",
        )

    def report(self) -> dict[str, Any]:
        return {
            "agent": self.name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_findings": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
        }

    def print_report(self) -> str:
        data = self.report()
        lines = [
            f"╔══ SECOPS REPORT ── {self.name}",
            f"║  Timestamp: {data['timestamp']}",
            f"║  Findings:  {data['total_findings']}",
        ]
        for f in data["findings"]:
            lines.append(f"║")
            lines.append(f"║  [{f['severity'].upper()}] {f['category']}: {f['title']}")
            if f["resource"]:
                lines.append(f"║    Resource: {f['resource']}")
            if f["recommendation"]:
                lines.append(f"║    Fix: {f['recommendation']}")
            if f["iso_control"]:
                lines.append(f"║    ISO: {f['iso_control']}")
        lines.append(f"╚══ END REPORT")
        report_str = "\n".join(lines)
        logger.info("\n" + report_str)
        return report_str

    async def run(self) -> dict[str, Any]:
        raise NotImplementedError
