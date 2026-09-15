"""Compatibility wrapper for the canonical shared MCP client hub implementation."""

from mcp_hub.hub import (
    MCPCallTrace,
    MCPClientHub,
    MCPHubError,
    MCPPolicyError,
    MCPStdioSession,
    get_default_mcp_client_hub,
)

__all__ = [
    "MCPCallTrace",
    "MCPClientHub",
    "MCPHubError",
    "MCPPolicyError",
    "MCPStdioSession",
    "get_default_mcp_client_hub",
]
