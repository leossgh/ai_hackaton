from __future__ import annotations

import numpy as np
import polars as pl

from abpipe.base import Aggregator, Context
from abpipe.registry import register


def _cols(df, directions, columns):
    cols = list(columns) if columns else list(directions)
    if not cols:
        raise ValueError("no score columns to rank on; add a scorer")
    bad = [c for c in cols if c not in directions or c not in df.columns]
    if bad:
        raise ValueError(f"unknown score columns {bad}; available {sorted(directions)}")
    return cols


def _ranks(df, directions, cols) -> dict:
    """Per-column rank, 1 = best. Missing values rank worst."""
    n = df.height
    return {c: df[c].rank(method="average", descending=(directions[c] == "higher")).fill_null(float(n)).to_numpy()
            for c in cols}


def _finish(df, cols, ranks, rank_score) -> pl.DataFrame:
    extra = [pl.Series("rank_score", rank_score)] + [pl.Series("rank__" + c.removeprefix("score__"), ranks[c]) for c in cols]
    out = df.with_columns(extra).sort(["rank_score", "sequence_id"], descending=[True, False])
    return out.with_row_index("rank", offset=1)


@register("aggregator", "borda")
class Borda(Aggregator):
    """Mean of per-score ranks (lower mean rank is better). Scale-free; weights optional."""

    version = "1"

    def __init__(self, columns: tuple | None = None, weights: dict | None = None):
        self.columns, self.weights = columns, weights or {}

    def combine(self, df, directions, ctx: Context):
        cols = _cols(df, directions, self.columns)
        r = _ranks(df, directions, cols)
        w = np.array([float(self.weights.get(c, 1.0)) for c in cols])
        mean_rank = sum(wi * r[c] for wi, c in zip(w, cols)) / w.sum()
        return _finish(df, cols, r, -mean_rank)


@register("aggregator", "weighted_sum")
class WeightedSum(Aggregator):
    """Weighted sum of per-score percentiles in [0, 1] (1 is best). Weights default to equal."""

    version = "1"

    def __init__(self, columns: tuple | None = None, weights: dict | None = None):
        self.columns, self.weights = columns, weights or {}

    def combine(self, df, directions, ctx: Context):
        cols = _cols(df, directions, self.columns)
        unknown = [c for c in self.weights if c not in cols]
        if unknown:
            raise ValueError(f"weights for unknown score columns {unknown}")
        n = df.height
        r = _ranks(df, directions, cols)
        pct = {c: (1.0 - (r[c] - 1.0) / (n - 1.0)) if n > 1 else np.ones(n) for c in cols}
        w = np.array([float(self.weights.get(c, 1.0)) for c in cols])
        return _finish(df, cols, r, sum(wi * pct[c] for wi, c in zip(w, cols)) / w.sum())


@register("aggregator", "pareto")
class Pareto(Aggregator):
    """Non-dominated sorting: front 1 is best; ties within a front broken by mean rank."""

    version = "1"

    def __init__(self, columns: tuple | None = None, block: int = 512):
        self.columns, self.block = columns, block

    def combine(self, df, directions, ctx: Context):
        cols = _cols(df, directions, self.columns)
        r = _ranks(df, directions, cols)
        V = -np.column_stack([r[c] for c in cols])               # higher is better
        n = len(V)
        front, remaining, f = np.full(n, -1), np.arange(n), 0
        while remaining.size:
            sub = V[remaining]
            dominated = np.zeros(len(sub), dtype=bool)
            for lo in range(0, len(sub), self.block):
                blk = sub[lo:lo + self.block]
                ge = (sub[None, :, :] >= blk[:, None, :]).all(axis=2)
                gt = (sub[None, :, :] > blk[:, None, :]).any(axis=2)
                dominated[lo:lo + self.block] = (ge & gt).any(axis=1)
            front[remaining[~dominated]] = f
            remaining, f = remaining[dominated], f + 1
        mean_rank = np.column_stack([r[c] for c in cols]).mean(axis=1)
        return _finish(df, cols, r, -(front + 1) - mean_rank / (n + 1.0))
