"""Organiser data used by more than one module: the FACS table and the parent antibody."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import polars as pl

from abpipe import abtools
from abpipe.base import Context, Parent

_FACS_ZIP = "her2-trastuzumab/tz_her2_facs_3classes_524346.csv.zip"
_memo: dict[str, pl.DataFrame] = {}


def facs_table(ctx: Context) -> pl.DataFrame:
    """CDRH3 window, binding_class (high/medium/low) and edit_distance for 524,346 variants."""
    path = ctx.cache_dir / "facs.parquet"
    key = str(path)
    if key in _memo:
        return _memo[key]
    if path.exists():
        df = pl.read_parquet(path)
    else:
        z = zipfile.ZipFile(ctx.data_dir / _FACS_ZIP)
        member = next(n for n in z.namelist() if n.endswith(".csv") and not n.startswith("__MACOSX"))
        df = pl.read_csv(io.BytesIO(z.read(member))).select("cdrh3", "binding_class", "edit_distance")
        ctx.cache_dir.mkdir(parents=True, exist_ok=True)
        df.write_parquet(path)
    _memo[key] = df
    return df


def load_parent(spec: dict, data_dir: Path) -> Parent:
    """Find the wild-type row in an organiser table.

    A row is wild type when abguard numbers its CDRH3 as trastuzumab's. All such rows
    must share one heavy and one light sequence, and the table's own `window_column`
    value must occur exactly once in the heavy chain.
    """
    from abguard.novelty import trastuzumab_cdrh3

    table = pl.read_csv(data_dir / spec["table"])
    probe = table.select(
        sequence_id=pl.format("row_{}", pl.int_range(pl.len())),
        kind=pl.lit("paired"), heavy_sequence="vh_sequence", light_sequence="vl_sequence",
        design_description=pl.lit("parent probe"))
    numbered = abtools.annotate_frame(probe)
    wt_cdrh3 = trastuzumab_cdrh3() if callable(trastuzumab_cdrh3) else trastuzumab_cdrh3
    idx = numbered.with_row_index("i").filter(pl.col("cdrh3") == wt_cdrh3)["i"].to_list()
    if not idx:
        raise ValueError(f"no row in {spec['table']} has CDRH3 {wt_cdrh3}")
    rows = table[idx]
    if rows["vh_sequence"].n_unique() != 1 or rows["vl_sequence"].n_unique() != 1:
        raise ValueError("wild-type rows disagree on the heavy or light sequence")
    heavy, light = rows["vh_sequence"][0], rows["vl_sequence"][0]
    window = rows[spec.get("window_column", "cdrh3")][0]
    if heavy.count(window) != 1:
        raise ValueError(f"window {window!r} occurs {heavy.count(window)} times in the heavy chain")
    return Parent(id=spec.get("id", "parent"), heavy=heavy, light=light, cdrh3=wt_cdrh3,
                  window=window, window_start=heavy.index(window))
