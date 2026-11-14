"""Phrase a KB section into a natural reply via a local llamafile server.

Turns the KB section the walk reached into a reply using llamafile's
OpenAI-compatible endpoint.

llamafile is a single executable that embeds the model and the runtime. Launch
it in server mode (see README) and this module calls its /v1/chat/completions
endpoint. If the server is not running, fall back to the raw section text so the
assistant still works without it.
"""

from __future__ import annotations

import asyncio
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_URL = "http://localhost:8080/v1/chat/completions"
DEFAULT_TIMEOUT = 180.0  # a 3B model on CPU can take a minute on a long passage set

SYSTEM = (
    "You are a customer support assistant. Rewrite the knowledge base section "
    "into a short, friendly reply that resolves the user's problem. Use ONLY "
    "facts from the section. Do not invent steps, numbers, or policies. If the "
    "section does not cover the question, say so plainly.\n"
    "If the section contains commands, code, or names a skill to run a task or "
    "workflow (for example a skill named `apheris-workflow-<id>`), reproduce "
    "those commands and skill names EXACTLY as written — never paraphrase, "
    "reorder, or invent flags — and present them as the numbered step-by-step to "
    "run it. Tell the user they can install and use that skill to run the "
    "workflow, and keep the execution target (standalone vs Hub) as the section "
    "states it.\n"
    "Answer the user directly: no preamble such as \"Here's a reply\" or greeting. "
    "Put every command in its own fenced code block (```) starting at the beginning "
    "of a line, never inside a numbered list item. If the passages contain no command, "
    "do not write one: answer in plain sentences."
)


def _call(url: str, payload: dict[str, Any], timeout: float) -> tuple[str, dict[str, int]]:
    data = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("APHERIS_LOCAL_API_KEY")  # the optional auth the decision client sends
    if api_key:
        headers["authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read())
    content = str(body["choices"][0]["message"]["content"])
    usage = {k: int(v) for k, v in (body.get("usage") or {}).items() if isinstance(v, int)}
    # Some llamafile builds leak the end-of-turn token into the text.
    return content.replace("<|eot_id|>", "").strip(), usage


def section_payload(title: str, section: str, user_message: str) -> dict[str, Any]:
    """The chat-completions request for a question answered from one whole KB section."""
    return {
        "model": "local",
        "temperature": 0.2,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": (
                    f"User problem: {user_message}\n\nKnowledge base section '{title}':\n{section}"
                ),
            },
        ],
    }


async def phrase(
    title: str,
    section: str,
    user_message: str,
    url: str = DEFAULT_URL,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    """Rephrase a KB section into a reply via a llamafile server.

    Args:
        title: The KB section title.
        section: The KB section body (the only facts allowed in the reply).
        user_message: The user's original message.
        url: llamafile OpenAI-compatible chat-completions endpoint.
        timeout: Request timeout in seconds.

    Returns:
        The phrased reply, or the raw section if the server is unreachable.
    """
    text, _ = await phrase_payload(section_payload(title, section, user_message),
                                   f"{title}\n\n{section}", url=url, timeout=timeout)
    return text


def chunk_payload(user_message: str, chunks: list[Any]) -> dict[str, Any]:
    """The chat-completions request for a question answered from selected passages.

    Passages are grouped under their KB file's title, so an answer built from several
    files keeps each file's steps together. Nothing else (no earlier turn) is included:
    this payload is the whole context window.
    """
    by_file: dict[str, list[str]] = {}
    for c in chunks:
        by_file.setdefault(c.title, []).append(c.text)
    sections = "\n\n".join(
        f"### {title}\n" + "\n\n".join(texts) for title, texts in by_file.items()
    )
    return {
        "model": "local",
        "temperature": 0.2,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": f"User problem: {user_message}\n\nKnowledge base passages:\n{sections}",
            },
        ],
    }


async def phrase_payload(
    payload: dict[str, Any], fallback: str, url: str = DEFAULT_URL,
    timeout: float = DEFAULT_TIMEOUT,
) -> tuple[str, dict[str, int]]:
    """Send a prepared payload to the llamafile server.

    Returns the reply and the server's token `usage` (prompt/completion/total); on an
    unreachable server, `fallback` and no usage.
    """
    try:
        return await asyncio.to_thread(_call, url, payload, timeout)
    except (urllib.error.URLError, OSError, KeyError, ValueError):
        return fallback, {}
