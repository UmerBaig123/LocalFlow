"""DateTimeTool — returns the current date and time."""

from datetime import datetime, timezone, timedelta
from typing import Any

from localflow.tools.base import BaseTool


class DateTimeTool(BaseTool):
    """Returns the current date and time with an optional UTC offset."""

    @property
    def name(self) -> str:
        return "get_datetime"

    @property
    def description(self) -> str:
        return "Get the current date and time. Optionally specify a UTC offset in hours."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "utc_offset": {
                    "type": "number",
                    "description": "UTC offset in hours (e.g. 5, -3, 5.5). Defaults to 0 (UTC).",
                },
            },
            "required": [],
        }

    def execute(self, **kwargs: Any) -> str:
        offset_hours = kwargs.get("utc_offset", 0)
        try:
            offset_hours = float(offset_hours)
        except (TypeError, ValueError):
            offset_hours = 0.0
        tz = timezone(timedelta(hours=offset_hours))
        now = datetime.now(tz)
        return now.strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)")
