"""NanoMelt's 639 measured nanobody Tm values: what the data says, whether cheap features can
screen fast, and whether trastuzumab's VH is even inside this model's domain."""
from pathlib import Path
import numpy as np, pandas as pd
from Bio import Align
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold
from scipy.stats import pearsonr, spearmanr

D = Path("ext/nanomelt/datasets")
df = pd.read_csv(D/"NanoMelt_640_nanobody_apparent_melting_temperatures.csv")
df.columns = ["id", "name", "source", "method", "tm", "seq"]
df = df.dropna(subset=["tm", "seq"]).reset_index(drop=True)
print(f"=== A. dataset: {len(df)} nanobodies with measured apparent Tm ===")
print("  Tm (C):", df.tm.describe()[["mean", "std", "min", "25%", "50%", "75%", "max"]].round(1).to_dict())
print("  seq length:", df.seq.str.len().describe()[["min", "50%", "max"]].astype(int).to_dict())
print("\n  by method:\n", df.method.value_counts().to_string())
print("\n  by source:\n", df.source.value_counts().head(8).to_string())
print("\n  !! spread WITHIN a method matters: std of Tm per method")
print(df.groupby("method").tm.agg(["size", "mean", "std"]).round(1).to_string())

# ---- identity clustering for leak-free CV ----
al = Align.PairwiseAligner(scoring="blastp", mode="global", open_gap_score=-11, extend_gap_score=-1)
def ident(a, b):
    aln = al.align(a, b)[0]
    s = str(aln).split("\n")
    m = sum(1 for x, y in zip(aln[0], aln[1]) if x == y and x != "-")
    return m / min(len(a), len(b))
n = len(df); seqs = df.seq.values
print("\n=== B. clustering at >=80% identity for grouped CV (pairwise, may take a minute) ===")
parent = list(range(n))
def find(x):
    while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
    return x
# 3-mer prefilter so we only align plausible pairs
kms = [set(s[i:i+3] for i in range(len(s)-2)) for s in seqs]
cand = [(i, j) for i in range(n) for j in range(i+1, n)
        if len(kms[i] & kms[j]) / len(kms[i] | kms[j]) > .45]
print(f"  candidate pairs after 3-mer prefilter: {len(cand)} of {n*(n-1)//2}")
linked = 0
for i, j in cand:
    if find(i) != find(j) and ident(seqs[i], seqs[j]) >= .80:
        parent[find(i)] = find(j); linked += 1
grp = np.array([find(i) for i in range(n)])
print(f"  {n} sequences -> {len(set(grp))} clusters ({linked} merges)")

# ---- cheap features ----
AA = "ACDEFGHIKLMNPQRSTVWY"
KD = dict(zip("AILMFWVCYHTSPGRNDQEK", [1.8,4.5,3.8,1.9,2.8,-.9,4.2,2.5,-1.3,-3.2,-.7,-.8,-1.6,-.4,-4.5,-3.5,-3.5,-3.5,-3.5,-3.9]))
def feats(s):
    L = len(s); c = {a: s.count(a)/L for a in AA}
    return [L, sum(KD[x] for x in s)/L,
            (c["K"]+c["R"])*L, (c["D"]+c["E"])*L, (c["K"]+c["R"]-c["D"]-c["E"])*L,
            c["C"]*L, c["P"], c["G"], c["F"]+c["W"]+c["Y"], c["S"]+c["T"]+c["N"]+c["Q"]] + [c[a] for a in AA]
X = np.array([feats(s) for s in seqs], float); y = df.tm.values
names = ["len","gravy","n_pos","n_neg","net_charge","n_cys","P","G","aromatic","polar"] + list(AA)
print(f"\n=== C. can cheap features predict Tm? grouped CV, {X.shape[1]} features, no ESM, no GPU ===")
for tag, mk in [("ridge", lambda: RidgeCV(alphas=np.logspace(-2, 3, 20))),
                ("random forest", lambda: RandomForestRegressor(500, min_samples_leaf=3, n_jobs=-1, random_state=0))]:
    p = np.zeros(n)
    for tr, te in GroupKFold(5).split(X, y, grp):
        p[te] = mk().fit(X[tr], y[tr]).predict(X[te])
    print(f"  {tag:14s} pearson {pearsonr(p, y)[0]:+.3f}  spearman {spearmanr(p, y).statistic:+.3f}  MAE {np.abs(p-y).mean():.2f} C")
print(f"  {'predict the mean':14s} pearson    n/a   spearman    n/a   MAE {np.abs(y-y.mean()).mean():.2f} C  <- the number to beat")
print("  NanoMelt (published, ESM-1b+ESM-2 ensemble): pearson +0.853  spearman +0.832  MAE 4.1 C")
# which cheap features matter
r = RandomForestRegressor(500, min_samples_leaf=3, n_jobs=-1, random_state=0).fit(X, y)
imp = pd.Series(r.feature_importances_, index=names).sort_values(ascending=False)
print("\n  top cheap features by RF importance:", ", ".join(f"{k} {v:.3f}" for k, v in imp.head(8).items()))
print("  cysteine count vs Tm:", f"spearman {spearmanr(X[:, 5], y).statistic:+.3f}",
      "| mean Tm by n_cys:", df.assign(nc=X[:, 5]).groupby("nc").tm.agg(["size", "mean"]).round(1).to_dict("index"))

# ---- is trastuzumab VH inside this domain? ----
spr = pd.read_csv("../eda/data/trastuzumab_her2_spr_all_768.csv")
tz_vh = spr[spr.cdrh3 == "WGGDGFYAMD"].vh_sequence.iloc[0]
print(f"\n=== D. is trastuzumab VH in NanoMelt's domain? (VH len {len(tz_vh)}) ===")
ids = np.array([ident(tz_vh, s) for s in seqs])
print(f"  identity of trastuzumab VH to the 639 nanobodies: max {ids.max():.3f}, mean {ids.mean():.3f}, 95th pct {np.percentile(ids,95):.3f}")
# for contrast: how similar are nanobodies to each other?
rng = np.random.default_rng(0); pick = rng.choice(n, 120, replace=False)
nn = [max(ident(seqs[i], seqs[j]) for j in pick if j != i) for i in pick[:60]]
print(f"  for contrast, a nanobody's nearest neighbour within the set: median {np.median(nn):.3f}, min {np.min(nn):.3f}")
print(f"  closest nanobody to trastuzumab VH: {df.iloc[ids.argmax()][['id','method','tm']].to_dict()}")
