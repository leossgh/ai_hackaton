"""No single framework mutation clears NanoMelt's 4.1 C error bar. Do they stack?
Two filters applied first:
  - drop position 98: it is the residue immediately N-terminal to CDRH3 (the ...YYC-S-R|WGGDGFYAMD junction),
    so mutating it is the most likely of all to disturb antigen binding. It also dominates the top hits.
  - drop lone cysteine introductions: an unpaired Cys fails abguard's no-unpaired-cysteine check.
"""
import pandas as pd, numpy as np
TZ = "WGGDGFYAMD"
vh = pd.read_csv("../eda/data/trastuzumab_her2_spr_all_768.csv").query("cdrh3 == @TZ").vh_sequence.iloc[0]
m = pd.read_csv("saturation_scored.csv")
cdr3_start = vh.index(TZ) + 1  # 1-based position of CDRH3's first residue
print(f"CDRH3 occupies 1-based positions {cdr3_start}-{cdr3_start+9}; position 98 is its immediate N-flank")
safe = m[(m.pos != 98) & (m.mut != "C") & (m.dTm > 0.3)].copy()
print(f"candidate stabilising mutations after filters: {len(safe)} (from {len(m)})")
best = safe.sort_values("dTm", ascending=False).drop_duplicates("pos")
print("\nbest substitution per position, top 12:")
print(best.head(12)[["name", "pos", "wt", "mut", "dTm"]].round(2).to_string(index=False))
def apply_muts(seq, muts):
    s = list(seq)
    for _, r in muts.iterrows(): 
        assert s[int(r.pos)-1] == r.wt, (r.pos, r.wt, s[int(r.pos)-1])
        s[int(r.pos)-1] = r.mut
    return "".join(s)
rows = [dict(name="WT", k=0, muts="", seq=vh)]
# greedy cumulative stacks
for k in range(1, 13):
    sub = best.head(k)
    rows.append(dict(name=f"stack{k}", k=k, muts="+".join(sub.name), seq=apply_muts(vh, sub)))
# include the risky position-98 winner for comparison
r98 = m[(m.pos == 98)].nlargest(1, "dTm")
rows.append(dict(name="R98A_only", k=1, muts=r98.name.iloc[0], seq=apply_muts(vh, r98)))
rows.append(dict(name=f"stack6_plus_R98A", k=7, muts="+".join(best.head(6).name)+"+"+r98.name.iloc[0],
                 seq=apply_muts(vh, pd.concat([best.head(6), r98]))))
# random 6-mutation subsets, to see whether greedy order matters
rng = np.random.default_rng(0)
pool = safe.sort_values("dTm", ascending=False).drop_duplicates("pos").head(20)
for i in range(15):
    sub = pool.sample(6, random_state=int(rng.integers(1e6)))
    rows.append(dict(name=f"rand6_{i+1}", k=6, muts="+".join(sub.name), seq=apply_muts(vh, sub)))
d = pd.DataFrame(rows).drop_duplicates("seq").reset_index(drop=True)
d["n_cys"] = d.seq.str.count("C")
assert (d.n_cys == d.n_cys.iloc[0]).all(), "cysteine count changed"
d.to_csv("data_combos.csv", index=False)
with open("combos.fa", "w") as f:
    for r in d.itertuples(): f.write(f">{r.name}\n{r.seq}\n")
print(f"\n{len(d)} combination sequences written; cysteine count unchanged at {d.n_cys.iloc[0]} in all")
