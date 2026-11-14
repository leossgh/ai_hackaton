"""Routing a question to a KB page with the decision model.

A scope `Noul` first asks whether the KB covers the problem at all; out-of-scope or vague
queries bail to `ask_followup` instead of over-committing to a page. Then `shortlist_walk`
lets BM25 shortlist the pages and one `Choice` (with a `Score` for fit) picks among them,
descending only if the gates pass:

  * choice confidence >= conf_floor, margin (top1 - top2) >= margin_floor
  * topic match score >= match_floor

`beam_search` gathers the candidate files whose passages the answer is built from.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

from typesafe_sdk import Choice, Noul, Score

from ._types import KB, DecisionClient, WalkStep
from .kb import Node, children

MATCH_LEVELS = ["no match", "weak", "moderate", "strong"]


@dataclass(frozen=True)
class Gates:
    """Descent thresholds for the walk.

    Defaults suit JEV's calibrated confidence; local backends with different
    calibration pass their own (see backends.py).
    """

    conf_floor: float = 0.6  # Choice confidence below this is untrustworthy
    margin_floor: float = 0.15  # top1 - top2; stops near-tie coin-flip picks
    match_floor: int = 2  # index into MATCH_LEVELS; "moderate" to descend
    scope_floor: float = 0.5  # scope Noul below this: KB does not cover query


DEFAULT_GATES = Gates()


@dataclass
class WalkResult:
    route: str  # answer_from_kb | escalate | ask_followup
    node: Node  # final node reached (a leaf for answer_from_kb/escalate)
    trace: list[str] = field(default_factory=list)
    scope: float = 1.0  # scope Noul value (1.0 if no scope call was made)
    steps: list[WalkStep] = field(default_factory=list)  # per-level signals
    alternatives: list[str] = field(default_factory=list)  # beam: other leaves, best first


def blocked_ids(kb: KB, root_id: str, exclude: frozenset[str]) -> frozenset[str]:
    """`exclude` plus every area whose whole subtree is excluded (nothing left to reach)."""
    if not exclude:
        return exclude
    out = set(exclude)

    def dead(node_id: str) -> bool:
        node = kb[node_id]
        if node_id in out:
            return True
        if node.children and all([dead(c) for c in node.children]):
            out.add(node_id)
            return True
        return False

    dead(root_id)
    return frozenset(out)


def _margin(probabilities: dict[str, float]) -> float:
    ranked = sorted(probabilities.values(), reverse=True)
    return ranked[0] - (ranked[1] if len(ranked) > 1 else 0.0)


async def _scope(client: DecisionClient, kb: KB, root: Node, user_message: str,
                 conversation: list[str]) -> float:
    """Scope pre-gate: can the KB cover this at all? (the `in_scope` Noul over the areas)."""
    scope = await client.system_one(
        state={
            "user_message": user_message,
            "conversation": conversation,
            "topics": {a.id: a.gloss for a in children(kb, root)},
        },
        questions={
            "in_scope": Noul(
                instructions="Is the user's problem covered by one of the listed support topics?",
            ),
        },
    )
    return float(scope.nouls["in_scope"].noul)


SHORTLIST_K = 8  # BM25 top-8 holds the right page for ~98% of answerable apheris questions


def _leaves(kb: KB, node_id: str, skip: frozenset[str]) -> list[Node]:
    node = kb[node_id]
    if node_id in skip:
        return []
    if not node.children:
        return [node]
    return [leaf for c in node.children for leaf in _leaves(kb, c, skip)]


_WORDS = re.compile(r"[a-z0-9]+")


def _named_workflow(pages: list[Node], user_message: str) -> Node | None:
    """The workflow page the message names by its id words ("rfd4 finetune"), if exactly one.

    A workflow page id is `workflows-<words>`; a page is named when at least two of its words
    appear in the message, and it is used only when no other page matches as many. "Fine-tune"
    is folded to the id's `finetune`. Other pages (CLI, getting started) are left to the walk.
    """
    text = re.sub(r"fine[\s-]?tun\w*", "finetune", user_message.lower())
    said = set(_WORDS.findall(text))
    hits = []
    for p in pages:
        if p.id.startswith("workflows-"):
            words = set(p.id[len("workflows-"):].split("-"))
            hits.append((len(words & said), p))
    if not hits:
        return None
    hits.sort(key=lambda h: -h[0])
    best = hits[0][0]
    if best < 2 or (len(hits) > 1 and hits[1][0] == best):
        return None
    return hits[0][1]


async def shortlist_walk(
    client: DecisionClient,
    kb: KB,
    user_message: str,
    conversation: list[str],
    root_id: str = "root",
    gates: Gates = DEFAULT_GATES,
    k: int = SHORTLIST_K,
    exclude: frozenset[str] = frozenset(),
) -> WalkResult:
    """Retrieve, then choose: BM25 shortlists `k` pages, one Choice picks among them.

    A deep tree makes the decision model right at every level in a row (a 4-level walk at
    0.8 per step reaches the right page about 40% of the time); here it makes one choice,
    between pages that already match the question's words. The shortlist's other pages, best first,
    come back as `alternatives` for passage gathering and the suggestions list.
    """
    from .bm25 import BM25  # zero-dependency lexical ranker

    root = kb[root_id]
    skip = blocked_ids(kb, root_id, exclude)
    trace: list[str] = []
    steps: list[WalkStep] = []
    in_scope = await _scope(client, kb, root, user_message, conversation)
    trace.append(f"scope: in_scope={in_scope:.2f}")
    if in_scope < gates.scope_floor:
        return WalkResult("ask_followup", root, trace, scope=in_scope, steps=steps)

    pages = _leaves(kb, root_id, skip)
    if not pages:
        trace.append(f"{root_id}: every page excluded")
        return WalkResult("ask_followup", root, trace, scope=in_scope, steps=steps)
    named = _named_workflow(pages, user_message)
    if named is not None:  # the user named the workflow: don't let a near sibling win the choice
        trace.append(f"named workflow: {named.id}")
        route = "escalate" if named.requires_human else "answer_from_kb"
        return WalkResult(route, named, trace, scope=in_scope, steps=steps)
    sims = BM25([f"{p.title} {p.body} {' '.join(p.examples)}" for p in pages])(user_message)
    shortlist = [pages[i] for i in sorted(range(len(pages)), key=lambda i: -sims[i])[:k]]
    trace.append(f"shortlist: {[p.id for p in shortlist]}")
    if len(shortlist) == 1:
        page = shortlist[0]
        route = "escalate" if page.requires_human else "answer_from_kb"
        return WalkResult(route, page, trace, scope=in_scope, steps=steps)

    response = await client.system_one(
        state={"user_message": user_message, "conversation": conversation,
               "current_topic": root.title},
        questions={
            "choose": Choice(
                instructions="Which page best answers the user's problem?",
                criteria={p.id: p.gloss for p in shortlist},
            ),
            "match": Score(
                instructions=f"How well does the user's problem fit the topic '{root.title}'?",
                criteria=MATCH_LEVELS,
            ),
        },
    )
    choose = response.choices["choose"]
    probs = dict(choose.probabilities)
    margin = _margin(probs)
    match_idx = max(0, min(len(MATCH_LEVELS) - 1, round(response.scores["match"].score)))
    steps.append({"node": root_id, "chosen": choose.choice, "conf": choose.confidence,
                  "margin": margin, "match_idx": match_idx, "probs": probs,
                  "shortlist": [p.id for p in shortlist]})
    trace.append(f"{root_id}: chose={choose.choice} conf={choose.confidence:.2f} "
                 f"margin={margin:.2f} match={MATCH_LEVELS[match_idx]}")
    alternatives = [i for i in sorted(probs, key=lambda i: -probs[i]) if i != choose.choice]
    if not (choose.confidence >= gates.conf_floor and margin >= gates.margin_floor
            and match_idx >= gates.match_floor):
        return WalkResult("ask_followup", root, trace, scope=in_scope, steps=steps,
                          alternatives=[choose.choice, *alternatives])
    page = kb[choose.choice]
    route = "escalate" if page.requires_human else "answer_from_kb"
    return WalkResult(route, page, trace, scope=in_scope, steps=steps,
                      alternatives=alternatives)


async def beam_search(
    client: DecisionClient,
    kb: KB,
    user_message: str,
    conversation: list[str],
    *,
    root_id: str = "root",
    beam_width: int = 3,
    max_depth: int = 6,
    exclude: frozenset[str] = frozenset(),
) -> WalkResult:
    """Beam search over the Choice distributions to the best leaf.

    Keeps `beam_width` paths, expands each frontier node's children with one Choice,
    and ranks paths by the length-normalized geometric mean of their edge
    probabilities (`exp(mean(log p))`; singleton levels don't count). Deeper evidence can repair an ambiguous early pick, and there
    is no scope/match gate — it descends to a leaf. Only the Choice distribution is
    used, so every backend (decision or retrieval) works.

    The other leaves left in the final beam are returned as `alternatives` (best first):
    candidates for a question that spans more than one KB file. Nodes in `exclude` are
    never offered.
    """
    skip = blocked_ids(kb, root_id, exclude)
    paths: list[dict[str, Any]] = [
        {"logprob": 0.0, "decisions": 0, "score": 1.0, "leaf": root_id,
         "done": False, "steps": []}
    ]
    for _ in range(max_depth):
        if all(p["done"] for p in paths):
            break
        expanded: list[dict[str, Any]] = []
        for p in paths:
            if p["done"]:
                expanded.append(p)
                continue
            node = kb[p["leaf"]]
            kids = [k for k in children(kb, node) if k.id not in skip]
            if not kids and node.children:  # dead end: every branch excluded, drop the path
                continue
            if not kids:
                p["done"] = True
                expanded.append(p)
                continue
            if len(kids) == 1:  # forced step: no decision, probability unchanged
                child = kids[0]
                expanded.append({
                    **p, "leaf": child.id,
                    "steps": p["steps"] + [{"node": node.id, "chosen": child.id,
                                            "conf": 1.0, "margin": 0.0, "match_idx": -1,
                                            "probs": {child.id: 1.0}}],
                })
                continue
            response = await client.system_one(
                state={
                    "user_message": user_message,
                    "conversation": conversation,
                    "current_topic": node.title,
                },
                questions={
                    "choose": Choice(
                        instructions="Which branch best matches the user's problem?",
                        criteria={k.id: k.gloss for k in kids},
                    ),
                },
            )
            choose = response.choices["choose"]
            probs = choose.probabilities
            margin = _margin(probs)
            ranked = sorted(kids, key=lambda c: probs.get(c.id, 0.0), reverse=True)
            for child in ranked[:beam_width]:
                prob = probs.get(child.id, 0.0)
                logprob = p["logprob"] + math.log(max(prob, 1e-9))
                decisions = p["decisions"] + 1
                expanded.append({
                    "logprob": logprob, "decisions": decisions,
                    "score": math.exp(logprob / decisions), "leaf": child.id, "done": False,
                    "steps": p["steps"] + [{"node": node.id, "chosen": child.id,
                                            "conf": prob, "margin": margin, "match_idx": -1,
                                            "probs": dict(probs)}],
                })
        if not expanded:  # every path hit an excluded dead end
            return WalkResult("ask_followup", kb[root_id], ["beam: every branch excluded"])
        paths = sorted(expanded, key=lambda p: p["score"], reverse=True)[:beam_width]

    best = max(paths, key=lambda p: p["score"])
    node = kb[best["leaf"]]
    trace = [f"{s['node']}: chose={s['chosen']} p={s['conf']:.2f}" for s in best["steps"]]
    trace.append(f"beam score={best['score']:.2f} (width={beam_width}, depth<={max_depth})")
    route = "escalate" if node.requires_human else "answer_from_kb"
    others = [p["leaf"] for p in sorted(paths, key=lambda p: -p["score"])
              if p is not best and not kb[p["leaf"]].children]
    return WalkResult(route, node, trace, scope=1.0, steps=best["steps"],
                      alternatives=list(dict.fromkeys(others)))
