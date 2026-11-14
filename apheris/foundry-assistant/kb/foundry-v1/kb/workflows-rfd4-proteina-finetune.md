---
id: workflows-rfd4-proteina-finetune
type: article
title: RFD4-Proteina fine-tuning
gloss: Adapt the released RFD4-Proteina denoiser to an upstream-compatible Parquet/CIF dataset on one CUDA GPU. Training updates the denoiser, keeps the autoencoder frozen and starts fresh optimizer state.
examples:
- What columns does my training Parquet need? I only have a table of CIF file paths.
- how do i run the one-step example for rfd4 finetune?
- How much GPU, RAM and disk should I plan for?
- I finished training. How do I generate a design with the fine-tuned weights?
- Can I resume training from a checkpoint with the optimizer state?
- What does an epoch mean here, and what gets trained?
- Is the last checkpoint the best one? How do I know my fine-tuned model is better?
- What are the default training parameters and where do the CIFs go?
---
Adapt the released RFD4-Proteina denoiser to an upstream-compatible Parquet/CIF
dataset on one CUDA GPU. Training updates the denoiser, keeps the autoencoder
frozen and starts fresh optimizer state.

## When to use it

Use this workflow when you already have a structural training dataset in the
upstream format. Start with a bounded training check, then compare the retained
EMA checkpoint with the released baseline on held-out design inputs. Use
[rfd4-proteina-design](../rfd4-proteina-design/README.md) for generation.

### One-step example

