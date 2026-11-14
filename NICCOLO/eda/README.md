# HER2 CDRH3 pre-filter (NICCOLO)

Fast screen for trastuzumab CDRH3 variants: hard rules → binder classifier → affinity ranker.
Built on the only labelled data we have, and validated with sequence clusters held out together.

**Scope:** 10-residue CDRH3 variants on the trastuzumab VH/VL framework — the **optimisation track only**.
Nothing here transfers to de novo designs (<70% identity to known antibodies); for those we have no labels.

## Files

| File | What it does |
|---|---|
| `prefilter.py` | The deliverable. `PreFilter().fit()`, `.score(seqs)`, `validate()`, `benchmark()`. Run it directly to reproduce every number below. |
| `eda.py`, `eda2.py` | Dataset EDA: ipTM/topmodel real-vs-shuffled, SPR-768 structure, first baselines |
| `p1_splits.py` | Checks the clonotype splits really are leakage-controlled |
| `p2_classifier.py` | FACS 524k classifier on the grouped splits, with novelty stratification |
| `p3_sanity.py` | Learning curve, permuted-label control, cluster purity |
| `p4_external.py` | External check: FACS-trained model scored against measured SPR |
| `p5_ranker.py` | Grouped-CV model comparison for both tasks, in and out of the constraint band |

`data/` and `models/` are git-ignored. Pull the inputs with the `scp` commands in the project README
(SPR-768, FACS 524k, and the `clonotype_split/0.7_0.15_0.15` splits from the Mehta `data.zip`).

## Validation design (why these numbers are not inflated)

Random CV on this data is meaningless: variants differ by 1–2 residues, so neighbours land on both sides
of a split. Three guards:

1. **Grouped CV.** Single-linkage clusters at Hamming ≤ 2 are held out together (179 quantified variants → 120 clusters).
2. **Constraint band.** Everything is also reported on variants ≥3 mutations from trastuzumab, since
   `abguard` requires >2 mutations. That is the region we are actually allowed to design in.
3. **No FACS leakage.** The 31 SPR sequences present in the FACS training data are removed before the
   FACS model is fitted, so its score is never a leaked label downstream.

The published clonotype splits are clean (zero sequence and zero cluster overlap), but **57% of their test
sequences still sit 1 mutation from a training sequence** (a random split gives 90%). So in-library scores
are not novelty scores — hence guard 2 and the external check below.

## Results

**Stage 1 — classifier, "will this give a measurable KD?"** (620 SPR outcomes, 179 positive)

| Model | AUROC | AP | AUROC, ≥3 mut |
|---|---|---|---|
| one-hot logistic | **0.927** | 0.875 | **0.915** |
| + mutation count + FACS score | 0.926 | 0.878 | 0.914 |
| mutation count alone | 0.800 | 0.645 | 0.763 |
| FACS score alone | 0.696 | 0.453 | 0.678 |

**Stage 2 — ranker, log10 KD** (179 quantified, grouped CV)

| Model | Spearman | ≥3 mut | Median true KD of its top 20 |
|---|---|---|---|
| one-hot + mut count + FACS ridge | **+0.687** | **+0.622** | **1.42 nM** |
| one-hot ridge | +0.667 | +0.610 | 1.42 nM |
| mutation count alone | +0.387 | +0.242 | 4.89 nM |
| FACS score alone | +0.063 | +0.131 | 81 nM |

Overall median KD is 86 nM, so the ranker's top 20 is a ~60× improvement in median affinity, and it
recovers the 0.023 nM best binder in the set.

**Ensemble verdict.** Use both stages, but the ensemble *features* barely help: adding the FACS score and
mutation count to the ranker is worth +0.02 Spearman and nothing at all to the classifier. The two stages
answer different questions (will it bind / how tightly), so both are kept.

## Throughput (laptop, single process, 2M random 10-mers)

| Stage | Rate |
|---|---|
| Featurise + classifier | **1.29M sequences/s** |
| Full pipeline incl. FACS GBM | 160k sequences/s |

The FACS gradient-boosting model is the only slow part (~285k/s) and contributes almost nothing, so for a
large screen drop it and run at ~1M/s. The entire 20^10 space is out of reach, but any realistic candidate
set (10^5–10^7) screens in seconds to minutes on CPU. **No GPU is needed for the pre-filter.**

## What the data does and does not support

- **The 524k FACS table is nearly useless for ranking.** Its 3 classes do not track measured KD: among the
  37 CDRH3s shared with the SPR table, median KD is 7.2 nM for `high`, 4.2 nM for `medium`, 15.4 nM for
  `low` — not monotonic.
- **In-library accuracy is misleading.** A gradient-boosting model reaches AUROC 0.995 on the FACS grouped
  test set, but only **0.757** on the external SPR set, where mutation count alone gets 0.802. The learning
  curve is smooth and a permuted-label control gives 0.47, so this is not leakage — the FACS label is simply
  easy to learn *within its own library*.
- **The small measured set carries the signal.** 620 SPR rows beat 524k FACS rows for both tasks.
- **Calibration limit.** The ranker is fitted on a variant range with median 86 nM and compresses at the
  tight end: it puts trastuzumab's own CDRH3 at 1.8 nM against a measured 0.03–0.18 nM. Treat its output as
  a ranking, not a predicted KD.
- **Not covered at all:** thermostability and epitope preservation, two of the three judged properties. No
  labelled data for either, so the pre-filter cannot speak to them.

## How to use it

```python
from prefilter import PreFilter, load
spr, facs = load()
pf = PreFilter().fit(spr, facs)
pf.score(["WGGDGFYAMD", ...])   # -> n_mut, p_facs_high, p_binder, pred_log10_kd
```

Rank on `pred_log10_kd` (lower is tighter) after gating on `p_binder`. This is a pre-filter, not evidence of
binding: survivors still go through **BASE VALIDATION** (`scripts/check_*.py`, `abguard`) and then structure
prediction. And per the Smorodina data in `eda.py`, do not then rank on ipTM alone — AF3 separates real from
shuffled pairs at only AUROC 0.75, and Boltz-2 at 0.64.
