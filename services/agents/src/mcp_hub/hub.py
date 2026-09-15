from __future__ import annotations

import asyncio
import json
import logging
import os
import select
import subprocess
import shutil
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from capability_registry import ConnectorManifest, MarkRegistry, load_default_registry

logger = logging.getLogger("mcp_hub")


def _read_dotenv_value(path: str, key: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                if name.strip() == key:
                    return value.strip().strip("'\"")
    except OSError:
        return None
    return None


def _env_value(key: str) -> str | None:
    value = os.environ.get(key)
    if value:
        return value

    here = os.path.abspath(__file__)
    candidates: list[str] = []
    cur = os.path.dirname(here)
    while True:
        candidates.append(os.path.join(cur, ".env"))
        candidates.append(os.path.join(cur, "backend", ".env"))
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent

    cwd = os.getcwd()
    candidates.append(os.path.join(cwd, ".env"))
    candidates.append(os.path.join(cwd, "backend", ".env"))

    seen: set[str] = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        value = _read_dotenv_value(path, key)
        if value:
            return value
    return None


class MCPHubError(RuntimeError):
    """Raised when an MCP connector call fails."""


class MCPPolicyError(PermissionError):
    """Raised when a connector policy blocks a call."""


class MCPStdioSession:
    """Persistent JSON-RPC MCP session over stdio."""

    def __init__(self, connector: ConnectorManifest, runtime: dict[str, Any]) -> None:
        self.connector = connector
        self.runtime = runtime
        self.process: subprocess.Popen[bytes] | None = None
        self._next_id = 1
        self._initialized = False

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        self._ensure_initialized()
        return self._request("tools/call", {"name": tool_name, "arguments": arguments})

    def list_tools(self) -> Any:
        self._ensure_initialized()
        return self._request("tools/list", {})

    def close(self) -> None:
        proc = self.process
        self.process = None
        self._initialized = False
        if not proc:
            return
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    def _ensure_initialized(self) -> None:
        self._ensure_process()
        if self._initialized:
            return
        self._request(
            "initialize",
            {
                "protocolVersion": str(self.runtime.get("protocol_version", "2025-06-18")),
                "capabilities": {},
                "clientInfo": {"name": "mark-mcp-client-hub", "version": "1.0.0"},
            },
        )
        self._notification("notifications/initialized", {})
        self._initialized = True

    def _ensure_process(self) -> None:
        if self.process and self.process.poll() is None:
            return

        command = MCPClientHub._resolve_command(self.runtime)
        if not command:
            raise MCPHubError(f"{self.connector.id} is missing MCP stdio command config")
        if os.path.isabs(command) and not os.path.exists(command):
            raise MCPHubError(f"{self.connector.id} MCP command does not exist: {command}")
        if not os.path.isabs(command) and not shutil.which(command):
            raise MCPHubError(f"{self.connector.id} MCP command not found on PATH: {command}")

        args = [str(arg) for arg in self.runtime.get("args", [])]
        env = os.environ.copy()
        for key in self.connector.env:
            value = _env_value(key)
            if value:
                env[key] = value
        self.process = subprocess.Popen(
            [command, *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            bufsize=0,
        )

    def _request(self, method: str, params: dict[str, Any]) -> Any:
        request_id = self._next_id
        self._next_id += 1
        self._write_message({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = time.time() + float(self.runtime.get("timeout_seconds", 20))
        while time.time() < deadline:
            message = self._read_message(deadline)
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise MCPHubError(str(message["error"]))
            return message.get("result", {})
        raise MCPHubError(f"{self.connector.id}.{method} timed out")

    def _notification(self, method: str, params: dict[str, Any]) -> None:
        self._write_message({"jsonrpc": "2.0", "method": method, "params": params})

    def _write_message(self, message: dict[str, Any]) -> None:
        self._ensure_process()
        if not self.process or not self.process.stdin:
            raise MCPHubError(f"{self.connector.id} MCP stdio stdin unavailable")
        body = json.dumps(message, separators=(",", ":")).encode("utf-8")
        if self.runtime.get("stdio_framing") == "json_lines":
            self.process.stdin.write(body + b"\n")
            self.process.stdin.flush()
            return
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        self.process.stdin.write(header + body)
        self.process.stdin.flush()

    def _read_message(self, deadline: float) -> dict[str, Any]:
        if not self.process or not self.process.stdout:
            raise MCPHubError(f"{self.connector.id} MCP stdio stdout unavailable")

        if self.runtime.get("stdio_framing") == "json_lines":
            remaining = max(0.0, deadline - time.time())
            ready, _, _ = select.select([self.process.stdout], [], [], remaining)
            if not ready:
                raise MCPHubError(
                    f"{self.connector.id} MCP stdio timed out waiting for JSON line"
                    f"{self._stderr_suffix()}"
                )
            line = self.process.stdout.readline()
            if not line:
                raise MCPHubError(f"{self.connector.id} MCP stdio closed{self._stderr_suffix()}")
            return json.loads(line.decode("utf-8"))

        headers: dict[str, str] = {}
        while time.time() < deadline:
            remaining = max(0.0, deadline - time.time())
            ready, _, _ = select.select([self.process.stdout], [], [], remaining)
            if not ready:
                raise MCPHubError(
                    f"{self.connector.id} MCP stdio timed out waiting for response headers"
                    f"{self._stderr_suffix()}"
                )
            line = self.process.stdout.readline()
            if line in (b"\r\n", b"\n", b""):
                if line == b"":
                    raise MCPHubError(f"{self.connector.id} MCP stdio closed{self._stderr_suffix()}")
                break
            decoded = line.decode("ascii", errors="replace").strip()
            if ":" in decoded:
                key, value = decoded.split(":", 1)
                headers[key.lower()] = value.strip()

        length = int(headers.get("content-length", "0"))
        if length <= 0:
            raise MCPHubError(f"{self.connector.id} MCP response missing Content-Length{self._stderr_suffix()}")
        remaining = max(0.0, deadline - time.time())
        ready, _, _ = select.select([self.process.stdout], [], [], remaining)
        if not ready:
            raise MCPHubError(f"{self.connector.id} MCP stdio timed out waiting for response body{self._stderr_suffix()}")
        body = self.process.stdout.read(length)
        return json.loads(body.decode("utf-8"))

    def _stderr_suffix(self) -> str:
        if not self.process or not self.process.stderr:
            return ""
        try:
            ready, _, _ = select.select([self.process.stderr], [], [], 0)
            if not ready:
                return ""
            data = self.process.stderr.read(4096)
            if not data:
                return ""
            return f"; stderr: {data.decode('utf-8', errors='replace').strip()[:500]}"
        except Exception:
            return ""


@dataclass(frozen=True)
class MCPCallTrace:
    connector_id: str
    tool_name: str
    transport: str
    started_at: float
    latency_ms: float
    status: str
    approval_required: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "tool_name": self.tool_name,
            "transport": self.transport,
            "started_at": self.started_at,
            "latency_ms": self.latency_ms,
            "status": self.status,
            "approval_required": self.approval_required,
            "error": self.error,
        }


class MCPClientHub:
    """One outbound MCP client hub for all MARK connector manifests."""

    _SIDE_EFFECT_PREFIXES = (
        "send",
        "create",
        "update",
        "delete",
        "write",
        "run",
        "execute",
        "deploy",
        "apply",
    )

    def __init__(self, registry: MarkRegistry | None = None) -> None:
        self.registry = registry or load_default_registry()
        self.traces: list[MCPCallTrace] = []
        self._stdio_sessions: dict[str, MCPStdioSession] = {}
        self._http_session_ids: dict[str, str] = {}
        self._http_initialized: set[str] = set()

    def connector_status(self) -> dict[str, dict[str, Any]]:
        return {connector_id: self._status_for(connector) for connector_id, connector in self.registry.connectors.items()}

    async def list_tools(self, connector_id: str) -> Any:
        connector = self._connector(connector_id)
        started = time.time()
        try:
            runtime = self._runtime(connector)
            protocol = self._protocol(runtime)
            if protocol == "http":
                result = await asyncio.to_thread(self._call_http_method, connector, "tools/list", {})
            elif protocol == "stdio":
                result = await asyncio.to_thread(self._stdio_session(connector).list_tools)
            else:
                raise MCPHubError(f"unsupported MCP protocol for {connector_id}: {protocol}")
            self._record(connector_id, "tools/list", connector.transport, started, "ok", False)
            return result
        except Exception as exc:
            self._record(connector_id, "tools/list", connector.transport, started, "error", False, str(exc))
            raise

    def list_tools_sync(self, connector_id: str) -> Any:
        connector = self._connector(connector_id)
        started = time.time()
        try:
            runtime = self._runtime(connector)
            protocol = self._protocol(runtime)
            if protocol == "http":
                result = self._call_http_method(connector, "tools/list", {})
            elif protocol == "stdio":
                result = self._stdio_session(connector).list_tools()
            else:
                raise MCPHubError(f"unsupported MCP protocol for {connector_id}: {protocol}")
            self._record(connector_id, "tools/list", connector.transport, started, "ok", False)
            return result
        except Exception as exc:
            self._record(connector_id, "tools/list", connector.transport, started, "error", False, str(exc))
            raise

    async def call_tool(
        self,
        connector_id: str,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        *,
        require_approval: bool | None = None,
        approval_granted: bool = False,
    ) -> Any:
        connector = self._connector(connector_id)
        arguments = arguments or {}
        approval_required = self._requires_approval(connector, tool_name, require_approval)
        if approval_required and not approval_granted:
            raise MCPPolicyError(f"{connector_id}.{tool_name} requires explicit approval")

        started = time.time()
        try:
            runtime = self._runtime(connector)
            protocol = self._protocol(runtime)
            if protocol == "http":
                result = await asyncio.to_thread(
                    self._call_http_method,
                    connector,
                    "tools/call",
                    {"name": tool_name, "arguments": arguments},
                )
            elif protocol == "stdio":
                result = await asyncio.to_thread(self._stdio_session(connector).call_tool, tool_name, arguments)
            else:
                raise MCPHubError(f"unsupported MCP protocol for {connector_id}: {protocol}")
            self._record(connector_id, tool_name, connector.transport, started, "ok", approval_required)
            return result
        except Exception as exc:
            self._record(connector_id, tool_name, connector.transport, started, "error", approval_required, str(exc))
            raise

    def call_tool_sync(
        self,
        connector_id: str,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        *,
        require_approval: bool | None = None,
        approval_granted: bool = False,
    ) -> Any:
        connector = self._connector(connector_id)
        arguments = arguments or {}
        approval_required = self._requires_approval(connector, tool_name, require_approval)
        if approval_required and not approval_granted:
            raise MCPPolicyError(f"{connector_id}.{tool_name} requires explicit approval")

        started = time.time()
        try:
            runtime = self._runtime(connector)
            protocol = self._protocol(runtime)
            if protocol == "http":
                result = self._call_http_method(
                    connector,
                    "tools/call",
                    {"name": tool_name, "arguments": arguments},
                )
            elif protocol == "stdio":
                result = self._stdio_session(connector).call_tool(tool_name, arguments)
            else:
                raise MCPHubError(f"unsupported MCP protocol for {connector_id}: {protocol}")
            self._record(connector_id, tool_name, connector.transport, started, "ok", approval_required)
            return result
        except Exception as exc:
            self._record(connector_id, tool_name, connector.transport, started, "error", approval_required, str(exc))
            raise

    def latest_traces(self, limit: int = 20) -> list[dict[str, Any]]:
        return [trace.to_dict() for trace in self.traces[-limit:]]

    def close(self) -> None:
        for session in list(self._stdio_sessions.values()):
            session.close()
        self._stdio_sessions.clear()

    def _connector(self, connector_id: str) -> ConnectorManifest:
        try:
            return self.registry.connectors[connector_id]
        except KeyError as exc:
            raise MCPHubError(f"unknown connector: {connector_id}") from exc

    def _status_for(self, connector: ConnectorManifest) -> dict[str, Any]:
        runtime = self._runtime(connector)
        protocol = self._protocol(runtime)
        configured = False
        detail = ""

        if connector.transport != "mcp":
            detail = f"connector transport is {connector.transport}"
        elif protocol == "http":
            url = self._resolve_url(runtime)
            configured = bool(url)
            detail = url or f"missing {runtime.get('url_env', 'MCP_URL')}"
        elif protocol == "stdio":
            command = self._resolve_command(runtime)
            configured = bool(command and (os.path.isabs(command) and os.path.exists(command) or shutil.which(command)))
            detail = command or f"missing {runtime.get('command_env', 'MCP_COMMAND')}"
        else:
            detail = f"unsupported protocol {protocol}"

        return {
            "id": connector.id,
            "name": connector.name,
            "manifest_status": connector.status,
            "transport": connector.transport,
            "managed_by": connector.managed_by,
            "protocol": protocol,
            "stdio_framing": runtime.get("stdio_framing", "content_length") if protocol == "stdio" else None,
            "session_active": self._stdio_session_active(connector.id) if protocol == "stdio" else None,
            "http_session_active": connector.id in self._http_initialized if protocol == "http" else None,
            "configured": configured,
            "detail": detail,
            "permissions": connector.permissions,
        }

    def _stdio_session_active(self, connector_id: str) -> bool:
        session = self._stdio_sessions.get(connector_id)
        return bool(session and session.process and session.process.poll() is None)

    def _stdio_session(self, connector: ConnectorManifest) -> MCPStdioSession:
        session = self._stdio_sessions.get(connector.id)
        if session is None:
            session = MCPStdioSession(connector, self._runtime(connector))
            self._stdio_sessions[connector.id] = session
        return session

    def _requires_approval(
        self,
        connector: ConnectorManifest,
        tool_name: str,
        require_approval: bool | None,
    ) -> bool:
        if require_approval is not None:
            return require_approval
        if any(permission.endswith("requires_approval") for permission in connector.permissions):
            if tool_name.split("/")[-1].startswith(self._SIDE_EFFECT_PREFIXES):
                return True
        return False

    def _call_http_method(self, connector: ConnectorManifest, method: str, params: dict[str, Any]) -> Any:
        runtime = self._runtime(connector)
        if self._requires_http_session(runtime) and method not in {"initialize", "notifications/initialized"}:
            self._ensure_http_initialized(connector)
        result, _headers = self._send_http_jsonrpc(
            connector,
            method,
            params,
            session_id=self._http_session_ids.get(connector.id),
            include_id=True,
        )
        return result

    def _ensure_http_initialized(self, connector: ConnectorManifest) -> None:
        if connector.id in self._http_initialized:
            return
        runtime = self._runtime(connector)
        result, headers = self._send_http_jsonrpc(
            connector,
            "initialize",
            {
                "protocolVersion": str(runtime.get("protocol_version", "2025-03-26")),
                "capabilities": {},
                "clientInfo": {"name": "mark-mcp-client-hub", "version": "1.0.0"},
            },
            session_id=None,
            include_id=True,
        )
        session_id = self._header_value(headers, "Mcp-Session-Id")
        if session_id:
            self._http_session_ids[connector.id] = session_id
        self._send_http_jsonrpc(
            connector,
            "notifications/initialized",
            {},
            session_id=session_id,
            include_id=False,
        )
        self._http_initialized.add(connector.id)
        logger.debug("Initialized HTTP MCP connector %s with result keys=%s", connector.id, list(result) if isinstance(result, dict) else type(result).__name__)

    def _send_http_jsonrpc(
        self,
        connector: ConnectorManifest,
        method: str,
        params: dict[str, Any],
        *,
        session_id: str | None,
        include_id: bool,
    ) -> tuple[Any, Any]:
        runtime = self._runtime(connector)
        url = self._resolve_url(runtime)
        if not url:
            raise MCPHubError(f"{connector.id} is missing MCP URL config")
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method, "params": params}
        if include_id:
            payload["id"] = int(time.time() * 1000)
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._normalize_mcp_url(url),
            data=body,
            headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json"},
        )
        protocol_version = str(runtime.get("protocol_version", ""))
        if protocol_version:
            req.add_header("Mcp-Protocol-Version", protocol_version)
        token = self._resolve_token(runtime)
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        if session_id:
            req.add_header("Mcp-Session-Id", session_id)
        try:
            with urllib.request.urlopen(req, timeout=float(runtime.get("timeout_seconds", 15))) as resp:
                text = resp.read().decode("utf-8")
                if not text.strip():
                    return {}, resp.headers
                return self._unwrap_mcp_payload(text, resp.headers.get("Content-Type", "")), resp.headers
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace").strip()
            message = f"HTTP Error {exc.code}: {exc.reason}"
            if body_text:
                message = f"{message}: {body_text[:500]}"
            raise MCPHubError(message) from exc

    def _record(
        self,
        connector_id: str,
        tool_name: str,
        transport: str,
        started: float,
        status: str,
        approval_required: bool,
        error: str | None = None,
    ) -> None:
        self.traces.append(
            MCPCallTrace(
                connector_id=connector_id,
                tool_name=tool_name,
                transport=transport,
                started_at=started,
                latency_ms=(time.time() - started) * 1000,
                status=status,
                approval_required=approval_required,
                error=error,
            )
        )

    @staticmethod
    def _runtime(connector: ConnectorManifest) -> dict[str, Any]:
        runtime = connector.raw.get("mcp_runtime", {})
        return runtime if isinstance(runtime, dict) else {}

    @staticmethod
    def _protocol(runtime: dict[str, Any]) -> str:
        env_key = runtime.get("protocol_env")
        if env_key and _env_value(env_key):
            return str(_env_value(env_key))
        return str(runtime.get("protocol", "http"))

    @staticmethod
    def _resolve_url(runtime: dict[str, Any]) -> str:
        env_key = runtime.get("url_env")
        if env_key and _env_value(env_key):
            return str(_env_value(env_key))
        return str(runtime.get("default_url", ""))

    @staticmethod
    def _resolve_token(runtime: dict[str, Any]) -> str:
        env_key = runtime.get("token_env")
        if env_key and _env_value(env_key):
            return str(_env_value(env_key))
        return ""

    @staticmethod
    def _resolve_command(runtime: dict[str, Any]) -> str:
        env_key = runtime.get("command_env")
        if env_key and _env_value(env_key):
            return str(_env_value(env_key))
        return str(runtime.get("default_command", ""))

    @staticmethod
    def _requires_http_session(runtime: dict[str, Any]) -> bool:
        return bool(runtime.get("session_required") or runtime.get("http_session"))

    @staticmethod
    def _header_value(headers: Any, name: str) -> str | None:
        value = headers.get(name) if hasattr(headers, "get") else None
        if value:
            return str(value)
        lower_name = name.lower()
        try:
            for key, header_value in headers.items():
                if str(key).lower() == lower_name:
                    return str(header_value)
        except Exception:
            return None
        return None

    @staticmethod
    def _normalize_mcp_url(url: str) -> str:
        base_url = url.rstrip("/")
        return base_url if base_url.endswith("/mcp") else base_url + "/mcp"

    @staticmethod
    def _unwrap_mcp_payload(text: str, content_type: str) -> Any:
        if "text/event-stream" in content_type.lower():
            for line in text.splitlines():
                if not line.startswith("data:"):
                    continue
                payload = line.removeprefix("data:").strip()
                if payload and payload != "[DONE]":
                    data = json.loads(payload)
                    break
            else:
                raise MCPHubError(f"No MCP data payload in response: {text[:300]}")
        else:
            data = json.loads(text)

        if "error" in data:
            raise MCPHubError(str(data["error"]))
        result = data.get("result", data)
        content = result.get("content") if isinstance(result, dict) else None
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    value = item.get("text", "")
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
        return result


_DEFAULT_HUB: MCPClientHub | None = None


def get_default_mcp_client_hub() -> MCPClientHub:
    global _DEFAULT_HUB
    if _DEFAULT_HUB is None:
        _DEFAULT_HUB = MCPClientHub()
    return _DEFAULT_HUB
