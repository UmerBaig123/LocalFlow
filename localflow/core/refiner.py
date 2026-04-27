"""OpenAI streaming refinement via httpx — with tool-calling support."""

import json
from collections.abc import Callable, Generator
from typing import Any

import httpx

from localflow.config import (
    OPENAI_API_KEY, OPENAI_MODEL,
    OLLAMA_MODEL, OLLAMA_URL, USE_LOCAL,
    MODE_PROMPTS, TOOL_MAX_ITERATIONS,
)
from localflow.tools import create_default_registry
from localflow.tools.base import ToolRegistry

# Appended to every mode's system prompt so all responses are well-formatted.
_FORMAT_SUFFIX = """

## Formatting requirements

Structure your response for maximum readability:
- Use **bold** for key terms, names, and important phrases.
- Use headings (##, ###) to separate distinct sections when the response covers \
multiple topics or steps.
- Use bullet points or numbered lists for sequences, options, or multiple items — \
never bury a list in a paragraph.
- Use inline `code` for technical identifiers (functions, variables, commands, paths) \
and fenced code blocks for multi-line code or examples.
- Keep paragraphs short (2-4 sentences max). Prefer whitespace over walls of text.
- Front-load the most important information — put conclusions and answers first, \
then supporting detail.
- If the response is a single short sentence or phrase, return it plainly without \
unnecessary formatting."""


_NO_FORMAT_SUFFIX_MODES = {"code"}


def build_system_prompt(mode: str) -> str:
    """Return the full system prompt for *mode* with formatting rules appended."""
    base = MODE_PROMPTS[mode]
    if mode in _NO_FORMAT_SUFFIX_MODES:
        return base
    return base + _FORMAT_SUFFIX


class Refiner:
    """Sends raw transcription to OpenAI and yields refined tokens."""

    def __init__(self) -> None:
        self._registry: ToolRegistry = create_default_registry()

    def _get_endpoint(self) -> tuple[str, str, dict[str, str]]:
        """Return (url, model, headers) based on USE_LOCAL config."""
        if USE_LOCAL:
            return (
                f"{OLLAMA_URL}/v1/chat/completions",
                OLLAMA_MODEL,
                {"Content-Type": "application/json"},
            )
        return (
            "https://api.openai.com/v1/chat/completions",
            OPENAI_MODEL,
            {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
        )

    def _stream_one_request(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> Generator[str, None, tuple[str, list[dict[str, Any]]]]:
        """Stream a single chat-completion request.

        Yields content tokens as they arrive.
        Returns (full_content, tool_calls) when the stream ends.
        tool_calls is a list of dicts: {"id": ..., "function": {"name": ..., "arguments": ...}}
        """
        full_content: list[str] = []
        # Accumulate tool-call deltas keyed by index
        tool_call_accum: dict[int, dict[str, Any]] = {}

        with httpx.stream(
            "POST", url, headers=headers, json=payload, timeout=120.0,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                data = json.loads(data_str)
                delta = data["choices"][0]["delta"]

                # Content tokens
                token = delta.get("content", "")
                if token:
                    full_content.append(token)
                    yield token

                # Tool-call deltas
                if "tool_calls" in delta:
                    for tc_delta in delta["tool_calls"]:
                        idx = tc_delta["index"]
                        if idx not in tool_call_accum:
                            tool_call_accum[idx] = {
                                "id": "",
                                "function": {"name": "", "arguments": ""},
                            }
                        entry = tool_call_accum[idx]
                        if "id" in tc_delta:
                            entry["id"] += tc_delta["id"]
                        fn = tc_delta.get("function", {})
                        if "name" in fn:
                            entry["function"]["name"] += fn["name"]
                        if "arguments" in fn:
                            entry["function"]["arguments"] += fn["arguments"]

        tool_calls = [tool_call_accum[i] for i in sorted(tool_call_accum)]
        return "".join(full_content), tool_calls

    def refine_stream(
        self,
        raw_text: str,
        mode: str,
        status_callback: Callable[[str], Any] | None = None,
    ) -> Generator[str, None, None]:
        url, model, headers = self._get_endpoint()

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": build_system_prompt(mode)},
            {"role": "user", "content": raw_text},
        ]

        use_tools = mode in {"interact", "fitness", "todo"} and len(self._registry) > 0
        tool_schemas = self._registry.all_schemas() if use_tools else []

        for _iteration in range(TOOL_MAX_ITERATIONS):
            payload: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "stream": True,
            }
            if tool_schemas:
                payload["tools"] = tool_schemas

            # yield from forwards content tokens; gen.value captures the return
            gen = self._stream_one_request(url, headers, payload)
            try:
                while True:
                    yield next(gen)
            except StopIteration as e:
                full_content, tool_calls = e.value

            if not tool_calls:
                return

            # Build assistant message with tool calls
            assistant_msg: dict[str, Any] = {"role": "assistant"}
            if full_content:
                assistant_msg["content"] = full_content
            else:
                assistant_msg["content"] = None
            assistant_msg["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["function"]["name"],
                        "arguments": tc["function"]["arguments"],
                    },
                }
                for tc in tool_calls
            ]
            messages.append(assistant_msg)

            # Execute each tool call and append results
            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                raw_args = tc["function"]["arguments"]

                if status_callback:
                    status_callback(f"Running tool: {fn_name}...")

                tool = self._registry.get(fn_name)
                if tool is None:
                    result = f"Error: unknown tool '{fn_name}'"
                else:
                    try:
                        kwargs = json.loads(raw_args) if raw_args else {}
                        result = tool.execute(**kwargs)
                    except Exception as exc:
                        result = f"Error executing {fn_name}: {exc}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })

            if status_callback:
                status_callback("Responding...")
