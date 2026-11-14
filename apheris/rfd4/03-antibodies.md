---
type: Playbook
title: Antibody notes
description: "Preserve the framework and evaluate antibody\u2013antigen contacts explicitly."
tags:
- rfd4-proteina
- foundry
- antibodies
status: draft
sources:
- id: sources
  resource: sources.md
  title: Source and validation record
---

# Antibody notes

- **Keep the scaffold:** retain framework sequence, disulfide cysteines and
  internal backbone geometry (`C_CRDGRP: 1`). Use a shared group for paired
  VH/VL frameworks and `C_CATH: "2.60.40"` on antibody chains. Leave intended
  CDRs free. Derive boundaries from the actual structure.
- **Use the supplied schedule:** antibody settings use `high/front_loaded`.
  Keep hotspot resampling off when a specific contact is essential.
- **Inspect antigen contacts:** Fv scoring chooses one chain of interest.
  The other antibody domain counts as a partner, so a low interface PAE can
  reflect VH–VL confidence. The apo query also contains only the chosen chain.
- **Split incompatible refolding batches:** if variable light-chain CDR lengths
  break the shared-template check, prepare one candidate at a time with
  the CPU `refold-prepare` task and `top_n: 1`. The pilot already generates
  and prepares one candidate. Keep existing designs when preparing larger runs.

See [the input reference](https://rfd4-proteina.org/latest/reference/yaml-json.html)
for custom specs, or inspect the supplied [Fv specification](Data/03-fv/design.json).
When changing antigen, verify that every framework, target and hotspot selection
still names the intended atoms. Inspect antigen–CDR contacts and clashes in the
generated and refolded complexes before accepting a candidate.
