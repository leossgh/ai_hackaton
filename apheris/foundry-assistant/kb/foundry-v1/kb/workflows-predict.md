---
id: workflows-predict
type: article
title: Predict Structure
gloss: The production structure prediction workflow runs OpenFold3 or Protenix on a GPU to predict CIF structures of biomolecular complexes containing proteins, DNA, RNA and small-molecule ligands, described in a query JSON/YAML manifest or as uploaded CIF files.
steps:
- name: Inputs
  detail: queries JSON (chains + sequences) or .cif files
  io: true
- name: fetch-msa
  detail: alignments from the Hub MSA server (CPU; with --msaServerURL)
  optional: true
- name: predict-openfold3
  detail: OpenFold3 co-folding per seed × diffusion sample (GPU)
- name: Results
  detail: predicted CIFs + pLDDT/pTM/ipTM/PAE scores, result.json
  io: true
examples:
- How do I use my own fine-tuned checkpoint for prediction?
- My run failed at the MSA step and no GPU prediction started. Why?
- how do i skip the MSA for one protein chain
- Can I use pocket_constraint with Protenix?
- How are samples ranked, and what's the formula for model_ranking_score?
- Where do I find the output files and how do I know their names?
- How do I use a CIF as a template for my queries?
- Which model supports templates for DNA and RNA?
---
The production structure prediction workflow runs OpenFold3 or Protenix on a
GPU to predict CIF structures of biomolecular complexes containing proteins,
DNA, RNA and small-molecule ligands, described in a query JSON/YAML manifest or
as uploaded CIF files. An optional MSA search fetches alignments from the Hub's
configured MSA server, and optional templates, applied to the whole batch, guide
the prediction of every query.

## When to use it

- Predict the structure of one or more queries, each a set of chains with
  optional bonds, and rank the diffusion samples by the model's confidence
  scores.
- Compare OpenFold3 and Protenix, or two checkpoints of one of them, on the
  same queries: each run selects one model and one of its weights.
- Guide a binder chain towards a binding pocket with a query's
  `pocket_constraint`, which only OpenFold3 supports.
- Reuse known structures as templates for every query of a batch.
- To predict and score against known reference structures, use
  [`benchmark`](../benchmark/README.md). To fine-tune OpenFold3 on your own
  structures, use [`structural-finetune`](../structural-finetune/README.md).

## Data in

Upload either one JSON/YAML request with `{"queries": [...]}`, or one or more `.cif`
files, each of which becomes a query.

- A query lists its `chains`, with optional inter-chain `bonds`, or names a
  structure file with `path`, from which chains, entities and bonds are
  inferred; waters are dropped.
- A polymer chain has a `polymer_type` and a `sequence`, with nonstandard
  residues in parentheses, as in `AC(SEP)T`, and an optional `chain_id` and
  `msa_path`. A small molecule is a `smiles`, a CCD `component_id`, or a
  structure file under `path`; a branched polymer lists its `component_ids`
  and the `bonds` that join them.
- A query may set a `query_id`, of letters, digits, `.`, `_` and `-`, and a
  `pocket_constraint`: the binder chain, the binding residues, and an optional
  `max_distance` in Å.
- The CPU MSA task always matches top-level uploaded `.a3m` files (also
  accepting `msa_upload/*.a3m`) to required
  protein sequences before prediction. Without search, missing coverage fails
  this task; no GPU prediction starts. With search, uploaded matches are reused
  and only unmatched sequences are fetched from the configured server.
- Advanced CLI inline queries may explicitly set a protein chain's `msa_path`
  to JSON `null` to opt that sequence out of both matching and search. An omitted
  field still requires an MSA. CIF/path queries cannot use this opt-out. A named
  alignment must exist in the upload. Do not use a global missing-MSA override.
- Search fetches protein alignments only, so an RNA chain without an
  `msa_path` is predicted without an MSA.

A run selects its model, `openfold3` by default or `protenix`, and one of that
model's weights, each its own image, where the deployment can pull it:

