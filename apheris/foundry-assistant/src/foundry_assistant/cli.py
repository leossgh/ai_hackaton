"""A terminal front-end for the assistant — the hackathon build (CLI only, no browser).

Zero-config: it reads the KB and backend from a couple of flags and the same environment
the console uses (APHERIS_LOCAL_BASE_URL / _PHRASE_URL), routes with the KB's routing.json,
and answers on the on-premises model. Each reply shows where it came from and what it cost,
so a grounded answer and an honest decline look different at a glance.

    uv run foundry-ask                                 # the foundry-v1 KB
    uv run foundry-ask --kb path/to/other/kb           # any OKF knowledge base
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from foundry_assistant.api import answer, build_backend, load_knowledge_base, load_routing
from foundry_assistant.blocks import build_blocks

ROUTE_STYLE = {"answer_from_kb": "green", "ask_followup": "yellow", "escalate": "red"}
_FENCE = re.compile(r"```\w*\n.*?```\n?", re.DOTALL)


def _cost(reply: Any) -> str:
    """Decision + phrasing tokens, when the server reported them (the console's figure)."""
    dec = reply.decision_usage.get("total_tokens", 0)
    phrase = reply.llm_usage.get("total_tokens", 0)
    if dec and phrase:
        return f"{dec + phrase:,} tokens (decisions {dec:,} + phrasing {phrase:,})"
    if dec:
        return f"{dec:,} tokens (decisions)"
    return "tokens not metered"


def _footer(reply: Any) -> Text:
    bits = [f"route: {reply.route}", f"scope {reply.scope:.2f}"]
    if reply.verify is not None:
        bits.append(f"verify {reply.verify:.2f}")
    bits.append(_cost(reply))
    return Text(" · ".join(bits), style="dim")


def _workflow(console: Console, kb: dict, files: list[str]) -> None:
    """Terminal version of the console's workflow diagram.

    Each page's ordered steps as a vertical flow (◦ = input/output note, ▸ = a task;
    optional steps are marked skippable).
    """
    for fid in files:
        node = kb.get(fid)
        steps = getattr(node, "steps", None) if node else None
        if not steps:
            continue
        console.print(f"[bold]workflow · {escape(node.title)}[/bold]")
        for i, st in enumerate(steps):
            mark = "◦" if st.get("io") else "▸"
            opt = " [dim](optional — may be skipped)[/dim]" if st.get("optional") else ""
            detail = f" — [dim]{escape(st.get('detail', ''))}[/dim]" if st.get("detail") else ""
            console.print(f"  {mark} [cyan]{escape(st['name'])}[/cyan]{opt}{detail}")
            if i < len(steps) - 1:
                console.print("  [dim]│[/dim]")
        console.print()


def _diagram_block(console: Console, dia: dict[str, Any]) -> None:
    """A diagram block as a vertical flow (◦ = input/output note, ▸ = a task)."""
    console.print(f"[bold]workflow · {escape(dia['title'])}[/bold]")
    nodes = dia["nodes"]
    for i, n in enumerate(nodes):
        mark = "◦" if n["kind"] == "io" else "▸"
        opt = " [dim](optional)[/dim]" if n["kind"] == "optional" else ""
        detail = f" — [dim]{escape(n['detail'])}[/dim]" if n.get("detail") else ""
        console.print(f"  {mark} [cyan]{escape(n['label'])}[/cyan]{opt}{detail}")
        if i < len(nodes) - 1:
            console.print("  [dim]│[/dim]")
    console.print()


def _sources_block(console: Console, src: dict[str, Any]) -> None:
    """The cited page, or the closest pages to open when the assistant declined."""
    if src["suggested"]:
        console.print("[dim]closest pages:[/dim]")
        for it in src["items"]:
            console.print(f"  [cyan]{escape(it['id'])}[/cyan]  {escape(it['title'])}")
        console.print("  [dim]open one with[/dim] /read <page-id>")
    else:
        ids = ", ".join(f"[cyan]{escape(it['id'])}[/cyan]" for it in src["items"])
        console.print(f"[dim]sources:[/dim] {ids}")


def _render(console: Console, reply: Any, kb: dict) -> None:
    """Render one reply as the shared blocks: prose, command tips, diagrams, sources.

    The same four block kinds the web widget shows, so the two front-ends read alike. Fenced
    code is lifted out of the prose into highlighted command tips, as the widget does.
    """
    style = ROUTE_STYLE.get(reply.route, "white")
    title = (reply.node_title or "answer") if reply.route == "answer_from_kb" else (
        "not sure" if reply.route == "ask_followup" else "escalate")
    for b in build_blocks(reply, kb):
        kind = b["kind"]
        if kind == "text":
            prose = _FENCE.sub("", b["markdown"]).strip()
            body = Markdown(prose) if reply.route == "answer_from_kb" else Text(prose)
            console.print(Panel(body, title=f"[bold]{escape(title)}[/bold]",
                                border_style=style, title_align="left"))
        elif kind == "command":
            console.print(Panel(
                Syntax(b["command"], b.get("lang") or "bash",
                       background_color="default", word_wrap=True),
                title="▸ run", border_style="cyan", title_align="left", padding=(0, 1)))
        elif kind == "diagram":
            _diagram_block(console, b)
        elif kind == "sources":
            _sources_block(console, b)
    console.print(_footer(reply))
    console.print()


async def _repl(args: argparse.Namespace) -> None:
    load_dotenv()
    console = Console()
    kb_dir = Path(args.kb)
    kb = load_knowledge_base(kb_dir)
    base_url = os.environ.get("APHERIS_LOCAL_BASE_URL") if args.backend == "apheris-local" else None
    phrase_url = os.environ.get("APHERIS_LOCAL_PHRASE_URL")
    gates_file = kb_dir.parent / "gates.json"
    client_cm, gates = build_backend(args.backend, gates_file if gates_file.exists() else None,
                                     base_url=base_url)
    routed_gates = load_routing(kb_dir, args.backend, kb)
    gates = routed_gates or gates
    refiner_cm = (build_backend(args.backend, base_url=base_url)[0] if args.refine
                  else contextlib.nullcontext())
    from foundry_assistant.api import ContextFiles
    context = ContextFiles.new() if args.refine else None

    console.print(Panel(
        Text.assemble(("Apheris Foundry assistant", "bold"),
                      (f"  ·  {args.backend}  ·  on-premises\n", "dim"),
                      (f"knowledge base: {kb_dir}  ·  {len(kb)} pages\n", "dim"),
                      ("ask a question — /read <id> to open a page, /help, /quit", "dim")),
        border_style="cyan"))

    async with client_cm as client, refiner_cm as refiner:
        conversation: list[str] = []
        if args.question:  # one-shot: `foundry-ask "how do I run a workflow?"` → answer and exit
            msg = " ".join(args.question)
            with console.status("thinking…"):
                reply = await answer(client, kb, msg, gates, conversation=[],
                                     phrase_url=phrase_url, refiner=refiner, context=context)
            _render(console, reply, kb)
            return
        while True:
            try:
                msg = console.input("[bold cyan]ask ▸ [/bold cyan]").strip()
            except (EOFError, KeyboardInterrupt):
                console.print("\nbye")
                return
            if not msg:
                continue
            if msg in ("/quit", "/q", "/exit", "quit", "exit", ":q"):
                return
            if msg == "/help":
                console.print("[dim]ask anything about the docs · /read <page-id> · /quit[/dim]")
                continue
            if msg.startswith("/read "):
                node = kb.get(msg[6:].strip())
                if node is None:
                    console.print("[red]no such page[/red]")
                else:
                    console.print(Panel(Markdown(node.body), title=node.title,
                                        border_style="blue", title_align="left"))
                    _workflow(console, kb, [node.id])
                continue
            # prior turns only, as the API sends them: the current message is already the
            # decision prompt's "User message", and repeating it in the history skews scope
            # (an off-topic question read in-scope 0.84 instead of 0.01)
            try:
                with console.status("thinking…"):
                    reply = await answer(client, kb, msg, gates, conversation=conversation,
                                         phrase_url=phrase_url, refiner=refiner, context=context)
            except Exception as exc:  # noqa: BLE001 - keep the session alive
                console.print(f"[red]{type(exc).__name__}: {exc}[/red]\n")
                continue
            conversation += [f"user: {msg}", f"assistant: [{reply.route}] {reply.node_title}"]
            _render(console, reply, kb)


def main() -> None:
    """Parse flags and run one question (if given) or the terminal REPL."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("question", nargs="*", help="ask one question and exit; omit for a session")
    ap.add_argument("--kb", default="kb/foundry-v1/kb", help="knowledge-base dir")
    ap.add_argument("--backend", default="apheris-local", help="decision backend")
    ap.add_argument("--no-refine", dest="refine", action="store_false",
                    help="skip passage selection + verify (faster, less grounded)")
    ap.set_defaults(refine=True)
    asyncio.run(_repl(ap.parse_args()))


if __name__ == "__main__":
    main()
