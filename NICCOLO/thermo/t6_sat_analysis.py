import pandas as pd, numpy as np
p = pd.read_csv("nanomelt_sat.csv"); p.columns=[c.strip() for c in p.columns]
tmc=[c for c in p.columns if "Tm" in c][0]
p = p.rename(columns={tmc:"tm", p.columns[0]:"name"})[["name","tm"]]
d = pd.read_csv("data_saturation.csv").merge(p, on="name", how="left")
print("scored:", d.tm.notna().sum(), "of", len(d))
wt = d[d.name=="WT"].tm.iloc[0]; m = d[d.name!="WT"].copy(); m["dTm"] = m.tm - wt
print(f"=== WT trastuzumab VH predicted Tm {wt:.2f} C | NanoMelt held-out MAE 4.1 C ===")
print(f"{len(m)} single framework mutants: mean dTm {m.dTm.mean():+.2f}, std {m.dTm.std():.2f}, range {m.dTm.min():+.2f} to {m.dTm.max():+.2f}")
print(f"stabilising at all (>0): {(m.dTm>0).sum()} ({(m.dTm>0).mean():.1%}) | > +2 C: {(m.dTm>2).sum()} | > +4.1 C (above MAE): {(m.dTm>4.1).sum()}")
print(f"destabilising < -4.1 C: {(m.dTm<-4.1).sum()}")
print("\n--- TOP 20 predicted stabilising single mutations ---")
print(m.nlargest(20,"dTm")[["name","wt","pos","mut","tm","dTm"]].round(2).to_string(index=False))
print("\n--- positions with the highest mean gain (mean over 19 substitutions) ---")
g = m.groupby(["pos","wt"]).dTm.agg(["mean","max","size"]).round(2).sort_values("mean",ascending=False)
print(g.head(12).to_string())
print("\n--- most fragile positions (biggest mean loss) = do not touch ---")
print(g.tail(8).to_string())
print("\n--- substitution preferences overall ---")
print(m.groupby("mut").dTm.mean().round(2).sort_values(ascending=False).to_string())
m.to_csv("saturation_scored.csv", index=False)
