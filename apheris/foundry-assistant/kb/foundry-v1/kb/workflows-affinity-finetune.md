---
id: workflows-affinity-finetune
type: article
title: Fine-Tune Affinity
gloss: The workflow fine-tunes an affinity head on OpenFold3 trunk embeddings. It generates the embeddings for the train and test splits of an affinity query set, then trains the affinity head on them against your affinity labels, validating on the test split, so that the head learns the affinities of…
steps:
- name: Inputs
  detail: train/test queries .json + train/test labels .csv
  io: true
- name: fetch-msa
  detail: alignments from the Hub MSA server (CPU; with --msaServerURL)
  optional: true
- name: predict (embeddings)
  detail: train and test embeddings (GPU)
- name: train-from-embeddings
  detail: train the affinity head (GPU)
- name: Results
  detail: checkpoints/*.ckpt, metrics.csv, result.json
  io: true
examples:
- What files do I need to upload to fine-tune the affinity head?
- My query set is refused and it uses `id`, `molecule_type`, `chain_ids` and `main_msa_file_paths`. How do I fix it?
- what format should the label csv be in? what does affinity mean there
- Training never picks a best checkpoint and `best_checkpoint` is null in result.json. Why?
- Can I give a protein chain several MSA files or a folder of MSAs?
- What happens if a protein chain has no msa_path?
- How do I use the fine-tuned checkpoint to score new complexes?
- Can I trust the test split metrics as an independent evaluation?
---
The workflow fine-tunes an affinity head on OpenFold3 trunk embeddings. It
generates the embeddings for the train and test splits of an affinity query
set, then trains the affinity head on them against your affinity labels,
validating on the test split, so that the head learns the affinities of your
complexes. It produces the train and test trunk embeddings, training logs, and
fine-tuned affinity-head checkpoints.

## When to use it

- Fine-tune the affinity head on measured affinities of your own
  protein–ligand complexes.
- Score new query sets with the fine-tuned checkpoint afterwards, with
  [`affinity-predict`](../affinity-predict/README.md) and its `affinityCheckpoint` parameter.

## Data in

Upload `train_queries.yaml` and `test_queries.yaml` (or `.json`/`.yml`
for either split), one query set per split,
with the MSA files they reference, and `train_labels.csv` and
`test_labels.csv`.

- A query set holds `{"queries": [...]}`, in the query format of
  `apheris-affinity`. Each query holds its complex under `query`: a
  `query_id`, unique within the set, and `chains`. A protein chain has a
  `chain_id`, its `sequence` and its MSA under `msa_path`; a ligand chain has a
  `chain_id` and a `smiles`, a CCD `component_id`, or a structure file under
  `path`. `predict_affinity`, beside `query`, may name the chains the head
  scores; without it, every ligand chain is scored. A query may hold one
  ligand only.

```yaml
queries:
- query:
    query_id: target1_cmpd001
    chains:
    - chain_id: A
      sequence: <protein sequence>
      msa_path: msas/target1_A.a3m
    - chain_id: B
      smiles: <ligand SMILES>
```

- Each query holds its complex under `query`, with a `query_id`
  and its `chains`. The `query_id` names the query's output files, so it is
  unique within the set and holds only letters, digits, `.`, `_` and `-`, not
  starting with `.`; a set with any other id is refused. `predict_affinity`,
  beside `query`, may list the chain ids the head scores; without it, every
  ligand chain is scored. A query holds one ligand only.
- Every chain has its own `chain_id`, so a homodimer is two
  chains with the same `sequence`. A protein chain has a `sequence` and,
  optionally, its MSA under `msa_path`. A ligand chain has a `smiles`, a CCD
  `component_id` such as `ATP`, or a `path` to a structure file holding the
  one molecule.
- A protein chain takes one MSA file: a preparsed `.npz`, or an
  `.a3m` or `.sto` file, of any name. A folder of MSAs, or several files for
  one chain, is not accepted: choose one, or a preparsed `.npz`, which can
  hold the alignments of several databases. Paths are
  relative to the query set's folder, and every file they name must be
  uploaded with it. With an MSA server configured, a protein chain without
  `msa_path` gets one fetched; without a server, it is embedded from its
  sequence alone, which usually weakens the prediction. Set
  `"msa_path": null` to embed a chain without an MSA on purpose.
- The workflow refuses a query set in the older format, whose queries have an
  `id`, and chains with
  `molecule_type`, `chain_ids` and `main_msa_file_paths`. Convert one with
  `python -m apheris_affinity.scripts.convert_of3_query_sets <set>.json`, run
  in the `apheris-affinity` image, which writes `<set>.apheris.json` beside it
  and fails on a chain that lists more than one MSA file. Template fields are
  dropped: the workflow doesn't read templates.
- A label file has one row per labelled complex. `target_id`
  names the row's `query_id`, and every row's query must be in the split's
  query set. `affinity` is the measured value as pKd or pIC50, such as `7.6`
  for 25 nM; the head subtracts 6 internally. The optional `assay_id`
  groups rows into assays, for the per-assay metrics, and `source`,
  `uniprot_id` and `standard_type`, when given, split the groups further.
  Rows without `assay_id` are grouped by `target_id`, one row each, so the
  test labels need `assay_id` for training to select a best checkpoint.

Parameters:

| Param | Meaning | Default |
| --- | --- | --- |
| `numDiffusionSamples` | Diffusion samples per query | `5` |
| `diffusionSteps` | Diffusion denoising steps | `200` |
| `seed` | Random seed of the embedding runs | `42` |
| `maxEpochs` | Maximum training epochs | `50` |
| `batchSize` | Samples per batch | `8` |
| `headLr` | Affinity head learning rate | `0.0001` |
| `warmupSteps` | Linear learning-rate warmup steps; `0` disables it | `0` |
| `emaDecay` | EMA decay of the head | `0.8` |
| `of3Checkpoint` | The OpenFold3 trunk checkpoint, inside the image | `/opt/apheris/checkpoints/of3-p2-155k.pt` |
| `affinityCheckpoint` | The affinity-head checkpoint to start from, inside the image | `/opt/apheris/checkpoints/affbind_iqr_cartesian_interaction_only_h0h6zqam.pt` |

YAML and JSON represent the same input fields; JSON remains supported. Provide
only one file per manifest role. YAML uses JSON scalar types: `true`, `false`,
`null` and decimal numbers; IDs such as `on` and dates remain strings. Duplicate
keys, aliases, explicit tags and multiple documents are rejected. Input fields
and constraints come from the pinned model contract, where published, and the
model task. The workflow normalizes YAML to JSON for existing task readers. References marked as
files or directories by the model schema must exist inside the uploaded folder;
paths and schema-declared uniqueness rules are checked before tasks start.

## Results

- `train_embeddings/` and `test_embeddings/`: each split's trunk embeddings,
  one bundle per query, seed and ligand that holds its diffusion samples,
  listed in the split's prediction catalogue. A sample whose ligand doesn't
  bind the same site as the others keeps its catalogue row without an
  embedding.
- `finetune/`: the training outcome. `checkpoints/` holds the best
  checkpoint by validation and the last one; `result.json` names them, the
  epoch of the best, the validation metrics at each, and the metric that
  selected the best, `val/affinity_per_assay_spearman`. That metric covers
  the test split's assays of two or more rows whose affinities differ; with
  none, it is never logged, `best_checkpoint` is null, and
  `selected_checkpoint` names the last checkpoint. The metrics are MAE,
  MSE, Pearson and Spearman correlations, overall and per assay, in pKd units
  where they have one. Each checkpoint records the OpenFold3 trunk its
  embeddings came from. Pass the best checkpoint to
  `affinity-predict` as its `affinityCheckpoint`, with the same
  `of3Checkpoint`; it raises an error if the checkpoint was trained under a
  different trunk.

## Method

1. With an MSA server, `fetch-msa` of `apheris-msa` fetches one MSA per
   distinct protein sequence that lacks one, and attaches it to its chains.
2. `predict` of `apheris-affinity` runs the OpenFold3 trunk on one GPU for
   each split, by default `of3-p2-155k.pt`, which `of3Checkpoint` names,
   with the affinity head skipped, and saves the trunk embeddings. It
   reads each chain's full MSA and no templates, as native OpenFold3 does,
   and gives the same embeddings for the same inputs and `seed`.
3. Each label row is joined to its query's embedded samples by `target_id`,
   since the catalogue ids that training reads hash the run's config and
   checkpoint and only exist once the embeddings do.
4. `train-from-embeddings` trains the affinity head on one GPU, from
   `affinityCheckpoint` and with the architecture saved in it, on the train
   split, validating on the test split. By default it starts from the head
   that the image ships, `affbind_iqr_cartesian_interaction_only_h0h6zqam.pt`,
   which `affinity-predict` scores with.

## Limits

- The test split selects the best checkpoint, so its metrics are not an
  independent test. Measure the fine-tuned head on held-out queries with
  `affinity-predict` and its `affinityCheckpoint` parameter.
- A completed training run alone does not establish improved affinity
  ranking. With few rows per assay in the test split, the per-assay Spearman
  that selects the checkpoint is unstable.
- Use labels of one kind and scale; mixing pKd, pIC50 and Ki values, or
  different assays, adds noise. Report sample counts, missing embeddings, and
  leakage risks between the splits, such as shared ligands or close analogues.
- An unreadable sample is left out of training and of the metrics with a
  warning.
- Queries with more than one ligand are not supported yet.
- MSA search depends on the Hub's configured MSA server.
