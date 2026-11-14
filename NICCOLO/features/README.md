# Affinity ddG features: which ones are worth their cost (NICCOLO)

A cost/benefit breakdown of the 99 complex descriptors used for binding-ddG prediction, so we know
which features to keep when FoldX and ESM-IF are too expensive to run.

## Bottom line

1. **Fast features hold most of the signal.** T0 + T1 (42 features) gives mean LOCO r **0.548**,
   against **0.597** for all 99. Ten features alone reach **0.527**.
2. **DSSP and Voronoi are not worth the tooling.** +0.004 for two external dependencies.
3. **The expensive tiers buy little.** ESM-IF +0.027, FoldX +0.019 — the FoldX scan costs 26,676
   mutant builds for that.
4. **"Fast" still needs a complex structure.** T1 reads bound VHH–antigen coordinates (experimental
   or predicted), so it is *not* sequence-only.

All numbers are a ridge refit on 26-fold LOCO, ridge only — same recipe as DG32, no link stage.
Cost tiers are my assessment of what each feature needs as input; **nothing was timed**.

## Which feature sets are cheap

| tier | what it needs | features | importance share | mean LOCO r when added (cumulative) |
|---|---|---|---|---|
| T0 sequence-only | wild-type and mutant residue plus which chain; table lookups | 13 | 24% | 0.370 |
| T1 fast geometry | complex 3D coordinates; numpy neighbour counts and distances | 29 | 24% | 0.548 |
| T2 DSSP and Voronoi | external tools | 8 | 4% | 0.551 |
| T3 ESM-IF | an inverse-folding model run on the backbone | 14 | 14% | 0.578 |
| T4 FoldX scan | 19 substitutions at every site, 26,676 FoldX mutants | 35 | 34% | 0.597 |

Top-N by importance within T0 + T1: top 10 → 0.527, top 20 → 0.541, top 30 → 0.545.

Importance is a share of prediction variance in the all-99 model. Correlated features split credit,
so **read the tier refits as the real cost-benefit**, not the importance column.

## Top 20 fast features

| feature | what it is | flag | importance |
|---|---|---|---|
| blosum | BLOSUM62 score of the substitution | sequence-only | 6.3% |
| d_chg | change in charge | sequence-only | 4.2% |
| abs_hydro | absolute change in hydrophobicity | sequence-only | 3.6% |
| tip_partner_x_absvol | partner-chain atoms near the side-chain tip × absolute volume change | structure | 2.7% |
| n_contact | cross-interface atom pairs within 5 Å | structure | 2.7% |
| side_vhh | mutation is on the VHH rather than the antigen | sequence-only | 2.6% |
| tip_n_x_abschg | atoms near the side-chain tip × absolute charge change | structure | 2.4% |
| d_cen | distance to the interface-patch centre | structure | 2.3% |
| hse_up | residues on the side the side chain points to | structure | 2.3% |
| d_vol | change in volume | sequence-only | 2.1% |
| inv_dpart | 1/(1 + distance to the partner) | structure | 2.0% |
| d_hydro | change in hydrophobicity | sequence-only | 1.8% |
| abs_chg | absolute change in charge | sequence-only | 1.4% |
| hse_up_x_absvol | hse_up × absolute volume change | structure | 1.3% |
| cn_x_abschg | burial × absolute charge change | structure | 1.3% |
| hse_ratio | share of neighbours on the side-chain side | structure | 1.3% |
| ct_x_vol | contacts × absolute volume change | structure | 0.8% |
| hse_up_x_abshydro | hse_up × absolute hydrophobicity change | structure | 0.8% |
| cn_own | same-chain neighbours within 10 Å | structure | 0.7% |
| d_arom | change in aromatic flag | sequence-only | 0.6% |

The costly features that rank high: `foldx_ddg_total` (8.8%, T4), `llr_x_side` (4.1%, T3) and the
FoldX site means (T4).

## Tested on the HER2 pre-filter: no measurable gain

T0 was ported to trastuzumab CDRH3 variants in `../eda/seqfeat.py` and tested against the pre-filter's
classifier and ranker (`../eda/p11_features.py`, `p12_features_ci.py`, `p13_bootstrap.py`).

**Cluster-bootstrap 95% CIs on the paired difference all span zero**: ranker −0.047 [−0.095, +0.016] at
Hamming ≤2 and +0.060 [−0.099, +0.133] at ≤4; classifier +0.008 [−0.005, +0.026] and −0.012 [−0.034,
+0.028]. The pre-filter models were left unchanged. Details and the two methodology traps involved are in
`../eda/AGENT_GUIDE.md` §4.

This is not evidence against the tiering in this file, which is for a different task (binding ddG on a
complex, 26-fold LOCO). It only says T0 adds nothing *on top of a one-hot CDRH3 encoding* for
sequence-only KD ranking, where one-hot already spans the design space exactly.

## Where the tables live

On OLIVIA, `/cluster/projects/nn9603k/niccoloc/gmb_uio_lol/analysis/dg32_complex_descriptors/`:

- `feature_tiers.csv` — all 99 features with tier, type, importance and within-complex r
- `fast_features_arms.csv` — the tier refits

Job 2870052, 17 s on accel.
