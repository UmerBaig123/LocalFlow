"""MCP client — spawns MCP servers and wraps their tools as BaseTool instances."""

import atexit
import json
import subprocess
import sys
from typing import Any

from localflow.tools.base import BaseTool


class McpClient:
    """Manages a single MCP server subprocess (JSON-RPC over stdio)."""

    def __init__(self, name: str, command: list[str]) -> None:
        self.name = name
        self._proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self._next_id = 1
        self._initialize()
        atexit.register(self.close)

    # ── Low-level JSON-RPC ────────────────────────────────────────────

    def _send(
        self,
        method: str,
        params: dict | None = None,
        *,
        notify: bool = False,
    ) -> dict | None:
        """Send a JSON-RPC message. Returns the parsed response (or None for notifications)."""
        msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if not notify:
            msg["id"] = self._next_id
            self._next_id += 1
        if params is not None:
            msg["params"] = params

        self._proc.stdin.write(json.dumps(msg) + "\n")
        self._proc.stdin.flush()

        if notify:
            return None

        line = self._proc.stdout.readline()
        if not line:
            raise ConnectionError(f"MCP server '{self.name}' closed unexpectedly")
        return json.loads(line)

    # ── MCP protocol ──────────────────────────────────────────────────

    def _initialize(self) -> None:
        self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "localflow", "version": "1.0.0"},
        })
        self._send("notifications/initialized", notify=True)

    def list_tools(self) -> list[dict[str, Any]]:
        resp = self._send("tools/list", {})
        return resp["result"]["tools"]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        resp = self._send("tools/call", {"name": name, "arguments": arguments})
        if "error" in resp:
            return f"Error: {resp['error']['message']}"
        content = resp["result"].get("content", [])
        return "\n".join(
            c.get("text", "") for c in content if c.get("type") == "text"
        )

    # ── Lifecycle ─────────────────────────────────────────────────────

    def close(self) -> None:
        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()


class McpTool(BaseTool):
    """Wraps a single tool exposed by an MCP server as a BaseTool."""

    def __init__(self, client: McpClient, tool_def: dict[str, Any]) -> None:
        self._client = client
        self._name: str = tool_def["name"]
        self._description: str = tool_def.get("description", "")
        self._parameters: dict[str, Any] = tool_def.get(
            "inputSchema", {"type": "object", "properties": {}},
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> dict[str, Any]:
        return self._parameters

    def execute(self, **kwargs: Any) -> str:
        try:
            return self._client.call_tool(self._name, kwargs)
        except Exception as exc:
            return f"Error calling MCP tool '{self._name}': {exc}"