| Model       | Weight       | Checkpoint                                              |
|-------------|--------------|---------------------------------------------------------|
| `openfold3` | `of3ob`      | OpenBind, 174k-step training run (2025-06-30); default  |
| `openfold3` | `of3p2`      | preview2, 155k-step training run                        |
| `protenix`  | `v1-default` | Protenix base default v1.0.0; default                   |
| `protenix`  | `v2`         | Protenix v2                                             |

To predict with your own checkpoint, such as fine-tuned weights, select its
model and pass the checkpoint's path as `weights`; the model's default image runs
it instead of its built-in one.

Model parameters, given as `--model-params`, are `num_diffusion_samples`
(default `1`), `seeds` (default `[42]`), and `template_paths`.
A parameter the selected model lacks is refused. Templates are CIF
files: upload each, and name it in `template_paths`, which then requires exactly
one JSON/YAML request; uploaded CIFs never become extra queries. A file can be both a
query and a template. Every file a request or template names is
uploaded-relative, without absolute paths or `..`.
The `writeDetailedScores` workflow setting defaults to `true`; set it to
`false` to omit the larger per-atom and token-pair score files.

The `examples/` folder of the workflow package holds a request for the CRK SH3
domain and its PDB entry 1B07 as a template.

YAML and JSON represent the same input fields; JSON remains supported. Provide
only one file per manifest role. YAML uses JSON scalar types: `true`, `false`,
`null` and decimal numbers; IDs such as `on` and dates remain strings. Duplicate
keys, aliases, explicit tags and multiple documents are rejected. Input fields
and constraints come from the pinned model contract, where published, and the
model task. The workflow normalizes YAML to JSON for existing task readers. References marked as
files or directories by the model schema must exist inside the uploaded folder;
paths and schema-declared uniqueness rules are checked before tasks start.

## Results

Under `predict/` of the run's output, the task writes, for each query, seed
and diffusion sample, a predicted structure as CIF and its confidence scores as
JSON. By default, it also writes the detailed per-atom and token-pair scores as
gzipped CBOR. Its result manifest,
`result.json`, lists each prediction with its `path`, `scores_path`,
`detailed_scores_path`, `query_id`, `query_index`, `seed` and `sample`; follow
it rather than guessing file names. `detailed_scores_path` is absent when
`writeDetailedScores` is `false`.

The scores hold, among others:

- pLDDT per atom and on average, in [0, 100]: confidence in local atom
  positions.
- pTM for the complex, per chain and, as ipTM, for interfaces and chain pairs,
  between 0 and 1.
- PAE and PDE between tokens, and the global gPDE, in Å; lower is more
  confident.
- A clash flag and `model_ranking_score`, by which the model ranks samples:
  `0.8 * iptm + 0.2 * ptm + 0.5 * disorder - 100 * clash_flag` for OpenFold3,
  which also reports the disorder score, and
  `0.8 * iptm + 0.2 * ptm - 100 * clash_flag` for Protenix.

Matched and fetched alignments land in the run's MSA output directory.

## Method

The workflow first validates the request against the shared prediction
contract, then runs the CPU `fetch-msa` task for protein matching and
coverage validation, and finally runs the shared `predict` task on one GPU
inside `apheris-openfold3` or `apheris-protenix`, whichever the run's
`--model` selects. Fetching is enabled only when an MSA server is configured.
Each weight is its own image, which holds that checkpoint and predicts with it.

Each templated chain is matched to its best-aligning chain in each template
file (normalized global-alignment score above 0.5), not by chain ID or order, so
several files can each contribute one template per chain. OpenFold3 templates
protein, DNA and RNA chains; Protenix templates protein chains only, up to 4
templates each, and only with v1.0.0 weights or later. Some chains may remain
untemplated; validation fails only if no chain of a query matches any file.
Ligands and other non-polymer entities are never templated.

## Limits

- Confidence scores are not experimental affinity or proof of biological
  activity.
- MSA search depends on the Hub's configured MSA server; check the coverage
  that a run actually got rather than inferring it from the server's
  availability.
- Templates apply to the whole batch. Acceptance runs check that templates are
  used and outputs are valid, not that they improve accuracy, and cover
  templates with MSA search disabled only.
- `pocket_constraint` works only with OpenFold3's preview2 and OpenBind
  weights.
- Report query failures alongside any available diagnostic artifacts; do not
  assume the model attempted every query after a failure.
