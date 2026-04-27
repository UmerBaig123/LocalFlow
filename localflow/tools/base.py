"""BaseTool abstract class and ToolRegistry."""

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base class for all tools the LLM can invoke."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name (used in function-calling payloads)."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description shown to the LLM."""

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """JSON Schema describing the tool's parameters."""

    @abstractmethod
    def execute(self, **kwargs: Any) -> str:
        """Run the tool and return a plain-text result string."""

    def to_openai_schema(self) -> dict[str, Any]:
        """Return the OpenAI function-calling tool schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    """Dict-backed registry of available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def all_schemas(self) -> list[dict[str, Any]]:
        return [t.to_openai_schema() for t in self._tools.values()]

    def __len__(self) -> int:
        return len(self._tools)
