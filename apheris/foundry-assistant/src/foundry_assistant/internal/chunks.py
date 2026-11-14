"""Chunk-level grounding: split KB files into passages, keep the ones a question needs.

After the walk picks KB file(s), a second decision-model pass (a separate client, e.g.
JEV) judges every passage of every candidate file in one call — one question per
passage — and only the passages it keeps reach the phrasing LLM. A third pass checks
the LLM's reply against the question and those passages (`verify_reply`).

A question that spans several files ("predict a structure, then score it") is handled
by judging passages from several candidate files at once (`candidate_nodes`): files
with no kept passage simply drop out.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from typesafe_sdk import Noul, Score

from ._types import KB, DecisionClient
from .kb import Node

MAX_FILES = 5  # candidate files judged per question
TARGET_CHARS = 700  # blocks are packed into passages of about this size
MIN_CHARS = 250  # a heading starts a new passage once the current one is this long
MAX_CHUNKS = 40  # passages judged per call; more are pre-ranked lexically (BM25) first
SCORE_LEVELS = ["not useful", "marginally useful", "useful", "essential"]
_LINK = re.compile(r"\[\[([A-Za-z0-9_.-]+)\]\]")


@dataclass
class Chunk:
    """One passage of a KB file, and the relevance the decision model gave it."""

    id: str  # "<node id>#<index>"
    node_id: str
    title: str  # the file's title, shown with the passage
    text: str
    score: float = 0.0  # 0..1 relevance to the question
    kept: bool = False


def split_chunks(node: Node) -> list[Chunk]:
    """Split a KB body into passages.

    Splits at blank lines, keeps each heading with the block under it, and never splits a
    fenced code block.
    """
    blocks: list[str] = []
    current: list[str] = []
    fenced = False
    for line in node.body.splitlines():
        if line.strip().startswith("```"):
            fenced = not fenced
        if not line.strip() and not fenced:
            if current:
                blocks.append("\n".join(current))
                current = []
            continue
        current.append(line)
    if current:
        blocks.append("\n".join(current))

    merged: list[str] = []
    pending = ""  # headings wait for the block under them
    for block in blocks:
        if all(line.lstrip().startswith("#") for line in block.splitlines()):
            pending = f"{pending}\n{block}".strip()
            continue
        merged.append(f"{pending}\n{block}".strip() if pending else block)
        pending = ""
    if pending and merged:
        merged[-1] = f"{merged[-1]}\n{pending}"

    # Long doc pages split into hundreds of tiny blocks: pack neighbours into passages of
    # about TARGET_CHARS, starting afresh at a heading once the passage has some substance.
    pieces: list[str] = []
    for block in merged:  # a table or long code block with no blank line: cut at lines
        if len(block) <= 3 * TARGET_CHARS:
            pieces.append(block)
            continue
        part: list[str] = []
        lines = [ln[i:i + TARGET_CHARS] for ln in block.splitlines()
                 for i in range(0, max(len(ln), 1), TARGET_CHARS)]
        for line in lines:
            if part and sum(len(x) + 1 for x in part) + len(line) > TARGET_CHARS:
                pieces.append("\n".join(part))
                part = []
            part.append(line)
        if part:
            pieces.append("\n".join(part))

    packed: list[str] = []
    for block in pieces:
        if packed and len(packed[-1]) + len(block) <= TARGET_CHARS and not (
            block.lstrip().startswith("#") and len(packed[-1]) >= MIN_CHARS
        ):
            packed[-1] = f"{packed[-1]}\n\n{block}"
        else:
            packed.append(block)
    return [Chunk(f"{node.id}#{i}", node.id, node.title, text) for i, text in enumerate(packed)]


def linked_ids(node: Node) -> list[str]:
    """KB files a body links to with `[[id]]`, in order."""
    return list(dict.fromkeys(_LINK.findall(node.body)))


def candidate_nodes(
    kb: KB,
    primary: str,
    alternatives: list[str],
    *,
    exclude: frozenset[str] = frozenset(),
    follow_links: bool = True,
    limit: int = MAX_FILES,
) -> list[str]:
    """Files whose passages are judged for one question.

    The walk's leaf, the beam's other leaves, then the files the leaf links to — leaves
    only, deduplicated, minus `exclude`, at most `limit`.
    """
    ids = [primary, *alternatives, *(linked_ids(kb[primary]) if follow_links else [])]
    out = [i for i in dict.fromkeys(ids) if i in kb and not kb[i].children and i not in exclude]
    return out[:limit]


def closest_nodes(
    kb: KB,
    question: str,
    *,
    alternatives: list[str] | tuple[str, ...] = (),
    exclude: frozenset[str] = frozenset(),
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Closest answerable nodes to offer as links when the walk can't confidently answer.

    Ranks every leaf by BM25 over its title + body + sample questions (so both the KB text
    and the Q&A examples count), seeds the walk's own beam `alternatives` first, drops
    `exclude` (files already tried), and returns at most `limit` as {node_id, title, score,
    body} for the UI to render as in-app links.
    """
    from .bm25 import BM25

    if not isinstance(kb, dict):  # suggestions rank every leaf; only the markdown tree enumerates
        return []
    leaves = [n for n in kb.values() if not n.children and n.id not in exclude]
    if not leaves:
        return []
    sims = BM25([f"{n.title} {n.body} {' '.join(n.examples)}" for n in leaves])(question)
    score = {n.id: s for n, s in zip(leaves, sims, strict=True)}
    seeded = [i for i in dict.fromkeys(alternatives) if i in score]
    ranked = seeded + sorted((i for i in score if i not in seeded),
                             key=lambda i: score[i], reverse=True)
    return [{"node_id": i, "title": kb[i].title, "score": round(score[i], 3), "body": kb[i].body}
            for i in ranked[:limit]]


