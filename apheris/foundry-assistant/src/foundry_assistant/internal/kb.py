"""OKF knowledge base: markdown + YAML frontmatter nodes forming a topic tree.

Edges are the `children` ids in frontmatter. The walk (walk.py) descends this
tree using a decision model as the branch selector.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from ._types import KB

ROOT_ID = "root"


@dataclass
class Node:
    id: str
    type: str  # root | area | article
    title: str
    gloss: str  # one-line option text the branch selector sees
    children: list[str] = field(default_factory=list)
    requires_human: bool = False
    body: str = ""
    examples: list[str] = field(default_factory=list)  # sample user messages for this node
    # Ordered workflow steps ({name, detail, optional?, io?}) drawn as a diagram in the UI.
    steps: list[dict[str, Any]] = field(default_factory=list)


def _parse(path: Path) -> Node:
    raw = path.read_text()
    _, frontmatter, body = raw.split("---", 2)
    meta = yaml.safe_load(frontmatter)
    return Node(
        id=meta["id"],
        type=meta["type"],
        title=meta["title"],
        gloss=meta["gloss"],
        children=meta.get("children", []),
        requires_human=bool(meta.get("requires_human", False)),
        body=body.strip(),
        examples=list(meta.get("examples", [])),
        steps=list(meta.get("steps", [])),
    )


def load_kb(kb_dir: Path) -> dict[str, Node]:
    """Load and validate the OKF knowledge base.

    Args:
        kb_dir: Directory of OKF markdown files.

    Returns:
        Mapping of node id to Node.
    """
    kb = {}
    for path in sorted(Path(kb_dir).glob("*.md")):
        node = _parse(path)
        kb[node.id] = node
    _validate(kb)
    return kb


def _validate(kb: dict[str, Node]) -> None:
    if ROOT_ID not in kb:
        raise ValueError(f"KB has no '{ROOT_ID}' node")
    for node in kb.values():
        for child in node.children:
            if child not in kb:
                raise ValueError(f"{node.id} links to missing child '{child}'")


def children(kb: KB, node: Node) -> list[Node]:
    return [kb[c] for c in node.children]
