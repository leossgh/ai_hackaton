"""The shared answer format every front-end renders.

A `Reply` carries prose, commands and workflow steps in several fields; a terminal, a web
widget and an agent should all show the *same* answer. `build_blocks` turns one reply into an
ordered list of typed blocks so each front-end only has to render four shapes, not re-derive
them. The blocks, in order:

* ``text``     — the reply prose as markdown (``{"kind": "text", "markdown": str}``).
* ``command``  — one copyable CLI command pulled from a fenced code block
  (``{"kind": "command", "command": str, "lang": str}``).
* ``diagram``  — a cited page's ordered workflow steps as a small DAG
  (``{"kind": "diagram", "title": str, "nodes": [...], "edges": [...]}``).
* ``sources``  — cited pages and closest suggestions as links
  (``{"kind": "sources", "items": [{"id", "title"}], "suggested": bool}``).

Diagrams come from a KB page's ``steps``.
"""

from __future__ import annotations

import re
import textwrap
from typing import Any

from .internal._types import KB
from .internal.kb import Node

_FENCE = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
# fenced blocks in these languages are shown as copyable command tips
_COMMAND_LANGS = {"", "bash", "sh", "shell", "console", "text"}


def _commands(body: str) -> list[dict[str, Any]]:
    """Fenced shell/CLI blocks in the reply, each as a copyable command tip."""
    out: list[dict[str, Any]] = []
    for lang, code in _FENCE.findall(body):
        if lang.lower() not in _COMMAND_LANGS:
            continue
        # KB fences often sit indented under a list item; dedent the common indent so the
        # command reads (and copies) flush, while keeping any continuation-line indentation.
        command = textwrap.dedent(code).strip()
        if command:
            out.append({"kind": "command", "command": command, "lang": lang.lower() or "sh"})
    return out


def _diagram(node: Node) -> dict[str, Any] | None:
    """A page's ordered steps as a node/edge DAG (inputs/outputs are notes, tasks are steps).

    The chain is linear; an optional step also gets a dashed ``skip`` edge past it, mirroring
    the console's workflow flowchart.
    """
    steps = node.steps
    if not steps:
        return None
    nodes = [
        {"id": f"s{i}", "label": s["name"], "detail": s.get("detail", ""),
         "kind": "io" if s.get("io") else "optional" if s.get("optional") else "task"}
        for i, s in enumerate(steps)
    ]
    edges = [{"from": f"s{i}", "to": f"s{i + 1}"} for i in range(len(steps) - 1)]
    for i in range(len(steps) - 1):
        if steps[i + 1].get("optional") and i + 2 < len(steps):
            edges.append({"from": f"s{i}", "to": f"s{i + 2}", "label": "skip"})
    return {"kind": "diagram", "title": node.title, "nodes": nodes, "edges": edges}


def build_blocks(reply: Any, kb: KB) -> list[dict[str, Any]]:
    """Ordered render blocks for one reply: prose, command tips, diagrams, sources."""
    blocks: list[dict[str, Any]] = [{"kind": "text", "markdown": reply.body}]
    blocks += _commands(reply.body)

    if isinstance(kb, dict):
        cited = reply.files or ([reply.node_id] if reply.route == "answer_from_kb" else [])
        for fid in cited:
            node = kb.get(fid)
            if node is not None:
                diagram = _diagram(node)
                if diagram is not None:
                    blocks.append(diagram)

    items = ([{"id": reply.node_id, "title": reply.node_title}]
             if reply.route == "answer_from_kb" and reply.node_id
             else [{"id": s["node_id"], "title": s["title"]} for s in reply.suggestions])
    if items:
        blocks.append({"kind": "sources", "items": items,
                       "suggested": reply.route != "answer_from_kb"})
    return blocks
