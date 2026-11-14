from __future__ import annotations

import polars as pl

from abpipe import _niccolo
from abpipe.base import Context, Filter
from abpipe.registry import register


@register("filter", "prefilter_gate")
class PrefilterGate(Filter):
    """Keep variants whose P(measurable KD) is at least min_p_binder (step 2 of the cascade in NICCOLO/eda/AGENT_GUIDE.md).

    There is no calibrated threshold: pick it from how many designs you can afford downstream. 0.8 is the value
    his generate-and-screen script used. Rows the pre-filter cannot score are rejected, not passed.
    """

    version = "1"

    def __init__(self, min_p_binder: float = 0.8, eda_dir: str = _niccolo.EDA_REL, splits_dir: str | None = None,
                 spr_csv: str = _niccolo.SPR_REL):
        if not 0.0 <= min_p_binder <= 1.0:
            raise ValueError("min_p_binder must be in [0, 1]")
        self.min_p_binder, self.eda_dir, self.splits_dir, self.spr_csv = min_p_binder, eda_dir, splits_dir, spr_csv
        self.version = f"1+{_niccolo.quick_tag(eda_dir)}"

    def check(self, df: pl.DataFrame, ctx: Context) -> pl.DataFrame:
        fit = _niccolo.get_prefilter(data_dir=ctx.data_dir, cache_dir=ctx.cache_dir, repo_root=ctx.repo_root,
                                     eda_dir=self.eda_dir, splits_dir=self.splits_dir, spr_csv=self.spr_csv)
        parent = ctx.require_parent()
        _niccolo.check_parent(parent, fit)
        wins = _niccolo.windows(df["heavy_sequence"].to_list(), parent)
        p = _niccolo.score_windows(fit, wins)["p_binder"]
        reasons = []
        for w, pi in zip(wins, p):
            if w is None:
                reasons.append("CDRH3 window not scorable by the pre-filter (framework changed or non-standard residue)")
            else:
                reasons.append(None if pi >= self.min_p_binder else f"p_binder {pi:.2f} < {self.min_p_binder:g}")
        return pl.DataFrame({"sequence_id": df["sequence_id"], "reason": reasons},
                            schema={"sequence_id": pl.String, "reason": pl.String})
