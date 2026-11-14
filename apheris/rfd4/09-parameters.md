---
type: Reference
title: 'Technical reference: what to pass'
description: Place design conditions, workflow controls and folding parameters in
  their correct inputs.
tags:
- rfd4-proteina
- foundry
- parameters
status: draft
sources:
- resource: https://github.com/apheris/apheris-rfd4-proteina
  title: Foundry RFD4-Proteina module
- resource: https://github.com/RosettaCommons/RFD4-Proteina/tree/68058693cb88762a8aaf806571e13b291ce6318a
  title: Pinned upstream source
---

# Technical reference: what to pass

## Design instructions: the uploaded spec

Each top-level design ID maps to `input`, optional `contig`, `conditions` and
`input_as_annotated_cif`. Relative structure paths resolve from the spec's
directory and must stay inside the uploaded tree. Upload every referenced file.
With multiple specs, set workflow `spec` to the chosen relative filename.
The optional top-level `global_args` supplies defaults shared by the design IDs.

| Field / condition | Meaning |
| --- | --- |
| `input` | One CIF/BCIF path or a list of structures with distinct chain IDs |
| `input_as_annotated_cif: true` | Preserve existing conditioning. Default is `false` for freshly prepared inputs |
| `contig` | Retained residue ranges, expandable lengths and `/0` chain breaks |
| `C_SEQ` | Preserve selected residue identities |
| `C_CRD` | Fix selected atoms in absolute coordinates. Group 0 supplies the pose-scoring frame |
| `C_CRDGRP: 1` | Preserve internal geometry while allowing rigid-body placement. Use for framework backbones |
| `C_HOT` | Request contacts to selected target atoms |
| `C_CATH: "2.60.40"` | Supply immunoglobulin fold context on antibody chains |
| `C_RAS` | Exposure bin: `BURIED`, `INTERMEDIATE`, `EXPOSED` or `UNSPECIFIED` |
| `C_HB` | Hydrogen-bond role: `DONOR`, `ACCEPTOR` or `BOTH` |
| `C_PISTACK`, `C_PICATION` | Stacking: `true`. Aromatic/cation role: `AROMATIC`, `CATION` or `BOTH` |
| `C_CENTROID` | Literal `"x,y,z"` chain centroid, covering every atom of every chain |
| `C_IDX: false` | Unindex selected atoms, with a shared `group` label where their relative offsets must remain linked |

CDR lengths and hotspot selections are input conditions, not workflow flags.
An ordinary CIF needs an explicit design problem. Side-chain coordinate
conditioning also reveals residue identity. Backbone-only conditions permit
sequence redesign where sequence is not fixed.
For complete selection syntax and condition values, see the optional online
[spec reference](https://rfd4-proteina.org/latest/reference/yaml-json.html).

## Design Proteins: workflow parameters

| Parameter | Meaning and default |
| --- | --- |
| `input`, `output` | Upload directory and persistent result root. Keep output/work directories outside input |
| `spec` | Relative JSON/YAML spec filename. Inferred for a sole top-level spec |
| `numReplicates` | Designs per input, 1–200. Default `1` |
| `batchSize` | Generation batch size. Default `1` |
| `seed` | Nonnegative integer. Random when omitted |
| `recycleStrategy` | Default `thinking_medium` (`medium/front_loaded`). Use `high/front_loaded` for antibody examples, `medium/midpeak` for enzyme/ligand examples |
| `resampleHotspots` | Default `false`. `true` replaces annotated hotspots with 2–3 sampled nearby atoms |
| `partialTrajectoryFraction` | Omit for fresh generation. Fraction in `(0,1]` covering at least one of 60 steps, on an annotated generated parent |
| `inverseFolding` | Version-dependent fixed-backbone sequence redesign. Requires complete coordinates and a matching module contract |
| `compile` | Default `false`. Compilation adds startup cost per padded length |
| `weights` | Optional compatible flow-checkpoint path. Omission uses the selected build's weights and paired autoencoder |
| `sequenceTsrK` | Decimal number above 0 that sets how random each design's sequence is. Default 4. Higher values repeat the sequences the model rates most likely. 1 removes that sharpening and gives the most varied sequences. Below 1 is allowed but untested. Structure sampling is unchanged. See [HER2 models](12-her2.md) |
| `refold` | Default `false`. `true` prepares prediction inputs after generation, without running prediction |
| `refoldTopN` | Explicit count to prepare. Requires `refold: true`. Otherwise preparation selects the top 20%, rounded up |
| `logLevel` | Workflow logging level. Default `info` |

An antibody pilot, copied from the supplied settings file:

```json
{"numReplicates": 1, "batchSize": 1, "seed": 42,
 "recycleStrategy": "high/front_loaded", "resampleHotspots": false,
 "compile": false, "refold": true, "refoldTopN": 1}
```

Do not combine partial diffusion with hotspot resampling. Use the selected
workflow's camelCase fields here. Raw module snake_case controls and upstream
Hydra overrides are separate interfaces. `inverseFolding` is version-dependent.
See [advanced routes](07-advanced.md).

## Predict Structure and Score Refolded Designs

| Where to pass it | Fields |
| --- | --- |
| Predict workflow | `input`, `output`, `model`, optional custom checkpoint path `weights`. Select the weight build through the client |
| Predict `modelParams` | `template_paths`: uploaded-relative CIF filenames. `write_detailed_scores`: boolean. `num_diffusion_samples`: positive integer. `seeds`: nonempty list of nonnegative integers. `query_failures`: `fail` or `skip` |
| Score workflow | `input`, `output`, required `cofoldingModel` label. `criterion`: `auto`, `ppi` or `antibody`. Optional uploaded-relative YAML `passCriteria` |

`refold/holo/queries.json` already contains the chain sequences and explicit
`msa_path: null` opt-outs. Upload it with `template.cif` when one was written.
Templates apply to every query in the batch. Use separate prediction and score
runs for each model/weight combination. RFD4 generation checkpoints and folding
model checkpoints are different assets.
