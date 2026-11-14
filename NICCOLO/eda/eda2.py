"""EDA step 2: (A) topmodel score real vs shuffled + link to ipTM, (B) baseline predictors on the SPR-768 table.
Run: python -I eda2.py"""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import rankdata, spearmanr
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import roc_auc_score

D, F = Path("data"), Path("figs")
def auroc(pos, neg):
    r = rankdata(np.r_[pos, neg]); return (r[:len(pos)].sum() - len(pos)*(len(pos)+1)/2) / (len(pos)*len(neg))

print("=== A. topmodel score: real (system i==j) vs shuffled (i!=j) ===")
rows, sysmeans = [], {}
for m in ["af3", "boltz2", "chai1"]:
    t = pd.read_csv(D/f"topmodel_structure_accuracy/topmodel_{m}.csv")
    ex = t.ID.str.extract(r"system_(\d+)_(\d+)_([0-9A-Za-z]+)_([0-9A-Za-z]+)_")
    t["i"], t["j"] = ex[0].astype(int), ex[1].astype(int); t["v"], t["a"] = ex[2].str.upper(), ex[3].str.upper()
    t["real"] = t.i == t.j
    t = t[t.real | (t.v != t.a)]                      # drop shuffled rows that are really the same PDB pair
    t["score"] = t.score.clip(upper=t.score.quantile(.999))   # chai1 has absurd outliers (max 95587)
    sm = t.groupby(["i", "j", "v", "a", "real"]).score.agg(["mean", "max", "min"]).reset_index()
    sysmeans[m] = sm
    r, s = sm[sm.real], sm[~sm.real]
    rows.append(dict(model=m, n_real=len(r), n_shuf=len(s), real_med=r["mean"].median(), shuf_med=s["mean"].median(),
        auroc_mean_higher_is_real=auroc(r["mean"], s["mean"]), auroc_min=auroc(r["min"], s["min"])))
res = pd.DataFrame(rows).round(3); print(res.to_string(index=False)); res.to_csv(F/"topmodel_real_vs_shuffled.csv", index=False)
fig, ax = plt.subplots(1, 3, figsize=(13, 3.5))
for a, (m, sm) in zip(ax, sysmeans.items()):
    a.hist(sm[~sm.real]["mean"], bins=50, alpha=.6, density=True, label="shuffled"); a.hist(sm[sm.real]["mean"], bins=30, alpha=.6, density=True, label="real"); a.set_title(m); a.set_xlabel("mean topmodel score per system")
ax[0].legend(); fig.tight_layout(); fig.savefig(F/"topmodel_real_vs_shuffled.png", dpi=130)
# link to ipTM matrices (matrix label = complex PDB id; row = nanobody of that complex, col = antigen of that complex)
print("\n-- topmodel vs ipTM, per pair (Spearman) --")
for m in ["af3", "boltz2", "chai1"]:
    mx = pd.read_csv(D/f"iptm_confidence_scores/{m}_matrix_clean.csv", index_col=0)
    st = mx.stack().rename("iptm").reset_index(); st.columns = ["v", "a", "iptm"]
    j = sysmeans[m].merge(st.drop_duplicates(["v", "a"]), on=["v", "a"])
    print(m, "joined pairs", len(j), "spearman(topmodel mean, ipTM)=%.3f" % spearmanr(j["mean"], j.iptm).statistic,
          "| AUROC real-vs-shuffled using ipTM alone %.3f, topmodel alone %.3f" % (auroc(j[j.real].iptm, j[~j.real].iptm), auroc(j[j.real]["mean"], j[~j.real]["mean"])))

print("\n=== B. Baselines on SPR-768 (trastuzumab CDRH3 variants, 10-mers) ===")
TZ = "WGGDGFYAMD"; AA = "ACDEFGHIKLMNPQRSTVWY"
s = pd.read_csv(D/"trastuzumab_her2_spr_all_768.csv")
v = s[(s.cdrh3.str.len() == 10) & (s.cdrh3 != TZ) & (s.cdrh3 != "ARDRIVDDYYYYGMDV")].copy()
def onehot(seqs):
    X = np.zeros((len(seqs), 10*20), np.float32)
    for n, q in enumerate(seqs):
        for p, c in enumerate(q): X[n, p*20 + AA.index(c)] = 1
    return X
def same(seqs): return np.array([[c == TZ[p] for p, c in enumerate(q)] for q in seqs], np.float32)
# (1) KD regression on quantified
q = v[v.binding_result == "quantified_binding"].reset_index(drop=True); y = np.log10(q.kd_nM.values)
X1, X2 = onehot(q.cdrh3), np.hstack([onehot(q.cdrh3), same(q.cdrh3)]); ed = (same(q.cdrh3) == 0).sum(1).reshape(-1, 1)
print("KD regression, n =", len(q), "| 5-fold CV x5, Spearman of prediction vs true log10 KD")
def cv_reg(mk, X, reps=5):
    out = []
    for r in range(reps):
        p = np.zeros(len(y))
        for tr, te in KFold(5, shuffle=True, random_state=r).split(X): p[te] = mk().fit(X[tr], y[tr]).predict(X[te])
        out.append(spearmanr(p, y).statistic)
    return np.mean(out), np.std(out)
for name, mk, X in [("edit-distance only (linear)", lambda: Ridge(1e-6), ed), ("ridge one-hot", lambda: Ridge(3.0), X1),
                    ("ridge one-hot+same-as-tz", lambda: Ridge(3.0), X2), ("random forest one-hot", lambda: RandomForestRegressor(300, min_samples_leaf=2, n_jobs=-1, random_state=0), X1)]:
    mu, sd = cv_reg(mk, X); print(f"  {name:30s} {mu:.3f} +- {sd:.3f}")
# (2) measurable binder vs not (quantified vs no_reportable_kd)
b = v[v.binding_result.isin(["quantified_binding", "no_reportable_kd"])].reset_index(drop=True); yb = (b.binding_result == "quantified_binding").astype(int).values
Xb = onehot(b.cdrh3); edb = (same(b.cdrh3) == 0).sum(1).reshape(-1, 1)
print(f"\nBinder (KD measurable) vs not, n = {len(b)}, positives {yb.sum()} | 5-fold stratified CV AUROC")
for name, mk, X in [("edit distance only", lambda: LogisticRegression(), edb), ("logistic one-hot", lambda: LogisticRegression(C=.3, max_iter=2000), Xb),
                    ("random forest one-hot", lambda: RandomForestClassifier(300, min_samples_leaf=2, n_jobs=-1, random_state=0), Xb)]:
    aucs = []
    for r in range(5):
        p = np.zeros(len(yb))
        for tr, te in StratifiedKFold(5, shuffle=True, random_state=r).split(X, yb): p[te] = mk().fit(X[tr], yb[tr]).predict_proba(X[te])[:, 1]
        aucs.append(roc_auc_score(yb, p))
    print(f"  {name:30s} {np.mean(aucs):.3f} +- {np.std(aucs):.3f}")
# (3) which substitutions at which position hurt/help: mean log10KD by residue per position (quantified only, n>=4)
print("\nBest residues per position among quantified (mean log10 KD, n>=4; lower = tighter):")
for p in range(10):
    g = pd.DataFrame({"aa": [c[p] for c in q.cdrh3], "y": y}).groupby("aa").y.agg(["mean", "count"]); g = g[g["count"] >= 4].sort_values("mean")
    print(f"  pos {p+1} ({TZ[p]}):", ", ".join(f"{a}:{r['mean']:.2f}(n{int(r['count'])})" for a, r in g.head(3).iterrows()))
