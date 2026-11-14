---
type: Playbook
title: Connect an agent or run from the CLI
description: Install live workflow skills, verify the catalogue and complete one antibody
  pilot.
tags:
- rfd4-proteina
- foundry
- agent
status: draft
sources:
- id: sources
  resource: sources.md
  title: Source and validation record
---

# Connect an agent or run from the CLI

> **On the hackathon VM?** There is no Foundry Hub there. Use [Run on your hackathon VM](18-vm.md) instead of the `apheris-foundry` commands on this page.


Use the Foundry Hub CLI in a dedicated environment. For macOS/Linux or a Bash
session on Windows, install it with:

```bash
python3 -m venv .venv-foundry
source .venv-foundry/bin/activate
python -m pip install apheris-foundry-cli
```

Use the CLI version supported by your deployment. Run subsequent commands from
the extracted tutorial folder containing `Data/` and `Settings/`. If using this
HTML alone, download the input ZIP and linked settings first, keeping their
shown paths. Replace the example Hub URL with yours.

## Connect and discover

```bash
apheris-foundry --version
apheris-foundry login --url https://your-hub.example
apheris-foundry workflows list
apheris-foundry workflows docs --workflow rfd4-proteina-design
apheris-foundry workflows docs --workflow predict
apheris-foundry workflows docs --workflow rfd4-proteina-refold-score
apheris-foundry workflows models --workflow rfd4-proteina-design --json
apheris-foundry workflows models --workflow predict --json
```

Confirm these three workflows are available, with antibody weights and a
template-capable predictor. Use the deployed schema and advertised checkpoint.

## Add workflow skills to your agent

```bash
apheris-foundry skills install --agent codex
apheris-foundry skills install --workflow rfd4-proteina-design --agent codex
apheris-foundry skills install --workflow predict --agent codex
apheris-foundry skills install --workflow rfd4-proteina-refold-score --agent codex
```

Use `--agent claude` for Claude, or `--path` for a project skill directory.
Reload skills in the agent. Complete the CLI connection checks first. Skills
supply instructions. The CLI and your Hub session supply execution access.

## Run one antibody candidate

After confirming the advertised antibody weight, submit the supplied VHH example:

```bash
apheris-foundry workflows run --workflow rfd4-proteina-design \
  --input Data/03-vhh --weight antibody-2026-10-30 \
  --param numReplicates=1 --param batchSize=1 --param seed=42 \
  --param recycleStrategy=high/front_loaded \
  --param refold=true --param refoldTopN=1 --wait
```

Replace the quoted job ID below with the returned ID:

```bash
apheris-foundry jobs get --id "<design-job-id>"
apheris-foundry jobs logs --id "<design-job-id>"
apheris-foundry jobs download --id "<design-job-id>" --output runs/pilot
```

Use `cli-result.json` to locate the downloaded `refold/holo/` folder. Pass that
folder as the next input. If it is at the expected path below and Boltz-2 is
listed in your catalogue, run:

```bash
apheris-foundry workflows run --workflow predict \
  --input runs/pilot/refold/holo --model boltz --weight boltz2 \
  --model-params @Settings/06-holo-model-params.json --wait
```

Download that run separately:

```bash
apheris-foundry jobs download --id "<prediction-job-id>" --output runs/holo
```

Read each download's `cli-result.json` to locate the actual output folders.
Copy the complete `design/` and holo `predictions/` folders under
`runs/score-input/` as shown in [Evaluate](06-evaluate.md), then run:

```bash
apheris-foundry workflows run --workflow rfd4-proteina-refold-score \
  --input runs/score-input --param cofoldingModel=boltz2 \
  --param criterion=auto --wait
```

Download the scoring run in the same way and follow `score/result.json` to its
CSV. Check `pass`, `status` and `pass_note`, including failed evaluations.
For failures,
use `apheris-foundry jobs error --id "<job-id>"`. Once the complete pilot works,
increase `numReplicates` and choose how many candidates to refold.

## Agent request to copy

```text
Use my configured Hub and installed Foundry workflow skills.
Verify the deployed task schemas and antibody weight before computing.
Run Data/03-vhh with Settings/03-vhh.json for one candidate.
Refold with Boltz-2, explicitly selecting boltz2, then score its refold.
Preserve the prepared query, conditioned template and detailed scores.
If a required workflow, weight or task is absent, report the missing capability.
Return job IDs, image/weight identities, sequences, CIF paths and the score CSV,
including failed or missing evaluations. Do not launch a larger campaign.
```
