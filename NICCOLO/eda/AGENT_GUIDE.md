# HER2 CDRH3 pre-filter — guide for agents

Read this before you rank, shortlist or submit any **optimisation-track** design. It tells you which
model to use, how it works, what it is validated to do, and the four mistakes that will waste your run.

**Scope.** 10-residue CDRH3 variants on trastuzumab's VH/VL framework. Nothing here applies to de novo
designs (<70% identity to known antibodies) — we have no labelled data for those.

**This is a pre-filter, not evidence of binding.** Survivors still go through BASE VALIDATION
(`NICCOLO/scripts/check_denovo.py`, `NICCOLO/scripts/check_optimisation.py`, `abguard`) before they are candidates.

---

## 1. The two models

| | Classifier | Ranker |
|---|---|---|
| **Question** | Will this variant give a measurable KD at all? | Among those, how tight? |
| **Model** | Logistic regression, L2, `C=0.3` | Ridge regression, `alpha=3.0` |
| **Features** | one-hot CDRH3 (10 positions × 20 residues = 200) | the same 200, plus mutation count (201) |
| **Trained on** | 620 measured SPR outcomes (179 with a KD, 441 without) | the 179 variants with a measured KD |
| **Needs the FACS data?** | no | no — `use_facs=True` restores it, worth +0.00 |
| **Target** | `quantified_binding` vs `no_reportable_kd` | log10 KD in nM |
| **Validated** | AUROC **0.927**; **0.913** inside the legal design band | Spearman **+0.687**; **+0.628** in band |
| **Beats** | mutation count alone (0.800), FACS score alone (0.696) | mutation count alone (+0.412), FACS alone (+0.063) |

Band figures are for ≥4 substitutions (n=556 for the classifier, n=131 for the ranker); `validate()` prints
both the ≥3 and ≥4 bands.

Both are in `prefilter.py`. Linear models are not a compromise here: gradient boosting and random forests
were tried and lost on both tasks (classifier 0.915 vs 0.927; ranker +0.628 vs +0.667). With 620 labels and
a 200-dimensional one-hot space, regularised linear models are the right capacity. Hyperparameters are not
fitted to the test folds either — nested CV, choosing them inside each fold, gives 0.925 and +0.649 (§3).

### How they work

The whole library shares one VH framework and one VL — only the 10 CDRH3 residues vary. So a position-wise
one-hot encoding spans the entire design space exactly, with no sequence model needed. The classifier learns
a per-position, per-residue weight: how much does tryptophan at position 1 help or hurt. The ranker learns
the same shape against log10 KD, plus two scalars (how far from trastuzumab, and what a model trained on the
524k FACS library thinks).

That additive form is most of the signal. Interactions between positions add little, which is why the
linear models win — and it is the honest reason the pre-filter is cheap.

### Practical effect

Ranking the 179 measured binders and keeping the top 20 gives a median KD of 1.4 nM against 86 nM overall.
But that top 20 is full of 1–2 substitution variants the identity rule forbids. **Inside the legal band
(≥4 substitutions) the top 20 has a median KD of 6.5 nM** — still ~13x better than the 86 nM median, and the
number to quote. A random pick of 10 gives 74 nM; the ranker gives 14 nM out-of-fold.

The tightest binders in this library are the ones closest to trastuzumab, which the identity rule rules out.
Expect the legal band to cost you roughly 4x in achievable affinity before any model is involved.

---

## 2. How to use it

Set up the data once (the inputs are git-ignored; `K=~/.ssh/team-2`, `H=hackathon@89.169.114.1`):

```bash
cd NICCOLO/eda && mkdir -p data
scp -i $K $H:hackathon-team-3/apheris/hackathon-data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv data/
# only for use_facs=True or to rerun the FACS experiments: the clonotype splits,
# extracted on the VM from zenodo-10831512-trastuzumab-ngs/data.zip
# scp -i $K -r $H:nick-work/splits data/
```

Then:

```python
import sys; sys.path.insert(0, "NICCOLO/eda")
from prefilter import PreFilter, load

spr, _ = load()                               # SPR table only; no FACS download needed
pf = PreFilter().fit(spr)                     # < 1 s
out = pf.score(["WGGDGFYAMD", "WAADGFYSIE"])  # any number of 10-mers
```

`PreFilter(use_facs=True).fit(spr, facs)` adds the FACS feature and a `p_facs_high` column. The audit
below shows it is worth nothing, so the default leaves it out.

`score()` returns one row per sequence:

