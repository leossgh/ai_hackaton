#!/usr/bin/env python3
"""Can a legal (>=4 substitution) CDRH3 variant beat trastuzumab on measured KD?

EXP-007 established that the legal band costs ~4x in achievable affinity. But
the number we are actually scored against is **trastuzumab's own measured KD**,
not the dataset's best variant. This asks the decisive question directly from
measured values: among variants that `abguard` would permit, does any beat
trastuzumab, and by how much?

Input: analysis/fold_calibration_both_models.csv (origin/nick fd1b002), the only
SPR table committed to the repo. 60 variants, 30 with a quantified KD.

  python -I legal_band_affinity.py      # writes legal_band_affinity.txt

IMPORTANT SAMPLING CAVEAT, carried into the output: these 60 were *chosen* for a
fold-calibration set (30 binders spanning the KD range, 30 non-binders), so the
hit rate here is not an unbiased estimate of the base rate in SPR-768's 179
quantified variants. Treat counts as existence proofs, not frequencies.
"""
from __future__ import annotations

import csv
import os
import statistics as st
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "fold_calibration_both_models.csv")
OUT_PATH = os.path.join(HERE, "legal_band_affinity.txt")

WT = "WGGDGFYAMD"          # trastuzumab CDRH3 positions 99-108 (the SPR 10-mer)
POS_LABEL = [f"{a}{i}" for a, i in zip(WT, range(99, 109))]
LEGAL_MIN_SUBS = 4         # 3/10 = exactly 70% identity, which fails "strictly under"


def main() -> int:
    lines: list[str] = []

    def say(t: str = "") -> None:
        print(t)
        lines.append(t)

    with open(CSV_PATH, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    binders = [
        (int(r["nmut"]), float(r["kd_nM"]), r["cdrh3"])
        for r in rows
        if r["binding_result"] == "quantified_binding" and r["kd_nM"]
    ]
    wt = [k for n, k, s in binders if n == 0]
    tz_kd = wt[0] if wt else None

    say("Can a legal (>=4 substitution) CDRH3 beat trastuzumab on measured KD?")
    say(f"Source: fold_calibration_both_models.csv | quantified binders n={len(binders)}")
    say(f"Trastuzumab CDRH3 {WT}: measured KD = {tz_kd} nM" if tz_kd
        else "Trastuzumab not present in this subset")
    say()
    say("By substitution count (measured KD, nM):")
    say(f"{'nmut':<6}{'n':>4}{'best':>10}{'median':>12}")
    for lo, hi, lab in [(1, 1, "1"), (2, 2, "2"), (3, 3, "3"),
                        (LEGAL_MIN_SUBS, 99, f">={LEGAL_MIN_SUBS} (legal)")]:
        g = [k for n, k, _ in binders if lo <= n <= hi]
        if g:
            say(f"{lab:<6}{len(g):>4}{min(g):>10.3f}{st.median(g):>12.3f}")

    legal = sorted([x for x in binders if x[0] >= LEGAL_MIN_SUBS], key=lambda t: t[1])
    say()
    say(f"Legal band, tightest first (top {min(8, len(legal))}):")
    for n, k, s in legal[:8]:
        subs = [f"{POS_LABEL[i]}{s[i]}" for i in range(len(WT)) if s[i] != WT[i]]
        say(f"  {s}  nmut={n}  KD={k:>9.3f} nM   {' '.join(subs)}")

    if tz_kd is not None:
        better = [x for x in legal if x[1] < tz_kd]
        say()
        say(f"Legal variants beating trastuzumab ({tz_kd} nM): "
            f"{len(better)} of {len(legal)}")
        for n, k, s in better:
            subs = [f"{POS_LABEL[i]}{s[i]}" for i in range(len(WT)) if s[i] != WT[i]]
            say(f"  {s}  nmut={n}  KD={k} nM  ({tz_kd / k:.1f}x better)  {' '.join(subs)}")
        best_illegal = min((x for x in binders if 1 <= x[0] < LEGAL_MIN_SUBS),
                           key=lambda t: t[1], default=None)
        if best_illegal:
            n, k, s = best_illegal
            say()
            say(f"For contrast, the best binder below the legal band: {s} "
                f"nmut={n} KD={k} nM ({tz_kd / k:.1f}x better than trastuzumab) "
                "- forbidden by the identity rule.")

    say()
    say("SAMPLING CAVEAT: these 60 variants were chosen for a fold-calibration")
    say("set (30 binders spanning the KD range, 30 non-binders), not sampled at")
    say("random from SPR-768's 179 quantified variants. So the counts above are")
    say("existence proofs, not base rates. Re-run on the full SPR table for a")
    say("real hit rate.")

    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\nwrote {os.path.basename(OUT_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
