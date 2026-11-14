"""Step 10: leakage audit. Is the reported performance in-sample, or does it survive harder holdouts?

Tests
  A  permuted-label control                -> must collapse to chance
  B  cluster-threshold sweep (Hamming 1-6) -> does the score depend on how aggressively we group?
  C  mutation-distance extrapolation       -> train near trastuzumab, test far
  D  nested CV (hyperparameters chosen inside each fold) -> removes model-selection optimism
  E  explicit train/test membership check  -> no sequence or near-neighbour straddles a fold
  F  p_facs ablation                       -> is the FACS feature carrying hidden information?
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr
from prefilter import load, onehot, ordinal, nmut, clusters, L

spr, facs = load()
spr = spr.copy(); spr["n_mut"] = nmut(spr.cdrh3.values)
clean = facs[~facs.seq.isin(set(spr.cdrh3))]
fm = HistGradientBoostingClassifier(max_iter=400, max_leaf_nodes=63, categorical_features=list(range(L)),
                                    random_state=0).fit(ordinal(clean.seq.values), clean.label.values)
spr["p_facs"] = fm.predict_proba(ordinal(spr.cdrh3.values))[:, 1]

b = spr[spr.binding_result.isin(["quantified_binding", "no_reportable_kd"])].reset_index(drop=True)
yb = (b.binding_result == "quantified_binding").astype(int).values
q = spr[spr.binding_result == "quantified_binding"].reset_index(drop=True)
yq = np.log10(q.kd_nM.values)
OHb, OHq = onehot(b.cdrh3.values), onehot(q.cdrh3.values)

def cv_clf(X, y, g, mk=lambda: LogisticRegression(C=.3, max_iter=4000)):
    p = np.zeros(len(y))
    for tr, te in GroupKFold(min(5, len(np.unique(g)))).split(X, y, g):
        if len(np.unique(y[tr])) < 2:      # degenerate fold: predict the training prior
            p[te] = y[tr].mean(); continue
        p[te] = mk().fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return roc_auc_score(y, p)
def cv_reg(X, y, g, mk=lambda: Ridge(3.0)):
    p = np.zeros(len(y))
    for tr, te in GroupKFold(min(5, len(np.unique(g)))).split(X, y, g):
        p[te] = mk().fit(X[tr], y[tr]).predict(X[te])
    return spearmanr(p, y).statistic

print("=== E. membership check: does any sequence or near-neighbour straddle a fold? ===")
gb = clusters(b.cdrh3.tolist(), 2)
Ob = ordinal(b.cdrh3.values).astype(np.int16)
D = (Ob[:, None, :] != Ob[None, :, :]).sum(2)
worst_dup, worst_near = 0, 99
for tr, te in GroupKFold(5).split(OHb, yb, gb):
    s_tr, s_te = set(b.cdrh3.values[tr]), set(b.cdrh3.values[te])
    worst_dup = max(worst_dup, len(s_tr & s_te))
    worst_near = min(worst_near, D[np.ix_(te, tr)].min())
print(f"  identical sequences shared train/test, worst fold: {worst_dup}  (must be 0)")
print(f"  closest train-test pair across folds: Hamming {worst_near}  (grouping threshold was 2)")

print("\n=== A. permuted-label control (must collapse) ===")
rng = np.random.default_rng(0)
print(f"  classifier, real labels : AUROC {cv_clf(OHb, yb, gb):.3f}")
aucs = [cv_clf(OHb, rng.permutation(yb), gb) for _ in range(5)]
print(f"  classifier, permuted    : AUROC {np.mean(aucs):.3f} +- {np.std(aucs):.3f}")
gq = clusters(q.cdrh3.tolist(), 2)
print(f"  ranker, real targets    : spearman {cv_reg(np.hstack([OHq, q[['n_mut','p_facs']].values]), yq, gq):+.3f}")
sps = [cv_reg(np.hstack([OHq, q[['n_mut','p_facs']].values]), rng.permutation(yq), gq) for _ in range(5)]
print(f"  ranker, permuted        : spearman {np.mean(sps):+.3f} +- {np.std(sps):.3f}")

print("\n=== B. cluster-threshold sweep: how much does grouping aggressiveness matter? ===")
print("  thr | clf: groups  AUROC | rank: groups  spearman")
for thr in [0, 1, 2, 3, 4, 5]:
    g1 = clusters(b.cdrh3.tolist(), thr) if thr else np.arange(len(b))
    g2 = clusters(q.cdrh3.tolist(), thr) if thr else np.arange(len(q))
    a = cv_clf(OHb, yb, g1)
    s = cv_reg(np.hstack([OHq, q[['n_mut','p_facs']].values]), yq, g2)
    tag = "  <- random CV (no grouping)" if thr == 0 else ("  <- reported" if thr == 2 else "")
    print(f"  {thr:3d} | {len(np.unique(g1)):11d} {a:.3f} | {len(np.unique(g2)):12d} {s:+.3f}{tag}")

print("\n=== C. mutation-distance extrapolation (hardest realistic holdout) ===")
for cut in [4, 5, 6]:
    tr, te = b.n_mut <= cut, b.n_mut > cut
    if te.sum() < 20 or yb[te.values].sum() < 5: print(f"  clf  train<={cut}: too few test positives"); continue
    m = LogisticRegression(C=.3, max_iter=4000).fit(OHb[tr.values], yb[tr.values])
    a = roc_auc_score(yb[te.values], m.predict_proba(OHb[te.values])[:, 1])
    base = roc_auc_score(yb[te.values], -b.n_mut.values[te.values])
    print(f"  clf  train n_mut<={cut} (n={tr.sum()}), test >{cut} (n={te.sum()}, pos={yb[te.values].sum()}): AUROC {a:.3f}  | n_mut baseline {base:.3f}")
for cut in [4, 5, 6]:
    tr, te = q.n_mut <= cut, q.n_mut > cut
    if te.sum() < 15: print(f"  rank train<={cut}: too few test points"); continue
    X = np.hstack([OHq, q[['n_mut','p_facs']].values])
    m = Ridge(3.0).fit(X[tr.values], yq[tr.values])
    s = spearmanr(m.predict(X[te.values]), yq[te.values]).statistic
    print(f"  rank train n_mut<={cut} (n={tr.sum()}), test >{cut} (n={te.sum()}): spearman {s:+.3f}")

print("\n=== D. nested CV: hyperparameters chosen inside each fold ===")
def nested_clf(X, y, g):
    p = np.zeros(len(y)); outer = GroupKFold(5)
    for tr, te in outer.split(X, y, g):
        best, bestC = -1, None
        for C in [.03, .1, .3, 1, 3]:
            inner_g = g[tr]
            if len(np.unique(inner_g)) < 3: bestC = .3; break
            pp = np.zeros(len(tr))
            for i2, t2 in GroupKFold(3).split(X[tr], y[tr], inner_g):
                pp[t2] = LogisticRegression(C=C, max_iter=4000).fit(X[tr][i2], y[tr][i2]).predict_proba(X[tr][t2])[:, 1]
            a = roc_auc_score(y[tr], pp)
            if a > best: best, bestC = a, C
        p[te] = LogisticRegression(C=bestC, max_iter=4000).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return roc_auc_score(y, p)
print(f"  classifier, nested AUROC {nested_clf(OHb, yb, gb):.3f}  (fixed C=0.3 gave {cv_clf(OHb, yb, gb):.3f})")
def nested_reg(X, y, g):
    p = np.zeros(len(y))
    for tr, te in GroupKFold(5).split(X, y, g):
        best, bestA = -9, None
        for al in [.3, 1, 3, 10, 30]:
            pp = np.zeros(len(tr))
            for i2, t2 in GroupKFold(3).split(X[tr], y[tr], g[tr]):
                pp[t2] = Ridge(al).fit(X[tr][i2], y[tr][i2]).predict(X[tr][t2])
            s = spearmanr(pp, y[tr]).statistic
            if s > best: best, bestA = s, al
        p[te] = Ridge(bestA).fit(X[tr], y[tr]).predict(X[te])
    return spearmanr(p, y).statistic
Xq = np.hstack([OHq, q[['n_mut','p_facs']].values])
print(f"  ranker, nested spearman {nested_reg(Xq, yq, gq):+.3f}  (fixed alpha=3 gave {cv_reg(Xq, yq, gq):+.3f})")

print("\n=== F. p_facs ablation: is the FACS feature smuggling anything in? ===")
print(f"  ranker one-hot only            : {cv_reg(OHq, yq, gq):+.3f}")
print(f"  ranker one-hot + n_mut         : {cv_reg(np.hstack([OHq, q[['n_mut']].values]), yq, gq):+.3f}")
print(f"  ranker one-hot + n_mut + p_facs: {cv_reg(Xq, yq, gq):+.3f}")
print(f"  ranker p_facs alone            : {cv_reg(q[['p_facs']].values, yq, gq):+.3f}")

print("\n=== G. is the threshold-sweep decline novelty, or just less training data? ===")
print("   At thr=5 the ranker has far fewer effective training points. Control: keep thr=2 grouping but")
print("   subsample the training set to the same size, and see whether it degrades as much.")
sizes = {}
for thr in [2, 4, 5]:
    g = clusters(q.cdrh3.tolist(), thr)
    n = int(np.mean([len(tr) for tr, _ in GroupKFold(min(5, len(np.unique(g)))).split(Xq, yq, g)]))
    sizes[thr] = n
print("   mean training-set size per fold:", sizes)
g2 = clusters(q.cdrh3.tolist(), 2)
for thr in [4, 5]:
    target = sizes[thr]; out = []
    for rep in range(10):
        rs = np.random.default_rng(rep)
        p = np.zeros(len(yq)); mask = np.zeros(len(yq), bool)
        for tr, te in GroupKFold(5).split(Xq, yq, g2):
            sub = rs.choice(tr, min(target, len(tr)), replace=False)
            p[te] = Ridge(3.0).fit(Xq[sub], yq[sub]).predict(Xq[te]); mask[te] = True
        out.append(spearmanr(p[mask], yq[mask]).statistic)
    print(f"   thr=2 grouping, training subsampled to {target} (= thr={thr} size): spearman {np.mean(out):+.3f} +- {np.std(out):.3f}"
          f"   | actual thr={thr}: {cv_reg(Xq, yq, clusters(q.cdrh3.tolist(), thr)):+.3f}")