| Column | Meaning | How to use it |
|---|---|---|
| `n_mut` | Hamming distance to trastuzumab's CDRH3 | **≥4** in practice, see below |
| `p_binder` | P(measurable KD) | **gate** on this |
| `pred_log10_kd` | predicted log10 KD, nM | **rank** on this, lower is tighter |

Recommended cascade:

1. **Hard rules first.** Drop anything whose CDRH3 matches one of the 525,063 provided CDRH3s (novelty),
   and anything with `n_mut < 4`. Cheapest stage, so it goes first.

   The **70% CDRH3 identity rule binds before the mutation count**: trastuzumab's CDRH3 is `SRWGGDGFYAMDY`
   (13 aa), so at equal length a design needs **at least 4 substitutions** to fall under 70% identity
   (9/13 = 69.2%, while 3 substitutions give 76.9%). The ">2 mutations" rule alone would let a 3-substitution
   design through, and `NICCOLO/scripts/check_optimisation.py` then rejects it on identity. Verified in
   `AGENTS.md`. Indels were not tested. The 3-mutation floor also applies against *every* CDRH3 in the
   reference set, not only trastuzumab's.
2. **Gate** on `p_binder`. There is no calibrated threshold — pick it from how many designs you can afford
   downstream, not from a magic number. `p_binder` is a ranking, and its absolute value is not a calibrated
   probability for novel designs.
3. **Rank** survivors on `pred_log10_kd`.
4. **BASE VALIDATION** on the shortlist (`abguard` decides the track; local labels are predictions).
5. **Refold the final handful** as a structural sanity check only — see §4.

### Throughput

Measured on a laptop, single process, 2M random 10-mers:

| Stage | Rate |
|---|---|
| Featurise + classifier | **1.5M sequences/s** |
| Full pipeline (default, no FACS) | 540k/s |
| Full pipeline with `use_facs=True` | 160k/s |

**No GPU is needed for screening.** Reproduce with `python prefilter.py`.

---

## 3. Leakage audit, and the one limit that matters

`p10_leakage_audit.py` checks whether the headline numbers are really out-of-sample.

| Check | Result |
|---|---|
| Identical sequences shared train/test | **0** in every fold |
| Closest train–test pair | Hamming **3** (grouping threshold 2, so it holds) |
| Permuted labels, classifier | **0.486** ± 0.023 |
| Permuted labels, ranker | **+0.045** ± 0.028 |
| Nested CV (hyperparameters chosen inside each fold) | 0.925 / +0.649, vs 0.930 / +0.671 fixed |
| Train on ≤4 mutations, test beyond (classifier) | **0.904**, vs 0.738 for mutation count |

No label leakage, no shared sequences, and model selection is worth only ~0.005 AUROC and ~0.02 Spearman.

### The ranker interpolates — this is the real limit

Sweeping the clustering threshold, with training-set size fixed at 143 by construction, so only train–test
*similarity* changes:

| Grouping | Classifier AUROC | Ranker Spearman |
|---|---|---|
| none (random CV) | 0.933 | +0.730 |
| Hamming ≤2 (reported) | 0.930 | +0.671 |
| Hamming ≤3 | 0.917 | +0.641 |
| Hamming ≤4 | 0.902 | **+0.433** |
| Hamming ≤5 | 0.845 | **−0.057** |

**Push test sequences ~5 mutations away from everything the ranker trained on and its signal vanishes.**
This is not a data-volume artefact: subsampling the training set at threshold 2 down to the same 143 points
still gives +0.670, against +0.433 and −0.057 for the genuinely distant splits.

What this means in practice:

- **Trust the classifier further than the ranker.** It degrades gracefully and survives distance
  extrapolation (0.904 training on ≤4 mutations and testing beyond).
- **The ranker is only meaningful for designs with close relatives among the 179 measured variants.** Check
  that before believing a `pred_log10_kd`: compute the minimum Hamming distance from your design to the
  training CDRH3s. At ≥5, treat the ranker's output as uninformative, not as a weak signal.
- This is the sharpest argument for getting more measured affinity data in the region we actually design in.

## 4. Four mistakes to avoid

1. **Do not validate with random cross-validation.** Variants differ by 1–2 residues, so neighbours land on
   both sides of a random split and every score inflates. Use `clusters()` (single-linkage, Hamming ≤2) as
   CV groups, as `validate()` does. Random CV reported AUROC 0.93 where grouped CV gives 0.927 — close here,
   but on the FACS data the same mistake turns 0.757 into 0.995.
2. **Do not trust in-library accuracy.** A model trained on the 524k FACS table reaches AUROC 0.995 on its
   own grouped test set and **0.757** on the external SPR set, where mutation count alone gets 0.802. The
   published clonotype splits are clean, yet 57% of their test sequences still sit 1 mutation from a
   training sequence. Always check against measured SPR.
