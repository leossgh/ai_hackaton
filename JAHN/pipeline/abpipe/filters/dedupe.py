from __future__ import annotations

import polars as pl

from abpipe import abtools
from abpipe.base import Context, Filter
from abpipe.distance import check_metric, nearest
from abpipe.registry import register


@register("filter", "dedupe")
class Dedupe(Filter):
    """Drop exact duplicates; optionally drop CDRH3s within min_cdrh3_distance edits of an earlier one.

    metric auto compares equal-length CDRH3s by Hamming and different lengths by Levenshtein.
    Greedy and order-dependent: it keeps whichever candidate comes first, so use the near-duplicate
    option only where order does not matter; diversity-aware selection belongs after ranking.
    """

    version = "2"

    def __init__(self, min_cdrh3_distance: int = 0, metric: str = "auto"):
        self.min_cdrh3_distance = min_cdrh3_distance
        self.metric = check_metric(metric)

    def check(self, df: pl.DataFrame, ctx: Context) -> pl.DataFrame:
        ids = df["sequence_id"].to_list()
        key = list(zip(df["heavy_sequence"].to_list(), df["light_sequence"].to_list()))
        first, reasons = {}, [None] * len(ids)
        for i, k in enumerate(key):
            if k in first:
                reasons[i] = f"exact duplicate of {ids[first[k]]}"
            else:
                first[k] = i
        if self.min_cdrh3_distance > 0:
            cdrh3 = abtools.annotate_frame(df)["cdrh3"].to_list()
            buckets: dict = {}
            for i, c3 in enumerate(cdrh3):
                if reasons[i] or c3 is None:
                    continue
                best = nearest(c3, buckets, self.metric)
                if best is not None and best[0] < self.min_cdrh3_distance:
                    reasons[i] = f"CDRH3 within {best[0]} edit(s) of {best[1]}"
                    continue
                seqs, kept = buckets.setdefault(len(c3), ([], []))
                seqs.append(c3); kept.append(ids[i])
        return pl.DataFrame({"sequence_id": ids, "reason": reasons}, schema={"sequence_id": pl.String, "reason": pl.String})
