---
type: Playbook
title: 1. Create a protein
description: Generate a 100-residue monomer without a target or fixed motif.
tags:
- rfd4-proteina
- foundry
- from-scratch
status: draft
sources:
- id: sources
  resource: sources.md
  title: Source and validation record
---

# 1. Create a protein

**Goal:** generate a new 100-residue sequence and fold, without a target.

Upload [Data/01-monomer/](Data/01-monomer/), select the **general release**
weights and use [Settings/01-monomer.json](Settings/01-monomer.json).
The annotated CIF encodes the length. Its spec preserves those instructions:

```yaml
monomer:
  input: monomer-short.cif.zst
  input_as_annotated_cif: true
```

Expect four generated single-chain structures. Check length, continuity and
clashes, then [refold them](06-evaluate.md) without a target template.
To request 150 residues, decompress the example CIF and set both
`_atom_site.annotation_expsegmin_1_residue` and
`_atom_site.annotation_expsegmax_1_residue` to `150`. Keep its placeholder
`label_comp_id` and `auth_comp_id` consistent as `150-150`, and update the
spec's `input` to the edited `.cif`. Preserve the other annotations.
