"""Step 7: interface PAE (min_ipae) across the CDRH3<->HER2 interface -- the Foundry-recommended
metric, and the most targeted fold signal available. Does it beat ipTM, and does it add to the pre-filter?"""
import sys, pathlib, gzip, glob
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd, cbor2
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr
TZ = "WGGDGFYAMD"
LEN_A, LEN_B, LEN_C, LEN_D = 107, 120, 92, 17
OFF_B, OFF_C = LEN_A, LEN_A + LEN_B
N = LEN_A + LEN_B + LEN_C + LEN_D

DT = {85: "<f4", 86: ">f4", 81: "<u2", 82: "<u4", 72: "u1"}   # RFC 8746 typed-array tags
def typed(x):
    """Decode RFC 8746 typed arrays, including tag 40 (row-major multi-dim) wrapping a typed array."""
    if isinstance(x, cbor2.CBORTag):
        if x.tag == 40:                      # [dims, flat typed array]
            dims, flat = x.value
            return typed(flat).reshape(tuple(dims))
        if x.tag in DT:
            return np.frombuffer(x.value, DT[x.tag])
        raise AssertionError(f"unexpected tag {x.tag}")
    return np.asarray(x)

spr = pd.read_csv("data/trastuzumab_her2_spr_all_768.csv")
vh = dict(zip(spr.cdrh3, spr.vh_sequence))
rows = []
for f in sorted(glob.glob("data/detailed/*/seed_42/*detailed_scores.cbor.gz")):
    cd = f.split("/")[2]
    d = cbor2.loads(gzip.open(f).read())
    pae = typed(d["token_token_predicted_aligned_error"])
    assert pae.shape == (N, N), f"{cd}: PAE shape {pae.shape} != {(N, N)}"
    st = vh[cd].index(cd); assert st > 0
    loop = np.arange(OFF_B+st, OFF_B+st+10)        # CDRH3 tokens
    her2 = np.arange(OFF_C, N)                      # HER2 chains C+D
    sub = np.minimum(pae[np.ix_(loop, her2)], pae[np.ix_(her2, loop)].T)   # symmetrise
    ab = np.arange(0, OFF_C)                        # whole antibody (VL+VH)
    sub_ab = np.minimum(pae[np.ix_(ab, her2)], pae[np.ix_(her2, ab)].T)
    rows.append(dict(cdrh3=cd, min_ipae_loop=sub.min(), mean_ipae_loop=sub.mean(),
                     min_ipae_ab=sub_ab.min(), mean_ipae_ab=sub_ab.mean(),
                     loop_pae_internal=pae[np.ix_(loop, loop)].mean()))
ip = pd.DataFrame(rows)
cal = pd.read_csv("figs/iptm_calibration.csv").merge(ip, on="cdrh3")
print(f"n={len(cal)}")
print("\n=== interface PAE by outcome (lower = more confident interface) ===")
print(cal.groupby("binding_result")[["min_ipae_loop", "mean_ipae_loop", "min_ipae_ab", "mean_ipae_ab", "loop_pae_internal"]].agg(["mean", "std"]).round(3).to_string())
print("\n=== AUROC, binder vs no measurable KD (n=%d, %d pos) ===" % (len(cal), cal.y.sum()))
for c in ["min_ipae_loop", "mean_ipae_loop", "min_ipae_ab", "mean_ipae_ab", "loop_pae_internal"]:
    print(f"  {c:20s} {roc_auc_score(cal.y, -cal[c]):.3f}   (inverted: lower PAE = binder)")
print(f"  {'iptm':20s} {roc_auc_score(cal.y, cal.iptm):.3f}")
print(f"  {'p_binder (seq)':20s} {roc_auc_score(cal.y, cal.p_binder):.3f}  <-- in-sample, see note")
q = cal[cal.y == 1].copy(); q["logkd"] = np.log10(q.kd_nM)
print("\n=== among the 30 measured binders, vs log10 KD ===")
for c in ["min_ipae_loop", "mean_ipae_loop", "min_ipae_ab", "mean_ipae_ab", "loop_pae_internal", "iptm"]:
    r = spearmanr(q[c], q.logkd); print(f"  spearman({c:20s}, log10KD) = {r.statistic:+.3f}  p={r.pvalue:.3f}")
print("\n=== why global metrics cannot work here ===")
print(f"  all 60 complexes share {N-10} of {N} tokens (only the 10 CDRH3 residues vary) = {100*(N-10)/N:.1f}% identical")
print(f"  observed ipTM spread: {cal.iptm.max()-cal.iptm.min():.3f} | min_ipae_loop spread: {cal.min_ipae_loop.max()-cal.min_ipae_loop.min():.3f}")
cal.to_csv("figs/iptm_calibration_full.csv", index=False)
