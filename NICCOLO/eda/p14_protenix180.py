"""Step 14: the n=180 Protenix test. At n=30 every metric pointed the right way (ipTM -0.237) without
reaching significance. n=180 can resolve |r| ~ 0.2 at p < 0.01, so this settles it."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from prefilter import load, onehot, nmut, clusters

px = pd.read_csv("data/protenix_all.csv")
man = pd.read_csv("data/calib_all/manifest.csv")
d = man.merge(px, on="cdrh3").reset_index(drop=True)
d["logkd"] = np.log10(d.kd_nM)
print(f"n={len(d)} folded binders | KD {d.kd_nM.min():.3f}-{d.kd_nM.max():.1f} nM | clashes {int(d.clash.sum())}")
mets = ["iptm", "ptm", "plddt", "rank", "gpde", "iptm_BC", "iptm_BD", "iptm_AC", "iptm_AD", "iptm_ab_her2", "ptm_B"]
print("\n=== Spearman vs log10 KD (negative = higher confidence means tighter binding) ===")
print("  metric            r        p        95% CI (cluster bootstrap)")
g = clusters(d.cdrh3.tolist(), 2)
u = np.unique(g); idx = {x: np.where(g == x)[0] for x in u}
rs = np.random.default_rng(0)
boots = [np.concatenate([idx[x] for x in rs.choice(u, len(u), replace=True)]) for _ in range(2000)]
for m in mets:
    r = spearmanr(d[m], d.logkd)
    bs = np.array([spearmanr(d[m].values[b], d.logkd.values[b]).statistic for b in boots])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    sig = "" if lo < 0 < hi else "   <-- excludes 0"
    print(f"  {m:16s} {r.statistic:+.3f}  p={r.pvalue:.4f}  [{lo:+.3f}, {hi:+.3f}]{sig}")
print(f"\n  n=180 can resolve |r|=0.2 at p<0.01; at n=30 the same effect gave p=0.21")
print("\n=== does Protenix confidence add to the sequence ranker? (grouped CV, cluster bootstrap) ===")
spr, _ = load(); spr = spr.copy(); spr["n_mut"] = nmut(spr.cdrh3.values)
q = spr[spr.binding_result == "quantified_binding"].reset_index(drop=True)
j = q.merge(d[["cdrh3"] + mets], on="cdrh3", how="inner").reset_index(drop=True)
y = np.log10(j.kd_nM.values); gj = clusters(j.cdrh3.tolist(), 2)
oh = onehot(j.cdrh3.values); nm = j[["n_mut"]].values.astype(float)
FOLD = j[["iptm", "ptm", "plddt", "rank", "iptm_ab_her2"]].values
print(f"  matched to the SPR table: n={len(j)}, {len(np.unique(gj))} clusters")
def pipe(n_oh, dim):
    if n_oh >= dim: return Ridge(3.0)
    return make_pipeline(ColumnTransformer([("oh", "passthrough", list(range(n_oh))),
        ("num", StandardScaler(), list(range(n_oh, dim)))]), Ridge(3.0))
def folds(groups, k, rs):
    uu = np.unique(groups); rs.shuffle(uu)
    a = {x: i % k for i, x in enumerate(uu)}; f = np.array([a[x] for x in groups])
    return [(np.where(f != i)[0], np.where(f == i)[0]) for i in range(k)]
def oof(X, n_oh, reps=12):
    acc = np.zeros(len(y)); cnt = np.zeros(len(y))
    for r in range(reps):
        for tr, te in folds(gj, 5, np.random.default_rng(r)):
            if len(te) == 0: continue
            acc[te] += pipe(n_oh, X.shape[1]).fit(X[tr], y[tr]).predict(X[te]); cnt[te] += 1
    return acc/np.maximum(cnt, 1)
cur = oof(np.hstack([oh, nm]), oh.shape[1])
new = oof(np.hstack([oh, nm, FOLD]), oh.shape[1])
fold_only = oof(FOLD, 0)
uj = np.unique(gj); ij = {x: np.where(gj == x)[0] for x in uj}
rs = np.random.default_rng(1)
dif = []
for _ in range(3000):
    bb = np.concatenate([ij[x] for x in rs.choice(uj, len(uj), replace=True)])
    dif.append(spearmanr(new[bb], y[bb]).statistic - spearmanr(cur[bb], y[bb]).statistic)
lo, hi = np.percentile(dif, [2.5, 97.5])
print(f"  sequence only            spearman {spearmanr(cur, y).statistic:+.3f}")
print(f"  sequence + Protenix      spearman {spearmanr(new, y).statistic:+.3f}")
print(f"  Protenix metrics alone   spearman {spearmanr(fold_only, y).statistic:+.3f}")
verdict = "adds signal" if lo > 0 else ("HURTS (CI entirely below 0)" if hi < 0 else "no difference (CI spans 0)")
print(f"  difference {np.mean(dif):+.3f}  95% CI [{lo:+.3f}, {hi:+.3f}]  -> {verdict}")
print("  note: 'Protenix alone' is an out-of-fold ridge prediction; a negative Spearman means it ranks")
print("        designs in actively the wrong order, not merely at chance.")
d.to_csv("figs/protenix180.csv", index=False)
