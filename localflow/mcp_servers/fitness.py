"""MCP server: Fitness food-tracking API.

Speaks JSON-RPC 2.0 over stdio.  Exposes tools to add, list, update,
and delete food entries via the fitness app running on localhost:5050.

Run via:  python -m localflow.mcp_servers.fitness
"""

import datetime
import json
import sys
import urllib.request

BASE_URL = "http://localhost:5050"

# ── Tool definitions ────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "add_food_entry",
        "description": (
            "Log a food entry with estimated macros. "
            "Required: name, mealType (BREAKFAST|LUNCH|DINNER|SNACK), "
            "servingSizeG, calories, proteinG, carbsG, fatG. "
            "Optional: numberOfServings, fiberG, sugarG, sodiumMg."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Food name"},
                "mealType": {
                    "type": "string",
                    "enum": ["BREAKFAST", "LUNCH", "DINNER", "SNACK"],
                    "description": "Meal category",
                },
                "servingSizeG": {"type": "number", "description": "Serving size in grams"},
                "calories": {"type": "number", "description": "Total calories"},
                "proteinG": {"type": "number", "description": "Protein in grams"},
                "carbsG": {"type": "number", "description": "Carbs in grams"},
                "fatG": {"type": "number", "description": "Fat in grams"},
                "numberOfServings": {"type": "number", "description": "Number of servings (default 1)"},
                "fiberG": {"type": "number", "description": "Fiber in grams"},
                "sugarG": {"type": "number", "description": "Sugar in grams"},
                "sodiumMg": {"type": "number", "description": "Sodium in milligrams"},
            },
            "required": ["name", "mealType", "servingSizeG", "calories", "proteinG", "carbsG", "fatG"],
        },
    },
    {
        "name": "get_food_entries",
        "description": (
            "List today's food entries. Returns entry IDs, names, meal types, "
            "and macro totals. Use this before editing or deleting to find entry IDs."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format (defaults to today)",
                },
                "mealType": {
                    "type": "string",
                    "enum": ["BREAKFAST", "LUNCH", "DINNER", "SNACK"],
                    "description": "Filter by meal type (optional)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "update_food_entry",
        "description": (
            "Update an existing food entry by ID. Partial updates are OK — "
            "only include the fields you want to change."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Entry ID to update"},
                "name": {"type": "string"},
                "mealType": {"type": "string", "enum": ["BREAKFAST", "LUNCH", "DINNER", "SNACK"]},
                "servingSizeG": {"type": "number"},
                "calories": {"type": "number"},
                "proteinG": {"type": "number"},
                "carbsG": {"type": "number"},
                "fatG": {"type": "number"},
                "numberOfServings": {"type": "number"},
                "fiberG": {"type": "number"},
                "sugarG": {"type": "number"},
                "sodiumMg": {"type": "number"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "delete_food_entry",
        "description": "Delete a food entry by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Entry ID to delete"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "get_daily_requirements",
        "description": (
            "Get daily nutritional targets, consumed amounts, and remaining amounts. "
            "Use this when the user asks about remaining calories, protein, or other macros."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format (defaults to today)",
                },
            },
            "required": [],
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


def _add_food_entry(args: dict) -> str:
    today = datetime.date.today().isoformat()
    payload = {
        "name": args["name"],
        "mealType": args["mealType"],
        "servingSizeG": args["servingSizeG"],
        "calories": args["calories"],
        "proteinG": args["proteinG"],
        "carbsG": args["carbsG"],
        "fatG": args["fatG"],
        "date": today,
    }
    for opt in ("numberOfServings", "fiberG", "sugarG", "sodiumMg"):
        if opt in args:
            payload[opt] = args[opt]

    entry = _http_request(f"{BASE_URL}/api/food-entries", method="POST", data=payload)
    return (
        f"Added: {entry['name']} ({entry['mealType']})\n"
        f"  ID: {entry['id']}\n"
        f"  Calories: {entry['calories']} | "
        f"Protein: {entry['proteinG']}g | "
        f"Carbs: {entry['carbsG']}g | "
        f"Fat: {entry['fatG']}g"
    )


def _get_food_entries(args: dict) -> str:
    date = args.get("date") or datetime.date.today().isoformat()
    url = f"{BASE_URL}/api/food-entries?date={date}"
    if "mealType" in args:
        url += f"&mealType={args['mealType']}"

    data = _http_request(url)
    entries = data.get("entries", [])
    if not entries:
        return f"No food entries found for {date}."

    lines = [f"Food entries for {date}:", ""]
    for e in entries:
        lines.append(
            f"  [{e['id']}] {e['name']} — {e['mealType']}\n"
            f"    Calories: {e['calories']} | "
            f"Protein: {e['proteinG']}g | "
            f"Carbs: {e['carbsG']}g | "
            f"Fat: {e['fatG']}g | "
            f"Serving: {e['servingSizeG']}g"
        )

    totals = data.get("totals", {})
    if totals:
        lines.append("")
        lines.append(
            f"Daily totals — "
            f"Calories: {totals.get('calories', 0)} | "
            f"Protein: {totals.get('proteinG', 0)}g | "
            f"Carbs: {totals.get('carbsG', 0)}g | "
            f"Fat: {totals.get('fatG', 0)}g"
        )
    return "\n".join(lines)


def _update_food_entry(args: dict) -> str:
    entry_id = args.pop("id")
    # args now contains only the fields to update
    entry = _http_request(
        f"{BASE_URL}/api/food-entries/{entry_id}", method="PUT", data=args,
    )
    return (
        f"Updated: {entry['name']} ({entry['mealType']})\n"
        f"  ID: {entry['id']}\n"
        f"  Calories: {entry['calories']} | "
        f"Protein: {entry['proteinG']}g | "
        f"Carbs: {entry['carbsG']}g | "
        f"Fat: {entry['fatG']}g"
    )


def _delete_food_entry(args: dict) -> str:
    entry_id = args["id"]
    _http_request(f"{BASE_URL}/api/food-entries/{entry_id}", method="DELETE")
    return f"Deleted entry {entry_id}."


def _get_daily_requirements(args: dict) -> str:
    date = args.get("date") or datetime.date.today().isoformat()
    data = _http_request(f"{BASE_URL}/api/daily-requirements?date={date}")

    lines = [f"Daily requirements for {data.get('date', date)} (Goal: {data.get('goal', 'N/A')}):", ""]
    for r in data.get("requirements", []):
        lines.append(
            f"  {r['name']}: {r['consumed']}/{r['target']} {r['unit']} "
            f"({r['remaining']} {r['unit']} remaining)"
        )
    return "\n".join(lines)


_TOOL_DISPATCH = {
    "add_food_entry": _add_food_entry,
    "get_food_entries": _get_food_entries,
    "update_food_entry": _update_food_entry,
    "delete_food_entry": _delete_food_entry,
    "get_daily_requirements": _get_daily_requirements,
}

# ── JSON-RPC handlers ──────────────────────────────────────────────────


def _handle_initialize(msg_id):
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "fitness", "version": "1.0.0"},
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
