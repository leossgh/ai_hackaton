"""Step 3: is the 0.995 real? Learning curve, label-permutation control, cluster purity, and a check of
whether the FACS labels agree with the independently measured SPR outcomes."""
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
AA = "ACDEFGHIKLMNPQRSTVWY"; IDX = {c: i for i, c in enumerate(AA)}; L = 10
D = Path("data/splits")
tr, te = pd.read_csv(D/"train.csv"), pd.read_csv(D/"test.csv")
def ordinal(s):
    a = np.frombuffer("".join(s).encode(), np.uint8).reshape(-1, L); o = np.full(a.shape, -1, np.int8)
    for c, i in IDX.items(): o[a == ord(c)] = i
    return o
Otr, Ote, ytr, yte = ordinal(tr.seq.values), ordinal(te.seq.values), tr.label.values, te.label.values
def gbm(): return HistGradientBoostingClassifier(max_iter=300, max_leaf_nodes=63, categorical_features=list(range(L)), random_state=0)

print("=== learning curve: train size vs test AUROC (grouped test set) ===")
rng = np.random.default_rng(0)
for n in [140, 560, 2240, 10000, 50000, 367044]:
    idx = rng.choice(len(Otr), min(n, len(Otr)), replace=False)
    m = gbm().fit(Otr[idx], ytr[idx]); print(f"  n_train={n:7d}  test AUROC {roc_auc_score(yte, m.predict_proba(Ote)[:,1]):.4f}")

print("\n=== control: labels permuted within train (expect ~0.50) ===")
yp = rng.permutation(ytr)
print("  permuted-label test AUROC %.4f" % roc_auc_score(yte, gbm().fit(Otr, yp).predict_proba(Ote)[:,1]))

print("\n=== cluster label purity (are clonotype clusters all-one-label?) ===")
g = tr.groupby("cluster_centre").label.agg(["mean", "size"])
print("  clusters:", len(g), "| pure clusters: %.3f" % ((g["mean"] == 0) | (g["mean"] == 1)).mean(), "| median size:", int(g["size"].median()))
print("  distribution of cluster mean label:", pd.cut(g["mean"], [-.01,.01,.2,.8,.99,1.01]).value_counts().sort_index().to_dict())

print("\n=== how much does each single position carry? (AUROC using one position only) ===")
for p in range(L):
    m = HistGradientBoostingClassifier(max_iter=100, categorical_features=[0], random_state=0).fit(Otr[:, [p]], ytr); print(f"  pos {p+1}: {roc_auc_score(yte, m.predict_proba(Ote[:, [p]])[:,1]):.3f}", end="")
print()
print("=== additive-only model (one-hot logistic, no interactions) was 0.944; GBM with interactions 0.995 ===")

print("\n=== EXTERNAL check: do FACS labels predict the independently measured SPR outcome? ===")
spr = pd.read_csv("data/trastuzumab_her2_spr_all_768.csv")
facs = pd.read_csv("data/tz_her2_facs_3classes_524346.csv", usecols=["cdrh3", "binding_class"])
j = spr.merge(facs, on="cdrh3", how="inner")
print("  CDRH3s shared between SPR and FACS:", len(j))
print(pd.crosstab(j.binding_class, j.binding_result).to_string())
q = j[j.binding_result == "quantified_binding"]
if len(q): print("  median KD (nM) by FACS class:", q.groupby("binding_class").kd_nM.agg(["median", "size"]).round(2).to_dict("index"))
