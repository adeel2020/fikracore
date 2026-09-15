"""Compatibility wrapper for the canonical shared MCP client hub."""

from mcp_hub import MCPClientHub, MCPHubError, MCPPolicyError, get_default_mcp_client_hub

__all__ = ["MCPClientHub", "MCPHubError", "MCPPolicyError", "get_default_mcp_client_hub"]
