"""Step 4: the decisive external check. Does a FACS-trained classifier agree with the independently
measured SPR outcomes, and do the FACS classes track measured KD?"""
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
AA = "ACDEFGHIKLMNPQRSTVWY"; IDX = {c: i for i, c in enumerate(AA)}; L = 10
TZ = "WGGDGFYAMD"
def ordinal(s):
    a = np.frombuffer("".join(s).encode(), np.uint8).reshape(-1, L); o = np.full(a.shape, -1, np.int8)
    for c, i in IDX.items(): o[a == ord(c)] = i
    return o
def onehot(s):
    o = ordinal(s).astype(np.int32); X = np.zeros((len(o), L*20), np.float32); r = np.arange(len(o))
    for p in range(L): X[r, p*20+o[:, p]] = 1
    return X

print("=== A. Do FACS classes track measured SPR KD? (shared CDRH3s) ===")
spr = pd.read_csv("data/trastuzumab_her2_spr_all_768.csv")
facs = pd.read_csv("data/tz_her2_facs_3classes_524346.csv", usecols=["cdrh3", "binding_class"])
j = spr.merge(facs, on="cdrh3", how="inner")
print("  shared CDRH3s:", len(j))
print(pd.crosstab(j.binding_class, j.binding_result).to_string())
q = j[j.binding_result == "quantified_binding"]
print("\n  measured KD (nM) by FACS class:\n", q.groupby("binding_class").kd_nM.agg(["size", "median", "min", "max"]).round(3).to_string())

print("\n=== B. FACS-trained classifier scored on the SPR set (fully external: different assay) ===")
tr = pd.read_csv("data/splits/train.csv"); va = pd.read_csv("data/splits/val.csv")
trall = pd.concat([tr, va], ignore_index=True)
Otr, ytr = ordinal(trall.seq.values), trall.label.values
gbm = HistGradientBoostingClassifier(max_iter=400, max_leaf_nodes=63, categorical_features=list(range(L)), random_state=0).fit(Otr, ytr)
log = LogisticRegression(C=1.0, max_iter=3000).fit(onehot(trall.seq.values), ytr)
# SPR variants, 10-mers, excluding trastuzumab itself and the unrelated antibody
v = spr[(spr.cdrh3.str.len() == 10) & (spr.cdrh3 != TZ) & (spr.cdrh3 != "ARDRIVDDYYYYGMDV")].copy()
v = v[v.cdrh3.str.strip().str.upper().map(lambda s: set(s) <= set(AA))]
trainset = set(trall.seq.values)
v["in_facs_train"] = v.cdrh3.isin(trainset)
v["p_gbm"] = gbm.predict_proba(ordinal(v.cdrh3.values))[:, 1]
v["p_log"] = log.predict_proba(onehot(v.cdrh3.values))[:, 1]
print("  SPR 10-mer variants:", len(v), "| of these, present in FACS train/val (leaky):", int(v.in_facs_train.sum()))
b = v[v.binding_result.isin(["quantified_binding", "no_reportable_kd"])].copy()
b["y"] = (b.binding_result == "quantified_binding").astype(int)
for tag, sub in [("ALL SPR 10-mers", b), ("LEAK-FREE (not in FACS train)", b[~b.in_facs_train])]:
    if len(sub) < 20: continue
    print(f"\n  -- {tag}: n={len(sub)}, positives={sub.y.sum()} (base rate {sub.y.mean():.3f})")
    for c in ["p_gbm", "p_log"]:
        print(f"     {c}: AUROC {roc_auc_score(sub.y, sub[c]):.3f}  AP {average_precision_score(sub.y, sub[c]):.3f}")
    ed = -np.array([sum(a != t for a, t in zip(s, TZ)) for s in sub.cdrh3])
    print(f"     baseline -edit_distance: AUROC {roc_auc_score(sub.y, ed):.3f}")

print("\n=== C. Does the classifier rank affinity among confirmed binders? (KD, lower=tighter) ===")
from scipy.stats import spearmanr
qq = v[(v.binding_result == "quantified_binding")].copy(); qq["logkd"] = np.log10(qq.kd_nM)
for tag, sub in [("all quantified", qq), ("leak-free", qq[~qq.in_facs_train])]:
    if len(sub) < 10: continue
    print(f"  {tag} n={len(sub)}: spearman(p_gbm, log10KD) = {spearmanr(sub.p_gbm, sub.logkd).statistic:+.3f} (negative = classifier score tracks tighter binding)")

print("\n=== D. Shanehsazzadeh external set (198 designed binders with affinity) ===")
sh = pd.read_csv("data/splits/shane_test.csv")
sh = sh[sh.seq.str.len() == 10]
sh = sh[sh.seq.map(lambda s: set(s) <= set(AA))]
sh["in_facs_train"] = sh.seq.isin(trainset)
sh["p_gbm"] = gbm.predict_proba(ordinal(sh.seq.values))[:, 1]
print("  n:", len(sh), "| in FACS train:", int(sh.in_facs_train.sum()), "| label counts:", sh.label.value_counts().to_dict())
if sh.label.nunique() > 1:
    print("  AUROC (label) :", round(roc_auc_score(sh.label, sh.p_gbm), 3))
s2 = sh[~sh.in_facs_train]
print(f"  spearman(p_gbm, affinity) all n={len(sh)}: {spearmanr(sh.p_gbm, sh.affinity).statistic:+.3f} | leak-free n={len(s2)}: {spearmanr(s2.p_gbm, s2.affinity).statistic:+.3f}  (affinity higher = tighter)")
v.to_csv("figs/spr_scored.csv", index=False)
