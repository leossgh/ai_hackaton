---
id: workflows-affinity-predict
type: article
title: Predict Affinity
gloss: The workflow predicts binding affinities of protein–ligand complexes with the affinity head that ships with `apheris-affinity`, on OpenFold3 trunk embeddings.
steps:
- name: Inputs
  detail: test_queries.json + checkpoint.ckpt (+ optional test_labels.csv)
  io: true
- name: fetch-msa
  detail: alignments from the Hub MSA server (CPU; with --msaServerURL)
  optional: true
- name: predict (embeddings)
  detail: OpenFold3 embeddings per query (GPU)
- name: predict-from-embeddings
  detail: affinity head scores each complex (GPU)
- name: Results
  detail: affinity_predictions.csv, result.json
  io: true
examples:
- What does the predict affinity workflow do, and do I need to fine-tune anything first?
- My MSA files are .sto and the workflow rejects them. What format do I need?
- I have a queries.json in the old format with id, molecule_type, chain_ids and main_msa_file_paths. It gets refused. How do I fix it?
- what happens if I don't give an msa_path for a protein chain?
- How do I score compounds with my own fine-tuned checkpoint from affinity-finetune?
- Where do I find the pKd and binding probability in the output?
- Can I submit a query with two ligands?
- What are the default parameters and how can I skip saving structures?
---
The workflow predicts binding affinities of protein–ligand complexes with the
affinity head that ships with `apheris-affinity`, on OpenFold3 trunk
embeddings. It needs no fine-tuning run: it co-folds each query and scores its
ligand in one step, for a first estimate before you have affinity data of your
own.

## When to use it

- Predict the affinities of protein–ligand complexes without measured
  affinities of your own to fine-tune on.
- Get a first ranking of compounds against a target before fine-tuning.
- Score with a fine-tuned checkpoint from
  [`affinity-finetune`](../affinity-finetune/README.md) by supplying it as
  `affinityCheckpoint`.

## Data in

Upload `queries.yaml` (or `.json`/`.yml`), a query set with the MSA files it
references.

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

- The query set uses the format of `apheris-affinity`, which the
  `affinity-finetune` README describes in full. Each query holds one
  protein–ligand complex under `query`, with a `query_id` of letters, digits,
  `.`, `_` and `-`, unique within the set, and its `chains`, each with its own
  `chain_id`. A query holds one ligand only, as a `smiles`, a CCD
  `component_id`, or a `path` to a structure file.
- A protein chain takes one `.a3m` MSA file under `msa_path`, of any name,
  relative to the query set's folder; the workflow refuses other MSA formats.
  With an MSA server configured, a protein chain without `msa_path` gets one
  fetched; without a server, it is predicted from its sequence alone, which
  usually weakens the prediction. `"msa_path": null` predicts a chain without
  an MSA on purpose.
- The workflow refuses a query set in the older format, with `id`,
  `molecule_type`, `chain_ids` and `main_msa_file_paths`. Convert one with
  `python -m apheris_affinity.scripts.convert_of3_query_sets <set>.json`, run
  in the `apheris-affinity` image.
- The package's `examples/` folder holds `queries.json`, one JAK2–ligand
  complex without an MSA, for a run with an MSA server.

Parameters:

| Param | Meaning | Default |
| --- | --- | --- |
| `numDiffusionSamples` | Diffusion samples per query | `5` |
| `diffusionSteps` | Diffusion denoising steps | `200` |
| `seed` | Random seed of the prediction | `42` |
| `saveStructures` | Save the predicted structures beside the affinities | `true` |
| `of3Checkpoint` | The OpenFold3 trunk checkpoint, inside the image | `/opt/apheris/checkpoints/of3-p2-155k.pt` |
| `affinityCheckpoint` | Optional fine-tuned affinity-head checkpoint; uses the image's default head when omitted | `''` |

YAML and JSON represent the same input fields; JSON remains supported. Provide
only one file per manifest role. YAML uses JSON scalar types: `true`, `false`,
`null` and decimal numbers; IDs such as `on` and dates remain strings. Duplicate
keys, aliases, explicit tags and multiple documents are rejected. Input fields
and constraints come from the pinned model contract, where published, and the
model task. The workflow normalizes YAML to JSON for existing task readers. References marked as
files or directories by the model schema must exist inside the uploaded folder;
paths and schema-declared uniqueness rules are checked before tasks start.

## Results

Under `predictions/predictions/`, the workflow writes, for each query and seed:

- `<query_id>/seed_<seed>/<query_id>_seed_<seed>_affinity.json`: for each
  ligand of the query under `ligands`, the `pKd` and `binding_probability`
  that the head predicts, with the pTM, ipTM, pLDDT and ranking score of its
  structure, overall and per diffusion sample under `samples`.
  `binding_affinity` is the same value as the head outputs it, `pKd − 6`.
- With `saveStructures`, each diffusion sample's predicted structure in the
  query's folder, as `<query_id>_seed_<seed>_sample_<n>.cif`, an mmCIF file
  with pLDDT in its B-factors, beside its `_confidence.json`.

`prediction_catalog.parquet`, in the same folder, lists every prediction with
its files. `predictions/result.json` names the catalogue and lists the queries
that lack an output the run asked for. No trunk embeddings are saved.

## Method

1. With an MSA server, `fetch-msa` of `apheris-msa` fetches one MSA per
   distinct protein sequence that lacks one, and attaches it to its chains.
2. `predict` of `apheris-affinity` runs the OpenFold3 trunk on one GPU,
   by default `of3-p2-155k.pt`, which `of3Checkpoint` names, and scores each
   query's ligand with the affinity head. Without `affinityCheckpoint`, it uses
   the head that the image ships,
   `/opt/apheris/checkpoints/affbind_iqr_cartesian_interaction_only_h0h6zqam.pt`;
   with it, the supplied fine-tuned checkpoint is used instead. Trunk embeddings
   are not saved.

## Limits

- A predicted affinity is not a measured one. The head wasn't trained on your
  targets or compounds, so check its predictions against measured affinities
  before you rely on them, or fine-tune it on your own data with
  `affinity-finetune`.
- The workflow computes no metrics against labels.
- Queries with more than one ligand are not supported yet.
- MSA search depends on the Hub's configured MSA server.
