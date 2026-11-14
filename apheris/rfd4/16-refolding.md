---
type: Reference
title: Check designs by refolding them
description: How to check RFD4-Proteina designs in Foundry by refolding them with a folding model (OpenFold3, Protenix,
  Boltz, Mol-1, ESMFold2) and scoring them against RFD4-Proteina's pass criteria.
questions:
- How do I check or score my designs?
- Which folding model should I use to refold designs?
- What do the refolding pass criteria measure?
- How many designs should I make per target?
tags:
- rfd4-proteina
- foundry
status: draft
sources:
- resource: https://github.com/apheris/apheris-rfd4-proteina
  title: Foundry RFD4-Proteina module docs
---

# Check designs by refolding them

> **On the hackathon VM?** There is no Foundry Hub there. Use [Run on your hackathon VM](18-vm.md) instead of the `apheris-foundry` commands on this page.


A design is worth testing when an independent folding model, given only its sequence, folds it into the
designed complex. Foundry runs this in three steps:

1. **Design Proteins** with `refold=true` prepares the best designs for refolding (the top 20% by default,
   or `refoldTopN`).
2. **Predict Structure** refolds them with a folding model, once bound to the target (holo) and once alone
   (apo).
3. **Score Refolded Designs** scores each refold against RFD4-Proteina's pass criteria, taken from the
   upstream AlphaFold3 check: confidence in the binder, confidence in the interface, and agreement with the
   designed structure.

The folding models and their score labels are listed in [Models](14-models.md).
For binders, prefer one that uses a template. The cut-offs were calibrated on AlphaFold3 and can shift by
model, so compare pass rates within one model.

Upstream reports binder pass rates of 7.7% to 10.6%, so plan 100 to 200 designs per target. On an A100,
refolding takes about 25 s per design per model, plus 20 s for the apo run.

The full protocol and the exact pass criteria are in [Evaluate candidates](06-evaluate.md). Upstream's own
metrics, without refolding, are in [Advanced routes](07-advanced.md).
