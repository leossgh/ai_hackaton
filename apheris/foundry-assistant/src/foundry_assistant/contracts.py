"""Typed inter-component contracts for the support assistant.

Structured payloads are Pydantic models so other components can validate them
against a JSON Schema; bulk data (the KB) stays as files.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .internal._types import WalkStep


class Reply(BaseModel):
    """The assistant's answer to one user message."""

    question: str = Field(description="The user's message.")
    route: str = Field(description="answer_from_kb | escalate | ask_followup.")
    node_id: str = Field(description="KB node the walk stopped on.")
    node_title: str = Field(description="Title of that node.")
    body: str = Field(description="Reply text (phrased, or the raw KB section).")
    scope: float = Field(description="Scope-noul probability the KB covers the query.")
    trace: list[str] = Field(default_factory=list, description="Per-level walk trace.")
    steps: list[WalkStep] = Field(
        default_factory=list, description="Per-level signals of the final walk (for display)."
    )
    files: list[str] = Field(
        default_factory=list, description="KB files whose passages fed the reply (refined)."
    )
    chunks: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Every judged passage: file, id, relevance score, kept (refined).",
    )
    suggestions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="When not confident: closest KB/Q&A nodes to offer as links "
        "(node_id, title, score, body). Empty on a confident answer.",
    )
    verify: float | None = Field(
        default=None, description="Decision-model check that the reply answers the question."
    )
    attempts: int = Field(default=1, description="Walk + answer rounds until verified.")
    llm_usage: dict[str, int] = Field(
        default_factory=dict,
        description="Phrasing LLM tokens: prompt_tokens / completion_tokens / total_tokens.",
    )
    decision_usage: dict[str, int] = Field(
        default_factory=dict,
        description="Decision-model tokens summed over every system_one call "
        "(prompt_tokens / completion_tokens / total_tokens), when the server reports them.",
    )
    context_dir: str | None = Field(
        default=None, description="Folder holding conversation.jsonl and next_context.json."
    )
    blocks: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Ordered render blocks (text / command / diagram / sources) every "
        "front-end shows; filled by foundry_assistant.blocks.build_blocks at the API boundary.",
    )
