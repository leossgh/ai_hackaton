---
type: Playbook
title: Start here
description: Choose a task, upload its example and use the shared run settings.
tags:
- rfd4-proteina
- foundry
- start
status: draft
sources:
- id: sources
  resource: sources.md
  title: Source and validation record
---

# Before you run

> **On the hackathon VM?** There is no Foundry Hub there. Use [Run on your hackathon VM](18-vm.md) instead of the `apheris-foundry` commands on this page.


RFD4-Proteina generates protein sequences and all-atom structures together.
Start with [a new protein](01-from-scratch.md), [a binder](02-miniprotein.md)
or [refinement](04-refine.md).

## Set up once

Get your Foundry URL and access to **Design Proteins**, **Predict Structure**
and **Score Refolded Designs** from your platform team. Check the available
weight builds. [Foundry setup](https://www.apheris.com/docs/foundry/getting-started.html)
is an optional online reference.

The workflow IDs are `rfd4-proteina-design`, `predict` and
`rfd4-proteina-refold-score`, respectively.

For an agent or command-line session, start with
[connection and submission instructions](10-agent.md).

1. Download the chosen input ZIP from this guide and extract it. Upload its
   `Data/<example>/` folder, keeping the spec and structures together.
2. Apply the values in its linked `Settings/` file to the workflow parameters.
   Keep settings outside the upload. Your client supplies input, output and weight selection.
3. Run Design Proteins. Antibody pilots request one candidate. Other fresh-design
   examples request four. Both use batch size 1 and seed 42. Counts are per input.
4. Open `design/result.json` for structures, metrics and logs, then
   [evaluate the candidates](06-evaluate.md).

**Put each setting in the right place:** design length, fixed atoms and hotspots
belong in `design.yaml` / `design.json` or the annotated CIF. Generation settings
such as `numReplicates` belong to Design Proteins. Folding settings such as
`seeds` belong inside Predict Structure's `modelParams`.
The [technical reference](09-parameters.md) lists accepted fields and defaults.
Design results live in `<output>/design/`. Manifest paths are relative to that
task directory. Refolding preparation writes `<output>/refold/`.

Design requests one NVIDIA GPU, eight CPUs and 64 GiB host RAM. GPU memory
depends on the input. These examples use CIF, not PDB.

Also available: [motifs, enzymes, ligands and DNA](05-context.md),
[training and metrics](07-advanced.md), and [troubleshooting](11-troubleshooting.md).

## Use the UI

1. Open **Design Proteins** and upload the chosen example folder.
2. Select the required weight build and enter the linked settings in the
   displayed workflow controls. Keep the input spec with its structures.
3. Submit the job, check its final state and download the complete outputs.
4. Follow [Evaluate](06-evaluate.md) through **Predict Structure** and
   **Score Refolded Designs**, using the prepared inputs and matching model label.

If a required control or model is unavailable, check your deployment's workflow
documentation before submitting. For agents, complete the CLI connection checks
before installing workflow skills.
