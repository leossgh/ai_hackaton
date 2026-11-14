from __future__ import annotations

import polars as pl

from abpipe import abtools
from abpipe.base import Context, Filter
from abpipe.registry import register


@register("filter", "abguard_hard")
class AbguardHard(Filter):
    """abguard hard checks: numbering confidence, format, length, unpaired cysteines, unique ids."""

    version = "1"

    def check(self, df: pl.DataFrame, ctx: Context) -> pl.DataFrame:
        a = abtools.annotate_frame(df, liabilities=False, gate_novelty=False)
        return a.select(
            "sequence_id",
            reason=pl.when(pl.col("errors").list.len() > 0).then(pl.col("errors").list.join("; ")).otherwise(None),
            info__cdrh3=pl.col("cdrh3"))
