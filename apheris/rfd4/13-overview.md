---
type: Reference
title: About RFD4-Proteina
description: What RFD4-Proteina is, what it can design (antibodies, binders, enzymes), which design models and folding
  models are available, and where to start in Apheris Foundry.
questions:
- What is RFD4-Proteina?
- What can I design with RFD4-Proteina?
- Where do I start with RFD4-Proteina in Foundry?
tags:
- rfd4-proteina
- foundry
status: draft
sources:
- resource: https://github.com/apheris/apheris-rfd4-proteina
  title: Foundry RFD4-Proteina module docs
---

# About RFD4-Proteina

RFD4-Proteina is a generative protein design model from NVIDIA and the Baker Lab. It designs a protein's
sequence and its full-atom 3D structure together, conditioned on a target you give it. Apheris Foundry runs
it as three workflows:

| Workflow | ID | What it does |
| --- | --- | --- |
| Design Proteins | `rfd4-proteina-design` | Generates designs, and optionally prepares the best ones for refolding |
| Score Refolded Designs | `rfd4-proteina-refold-score` | Scores folding-model refolds of designs against RFD4-Proteina's pass criteria |
| Fine-Tune Protein Design Model | `rfd4-proteina-finetune` | Trains the design model further on your own structures |

## What it designs

- **Antibodies:** VHHs (nanobodies) and paired VH/VL (Fv). It designs new CDRs against an epitope you choose,
  or redesigns selected CDRs of an existing antibody. See [How to design an antibody](15-antibody-design.md).
- **Miniprotein binders** to protein targets.
- **Binders to small molecules, DNA and RNA.**
- **Enzymes** built around a catalytic motif, and **scaffolds** for a given functional motif.
- **Monomers** from scratch.

It can also refine an earlier design (partial diffusion) or design new sequences for a kept backbone
(inverse folding).
