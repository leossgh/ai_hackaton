---
type: Playbook
title: Evaluate candidates
description: Refold candidates, score pose recovery and inspect the evidence.
tags:
- rfd4-proteina
- foundry
- evaluate
status: draft
sources:
- id: sources
  resource: sources.md
  title: Source and validation record
---

# Evaluate candidates

> **On the hackathon VM?** There is no Foundry Hub there. Use [Run on your hackathon VM](18-vm.md) instead of the `apheris-foundry` commands on this page.


Generation proposes candidates. Refolding checks whether another predictor
recovers their folds and poses. Experiments establish binding and specificity.

## 1. Prepare

The pilot settings enable `refold` and prepare every candidate. Keep
`design/`, `refold/holo/` and `refold/selection.csv`. A failed preparation can
leave valid designs. Read `refold/error.json` and split incompatible batches.

## 2. Predict

Upload `refold/holo/` to **Predict Structure**. Select a model and weight offered
by your deployment. The cofolding modules support these choices:

| Model | Weight build | Matching score label | Uses a template |
| --- | --- | --- | --- |
| OpenFold3 | `of3ob` / `of3p2` | `openfold3-of3ob` / `openfold3-of3p2` | Yes |
| Protenix | `v2` / `v1-default` | `protenix-v2` / `protenix-v1` | Yes |
| Boltz-2 | `boltz2` | `boltz2` | Yes |
| Mol-1 | `base` | `mol1-base` | Yes |
| Boltz-1 | `boltz1` | `boltz1` | No |
| ESMFold2 | `release` | `esmfold2-release` | No |

Models without a template fold the target unguided. Run them with the untemplated
settings below, even for binders.

Mol-1 uses the shared prediction workflow. For Boltz, select
`--model boltz --weight boltz2` explicitly. The optional `weights` field is a
checkpoint-path override. Select build names such as `boltz2` through the client.
Put the [holo model settings](Settings/06-holo-model-params.json) inside `modelParams`:

```json
{"template_paths": ["template.cif"], "write_detailed_scores": true,
 "num_diffusion_samples": 1, "seeds": [42], "query_failures": "skip"}
```

Clients may serialize this object as JSON for `modelParams`. Preserve its keys
and value types. In the Hub CLI, use `--model-params @file.json`, not
`--param modelParams=...`. Keep model and weight selection outside that object.

Templates contain conditioned antigen/framework residues, not generated CDRs.
Monomers have no template: use [untemplated settings](Settings/06-untemplated-model-params.json).
No MSA upload is needed. Optional apo prediction uses those same untemplated
settings and the same model/weights. It does not change automated pass/fail.
Use the template-capable weights above for binder evaluation. Do not rely on
an unspecified model or weight default.

## 3. Score

Upload complete `design/` and holo `predictions/` outputs together to **Score
Refolded Designs**, retaining manifests and `.cbor.gz` detailed scores.
Use this folder layout:

```text
input/
├── design/             # complete design task output
├── predictions/        # complete holo prediction output
└── apo-predictions/    # optional complete apo prediction output
```

Set `cofoldingModel` to the matching label above and `criterion: "auto"`.
This records which model ran. Model selection happens in Predict Structure.
Find the CSV through `score/result.json`. To compare predictors, repeat prediction
and scoring separately on the same designs. Keep each model's scores separate.

| Design | Automated pass |
| --- | --- |
| Monomer | Backbone RMSD ≤ 1.5 Å |
| Protein binder | Binder pTM ≥ 0.8. Interface PAE ≤ 1.5 Å. Target-backbone-aligned binder RMSD ≤ 2.5 Å |
| Antibody | Interface PAE ≤ 2.0 Å. Target-aligned binder RMSD ≤ 2.0 Å |

Read `pass`, `status` and `pass_note`. Empty pass means missing evidence.
Preliminary filter failures cannot pass. Pose scoring needs group-0 target
atoms, and Fv interface metrics include VH–VL contacts. Compare results within
one predictor/protocol. Thresholds were calibrated with upstream's AF3 oracle.
If `refold/error.json` reports a template mismatch, split the designs into
compatible target/framework groups. Keep detailed scores enabled for binder
metrics. An optional `passCriteria` file changes thresholds. Leave it unset
for the vendored criteria.
