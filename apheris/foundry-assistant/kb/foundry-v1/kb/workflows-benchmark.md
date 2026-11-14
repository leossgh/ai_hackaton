---
id: workflows-benchmark
type: article
title: Benchmark Structure
gloss: Compare one co-folding prediction per reference structure with its standardized reference. The run picks `openfold3` or `protenix` as the prediction model. Preprocessing must succeed for the entire cohort before prediction.
examples:
- I uploaded my structures folder with manifest.yaml and the references, but my CIF and PDB have the same filename stem (a.cif and a.pdb). Is that a problem?
- How do I set up the manifest for a benchmark run?
- where do I put precomputed a3m files?
- 'Can I set missing_msas to ignore for my CIF benchmark, or pass msa_path: null?'
- My run shows as failed but some predictions worked. Do I still get results?
- What does batchSize do and how are batches named in the task rows?
- How is aggregated_scores.json calculated? Is it a pooled score across all atoms?
- I set smokePredict=true and got perfect scores. Does that mean the model is good?
---
Compare one co-folding prediction per reference structure with its standardized
reference. The run picks `openfold3` or `protenix` as the prediction model. Preprocessing must succeed for the entire cohort before prediction.
Once prediction starts, independent batches are attempted; failures
produce a failed run with partial metrics for the successful predictions.

## When to use it

Evaluate a fixed model and weights on known structures. Use prediction when no
reference comparison is needed.
This workflow does not train models or compare multiple checkpoints in one run.

## Data in

Upload a directory containing one top-level JSON/YAML manifest and all files it
references. For example, `manifest.yaml` can contain:

```yaml
structures:
- path: references/a.cif
- path: references/b.pdb
```

Include both files under `references/` in the upload. Paths are relative to the
upload root, including optional `custom_components[].path` files. Entry fields
`custom_components`, `full_sequences`, and `include` pass through to preprocessing.
Structure stems must be unique, even across directories or CIF/PDB extensions.
The manifest defines the cohort; extra uploaded structures are ignored. Uploading
the manifest's assets is required and does not add duplicate samples. Do not
upload unrelated top-level JSON/YAML files: they are treated as extra manifests.
Without a manifest, only top-level `.cif` and `.pdb` files are selected.

Place precomputed `.a3m` files at the upload root; `msa_upload/*.a3m` is
also accepted for consistency with fine-tuning. Other subdirectories are not
searched. The CPU MSA task matches
query sequences to the standardized protein sequences and validates coverage.
With search disabled, every required sequence must have a matching uploaded MSA;
missing coverage fails the MSA task before any GPU prediction. With a configured
MSA server, supplied matches are reused and only unmatched sequences are fetched.
A server or matching failure also stops the workflow before prediction.

CIF/PDB benchmark inputs cannot opt out of MSA use. Global `missing_msas: "ignore"`
is rejected. Explicit `msa_path: null` is an advanced feature of inline
protein queries in the separate `predict` workflow, not benchmark references.

Discover `benchmark` through the selected execution client's workflow metadata.
For Hub, submit the dataset directory as the run's input. Use the client's
authentication, monitoring and download
instructions and the deployed workflow's settings. Inputs are uploaded to Hub.

| Workflow setting | Meaning and default |
| --- | --- |
| `model` | `openfold3` (default) or `protenix` |
| `batchSize` | Structures per prediction task; positive integer, default `10`, minimum `1`. The last batch may be smaller |
| `weights` | Checkpoint available to the prediction container; default empty, which selects the image's built-in checkpoint. A local filename does not upload weights |
| `modelParams` | JSON with `num_diffusion_samples: 1`, one nonnegative integer `seeds` entry (default `[42]`), and `missing_msas: "fail"` (required) |
| `expectedFeature`, `ligandize` | Comma-separated preprocessing options from the pinned task contract |
| `ignoreValidationIssues` | `true` or `false`; default false. Changes preprocessing validation, so record deliberate use |
| `metricSet` | Default reference-based metrics; `inference` selects reference-free metrics and does not measure reference agreement |
| `nDigits` | Optional integer rounding of task average scores |
| `msaServerURL`, `msaServerType`, `msaServerConfig` | Deployment MSA endpoint, required server type when an endpoint is set, and provider JSON |
| `msaOutput` | Optional server-side MSA directory; default `<output>/msa` |
| `smokePredict` | `true` or `false`; default false. Explicitly synthetic plumbing mode; only supported with `model=openfold3` |
| `writeDetailedScores` | Write each prediction's larger per-atom and token-pair score file; default `true` |

YAML and JSON represent the same input fields; JSON remains supported. Provide
only one file per manifest role. YAML uses JSON scalar types: `true`, `false`,
`null` and decimal numbers; IDs such as `on` and dates remain strings. Duplicate
keys, aliases, explicit tags and multiple documents are rejected. Input fields
and constraints come from the pinned model contract, where published, and the
model task. The workflow normalizes YAML to JSON for existing task readers.

