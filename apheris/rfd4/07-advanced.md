---
type: Playbook
title: Advanced routes
description: Identify which capabilities need another task or upstream interface.
tags:
- rfd4-proteina
- foundry
- advanced
status: draft
sources:
- id: sources
  resource: sources.md
  title: Source and validation record
---

# Other routes

The supplied Hub workflows cover design, prediction and refold scoring.
The module also exposes `finetune` and `metrics` tasks. Run these through a
workflow that exposes them, or inside the supplied module container. Their
snake_case configuration keys are not Design Proteins workflow parameters.

## Fine-tune the generator

Provide a Parquet dataset with `example_id`, `path` and the metadata required by
the upstream PLINDER training recipe. Every referenced CIF must exist under the
`structures` root. Use compatible base weights and the paired autoencoder.

Inside the configured module container, with the dataset mounted at `/data`:

```bash
module-run finetune --input /data/train.parquet --output /output/train \
  --config '{"structures":"/data/cifs","epochs":1,"steps_per_epoch":50,"batch_size":1,"learning_rate":0.00001,"seed":42,"task_mix":"antibody"}'
```

Choose `task_mix: "plinder"` for the general training mix. Antibody training
requires a protein antigen and `_atom_site.ig_region` labels on antibody atoms
(`framework`, `cdr1`–`cdr4`). The autoencoder stays frozen. Training saves regular
and EMA checkpoints under `training/checkpoints/` and lists them in `result.json`.
Use a compatible `*-ema.ckpt` for inference and retain its paired autoencoder.
Assess it on independent data before scaling up.

## Recalculate metrics or cluster designs

Use a directory containing only the intended designs, excluding references
and refold outputs:

```bash
module-run metrics --input /data/designs --output /output/metrics \
  --config '{"metrics_tags":["design","hotspot_conditioning"],"cluster":false}'
```

Optional `task_csv` assigns structures to task groups. `cluster: true` requires
Foldseek through `FOLDSEEK_EXEC`. Read per-design, per-task and aggregate CSVs
from `result.json`, and compare report rows with the input count. Oracle tags
such as `antibody` and `*_refolding` are rejected by this image. Use Predict
Structure and Score Refolded Designs for refolding.

## Fixed-backbone redesign and upstream options

`inverseFolding` is exposed by the inspected workflow and pinned contract, but
the local module's `DesignConfig` lacks it. Confirm the deployed pair supports it.
It needs coordinates for every designed residue and cannot be combined with
expandable segments, partial diffusion or hotspot resampling.

Reward-guided search and metric guidance use upstream configuration beyond
the supplied workflow controls. Folding an existing sequence uses Predict
Structure directly. Context-conditioned design is covered in [other tasks](05-context.md).
