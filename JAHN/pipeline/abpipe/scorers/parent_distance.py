from __future__ import annotations

import polars as pl

from abpipe.base import Context, Scorer
from abpipe.distance import check_metric, distance
from abpipe.registry import register


@register("scorer", "parent_distance")
class ParentDistance(Scorer):
    """Distance from the parent summed over both chains (lower is better).

    metric auto: Hamming (substituted positions) per chain when the length matches the parent's,
    Levenshtein when it does not. Deliberately simple: among measured SPR variants, fewer
    mutations from wild type separates binders from non-binders better than the FACS profile.
    """

    version = "2"
    outputs = {"score__parent_distance": "lower"}

    def __init__(self, metric: str = "auto"):
        self.metric = check_metric(metric)

    def score(self, df: pl.DataFrame, ctx: Context) -> pl.DataFrame:
        p = ctx.require_parent()
        out = []
        for h, l in zip(df["heavy_sequence"].to_list(), df["light_sequence"].to_list()):
            dh, dl = distance(h, p.heavy, self.metric), distance(l or "", p.light, self.metric)
            if dh is None or dl is None:
                raise ValueError("metric 'hamming' needs candidates the same length as the parent; use 'auto'")
            out.append(dh + dl)
        return pl.DataFrame({"sequence_id": df["sequence_id"], "score__parent_distance": pl.Series(out, dtype=pl.Float64)})
