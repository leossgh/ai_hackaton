"""Step 11: do the T0 sequence-only ddG features improve the pre-filter, and do they help OOD?

Validation is deliberately hostile:
  - grouped CV at Hamming thresholds 2..5 (threshold 4-5 is where one-hot was shown to collapse)
  - distance extrapolation: train near trastuzumab, test far
Regularisation is chosen by inner CV per fold, so feature sets with different widths compete fairly,
and scaling is fit inside each fold.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr
from prefilter import load, onehot, nmut, clusters, TZ
import seqfeat

spr, _ = load()
spr = spr.copy(); spr["n_mut"] = nmut(spr.cdrh3.values)
b = spr[spr.binding_result.isin(["quantified_binding", "no_reportable_kd"])].reset_index(drop=True)
yb = (b.binding_result == "quantified_binding").astype(int).values
q = spr[spr.binding_result == "quantified_binding"].reset_index(drop=True)
yq = np.log10(q.kd_nM.values)

def build(df):
    """Each entry is (matrix, n_leading_onehot_cols). One-hot columns are left unscaled; only the
    continuous physicochemical block is standardised, so the baseline is not handicapped."""
    oh, ag, po = onehot(df.cdrh3.values), seqfeat.agg(df.cdrh3.tolist()), seqfeat.positional(df.cdrh3.tolist())
    nm = df[["n_mut"]].values.astype(np.float32)
    return {"one-hot (current)": (oh, oh.shape[1]), "T0 agg": (ag, 0), "T0 positional": (po, 0),
            "one-hot + T0 agg": (np.hstack([oh, ag]), oh.shape[1]),
            "one-hot + T0 positional": (np.hstack([oh, po]), oh.shape[1]),
            "T0 agg + positional": (np.hstack([ag, po]), 0), "n_mut only": (nm, 0),
            "one-hot + n_mut (ranker)": (np.hstack([oh, nm]), oh.shape[1])}
Fb, Fq = build(b), build(q)

def pipe(est, n_oh, dim):
    """Scale only columns >= n_oh (the continuous block); pass the one-hot block through untouched."""
    if n_oh == 0: return make_pipeline(StandardScaler(), est)
    if n_oh >= dim: return est
    ct = ColumnTransformer([("oh", "passthrough", list(range(n_oh))),
                            ("num", StandardScaler(), list(range(n_oh, dim)))])
    return make_pipeline(ct, est)

CGRID = [.03, .1, .3, 1, 3]
AGRID = [.3, 1, 3, 10, 30, 100]
def nested_clf(X, y, g, n_oh=0):
    p = np.zeros(len(y)); ns = min(5, len(np.unique(g)))
    for tr, te in GroupKFold(ns).split(X, y, g):
        best, bc = -1, .3
        if len(np.unique(g[tr])) >= 3:
            for C in CGRID:
                pp = np.zeros(len(tr)); ok = True
                for i2, t2 in GroupKFold(3).split(X[tr], y[tr], g[tr]):
                    if len(np.unique(y[tr][i2])) < 2: ok = False; break
                    pp[t2] = pipe(LogisticRegression(C=C, max_iter=5000), n_oh, X.shape[1]).fit(X[tr][i2], y[tr][i2]).predict_proba(X[tr][t2])[:, 1]
                if ok:
                    a = roc_auc_score(y[tr], pp)
                    if a > best: best, bc = a, C
        p[te] = pipe(LogisticRegression(C=bc, max_iter=5000), n_oh, X.shape[1]).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return roc_auc_score(y, p)
def nested_reg(X, y, g, n_oh=0):
    p = np.zeros(len(y)); ns = min(5, len(np.unique(g)))
    for tr, te in GroupKFold(ns).split(X, y, g):
        best, ba = -9, 3.0
        if len(np.unique(g[tr])) >= 3:
            for al in AGRID:
                pp = np.zeros(len(tr))
                for i2, t2 in GroupKFold(3).split(X[tr], y[tr], g[tr]):
                    pp[t2] = pipe(Ridge(al), n_oh, X.shape[1]).fit(X[tr][i2], y[tr][i2]).predict(X[tr][t2])
                s = spearmanr(pp, y[tr]).statistic
                if s > best: best, ba = s, al
        p[te] = pipe(Ridge(ba), n_oh, X.shape[1]).fit(X[tr], y[tr]).predict(X[te])
    return spearmanr(p, y).statistic

print("=== CLASSIFIER: measurable KD vs none (n=%d, %d pos) -- AUROC, nested CV ===" % (len(b), yb.sum()))
thrs = [2, 3, 4, 5]
gb = {t: clusters(b.cdrh3.tolist(), t) for t in thrs}
rows = []
for name, (X, n_oh) in Fb.items():
    r = {"features": name, "dim": X.shape[1]}
    for t in thrs: r[f"H<={t}"] = nested_clf(X, yb, gb[t], n_oh)
    rows.append(r)
cf = pd.DataFrame(rows)
print(cf.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

print("\n=== RANKER: log10 KD (n=%d) -- Spearman, nested CV ===" % len(q))
gq = {t: clusters(q.cdrh3.tolist(), t) for t in thrs}
rows = []
for name, (X, n_oh) in Fq.items():
    r = {"features": name, "dim": X.shape[1]}
    for t in thrs: r[f"H<={t}"] = nested_reg(X, yq, gq[t], n_oh)
    rows.append(r)
rf = pd.DataFrame(rows)
print(rf.to_string(index=False, float_format=lambda x: f"{x:+.3f}"))

print("\n=== DISTANCE EXTRAPOLATION: train near trastuzumab, test far (true OOD) ===")
for cut in [4, 5]:
    tr, te = (b.n_mut <= cut).values, (b.n_mut > cut).values
    print(f"  classifier, train n_mut<={cut} (n={tr.sum()}) -> test >{cut} (n={te.sum()}, pos={yb[te].sum()})")
    for name, (X, n_oh) in Fb.items():
        m = pipe(LogisticRegression(C=.3, max_iter=5000), n_oh, X.shape[1]).fit(X[tr], yb[tr])
        print(f"     {name:26s} AUROC {roc_auc_score(yb[te], m.predict_proba(X[te])[:, 1]):.3f}")
for cut in [4, 5]:
    tr, te = (q.n_mut <= cut).values, (q.n_mut > cut).values
    if te.sum() < 15: continue
    print(f"  ranker, train n_mut<={cut} (n={tr.sum()}) -> test >{cut} (n={te.sum()})")
    for name, (X, n_oh) in Fq.items():
        m = pipe(Ridge(3.0), n_oh, X.shape[1]).fit(X[tr], yq[tr])
        print(f"     {name:26s} spearman {spearmanr(m.predict(X[te]), yq[te]).statistic:+.3f}")
cf.to_csv("figs/features_classifier.csv", index=False); rf.to_csv("figs/features_ranker.csv", index=False)
