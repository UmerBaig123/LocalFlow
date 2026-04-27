"""Tool registry factory for LocalFlow."""

import sys

from localflow.tools.base import ToolRegistry
from localflow.tools.datetime_tool import DateTimeTool
from localflow.tools.mcp_client import McpClient, McpTool
from localflow.config import MCP_SERVERS

_default_registry: ToolRegistry | None = None


def create_default_registry() -> ToolRegistry:
    """Return the shared tool registry, creating it on first call.

    Built-in tools are registered directly.  MCP servers listed in
    ``MCP_SERVERS`` are spawned as subprocesses and their tools are
    discovered and wrapped automatically.  The registry (and its MCP
    subprocesses) are cached for the lifetime of the process.
    """
    global _default_registry
    if _default_registry is not None:
        return _default_registry

    registry = ToolRegistry()

    # Built-in tools
    registry.register(DateTimeTool())

    # MCP-provided tools
    for server_name, command in MCP_SERVERS.items():
        try:
            client = McpClient(server_name, command)
            for tool_def in client.list_tools():
                registry.register(McpTool(client, tool_def))
        except Exception as exc:
            print(
                f"[LocalFlow] Warning: MCP server '{server_name}' failed to start: {exc}",
                file=sys.stderr,
            )

    _default_registry = registry
    return registry
