"""The decision prompt format the decision adapter was trained on, and its answer readout.

Copied verbatim from the training repo (`training/models.py` render_decision and
`training/serve_fused.py` _answer) so the server ships without the training code. The prompt
text must match training exactly — change it there and re-copy, never edit it only here.

Every app decision (`Choice`/`Score`/`Noul`) is "pick one of N labelled options": the options
are listed with two-digit codes and the server reads the next-token probability of each code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def code(i: int) -> str:
    """The two-digit option code the model emits (00, 01, …)."""
    return f"{i:02d}"


@dataclass
class DecisionPrompt:
    """One rendered decision: the user content, the ordered option codes, and the labels."""

    content: str
    option_ids: list[str]  # the caller's ids/labels, in code order
    kind: str  # "choice" | "noul" | "score"
    key: str  # the question key in the app's request (choose / match / in_scope / …)


def render_decision(state: dict, key: str, question: dict, layout: str = "head") -> DecisionPrompt:
    """Render one app `system_one` question into the uniform option-code prompt.

    `question` is `{"type", "instructions", "criteria"?}` as the backends wire it
    (see internal/jeff_backend.py). `criteria` is the options (a dict id->gloss for a
    choice, a list for a score); a noul has none and becomes no / yes.

    `layout` "head" puts the instructions first (what gold4 and earlier were trained on);
    "tail" puts the state first, so the questions of one call (same state) share a prompt
    prefix the server keeps cached, and only the instructions + options are new per question.
    """
    qtype = question["type"]
    if qtype == "noul":
        options, ids = ["no", "yes"], ["no", "yes"]
    elif qtype == "score":
        options = list(question["criteria"])
        ids = options
    else:  # choice
        crit = question["criteria"]
        ids = list(crit)
        options = [str(crit[i]) for i in ids]
    instructions = [question["instructions"], ""]
    lines = [] if layout == "tail" else list(instructions)
    ctx = _context(state)
    if ctx:
        lines += [ctx, ""]
    if layout == "tail":
        lines += instructions
    lines.append("Options:")
    lines += [f"{code(i)} {opt}" for i, opt in enumerate(options)]
    lines += ["", "Reply with the option code only."]
    return DecisionPrompt("\n".join(lines), ids, qtype, key)


def _context(state: dict) -> str:
    """The parts of the app's `state` that belong in the prompt body."""
    out = []
    if state.get("current_topic"):
        out.append(f"Current topic: {state['current_topic']}")
    if state.get("user_message"):
        out.append(f"User message: {state['user_message']}")
    if state.get("reply"):
        out.append(f"Reply to judge:\n{state['reply']}")
    for name in ("topics", "passages"):
        if state.get(name):
            joined = "\n".join(f"- {k}: {v}" for k, v in state[name].items())
            out.append(f"{name.capitalize()}:\n{joined}")
    convo = state.get("conversation") or []
    if convo:
        out.append("Conversation so far:\n" + "\n".join(convo[-6:]))
    return "\n\n".join(out)


def answer(p: Any, probs: list[float]) -> dict:
    """Map the option-code probabilities back to the app's answer shape."""
    best = max(range(len(probs)), key=lambda i: probs[i])
    if p.kind == "noul":  # render_decision orders noul as [no, yes]
        return {"type": "noul", "noul": probs[p.option_ids.index("yes")]}
    if p.kind == "score":
        return {"type": "score", "score": sum(i * pr for i, pr in enumerate(probs)),
                "confidence": probs[best]}
    return {"type": "choice", "choice": p.option_ids[best], "confidence": probs[best],
            "probabilities": dict(zip(p.option_ids, probs, strict=True))}
