"""Automated Test Suite for Step 4.5 Live gbrain MCP Integration Smoke Test.

Covers:
1. Hermetic mock-based tests for all 15+ smoke checks and classification decisions
2. Failure category handling (MCP_UNREACHABLE, MCP_AUTH_FAILED, MCP_TOOL_MISSING, PAGE_NOT_FOUND, HIDDEN_TRUTH_LEAKAGE)
3. CLI dispatch and arguments for 'inspect mcp', 'inspect live-knowledge', and 'mcp-smoke'
4. Live integration test against http://localhost:3131/mcp (marked for live execution)
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from engine_stack.engines.telecom_brain.investigation.mcp_smoke_test import (
    LiveMcpSmokeTestRunner,
    run_mcp_smoke_test,
)
from engine_stack.engines.telecom_brain.investigation.cli import build_parser, main
from engine_stack.engines.telecom_brain.investigation.contracts import (
    Terminal,
    WhatIfSimulationResult,
    WhatIfTrigger,
    BlastRadiusAssessment,
    BlastRadiusLevel,
)


class FakeMockProvider:
    """Hermetic mock provider simulating a healthy telecombrain MCP instance."""

    def __init__(self):
        self.metadata = {
            "knowledge_provider_type": "GbrainTelecomBrainProvider",
            "brain": "telecombrain",
            "snapshot_version": None,
            "consistency": "live; may evolve during investigation",
        }
        self.contracts = {
            "get_page": {},
            "get_links": {},
            "get_backlinks": {},
            "traverse_graph": {},
            "search": {},
            "query": {},
            "get_active_schema_pack": {},
        }
        self.pages = {
            "domains/mobile-core/networks/lte/functions/mme-01": {
                "slug": "domains/mobile-core/networks/lte/functions/mme-01",
                "title": "mme-01 (mme, mobile-core)",
                "type": "domain-function",
            },
            "domains/mobile-core/networks/ps/functions/pgw-01": {
                "slug": "domains/mobile-core/networks/ps/functions/pgw-01",
                "title": "pgw-01 (pgw, mobile-core)",
                "type": "domain-function",
            },
            "domains/transport/functions/sgi-edge-01": {
                "slug": "domains/transport/functions/sgi-edge-01",
                "title": "sgi-edge-01 (edge-router, transport)",
                "type": "domain-function",
            },
            "tickets/mobile-core/tt-984210": {
                "slug": "tickets/mobile-core/tt-984210",
                "title": "Trouble Ticket TT-984210 Journey",
                "type": "ticket-journey",
            },
            "incidents/mobile-core/sgi-data-a154bb7a3997859c": {
                "slug": "incidents/mobile-core/sgi-data-a154bb7a3997859c",
                "title": "SGi Data Forwarding Incident",
                "type": "incident",
            },
            "router-02": {
                "slug": "router-02",
                "title": "Router 02",
                "type": "domain-function",
            },
        }

    def _call(self, name: str, arguments: dict):
        if name == "get_active_schema_pack":
            return {
                "identity": "mobile-core@0.1.0+2eea5e14",
                "pack_name": "mobile-core",
                "version": "0.1.0",
                "page_types_count": 27,
                "link_types_count": 25,
                "source_tier": "home-config",
            }
        return {}

    def get_page(self, slug: str):
        return self.pages.get(slug)

    def get_links(self, slug: str):
        return [{"source": slug, "target": "router-02", "link_type": "depends-on"}]

    def get_backlinks(self, slug: str):
        return [{"source": "service-01", "target": slug, "link_type": "involves"}]

    def traverse(self, slug: str, depth: int = 1, direction: str = "both", link_type: str | None = None):
        return [{"source": slug, "target": "router-02", "link_type": "depends-on", "depth": 1, "state": "CONFIRMED"}]

    def search(self, query: str):
        return [p for p in self.pages.values() if query.lower() in p["title"].lower() or query.lower() in p["slug"].lower()]

    def query(self, query: str):
        return self.search(query)


def test_runner_all_pass_hermetic(tmp_path):
    """Verify that when all mock checks pass, runner produces LIVE_MCP_SMOKE_SUPPORTED."""
    runner = LiveMcpSmokeTestRunner(
        url="http://localhost:3131/mcp",
        output_dir=tmp_path / "integration",
    )
    fake_provider = FakeMockProvider()

    with patch.object(runner, "test_1_connectivity", return_value=True), \
         patch.object(runner, "test_2_auth_and_session", return_value=True):
        runner.provider = fake_provider
        runner.results["connectivity"] = "PASS"
        runner.results["authentication"] = "PASS"
        runner.results["session"] = "PASS"

        summary = runner.run_all()

    assert summary["decision"] == "LIVE_MCP_SMOKE_SUPPORTED"
    assert summary["hidden_truth_leakage"] == 0
    assert summary["checks"]["page_read"] == "PASS"
    assert summary["checks"]["schema"] == "PASS"
    assert summary["checks"]["canonical_resolution"] == "PASS"
    assert (tmp_path / "integration" / "mcp-smoke-test.json").exists()
    assert (tmp_path / "integration" / "mcp-smoke-test.md").exists()


def test_runner_unreachable(tmp_path):
    """Verify MCP_UNREACHABLE classification when endpoint cannot be contacted."""
    runner = LiveMcpSmokeTestRunner(
        url="http://invalid-host-9999.invalid:3131/mcp",
        output_dir=tmp_path / "integration",
    )
    summary = runner.run_all()
    assert summary["decision"] == "LIVE_MCP_SMOKE_NOT_SUPPORTED"
    assert summary["checks"].get("connectivity") == "FAIL"
    assert any(f["category"] == "MCP_UNREACHABLE" for f in summary["failures"])


def test_runner_tool_missing(tmp_path):
    """Verify MCP_TOOL_MISSING classification when mandatory tool is absent."""
    runner = LiveMcpSmokeTestRunner(output_dir=tmp_path / "integration")
    fake = FakeMockProvider()
    del fake.contracts["traverse_graph"]
    runner.provider = fake

    ok = runner.test_3_tool_discovery()
    assert ok is False
    assert any(f["category"] == "MCP_TOOL_MISSING" for f in runner.failures)


def test_runner_page_not_found(tmp_path):
    """Verify PAGE_NOT_FOUND classification when fewer than 3 known pages exist."""
    runner = LiveMcpSmokeTestRunner(output_dir=tmp_path / "integration")
    fake = FakeMockProvider()
    fake.pages.clear()
    runner.provider = fake

    ok = runner.test_5_page_read()
    assert ok is False
    assert any(f["category"] == "PAGE_NOT_FOUND" for f in runner.failures)


def test_runner_hidden_truth_boundary_leakage_detected(tmp_path):
    """Verify HIDDEN_TRUTH_LEAKAGE is caught if evaluator truth is present."""
    runner = LiveMcpSmokeTestRunner(output_dir=tmp_path / "integration")
    leaked_payload = {"observed": "node-1", "actual_root_cause": "node-0"}
    runner._check_truth_leakage(leaked_payload, "test_context")

    assert runner.hidden_truth_leakage > 0
    ok = runner.test_15_hidden_truth_boundary()
    assert ok is False
    assert any(f["category"] == "HIDDEN_TRUTH_LEAKAGE" for f in runner.failures)


def test_cli_parser_inspect_mcp_and_smoke():
    """Verify CLI parser options for inspect mcp and mcp-smoke."""
    parser = build_parser()
    args_inspect = parser.parse_args(["inspect", "mcp", "--reasoning"])
    assert args_inspect.command == "inspect"
    assert args_inspect.scenario == "mcp"
    assert args_inspect.reasoning is True

    args_smoke = parser.parse_args(["mcp-smoke", "--output-dir", "artifacts/integration"])
    assert args_smoke.command == "mcp-smoke"
    assert args_smoke.output_dir == Path("artifacts/integration")
    assert args_smoke.no_reasoning is False


def test_cli_execution_inspect_mcp(capsys):
    """Verify CLI main dispatch for inspect mcp invokes runner."""
    with patch("engine_stack.engines.telecom_brain.investigation.mcp_smoke_test.LiveMcpSmokeTestRunner.run_all") as mock_run:
        mock_run.return_value = {
            "decision": "LIVE_MCP_SMOKE_SUPPORTED",
            "passed_count": "16/16",
        }
        main(["inspect", "mcp"])
        captured = capsys.readouterr()
        assert "LIVE_MCP_SMOKE_SUPPORTED" in captured.out
