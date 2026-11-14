"""Step 12: error bars on the feature comparison. GroupKFold is deterministic, so repeat with randomised
group->fold assignment to get a spread, and paired differences against the current model."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr
from prefilter import load, onehot, nmut, clusters
import seqfeat

spr, _ = load(); spr = spr.copy(); spr["n_mut"] = nmut(spr.cdrh3.values)
b = spr[spr.binding_result.isin(["quantified_binding", "no_reportable_kd"])].reset_index(drop=True)
yb = (b.binding_result == "quantified_binding").astype(int).values
q = spr[spr.binding_result == "quantified_binding"].reset_index(drop=True)
yq = np.log10(q.kd_nM.values)

def sets(df):
    oh, ag, po = onehot(df.cdrh3.values), seqfeat.agg(df.cdrh3.tolist()), seqfeat.positional(df.cdrh3.tolist())
    nm = df[["n_mut"]].values.astype(np.float32)
    return {"one-hot + n_mut (CURRENT)": (np.hstack([oh, nm]), oh.shape[1]),
            "one-hot": (oh, oh.shape[1]),
            "T0 agg": (ag, 0),
            "one-hot + T0 agg": (np.hstack([oh, ag]), oh.shape[1]),
            "one-hot + T0 agg + pos": (np.hstack([oh, ag, po]), oh.shape[1])}
Sb, Sq = sets(b), sets(q)

def pipe(est, n_oh, dim):
    if n_oh == 0: return make_pipeline(StandardScaler(), est)
    if n_oh >= dim: return est
    return make_pipeline(ColumnTransformer([("oh", "passthrough", list(range(n_oh))),
        ("num", StandardScaler(), list(range(n_oh, dim)))]), est)

def folds(groups, k, rs):
    """Random partition of whole groups into k folds (groups never split)."""
    u = np.unique(groups); rs.shuffle(u)
    assign = {g: i % k for i, g in enumerate(u)}
    f = np.array([assign[g] for g in groups])
    return [(np.where(f != i)[0], np.where(f == i)[0]) for i in range(k)]

def run(X, y, n_oh, groups, kind, reps=12, k=5):
    out = []
    for r in range(reps):
        rs = np.random.default_rng(r); p = np.zeros(len(y)); ok = np.zeros(len(y), bool)
        for tr, te in folds(groups, k, rs):
            if len(te) == 0 or len(np.unique(y[tr])) < 2 and kind == "clf": continue
            m = pipe(LogisticRegression(C=.3, max_iter=5000) if kind == "clf" else Ridge(3.0), n_oh, X.shape[1])
            m.fit(X[tr], y[tr])
            p[te] = m.predict_proba(X[te])[:, 1] if kind == "clf" else m.predict(X[te]); ok[te] = True
        out.append(roc_auc_score(y[ok], p[ok]) if kind == "clf" else spearmanr(p[ok], y[ok]).statistic)
    return np.array(out)

for task, S, y, df, kind, lab in [("CLASSIFIER", Sb, yb, b, "clf", "AUROC"), ("RANKER", Sq, yq, q, "reg", "Spearman")]:
    print(f"\n=== {task} ({lab}, mean +- sd over 12 randomised grouped-CV repeats) ===")
    for thr in [2, 4]:
        g = clusters(df.cdrh3.tolist(), thr)
        res = {n: run(X, y, n_oh, g, kind) for n, (X, n_oh) in S.items()}
        base = res["one-hot + n_mut (CURRENT)"]
        print(f"  Hamming<={thr}  ({len(np.unique(g))} groups)")
        for n, v in res.items():
            d = v - base
            star = ""
            if n != "one-hot + n_mut (CURRENT)":
                # paired across repeats: same fold randomisation per repeat index
                star = "  significant" if abs(d.mean()) > 2*d.std()/np.sqrt(len(d)) else "  ns"
            print(f"    {n:28s} {v.mean():+.3f} +- {v.std():.3f}   vs current {d.mean():+.3f}{star}")
