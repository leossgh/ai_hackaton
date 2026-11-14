"""Build the test panel: trastuzumab VH carrying different CDRH3s (spanning the measured KD range),
plus the nanobody controls. Question: can CDRH3 substitution move predicted Tm at all?"""
import numpy as np, pandas as pd
TZ = "WGGDGFYAMD"
spr = pd.read_csv("../eda/data/trastuzumab_her2_spr_all_768.csv")
tz = spr[spr.cdrh3 == TZ].iloc[0]
vh_tpl = tz.vh_sequence
assert TZ in vh_tpl
print("trastuzumab VH:", len(vh_tpl), "aa | CDRH3 at", vh_tpl.index(TZ))
AA = set("ACDEFGHIKLMNPQRSTVWY")
v = spr[(spr.cdrh3.str.len() == 10) & (spr.cdrh3 != TZ) & (spr.cdrh3 != "ARDRIVDDYYYYGMDV")]
v = v[v.cdrh3.map(lambda s: set(s) <= AA)].copy()
v["nmut"] = v.cdrh3.map(lambda s: sum(a != b for a, b in zip(s, TZ)))
rows = [dict(name="trastuzumab_WT", cdrh3=TZ, kd_nM=tz.kd_nM, binding_result=tz.binding_result, nmut=0)]
# tight binders, weak binders, non-measurable, and extreme-composition loops
q = v[v.binding_result == "quantified_binding"].sort_values("kd_nM")
rows += [dict(name=f"tight_{i+1}", cdrh3=r.cdrh3, kd_nM=r.kd_nM, binding_result=r.binding_result, nmut=r.nmut) for i, r in enumerate(q.head(10).itertuples())]
rows += [dict(name=f"weak_{i+1}", cdrh3=r.cdrh3, kd_nM=r.kd_nM, binding_result=r.binding_result, nmut=r.nmut) for i, r in enumerate(q.tail(10).itertuples())]
nb = v[v.binding_result == "no_reportable_kd"].sample(10, random_state=0)
rows += [dict(name=f"nokd_{i+1}", cdrh3=r.cdrh3, kd_nM=np.nan, binding_result=r.binding_result, nmut=r.nmut) for i, r in enumerate(nb.itertuples())]
# synthetic extremes: most hydrophobic / most charged / most glycine loops the library offers
KD_H = dict(zip("AILMFWVCYHTSPGRNDQEK", [1.8,4.5,3.8,1.9,2.8,-.9,4.2,2.5,-1.3,-3.2,-.7,-.8,-1.6,-.4,-4.5,-3.5,-3.5,-3.5,-3.5,-3.9]))
v["gravy"] = v.cdrh3.map(lambda s: sum(KD_H[c] for c in s)/10)
for tag, sub in [("hydrophobic", v.nlargest(5, "gravy")), ("hydrophilic", v.nsmallest(5, "gravy"))]:
    rows += [dict(name=f"{tag}_{i+1}", cdrh3=r.cdrh3, kd_nM=r.kd_nM, binding_result=r.binding_result, nmut=r.nmut) for i, r in enumerate(sub.itertuples())]
# engineered-disulfide controls: the dataset showed +5.7 C for an extra pair. Add a CDRH3 with 2 Cys.
rows += [dict(name="cys_pair_in_loop", cdrh3="WGCDGFYCMD", kd_nM=np.nan, binding_result="synthetic", nmut=2)]
p = pd.DataFrame(rows).drop_duplicates("cdrh3").reset_index(drop=True)
p["vh_sequence"] = [vh_tpl.replace(TZ, c) for c in p.cdrh3]
assert p.vh_sequence.str.len().nunique() == 1
p.to_csv("data_panel.csv", index=False)
with open("panel.fa", "w") as f:
    for r in p.itertuples(): f.write(f">{r.name}|{r.cdrh3}\n{r.vh_sequence}\n")
print(f"panel: {len(p)} sequences, all {p.vh_sequence.str.len().iloc[0]} aa, differing ONLY in the 10-residue CDRH3")
print(p.groupby("binding_result").size().to_string())
