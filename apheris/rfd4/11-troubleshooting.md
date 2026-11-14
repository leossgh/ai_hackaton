---
type: Reference
title: Troubleshooting
description: Recover missing inputs, failed preparation and incomplete scores.
tags:
- rfd4-proteina
- foundry
- troubleshooting
status: draft
sources:
- resource: sources.md
  title: Sources and validation
---

# Troubleshooting

| Symptom | What to check |
| --- | --- |
| Missing input or settings | Use the embedded downloads in the Files tab. Extract the input ZIP and retain the displayed folder names. Settings are separate from the upload. |
| Workflow or antibody weight absent | Run `workflows list` and `workflows models` for the selected workflow. Ask your platform team for the required access or deployment. |
| Field rejected | Read `workflows docs` for that workflow. Design settings use camelCase, prediction settings belong inside `modelParams`, and module tasks use snake_case. |
| GPU out of memory | Start with `batchSize: 1` and one antibody candidate. If it still fails, use a smaller design problem or a GPU with sufficient memory. |
| Designs exist but refold preparation failed | Keep `design/` and inspect `refold/error.json`. A shared template requires compatible target/framework geometry and lengths. Prepare compatible groups separately. |
| Missing binder metrics | Retain the complete prediction output, including `.cbor.gz` scores. Set `write_detailed_scores: true` and check prediction failures. |
| Missing target-aligned RMSD | Fix at least three target atoms with absolute `C_CRD` conditioning. Framework-relative coordinate groups do not supply the target frame. |
| Low Fv interface PAE but poor antigen contact | The metric includes VH–VL contacts. Inspect antigen–CDR geometry explicitly. |
| Blank `pass` or failed rows | Read `status` and `pass_note`. Missing predictions or an unsupported criterion are not passing designs. |

Use `apheris-foundry jobs error --id "<job-id>"` for a job's error report.
Record the job ID, effective image, weight build and input settings when reporting
a failure. See [evaluation](06-evaluate.md) for the required output layout.