async def score_chunks(
    client: DecisionClient,
    question: str,
    conversation: list[str],
    chunks: list[Chunk],
    *,
    mode: str = "noul",
    floor: float = 0.5,
    max_chunks: int = MAX_CHUNKS,
) -> list[Chunk]:
    """Score the chunks for the question in one call and mark those at or above `floor` kept.

    When there are more than `max_chunks`, only the lexically closest that many are judged
    (the rest stay unkept) — this bounds the decision prompt, which dominates latency on CPU.
    mode "noul": a yes/no probability "is this passage needed?"; mode "score": a 4-level
    usefulness rating scaled to 0..1. The best judged chunk is always kept, so a reply is never
    built from nothing. Mutates each Chunk's `kept`/`score` in place and returns the same list
    in its original order.
    """
    if not chunks:
        return chunks
    judged = chunks
    if len(chunks) > max_chunks:  # too many for one call: judge the lexically closest
        from .bm25 import BM25

        sims = BM25([f"{c.title} {c.text}" for c in chunks])(question)
        top = sorted(range(len(chunks)), key=lambda i: -sims[i])[:max_chunks]
        judged = [chunks[i] for i in sorted(top)]
    pid = {c.id: f"p{i}" for i, c in enumerate(judged)}
    state = {
        "user_message": question,
        "conversation": conversation,
        "passages": {pid[c.id]: f"[{c.title}] {c.text}" for c in judged},
    }
    if mode == "noul":
        questions: dict[str, Any] = {
            pid[c.id]: Noul(instructions=f"Is passage {pid[c.id]} needed to answer the "
                                         "user's question?")
            for c in judged
        }
    elif mode == "score":
        questions = {
            pid[c.id]: Score(instructions=f"How useful is passage {pid[c.id]} for answering "
                                          "the user's question?", criteria=SCORE_LEVELS)
            for c in judged
        }
    else:
        raise ValueError(f"unknown chunk mode {mode!r}")
    response = await client.system_one(state=state, questions=questions)
    for c in judged:
        if mode == "noul":
            c.score = float(response.nouls[pid[c.id]].noul)
        else:
            c.score = float(response.scores[pid[c.id]].score) / (len(SCORE_LEVELS) - 1)
        c.kept = c.score >= floor
    best = max(judged, key=lambda c: c.score)
    best.kept = True
    return chunks


async def verify_reply(
    client: DecisionClient, question: str, reply: str, chunks: list[Chunk],
) -> float:
    """Probability that `reply` answers `question` correctly, grounded in `chunks`."""
    response = await client.system_one(
        state={
            "user_message": question,
            "reply": reply,
            "passages": {f"p{i}": f"[{c.title}] {c.text}" for i, c in enumerate(chunks)},
        },
        questions={
            "verified": Noul(
                instructions="Does the reply make sense and correctly answer the user's "
                             "question — doing the task the user asked for, not a related "
                             "one — using only facts from the passages?",
            ),
        },
    )
    return float(response.nouls["verified"].noul)


def unsupported_commands(reply: str, source: str) -> list[str]:
    """`--flags` and `apheris…` commands in the reply's code that `source` never mentions.

    A deterministic check for the phrasing model's worst failure: writing a plausible
    command (`apheris-foundry jobs logs`) that the passages do not contain.
    """
    code = " ".join(re.findall(r"```.*?```|`[^`\n]+`", reply, flags=re.S))
    found = set(re.findall(r"--[a-z][\w-]*", code))
    found |= {m.group(0) for m in re.finditer(r"\bapheris(?:-[\w]+)?(?: [a-z][\w-]*){1,2}", code)}
    return sorted(t for t in found if t not in source)
