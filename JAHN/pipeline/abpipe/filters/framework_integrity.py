from __future__ import annotations

import polars as pl

from abpipe.base import Context, Filter
from abpipe.registry import register


@register("filter", "framework_integrity")
class FrameworkIntegrity(Filter):
    """Candidate equals the parent outside the mutable CDRH3 window (substitutions only), same light chain."""

    version = "1"

    def __init__(self, allow_light_changes: bool = False):
        self.allow_light_changes = allow_light_changes

    def check(self, df: pl.DataFrame, ctx: Context) -> pl.DataFrame:
        p = ctx.require_parent()
        s, e = p.window_start, p.window_start + len(p.window)
        h = pl.col("heavy_sequence")
        reason = (pl.when(h.str.len_chars() != len(p.heavy)).then(pl.lit("heavy length differs from the parent"))
                  .when((h.str.slice(0, s) != p.heavy[:s]) | (h.str.slice(e) != p.heavy[e:]))
                  .then(pl.lit("heavy framework changed outside the CDRH3 window")))
        if not self.allow_light_changes:
            reason = reason.when(pl.col("light_sequence").fill_null("") != p.light).then(pl.lit("light chain differs from the parent"))
        return df.select("sequence_id", reason=reason.otherwise(None))
