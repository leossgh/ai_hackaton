---
type: Reference
title: Models available for RFD4-Proteina
description: Every model you can use with RFD4-Proteina in Foundry. The design models (weights release, antibody,
  HER2) and the folding models (OpenFold3, Protenix, Boltz, Mol-1, ESMFold2) that refold designs to check them.
questions:
- What models are available for RFD4-Proteina?
- Which folding models can I use with RFD4-Proteina?
- Which weights do I use to design antibodies?
- Which folding model should I use to check my designs?
tags:
- rfd4-proteina
- foundry
status: draft
sources:
- resource: https://github.com/apheris/apheris-rfd4-proteina
  title: Foundry RFD4-Proteina module docs
---

# Models available for RFD4-Proteina

RFD4-Proteina uses two kinds of model: a **design model** that generates proteins, and a **folding model**
that refolds each design to check it.

## Design models

Pick one with `--weight` in Design Proteins. Each is its own image build.

| Weight | What it is | Use it for |
| --- | --- | --- |
| `release-2026-10-19` | NVIDIA's general RFD4-Proteina model | Miniprotein binders, monomers, enzymes, motif scaffolds, ligand and DNA binders |
| `antibody-2026-10-30` | NVIDIA's antibody model | VHH and paired VH/VL antibody design against a chosen epitope |
| `her2-2026-11-07` | The antibody model, fine-tuned by Apheris on trastuzumab CDRH3 HER2 binders | Redesigning trastuzumab's CDRH3. `sequenceTsrK` 2 or 1 gives more varied loops. See [HER2 models](12-her2.md) |
| `her2-novel-2026-11-09` | The antibody model, trained by Apheris on pairs of HER2 binders and non-binders | Mostly new trastuzumab CDRH3 loops |
| Your own | A checkpoint from Fine-Tune Protein Design Model | Pass it as `weights` |

With `module-run`, the same models are named `release`, `antibody`, `her2-conservative`, `her2-balanced`,
`her2-exploratory` and `her2-novel` (`--model`), for a weights folder that holds several checkpoints.

## Folding models

Design Proteins prepares the best designs for refolding, Predict Structure refolds them with a folding model,
and Score Refolded Designs scores the result. Score with the label that matches the model you folded with.

| Folding model | Weight | Score label | Uses a template |
| --- | --- | --- | --- |
| OpenFold3 OpenBind | `of3ob` | `openfold3-of3ob` | Yes |
| OpenFold3 preview 2 | `of3p2` | `openfold3-of3p2` | Yes |
| Protenix v2 | `v2` | `protenix-v2` | Yes |
| Protenix v1 | `v1-default` | `protenix-v1` | Yes |
| Boltz-2 | `boltz2` | `boltz2` | Yes |
| Boltz-1 | `boltz1` | `boltz1` | No |
| Mol-1 | `base` | `mol1-base` | Yes |
| ESMFold2 | `release` | `esmfold2-release` | No |

For binders, prefer a model that uses a template: it folds the design against the target in its known
pose. Models without one fold the target unguided.

Settings for each model are in the [technical reference](09-parameters.md).