The example below performs one optimizer update on four public tutorial records.
It checks execution and checkpoint saving; it does not evaluate learning.
From a toolkit checkout, use the prerequisites and registry setup in the
[workflow development guide](https://github.com/apheris/foundry-toolkit/blob/main/workflows/DEVELOPMENT.md).
The selected module must be available to the execution environment.
Choose a fresh `RUN` directory:

```bash
EXAMPLE="$PWD/workflows/rfd4-proteina-finetune/examples"
RUN="$PWD/.workflow-dev/rfd4-finetune-one-step"
mkdir -p "$RUN"
IMAGE=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["images"][0])' \
  workflows/rfd4-proteina-finetune/contracts/rfd4-proteina.json)
docker pull "$IMAGE"
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$EXAMPLE:/example:ro" -v "$RUN:$RUN" --workdir "$RUN" \
  "$IMAGE" python /example/prepare.py "$RUN/data"
task workflow:generate workflow=rfd4-proteina-finetune policy=local \
  output="$RUN/generated-finetune"
task workflow:run workflow=rfd4-proteina-finetune \
  generated="$RUN/generated-finetune" params="$RUN/data/params.json" \
  config="$EXAMPLE/runtime.config" output="$RUN/train"
```

`prepare.py` downloads `test_dataset/test_dataset.tar.gz` from `nvidia/RFD4-Proteina`
at the revision recorded in that script, verifies its SHA-256 and selects four
records while preserving all Parquet columns and nested CIF paths.
It writes `train.parquet`, `cifs/`, `provenance.json` and location-specific
`params.json`. The portable recipe is `examples/finetune.json`: one epoch, one
step, batch size one, learning rate 0.00001 and seed 42. Regenerate parameters if
the dataset moves. To reuse the archive, pass
`prepare.py --archive /path/to/test_dataset.tar.gz OUTPUT`.

For Hub execution, upload the prepared Parquet and complete CIF tree, then set
`input` and `structures` to their uploaded paths using the execution client's
instructions. The preparation script runs on CPU; the training task needs a GPU.

### Extended training example

After the one-step check, use `examples/tutorial.json` for 200 full-denoiser
updates on the same four records: four epochs of 50 steps, batch size one,
learning rate 0.00001 and seed 42. Reuse `EXAMPLE` and `IMAGE` from above with a
fresh `RUN` directory:

```bash
RUN="$PWD/.workflow-dev/rfd4-finetune-tutorial"
mkdir -p "$RUN"
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$EXAMPLE:/example:ro" -v "$RUN:$RUN" --workdir "$RUN" \
  "$IMAGE" python /example/prepare.py --recipe /example/tutorial.json "$RUN/data"
task workflow:generate workflow=rfd4-proteina-finetune policy=local \
  output="$RUN/generated-finetune"
task workflow:run workflow=rfd4-proteina-finetune \
  generated="$RUN/generated-finetune" params="$RUN/data/params.json" \
  config="$EXAMPLE/runtime.config" output="$RUN/train"
```

Inspect `$RUN/train/results/finetune/result.json`, the training log, resolved
configuration and retained checkpoints. Continue with
[checkpoint reuse](#reuse-a-checkpoint-for-design) to generate a monomer with the
saved EMA weights. This example demonstrates execution and checkpoint reuse;
it does not establish improved designs.

## Data in

Provide an upstream training Parquet file and its CIF directory. The dataset
requires `example_id`, `path`, and the metadata consumed by the upstream PLINDER
design-task transforms. An arbitrary table containing only file paths is
insufficient. Every Parquet `path` resolves from the CIF root; preserve nested
paths. The model validates training data inside the task.

| Parameter | Meaning | Default |
| --- | --- | --- |
| `input` | Upstream-compatible training Parquet file | Required |
| `output` | Persistent result root | Required |
| `structures` | CIF root for Parquet paths | `cifs/` beside the Parquet |
| `epochs` | Fine-tuning epochs | `1` |
| `stepsPerEpoch` | Training steps per epoch | `50` |
| `batchSize` | Training examples per batch | `1` |
| `learningRate` | Denoiser optimizer learning rate | `0.00001` |
| `seed` | Training random seed | `42` |
| `checkpoint` | Uploaded initialization checkpoint | Released flow weights |
| `logLevel` | `debug`, `info`, `warning`, `error`, `critical` | `info` |

Keep output and Nextflow work directories outside the CIF tree. Uploaded
checkpoints must match the model architecture. The bundled released flow weights
and paired autoencoder remain under `/weights` inside the image.

### Resources

The task requests eight CPUs, 64 GiB host RAM and one NVIDIA GPU. This is a tested
allocation for the one-step example, not a general minimum. Host RAM and GPU
VRAM are separate resources. Use a GPU from the
[upstream supported hardware list](https://rfd4-proteina.org/latest/installation.html#supported-hardware)
and measure peak usage on the intended dataset before increasing batch size.
The historical one-step test used an A100 80 GB and Docker's default 64 MiB
shared memory with the recipe's zero-worker loader.

Plan for 25 GiB free output space for the one-step example, plus image and
dataset storage. That test wrote about 16.84 GB, including four checkpoints of
about 4.21 GB each. Longer runs require a separate storage estimate.

## Results

Read `finetune/result.json` under the workflow output root. Its `result` object
lists regular and EMA files in `checkpoints`, the training directory in
`artifacts`, and captured output in `log`. Paths resolve from that task output
directory. Inspect finite losses, actual training steps and nonempty checkpoints;
on failure inspect `error.json` and the model log. Preserve the resolved
configuration, dataset provenance, image digest and starting weights.

### Reuse a checkpoint for design

Select a retained `*-ema.ckpt` from the result's checkpoint list and upload it
with the input to `rfd4-proteina-design`. Set that workflow's `checkpoint` to the
uploaded file and retain the same paired autoencoder. A checkpoint initializes
a new run; it does not resume optimizer state. Evaluate it and the released
baseline on identical held-out inputs and generation settings. Training saves
no validation ranking, so the final checkpoint is not necessarily the best one.

For a local run from either example, select the most recently written nonempty
EMA checkpoint and generate a monomer:

```bash
python3 - "$RUN" "$PWD/workflows/rfd4-proteina-design/examples/design.yaml" <<'PY'
import json, sys
from pathlib import Path
run, condition = Path(sys.argv[1]), Path(sys.argv[2])
root = run / "train/results/finetune"
result = json.loads((root / "result.json").read_text())["result"]
ema = [root / p for p in result["checkpoints"] if p.endswith("-ema.ckpt")]
ema = [p for p in ema if p.is_file() and p.stat().st_size]
if not ema:
    raise SystemExit("Training returned no nonempty EMA checkpoint")
checkpoint = max(ema, key=lambda p: p.stat().st_mtime_ns)
(run / "design.json").write_text(json.dumps({
    "input": str(condition), "checkpoint": str(checkpoint),
    "numReplicates": 1, "batchSize": 1, "seed": 42,
}, indent=2) + "\n")
PY
task workflow:generate workflow=rfd4-proteina-design policy=local \
  output="$RUN/generated-design"
task workflow:run workflow=rfd4-proteina-design \
  generated="$RUN/generated-design" params="$RUN/design.json" \
  config="$EXAMPLE/runtime.config" output="$RUN/design"
```

Inspect `$RUN/design/results/design/result.json` and the CIF files it lists.
Preserve the training provenance, generated bindings, logs, resolved
configuration and selected EMA checkpoint alongside the designs.

### Historical validation

The [historical validation record](https://github.com/apheris/foundry-toolkit/pull/604)
contains the original GPU evidence. Execution checks passed: one training step,
finite losses, regular and EMA checkpoints, and valid 100-residue designs from
the workflow and direct EMA checkpoints. Strict numerical comparisons failed,
including variation between two direct module runs. Four component-loss columns
and 442 of 1,257 tensors per checkpoint comparison exceeded the preset tolerances;
the EMA designs differed by up to 0.109 angstroms without alignment. The recipe
sets `torch_deterministic: false`; the source of the variation remains unresolved.
These results do not establish scientific equivalence or validate the new release.

The unchanged criteria remain in `examples/expected-result.json`. With retained
one-step outputs, run the verifier inside the model image:

```bash
python workflows/rfd4-proteina-finetune/examples/verify_training.py \
  "$RUN" workflows/rfd4-proteina-finetune/examples/expected-result.json \
  /results/workflow/finetune /results/direct
```

It checks steps, losses and regular/EMA tensors and returns nonzero when the
original tolerances fail. The design example's `verify_results.py` compares
EMA-generated CIFs. Do not widen tolerances after seeing differences.

## Method

The image uses upstream's `tutorial/finetune_test_dataset` recipe and the
RFD4-Proteina architecture described by the selected module. Users inherit its
dataset transforms, sampling, cropping and data-loader settings. An epoch lasts `stepsPerEpoch` steps, rather
than one pass over the dataset. Training updates the full denoiser, keeps the
autoencoder frozen, saves checkpoints each epoch and disables compilation,
WandB and validation generation. See the
[upstream training guide](https://rfd4-proteina.org/latest/contributing/developer-guide.html).

## Limits

Dataset preparation, LoRA training, optimizer-state resume and validation
controls are outside this workflow. The example's preparation script only
prepares its fixed tutorial records. Scientific review of the inherited recipe
for other datasets and of the numerical differences remains pending. Successful
execution or decreasing training loss does not establish improved designs.

## Contact

Scientific owner: Leonardo Castorina.

Report integration issues in the foundry-toolkit repository.
