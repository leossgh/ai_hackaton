from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import polars as pl

from abpipe import abtools
from abpipe.base import Context, Filter
from abpipe.registry import register

_SCRIPTS = {"de_novo": "check_denovo", "novel": "check_optimisation"}   # abguard class -> team script module

# The team scripts measure edit distance with a pure-Python dynamic program (about 10 s per design
# against the 768 provided antibodies). This wrapper runs the scripts' own code unchanged, after
# replacing only that distance function with rapidfuzz's Levenshtein, which has the same unit-cost
# definition. tests/test_pipeline_data.py checks the two agree on distances and on verdicts.
# It deliberately stays Levenshtein and not Hamming: Hamming is never smaller, so it could overstate the
# distance from a known antibody (a shifted loop) and let through a design the real abguard rejects.
_FAST = """
import importlib, sys
scripts_dir, module, *argv = sys.argv[1:]
sys.path.insert(0, scripts_dir)
import _track_common
from rapidfuzz.distance import Levenshtein
_track_common.levenshtein = Levenshtein.distance
mod = importlib.import_module(module)
sys.argv = [module + ".py", *argv]
raise SystemExit(mod.main())
"""


@register("filter", "track_check")
class TrackCheck(Filter):
    """Track assignment plus each track's extra rules, by running the team's scripts/check_*.py.

    A design passes only if it shows PASS in the script for the track abguard assigned it.
    fast_distance=True swaps the scripts' Python Levenshtein for an equivalent C++ one (needed
    beyond a few dozen candidates); use False to run the stock scripts, e.g. on a final shortlist.
    """

    version = "3"

    def __init__(self, provided: str = "her2-trastuzumab/trastuzumab_her2_spr_all_768.csv",
                 reference_db: str | None = None, fast_distance: bool = True, timeout_s: int = 3600,
                 scripts_dir: str | None = None):
        self.provided, self.reference_db = provided, reference_db
        self.fast_distance, self.timeout_s, self.scripts_dir = fast_distance, timeout_s, scripts_dir

    def _scripts(self, ctx: Context) -> Path:
        """Where check_*.py live. They moved from <repo>/scripts to <repo>/NICCOLO/scripts (commit f4d8da8)."""
        if self.scripts_dir:
            p = Path(self.scripts_dir)
            return p if p.is_absolute() else ctx.repo_root / p
        for rel in ("NICCOLO/scripts", "scripts"):
            if (ctx.repo_root / rel / "_track_common.py").exists():
                return ctx.repo_root / rel
        raise FileNotFoundError(f"check_*.py not found under {ctx.repo_root}/NICCOLO/scripts or /scripts; set scripts_dir")

    def _run(self, module: str, inp: Path, out: Path, ctx: Context, extra: list[str]) -> pl.DataFrame:
        scripts = self._scripts(ctx)
        args = [str(inp), "-o", str(out), *extra]
        if self.reference_db:
            args += ["--reference-db", self.reference_db]
        if self.fast_distance:
            cmd = [sys.executable, "-c", _FAST, str(scripts), module, *args]
        else:
            cmd = [sys.executable, str(scripts / f"{module}.py"), *args]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout_s, cwd=ctx.repo_root)
        if not out.exists():
            raise RuntimeError(f"{module} produced no report (exit {proc.returncode}):\n{proc.stderr[-1500:]}")
        return pl.read_csv(out, schema_overrides={"sequence_id": pl.String, "failures": pl.String})

    def check(self, df: pl.DataFrame, ctx: Context) -> pl.DataFrame:
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            inp = td / "designs.csv"
            abtools.submission_frame(df).write_csv(inp)
            rep = {"de_novo": self._run(_SCRIPTS["de_novo"], inp, td / "denovo.csv", ctx, []),
                   "novel": self._run(_SCRIPTS["novel"], inp, td / "optimisation.csv", ctx,
                                      ["--provided", str(ctx.data_dir / self.provided)])}
        by_track = {t: {r["sequence_id"]: r for r in d.iter_rows(named=True)} for t, d in rep.items()}
        ids, reasons, tracks, dist = [], [], [], []
        for sid in df["sequence_id"].to_list():
            row = by_track["novel"][sid]
            track = row["track_assigned"]
            ids.append(sid); tracks.append(track); dist.append(row["cdrh3_min_distance"])
            if track not in by_track:
                reasons.append("no track assigned (not numberable as an antibody?)")
                continue
            r = by_track[track][sid]
            reasons.append(None if r["passes"] else f"[{track} track] {r['failures'] or 'failed'}")
        return pl.DataFrame({"sequence_id": ids, "reason": reasons, "info__track": tracks,
                             "info__cdrh3_min_distance": dist},
                            schema={"sequence_id": pl.String, "reason": pl.String, "info__track": pl.String,
                                    "info__cdrh3_min_distance": pl.Int64})
