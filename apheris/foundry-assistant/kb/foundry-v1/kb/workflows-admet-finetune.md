---
id: workflows-admet-finetune
type: article
title: Fine-Tune ADMET
gloss: The workflow fine-tunes an ADMET model on your own measured assay values with `apheris-admet`. By default it starts from the foundation model that the image bundles, `chemeleon`, and it writes a model that [`admet-predict`](../admet-predict/README.md) predicts with.
examples:
- What columns does train.csv need and in what format?
- My run failed with an internal error. What kinds of data problems cause that?
- can I train regression and classification assays together in one run?
- How do I fine-tune a model I already fine-tuned before?
- How do I use the fine-tuned model for predictions?
- I don't have a validation.csv. How is validation data chosen?
- What happens with duplicate measurements of the same molecule?
- Why does my second run fail on the output folder, and how long will training take?
---
The workflow fine-tunes an ADMET model on your own measured assay values with
`apheris-admet`. By default it starts from the foundation model that the
image bundles, `chemeleon`, and it writes a model that
[`admet-predict`](../admet-predict/README.md) predicts with.

## When to use it

- Train a model for an assay of your own, such as a logD, solubility or
  permeability measurement, from your compounds' SMILES and values.
- Train a classification model from class labels, such as `active` and
  `inactive`.
- Fine-tune a model you fine-tuned earlier on more data.

## Data in

Upload `train.csv`, your measurements, one row per measurement, under a
header row that names all four columns. Optionally, add `validation.csv`, in
the same layout, to choose the molecules the model is checked on while it
trains.

A regression file, `trainingType` `regression`:

```csv
assay_id,smiles,qualifier,value
logd_example,CCO,=,-0.31
logd_example,c1ccc2ccccc2c1,>,3.30
solubility_example,CCO,=,1.10
```

A classification file, `trainingType` `classification`:

```csv
assay_id,smiles,qualifier,value
herg_example,CCO,=,inactive
herg_example,c1ccccc1N,=,active
```

| Column | Each cell, for `regression` | Each cell, for `classification` |
| --- | --- | --- |
| `assay_id` | The assay's name, such as `logd_example` | The same |
| `smiles` | The molecule as a SMILES string | The same |
| `qualifier` | `=` for a measured value; `<` or `>` when the value is an upper or a lower bound, such as a solubility above the assay's range | `=` |
| `value` | The measured number, such as `-0.31`; a decimal point, no units | The class label, such as `active`; text, not a number such as `0` or `1` |

Every cell needs a value. The files:

- are comma-separated text, UTF-8, with the column names exactly as above,
  in lower case. The columns may come in any order, and the module ignores
  any other column.
- hold one kind of assay each: `trainingType` applies to every assay in the
  run, so regression and classification assays can't share a run.
- may hold several assays, which the model learns together. The assays need
  not cover the same molecules.
- may repeat a molecule within an assay: the module merges the repeats into
  one, by their median value for regression, and by their most common label
  for classification.
- sit alone in the input folder: the workflow refuses a folder without
  `train.csv`, with any CSV but `train.csv` and `validation.csv`, or with a
  CSV whose header lacks one of the four columns, before a task starts.

The module checks the rows, and drops a molecule whose SMILES string it can't
parse. It stops the whole run, with an internal error, when a cell is empty,
a `qualifier` holds anything but `=`, `<` or `>`, spaces included, a
regression `value` isn't a number, or a classification `value` is a number.
`mean_variance_estimator` takes `=` qualifiers only.

`validation.csv` holds only assays that `train.csv` holds, and, for
classification, only labels that `train.csv` holds for that assay. Without
it, the workflow holds out `validationFraction` of `train.csv`, at random,
with `dataSeed`.

The package's `examples/` folder holds `train.csv`, from the ADMET team: 477
measured values of one regression assay, `AX_ksol_v1`, for 418 molecules.
Some molecules are measured more than once, and the module merges their
values.

Parameters:

| Param | Meaning | Default |
| --- | --- | --- |
| `trainingType` | `regression` or `classification` | `regression` |
| `estimatorType` | `mesage_passing_neural_network`, spelled so by the module, or `mean_variance_estimator`, which also predicts each value's variance; regression only, and `=` qualifiers only | `mesage_passing_neural_network` |
| `baseModelTag` | The tag of the model to start from | `chemeleon`, the model inside the image |
| `modelDirectory` | The directory to find `baseModelTag` in, searched recursively | `/app/default-models`, the model inside the image |
| `validationFraction` | The share of `train.csv` held out, between 0 and 1, when there's no `validation.csv` | `0.2` |
| `epochs` | Training epochs; more than `warmupEpochs` | `50` |
| `warmupEpochs` | Epochs over which the learning rate rises to `initLr` | `2` |
| `initLr`, `maxLr`, `finalLr` | The learning rate after warmup, at its peak, and at the end | `0.0001`, `0.001`, `0.0001` |
| `modelSeed`, `dataSeed` | Seeds of the weight initialization and of the validation split | `42`, `0` |
| `logLevel` | The module's log level: `trace`, `debug`, `info`, `warning`, `error` or `none` | `info` |

`chemeleon` is always available, whatever `modelDirectory` names. To start
from a model you fine-tuned earlier, set `modelDirectory` to its folder and
`baseModelTag` to its tag. The workflow doesn't stage that folder: mount it
into the task at the path `modelDirectory` names.

## Results

Under `model/`, the workflow writes the fine-tuned model:

- `<tag>.pt`, the model's weights, and `<tag>-inference_config.json`, its
  assays, labels and type, where `<tag>` is `fine-tuning-<UTC time>`.
- `result.json`, whose `result.inference_tasks` lists one entry per assay
  and output: its `assay_id`, the new `model_tag`, its `task_type`,
  `estimator_type` and `task_output`, and, for classification, its
  `categorical_labels`.
- The module's `config.json` and `logs/`.

`model/` is a model directory as `admet-predict` reads it: run
`admet-predict` with `modelDirectory` set to it, mounted into the task, and
`predictionTasks` naming the `assay_id` and `model_tag` that `result.json`
lists, or left empty to predict with every model in the folder.

## Method

`finetune` of `apheris-admet` 0.99.0 trains a `chemprop` message
passing neural network from the base model on CPU. It merges replicate
measurements of a molecule, splits off the validation set, and keeps the
weights of the epoch with the best validation loss. Two class labels give a
`binary_classification` model; a mean-variance model predicts a `mean` and
a `variance` for each assay.

## Limits

- The model learns only from the data you give it: check its predictions on
  molecules it didn't train on before you rely on them.
- Training runs on CPU. The example's 477 rows take about a minute for 5
  epochs and about 8 minutes at the default 50, on a laptop running the
  amd64 image under emulation; thousands of molecules take much longer.
- A run writes into `model/` once: give each run a new `--output`, as the
  module refuses a folder that isn't empty.
- The module reports most mistakes in the rows, such as a label in a
  regression file, as an internal error, not as a data error.
