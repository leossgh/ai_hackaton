"""Module contracts. A module is swappable because it only has to honour one of these."""
from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import polars as pl

INFO = "info__"
SCORE = "score__"


@dataclass(frozen=True)
class Parent:
    """The antibody being optimised (trastuzumab for this challenge)."""
    id: str
    heavy: str
    light: str
    cdrh3: str          # IMGT CDRH3 as numbered by abguard
    window: str         # the mutable segment inside the CDRH3 (the FACS 10-mer)
    window_start: int   # 0-based offset of the window in `heavy`


@dataclass
class Context:
    data_dir: Path
    repo_root: Path
    run_dir: Path
    cache_dir: Path
    seed: int = 0
    parent: Parent | None = None

    def require_parent(self) -> Parent:
        if self.parent is None:
            raise RuntimeError("this module needs a `parent:` section in the config")
        return self.parent


class Module:
    kind: ClassVar[str] = ""
    name: ClassVar[str] = ""
    version: ClassVar[str] = "1"
    cost_usd: float = 0.0   # modules that spend money (remote APIs) add to this

    def __init__(self, **params):
        if params:
            raise TypeError(f"{type(self).__name__} got unexpected parameters {sorted(params)}")

    @classmethod
    def summary(cls) -> str:
        doc = (cls.__doc__ or "").strip().splitlines()
        return doc[0] if doc else ""

    @classmethod
    def signature(cls) -> str:
        sig = inspect.signature(cls.__init__)
        params = [p for n, p in sig.parameters.items() if n != "self"]
        return "(" + ", ".join(str(p) for p in params) + ")"


class Generator(Module):
    """Produce candidates. Must return the canonical table with unique sequence_id values."""

    def generate(self, n: int, seed: int, ctx: Context) -> pl.DataFrame:
        raise NotImplementedError


class Filter(Module):
    """Judge candidates. Return one row per input: sequence_id, reason (null = pass).

    Extra columns named info__* are joined onto the surviving table. Whether a failing
    row is dropped or only flagged is the runner's decision (config `on_fail`).
    """

    def check(self, df: pl.DataFrame, ctx: Context) -> pl.DataFrame:
        raise NotImplementedError


class Scorer(Module):
    """Score candidates. `outputs` maps each score__* column to 'higher' or 'lower' (better)."""

    outputs: ClassVar[dict[str, str]] = {}

    def score(self, df: pl.DataFrame, ctx: Context) -> pl.DataFrame:
        raise NotImplementedError


class Aggregator(Module):
    """Combine score__* columns into rank_score (higher is better) and rank (1 is best)."""

    def combine(self, df: pl.DataFrame, directions: dict[str, str], ctx: Context) -> pl.DataFrame:
        raise NotImplementedError
