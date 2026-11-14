"""Shared structural types for the decision pipeline.

The decision client is duck-typed: the local `JeffClient` satisfies
`DecisionClient` without a common base. The knowledge base is a loaded markdown tree.
"""

from __future__ import annotations

from typing import Any, Protocol, TypedDict

from .kb import Node

KB = dict[str, Node]  # page id -> page


class DecisionClient(Protocol):
    """A decision-model client the walk drives: anything with `system_one`."""

    async def system_one(self, state: Any, questions: Any) -> Any: ...


class DecisionClientCM(Protocol):
    """The async context manager `build_backend` returns; entering yields a client."""

    async def __aenter__(self) -> DecisionClient: ...
    async def __aexit__(self, *exc: object) -> bool | None: ...


class WalkStep(TypedDict, total=False):
    """One decision level's signals, read by the console by string key."""

    node: str
    chosen: str
    conf: float
    margin: float
    match_idx: int
    probs: dict[str, float]
    shortlist: list[str]
