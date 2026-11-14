"""Turn a folder of Markdown documentation into a knowledge base the assistant can answer from.

The folder becomes a tree: subfolders are areas, `.md` files are pages, and each page's gloss
(the one line the router sees) is its frontmatter `description`, else its first paragraph. A
folder's `README.md` / `index.md` stands for the folder itself, so `workflows/predict/README.md`
is the page `workflows-predict`. Hidden folders and `node_modules` are skipped; `--exclude`
drops more (globs on the path inside the docs folder).

The output is a KB directory the assistant reads with `--kb <out>/kb`:

    <out>/kb/*.md        one OKF page per node (frontmatter + body)
    <out>/routing.json   which gates the local backend uses
    <out>/gates.json     those gates: permissive, gated on scope only

    foundry-assistant-kb ~/docs kb/mydocs
    foundry-assistant-kb ../foundry-toolkit kb/toolkit --exclude 'docs/*' --exclude '*/SKILL.md'

Glosses are generated; an author can sharpen them (and add `examples:`) in the page files
before going live — the router chooses between pages on their glosses.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
from pathlib import Path

import yaml

from .internal.kb import ROOT_ID, Node, _validate, load_kb

_GLOSS_CHARS = 300  # a page gloss; area glosses list their pages and are not capped
_INDEX = ("readme.md", "index.md")
_SKIP_DIRS = {"node_modules", "__pycache__"}
# Permissive gates (the walk chooses freely once the KB plausibly covers the message), as the
# shipped foundry-v1 KB uses with the 0.5B decision model.
_GATES_KEY = "apheris-local-0.5b-tail-shortlist"
_GATES = {"conf_floor": 0.0, "margin_floor": 0.0, "match_floor": 0, "scope_floor": 0.4}


def _slug(parts: tuple[str, ...]) -> str:
    return re.sub(r"[^a-z0-9]+", "-", "-".join(parts).lower()).strip("-")


def _title(name: str) -> str:
    return re.sub(r"[-_]+", " ", name).strip().capitalize()


def _clip(text: str, limit: int = _GLOSS_CHARS) -> str:
    """`text` cut to at most `limit` chars at a sentence end (else a word), never mid-word."""
    if len(text) <= limit:
        return text
    head = text[:limit]
    end = max(head.rfind(". "), head.rfind("? "), head.rfind("! "))
    if end + 1 >= limit // 2:  # a sentence end, unless it would drop over half the text
        return head[: end + 1]
    return head[: head.rfind(" ")].rstrip(",;:") + "…"


def _gloss(text: str) -> str:
    """First paragraph that is not a heading, a list, a table or a fence, on one line."""
    for block in re.split(r"\n\s*\n", text):
        block = " ".join(block.split())
        if block and not block.startswith(("#", "-", "*", "```", "|", "<")) \
                and not block[0].isdigit():
            return _clip(block)
    return ""


def _leaf_titles(kb: dict[str, Node], node_id: str) -> list[str]:
    node = kb[node_id]
    if not node.children:
        return [node.title]
    return [t for c in node.children for t in _leaf_titles(kb, c)]


def _page(path: Path, node_id: str, fallback_title: str) -> Node:
    text = path.read_text(errors="replace")
    meta: dict[str, object] = {}
    if text.startswith("---"):
        _, front, text = text.split("---", 2)
        meta = yaml.safe_load(front) or {}
    heading = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = str(meta.get("title") or (heading.group(1).strip() if heading else fallback_title))
    body = (text[: heading.start()] + text[heading.end():]) if heading else text
    body = body.strip()
    gloss = str(meta.get("description") or _gloss(body) or title)
    examples = [str(e) for e in (meta.get("examples") or [])]
    return Node(node_id, "article", title, gloss, body=body, examples=examples)


def docs_to_kb(docs: Path, exclude: list[str] | None = None,
               title: str | None = None) -> dict[str, Node]:
    """Read a docs folder into a validated KB tree (see the module docstring for the rules)."""
    docs = Path(docs)
    patterns = exclude or []
    kb: dict[str, Node] = {}

    def skipped(rel: Path) -> bool:
        return any(fnmatch.fnmatch(rel.as_posix(), p) or fnmatch.fnmatch(rel.name, p)
                   for p in patterns)

    def visit(folder: Path) -> list[str]:
        """Pages and areas directly under `folder`; returns their ids."""
        ids: list[str] = []
        rel_folder = folder.relative_to(docs)
        files = [e for e in sorted(folder.iterdir())
                 if e.is_file() and e.suffix.lower() == ".md" and not skipped(e.relative_to(docs))]
        index = next((e for e in files if e.name.lower() in _INDEX), None)
        for entry in files:
            if entry is index:
                continue
            node = _page(entry, _slug((*rel_folder.parts, entry.stem)), _title(entry.stem))
            kb[node.id] = node
            ids.append(node.id)
        for sub in sorted(e for e in folder.iterdir() if e.is_dir()):
            if sub.name.startswith(".") or sub.name in _SKIP_DIRS or skipped(sub.relative_to(docs)):
                continue
            ids += visit_area(sub)
        if index is not None:
            page_id = _slug(rel_folder.parts)
            if not page_id:  # the docs folder's own README
                page_id = "overview"
            elif ids:  # the folder has more pages: its README is the area's overview page
                page_id += "-overview"
            node = _page(index, page_id, _title(folder.name))
            kb[node.id] = node
            ids.insert(0, node.id)
        return ids

    def visit_area(folder: Path) -> list[str]:
        kids = visit(folder)
        if not kids:
            return []
        area_id = _slug(folder.relative_to(docs).parts)
        if len(kids) == 1 and kids[0] == area_id:  # only a README: the folder is that page
            return kids
        names = ", ".join(t.lower() for k in kids for t in _leaf_titles(kb, k))
        # The folder's index page (if any) carries an authored gloss; the router reads the area
        # on it, so prefer it over the generated page list.
        overview = kb.get(f"{area_id}-overview")
        gloss = overview.gloss if overview else f"{_title(folder.name)}: {names}."
        kb[area_id] = Node(area_id, "area", _title(folder.name), gloss, kids)
        return [area_id]

    top = visit(docs)
    if not top:
        raise SystemExit(f"no Markdown pages found under {docs}")
    name = title or _title(docs.resolve().name)
    kb[ROOT_ID] = Node(ROOT_ID, "root", name, f"Top of the {name} documentation.", top)
    _validate(kb)
    return kb


def write_kb(kb: dict[str, Node], out: Path) -> Path:
    """Write the KB to `out/kb/` plus its routing and gates; returns the `kb/` directory."""
    pages = Path(out) / "kb"
    pages.mkdir(parents=True, exist_ok=True)
    for old in pages.glob("*.md"):  # a re-run replaces the pages, it doesn't accumulate them
        old.unlink()
    for node in kb.values():
        meta: dict[str, object] = {
            "id": node.id, "type": node.type, "title": node.title, "gloss": node.gloss}
        if node.children:
            meta["children"] = node.children
        if node.examples:
            meta["examples"] = node.examples
        if node.steps:
            meta["steps"] = node.steps
        # JSON is valid YAML and quotes every string, so ids like "no" stay strings.
        front = "\n".join(f"{k}: {json.dumps(v)}" for k, v in meta.items())
        (pages / f"{node.id}.md").write_text(f"---\n{front}\n---\n\n{node.body}\n")
    (Path(out) / "routing.json").write_text(
        json.dumps({"apheris-local": {"gates": _GATES_KEY}}, indent=2) + "\n")
    (Path(out) / "gates.json").write_text(json.dumps({_GATES_KEY: _GATES}, indent=2) + "\n")
    return pages


def main(argv: list[str] | None = None) -> None:
    """`foundry-assistant-kb <docs-dir> <out-dir>`: convert Markdown docs into a KB."""
    ap = argparse.ArgumentParser(prog="foundry-assistant-kb", description=main.__doc__)
    ap.add_argument("docs", type=Path, help="folder of Markdown documentation")
    ap.add_argument("out", type=Path, help="KB folder to write (pages go to <out>/kb)")
    ap.add_argument("--exclude", action="append", default=[], metavar="GLOB",
                    help="skip paths matching GLOB (repeatable), e.g. 'docs/adr/*', 'SKILL.md'")
    ap.add_argument("--title", help="name of the documentation (default: the folder name)")
    args = ap.parse_args(argv)
    kb = docs_to_kb(args.docs, args.exclude, args.title)
    pages = write_kb(kb, args.out)
    load_kb(pages)  # what the assistant will read must load back
    leaves = sum(1 for n in kb.values() if not n.children)
    print(f"wrote {leaves} pages ({len(kb) - leaves - 1} areas) to {pages}\n"
          f"ask it:  make ask KB={pages} Q=\"…\"")


if __name__ == "__main__":
    main()
