"""Public API: typed functions with explicit parameters and no config access.

This is the component's library surface; the terminal client calls these.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import Reply
from .internal import backends
from .internal._types import KB, DecisionClient, DecisionClientCM
from .internal.chunks import (
    Chunk,
    candidate_nodes,
    closest_nodes,
    score_chunks,
    split_chunks,
    unsupported_commands,
    verify_reply,
)
from .internal.context import ContextFiles
from .internal.kb import Node, load_kb
from .internal.phrase import (
    chunk_payload,
    phrase_payload,
    section_payload,
)
from .internal.walk import (
    Gates,
    WalkResult,
    beam_search,
    shortlist_walk,
)

STRICTER = 0.15  # the narrowing retry raises the passage floor by this much

_FOLLOWUP = (
    "I need a bit more detail. Can you describe exactly what happened and any "
    "error message you saw?"
)

_OUT_OF_SCOPE = (
    "I'm the Apheris Foundry assistant, so I can only help with Foundry — running and "
    "troubleshooting workflows, models, jobs and the CLI. Ask me something about those "
    "and I'll point you to the right page."
)

def load_knowledge_base(kb_dir: Path) -> dict[str, Node]:
    """Load and validate the OKF knowledge base from a directory."""
    return load_kb(kb_dir)


def load_routing(
    kb_dir: Path, backend: str, kb: dict[str, Node],
) -> Gates | None:
    """A KB's fitted gates for a backend, or None to keep the caller's.

    Read from `routing.json` next to the KB (`{"<backend>": {"gates": "<gates.json key>"}}`).
    """
    path = kb_dir.parent / "routing.json"
    entry = json.loads(path.read_text()).get(backend, {}) if path.exists() else {}
    gates = (backends.gates_for(entry["gates"], kb_dir.parent / "gates.json")
             if "gates" in entry else None)
    return gates


def build_backend(
    backend: str,
    gates_file: Path | None = None,
    *,
    base_url: str | None = None,
    model: str | None = None,
) -> tuple[DecisionClientCM, Gates]:
    """Build the decision client and its gates for a backend.

    Args:
        backend: Backend name (apheris-local).
        gates_file: Optional JSON file of fitted gates.
        base_url: apheris-local's server URL.
        model: The model name apheris-local reports.

    Returns:
        Tuple of (async client context manager, Gates).
    """
    return backends.make_client(backend, gates_file, base_url=base_url, model=model)


async def answer(
    client: DecisionClient,
    kb: KB,
    question: str,
    gates: Gates,
    *,
    conversation: list[str] | None = None,
    phrase_url: str | None = None,
    root_id: str = "root",
    refiner: DecisionClient | None = None,
    context: ContextFiles | None = None,
    chunk_mode: str = "noul",
    chunk_floor: float = 0.5,
    verify_floor: float = 0.5,
    max_attempts: int = 3,
    max_chunks: int = 8,
) -> Reply:
    """Route one question through the KB walk and build a reply.

    With a `refiner` (a decision client for passages and verification) the reply is grounded passage by
    passage: candidate KB files (walk leaf, beam alternatives, linked files) are split into
    passages, the refiner keeps those the question needs, the LLM sees only those, and the
    refiner then verifies the LLM's reply — on failure the files used are excluded and the
    walk runs again, up to `max_attempts`. See `_refined`.

    Args:
        client: An async decision client from `build_backend`.
        kb: The loaded knowledge base.
        question: The user's message.
        gates: Descent thresholds for this backend.
        conversation: Prior turns, oldest first.
        phrase_url: llamafile endpoint; if set, answers are phrased, else raw.
        root_id: Node the walk starts from.
        refiner: Decision client for passage selection and reply verification; None keeps
            the plain path (whole KB section to the LLM, no verification).
        context: Temp files for the conversation log and the LLM's next context window.
        chunk_mode: "noul" (yes/no probability, the default: best on the foundry
            suites) or "score" (4-level usefulness).
        chunk_floor: Relevance (0..1) a passage needs to be kept.
        verify_floor: Verification probability a reply needs to go through.
        max_attempts: Walk + answer rounds before giving up with a follow-up.
        max_chunks: Passages judged per selection call (BM25 pre-ranks to this many); lower is
            faster on CPU, where the decision prompt dominates latency.

    Returns:
        A `Reply` describing the route, the KB node, and the reply text.
    """
    conversation = conversation or []
    if refiner is not None:
        return await _refined(
            client, refiner, kb, question, gates, conversation, phrase_url, root_id,
            context, chunk_mode, chunk_floor, verify_floor, max_attempts, max_chunks,
        )
    result = await _route(client, kb, question, conversation, root_id, gates)
    # When the walk stops without reaching an answer (followup, or an escalate because it
    # knew the area but not the specific), offer the stop node's own topics so a broad
    # question ("how do I use X?") gets the map to steer by, not a canned ask or handoff.
    topics = [kb[c].title for c in result.node.children] if result.route != "answer_from_kb" else []
    out_of_scope = result.route != "answer_from_kb" and result.scope < gates.scope_floor
    body, usage = await _body(result, question, phrase_url, topics, out_of_scope)
    suggestions = ([] if result.route == "answer_from_kb"
                   else closest_nodes(kb, question, alternatives=result.alternatives))
    return Reply(
        question=question,
        route=result.route,
        node_id=result.node.id,
        node_title=result.node.title,
        body=body,
        scope=result.scope,
        trace=result.trace,
        steps=result.steps,
        llm_usage=usage,
        decision_usage=_decision_usage(client),
        suggestions=suggestions,
    )


def _decision_usage(*clients: Any) -> dict[str, int]:
    """Decision tokens summed over the clients that reported any (empty when none did)."""
    total: dict[str, int] = {}
    for c in clients:
        for k, v in (getattr(c, "decision_usage", None) or {}).items():
            total[k] = total.get(k, 0) + int(v)
    return total


async def _route(
    client: DecisionClient, kb: KB, question: str, conversation: list[str], root_id: str,
    gates: Gates, exclude: frozenset[str] = frozenset(),
) -> WalkResult:
    """BM25 shortlists the pages, the decision model picks one."""
    return await shortlist_walk(client, kb, question, conversation, root_id=root_id, gates=gates,
                         exclude=exclude)


async def _body(
    result: WalkResult, question: str, phrase_url: str | None, topics: list[str] | None = None,
    out_of_scope: bool = False,
) -> tuple[str, dict[str, int]]:
    """The reply text, and the phrasing LLM's token usage (empty when it was not used)."""
    if result.route == "answer_from_kb":
        raw = f"{result.node.title}\n\n{result.node.body}"
        if phrase_url:
            payload = section_payload(result.node.title, result.node.body, question)
            return await phrase_payload(payload, raw, url=phrase_url)
        return raw, {}
    if out_of_scope:  # scope gate failed: a short, polite redirect, not the whole topic map
        return _OUT_OF_SCOPE, {}
    if topics:
        # Stopped at a node with sub-topics (at the root, or an area deeper in): show them
        # so a broad question gets the map to narrow by, whatever the route.
        listed = "\n".join(f"- {t}" for t in topics)
        return (
            f"I can help with {result.node.title.lower()} — tell me which of these, or add "
            f"a line about what you're trying to do:\n{listed}"
        ), {}
    if result.route == "escalate":
        return f"This needs a human agent ({result.node.title}). Escalating your ticket now.", {}
    return _FOLLOWUP, {}


