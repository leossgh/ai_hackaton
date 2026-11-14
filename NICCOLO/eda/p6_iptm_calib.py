"""Step 6: does Boltz-2 fold confidence add anything over the sequence-only pre-filter?
Calibrated on 60 SPR variants with known outcomes."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd, pickle
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, average_precision_score
from scipy.stats import spearmanr
from prefilter import PreFilter, load, clusters, onehot, nmut, TZ

sc = pd.read_csv("data/calib_scores.csv").rename(columns={"cdrh3": "cdrh3"})
man = pd.read_csv("data/calib/manifest.csv")
d = man.merge(sc, on="cdrh3", how="inner")
print(f"calibration set: {len(d)} folded structures, {d.binding_result.value_counts().to_dict()}")
spr, facs = load()
pf = PreFilter().fit(spr, facs)
s = pf.score(d.cdrh3.tolist())
d = d.merge(s.drop(columns=["n_mut"]), on="cdrh3")
d["y"] = (d.binding_result == "quantified_binding").astype(int)

print("\n=== A. fold metrics: binders vs no measurable KD ===")
print(d.groupby("binding_result")[["iptm", "ptm", "plddt", "rank", "gpde"]].agg(["mean", "min", "max"]).round(3).to_string())
print("\n  AUROC of each fold metric alone (n=%d, %d positive):" % (len(d), d.y.sum()))
for c in ["iptm", "ptm", "plddt", "rank"]:
    print(f"    {c:6s} {roc_auc_score(d.y, d[c]):.3f}")
print(f"    gpde (inverted)  {roc_auc_score(d.y, -d.gpde):.3f}")
print("  for comparison, sequence-only pre-filter on the same 60:")
print(f"    p_binder        {roc_auc_score(d.y, d.p_binder):.3f}")
print(f"    -pred_log10_kd  {roc_auc_score(d.y, -d.pred_log10_kd):.3f}")
print(f"    -n_mut          {roc_auc_score(d.y, -d.nmut):.3f}")

print("\n=== B. among measured binders, do fold metrics track KD? ===")
q = d[d.y == 1].copy(); q["logkd"] = np.log10(q.kd_nM)
print(f"  n={len(q)}, KD {q.kd_nM.min():.3f} to {q.kd_nM.max():.1f} nM")
for c in ["iptm", "ptm", "plddt", "rank", "gpde"]:
    r = spearmanr(q[c], q.logkd)
    print(f"    spearman({c}, log10KD) = {r.statistic:+.3f}  p={r.pvalue:.3f}")
r = spearmanr(q.pred_log10_kd, q.logkd)
print(f"    [pre-filter] spearman(pred_log10_kd, log10KD) = {r.statistic:+.3f}  p={r.pvalue:.4f}")

print("\n=== C. does adding ipTM to the pre-filter help? (grouped CV on the 60) ===")
d["grp"] = clusters(d.cdrh3.tolist())
print(f"  {d.grp.nunique()} sequence clusters among {len(d)} variants")
def cv(X, y, grp, kind="clf"):
    p = np.zeros(len(y)); n = min(5, len(np.unique(grp)))
    for tr, te in GroupKFold(n).split(X, y, grp):
        if kind == "clf":
            if len(np.unique(y[tr])) < 2: p[te] = y[tr].mean(); continue
            p[te] = LogisticRegression(C=.3, max_iter=4000).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
        else: p[te] = Ridge(3.0).fit(X[tr], y[tr]).predict(X[te])
    return p
oh = onehot(d.cdrh3.tolist()); nm = d[["nmut"]].values.astype(float); ip = d[["iptm", "ptm", "plddt"]].values
y = d.y.values
for name, X in [("sequence only (one-hot)", oh), ("fold metrics only", ip), ("one-hot + fold metrics", np.hstack([oh, ip]))]:
    p = cv(X, y, d.grp.values)
    print(f"    {name:26s} AUROC {roc_auc_score(y, p):.3f}  AP {average_precision_score(y, p):.3f}")
print("\n=== D. verdict inputs: how many folds would the cascade waste? ===")
print(f"  ipTM>=0.7 pass rate on TRUE non-binders: {(d[d.y==0].iptm>=.7).mean():.2f}  (n={int((d.y==0).sum())})")
print(f"  ipTM>=0.7 pass rate on TRUE binders:     {(d[d.y==1].iptm>=.7).mean():.2f}")
print(f"  ipTM range overall: {d.iptm.min():.3f}-{d.iptm.max():.3f}  (spread {d.iptm.max()-d.iptm.min():.3f})")
d.to_csv("figs/iptm_calibration.csv", index=False)
