---
id: workflows-structural-finetune
type: article
title: Fine-Tune Structure
gloss: The production OpenFold3 structural fine-tuning workflow prepares train and validation structures, with supplied MSAs and optional search for missing alignments, generates an OpenFold3 training dataset from them, and fine-tunes OpenFold3 on a GPU.
steps:
- name: Inputs
  detail: train.json + validation.json (+ optional msa_upload/*.a3m)
  io: true
- name: fetch-msa
  detail: alignments from the Hub MSA server (CPU; with --msaServerURL)
  optional: true
- name: merge MSAs
  detail: combine uploaded and server alignments
- name: generate-openfold3-dataset
  detail: build the training dataset (CPU)
- name: finetune-openfold3
  detail: fine-tune OpenFold3 weights (GPU)
- name: Results
  detail: fine-tuned checkpoints, per-epoch metrics, result.json
  io: true
examples:
- I want to do a quick test run of fine-tuning with --maxSteps 500 but I only see two validation points. Why, and how do I get a real curve?
- What files do I need to upload to fine-tune?
- my run failed before GPU training saying MSA coverage is missing. what's going on?
- Can I use missingMsas=ignore or set msa_path to null for a chain in fine-tuning?
- One of my structures fails geometric validation (ligand stereo mismatch) and aborts the run. What are my options?
- Which checkpoints does fine-tuning keep and how big are they?
- How do I reduce GPU memory usage during fine-tuning?
- Can I change the learning rate or EMA decay?
---
The production OpenFold3 structural fine-tuning workflow prepares train and
validation structures, with supplied MSAs and optional search for missing alignments,
generates an OpenFold3 training dataset from them, and fine-tunes OpenFold3 on
a GPU. It produces fine-tuned checkpoints with training and validation metrics
per epoch, so that a model adapted to your structures can be compared with its
starting point on the same validation set.

The workflow offers the same OpenFold3 checkpoint builds as Predict Structure
for its module version: OpenBind (`of3ob`, the default) and preview2 (`of3p2`),
where available to the deployment. Selecting a checkpoint selects its image for
both dataset generation and fine-tuning. The base image without weights is not
offered alongside these checkpoint builds.

## When to use it

- Fine-tune OpenFold3 on your own experimental structures, from the selected
  image's built-in checkpoint or another one.
- Plan a short run to check data and settings before a full training budget.
- To clean and standardise structures first, use
  [`preprocess-structures`](../preprocess-structures/README.md); to predict
  structures with OpenFold3, use [`predict`](../predict/README.md).

## Data in

Upload `train.yaml`, `validation.yaml` (or `.json`/`.yml` for either split),
and every CIF or PDB file they
reference, together. Each manifest holds `{"structures": [...]}`; a structure
names its file with `path`, relative to the upload, and may set an `id`, which
defaults to the lowercased file stem, `custom_components` that its non-CCD
components use, and `full_sequences` for chains with unresolved or missing
residues. The workflow assigns each structure the split of its manifest. Keep
training and validation splits separate, and record their provenance and any
sequence overlap between them.

For PDB inputs, `include.chain_ids` also restricts MSA preparation to the
selected chains. The workflow makes a filtered copy for MSA matching while
retaining the original structure and selection for dataset generation.
Compressed structure names keep their full extension, such as `.pdb.gz`.

Upload `.a3m` alignments at the input root; `msa_upload/*.a3m` also remains
supported. The CPU MSA task always matches uploaded alignments by protein
sequence before dataset generation. With search disabled, missing protein
coverage fails before dataset generation or GPU training. With a configured
server, supplied matches are reused and only missing sequences are fetched.
Conflicting alignments for the same sequence follow the MSA task's ambiguity
validation; the workflow never picks an arbitrary filename.

This is the same preparation policy as Predict Structure and Benchmark
Structure. Per-chain `msa_path` (including the explicit null opt-out) belongs
only to inline queries in Predict Structure. Fine-tuning accepts neither that
opt-out nor `missingMsas=ignore`. The MSA task searches protein sequences;
supplied RNA alignments are retained for the dataset task's own validation.

`msaServerURL`, `msaServerType`, and `msaServerConfig` configure optional
search; a URL requires a server type. `msaOutput` defaults to `<output>/msa`.

Pass parameters with `--param`:

| Param | Meaning | Default |
| --- | --- | --- |
| `maxSteps` | Optimizer steps to run | `1000` |
| `stepsPerEpoch` | Optimizer steps per epoch: how often validation and checkpointing run | the task's, `1000` |
| `cropSize` | Per-sample token crop size, the main lever for memory use | `384` |
| `batchesPerStep` | Training batches accumulated into each optimizer step | `1` |
| `precision` | Floating point precision for training: `fp32` or `bf16` | `bf16` |
| `keepTopNCheckpoints` | Best checkpoints to keep, plus the most recent | `1` |
| `validationFailures` | A structure that fails geometric validation: `fail` aborts the run, `ignore` keeps it | the task's, `fail` |
| `preprocessingFailures` | A structure that fails preprocessing: `fail` aborts the run, `remove` drops it | the task's, `fail` |
| `missingMsas` | Only `fail` is accepted; missing protein coverage already fails in MSA preparation | the task's, `fail` |
| `weights` | The checkpoint to fine-tune from, a path inside the image | the selected image's built-in checkpoint |
| `ccdPath` | Chemical Component Dictionary, a path inside the image | the selected image's dictionary |

At the default of 1000 steps per epoch, a short run such as `--maxSteps 500`
is a single epoch and validates only twice, at Lightning's pre-step sanity check
and at the end, so there is no intermediate curve to early-stop or select a
checkpoint on. `--stepsPerEpoch 100 --maxSteps 500` gives five validation
points.

The dataset policies decide whether a run aborts on one bad structure:
`validationFailures=ignore` keeps a structure that fails geometric validation,
such as a ligand stereo label that disagrees between the CCD and the deposited
coordinates; `preprocessingFailures=remove` drops one that fails preprocessing;
missing protein alignments always fail during MSA preparation.
Choose the policy deliberately: relaxing one to make a run finish changes the
data.

The learning rate, its warmup, the EMA decay and the checkpoint metric keep the
task's defaults; the workflow exposes no parameter for them.

YAML and JSON represent the same input fields; JSON remains supported. Provide
only one file per manifest role. YAML uses JSON scalar types: `true`, `false`,
`null` and decimal numbers; IDs such as `on` and dates remain strings. Duplicate
keys, aliases, explicit tags and multiple documents are rejected. Input fields
and constraints come from the pinned model contract, where published, and the
model task. The workflow normalizes YAML to JSON for existing task readers. References marked as
files or directories by the model schema must exist inside the uploaded folder;
paths and schema-declared uniqueness rules are checked before tasks start.

## Results

- `dataset/`: the generated dataset, with the number of structures, chains and
  distinct reference molecules, and of missing MSAs, preprocessing failures and
  validation failures. Each policy logs its cases to its own YAML file, such as
  `missing_msa_sequences.yaml`, `preprocessing_failures.yaml` and
  `validation_failures.yaml`, either way.
- `finetune/`: for every epoch, the mean training and validation loss, the
  aggregate and per-structure metrics, and the retained checkpoint; epoch 0 is
  the sanity check. Compact CSVs hold the per-epoch validation metrics and the
  per-step training metrics. Checkpoints are kept by the best validation
  `lddt_inter_protein_ligand`, plus `last.ckpt` for the final partial epoch,
  and can be several GB each.

## Method

Each task runs the module version that `modules.yaml` pins.

1. The two manifests merge into one dataset manifest, each structure tagged
   `train` or `val`.
2. `fetch-msa` of `apheris-msa` matches supplied alignments and, with a
   configured server, fetches missing protein sequences.
3. The validated alignment directory is attached to the dataset manifest.
4. `generate-dataset` of `apheris-openfold3` builds the
   training dataset, using the Chemical Component Dictionary in the image.
5. `finetune` trains on one GPU from the selected image's built-in checkpoint
   or the supplied `weights`, validating on the `val`
   split every `stepsPerEpoch` steps.

## Limits

- Execution success alone does not demonstrate scientific improvement. Compare
  checkpoints on the same validation set, and inspect dataset counts, excluded
  structures, actual MSA coverage, finite losses and validation metrics.
- A short run with the default steps per epoch yields no validation curve.
- The dataset policies can drop structures or keep invalid ones; inspect the
  dataset logs and reports.
- The workflow does not check for sequence overlap between the training and
  validation splits; record it with the splits' provenance.