def _grouped(chunks: list[Chunk]) -> str:
    """Kept passages as plain text, grouped under their file's title (the no-LLM reply)."""
    by_file: dict[str, list[str]] = {}
    for c in chunks:
        by_file.setdefault(c.title, []).append(c.text)
    return "\n\n".join(f"{title}\n\n" + "\n\n".join(t) for title, t in by_file.items())


async def _refined(
    client: DecisionClient,
    refiner: DecisionClient,
    kb: KB,
    question: str,
    gates: Gates,
    conversation: list[str],
    phrase_url: str | None,
    root_id: str,
    context: ContextFiles | None,
    chunk_mode: str,
    chunk_floor: float,
    verify_floor: float,
    max_attempts: int,
    max_chunks: int,
) -> Reply:
    """Walk → passages → select (A) → fresh context (B) → phrase → verify (C), looping."""
    context = context or ContextFiles.new()
    recent = conversation[-6:]  # the decision models resolve follow-ups; the LLM does not
    exclude: frozenset[str] = frozenset()
    tried: list[str] = []
    history: list[str] = []  # one line per attempt, carried into the final trace
    result: WalkResult | None = None
    narrowed: list[Chunk] | None = None  # retry with only the strongest passages
    chunks: list[Chunk] = []
    for attempt in range(1, max_attempts + 1):
        context.clear_next()  # B: every question starts from an empty context window
        if narrowed is not None:
            used, narrowed = narrowed, None
        else:
            result = await _route(client, kb, question, recent, root_id, gates, exclude)
            used = []
        assert result is not None
        if not used and result.route != "answer_from_kb":
            if result.steps and result.node.children:
                # The walk got into the KB but stopped at an area on a gate — typically a
                # question spanning two of its topics ("task vs workflow"). Search that
                # subtree and answer if a passage is genuinely relevant (verify still checks).
                chunks = await _gather(client, refiner, kb, question, recent, result.node.id,
                                       None, exclude, chunk_mode, chunk_floor, max_chunks)
                if any(c.score >= chunk_floor for c in chunks):
                    used = [c for c in chunks if c.kept]
                    history.append(f"attempt {attempt}: walk stopped at {result.node.id}; "
                                   "searched its subtree")
        if not used and result.route != "answer_from_kb":
            if attempt == 1:  # out of scope / too vague: the usual follow-up or handoff
                topics = [kb[c].title for c in result.node.children]
                out_of_scope = result.scope < gates.scope_floor
                body, _ = await _body(result, question, None, topics, out_of_scope)
                return _log(context, Reply(
                    question=question, route=result.route, node_id=result.node.id,
                    node_title=result.node.title, body=body, scope=result.scope,
                    trace=result.trace, steps=result.steps, context_dir=str(context.directory),
                    decision_usage=_decision_usage(client, refiner),
                    suggestions=closest_nodes(kb, question, alternatives=result.alternatives),
                ))
            break  # no file left to try
        if not used:  # a fresh walk: gather candidate files and select their passages (A)
            chunks = await _gather(client, refiner, kb, question, recent, root_id,
                                   result.node.id, exclude, chunk_mode, chunk_floor, max_chunks)
            used = [c for c in chunks if c.kept]
        payload = chunk_payload(question, used)
        context.write_next(payload)
        verified: float | None = None
        usage: dict[str, int] = {}
        if phrase_url:
            body, usage = await phrase_payload(payload, _grouped(used), url=phrase_url)
            # a command/flag the passages do not contain is invented (the small phrasing
            # model's most frequent hard error). The passages themselves were selected for this
            # question, so answer with them verbatim rather than drop the file and retry — a
            # retry walks away from the right page and can land on a wrong one that verifies.
            invented = unsupported_commands(body, " ".join(c.text for c in used))
            if invented:
                body = _grouped(used)
                history.append(f"attempt {attempt}: reply used commands not in the passages "
                               f"({', '.join(invented)}); answered with the passages")
            else:
                verified = await verify_reply(refiner, question, body, used)  # C
        else:
            body = _grouped(used)  # no LLM: the selected passages are the answer
        used_files = list(dict.fromkeys(c.node_id for c in used))
        tried += used_files
        history.append(f"attempt {attempt}: files {used_files}"
                       + (f" verify={verified:.2f}" if verified is not None else ""))
        # answered from an area's subtree: name the files actually used, not the area
        title = (" + ".join(kb[f].title for f in used_files) if result.node.children
                 else result.node.title)
        reply = Reply(
            question=question, route="answer_from_kb", node_id=result.node.id,
            node_title=title, body=body, scope=result.scope,
            trace=[*result.trace, *history],
            steps=result.steps, files=used_files,
            chunks=[{"file": c.node_id, "id": c.id, "score": round(c.score, 3),
                     "kept": c in used, "text": c.text} for c in chunks],
            verify=verified, attempts=attempt, llm_usage=usage,
            decision_usage=_decision_usage(client, refiner),
            context_dir=str(context.directory),
        )
        if verified is None or verified >= verify_floor:
            return _log(context, reply)
        # First retry: the same files, only their strongest passages (weak ones from a
        # neighbouring file are what lead the LLM astray; a real second topic scores high
        # and stays). If that drops nothing, loop back to different files.
        strict = [c for c in used if c.score >= chunk_floor + STRICTER] or [
            max(used, key=lambda c: c.score)]
        if len(strict) < len(used):
            narrowed = strict
            history.append(f"retry {attempt + 1}: strongest passages only "
                           f"(relevance >= {chunk_floor + STRICTER:.2f})")
        else:
            exclude = exclude | set(used_files)

    titles = [kb[f].title for f in dict.fromkeys(tried)]
    last = [{"file": c.node_id, "id": c.id, "score": round(c.score, 3), "kept": c.kept,
             "text": c.text} for c in chunks]  # what the final attempt judged, for display
    return _log(context, Reply(
        question=question, route="ask_followup", node_id=root_id,
        node_title=kb[root_id].title,
        body="I couldn't put together an answer I'm confident in from the knowledge base. "
             "Could you rephrase, or add a line about what you're trying to do?"
             + ("\nI looked in:\n" + "\n".join(f"- {t}" for t in titles) if titles else ""),
        scope=result.scope if result else 0.0, trace=history, chunks=last,
        attempts=max_attempts, context_dir=str(context.directory),
        decision_usage=_decision_usage(client, refiner),
        suggestions=closest_nodes(
            kb, question,
            alternatives=result.alternatives if result else (),
            exclude=frozenset(tried),  # the files we already tried and couldn't verify
        ),
    ))


