"""Control for the CDRH3 result: is NanoMelt insensitive to CDRH3 specifically, or to point mutations
anywhere? Same VH, single point mutations in framework vs in CDRH3."""
import numpy as np, pandas as pd
TZ = "WGGDGFYAMD"
spr = pd.read_csv("../eda/data/trastuzumab_her2_spr_all_768.csv")
vh = spr[spr.cdrh3 == TZ].vh_sequence.iloc[0]
CDR1, CDR2 = "GFNIKDTYIH", "RIYPTNGYTRYADSVKG"
cdr_spans = []
for c in (CDR1, CDR2, TZ):
    i = vh.index(c); cdr_spans.append((i, i+len(c)))
in_cdr = lambda p: any(a <= p < b for a, b in cdr_spans)
fw_pos = [p for p in range(len(vh)) if not in_cdr(p)]
cd3_pos = list(range(*cdr_spans[2]))
print(f"VH {len(vh)} aa | framework positions {len(fw_pos)} | CDRH3 positions {len(cd3_pos)}")
AA = "ACDEFGHIKLMNPQRSTVWY"
rng = np.random.default_rng(0)
rows = [dict(name="WT", region="wt", pos=-1, wt="-", mut="-", seq=vh)]
for region, pool, k in [("framework", fw_pos, 60), ("cdrh3", cd3_pos, 20)]:
    picks = rng.choice(pool, k, replace=True)
    for n, p in enumerate(picks):
        m = rng.choice([a for a in AA if a != vh[p]])
        rows.append(dict(name=f"{region}_{n+1}_{vh[p]}{p+1}{m}", region=region, pos=p+1,
                         wt=vh[p], mut=m, seq=vh[:p]+m+vh[p+1:]))
d = pd.DataFrame(rows).drop_duplicates("seq").reset_index(drop=True)
d.to_csv("data_fwpanel.csv", index=False)
with open("fwpanel.fa", "w") as f:
    for r in d.itertuples(): f.write(f">{r.name}\n{r.seq}\n")
print(f"{len(d)} sequences: {(d.region=='framework').sum()} framework, {(d.region=='cdrh3').sum()} CDRH3 single mutants + WT")
