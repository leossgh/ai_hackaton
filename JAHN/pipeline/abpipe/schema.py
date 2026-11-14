"""The one table every module reads and writes.

The first five columns are abguard's submission columns, so any stage's output can be
handed straight to abguard. Everything else is optional provenance or module output:
  info__*   annotations a filter wants to keep (e.g. info__track)
  flag__*   a filter run with on_fail: flag leaves its reason here instead of dropping
  score__*  scorer outputs
  rank__*, rank_score, rank   aggregator outputs
"""
from __future__ import annotations

import hashlib
import io

import polars as pl

REQUIRED = ["sequence_id", "kind", "heavy_sequence", "light_sequence", "design_description"]
OPTIONAL = {"parent_id": pl.String, "origin": pl.String, "seed": pl.Int64, "meta": pl.String}
KINDS = ("paired", "vhh", "scfv")


class SchemaError(ValueError):
    pass


def validate(df: pl.DataFrame, where: str = "table") -> pl.DataFrame:
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise SchemaError(f"{where}: missing required columns {missing}")
    dup = df.filter(pl.col("sequence_id").is_duplicated())["sequence_id"].unique().to_list()
    if dup:
        raise SchemaError(f"{where}: duplicate sequence_id values, e.g. {dup[:3]}")
    if df["sequence_id"].null_count():
        raise SchemaError(f"{where}: null sequence_id")
    bad = df.filter(~pl.col("kind").is_in(list(KINDS)))
    if bad.height:
        raise SchemaError(f"{where}: kind must be one of {KINDS}, got {bad['kind'].unique().to_list()[:3]}")
    empty = df.filter(pl.col("heavy_sequence").is_null() | (pl.col("heavy_sequence") == ""))
    if empty.height:
        raise SchemaError(f"{where}: empty heavy_sequence for {empty['sequence_id'].to_list()[:3]}")
    return df


def with_optional(df: pl.DataFrame) -> pl.DataFrame:
    add = [pl.lit(None, dtype=t).alias(c) for c, t in OPTIONAL.items() if c not in df.columns]
    return df.with_columns(add) if add else df


def content_hash(df: pl.DataFrame, columns: list[str] | None = None) -> str:
    """Stable hash of a table's content, used for cache keys."""
    cols = columns if columns is not None else sorted(df.columns)
    buf = io.BytesIO()
    df.select(cols).write_ipc(buf)
    return hashlib.sha256(buf.getvalue()).hexdigest()[:16]
