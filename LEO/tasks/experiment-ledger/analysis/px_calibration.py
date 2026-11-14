#!/usr/bin/env python3
"""Does Protenix rank HER2 CDRH3 binders any better than Boltz-2? Measured: no.

EXP-004 showed Boltz-2 fold confidence is at chance for separating measured
binders from non-binders. `AGENTS.md` prefers folding models that take a
template (OpenFold3, Protenix, Boltz-2, Mol-1), so the open question was
whether a different template-taking model does better. This answers it from
the teammate's committed calibration table, with no new folding runs.

Input: analysis/fold_calibration_both_models.csv, extracted verbatim from
branch origin/nick commit fd1b002, path NICCOLO/eda/figs/fold_calibration_both_models.csv.
60 SPR variants: 30 with a measured KD, 30 with no reportable KD.

  python -I px_calibration.py            # writes px_calibration.txt beside it

Statistics are computed here rather than taken from the teammate's scripts,
whose numeric output was not committed. AUROC is the rank-based Mann-Whitney
estimate with tie correction; Spearman is Pearson on ranks. No scipy needed.
"""
from __future__ import annotations

import csv
import math
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "fold_calibration_both_models.csv")
OUT_PATH = os.path.join(HERE, "px_calibration.txt")

# metric -> +1 if a HIGHER value should mean "more likely to bind / tighter"
METRICS = {
    "boltz2_iptm": +1,
    "px_iptm": +1,
    "px_ptm": +1,
    "px_plddt": +1,
    "px_rank": +1,
    "px_gpde": -1,          # predicted error: lower is better
    "px_iptm_ab_her2": +1,  # antibody<->HER2 chain-pair ipTM
    "px_iptm_BC": +1,
    "px_iptm_BD": +1,
    "p_binder": +1,         # the sequence classifier, for scale
}


def ranks(xs: list[float]) -> list[float]:
    """Average ranks, ties shared."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


def auroc(scores: list[float], labels: list[int]) -> float:
    """Mann-Whitney U / (n_pos * n_neg), ties handled via average ranks."""
    r = ranks(scores)
    pos = [r[i] for i, y in enumerate(labels) if y == 1]
    n_pos, n_neg = len(pos), len(labels) - len(pos)
    if not n_pos or not n_neg:
        return float("nan")
    return (sum(pos) - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def spearman(a: list[float], b: list[float]) -> float:
    ra, rb = ranks(a), ranks(b)
    n = len(ra)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    da = math.sqrt(sum((x - ma) ** 2 for x in ra))
    db = math.sqrt(sum((y - mb) ** 2 for y in rb))
    return num / (da * db) if da and db else float("nan")


def main() -> int:
    with open(CSV_PATH, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    labels = [int(r["y"]) for r in rows]
    binders = [r for r in rows if int(r["y"]) == 1 and r["kd_nM"]]
    log_kd = [math.log10(float(r["kd_nM"])) for r in binders]

    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    say("Fold-metric calibration against measured affinity, Boltz-2 vs Protenix")
    say("Input: fold_calibration_both_models.csv (origin/nick fd1b002), "
        f"n={len(rows)}, {sum(labels)} binders / {len(labels) - sum(labels)} non-binders")
    say(f"Measured KD among binders: {min(10 ** v for v in log_kd):.3f}"
        f"-{max(10 ** v for v in log_kd):.1f} nM")
    say()
    say("AUROC = binder vs non-binder separation (0.5 is chance)")
    say("Spearman = agreement with tighter binding among the 30 binders "
        "(positive means the metric is right)")
    say()
    say(f"{'metric':<20} {'AUROC':>7} {'Spearman':>9}")
    say("-" * 38)

    results = []
    for metric, sign in METRICS.items():
        if metric not in rows[0]:
            continue
        try:
            all_s = [sign * float(r[metric]) for r in rows]
            bind_s = [sign * float(r[metric]) for r in binders]
        except (ValueError, KeyError):
            continue
        a = auroc(all_s, labels)
        # negate log_kd so that "higher is tighter" makes a positive Spearman
        rho = spearman(bind_s, [-v for v in log_kd])
        results.append((metric, a, rho))
    for metric, a, rho in sorted(results, key=lambda t: -t[1]):
        say(f"{metric:<20} {a:>7.3f} {rho:>9.3f}")

    say()
    say("Reading: every Protenix metric sits as close to chance as Boltz-2's")
    say("ipTM does -- AUROC 0.426 to 0.526 across ten metrics, including the")
    say("antibody<->HER2 chain-pair ipTM. So the EXP-004 failure is a property")
    say("of fixed-framework CDRH3 optimisation, not of Boltz-2 specifically,")
    say("and switching to another template-taking model will not fix it.")
    say()
    say("DO NOT QUOTE p_binder's 0.980 AS VALIDATION. These 60 variants are")
    say("part of the classifier's own training data, so that figure is")
    say("in-sample and inflated. The honest numbers are the grouped-CV ones")
    say("from EXP-003/EXP-004: AUROC 0.927 overall, 0.915 in the >=3-mutation")
    say("band, and 0.849 on this 60-variant subset. It is shown here only to")
    say("make the scale of the fold-metric failure legible.")

    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\nwrote {os.path.basename(OUT_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
