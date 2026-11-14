from __future__ import annotations

from collections import Counter

import polars as pl

from abpipe import abtools
from abpipe.base import Context, Filter
from abpipe.registry import register


@register("filter", "new_liabilities")
class NewLiabilities(Filter):
    """Reject variants that introduce more LAP liabilities than the parent already has (via abguard).

    Judged against the parent because trastuzumab itself carries high-severity liabilities,
    so an absolute rule would reject the molecule we are trying to improve.
    """

    version = "1"

    def __init__(self, severities: tuple = ("high",), regions: tuple | None = None,
                 max_new: int = 0, ignore_tags: tuple = ()):
        self.severities, self.max_new = set(severities), max_new
        self.regions = set(regions) if regions else None
        self.ignore_tags = set(ignore_tags)

    def _key_counts(self, hits) -> Counter:
        c = Counter()
        for h in hits or []:
            if h["severity"] not in self.severities or h["tag"] in self.ignore_tags:
                continue
            if self.regions is not None and h["region"] not in self.regions:
                continue
            c[(h["tag"], h["chain"], h["region"])] += 1
        return c

    def check(self, df: pl.DataFrame, ctx: Context) -> pl.DataFrame:
        parent = ctx.require_parent()
        probe = pl.DataFrame({"sequence_id": ["__parent__"], "kind": ["paired"], "heavy_sequence": [parent.heavy],
                              "light_sequence": [parent.light], "design_description": ["parent"]})
        both = pl.concat([abtools.submission_frame(df), probe])
        a = abtools.annotate_frame(both, liabilities=True, gate_novelty=False)
        hits = dict(zip(a["sequence_id"].to_list(), a["liabilities"].to_list()))
        base = self._key_counts(hits["__parent__"])
        ids, reasons, counts = [], [], []
        for sid in df["sequence_id"].to_list():
            new = self._key_counts(hits[sid]) - base            # Counter subtraction keeps positive excess only
            total = sum(new.values())
            ids.append(sid); counts.append(total)
            reasons.append(None if total <= self.max_new else
                           f"introduces {total} new {'/'.join(sorted(self.severities))} liabilities: "
                           + ", ".join(f"{t}@{ch}:{rg}" for (t, ch, rg) in sorted(new)))
        return pl.DataFrame({"sequence_id": ids, "reason": reasons, "info__n_new_liabilities": counts},
                            schema={"sequence_id": pl.String, "reason": pl.String, "info__n_new_liabilities": pl.Int64})