## Results

`summary.json` records `status` (`succeeded` or `failed`), `complete`, original
cohort size, successful/failed counts, successful structures, and named failures.
Each successful entry indexes its reference, prediction and scores file using
output-relative paths and records the seed and sample. `prediction_failures.json`
lists failed structures and batches with available diagnostic log paths.
All structures in a failed or invalid batch are excluded from metrics and counted
as failed, even if the model left some prediction files behind.

`metrics.json` contains per-structure averages and weighted averages for successful
predictions. `aggregated_scores.json` takes the arithmetic mean of each available
metric across those structures, including the per-structure weighted averages.
This is not a pooled atom/residue-weighted cohort score. `metric_counts` gives the
number of contributing structures for each metric. Missing metrics are omitted,
never counted as zero; non-finite or entirely empty metric results fail reporting.
Compare identical cohorts and denominators, especially for partial runs.

Stage artifacts remain under `preprocess/`, `msa/`, `predict/`, and `metrics/`
(MSAs may use the configured directory). `uploaded-msas/` holds copies of the
upload's top-level `.a3m` files, which the MSA task matches. Real predictions have per-batch
`predict/<batch-id>/output/` (including `task.log` and `status.json`); `predict/result.json` combines
the successful result entries. Always follow the summary's paths.

**Failure policy:**

- Any preprocessing failure stops the run before MSA search or GPU prediction.
  `failed_structures.json` and `structures_report.json` name failures and reasons;
  the run error also names the failed structures. The user can fix or deliberately
  remove them and submit a new run. No samples are silently removed.
- Once preprocessing and the MSA task pass, each batch is attempted.
  A failed batch does not cancel other batches. Each batch is all-or-nothing:
  a nonzero exit or invalid/missing output excludes the whole batch from metrics.
  The model controls execution inside its batch; the workflow does not recover
  partial outputs from failed batches. Metrics are computed for the
  successful subset, reports are written with `status: failed` and `complete: false`,
  and the workflow then exits unsuccessfully so Hub also shows **failed**.
- If all predictions fail, reports contain zero successes and empty metrics; the
  metrics task is skipped. MSA-task or metrics-task failures also fail the run;
  final benchmark reports may not exist, but stage diagnostics remain available.
- Cancellation, loss of the workflow runner or storage, and other run-wide
  infrastructure failures can prevent remaining attempts or final reports.

Download available artifacts even when the run is failed. Preprocessing reports
describe preprocessing only; use prediction failures and summary for inference.
A client may report the failed status as an error even after saving those
files. Inspect the downloaded summary and metrics regardless, or download
individual artifacts. The run's failed status remains intentional.
Submit corrected inputs as a new run with fresh outputs. The package does not
automatically retry failed predictions or promise per-sample recovery through
Nextflow resume. Never treat stale reports in a reused output directory as a new
run's evidence.

## Method

The workflow scores predictions against standardized references, preserving query,
seed and sample identity. `batchSize` groups the sorted cohort into
batches; 15 structures at size 5 produce three model invocations
and three task pods. Each pod passes its whole batch to the model once. The model
owns within-batch execution; the workflow does not implement a per-query retry loop.
Preprocessing, MSA and metrics remain batched.

Prediction concurrency defaults to one GPU task per run; the deployment's GPU
compute class can configure Nextflow `maxForks` for its available capacity.
Each task requests a whole GPU plus its declared CPU and memory. Kubernetes
places the pods; a pending pod has not started inference. This per-run limit is
not a global GPU budget across users or runs. Larger batches amortize model startup
but increase the number of structures affected if the model aborts a task.

Task rows show `batch-<start>-<end>`, using inclusive positions starting at 1 in
sorted structure order. For example, 19 structures at batch size 10 produce
`batch-1-10` and `batch-11-19`, covering ten and nine structures respectively.
A task containing one structure shows its structure ID, even when it is the last
batch of a larger batch size. Rows also show execution status and task-specific
files. Artifact directories retain `batch-<first-structure-id>` for configured
batch sizes above one and the structure ID for batch size one.
`COMPLETED` means the module process finished; the final prediction report
also validates its outputs. Use `summary.json` and `prediction_failures.json` for
the authoritative scientific cohort counts, including invalid or missing results.

## Limits

Results measure structural agreement, not binding affinity or biological activity.
Record dataset provenance, model, weights, versions, seed, preprocessing and MSA
settings. Possible model-training overlap limits interpretation. Templates,
multiple seeds/samples and multi-model comparisons are not exposed here.

`smokePredict=true` copies standardized references as synthetic predictions. Reports
carry `synthetic: true`; perfect self-comparison scores are not model performance.
Preprocessing and metrics still run, and a configured MSA server is still used.
Live Hub acceptance and pinned-image verification remain release gates; local task
doubles do not establish real-model correctness or production readiness.
