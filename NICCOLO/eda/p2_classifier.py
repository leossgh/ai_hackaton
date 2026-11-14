"""Step 2: binder classifier on the clonotype-grouped FACS splits (label 1 = high binder, 0 = mid/low).
Reports screening metrics and stratifies the test set by novelty (distance to nearest training sequence)."""
import time, pickle
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score
AA = "ACDEFGHIKLMNPQRSTVWY"; IDX = {c: i for i, c in enumerate(AA)}; L = 10
D = Path("data/splits"); OUT = Path("models"); OUT.mkdir(exist_ok=True)
tr, va, te = (pd.read_csv(D/f) for f in ["train.csv", "val.csv", "test.csv"])

def ordinal(seqs):
    a = np.frombuffer("".join(seqs).encode(), np.uint8).reshape(-1, L)
    out = np.full(a.shape, -1, np.int8)
    for c, i in IDX.items(): out[a == ord(c)] = i
    return out
def onehot(seqs):
    o = ordinal(seqs).astype(np.int32); assert o.min() >= 0, "non-standard residue"
    X = np.zeros((len(o), L*20), np.float32)
    r = np.arange(len(o))
    for p in range(L): X[r, p*20 + o[:, p]] = 1
    return X

Otr, Ova, Ote = ordinal(tr.seq.values), ordinal(va.seq.values), ordinal(te.seq.values)
ytr, yva, yte = tr.label.values, va.label.values, te.label.values
print("feature build done", Otr.shape)

# ---- novelty strata: is each test seq within 1 mutation of a training seq? ----
trset = set(tr.seq.values)
t0 = time.time()
near = np.zeros(len(te), bool)
for n, s in enumerate(te.seq.values):
    for p in range(L):
        if near[n]: break
        for c in AA:
            if c != s[p] and s[:p]+c+s[p+1:] in trset: near[n] = True; break
print(f"novelty strata in {time.time()-t0:.0f}s: d<=1 {near.mean():.3f}, d>=2 {1-near.mean():.3f}")

def screen_metrics(y, p, tag):
    o = np.argsort(-p); base = y.mean(); r = {"tag": tag, "n": len(y), "auroc": roc_auc_score(y, p), "ap": average_precision_score(y, p), "base_rate": base}
    for k in [0.001, 0.01, 0.05, 0.10]:
        m = max(1, int(len(y)*k)); prec = y[o[:m]].mean()
        r[f"prec@{k:g}"] = prec; r[f"enrich@{k:g}"] = prec/base
    # recall of positives when keeping top 10%
    m = int(len(y)*.10); r["recall@0.10"] = y[o[:m]].sum()/y.sum()
    return r

rows, models = [], {}
# baseline: edit distance only (fewer mutations -> more likely high binder)
p_ed = -te.edit_distance.values.astype(float)
rows.append(screen_metrics(yte, p_ed, "baseline: -edit_distance"))

for name, mk, feat in [
    ("logistic one-hot", lambda: LogisticRegression(C=1.0, max_iter=3000, n_jobs=-1), "oh"),
    ("hist-gradient-boosting", lambda: HistGradientBoostingClassifier(max_iter=400, learning_rate=.1, max_leaf_nodes=63,
        categorical_features=list(range(L)), early_stopping=True, validation_fraction=.1, random_state=0), "ord"),
]:
    Xtr, Xte = (onehot(tr.seq.values), onehot(te.seq.values)) if feat == "oh" else (Otr, Ote)
    Xva = onehot(va.seq.values) if feat == "oh" else Ova
    t0 = time.time(); m = mk().fit(Xtr, ytr); fit_s = time.time()-t0
    t0 = time.time(); pte = m.predict_proba(Xte)[:, 1]; pred_s = time.time()-t0
    pva = m.predict_proba(Xva)[:, 1]
    models[name] = (m, feat)
    r = screen_metrics(yte, pte, name); r["fit_s"] = round(fit_s, 1); r["seqs_per_s"] = int(len(Xte)/pred_s)
    r["val_auroc"] = roc_auc_score(yva, pva); rows.append(r)
    print(f"  {name}: fit {fit_s:.0f}s, test AUROC {r['auroc']:.4f}, val AUROC {r['val_auroc']:.4f}, {r['seqs_per_s']:,}/s")
    # novelty stratification
    for lab, mask in [("d<=1 to train", near), ("d>=2 to train", ~near)]:
        rr = screen_metrics(yte[mask], pte[mask], f"  {name} | {lab}"); rows.append(rr)

res = pd.DataFrame(rows)
cols = ["tag", "n", "base_rate", "auroc", "ap", "prec@0.001", "prec@0.01", "enrich@0.01", "recall@0.10", "val_auroc", "fit_s", "seqs_per_s"]
print("\n" + res[cols].to_string(index=False, float_format=lambda x: f"{x:.4f}"))
res.to_csv("figs/classifier_results.csv", index=False)
# ensemble of the two + persist
pl = models["logistic one-hot"][0].predict_proba(onehot(te.seq.values))[:, 1]
pg = models["hist-gradient-boosting"][0].predict_proba(Ote)[:, 1]
from scipy.stats import rankdata
pe = (rankdata(pl) + rankdata(pg))/2/len(pl)
print("\nensemble (mean rank):", {k: round(v, 4) for k, v in screen_metrics(yte, pe, "ens").items() if k != "tag"})
print("spearman(logistic, gbm) =", np.corrcoef(rankdata(pl), rankdata(pg))[0, 1].round(3))
pickle.dump({k: v for k, v in models.items()}, open(OUT/"facs_classifiers.pkl", "wb"))
np.save(OUT/"test_pred_logistic.npy", pl); np.save(OUT/"test_pred_gbm.npy", pg); np.save(OUT/"test_near.npy", near)
