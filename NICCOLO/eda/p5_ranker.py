"""Step 5: the pre-filter itself. Ranker on measured SPR KD + ensemble with the FACS classifier,
validated leak-free: sequence clusters held out together, and evaluated inside the design-constraint band."""
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, average_precision_score
from scipy.stats import spearmanr
AA = "ACDEFGHIKLMNPQRSTVWY"; IDX = {c: i for i, c in enumerate(AA)}; L = 10; TZ = "WGGDGFYAMD"
def ordinal(s):
    a = np.frombuffer("".join(s).encode(), np.uint8).reshape(-1, L); o = np.full(a.shape, -1, np.int8)
    for c, i in IDX.items(): o[a == ord(c)] = i
    return o
def onehot(s):
    o = ordinal(s).astype(np.int32); X = np.zeros((len(o), L*20), np.float32); r = np.arange(len(o))
    for p in range(L): X[r, p*20+o[:, p]] = 1
    return X
def nmut(s): return sum(a != b for a, b in zip(s, TZ))

# ---------- FACS classifier (trained once, on data excluding any SPR sequence) ----------
tr = pd.concat([pd.read_csv("data/splits/train.csv"), pd.read_csv("data/splits/val.csv")], ignore_index=True)
spr = pd.read_csv("data/trastuzumab_her2_spr_all_768.csv")
v = spr[(spr.cdrh3.str.len() == 10) & (spr.cdrh3 != TZ) & (spr.cdrh3 != "ARDRIVDDYYYYGMDV")].copy()
v = v[v.cdrh3.map(lambda s: set(s) <= set(AA))].reset_index(drop=True)
clean = tr[~tr.seq.isin(set(v.cdrh3))]
print(f"FACS train rows {len(tr)} -> {len(clean)} after removing {len(tr)-len(clean)} SPR sequences (no leakage into the screen)")
facs = HistGradientBoostingClassifier(max_iter=400, max_leaf_nodes=63, categorical_features=list(range(L)), random_state=0)
facs.fit(ordinal(clean.seq.values), clean.label.values)
v["p_facs"] = facs.predict_proba(ordinal(v.cdrh3.values))[:, 1]
v["nmut"] = v.cdrh3.map(nmut)

# ---------- leak-free grouping: single-linkage clusters at Hamming <= 2 ----------
O = ordinal(v.cdrh3.values).astype(np.int16)
Dm = (O[:, None, :] != O[None, :, :]).sum(2)
parent = list(range(len(v)))
def find(x):
    while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
    return x
for i, j in zip(*np.where(np.triu(Dm <= 2, 1))):
    a, b = find(i), find(j)
    if a != b: parent[a] = b
v["grp"] = [find(i) for i in range(len(v))]
print(f"SPR variants {len(v)} -> {v.grp.nunique()} sequence clusters (single-linkage, Hamming<=2) used as CV groups")

def grouped_cv(X, y, groups, mk, task, reps=1):
    n_splits = min(5, len(np.unique(groups)))
    p = np.zeros(len(y))
    for tr_i, te_i in GroupKFold(n_splits).split(X, y, groups):
        m = mk().fit(X[tr_i], y[tr_i])
        p[te_i] = m.predict_proba(X[te_i])[:, 1] if task == "clf" else m.predict(X[te_i])
    return p

# ================= TASK 1: will a design give a measurable KD? =================
b = v[v.binding_result.isin(["quantified_binding", "no_reportable_kd"])].copy().reset_index(drop=True)
yb = (b.binding_result == "quantified_binding").astype(int).values
Xoh, Xmut, Xfacs = onehot(b.cdrh3.values), b[["nmut"]].values.astype(float), b[["p_facs"]].values
feats = {"nmut only": Xmut, "FACS score only": Xfacs, "one-hot": Xoh,
         "one-hot + nmut + FACS": np.hstack([Xoh, Xmut, Xfacs]), "nmut + FACS": np.hstack([Xmut, Xfacs])}
print(f"\n=== TASK 1: measurable KD vs none | n={len(b)}, positives={yb.sum()} ({yb.mean():.3f}) ===")
print("    GROUPED CV (clusters held out together) — the honest number")
preds1 = {}
for name, X in feats.items():
    for mdl, mk in [("logreg", lambda: LogisticRegression(C=.3, max_iter=4000)), ("RF", lambda: RandomForestClassifier(400, min_samples_leaf=3, n_jobs=-1, random_state=0))]:
        p = grouped_cv(X, yb, b.grp.values, mk, "clf"); preds1[f"{name} [{mdl}]"] = p
        print(f"      {name:24s} [{mdl:6s}] AUROC {roc_auc_score(yb, p):.3f}  AP {average_precision_score(yb, p):.3f}")
# constraint band: designs must be >2 mutations from any provided data point
band = b.nmut >= 3
print(f"\n    INSIDE THE DESIGN-CONSTRAINT BAND (>=3 mutations): n={band.sum()}, positives={yb[band].sum()} ({yb[band].mean():.3f})")
for name, p in preds1.items():
    print(f"      {name:34s} AUROC {roc_auc_score(yb[band], p[band]):.3f}  AP {average_precision_score(yb[band], p[band]):.3f}")

# ================= TASK 2: rank affinity (log10 KD) among quantified =================
q = v[v.binding_result == "quantified_binding"].copy().reset_index(drop=True)
yq = np.log10(q.kd_nM.values)
Qoh, Qmut, Qfacs = onehot(q.cdrh3.values), q[["nmut"]].values.astype(float), q[["p_facs"]].values
qfeats = {"nmut only": Qmut, "FACS score only": Qfacs, "one-hot": Qoh,
          "one-hot + nmut + FACS": np.hstack([Qoh, Qmut, Qfacs]), "nmut + FACS": np.hstack([Qmut, Qfacs])}
print(f"\n=== TASK 2: rank log10 KD | n={len(q)} quantified, {q.grp.nunique()} clusters ===")
print("    GROUPED CV Spearman (negative is useless; we want positive = predicts true KD order)")
preds2 = {}
for name, X in qfeats.items():
    for mdl, mk in [("ridge", lambda: Ridge(3.0)), ("RF", lambda: RandomForestRegressor(400, min_samples_leaf=3, n_jobs=-1, random_state=0))]:
        p = grouped_cv(X, yq, q.grp.values, mk, "reg"); preds2[f"{name} [{mdl}]"] = p
        print(f"      {name:24s} [{mdl:5s}] spearman {spearmanr(p, yq).statistic:+.3f}")
qband = q.nmut >= 3
print(f"\n    INSIDE THE CONSTRAINT BAND (>=3 mutations): n={qband.sum()}")
for name, p in preds2.items():
    print(f"      {name:34s} spearman {spearmanr(p[qband], yq[qband]).statistic:+.3f}")
# how well does it find the tightest binders?
print(f"\n    Top-20 selection by each model: median true KD (nM) | overall median {10**np.median(yq):.1f}")
for name, p in preds2.items():
    top = np.argsort(p)[:20]; print(f"      {name:34s} {10**np.median(yq[top]):8.2f}   best {10**yq[top].min():.3f}")
np.save("models/spr_grp.npy", v.grp.values); v.to_csv("figs/spr_with_scores.csv", index=False)
