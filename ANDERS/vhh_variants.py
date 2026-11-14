#!/usr/bin/env python3
"""vhh_variants.py — generate de-novo-track trastuzumab VHH variants from a scored/ranked list.

Takes a ranked list of VHH (or VH-bearing) sequences plus a score column, generates
variants by four score-aware strategies, pre-screens them against the de novo gate
with safety margins, and writes a submission-format table that is then verified with
the official NICCOLO/scripts/check_denovo.py.

What the gate measures (measured by NICCOLO on this VM, see ../NICCOLO/denovo/GATE_NOTES.md):
  * identity to trastuzumab is a pooled Levenshtein ratio over the immunum IMGT Fv;
    for a VHH only the heavy chain counts; de novo needs < 0.70 strictly.
  * CDRH3 must be >= 2 Levenshtein edits from every one of the 610,109 reference
    loops (trastuzumab's own CDRH3 is one of them).
  * shared hard checks: canonical AAs, length <= 250, no unpaired cysteines,
    numbering confidence >= 0.1, exactly one domain for a VHH, unique ids.

Margins used here (same as ../NICCOLO/denovo/gate.py): identity <= 0.62 and CDRH3
>= 4 edits from trastuzumab and from the whole reference set, so a variant that
clears the pre-screen still clears the official gate after a re-numbering or a
reference refresh.

Usage:
  vhh_variants.py generate RANKED.csv -o OUTDIR [options]
  vhh_variants.py demo OUTDIR [--n-parents 12] [--seed 1]
  vhh_variants.py check DESIGNS.csv -o REPORT.csv

RANKED.csv needs columns sequence_id, heavy_sequence (a VHH sequence; a paired or
scFv row contributes its heavy-chain CDRs only) and, optionally, a score column.
Score auto-detection looks for: score, rank_score, demo_score, iptm, binder_plddt,
min_ipae, pred_log10_kd, p_binder. min_ipae and pred_log10_kd are treated as
lower-is-better; everything else as higher-is-better. With no score column, input
order is the rank order. The score is used ONLY to pick parents and to build the
CDR position matrix — it is inherited by variants as a prior, never as evidence.

Run it with the interpreter that has abguard, e.g.
  /home/hackathon/.venvs/abguard/bin/python ANDERS/vhh_variants.py ...
(it re-execs itself there if started elsewhere, like NICCOLO/scripts/_track_common.py).
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import shutil
import subprocess
import sys
import tempfile
from glob import glob
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CHECKER = REPO / "NICCOLO" / "scripts" / "check_denovo.py"

TRASTUZUMAB_CDRH3 = "SRWGGDGFYAMDY"
IDENTITY_CAP = 0.70           # official: must be strictly below this
OFFICIAL_CDRH3_DIST_MIN = 2   # official de novo floor
INTERNAL_IDENTITY_MAX = 0.62  # our margin, from NICCOLO/denovo/gate.py
INTERNAL_CDRH3_DIST_MIN = 4   # our margin, from NICCOLO/denovo/gate.py
MAX_CDR3_LEN = 40             # measured: numbering holds to a +20 extension; stay under
VHH_KIND = "vhh"
REGIONS = ("prefix", "fr1", "cdr1", "fr2", "cdr2", "fr3", "cdr3", "fr4", "postfix")

#: CDR fills never contain C, so cysteine parity stays decided by the framework
#: (both conserved framework cysteines are always present in these scaffolds).
CDR_ALPHABET = "ADEFGHIKLMNPQRSTVWY"
#: CDR-like amino-acid composition (approximate nanobody loop composition, no Cys).
CDR_WEIGHTS = {
    "A": 7, "D": 7, "E": 6, "F": 5, "G": 9, "H": 2, "I": 4, "K": 3, "L": 5,
    "M": 1, "N": 8, "P": 3, "Q": 4, "R": 6, "S": 10, "T": 7, "V": 6, "W": 4, "Y": 10,
}
#: Apex insertions are flexible/polar/aromatic-biased, as camelid apical loops are.
APEX_WEIGHTS = {
    "D": 7, "G": 14, "N": 7, "R": 4, "S": 10, "T": 6, "W": 2, "Y": 10,
}

#: VHH frameworks measured in ../NICCOLO/denovo/scaffolds/SCAFFOLDS.md
#: ("Safe to use with the framework SEQUENCE KEPT", CDR3 extended to recommended
#: length). FR segments are the exact framework pieces of the deposited scaffolds;
#: lowercase CDRs were replaced, which is what the generator does too.
#: recommended_cdr3_len = shipped CDR3 + 14 (the +12..+16 band measured there).
SCAFFOLDS = [
    {
        "name": "vhh_6XYF_A",
        "fr1": "VQLQESGGGLVQAGGSLRLSCAAS",
        "fr2": "MAWFRQAPGKAREFAAG",
        "fr3": "DYEDSVKGRFTISRDNAKNTMYLQMNSLKPEDTAVYYC",
        "fr4": "WGKGTQVTVSS",
        "cdr1_len": 8, "cdr2_len": 8, "recommended_cdr3_len": 33,
        "note": "lowest own-parent identity in the library; parent is an unpublished phasing nanobody",
    },
    {
        "name": "vhh_8E2N_B",
        "fr1": "EVQLVESGGGLVPAGGSLRLSCTTS",
        "fr2": "MGWFRQAPGKEREFVAA",
        "fr3": "VVADSVAGRFTIFRDNAKNTVYLQMNSLKPEDTAVYYC",
        "fr4": "WGHGTQVTVSS",
        "cdr1_len": 8, "cdr2_len": 11, "recommended_cdr3_len": 31,
        "note": "divergent FR1; most shipped CDR content; parent VHH113, no primary publication",
    },
    {
        "name": "vhh_6JB9_A",
        "fr1": "DVQLVESGGGSVQAGGSLRLSCAAS",
        "fr2": "MTWFRQAPGKAREGVAA",
        "fr3": "YYTDSVKGRFTISQDKAKNMAYLRMDSVKSEDTAIYTC",
        "fr4": "WGQGTQVTVSS",
        "cdr1_len": 8, "cdr2_len": 8, "recommended_cdr3_len": 34,
        "note": "apo scaffold; loops not moulded onto an antigen",
    },
    {
        "name": "vhh_8CDS_A",
        "fr1": "QVQLVESGGGVVQTGDSLMLSCTVS",
        "fr2": "MGWFRQTPRKQREFVAA",
        "fr3": "IYGNSVKGRFTVSRDNAKNMVYLRMNSLKPEDTAVYFC",
        "fr4": "WGQGTQVTVSS",
        "cdr1_len": 8, "cdr2_len": 8, "recommended_cdr3_len": 32,
        "note": "lowest trastuzumab identity of any VHH (52%); most divergent FR1",
    },
    {
        "name": "vhh_5VLV_A",
        "fr1": "EVQLVESGGGLVQTGDSLRLSCAAS",
        "fr2": "MAWFRQAPGKEREFVAG",
        "fr3": "AYADSVRGRATISRDSAKKTVYLQMNSLKPEDTAVYSC",
        "fr4": "WGRGTQVTVSS",
        "cdr1_len": 8, "cdr2_len": 8, "recommended_cdr3_len": 31,
        "note": "apo hapten-binder framework; structural diversity partner",
    },
]

SCORE_COLUMNS = (
    "score", "rank_score", "demo_score", "iptm", "binder_plddt",
    "min_ipae", "pred_log10_kd", "p_binder",
)
LOWER_IS_BETTER = {"min_ipae", "pred_log10_kd"}


# --------------------------------------------------------------------------- #
# interpreter plumbing (same pattern as NICCOLO/scripts/_track_common.py)
# --------------------------------------------------------------------------- #
def _ensure_abguard() -> None:
    try:
        import abguard  # noqa: F401
        return
    except ImportError:
        pass
    if os.environ.get("_VHHV_REEXEC") == "1":
        sys.exit("abguard is not importable. Set ABGUARD_PY=/path/to/python that has it.")
    candidates = [os.environ.get("ABGUARD_PY", "")]
    exe = shutil.which("abguard")
    if exe:
        candidates.append(str(Path(exe).resolve().parent / "python"))
    candidates.append("/home/hackathon/.venvs/abguard/bin/python")
    envs = glob(os.path.expanduser(
        "~/.cache/uv/archive-v0/*/lib/python3*/site-packages/abguard/novelty.py"))
    for novelty in sorted(envs, key=os.path.getmtime, reverse=True):
        candidates.append(str(Path(novelty).parents[4] / "bin" / "python"))
    for py in candidates:
        if py and os.path.exists(py):
            os.environ["_VHHV_REEXEC"] = "1"
            os.execv(py, [py, *sys.argv])
    sys.exit("abguard is not importable. Install it, or set ABGUARD_PY.")


_ensure_abguard()

import polars as pl  # noqa: E402
from abguard.annotate import annotate  # noqa: E402
from abguard.config import ANY_IG, PipelineConfig  # noqa: E402
from abguard.reference import bundled_reference, cdrh3_reference  # noqa: E402
from immunum.polars import segment_domains  # noqa: E402


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def draw(weights: dict, rng: random.Random, n: int = 1) -> str:
    letters = list(weights)
    vals = [weights[x] for x in letters]
    return "".join(rng.choices(letters, weights=vals, k=n))


def segment(sequences: list[str]) -> list[dict | None]:
    """immunum IMGT segmentation per sequence; one H-chain domain dict or None."""
    if not sequences:
        return []
    frame = pl.LazyFrame({"sequence": sequences}).with_columns(
        _seg=segment_domains(
            "sequence", chains=list(ANY_IG), scheme="imgt", min_confidence=0.1
        )
    )
    rows = frame.collect()["_seg"].to_list()
    out: list[dict | None] = []
    for domains in rows:
        # segment_domains structs carry regions only (no chain field); the first
        # cleanly numbered domain of a heavy_sequence is the VH. An scFv's VH is
        # conventionally first, and a VHH has exactly one domain.
        picked = next((d for d in domains or [] if d.get("error_kind") is None), None)
        out.append(picked)
    return out


def assemble(seg: dict, cdr1: str | None = None, cdr2: str | None = None,
             cdr3: str | None = None) -> str:
    parts = dict(seg)
    if cdr1 is not None:
        parts["cdr1"] = cdr1
    if cdr2 is not None:
        parts["cdr2"] = cdr2
    if cdr3 is not None:
        parts["cdr3"] = cdr3
    return "".join(parts[r] or "" for r in REGIONS)


# --------------------------------------------------------------------------- #
# input: a scored/ranked list
# --------------------------------------------------------------------------- #
def parse_ranked(path: Path, score_col: str | None, lower_is_better: bool | None):
    with path.open(newline="") as fh:
        rows = [dict(r) for r in csv.DictReader(fh)]
    if not rows:
        raise SystemExit(f"{path}: no rows")
    cols = list(rows[0])
    for need in ("sequence_id", "heavy_sequence"):
        if need not in cols:
            raise SystemExit(f"{path}: missing column {need} (found {cols})")
    if score_col and score_col not in cols:
        raise SystemExit(f"{path}: --score-col {score_col} not in {cols}")
    if not score_col:
        for c in SCORE_COLUMNS:
            if c in cols:
                score_col = c
                break
    direction = lower_is_better
    if direction is None:
        direction = score_col in LOWER_IS_BETTER if score_col else False

    parsed = []
    for i, r in enumerate(rows):
        seq = (r.get("heavy_sequence") or "").strip().upper()
        sid = r.get("sequence_id") or f"row_{i}"
        kind = (r.get("kind") or VHH_KIND).strip().lower()
        score = None
        if score_col and r.get(score_col) not in (None, ""):
            try:
                score = float(r[score_col])
            except ValueError:
                pass
        parsed.append({
            "sequence_id": sid,
            "kind": kind,
            "heavy_sequence": seq,
            "design_description": r.get("design_description") or "",
            "score": score,
            "order": i,
        })
    # rank: explicit score first (respecting direction), then input order
    scored = [p for p in parsed if p["score"] is not None]
    unscored = [p for p in parsed if p["score"] is None]
    scored.sort(key=lambda p: (p["score"] if not direction else -p["score"]), reverse=not direction)
    ranked = scored + unscored
    for rank, p in enumerate(ranked, 1):
        p["rank"] = rank
    return ranked, score_col, direction


def parent_cdrs(parents: list[dict]) -> None:
    """Attach immunum segmentation + CDRs to each parent, in rank order."""
    segs = segment([p["heavy_sequence"] for p in parents])
    for p, s in zip(parents, segs):
        p["seg"] = s
        p["usable"] = s is not None and p["kind"] in ("vhh", "paired", "scfv")
        if s:
            p["cdr1"] = s["cdr1"] or ""
            p["cdr2"] = s["cdr2"] or ""
            p["cdr3"] = s["cdr3"] or ""
            p["framework"] = "".join((s[r] or "") for r in
                                     ("prefix", "fr1", "fr2", "fr3", "fr4", "postfix"))


# --------------------------------------------------------------------------- #
# pre-screen: the official annotation plus our margins
# --------------------------------------------------------------------------- #
def prescreen(records: list[dict], identity_max: float, cdrh3_dist_min: int) -> list[dict]:
    """Annotate candidate variants with abguard itself; keep those inside margins."""
    if not records:
        return []
    config = PipelineConfig()
    ref = cdrh3_reference(bundled_reference(), config=config)
    frame = pl.DataFrame({
        "sequence_id": [r["sequence_id"] for r in records],
        "kind": [VHH_KIND] * len(records),
        "heavy_sequence": [r["heavy_sequence"] for r in records],
        "light_sequence": [""] * len(records),
        "design_description": [r.get("design_description", "") for r in records],
    })
    out = annotate(frame, config, include_liabilities=False, reference=ref,
                   gate_novelty=False)
    by_id = {r["sequence_id"]: r for r in records}
    kept = []
    for row in out.to_dicts():
        rec = by_id[row["sequence_id"]]
        identity = row.get("identity_to_trastuzumab")
        dist = row.get("cdrh3_min_distance")
        cdrh3 = row.get("cdrh3") or ""
        d_tz = levenshtein(cdrh3, TRASTUZUMAB_CDRH3)
        problems = list(row.get("errors") or [])
        if row.get("novelty_class") != "de_novo":
            problems.append(
                f"identity {identity:.3f} not < {IDENTITY_CAP:.2f} (would be optimisation track)"
                if identity is not None else "novelty class is not de_novo")
        elif identity is None or identity > identity_max:
            problems.append(f"identity {identity} > margin {identity_max}")
        if dist is None or dist < cdrh3_dist_min:
            problems.append(f"CDRH3 {dist} edits from reference set < margin {cdrh3_dist_min}")
        if d_tz < cdrh3_dist_min:
            problems.append(f"CDRH3 {d_tz} edits from trastuzumab < margin {cdrh3_dist_min}")
        rec.update({
            "identity_to_trastuzumab": identity,
            "novelty_class": row.get("novelty_class"),
            "cdrh3": cdrh3,
            "cdrh3_len": len(cdrh3),
            "cdrh3_min_distance": dist,
            "cdrh3_dist_trastuzumab": d_tz,
            "prescreen_errors": problems,
        })
        if not problems:
            kept.append(rec)
    return kept


# --------------------------------------------------------------------------- #
# the four variant strategies
# --------------------------------------------------------------------------- #
def strat_recombine(pool: list[dict], rng: random.Random, n: int, tag: str) -> list[dict]:
    """CDR shuffling onto the lead parent's framework.

    Framework = the best parent; each CDR is drawn independently from the top-K
    pool, so a variant combines loop content the generative model never sampled
    together while every piece has ranked parentage.
    """
    out = []
    lead = pool[0]
    for i in range(n):
        c1 = rng.choice(pool)["cdr1"]
        c2 = rng.choice(pool)["cdr2"]
        c3 = rng.choice(pool)["cdr3"]
        seq = assemble(lead["seg"], cdr1=c1, cdr2=c2, cdr3=c3)
        out.append({
            "sequence_id": f"var_{tag}_{i:03d}",
            "heavy_sequence": seq,
            "strategy": "recombine",
            "parents": ",".join(sorted({p["sequence_id"] for p in pool
                                        if p["cdr1"] == c1 or p["cdr2"] == c2
                                        or p["cdr3"] == c3} | {lead["sequence_id"]})),
            "parent_scores": str(lead["score"]),
        })
    return out


def strat_extend(parents: list[dict], rng: random.Random, per_parent: int, tag: str) -> list[dict]:
    """CDR3 apex extension by +4/+6/+8 residues.

    The measured identity lever (SCAFFOLDS.md): each extension residue is one more
    guaranteed edit vs trastuzumab's Fv and widens CDRH3 distance; +12..+16 is what
    clears even an own-parent identity bar, so +4..+8 on an already-passing parent
    buys margin without asking the numbering for an exotic loop.
    """
    out = []
    for p in parents:
        if not p.get("usable") or not p.get("cdr3"):
            continue
        for i in range(per_parent):
            k = rng.choice((4, 6, 8))
            if len(p["cdr3"]) + k > MAX_CDR3_LEN:
                k = max(4, MAX_CDR3_LEN - len(p["cdr3"]))
                if len(p["cdr3"]) + k > MAX_CDR3_LEN:
                    continue
            mid = len(p["cdr3"]) // 2
            new3 = p["cdr3"][:mid] + draw(APEX_WEIGHTS, rng, k) + p["cdr3"][mid:]
            out.append({
                "sequence_id": f"var_{tag}_{p['sequence_id']}_{i:02d}",
                "heavy_sequence": assemble(p["seg"], cdr3=new3),
                "strategy": "extend",
                "parents": p["sequence_id"],
                "parent_scores": str(p["score"]),
            })
    return out


def build_pssm(parents: list[dict]) -> dict:
    """Per-CDR, per-position amino-acid weights from the ranked parents.

    Simple positional tally (unaligned positions beyond a parent's CDR length are
    skipped). With a bigger ranked list this becomes a real PSSM; with 5-10 parents
    it is a weak prior, which is all it is used as.
    """
    pssm: dict[str, list[dict]] = {}
    for cdr in ("cdr1", "cdr2", "cdr3"):
        cols: list[dict] = []
        for p in parents:
            seq = p.get(cdr) or ""
            for i, aa in enumerate(seq):
                while len(cols) <= i:
                    cols.append({})
                cols[i][aa] = cols[i].get(aa, 0) + 1
        pssm[cdr] = cols
    return pssm


def strat_mutate(parents: list[dict], pssm: dict, rng: random.Random,
                 per_parent: int, tag: str) -> list[dict]:
    """1-3 PSSM-guided CDR substitutions, Cys never introduced or removed.

    Substitutions concentrate in CDR3 and CDR1 (the paratope core for a VHH on
    HER2 domain IV) while every change also lowers whole-Fv identity.
    """
    out = []
    for p in parents:
        if not p.get("usable"):
            continue
        for i in range(per_parent):
            edits: dict[str, str] = {}
            for cdr, n_subs in (("cdr3", 2), ("cdr1", 1), ("cdr2", 1)):
                seq = p.get(cdr) or ""
                if not seq:
                    continue
                for pos in rng.sample(range(len(seq)), k=min(len(seq), n_subs)):
                    weights = dict(CDR_WEIGHTS)
                    cols = pssm.get(cdr) or []
                    if pos < len(cols) and cols[pos]:
                        weights = {k: v * 2 for k, v in CDR_WEIGHTS.items()}
                        for aa, cnt in cols[pos].items():
                            weights[aa] = weights.get(aa, 0) + cnt * 3
                    weights.pop(seq[pos], None)
                    weights.pop("C", None)
                    if not weights:
                        continue
                    edits.setdefault(cdr, seq)
                    s = edits[cdr]
                    edits[cdr] = s[:pos] + draw(weights, rng, 1) + s[pos + 1:]
            if not edits:
                continue
            out.append({
                "sequence_id": f"var_{tag}_{p['sequence_id']}_{i:02d}",
                "heavy_sequence": assemble(
                    p["seg"], cdr1=edits.get("cdr1"), cdr2=edits.get("cdr2"),
                    cdr3=edits.get("cdr3")),
                "strategy": "mutate",
                "parents": p["sequence_id"],
                "parent_scores": str(p["score"]),
            })
    return out


def strat_graft(parents: list[dict], rng: random.Random, per_parent: int, tag: str) -> list[dict]:
    """Scaffold hop: each parent's CDRs on a different measured VHH framework.

    The frameworks are the five that SCAFFOLDS.md marks safe to keep with an
    extended CDR3; a hop diversifies the family around one hit, drops identity
    (a different FR is ~30-40 framework edits vs the parent) and keeps numbering
    confidence high, because every framework is a real numbered VHH.
    """
    out = []
    for p in parents:
        if not p.get("usable"):
            continue
        for i in range(per_parent):
            sc = rng.choice(SCAFFOLDS)
            if p.get("framework") and sc["fr3"] in p["framework"]:
                continue  # same framework: that is not a hop
            seq = sc["fr1"] + (p.get("cdr1") or draw(CDR_WEIGHTS, rng, sc["cdr1_len"])) \
                + sc["fr2"] + (p.get("cdr2") or draw(CDR_WEIGHTS, rng, sc["cdr2_len"])) \
                + sc["fr3"] + (p.get("cdr3") or draw(CDR_WEIGHTS, rng, sc["recommended_cdr3_len"])) \
                + sc["fr4"]
            out.append({
                "sequence_id": f"var_{tag}_{p['sequence_id']}_{i:02d}",
                "heavy_sequence": seq,
                "strategy": "graft",
                "parents": f"{p['sequence_id']}+{sc['name']}",
                "parent_scores": str(p["score"]),
                "scaffold": sc["name"],
            })
    return out


# --------------------------------------------------------------------------- #
# official verdict
# --------------------------------------------------------------------------- #
def run_official(designs: Path, report: Path) -> tuple[int, str]:
    cmd = [sys.executable, str(CHECKER), str(designs), "-o", str(report), "--strict-exit"]
    done = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    return done.returncode, (done.stdout or "") + (done.stderr or "")


# --------------------------------------------------------------------------- #
# subcommands
# --------------------------------------------------------------------------- #
def cmd_generate(args) -> int:
    ranked_path = Path(args.ranked)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    ranked, score_col, lower = parse_ranked(ranked_path, args.score_col,
                                            args.lower_is_better)
    print(f"input: {len(ranked)} rows; score column: "
          f"{score_col or 'none (using input order)'} "
          f"({'lower is better' if lower else 'higher is better'})")

    vhhs = [r for r in ranked if r["kind"] == VHH_KIND]
    others = [r for r in ranked if r["kind"] != VHH_KIND]
    if others:
        print(f"note: {len(others)} non-VHH row(s) contribute heavy-chain CDRs only: "
              + ", ".join(sorted({r['kind'] for r in others})))
    pool = vhhs + others
    parent_cdrs(pool)
    unusable = [p["sequence_id"] for p in pool if not p.get("usable")]
    if unusable:
        print(f"note: {len(unusable)} row(s) could not be numbered as Ig and are unused: "
              + ", ".join(unusable))

    # parents: the top-K that themselves clear the de novo pre-screen, falling
    # back to the top-K raw if none do (variants are re-screened either way).
    top = [p for p in pool if p.get("usable")][:args.parents_top]
    if not top:
        raise SystemExit("no usable parents")
    print(f"parent pool: top {args.parents_top} by rank -> screening parents first ...")
    parent_probe = prescreen([dict(r, sequence_id=f"parent_probe_{r['sequence_id']}",
                                   heavy_sequence=r["heavy_sequence"],
                                   design_description="parent probe")
                              for r in top], INTERNAL_IDENTITY_MAX, INTERNAL_CDRH3_DIST_MIN)
    passing_parent_ids = {r["sequence_id"].replace("parent_probe_", "")
                          for r in parent_probe}
    for p in top:
        p["passes_gate"] = p["sequence_id"] in passing_parent_ids
    if passing_parent_ids:
        parents = [p for p in top if p["passes_gate"]]
        print(f"parents: {len(parents)}/{len(top)} top rows already clear the de novo "
              f"gate with margins; excluded: "
              + ", ".join(p["sequence_id"] for p in top if not p["passes_gate"]))
    else:
        parents = top
        print("WARNING: no top-K parent clears the de novo gate; generating from the "
              "top-K anyway (variants are re-screened, and extend/mutate must move "
              "their CDR3s away from prior art)")

    rng = random.Random(args.seed)
    strategies = [s.strip() for s in args.strategies.split(",") if s.strip()]
    candidates: list[dict] = []
    if "recombine" in strategies:
        candidates += strat_recombine(parents, rng, args.per_strategy, "rec")
    if "extend" in strategies:
        candidates += strat_extend(parents, rng, max(2, args.per_strategy // 2), "ext")
    if "mutate" in strategies:
        pssm = build_pssm(parents)
        candidates += strat_mutate(parents, pssm, rng,
                                   max(2, args.per_strategy // 2), "mut")
    if "graft" in strategies:
        candidates += strat_graft(parents, rng, max(2, args.per_strategy // 2), "gra")

    # cheap uniqueness / hard-rule hygiene before the expensive screen
    seen: set[str] = set()
    clean = []
    for c in candidates:
        seq = c["heavy_sequence"]
        if seq in seen or not seq:
            continue
        if any(ch not in "ACDEFGHIKLMNPQRSTVWY" for ch in seq):
            continue
        if len(seq) > 250 or seq.count("C") % 2:
            continue
        seen.add(seq)
        c["design_description"] = (
            f"{c['strategy']} variant of {c['parents']}; parent score "
            f"{c['parent_scores']}; de novo track"
        )
        clean.append(c)
    print(f"generated {len(clean)} unique candidates "
          f"({len(candidates) - len(clean)} dropped as duplicates/hard-rule fails)")

    kept = prescreen(clean, args.identity_max, args.cdrh3_dist_min)

    def _inherited(r: dict) -> float:
        try:
            return float(r.get("parent_scores"))
        except (TypeError, ValueError):
            return float("-inf")

    print(f"pre-screen (identity <= {args.identity_max}, CDRH3 >= {args.cdrh3_dist_min} "
          f"edits): {len(kept)}/{len(clean)} passed, per strategy:")
    for strat in sorted({c["strategy"] for c in clean}):
        total = [c for c in clean if c["strategy"] == strat]
        good = [c for c in total if not c.get("prescreen_errors")]
        print(f"  {strat:10s} {len(good):3d}/{len(total):3d}")

    kept.sort(key=lambda r: _inherited(r), reverse=True)
    if len(kept) > args.max_output:
        print(f"capping the submission list at {args.max_output} (ranked by inherited "
              f"parent score)")
    kept = kept[: args.max_output]

    for r in kept:
        r["sequence_id"] = r["sequence_id"].replace("parent_probe_", "")
    designs = outdir / "variants.csv"
    with designs.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sequence_id", "kind", "heavy_sequence", "light_sequence",
                    "design_description"])
        for r in kept:
            w.writerow([r["sequence_id"], VHH_KIND, r["heavy_sequence"], "",
                         r["design_description"]])
    meta = outdir / "variants_meta.csv"
    with meta.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sequence_id", "strategy", "parents", "parent_score",
                    "identity_to_trastuzumab", "cdrh3_len", "cdrh3",
                    "cdrh3_min_distance", "cdrh3_dist_trastuzumab", "predicted_track"])
        for r in kept:
            w.writerow([r["sequence_id"], r["strategy"], r["parents"], r["parent_scores"],
                        f"{r['identity_to_trastuzumab']:.4f}", r["cdrh3_len"], r["cdrh3"],
                        r["cdrh3_min_distance"], r["cdrh3_dist_trastuzumab"],
                        r["novelty_class"]])

    if args.no_official:
        print(f"wrote {designs} and {meta} (official check skipped)")
        return 0

    report = outdir / "variants_denovo_report.csv"
    code, stdout = run_official(designs, report)
    print("\n--- official check_denovo.py ---")
    print(stdout.strip())
    print(f"official exit code: {code} (0 means every variant PASSes)")
    print(f"wrote {designs}\nwrote {meta}\nwrote {report}")
    return code


def cmd_demo(args) -> int:
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    ranked = outdir / "ranked.csv"
    n = 0
    with ranked.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sequence_id", "kind", "heavy_sequence", "light_sequence",
                    "design_description", "demo_score"])
        while n < args.n_parents:
            sc = SCAFFOLDS[n % len(SCAFFOLDS)]
            cdr3_len = sc["recommended_cdr3_len"] + rng.randrange(0, 5)
            seq = (sc["fr1"] + draw(CDR_WEIGHTS, rng, sc["cdr1_len"])
                   + sc["fr2"] + draw(CDR_WEIGHTS, rng, sc["cdr2_len"])
                   + sc["fr3"] + draw(CDR_WEIGHTS, rng, cdr3_len) + sc["fr4"])
            w.writerow([f"demo_{sc['name']}_{n:02d}", VHH_KIND, seq, "",
                        f"synthetic demo parent on {sc['name']} framework "
                        f"(CDR3 {cdr3_len}); scores are synthetic",
                        f"{rng.uniform(0, 1):.4f}"])
            n += 1
    print(f"wrote {n} synthetic parents to {ranked}")
    print("now run, e.g.:")
    print(f"  {sys.executable} {Path(__file__)} generate {ranked} -o {outdir}/gen "
          f"--seed {args.seed}")
    return 0


def cmd_check(args) -> int:
    report = Path(args.output) if args.output else Path(
        args.designs).with_name("denovo_report.csv")
    code, stdout = run_official(Path(args.designs), report)
    print(stdout.strip())
    print(f"official exit code: {code}; report: {report}")
    return code


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="generate variants from a scored/ranked list")
    g.add_argument("ranked", help="CSV: sequence_id, heavy_sequence [, score column]")
    g.add_argument("-o", "--outdir", required=True, help="output directory")
    g.add_argument("--score-col", default=None,
                   help="score column name (default: auto-detect, else input order)")
    g.add_argument("--lower-is-better", default=None, action="store_true",
                   help="treat the score column as lower-is-better (default: auto)")
    g.add_argument("--parents-top", type=int, default=6,
                   help="how many top-ranked rows form the parent pool (default 6)")
    g.add_argument("--per-strategy", type=int, default=6,
                   help="variants per strategy/parent scale (default 6)")
    g.add_argument("--strategies", default="recombine,extend,mutate,graft",
                   help="comma-separated subset of: recombine,extend,mutate,graft")
    g.add_argument("--max-output", type=int, default=20,
                   help="submission list is capped at 20 designs (default 20)")
    g.add_argument("--identity-max", type=float, default=INTERNAL_IDENTITY_MAX,
                   help="internal identity ceiling (official cap 0.70)")
    g.add_argument("--cdrh3-dist-min", type=int, default=INTERNAL_CDRH3_DIST_MIN,
                   help="internal CDRH3 edit floor (official floor 2)")
    g.add_argument("--seed", type=int, default=1)
    g.add_argument("--no-official", action="store_true",
                   help="skip the final check_denovo.py run")
    g.set_defaults(fn=cmd_generate)

    d = sub.add_parser("demo", help="write a synthetic scored/ranked list for a dry run")
    d.add_argument("outdir")
    d.add_argument("--n-parents", type=int, default=12)
    d.add_argument("--seed", type=int, default=1)
    d.set_defaults(fn=cmd_demo)

    c = sub.add_parser("check", help="run the official checker on any designs table")
    c.add_argument("designs")
    c.add_argument("-o", "--output", default=None)
    c.set_defaults(fn=cmd_check)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
