---
type: Reference
title: Sources and validation
description: Record provenance, validation limits and package integration.
tags:
- rfd4-proteina
- foundry
- sources
status: draft
sources:
- resource: https://github.com/apheris/apheris-rfd4-proteina
  title: Foundry RFD4-Proteina module
- resource: https://github.com/RosettaCommons/RFD4-Proteina/tree/68058693cb88762a8aaf806571e13b291ce6318a
  title: Pinned upstream source
---

# Sources and validation

## Sources

- [Foundry workflows](https://www.apheris.com/docs/foundry/tasks-and-workflows.html): terminology and execution paths.
- [Hub CLI source](https://github.com/apheris/apheris-foundry-cli/tree/c2dc1779fee383466e49bbd3945414b69e0c989a): inspected login, skills and submission contract. Requires Apheris GitHub access.
- [Proteina module](https://github.com/apheris/apheris-rfd4-proteina): design, training, metrics and refold tasks. Requires Apheris GitHub access.
- [Cofolding source](https://github.com/apheris/apheris-cofolding/tree/958ea8c723c3aa2f6b1f955c29adf35f03e6750c): model capability maps and image builds. Requires Apheris GitHub access. [Bundled model options](Evidence/folding-models.json).
- [Pinned upstream](https://github.com/RosettaCommons/RFD4-Proteina/tree/68058693cb88762a8aaf806571e13b291ce6318a): examples, conditioning and recipes. [retained licence](LICENSE-RFD4.txt).
- [Chinery et al.](https://www.biorxiv.org/content/10.1101/2024.03.26.586756v2): trastuzumab CDRH3 binding screen behind the HER2 models.
- [Aggregate miniprotein results](Evidence/campaign-summary.json): the Adaptyv example's counts and limitations.
- [OKF v0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md): typed Markdown concepts and linked index.

## Package and checks

The HTML includes example ZIP downloads and inline settings. The full package
also contains `Data/`, `Settings/`, [Markdown](foundry.md) and [OKF](index.md).
`manifest.json` records input, settings and evidence hashes.

Checks cover package links, input hashes, parameter contracts, syntax,
interactive navigation, copy fallback and reproducible ZIP extraction.
The commands and packaged inputs were not rerun on a live Foundry deployment.
DOM tests do not verify rendered browser layout or a system clipboard.
Use the running workflow's documentation for its active contract and models.

## Changelog

10 November 2026: add the fine-tuned HER2 models exercise, its trastuzumab
example input and settings, the `her2-2026-11-07` weight and `sequenceTsrK`.

9 November 2026: replace raw-file navigation with inline previews and embedded
input downloads. Add navigation regression tests, troubleshooting and module
training/metrics instructions. Retain the Foundry theme and miniprotein-only
campaign example.
