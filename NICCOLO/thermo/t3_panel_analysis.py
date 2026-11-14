"""Analyse NanoMelt predictions for the 41-variant panel (identical except the 10-residue CDRH3).
Central question: can CDRH3 substitution move predicted Tm enough to matter, and does Tm trade off against affinity?"""
import sys
import numpy as np, pandas as pd
from scipy.stats import spearmanr, pearsonr
pred = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else "nanomelt_panel.csv")
pred.columns = [c.strip() for c in pred.columns]
tmcol = [c for c in pred.columns if "Tm" in c][0]
idcol = pred.columns[0]
pred["name"] = pred[idcol].astype(str).str.split("|").str[0]
pred["cdrh3"] = pred[idcol].astype(str).str.split("|").str[1]
p = pd.read_csv("data_panel.csv").merge(pred[["name", "cdrh3", tmcol]], on=["name", "cdrh3"], how="left")
p = p.rename(columns={tmcol: "tm_pred"})
wt = p[p.name == "trastuzumab_WT"].tm_pred.iloc[0]
p["dTm_vs_WT"] = p.tm_pred - wt
print(f"=== trastuzumab WT predicted Tm: {wt:.2f} C ===")
print(f"panel spread: min {p.tm_pred.min():.2f}, max {p.tm_pred.max():.2f}, range {p.tm_pred.max()-p.tm_pred.min():.2f} C, std {p.tm_pred.std():.2f} C")
print(f"variants predicted MORE stable than WT: {(p.dTm_vs_WT > 0).sum()} of {len(p)-1}")
print(f"  best gain: {p.dTm_vs_WT.max():+.2f} C | worst loss: {p.dTm_vs_WT.min():+.2f} C")
print("\n--- compare to the scale that matters ---")
print("  NanoMelt's own held-out MAE: 4.1 C. A predicted shift smaller than that is noise.")
print(f"  variants with |dTm| > 4.1 C: {(p.dTm_vs_WT.abs() > 4.1).sum()}")
print("\n--- by group ---")
print(p.groupby("binding_result").tm_pred.agg(["size", "mean", "std", "min", "max"]).round(2).to_string())
print("\n--- does predicted Tm trade off against measured affinity? ---")
q = p[p.kd_nM.notna()].copy()
if len(q) > 5:
    q["logkd"] = np.log10(q.kd_nM)
    print(f"  n={len(q)}  spearman(pred Tm, log10 KD) = {spearmanr(q.tm_pred, q.logkd).statistic:+.3f}  (positive = more stable means weaker binding)")
print(f"  spearman(pred Tm, n_mut) = {spearmanr(p.nmut, p.tm_pred).statistic:+.3f}")
print("\n--- the engineered-disulfide control ---")
cy = p[p.name == "cys_pair_in_loop"]
if len(cy): print(f"  CDRH3 with an added Cys pair: Tm {cy.tm_pred.iloc[0]:.2f} C ({cy.dTm_vs_WT.iloc[0]:+.2f} C vs WT)")
print("\n--- top and bottom 5 ---")
print(p.nlargest(5, "tm_pred")[["name", "cdrh3", "nmut", "kd_nM", "tm_pred", "dTm_vs_WT"]].round(2).to_string(index=False))
print(p.nsmallest(5, "tm_pred")[["name", "cdrh3", "nmut", "kd_nM", "tm_pred", "dTm_vs_WT"]].round(2).to_string(index=False))
p.to_csv("panel_scored.csv", index=False)
