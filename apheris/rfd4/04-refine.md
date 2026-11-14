---
type: Playbook
title: 3. Refine a binder
description: Explore related sequences and structures using partial diffusion.
tags:
- rfd4-proteina
- foundry
- refine
status: draft
sources:
- id: sources
  resource: sources.md
  title: Source and validation record
---

# 3. Refine a binder

**Goal:** explore nearby versions of a promising design. Partial diffusion
changes both sequence and structure. Evaluate children to establish improvement.

1. Upload one RFD4-Proteina `*_generated.cif` from an earlier run. Preserve its
   annotations and use the generated complex, rather than a predictor's refold.
2. Keep the parent's checkpoint family and recycle schedule. Use
   [miniprotein settings](Settings/04-refine.json) or
   [antibody settings](Settings/04-refine-antibody.json): eight children,
   `partialTrajectoryFraction: 0.4`, hotspot resampling off.
3. [Refold and compare](06-evaluate.md) children with the parent using the same
   prediction settings. Record each child's parent and fraction.

The fraction re-runs 40% of the 60 sampling steps. Smaller fractions generally
stay closer to the parent. Larger ones explore further. It does not specify
a structural displacement. An experimental binder first needs an explicit
annotated redesign problem.

Inspect parents before multiplying them: [Adaptyv refinement](08-adaptyv.md)
also propagated an unwanted terminal tail.
