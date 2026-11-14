---
type: Reference
title: How to design an antibody with RFD4-Proteina
description: Design antibodies (VHH nanobodies and paired VH/VL Fv) against a target and epitope with RFD4-Proteina's
  antibody model in Foundry. What to prepare, the design spec, how to run it and how to check the designs.
questions:
- How do I design an antibody?
- How do I design a VHH or nanobody against my target?
- How do I choose the epitope the antibody binds?
- Can I redesign the CDRs of an existing antibody?
tags:
- rfd4-proteina
- foundry
status: draft
sources:
- resource: https://github.com/apheris/apheris-rfd4-proteina
  title: Foundry RFD4-Proteina module docs
---

# How to design an antibody

Use the antibody model, weight `antibody-2026-10-30`, in Design Proteins. It designs new CDR loops against an
epitope you choose and keeps the antibody framework fixed. It handles VHHs (nanobodies) and paired VH/VL (Fv).
For a Fab or IgG, design the Fv and add the constant domains afterwards.

## What to prepare

1. **The antigen** as an mmCIF file. PDB files are rejected.
2. **A framework**: a VHH or VH/VL structure whose framework you want to keep, such as a clinical antibody.
3. **The epitope**: a few antigen atoms the antibody should contact (hotspots).
4. **A length range for each CDR.**

## The design spec

A short JSON or YAML file says what to keep and what to design. From the Fv example
([full file](Data/03-fv/design.json)), which designs six CDRs on adalimumab's
framework against ubiquitin (chain F):

```json
{
  "contig": "F1-76, /0, H1-22, 13-15, H24-37, 9-10, H39-75, 11-22, H77-87, /0, L1-23, 11-14, L25-38, 8-8, L40-71, 8-12, L73-82",
  "conditions": {
    "C_CRD":    {"true": [{"select": "sel('F/*/*/[N,CA,C,O]')"}]},
    "C_CRDGRP": {"1": [{"select": "sel('H/*/[1-22, 24-37, 39-75, 77-87]/[N,CA,C,O]')"},
                       {"select": "sel('L/*/[1-23, 25-38, 40-71, 73-82]/[N,CA,C,O]')"}]},
    "C_SEQ":    {"true": [{"select": "sel('F')"}, {"select": "sel('H/*/[1-22, 24-37, 39-75, 77-87]')"},
                          {"select": "sel('L/*/[1-23, 25-38, 40-71, 73-82]')"}]},
    "C_HOT":    {"true": [{"select": "sel('F/*/8/CD1')"}, {"select": "sel('F/*/70/CG1')"}]},
    "C_CATH":   {"2.60.40": [{"select": "sel('H')"}, {"select": "sel('L')"}]}
  }
}
```

- **`contig`** lays out the chains. Ranges with a chain letter are kept from the input. Bare ranges such as
  `13-15` are designed CDRs of that length. `/0` starts a new chain.
- **`C_SEQ`** keeps the sequence of the antigen and the framework.
- **`C_CRD`** keeps the antigen backbone where it is.
- **`C_CRDGRP`** keeps the framework's internal shape. Put VH and VL in one group so they stay paired.
- **`C_HOT`** marks the epitope atoms.
- **`C_CATH`** marks the antibody chains as an immunoglobulin fold (`2.60.40`).

Residue numbers are the file's own (`label_seq_id`). A VHH spec has one antibody chain and three CDRs.

To redesign selected CDRs of an existing antibody instead, keep every other CDR in `C_SEQ` and `C_CRDGRP`
and leave only the ones to redesign as bare ranges. For trastuzumab's CDRH3 against HER2, the
[HER2 models](12-her2.md) give better starting points than the general antibody model.

## Run it

```bash
apheris-foundry workflows run --workflow rfd4-proteina-design \
  --input Data/03-fv --weight antibody-2026-10-30 \
  --param numReplicates=100 --param batchSize=1 --param seed=1 \
  --param recycleStrategy=high/front_loaded \
  --param refold=true --param refoldTopN=20 --wait
```

Use `recycleStrategy=high/front_loaded` for antibodies. Plan 100 to 200 designs per target: upstream reports
binder pass rates around 8 to 11%. On an A100 a VHH takes about 24 s per design and a VH/VL about 36 s.

## Check the designs

Refold the prepared designs with a folding model and score them: see [Refolding](16-refolding.md).
Look at the antigen contacts in each accepted complex. For an Fv, scoring picks one chain of interest and
counts the other antibody domain as a partner, so a good interface score can reflect VH-VL confidence rather
than antigen binding.

To explore close variants of a promising design, run Design Proteins on its `*_generated.cif` with
`partialTrajectoryFraction` set (see [Refine a binder](04-refine.md)).
