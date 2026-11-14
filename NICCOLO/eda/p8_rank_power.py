"""Step 8: ranking power. If we ranked the 30 measured binders by each fold metric and kept the top N,
what affinity would we actually get? Compared against the sequence ranker and against random."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from prefilter import load, onehot, nmut, clusters, PreFilter

d = pd.read_csv("figs/iptm_calibration_full.csv")
q = d[d.y == 1].copy().reset_index(drop=True)
q["logkd"] = np.log10(q.kd_nM)
print(f"n={len(q)} measured binders | KD {q.kd_nM.min():.3f}-{q.kd_nM.max():.1f} nM | median {q.kd_nM.median():.1f} nM")

# honest sequence-ranker prediction for these 30: grouped CV, trained only on OTHER SPR variants
spr, facs = load()
spr = spr.copy(); spr["nm"] = nmut(spr.cdrh3.values)
qq = spr[spr.binding_result == "quantified_binding"].reset_index(drop=True)
grp = clusters(qq.cdrh3.tolist())
X = np.hstack([onehot(qq.cdrh3.values), qq[["nm"]].values.astype(float)])
yv = np.log10(qq.kd_nM.values)
oof = np.zeros(len(yv))
for tr, te in GroupKFold(5).split(X, yv, grp):
    oof[te] = Ridge(3.0).fit(X[tr], yv[tr]).predict(X[te])
pred = dict(zip(qq.cdrh3, oof))
q["seq_ranker_oof"] = q.cdrh3.map(pred)
miss = q[q.seq_ranker_oof.isna()]
if len(miss):
    print(f"  dropping {len(miss)} with no out-of-fold prediction (excluded from the ranker's training table): {list(miss.cdrh3)}")
    q = q[q.seq_ranker_oof.notna()].reset_index(drop=True)
print(f"  comparison set: n={len(q)}, median KD {q.kd_nM.median():.1f} nM")

# direction: for each metric, sign so that "higher score = we think tighter"
metrics = {"ipTM": +1, "ptm": +1, "plddt": +1, "rank": +1, "gpde": -1,
           "min_ipae_loop": -1, "mean_ipae_loop": -1, "min_ipae_ab": -1, "mean_ipae_ab": -1,
           "loop_pae_internal": -1, "seq_ranker_oof": -1}
colmap = {"ipTM": "iptm"}
rng = np.random.default_rng(0)
rand_med = np.median([np.median(q.kd_nM.values[rng.choice(len(q), 10, replace=False)]) for _ in range(20000)])
rand_best = np.median([q.kd_nM.values[rng.choice(len(q), 10, replace=False)].min() for _ in range(20000)])

rows = []
for name, sign in metrics.items():
    c = colmap.get(name, name)
    s = sign * q[c].values
    r = spearmanr(s, -q.logkd)            # positive = score agrees with tighter binding
    for N in (10,):
        top = np.argsort(-s)[:N]
        rows.append(dict(metric=name, spearman_with_affinity=r.statistic, p=r.pvalue,
                         top10_median_kd=np.median(q.kd_nM.values[top]), top10_best_kd=q.kd_nM.values[top].min(),
                         top10_n_sub1nM=int((q.kd_nM.values[top] < 1).sum())))
res = pd.DataFrame(rows).sort_values("top10_median_kd")
print("\n=== ranking the 30 binders: keep the top 10 by each metric ===")
print(res.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
print(f"\n  RANDOM pick of 10: median KD {rand_med:.1f} nM, best {rand_best:.2f} nM")
print(f"  how many of the 30 are sub-1 nM: {int((q.kd_nM<1).sum())}")
print("\n  (seq_ranker_oof is out-of-fold: trained only on other clusters, never on the variant it scores)")
