---
type: Playbook
title: 'Adaptyv: a miniprotein example'
description: Illustrate miniprotein generation, refinement and screening with aggregate
  results.
tags:
- rfd4-proteina
- foundry
- adaptyv
status: draft
sources:
- id: sources
  resource: sources.md
  title: Source and validation record
---

# Adaptyv: a miniprotein example

The November 2026 Adaptyv work provides a practical miniprotein example:
generate candidates, sample sequence alternatives with ProteinMPNN, refold
selected sequences with Protenix v2, then refine promising parents.

| Miniprotein outputs | Count |
| --- | --- |
| Generated backbones | 6,225 |
| Sequences screened | 2,040 |
| Passed campaign filters | 162 |
| Passes from refined children | 144 |

These were custom strict and relaxed filters, not the module's automated
pass rate. Related children are not independent discoveries. Keep parent
identity and evaluation settings with each candidate, and inspect the whole
structure before refinement.

The reviewed candidates had one prediction seed/sample and no wild-type or
empty-HLA controls. Specificity and experimental binding remain untested.
[Aggregate miniprotein evidence](Evidence/campaign-summary.json).
