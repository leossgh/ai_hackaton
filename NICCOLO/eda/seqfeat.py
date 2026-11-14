"""Sequence-only (T0) substitution features for trastuzumab CDRH3 variants.

Ports the T0 tier from ../features/README.md -- blosum, d_chg, d_hydro, abs_hydro, d_vol, abs_chg,
d_arom -- from single-mutation ddG prediction to a 10-residue variant, which carries 1-10 substitutions.
T1-T4 are excluded on purpose: they need bound complex coordinates, so they cannot feed a sequence screen.

Why this might help where one-hot cannot: one-hot has a free parameter per (position, residue) and so
cannot say anything about a combination it never saw. These deltas transfer across residues, which is the
regime where the ranker was shown to collapse (AGENT_GUIDE.md section 3).
"""
import numpy as np
from Bio.Align import substitution_matrices

TZ = "WGGDGFYAMD"
AA = "ACDEFGHIKLMNPQRSTVWY"
_B = substitution_matrices.load("BLOSUM62")
BLOSUM = {(a, b): float(_B[a, b]) for a in AA for b in AA}
# Kyte-Doolittle hydropathy
HYDRO = dict(zip(AA, [1.8, 2.5, -3.5, -3.5, 2.8, -0.4, -3.2, 4.5, -3.9, 3.8, 1.9, -3.5, -1.6, -3.5, -4.5, -0.8, -0.7, 4.2, -0.9, -1.3]))
# residue side-chain volume, A^3
VOL = dict(zip(AA, [88.6, 108.5, 111.1, 138.4, 189.9, 60.1, 153.2, 166.7, 168.6, 166.7, 162.9, 114.1, 112.7, 143.8, 173.4, 89.0, 116.1, 140.0, 227.8, 193.6]))
CHG = {a: 0.0 for a in AA}; CHG.update({"D": -1.0, "E": -1.0, "K": 1.0, "R": 1.0, "H": 0.5})
AROM = {a: 0.0 for a in AA}; AROM.update({"F": 1.0, "W": 1.0, "Y": 1.0, "H": 1.0})
POLAR = {a: 0.0 for a in AA}; POLAR.update({c: 1.0 for c in "DEKRHNQSTY"})

DELTAS = ["blosum", "d_hydro", "abs_hydro", "d_vol", "abs_vol", "d_chg", "abs_chg", "d_arom", "d_polar"]

def _per_position(seq, ref=TZ):
    """One row per position: the T0 deltas for the substitution there, zeros where unchanged."""
    out = np.zeros((len(ref), len(DELTAS)), np.float32)
    for p, (r, m) in enumerate(zip(ref, seq)):
        if r == m: continue
        out[p] = [BLOSUM[(r, m)], HYDRO[m]-HYDRO[r], abs(HYDRO[m]-HYDRO[r]), VOL[m]-VOL[r],
                  abs(VOL[m]-VOL[r]), CHG[m]-CHG[r], abs(CHG[m]-CHG[r]), AROM[m]-AROM[r], POLAR[m]-POLAR[r]]
    return out

def agg(seqs, ref=TZ):
    """Variant-level aggregates: 1 + 9*4 = 37 features. Invariant to which position changed."""
    rows = []
    for s in seqs:
        M = _per_position(s, ref)
        sub = M[[i for i in range(len(ref)) if s[i] != ref[i]]]
        n = len(sub)
        if n == 0: sub = np.zeros((1, len(DELTAS)), np.float32)
        rows.append(np.concatenate([[n], sub.sum(0), sub.mean(0), sub.min(0), sub.max(0)]))
    return np.asarray(rows, np.float32)

def positional(seqs, ref=TZ):
    """Position-resolved: 10 positions x 9 deltas = 90 features. Position-aware and residue-generalising."""
    return np.asarray([_per_position(s, ref).ravel() for s in seqs], np.float32)

def names_agg():
    return ["n_sub"] + [f"{st}_{d}" for st in ["sum", "mean", "min", "max"] for d in DELTAS]
def names_positional():
    return [f"p{p+1}_{d}" for p in range(len(TZ)) for d in DELTAS]

if __name__ == "__main__":
    xs = [TZ, "WAADGFYSIE", "AAAAAAAAAA"]
    A, P = agg(xs), positional(xs)
    print("agg", A.shape, "positional", P.shape)
    print("n_sub:", A[:, 0], "| sum_blosum:", A[:, 1].round(1))
    assert A.shape[1] == len(names_agg()) and P.shape[1] == len(names_positional())
    assert np.allclose(P[0], 0), "trastuzumab itself must have all-zero deltas"
    print("ok")
