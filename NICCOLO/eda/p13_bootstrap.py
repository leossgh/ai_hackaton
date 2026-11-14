"""Step 13: cluster bootstrap on the one comparison that could justify changing the models --
ranker, one-hot+n_mut vs one-hot+T0 agg, at Hamming<=4. Repeat-to-repeat spread only measures fold
noise; this measures uncertainty from the 179 data points, which is what decides the question."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr
from prefilter import load, onehot, nmut, clusters
import seqfeat

spr, _ = load(); spr = spr.copy(); spr["n_mut"] = nmut(spr.cdrh3.values)
q = spr[spr.binding_result == "quantified_binding"].reset_index(drop=True)
yq = np.log10(q.kd_nM.values)
b = spr[spr.binding_result.isin(["quantified_binding", "no_reportable_kd"])].reset_index(drop=True)
yb = (b.binding_result == "quantified_binding").astype(int).values

def pipe(est, n_oh, dim):
    if n_oh == 0: return make_pipeline(StandardScaler(), est)
    if n_oh >= dim: return est
    return make_pipeline(ColumnTransformer([("oh", "passthrough", list(range(n_oh))),
        ("num", StandardScaler(), list(range(n_oh, dim)))]), est)
def folds(groups, k, rs):
    u = np.unique(groups); rs.shuffle(u)
    a = {g: i % k for i, g in enumerate(u)}; f = np.array([a[g] for g in groups])
    return [(np.where(f != i)[0], np.where(f == i)[0]) for i in range(k)]
def oof(X, y, n_oh, groups, kind, reps=12, k=5):
    """Average OOF prediction over repeats, so fold noise is averaged out before bootstrapping."""
    acc = np.zeros(len(y)); cnt = np.zeros(len(y))
    for r in range(reps):
        rs = np.random.default_rng(r)
        for tr, te in folds(groups, k, rs):
            if len(te) == 0: continue
            if kind == "clf" and len(np.unique(y[tr])) < 2: continue
            m = pipe(LogisticRegression(C=.3, max_iter=5000) if kind == "clf" else Ridge(3.0), n_oh, X.shape[1]).fit(X[tr], y[tr])
            acc[te] += m.predict_proba(X[te])[:, 1] if kind == "clf" else m.predict(X[te]); cnt[te] += 1
    return acc/np.maximum(cnt, 1), cnt > 0

def boot(groups, pA, pB, y, mask, kind, B=4000):
    """Resample whole clusters with replacement; paired difference between the two models."""
    g = groups[mask]; yy = y[mask]; a = pA[mask]; bb = pB[mask]
    u = np.unique(g); idx = {x: np.where(g == x)[0] for x in u}
    rs = np.random.default_rng(0); d = np.empty(B)
    for i in range(B):
        pick = np.concatenate([idx[x] for x in rs.choice(u, len(u), replace=True)])
        if kind == "clf":
            if len(np.unique(yy[pick])) < 2: d[i] = np.nan; continue
            d[i] = roc_auc_score(yy[pick], a[pick]) - roc_auc_score(yy[pick], bb[pick])
        else:
            d[i] = spearmanr(a[pick], yy[pick]).statistic - spearmanr(bb[pick], yy[pick]).statistic
    return d[~np.isnan(d)]

oh_q, ag_q = onehot(q.cdrh3.values), seqfeat.agg(q.cdrh3.tolist())
nm_q = q[["n_mut"]].values.astype(np.float32)
oh_b, ag_b = onehot(b.cdrh3.values), seqfeat.agg(b.cdrh3.tolist())
nm_b = b[["n_mut"]].values.astype(np.float32)
CUR_q, NEW_q = (np.hstack([oh_q, nm_q]), oh_q.shape[1]), (np.hstack([oh_q, ag_q]), oh_q.shape[1])
CUR_b, NEW_b = (np.hstack([oh_b, nm_b]), oh_b.shape[1]), (np.hstack([oh_b, ag_b]), oh_b.shape[1])

for kind, lab, X1, X2, y, df in [("reg", "RANKER (Spearman)", CUR_q, NEW_q, yq, q),
                                 ("clf", "CLASSIFIER (AUROC)", CUR_b, NEW_b, yb, b)]:
    print(f"\n=== {lab}: current (one-hot + n_mut) vs candidate (one-hot + T0 agg) ===")
    for thr in [2, 4]:
        g = clusters(df.cdrh3.tolist(), thr)
        pA, mA = oof(X1[0], y, X1[1], g, kind)
        pB, mB = oof(X2[0], y, X2[1], g, kind)
        m = mA & mB
        sA = roc_auc_score(y[m], pA[m]) if kind == "clf" else spearmanr(pA[m], y[m]).statistic
        sB = roc_auc_score(y[m], pB[m]) if kind == "clf" else spearmanr(pB[m], y[m]).statistic
        d = boot(g, pB, pA, y, m, kind)       # candidate minus current
        lo, hi = np.percentile(d, [2.5, 97.5])
        verdict = "candidate better" if lo > 0 else ("current better" if hi < 0 else "NO DIFFERENCE (CI spans 0)")
        print(f"  Hamming<={thr}: current {sA:+.3f}  candidate {sB:+.3f}  diff {d.mean():+.3f}  95% CI [{lo:+.3f}, {hi:+.3f}]  -> {verdict}")
