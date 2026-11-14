"""EDA of the hackathon data available locally (small files, pulled from the VM into data/).
Run: python -I eda.py   (needs pandas numpy matplotlib scipy)"""
import re, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu, spearmanr

D = Path("data"); F = Path("figs"); F.mkdir(exist_ok=True)
TZ = "WGGDGFYAMD"
def say(*a): print(*a, flush=True)

# ---------- A. ipTM matrices (Smorodina et al., item 4) ----------
say("\n=== A. ipTM matrices: real (diagonal) vs shuffled (off-diagonal) ===")
mats = {}
for m in ["af3", "boltz2", "chai1"]:
    df = pd.read_csv(D/f"iptm_confidence_scores/{m}_matrix_clean.csv", index_col=0)
    mats[m] = df
    say(m, "shape", df.shape, "rows==cols:", list(df.index) == list(df.columns), "NaN:", int(df.isna().sum().sum()))
rows = []
for m, df in mats.items():
    common = [i for i in df.index if i in df.columns]
    diag = np.array([df.loc[i, i] for i in common], float)
    off = np.array([df.loc[i, j] for i in common for j in df.columns if j != i], float)
    off = off[~np.isnan(off)]; diag = diag[~np.isnan(diag)]
    # AUROC via rank
    from scipy.stats import rankdata
    r = rankdata(np.r_[diag, off]); auc = (r[:len(diag)].sum() - len(diag)*(len(diag)+1)/2) / (len(diag)*len(off))
    rows.append(dict(model=m, n_real=len(diag), n_shuffled=len(off), real_med=np.median(diag), shuf_med=np.median(off),
        real_ge07=(diag>=.7).mean(), shuf_ge07=(off>=.7).mean(), shuf_ge07_n=int((off>=.7).sum()), auroc=auc))
res = pd.DataFrame(rows).round(3); say(res.to_string(index=False)); res.to_csv(F/"iptm_summary.csv", index=False)
fig, ax = plt.subplots(1, 3, figsize=(13, 3.6), sharey=True)
for a, (m, df) in zip(ax, mats.items()):
    common = [i for i in df.index if i in df.columns]
    diag = [df.loc[i, i] for i in common]
    off = [df.loc[i, j] for i in common for j in df.columns if j != i]
    a.hist(off, bins=40, alpha=.6, density=True, label="shuffled"); a.hist(diag, bins=40, alpha=.6, density=True, label="real")
    a.axvline(.7, c="k", ls="--", lw=.8); a.set_title(m); a.set_xlabel("ipTM")
ax[0].legend(); ax[0].set_ylabel("density"); fig.tight_layout(); fig.savefig(F/"iptm_real_vs_shuffled.png", dpi=130)
# cross-model agreement on shared pairs
long = {m: df.stack() for m, df in mats.items()}
J = pd.concat(long, axis=1).dropna()
say("pairs scored by all 3 models:", len(J)); say("Spearman between models:\n", J.corr(method="spearman").round(3))
# per-nanobody: how many shuffled antigens get >=0.7 (false-positive burden)
fp = {m: (df.where(~np.eye(len(df), dtype=bool) if df.shape[0]==df.shape[1] else True) >= .7).sum(axis=1) for m, df in mats.items()}
say("AF3 nanobodies with >=1 shuffled partner at ipTM>=0.7:", int((fp["af3"]>0).sum()), "of", len(fp["af3"]))

# ---------- B. topmodel structure accuracy ----------
say("\n=== B. topmodel structure accuracy per model ===")
tm = {}
for m in ["af3", "boltz2", "chai1"]:
    t = pd.read_csv(D/f"topmodel_structure_accuracy/topmodel_{m}.csv")
    ex = t.ID.str.extract(r"system_(\d+)_(\d+)_([0-9A-Za-z]+)_([0-9A-Za-z]+)_")
    t["vhh_i"], t["ag_i"], t["vhh"], t["ag"] = ex[0], ex[1], ex[2], ex[3]
    t["real"] = t.vhh_i == t.ag_i if False else np.nan  # real pairs identified below via matrix diagonal
    tm[m] = t
    say(m, len(t), "rows;", t.score.describe().round(1).to_dict(), "unparsed IDs:", int(t.vhh.isna().sum()))
fig, a = plt.subplots(figsize=(6, 3.6))
for m, t in tm.items(): a.hist(t.score.dropna(), bins=50, alpha=.5, density=True, label=m)
a.set_xlabel("topmodel score"); a.legend(); fig.tight_layout(); fig.savefig(F/"topmodel_hist.png", dpi=130)

