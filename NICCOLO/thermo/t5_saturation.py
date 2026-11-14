"""Full single-mutation saturation scan of the trastuzumab VH framework (every non-CDR position x
all 19 substitutions), to find predicted-stabilising mutations. CDRH3 is left alone: it is inert for Tm."""
import pandas as pd
TZ = "WGGDGFYAMD"; AA = "ACDEFGHIKLMNPQRSTVWY"
vh = pd.read_csv("../eda/data/trastuzumab_her2_spr_all_768.csv").query("cdrh3 == @TZ").vh_sequence.iloc[0]
spans = [(vh.index(c), vh.index(c)+len(c)) for c in ("GFNIKDTYIH", "RIYPTNGYTRYADSVKG", TZ)]
fw = [p for p in range(len(vh)) if not any(a <= p < b for a, b in spans)]
rows = [dict(name="WT", pos=0, wt="-", mut="-", seq=vh)]
for p in fw:
    for m in AA:
        if m != vh[p]:
            rows.append(dict(name=f"{vh[p]}{p+1}{m}", pos=p+1, wt=vh[p], mut=m, seq=vh[:p]+m+vh[p+1:]))
d = pd.DataFrame(rows)
d.to_csv("data_saturation.csv", index=False)
with open("saturation.fa", "w") as f:
    for r in d.itertuples(): f.write(f">{r.name}\n{r.seq}\n")
print(f"{len(d)-1} single mutants across {len(fw)} framework positions (+WT)")