async def _gather(
    client: DecisionClient,
    refiner: DecisionClient,
    kb: KB,
    question: str,
    recent: list[str],
    start_id: str,
    primary: str | None,
    exclude: frozenset[str],
    chunk_mode: str,
    chunk_floor: float,
    max_chunks: int,
) -> list[Chunk]:
    """Candidate files under `start_id`, split into passages and scored for the question.

    The files are `primary` (else the beam's best leaf), the beam's other leaves, and the
    files they link to.
    """
    beam = await beam_search(client, kb, question, recent, root_id=start_id, beam_width=3,
                             exclude=exclude)
    files = candidate_nodes(kb, primary or beam.node.id, beam.alternatives, exclude=exclude)
    chunks = [c for f in files for c in split_chunks(kb[f])]
    await score_chunks(refiner, question, recent, chunks, mode=chunk_mode, floor=chunk_floor,
                       max_chunks=max_chunks)
    return chunks


def _log(context: ContextFiles, reply: Reply) -> Reply:
    context.append_turn({
        "question": reply.question, "route": reply.route, "node": reply.node_id,
        "files": reply.files, "verify": reply.verify, "attempts": reply.attempts,
        "kept": [{"id": c["id"], "score": c["score"]} for c in reply.chunks if c["kept"]],
        "reply": reply.body,
    })
    return reply
