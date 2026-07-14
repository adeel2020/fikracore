#!/usr/bin/env python3
"""SecOps agent runner — dispatches to the correct agent based on AGENT_ROLE env var.

Usage:
    AGENT_ROLE=secret-scanner python -m services.agents.src.secops.runner
    AGENT_ROLE=vulnerability-responder python -m services.agents.src.secops.runner
    AGENT_ROLE=compliance-auditor python -m services.agents.src.secops.runner
    AGENT_ROLE=deployment-guardian python -m services.agents.src.secops.runner
    AGENT_ROLE=policy-enforcer python -m services.agents.src.secops.runner
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

AGENT_MAP = {
    "secret-scanner": "secops.secret_scanner.SecretScanner",
    "vulnerability-responder": "secops.vulnerability_responder.VulnerabilityResponder",
    "compliance-auditor": "secops.compliance_auditor.ComplianceAuditor",
    "deployment-guardian": "secops.deployment_guardian.DeploymentGuardian",
    "policy-enforcer": "secops.policy_enforcer.PolicyEnforcer",
}


def main() -> None:
    role = os.environ.get("AGENT_ROLE", "")
    if not role:
        print("Usage: AGENT_ROLE=<role> python runner.py")
        print(f"Available roles: {', '.join(AGENT_MAP.keys())}")
        sys.exit(1)

    if role not in AGENT_MAP:
        print(f"Unknown role: {role}")
        print(f"Available roles: {', '.join(AGENT_MAP.keys())}")
        sys.exit(1)

    module_path, class_name = AGENT_MAP[role].rsplit(".", 1)
    import importlib
    module = importlib.import_module(f"secops.{module_path}" if "." not in module_path else module_path)
    agent_class = getattr(module, class_name)
    agent = agent_class()

    result = asyncio.run(agent.run())
    print("\n=== JSON Report ===")
    import json
    print(json.dumps(result, indent=2, default=str))

    exit_code = 0
    if result.get("total_findings", 0) > 0:
        severities = {f["severity"] for f in result.get("findings", [])}
        if "critical" in severities or "high" in severities:
            exit_code = 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
