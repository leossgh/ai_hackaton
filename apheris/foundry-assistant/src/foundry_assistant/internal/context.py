"""The two temp files behind the LLM's context window.

  conversation.jsonl  the whole multi-turn chat, one JSON line per turn (question, reply,
                      route, the files and passages used, the verify score) — the record
                      of the session; the LLM is never fed from it.
  next_context.json   exactly what the LLM is sent for the current question: the system
                      prompt, the passages selected for it, and the question. Cleared and
                      rebuilt on every question, so no earlier turn leaks into the window.

Follow-ups are still understood: the decision models (walk, passage selection) see the
recent conversation; only the generative LLM's window is reset to the selected passages.
"""

from __future__ import annotations

import json
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(tempfile.gettempdir()) / "foundry_assistant"


class ContextFiles:
    """A session's conversation log and next-question context, under one temp folder."""

    def __init__(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        self.directory = directory
        self.conversation = directory / "conversation.jsonl"
        self.next_context = directory / "next_context.json"

    @classmethod
    def new(cls, session_id: str | None = None) -> ContextFiles:
        """A fresh session folder `$TMPDIR/foundry_assistant/<session id>/`."""
        return cls(ROOT / (session_id or uuid.uuid4().hex[:12]))

    def clear_next(self) -> None:
        """Empty the context window before a new question is answered."""
        self.next_context.write_text("{}\n")

    def write_next(self, payload: dict[str, Any]) -> None:
        """Record exactly what is about to be sent to the LLM."""
        self.next_context.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    def append_turn(self, record: dict[str, Any]) -> None:
        """Append one finished turn to the conversation log."""
        line = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), **record}
        with self.conversation.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

