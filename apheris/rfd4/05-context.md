---
type: Playbook
title: Other design tasks
description: Scaffold motifs and design proteins around ligands or DNA.
tags:
- rfd4-proteina
- foundry
- context
status: draft
sources:
- id: sources
  resource: sources.md
  title: Source and validation record
---

# Other design tasks

The same model can preserve functional geometry and design protein around it.
Use **general release** weights and the linked settings:

| Goal | Upload | Settings |
| --- | --- | --- |
| Scaffold an enzyme site | [Annotated M-CSA motif](Data/05-enzyme/) | [Enzyme](Settings/05-enzyme.json) |
| Bind a small molecule | [SAM context](Data/05-ligand/) | [Ligand](Settings/05-ligand.json) |
| Bind DNA | [DNA structure context](Data/05-dna/) | [DNA](Settings/05-dna.json) |

These examples request four designs and preserve the CIF's annotations.
The model generates standard amino acids. Molecular context is supplied.
Check retained geometry, chemistry and clashes. Enzyme activity needs further testing.

The current refold adapter rejects ligand, DNA and RNA chains and has no motif
pass criterion. These exercises stop at design metrics (`refold: false`).
