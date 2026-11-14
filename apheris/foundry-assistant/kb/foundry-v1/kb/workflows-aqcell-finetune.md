---
id: workflows-aqcell-finetune
type: article
title: Fine-Tune Drug Response
gloss: Fine-tune AQCell's drug-response model on your harmonized gene-expression and cell-viability data, added to the data used to train its checkpoint. The workflow produces a reusable model bundle and per-epoch validation metrics for use with [AQCell prediction](../aqcell/README.md).
steps:
- name: Inputs
  detail: harmonised LINCS L1000 + GDSC2 parquet + split.parquet
  io: true
- name: fine-tune-dose-response
  detail: fine-tune AQCell (GPU)
- name: Results
  detail: per-epoch metrics, result.json
  io: true
examples:
- Can I still upload a dose-response CSV to fine-tune AQCell?
- My split.parquet only references LINCS samples. Do I still need the GDSC2 files?
- how is split.parquet supposed to be structured?
- What settings can I put in config.json and what are the defaults?
- I want to start training from a different checkpoint. How?
- Are the weights in weights/ the best epoch? How do I use them for prediction?
- When does training stop, and how long will it take?
- Can I add a new drug or cell line when fine-tuning?
---
Fine-tune AQCell's drug-response model on your harmonized gene-expression and
cell-viability data, added to the data used to train its checkpoint. The workflow
produces a reusable model bundle and per-epoch validation metrics for use with
[AQCell prediction](../aqcell/README.md).

## When to use it

Adapt AQCell to additional measurements of drugs and cell lines it already
knows, then predict with the resulting bundle. Use the prediction workflow
directly when no additional training is needed.

## Data in

Provide an extracted input directory of Parquet tables in SandboxAQ's harmonized
LINCS L1000 and GDSC2 formats. Data preparation is required: contact SandboxAQ
for harmonization. A dose-response CSV is no longer accepted.

```text
input/
├── preprocessed_lincs_l1000_v2020/
│   ├── expression/treatment.parquet
│   ├── expression/control.parquet
│   ├── metadata/experiment.parquet
│   └── metadata/compound.parquet
├── lincs_l1000_v2020_obs/obs.parquet
├── preprocessed_gdsc2/endpoint/treatment.parquet
├── gdsc2_obs/obs.parquet
├── split.parquet
└── config.json                         # optional
```

Treatment and control expression tables contain 978 landmark genes; experiment
metadata describes cell line, plate, drug, dose and time, and compound metadata
contains names, SMILES and InChIKeys. Observation tables identify treated samples
by drug InChIKey, Cellosaurus cell-line ID, dose and time. GDSC2 treatment data
contain drug-sensitivity wells and the dose-response curve's AUC.

`split.parquet` is indexed by `(dataset_artifact_name, sample_id, fold)` with a
`split` column: `train` or `val` in fold 0, `test` in fold -1. Other folds are
ignored. **Both datasets' files must be present**, even when the split references
only one dataset. Retain any additional harmonized metadata from the supplied
input package. Samples already in the model's training data are skipped.

Optional `config.json` settings:

| Setting | Meaning | Default |
| --- | --- | --- |
| `epochs` | Maximum training epochs, positive integer | 30 |
| `epoch_length` | Batches per epoch, positive integer or `null` | Full epoch |
| `base_seed` | Integer from 0 to 2147483647, or `null` | Checkpoint seeds |

The old `seed` and `use_all_user_data_for_training` settings are not supported.
`examples/config.json` is a short execution-check budget, not a full scientific
training run or a complete dataset. `--config filename.json` selects another
config file inside the input directory.

Training starts from `/opt/aqcell/weights/checkpoint` by default. `--weights`
alone selects another, which must already be available inside the task
container; the config takes no `weights`. The prediction bundle isn't a
training checkpoint.

## Results

- `weights/bundle.json`, `weights/training_set.json`, and
  `weights/model/exported_fn_<id>.pt2`: one exported model bundle, roughly
  10–13 MB. These are the **latest epoch's weights**, not a collection of
  checkpoints and not necessarily the best validation epoch. Mount `weights/`
  and pass its path to prediction's `--weights`. Use the matching AQCell
  prediction image; older AQCell images cannot consume this bundle.
- `metrics/epoch_0001.json`, …: metrics written live as each epoch finishes,
  with `epoch`, `iteration`, and a `metrics` map.
- `logs/training.log` and `logs/harness_config.json`: full training log and
  harness settings. Console output has one summary line per epoch.
- `config.json`: resolved settings.
- `result.json`: actual epochs trained, input train/validation/test row counts,
  seeds used, and relative artifact directories (`error.json` on failure).
  These input counts do not describe the complete combined training dataset.

The five validation metrics are:

| Metric key | Interpretation |
| --- | --- |
| `val/expression/PearsonDelta/aggregate/epoch` | Treatment-minus-control expression correlation across genes |
| `val/expression/PearsonDelta_T/aggregate/epoch` | Treatment-minus-control expression correlation across samples |
| `val/endpoint/Pearson/epoch` | Viability AUC Pearson correlation |
| `val/endpoint/Spearman/epoch` | Viability AUC rank correlation |
| `val/mtl/FischerZMeanPearsonX/aggregate/epoch` | Combined expression and viability correlation |

## Method

The workflow runs SandboxAQ's `apheris-aqcell-finetune`. The image contains its
pretrained checkpoint, training data and drug fingerprints. It adds nonduplicate
user samples and trains on fold 0 of the combined split under the original run's
training settings. Validation uses SandboxAQ's validation rows plus any
validation rows supplied by the user.

Training stops after five epochs without an improvement of 0.001 in
`mtl/FischerZMeanPearsonX`, or at the requested epoch limit. The default workflow
requests 8 CPUs, 48 GiB RAM and one GPU through the GPU compute class.
The image can also run on CPU, but this workflow requires a GPU. At least 32 GB RAM and about
4 GB free in `/tmp` are required. Runs can take hours: the supplier reports
about 9 minutes loading and 6.5 minutes per epoch on 16 vCPUs and a T4 with a
full-size input.

## Limits

Version 0.2 only accepts drugs for which the model already has Morgan
fingerprints, matched by InChIKey, and the 1,084 cell lines it already knows.
The task validates these constraints and required files before loading data.
This workflow does not add new drugs or cell lines to the model's vocabulary.

Validation metrics reflect the combined validation split, not automatically an
independent evaluation of your dataset. Example metrics from a short run are
not a scientific baseline, and successful execution does not establish model
improvement. Keep the exact seed values in `result.json` when reproducing a run.
