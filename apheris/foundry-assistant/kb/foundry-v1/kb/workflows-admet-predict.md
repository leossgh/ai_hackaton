---
id: workflows-admet-predict
type: article
title: Predict ADMET
gloss: 'The workflow predicts ADMET properties of small molecules from their SMILES with `apheris-admet`, using a directory of ADMET models: models that [`admet-finetune`](../admet-finetune/README.md) wrote, or Apheris ADMET models you already have.'
examples:
- I ran the predict ADMET workflow without setting anything and the values look meaningless. Why?
- What does molecules.csv need to look like?
- my run failed with an internal error and my molecule ids are 1, 2, 3... what's wrong
- What happens if one SMILES in my file is invalid?
- How do I predict with only some of the models in my directory?
- I set modelDirectory to my own folder but it can't find the models
- Where do the results go and what's in them?
- How is classification output different from regression output?
---
The workflow predicts ADMET properties of small molecules from their SMILES
with `apheris-admet`, using a directory of ADMET models: models that
[`admet-finetune`](../admet-finetune/README.md) wrote, or Apheris ADMET models
you already have. The image bundles no model that can predict: its
`chemeleon` is a base model to fine-tune from, so without models of your own,
run `admet-finetune` first.

## When to use it

- Predict absorption, distribution, metabolism, excretion and toxicity
  properties for a set of molecules.
- Predict with the models that an ADMET fine-tuning run produced, by naming
  their directory: [`admet-finetune`](../admet-finetune/README.md) writes
  one from your own measured values.

It needs those models: the workflow runs without `modelDirectory`, but then
predicts with `chemeleon`, which has no predictive head, and its values mean
nothing.

## Data in

Upload one file, `molecules.csv`: one row per molecule, under a header row
that names all three columns.

```csv
molecule,molecule_format,molecule_identifier
CCO,smiles,ethanol
c1ccccc1O,smiles,phenol
CC(=O)Oc1ccccc1C(=O)O,smiles,
```

| Column | In the header | Each cell |
| --- | --- | --- |
| `molecule` | Required | Required: the molecule as a SMILES string |
| `molecule_format` | Required | Required: `smiles`, in lower case, the only format the module reads |
| `molecule_identifier` | Required | Optional: your name or ID for the molecule, which its prediction keeps; leave the cell empty for none |

The file:

- is comma-separated text, UTF-8, with the column names exactly as above,
  in lower case. The columns may come in any order, and the module ignores
  any other column.
- sits alone in the input folder: the workflow refuses a folder that holds
  any other CSV, or no `molecules.csv`, before a task starts.
- keeps its rows' order in the results, duplicates included.

The module checks the rows, and stops the whole run, with an internal error,
when:

- the header lacks one of the three columns, `molecule_identifier`
  included;
- a `molecule` cell is empty, or a `molecule_format` cell isn't `smiles`;
- every identifier is a whole number, however large, such as `1`, `2` or
  `4497450133507029889`, with or without empty cells: the module reads the
  column as numbers, not text. Add a letter to them, such as `mol-1`; a
  column that mixes numbers and text works.

A SMILES string the module can't parse doesn't stop the run: its molecule
gets a `message` and no predictions.

The package's `examples/` folder holds `molecules.csv`, from the ADMET
team: 100 molecules, none of them in `admet-finetune`'s example
`train.csv`, so they also test a model fine-tuned on it.

Parameters:

| Param | Meaning | Default |
| --- | --- | --- |
| `modelDirectory` | The directory of model checkpoints and their configuration files, searched recursively; set it to predict | `/app/default-models`, the image's `chemeleon`, which can't predict |
| `predictionTasks` | A JSON list of the models to predict with, each `{"assay_id": ..., "model_tag": ...}`, with an optional `task_output` | Empty: every model in `modelDirectory` |
| `logLevel` | The module's log level: `trace`, `debug`, `info`, `warning`, `error` or `none` | `info` |

A `predictionTasks` entry names one model by its `assay_id` and `model_tag`,
as its configuration file records them. `task_output` is `prediction` by
default; `mean` and `variance` apply to a mean-variance estimator. The
workflow checks the list against the module's contract before a task starts,
and the module refuses a model that `modelDirectory` doesn't hold.

`modelDirectory` is a path the task reads in its container, which the
workflow doesn't stage: a directory of your own must be mounted into the task
at that path.

## Results

Under `predictions/`, the workflow writes:

- `predictions.json`, which lists under `molecule_predictions` one entry per
  input row, in input order: its `molecule`, `molecule_format` and
  `molecule_identifier`, a `message` when the module couldn't predict it,
  such as for a SMILES it can't parse, and its `predictions`, one per model.
- `result.json`, which names `predictions.json`, beside the module's
  `config.json` and `logs/`.

```json
{
  "molecule_predictions": [
    {
      "molecule": "CCO",
      "molecule_format": "smiles",
      "molecule_identifier": "ethanol",
      "predictions": [
        {
          "model_tag": "fine-tuning-2026-10-28T12-09-38",
          "assay_id": "AX_ksol_v1",
          "model_type": "regression",
          "output_type": "prediction",
          "output": {"prediction": 2.685}
        }
      ]
    }
  ]
}
```

A prediction names its model by `model_tag` and `assay_id`, and its
`model_type` and `output_type` say what `output` holds:

| `model_type` | `output_type` | `output` |
| --- | --- | --- |
| `regression` | `prediction` | `{"prediction": <value>}` |
| `regression` | `mean`, `variance` | `{"mean": <value>}`, `{"variance": <value>}`, from a mean-variance model |
| `classification`, `binary_classification` | `prediction` | Each label's probability, as `{"<label>": <probability>}` |

A molecule with a `message` has an empty `predictions` list.

## Method

`predict` of `apheris-admet` 0.99.0 loads each model in
`modelDirectory`, or those that `predictionTasks` names, and predicts every
molecule on CPU.

## Limits

- A model predicts only the assays it was fine-tuned on, in their units.
  Check its predictions against measured values before you rely on them.
- The workflow reads SMILES only.
- It computes no metrics and calibrates no uncertainty.
