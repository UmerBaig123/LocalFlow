"""MCP server: Task management API.

Speaks JSON-RPC 2.0 over stdio.  Exposes tools to create, list, update,
and delete tasks via the task management app running on localhost:5050.

Run via:  python -m localflow.mcp_servers.todo
"""

import json
import sys
import urllib.request

BASE_URL = "http://localhost:5050"

# ── Tool definitions ────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "list_tasks",
        "description": (
            "List all tasks, optionally filtered by status. "
            "Returns task IDs, titles, statuses, descriptions, and positions. "
            "Always call this before editing, deleting, or completing tasks "
            "to get real IDs."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["TODO", "IN_PROGRESS", "DONE"],
                    "description": "Filter by status (optional)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "create_task",
        "description": (
            "Create a new task. Required: title. "
            "Optional: description, status (TODO|IN_PROGRESS|DONE, defaults to TODO)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title"},
                "description": {"type": "string", "description": "Task description (optional)"},
                "status": {
                    "type": "string",
                    "enum": ["TODO", "IN_PROGRESS", "DONE"],
                    "description": "Task status (defaults to TODO)",
                },
            },
            "required": ["title"],
        },
    },
    {
        "name": "update_task",
        "description": (
            "Update an existing task by ID. Partial updates are OK — "
            "only include the fields you want to change. "
            "Use status 'DONE' to mark complete, 'IN_PROGRESS' to start. "
            "Use position (integer) to reorder."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Task ID to update"},
                "title": {"type": "string", "description": "New title"},
                "description": {"type": "string", "description": "New description"},
                "status": {
                    "type": "string",
                    "enum": ["TODO", "IN_PROGRESS", "DONE"],
                    "description": "New status",
                },
                "position": {"type": "integer", "description": "New position for reordering"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "delete_task",
        "description": "Permanently delete a task by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Task ID to delete"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "get_task",
        "description": "Get a single task's full details by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Task ID"},
            },
            "required": ["id"],
        },
    },
]

# ── HTTP helpers ────────────────────────────────────────────────────────


def _http_request(url: str, *, method: str = "GET", data: dict | None = None) -> dict:
    """Send an HTTP request and return parsed JSON."""
    body = None
    headers = {}
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


# ── Tool implementations ───────────────────────────────────────────────


def _list_tasks(args: dict) -> str:
    url = f"{BASE_URL}/api/tasks"
    if "status" in args:
        url += f"?status={args['status']}"

    data = _http_request(url)
    tasks = data if isinstance(data, list) else data.get("tasks", [])
    if not tasks:
        status_filter = args.get("status", "")
        return f"No tasks found{f' with status {status_filter}' if status_filter else ''}."

    lines = ["Tasks:", ""]
    for t in tasks:
        status = t.get("status", "TODO")
        title = t.get("title", "Untitled")
        desc = t.get("description", "")
        pos = t.get("position", "")
        line = f"  [{t['id']}] {title} — {status}"
        if pos != "":
            line += f" (position: {pos})"
        if desc:
            line += f"\n    Description: {desc}"
        lines.append(line)

    return "\n".join(lines)


def _create_task(args: dict) -> str:
    payload = {"title": args["title"]}
    for opt in ("description", "status"):
        if opt in args:
            payload[opt] = args[opt]

    task = _http_request(f"{BASE_URL}/api/tasks", method="POST", data=payload)
    return (
        f"Created: {task.get('title', args['title'])}\n"
        f"  ID: {task.get('id', 'N/A')}\n"
        f"  Status: {task.get('status', 'TODO')}"
    )


def _update_task(args: dict) -> str:
    task_id = args.pop("id")
    task = _http_request(
        f"{BASE_URL}/api/tasks/{task_id}", method="PUT", data=args,
    )
    result = f"Updated: {task.get('title', 'N/A')}\n  ID: {task.get('id', task_id)}\n  Status: {task.get('status', 'N/A')}"
    if task.get("position") is not None:
        result += f"\n  Position: {task['position']}"
    return result


def _delete_task(args: dict) -> str:
    task_id = args["id"]
    _http_request(f"{BASE_URL}/api/tasks/{task_id}", method="DELETE")
    return f"Deleted task {task_id}."


def _get_task(args: dict) -> str:
    task_id = args["id"]
    task = _http_request(f"{BASE_URL}/api/tasks/{task_id}")
    lines = [
        f"Task [{task.get('id', task_id)}]:",
        f"  Title: {task.get('title', 'N/A')}",
        f"  Status: {task.get('status', 'N/A')}",
    ]
    if task.get("description"):
        lines.append(f"  Description: {task['description']}")
    if task.get("position") is not None:
        lines.append(f"  Position: {task['position']}")
    return "\n".join(lines)


_TOOL_DISPATCH = {
    "list_tasks": _list_tasks,
    "create_task": _create_task,
    "update_task": _update_task,
    "delete_task": _delete_task,
    "get_task": _get_task,
}

# ── JSON-RPC handlers ──────────────────────────────────────────────────


def _handle_initialize(msg_id):
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "todo", "version": "1.0.0"},
        },
    }


def _handle_tools_list(msg_id):
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": {"tools": TOOLS},
    }


def _handle_tools_call(msg_id, params):
    name = params.get("name", "")
    handler = _TOOL_DISPATCH.get(name)
    if handler is None:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Unknown tool: {name}"},
        }
    try:
        arguments = params.get("arguments", {})
        text = handler(dict(arguments))
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"content": [{"type": "text", "text": text}]},
        }
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [{"type": "text", "text": f"Error: {exc}"}],
                "isError": True,
            },
        }


# ── Main loop ───────────────────────────────────────────────────────────

_HANDLERS = {
    "initialize": lambda mid, _p: _handle_initialize(mid),
    "tools/list": lambda mid, _p: _handle_tools_list(mid),
    "tools/call": lambda mid, p: _handle_tools_call(mid, p),
}


def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        method = msg.get("method", "")
        msg_id = msg.get("id")
        params = msg.get("params", {})

        handler = _HANDLERS.get(method)
        if handler and msg_id is not None:
            response = handler(msg_id, params)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