# ---------- C. Trastuzumab SPR (item 2: optimisation designs, Chinery) ----------
say("\n=== C. Trastuzumab HER2 SPR, 768 rows ===")
s = pd.read_csv(D/"trastuzumab_her2_spr_all_768.csv")
say(s.binding_result.value_counts().to_string())
tzrows = s[s.cdrh3 == TZ]; other = s[s.cdrh3 == "ARDRIVDDYYYYGMDV"]
say("trastuzumab reference rows:", len(tzrows), "KD range", tzrows.kd_nM.min(), tzrows.kd_nM.max(), "| other antibody rows:", len(other))
v = s[(s.cdrh3 != TZ) & (s.cdrh3 != "ARDRIVDDYYYYGMDV")].copy()
v["len"] = v.cdrh3.str.len()
def ham(a, b): return sum(x != y for x, y in zip(a, b)) if len(a) == len(b) else np.nan
v["edit"] = v.cdrh3.map(lambda x: ham(x, TZ))
say("variants:", len(v), "| unique CDRH3:", v.cdrh3.nunique(), "| duplicates:", len(v) - v.cdrh3.nunique())
say("CDRH3 length:", v.len.value_counts().to_dict())
say("Hamming to trastuzumab (10-mers only):", v.edit.describe().round(2).to_dict())
q = v[v.binding_result == "quantified_binding"].copy(); q["logkd"] = np.log10(q.kd_nM)
say("quantified:", len(q), "KD nM quantiles:", q.kd_nM.quantile([0, .1, .25, .5, .75, .9, 1]).round(3).to_dict())
tzmed = tzrows.kd_nM.median()
say(f"better than trastuzumab median ({tzmed:.3f} nM):", int((q.kd_nM < tzmed).sum()), "| better than its best (min):", int((q.kd_nM < tzrows.kd_nM.min()).sum()), "| KD<1 nM:", int((q.kd_nM < 1).sum()))
say("KD vs Hamming distance, Spearman:", spearmanr(q.edit, q.kd_nM, nan_policy="omit"))
say("hit rate by edit distance:\n", pd.crosstab(v.edit, v.binding_result).to_string())
# positional composition of quantified binders vs non-reportable
def posfreq(seqs):
    seqs = [x for x in seqs if len(x) == 10]
    return pd.DataFrame([[sum(x[i] == TZ[i] for x in seqs)/len(seqs)] for i in range(10)], columns=["frac_same_as_tz"])
pq, pn = posfreq(q.cdrh3), posfreq(v[v.binding_result == "no_reportable_kd"].cdrh3)
say("per-position fraction identical to trastuzumab (position: binders vs no-KD):")
for i in range(10): say(f"  {i+1} {TZ[i]}  {pq.iloc[i,0]:.2f}  {pn.iloc[i,0]:.2f}")
# AA composition shift
from collections import Counter
cq = Counter("".join(q.cdrh3)); cn = Counter("".join(v[v.binding_result=='no_reportable_kd'].cdrh3))
aa = sorted(set(cq) | set(cn)); fq = np.array([cq[a] for a in aa]) / sum(cq.values()); fn = np.array([cn[a] for a in aa]) / sum(cn.values())
fig, ax = plt.subplots(2, 2, figsize=(11, 7))
ax[0,0].bar(s.binding_result.value_counts().index, s.binding_result.value_counts().values); ax[0,0].set_title("binding_result"); ax[0,0].tick_params(axis="x", rotation=20)
ax[0,1].hist(q.logkd, bins=30); ax[0,1].axvline(np.log10(tzmed), c="r", ls="--", label="trastuzumab"); ax[0,1].set_xlabel("log10 KD (nM)"); ax[0,1].legend()
g = q.dropna(subset=["edit"]); ax[1,0].scatter(g.edit + np.random.uniform(-.15,.15,len(g)), g.logkd, s=10, alpha=.6); ax[1,0].set_xlabel("Hamming distance to trastuzumab CDRH3"); ax[1,0].set_ylabel("log10 KD")
w = .4; x = np.arange(len(aa)); ax[1,1].bar(x - w/2, fq, w, label="quantified"); ax[1,1].bar(x + w/2, fn, w, label="no KD"); ax[1,1].set_xticks(x); ax[1,1].set_xticklabels(aa); ax[1,1].legend(); ax[1,1].set_title("residue composition")
fig.tight_layout(); fig.savefig(F/"spr768.png", dpi=130)

# framework check: are VH/VL identical across variants outside CDRH3?
vh = v.apply(lambda r: r.vh_sequence.replace(r.cdrh3, "#"), axis=1)
say("distinct VH frameworks (CDRH3 masked):", vh.nunique(), "| distinct VL:", v.vl_sequence.nunique())

# ---------- D. Champloo SPR supplementary ----------
say("\n=== D. Champloo SPR table S1 ===")
t1 = pd.read_csv(D/"spr-supplementary/spr_table_s1_pairwise.csv")
say(pd.crosstab(t1.pair_type, t1.outcome_class).to_string())
say(t1[t1.kd_nM.notna()][["antigen_name", "vhh_design", "pair_type", "kd_nM", "kd_method", "af3_iptm"]].to_string(index=False))
x = pd.read_csv(D/"spr-supplementary/spr_crossreactivity_14target.csv"); say(x.to_string(index=False))
