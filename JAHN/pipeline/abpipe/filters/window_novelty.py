from __future__ import annotations

import polars as pl

from abpipe import _niccolo, novelty
from abpipe.base import Context, Filter
from abpipe.registry import register


@register("filter", "window_novelty")
class WindowNovelty(Filter):
    """Drop windows fewer than min_dist substitutions from any provided FACS/SPR window (fast, exact pre-screen).

    The optimisation track needs MORE than 2 point mutations from every provided data point, so min_dist = 3.
    This is the cheap, vectorised version of the rule for the 10-residue window; it can only reject designs the
    official Levenshtein check would also reject. track_check remains the authoritative verdict.
    info__window_min_dist: 0, 1, 2, or 3 (meaning 3 or more) substitutions from the nearest provided window.
    """

    version = "1"

    def __init__(self, min_dist: int = 3):
        if min_dist not in (0, 1, 2, 3):
            raise ValueError("min_dist must be 0, 1, 2 or 3")
        self.min_dist = min_dist

    def check(self, df: pl.DataFrame, ctx: Context) -> pl.DataFrame:
        parent = ctx.require_parent()
        wins = _niccolo.windows(df["heavy_sequence"].to_list(), parent)
        ok = [i for i, w in enumerate(wins) if w is not None]
        cls = [None] * len(wins)
        if ok:
            c = novelty.provided_index(ctx).distance_class(novelty.encode([wins[i] for i in ok]))
            for i, ci in zip(ok, c.tolist()):
                cls[i] = ci
        reasons = []
        for w, ci in zip(wins, cls):
            if w is None:
                reasons.append("CDRH3 window could not be read (framework length differs or non-standard residue)")
            else:
                reasons.append(None if ci >= self.min_dist else
                               f"CDRH3 window is {ci} substitution(s) from a provided window; needs >= {self.min_dist}")
        return pl.DataFrame({"sequence_id": df["sequence_id"], "reason": reasons, "info__window_min_dist": cls},
                            schema={"sequence_id": pl.String, "reason": pl.String, "info__window_min_dist": pl.Int64})
