---
type: Playbook
title: 2. Design a binder
description: Choose a miniprotein, VHH or paired VH/VL example for your target.
tags:
- rfd4-proteina
- foundry
- miniprotein
status: draft
sources:
- id: sources
  resource: sources.md
  title: Source and validation record
---

# 2. Design a binder

Supply a target and binding patch. Choose the binder format:

| Format | Upload | Workflow settings | Weights |
| --- | --- | --- | --- |
| Miniprotein | [PD-L1 example](Data/02-miniprotein/) | [Miniprotein](Settings/02-miniprotein.json) | General release |
| VHH / nanobody | [PMVK + caplacizumab framework](Data/03-vhh/) | [VHH](Settings/03-vhh.json) | Antibody |
| Paired VH/VL (Fv) | [Ubiquitin + adalimumab frameworks](Data/03-fv/) | [Fv](Settings/03-fv.json) | Antibody |

The miniprotein example creates a 50–80 residue binder. Antibody examples keep
framework sequence and internal geometry, generating three CDRs for VHH or six
for Fv. Select `antibody-2026-10-30` weights for the antibody exercises.
A complete Fab also includes constant domains. This exercise designs its Fv region.

For a hackathon, complete one supplied antibody example through design,
prediction and scoring before increasing the count or changing the antigen.
For a new antigen, provide its prepared CIF, the intended binding patch,
framework choice and CDR length ranges. Inspect the structure's chain and residue
map before editing conditions. Keep the original sample as a reference.

Run the selected example using [the shared steps](00-start.md). Inspect the
generated complex: does the binder reach the intended patch without clashes?
The CSV's `designed_sequences` identifies the binder chains, including retained
framework sequence. Keep both domains for Fv.

**For your own target:** replace the structure and update chain IDs, residue
ranges and hotspot atoms in the spec. Keep antigen sequence fixed (`C_SEQ`)
and its backbone in absolute coordinates (`C_CRD`) for pose scoring.
Selections use original mmCIF `label_seq_id`.

The miniprotein spec keeps target chain A and inserts a new protein chain:

```yaml
pdl1_miniprotein:
  input: target.cif.zst
  contig: "50-80, /0, A17-131"
  conditions:
    C_CRD: {true: [{select: "sel('A/*/*/[N,CA,C,O]')"}]}
    C_SEQ: {true: [{select: "sel('A')"}]}
    C_HOT:
      true:
        - select: "sel('A/*/56/[CG,OH]')"
        - select: "sel('A/*/115/[CG,SD]')"
        - select: "sel('A/*/123/[CD2,OH]')"
```

`50-80` is the generated length range. `/0` starts the target chain.
The conditions preserve target backbone and sequence and request contacts
to the listed atoms. Audit every selection when replacing the target.

For trastuzumab and HER2, start from [the fine-tuned HER2 models](12-her2.md).

Next: [evaluate](06-evaluate.md), or read the [antibody-specific notes](03-antibodies.md).
