---
id: getting-started-gs-run-a-workflow
type: article
title: How to run any workflow (get and run)
gloss: Every workflow is fetched and prepared by `foundry-toolkit`, then executed by Nextflow (standalone) or submitted to a Hub. The specific inputs/params are in each workflow's own page and its `apheris-workflow-<id>` skill.
steps:
- name: Pick a workflow
  detail: the result you want (predict, affinity-predict, ...)
  io: true
- name: foundry-toolkit workflow get
  detail: fetch main.nf + tasks.config for your policy/executor
- name: nextflow run
  detail: run main.nf with --input and --output
- name: Results
  detail: the workflow's output folder (follow result.json)
  io: true
examples:
- How do I run a workflow standalone without a Hub?
- how do i see which workflows are available
- What does `workflow get --policy` actually do?
- Before I run nextflow after workflow get, is there anything I should check?
- What's the command to run a workflow on a Hub and get the results?
- Where do I find the specific inputs and params for a workflow?
- Can I have an AI agent run a workflow for me? Which skills do I need?
- I submitted a request to a Hub, can the agent just run it locally instead?
---
# How to run any workflow (get and run)

Every workflow is fetched and prepared by `foundry-toolkit`, then executed by
Nextflow (standalone) or submitted to a Hub. The specific inputs/params are in
each workflow's own page and its `apheris-workflow-<id>` skill.

**Standalone (T1): foundry-toolkit + Nextflow**
```
foundry-toolkit workflow list --latest
foundry-toolkit workflow get --name <id> --version <v> \
  --policy <policy.json> --executor local --to <fresh-dir>
nextflow -C runtime.config,<fresh-dir>/tasks.config run <fresh-dir>/main.nf \
  <workflow input and output arguments>
```
`workflow get --policy` compiles the task wrappers from the pinned contracts and
writes `tasks.config` + `resources.json`; review the effective resources before
running. Keep the returned digest pin.

**On a Hub (T2):**
```
apheris-foundry workflows run --workflow <id> --input <file> --model-params @params.json
apheris-foundry jobs logs --id <job>; apheris-foundry jobs download --id <job>
```

**Let an agent run it:** install the `foundry-toolkit` skill (standalone) or
`apheris-foundry-hub` skill (Hub) plus the workflow's own `apheris-workflow-<id>`
skill (see [[gs-install-login]]); the skill carries the preparation and
interpretation steps for that workflow. Keep the chosen execution target — a Hub
request stays on Hub.
