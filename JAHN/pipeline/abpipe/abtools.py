"""Thin wrappers over abguard so modules do not each re-learn its API."""
from __future__ import annotations

import polars as pl

from abpipe.schema import REQUIRED


def submission_frame(df: pl.DataFrame) -> pl.DataFrame:
    """The five columns abguard expects; a missing light chain becomes an empty string."""
    return df.select(REQUIRED).with_columns(pl.col("light_sequence").fill_null(""))


def annotate_frame(df: pl.DataFrame, *, liabilities: bool = False, reference=None,
                   gate_novelty: bool = False) -> pl.DataFrame:
    """abguard.annotate on a candidate table. Nothing is filtered: every row comes back."""
    from abguard.annotate import annotate
    from abguard.config import PipelineConfig

    return annotate(submission_frame(df), PipelineConfig(), include_liabilities=liabilities,
                    reference=reference, gate_novelty=gate_novelty)
