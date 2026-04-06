"""OpenAI streaming refinement via httpx."""

import json
from collections.abc import Generator

import httpx

from localflow.config import (
    OPENAI_API_KEY, OPENAI_MODEL,
    OLLAMA_MODEL, OLLAMA_URL, USE_LOCAL,
    MODE_PROMPTS,
)

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

    def refine_stream(self, raw_text: str, mode: str) -> Generator[str, None, None]:
        if USE_LOCAL:
            url = f"{OLLAMA_URL}/v1/chat/completions"
            model = OLLAMA_MODEL
            headers = {"Content-Type": "application/json"}
        else:
            url = "https://api.openai.com/v1/chat/completions"
            model = OPENAI_MODEL
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": build_system_prompt(mode)},
                {"role": "user", "content": raw_text},
            ],
            "stream": True,
        }
        with httpx.stream(
            "POST", url, headers=headers, json=payload, timeout=60.0,
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
                token = delta.get("content", "")
                if token:
                    yield token