3. **Do not use the FACS classes to rank affinity.** They do not track KD. Among the 37 CDRH3s shared with
   the SPR table, median KD is 7.2 nM for `high`, 4.2 nM for `medium` and 15.4 nM for `low` — not monotonic.
   The 524k table is for coarse binder/non-binder signal and for the novelty filter.
4. **Do not screen or rank on fold confidence.** See §5.
5. **Do not believe `pred_log10_kd` for a design far from the training set.** See §3.

---

## 5. Refolding: measured, and it does not screen

We folded 60 SPR variants with known outcomes (30 with KD from 0.023 to 13,863 nM, 30 with no measurable
KD) against HER2 domain IV with the 1N8Z template, using **Boltz-2** and **Protenix v2**.

**Cost on our H100, measured:** Boltz-2 **7.9 s/structure** (475 s for 60), Protenix v2 **12.8 s/structure**
(772 s for 60). The ~80 s per fold quoted in the Nebius `START-HERE.md` does not apply to this setup.

**Every metric lands at chance** for separating binders from non-binders (n=60, 30/30):

| Metric | AUROC |
|---|---|
| Boltz-2 ipTM | 0.502 |
| Boltz-2 `min_ipae`, CDRH3↔HER2 interface | 0.497 |
| Boltz-2 pLDDT | 0.356 |
| Protenix ipTM | 0.502 |
| Protenix antibody↔HER2 interface ipTM | 0.552 |
| **sequence classifier**, grouped CV on the same 60 | **0.849** |

Among the 30 measured binders no fold metric tracks KD (all p ≥ 0.20). Adding fold metrics to the sequence
features made the classifier **worse** under grouped CV (0.849 → 0.806). **Boltz-2 ipTM ≥ 0.7 passes 100%
of true non-binders**, so as a gate it removes nothing. Ranking the binders by any fold metric and keeping
the top 10 gives a median KD of 58–119 nM against 74 nM for a random pick.

Part of the cause is structural: all 60 complexes share 326 of 336 tokens, so global confidence is dominated
by the unchanged framework and HER2, and Boltz-2 ipTM spans only 0.070. That does **not** explain
`min_ipae`, which has a real spread of 3.0 and is still at chance. The two fold models barely agree with
each other (Spearman +0.28).

**Limits of this result.** It covers CDRH3 optimisation on a fixed framework, one diffusion sample and one
seed. It does **not** transfer to de novo designs, where the whole binder changes — that is the regime the
Smorodina benchmark covers, and there AF3 ipTM does carry signal (AUROC 0.75, with Boltz-2 at 0.64 and
Chai-1 at 0.57; see `eda.py`). At n=60 we can rule out a strong effect, not a weak one. Every Protenix
metric correlates with KD in the *right* direction (ipTM −0.237) without reaching significance, so a
180-binder Protenix run is in progress to resolve it; this section will be updated with the result.

**So:** refold the designs you actually submit, as a plausibility check and because provenance is scored.
Do not use refolding to screen or rank, and do not rank on ipTM alone even for de novo designs.

---

## 6. What is not covered

- **Thermostability** and **epitope preservation** — two of the three judged properties. No labelled data
  for either, and no predictor chosen. The pre-filter says nothing about them.
- **Expression.** Adaptyv reports that Aggrescan 3D, SoluProt, NetSolP and ProteinMPNN with soluble weights
  improved expression success. Not evaluated here.
- **Calibration.** The ranker is fitted on a range whose median is 86 nM and compresses at the tight end: it
  puts trastuzumab's own CDRH3 at 1.8 nM against a measured 0.03–0.18 nM. Treat the output as a ranking, not
  a predicted KD.

## 7. Reproducing the numbers

```bash
cd NICCOLO/eda
python prefilter.py        # grouped-CV validation + throughput benchmark
python p1_splits.py        # are the clonotype splits leakage-controlled?
python p3_sanity.py        # learning curve, permuted-label control
python p4_external.py      # FACS-trained model vs measured SPR
python p5_ranker.py        # full model comparison, both tasks
python p6_iptm_calib.py    # do fold metrics add anything?
python p7_ipae.py          # interface PAE from the detailed scores
python p9_protenix.py      # second fold model
python p10_leakage_audit.py # leakage audit: permutation, threshold sweep, nested CV, extrapolation
```

Requires `pandas numpy scikit-learn scipy matplotlib cbor2`. Full results and caveats: `README.md`.
