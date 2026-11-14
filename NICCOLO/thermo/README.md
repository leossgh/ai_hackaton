# Thermostability: what we can and cannot do (NICCOLO)

Thermostability is one of the three judged properties and the only one with **no labelled data in the
hackathon set**. This folder establishes what is actually possible, with evidence.

## Bottom line

1. **Neither platform ships a Tm predictor.** Nebius' `stab-ddg` is [StaB-ddG](https://github.com/LDeng0205/StaB-ddG) —
   *binding* ddG, not folding stability. Foundry's "AQ" workflows are SandboxAQ small-molecule tools.
2. **Tm cannot be screened with cheap features.** On NanoMelt's own 639 measurements, composition/charge/
   hydrophobicity features reach Pearson +0.40, MAE 7.6 °C, against 8.3 °C for predicting the mean.
3. **[NanoMelt](https://doi.org/10.1080/19420862.2024.2442750) is the usable tool** (mAbs 2025; 639 measured
   nanobody Tm; published held-out Pearson 0.853, MAE 4.1 °C). Installed on the VM and **verified to
   reproduce its own reference output exactly**. Throughput ~45 sequences/s on the H100.
4. **CDRH3 cannot move thermostability.** Proven with a control, below. Spend CDRH3 on affinity/epitope only.
5. **Framework mutations can, on paper — but no single one clears the error bar**, and the combinations that
   do are dominated by charge-adding substitutions a VHH-trained model is biased toward. Not submission-ready.

## The CDRH3 result and its control

41 variants of the identical 120-aa trastuzumab VH, differing **only** in the 10-residue CDRH3
(10 tightest binders, 10 weakest, 10 non-measurable, hydrophobicity extremes, one engineered Cys pair):

| | Value |
|---|---|
| Predicted Tm spread, whole panel | **4.63 °C** (std 0.96) |
| Variants beyond the 4.1 °C MAE | **0 of 40** |
| Spearman(predicted Tm, measured KD) | **+0.001** |

The whole spread sits inside the predictor's error bar. To rule out "the model is just blind", single point
mutations in framework vs CDRH3 of the same VH:

| Region | n | Mean ΔTm | Range | Beyond 4.1 °C |
|---|---|---|---|---|
| Framework | 57 | −0.76 °C | −6.96 to +2.05 | 3 |
| CDRH3 | 20 | −0.09 °C | −1.30 to +0.56 | 0 |

|ΔTm| median 0.63 vs 0.19 °C, Mann-Whitney **p = 0.002**. The model resolves point mutations; CDRH3 is inert.

**Internal sanity check that the pipeline is sound:** the scan independently rediscovers the disulfide
effect. `C22Q` (removing a canonical disulfide cysteine) is predicted at **−5.03 °C**, and in NanoMelt's own
training data mean Tm is 41 °C with 0 cysteines, 67 °C with 2, 73 °C with 4, and drops back to 53 °C at 5
(odd ⇒ unpaired). Even counts stabilise, odd counts destabilise.

## Framework saturation scan

Every non-CDR position × all 19 substitutions = **1,577 single mutants**, 35 s of compute.

- mean ΔTm **−0.59 °C**; only 27.6% stabilising at all; 9 above +2 °C; **0 above +4.1 °C**; 19 below −4.1 °C
- most fragile positions (do not touch): **W36, C22, C96, L20, M83, V48, D73, E89**
- best single: `R98A` **+3.74 °C**

Combination test (30 sequences): gains are **strongly sub-additive and then harmful** — stack3 reaches
+4.28 °C where additivity predicts +6.23, and stack12 collapses to +1.44 °C where additivity predicts
+18.60 °C. Greedy ordering is not optimal: random 6-mutation subsets of the same pool average +4.16 °C and
the best reaches **+6.09 °C**. 12 of 29 combinations clear +4.1 °C.

## Three traps in those results

- **Charge bias.** 11 of the top 12 single mutations are `→ Glu`. Glutamate is the only substitution with a
  positive mean effect (+0.09) across the whole scan. NanoMelt appears to have learned "more acidic = more
  stable", so stacked hits are mostly a large net-charge change, with unknown cost to expression and function.
- **`V37F` is a VHH hallmark position.** The model partly wants to *nanobody-ify* trastuzumab's VH. That is a
  training-domain artifact, not evidence of stabilising a VH/VL pair.
- **Lone cysteines.** 4 of the top 20 single mutations introduce an unpaired Cys, which would fail `abguard`'s
  no-unpaired-cysteine check. `t7_combos.py` filters these out and asserts the cysteine count never changes.
- **Position 98** (the `...YYC-S-R|WGGDGFYAMD` junction, immediately N-terminal to CDRH3) dominates the top
  hits and is the single most likely place to disturb antigen binding. Also filtered out.

## The limitation that no amount of compute fixes here

NanoMelt predicts the Tm of an **isolated VHH domain**. Our optimisation designs are a VH/VL pair, whose
stability is governed largely by the VH/VL interface — which never enters the calculation. So these numbers
are a *relative ranking across same-framework VH variants*, not a Tm for the construct we would submit.
Treat any hit as a hypothesis for structure-based checking.

## Files

| File | What it does |
|---|---|
| `vm_install_nanomelt.sh` | Installs NanoMelt on the VM under `~/nick-work` |
| `t1_dataset.py` | The 639 Tm values; cheap-feature ceiling with identity-grouped CV; domain check |
| `t2_make_variants.py` → `t3_panel_analysis.py` | The 41-variant CDRH3 panel and its analysis |
| `t4_make_framework.py` | Framework-vs-CDRH3 point-mutation control |
| `t5_saturation.py` → `t6_sat_analysis.py` | 1,577-mutant framework saturation scan |
| `t7_combos.py` | Combination stacking, with the Cys/position-98 filters |

`ext/` (the cloned NanoMelt repo, 1 GB) and `data/` are git-ignored.

### Install gotchas

- Needs `openmm` and `pdbfixer` beyond the README's list (ImmuneBuilder/NanoBodyBuilder2 imports them).
- Put `nmenv/bin` on `PATH` or ANARCI fails with `FileNotFoundError: 'hmmscan'`.

```bash
ssh -i ~/.ssh/team-2 hackathon@89.169.114.1
export PATH=$HOME/nick-work/nmenv/bin:$PATH
nanomelt predict -i your.fa -o out.csv -align -ncpu 14
```
