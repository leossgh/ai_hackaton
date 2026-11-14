"""Step 9: Protenix v2 on the same 60. It has real dynamic range, unlike Boltz-2 -- does it discriminate?"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr
d = pd.read_csv("figs/iptm_calibration_full.csv")[["cdrh3", "binding_result", "kd_nM", "nmut", "y", "p_binder", "pred_log10_kd", "iptm"]]
d = d.rename(columns={"iptm": "boltz2_iptm"})
p = pd.read_csv("data/protenix_scores.csv").add_prefix("px_").rename(columns={"px_cdrh3": "cdrh3"})
m = d.merge(p, on="cdrh3")
print(f"n={len(m)} | positives={m.y.sum()}")
cols = [c for c in m.columns if c.startswith("px_") and c not in ("px_clash",)]
print("\n=== AUROC: binder vs no measurable KD (0.5 = chance) ===")
out = []
for c in cols:
    for sign, lab in [(1, "higher=binder"), (-1, "lower=binder")]:
        a = roc_auc_score(m.y, sign*m[c])
        if a >= 0.5: out.append((c, lab, a, m[c].min(), m[c].max()))
for c, lab, a, lo, hi in sorted(out, key=lambda x: -x[2]):
    print(f"  {c:16s} {lab:14s} AUROC {a:.3f}   range {lo:.3f}-{hi:.3f}")
print(f"  {'boltz2_iptm':16s} {'higher=binder':14s} AUROC {roc_auc_score(m.y, m.boltz2_iptm):.3f}")
q = m[m.y == 1].copy(); q["logkd"] = np.log10(q.kd_nM)
print(f"\n=== among the {len(q)} measured binders: Spearman vs log10 KD ===")
for c in cols:
    r = spearmanr(q[c], q.logkd)
    flag = "  <-- significant" if r.pvalue < 0.05 else ""
    print(f"  {c:16s} {r.statistic:+.3f}  p={r.pvalue:.3f}{flag}")
print(f"\n  agreement between the two fold models: spearman(boltz2_iptm, px_iptm) = {spearmanr(m.boltz2_iptm, m.px_iptm).statistic:+.3f}")
print(f"  Protenix ipTM>=0.7: {(m.px_iptm>=.7).sum()}/{len(m)} | of those, true binders: {m[m.px_iptm>=.7].y.sum()}")
m.to_csv("figs/fold_calibration_both_models.csv", index=False)
