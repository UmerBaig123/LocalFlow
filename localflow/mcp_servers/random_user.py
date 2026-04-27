"""MCP server: Random User API.

Speaks JSON-RPC 2.0 over stdio.  Exposes a single tool — ``get_random_user``
— that fetches a random user from https://randomuser.me/api/.

Run via:  python -m localflow.mcp_servers.random_user
"""

import json
import sys
import urllib.request

# ── Tool definition ──────────────────────────────────────────────────────

TOOL_DEF = {
    "name": "get_random_user",
    "description": (
        "Fetch a random user profile (name, email, location, phone, picture) "
        "from the Random User API."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

# ── Handlers ─────────────────────────────────────────────────────────────

def _handle_initialize(msg_id):
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "random-user", "version": "1.0.0"},
        },
    }


def _handle_tools_list(msg_id):
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": {"tools": [TOOL_DEF]},
    }


def _fetch_random_user() -> str:
    with urllib.request.urlopen("https://randomuser.me/api/", timeout=15) as resp:
        data = json.loads(resp.read())
    user = data["results"][0]
    name = user["name"]
    loc = user["location"]
    return (
        f"Name: {name['title']} {name['first']} {name['last']}\n"
        f"Email: {user['email']}\n"
        f"Phone: {user['phone']}\n"
        f"Location: {loc['city']}, {loc['state']}, {loc['country']}\n"
        f"Picture: {user['picture']['large']}"
    )


def _handle_tools_call(msg_id, params):
    name = params.get("name", "")
    if name != "get_random_user":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Unknown tool: {name}"},
        }
    try:
        text = _fetch_random_user()
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

# ── Main loop ────────────────────────────────────────────────────────────

_HANDLERS = {
    "initialize": lambda mid, _p: _handle_initialize(mid),
    "tools/list": lambda mid, _p: _handle_tools_list(mid),
    "tools/call": lambda mid, p: _handle_tools_call(mid, p),
}


def main():
    # Use readline() — iterating sys.stdin directly uses a read-ahead
    # buffer that blocks when stdin is a pipe.
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
        # Notifications (no id) like notifications/initialized are silently ignored.


if __name__ == "__main__":
    main()
