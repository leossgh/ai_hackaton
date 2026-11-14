"""Build Boltz-2 fold inputs for SPR variants whose KD we already know, so ipTM can be calibrated
against measured affinity before we trust it as a filter stage.

Run on the VM from ~/hackathon-team-3/apheris/rfd4:
  python3 make_calibration.py --ref runs/nick-ref/prepared/holo/queries.json --n 60 --out runs/nick-calib
"""
import argparse, json, re
from pathlib import Path
import numpy as np, pandas as pd

TZ = "WGGDGFYAMD"
SPR = Path.home()/"hackathon-team-3/apheris/hackathon-data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, help="an existing prepared/holo/queries.json, for the HER2 chains")
    ap.add_argument("--spr", default=str(SPR))
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--all-quantified", action="store_true", help="fold every quantified binder (for ranking power)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    ref = json.load(open(a.ref))["queries"][0]
    her2 = [c for c in ref["chains"] if c["chain_id"] in ("C", "D")]
    assert len(her2) == 2, "expected HER2 chains C and D in the reference"
    vl_ref = next(c["sequence"] for c in ref["chains"] if c["chain_id"] == "A")

    df = pd.read_csv(a.spr)
    df = df[df.cdrh3.str.len() == 10]
    df = df[df.cdrh3 != "ARDRIVDDYYYYGMDV"]
    df["nmut"] = df.cdrh3.map(lambda s: sum(x != y for x, y in zip(s, TZ)))
    # one VH framework / one VL across the library: verify before splicing
    assert df.vl_sequence.nunique() == 1 and df.vl_sequence.iloc[0] == vl_ref, "VL differs from the reference"
    assert df.apply(lambda r: r.vh_sequence.replace(r.cdrh3, "#"), axis=1).nunique() == 1, "VH framework is not constant"

    if a.all_quantified:
        sel = df[df.binding_result == "quantified_binding"].drop_duplicates("cdrh3").reset_index(drop=True)
        return write(sel, her2, a.out)

    q = df[df.binding_result == "quantified_binding"].copy()
    nq = df[df.binding_result == "no_reportable_kd"].copy()
    half = a.n // 2
    # positives: stratified across the measured KD range so we cover tight and weak binders
    q = q.sort_values("kd_nM")
    pos = q.iloc[np.linspace(0, len(q)-1, min(half, len(q))).astype(int)]
    # negatives: prefer the >=3-mutation band, the region we are allowed to design in
    nq3 = nq[nq.nmut >= 3]
    neg = nq3.sample(min(a.n - len(pos), len(nq3)), random_state=0)
    sel = pd.concat([pos, neg])
    # trastuzumab itself as a positive control (it is in the table 8x; keep one row)
    tzrow = df[df.cdrh3 == TZ].head(1)
    sel = pd.concat([tzrow, sel]).drop_duplicates("cdrh3").reset_index(drop=True)

    return write(sel, her2, a.out)

def write(sel, her2, outdir):
    queries = []
    for _, r in sel.iterrows():
        queries.append({"query_id": r.cdrh3, "chains": [
            {"chain_id": "A", "sequence": r.vl_sequence, "msa_path": None},
            {"chain_id": "B", "sequence": r.vh_sequence, "msa_path": None},
            *[dict(c) for c in her2]]})
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    json.dump({"queries": queries}, open(out/"queries.json", "w"), indent=1)
    cols = ["cdrh3", "binding_result", "kd_nM", "nmut"]
    sel[cols].to_csv(out/"manifest.csv", index=False)
    print(f"wrote {len(queries)} queries -> {out/'queries.json'}")
    print(sel.binding_result.value_counts().to_string())
    print("KD range:", round(sel.kd_nM.min(), 3), "to", round(sel.kd_nM.max(), 1), "nM")
    print("mutation counts:", sel.nmut.value_counts().sort_index().to_dict())

if __name__ == "__main__":
    main()
