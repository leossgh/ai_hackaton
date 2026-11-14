# RFD4-Proteina in Foundry

> **On the hackathon VM?** There is no Foundry Hub there. Use [Run on your hackathon VM](18-vm.md) instead of the `apheris-foundry` commands on this page.


Open [Tutorial.html](Tutorial.html) for the offline reader, or [index.md](index.md) for individual lessons.

## Before you run

RFD4-Proteina generates protein sequences and all-atom structures together.
Start with [a new protein](#1-create-a-protein), [a binder](#2-design-a-binder)
or [refinement](#3-refine-a-binder).

### Set up once

Get your Foundry URL and access to **Design Proteins**, **Predict Structure**
and **Score Refolded Designs** from your platform team. Check the available
weight builds. [Foundry setup](https://www.apheris.com/docs/foundry/getting-started.html)
is an optional online reference.

The workflow IDs are `rfd4-proteina-design`, `predict` and
`rfd4-proteina-refold-score`, respectively.

For an agent or command-line session, start with
[connection and submission instructions](#connect-an-agent-or-run-from-the-cli).

1. Download the chosen input ZIP from this guide and extract it. Upload its
   `Data/<example>/` folder, keeping the spec and structures together.
2. Apply the values in its linked `Settings/` file to the workflow parameters.
   Keep settings outside the upload. Your client supplies input, output and weight selection.
3. Run Design Proteins. Antibody pilots request one candidate. Other fresh-design
   examples request four. Both use batch size 1 and seed 42. Counts are per input.
4. Open `design/result.json` for structures, metrics and logs, then
   [evaluate the candidates](#evaluate-candidates).

**Put each setting in the right place:** design length, fixed atoms and hotspots
belong in `design.yaml` / `design.json` or the annotated CIF. Generation settings
such as `numReplicates` belong to Design Proteins. Folding settings such as
`seeds` belong inside Predict Structure's `modelParams`.
The [technical reference](#technical-reference-what-to-pass) lists accepted fields and defaults.
Design results live in `<output>/design/`. Manifest paths are relative to that
task directory. Refolding preparation writes `<output>/refold/`.

Design requests one NVIDIA GPU, eight CPUs and 64 GiB host RAM. GPU memory
depends on the input. These examples use CIF, not PDB.

Also available: [motifs, enzymes, ligands and DNA](#other-design-tasks),
[training and metrics](#other-routes), and [troubleshooting](#troubleshooting).

### Use the UI

1. Open **Design Proteins** and upload the chosen example folder.
2. Select the required weight build and enter the linked settings in the
   displayed workflow controls. Keep the input spec with its structures.
3. Submit the job, check its final state and download the complete outputs.
4. Follow [Evaluate](#evaluate-candidates) through **Predict Structure** and
   **Score Refolded Designs**, using the prepared inputs and matching model label.

If a required control or model is unavailable, check your deployment's workflow
documentation before submitting. For agents, complete the CLI connection checks
before installing workflow skills.

## Connect an agent or run from the CLI

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

### Connect and discover

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

### Add workflow skills to your agent

```bash
apheris-foundry skills install --agent codex
apheris-foundry skills install --workflow rfd4-proteina-design --agent codex
apheris-foundry skills install --workflow predict --agent codex
apheris-foundry skills install --workflow rfd4-proteina-refold-score --agent codex
```

Use `--agent claude` for Claude, or `--path` for a project skill directory.
Reload skills in the agent. Complete the CLI connection checks first. Skills
supply instructions. The CLI and your Hub session supply execution access.

### Run one antibody candidate

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
`runs/score-input/` as shown in [Evaluate](#evaluate-candidates), then run:

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

### Agent request to copy

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

## 1. Create a protein

**Goal:** generate a new 100-residue sequence and fold, without a target.

Upload [Data/01-monomer/](Data/01-monomer/), select the **general release**
weights and use [Settings/01-monomer.json](Settings/01-monomer.json).
The annotated CIF encodes the length. Its spec preserves those instructions:

```yaml
monomer:
  input: monomer-short.cif.zst
  input_as_annotated_cif: true
```

Expect four generated single-chain structures. Check length, continuity and
clashes, then [refold them](#evaluate-candidates) without a target template.
To request 150 residues, decompress the example CIF and set both
`_atom_site.annotation_expsegmin_1_residue` and
`_atom_site.annotation_expsegmax_1_residue` to `150`. Keep its placeholder
`label_comp_id` and `auth_comp_id` consistent as `150-150`, and update the
spec's `input` to the edited `.cif`. Preserve the other annotations.

## 2. Design a binder

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

Run the selected example using [the shared steps](#before-you-run). Inspect the
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

For trastuzumab and HER2, start from [the fine-tuned HER2 models](#4-redesign-trastuzumab-for-her2).

Next: [evaluate](#evaluate-candidates), or read the [antibody-specific notes](#antibody-notes).

## Antibody notes

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

## 3. Refine a binder

**Goal:** explore nearby versions of a promising design. Partial diffusion
changes both sequence and structure. Evaluate children to establish improvement.

1. Upload one RFD4-Proteina `*_generated.cif` from an earlier run. Preserve its
   annotations and use the generated complex, rather than a predictor's refold.
2. Keep the parent's checkpoint family and recycle schedule. Use
   [miniprotein settings](Settings/04-refine.json) or
   [antibody settings](Settings/04-refine-antibody.json): eight children,
   `partialTrajectoryFraction: 0.4`, hotspot resampling off.
3. [Refold and compare](#evaluate-candidates) children with the parent using the same
   prediction settings. Record each child's parent and fraction.

The fraction re-runs 40% of the 60 sampling steps. Smaller fractions generally
stay closer to the parent. Larger ones explore further. It does not specify
a structural displacement. An experimental binder first needs an explicit
annotated redesign problem.

Inspect parents before multiplying them: [Adaptyv refinement](#adaptyv-a-miniprotein-example)
also propagated an unwanted terminal tail.

## 4. Redesign trastuzumab for HER2

Two fine-tuned weights redesign the CDRH3 loop of trastuzumab, an antibody that
binds the HER2 receptor. Together with one sampling setting they give four
models. They learned from a public lab screen of trastuzumab variants, so their
loops match measured HER2 binders far more often than the general antibody
model's do. Use them as a starting point, then filter and rank the designs
yourself.

### Terms

| Term | Meaning |
| --- | --- |
| CDRH3 | The third loop of the antibody heavy chain that touches the target. It makes most of trastuzumab's contact with HER2. In the example file it is heavy chain B, residues 99 to 108 in the file's own numbering, sequence `WGGDGFYAMD` in trastuzumab. |
| FACS screen | The lab experiment the models learned from. [Chinery et al.](https://www.biorxiv.org/content/10.1101/2024.03.26.586756v2) made about 524,000 trastuzumab variants, each with a different CDRH3, and sorted them by how well they bind HER2 into high, medium and low binders. |
| Known binder | A design whose CDRH3 the screen labelled high. |
| Known non-binder | A design whose CDRH3 the screen labelled low. |
| SPR binder | A CDRH3 whose binding strength (affinity) was measured by surface plasmon resonance. [The challenge data](#her2-hackathon-data) lists them. |
| Challenge filter | The optimisation track's novelty rule. A design passes if its CDRH3 differs at 2 or more of its 10 positions from every sequence in the provided data (every screened variant and every SPR design) and is at most 70% identical to trastuzumab's CDRH3 (at least 3 of 10 positions changed). |
| Weight | A named set of trained model parameters on Foundry. You choose one with `--weight`. |
| `sequenceTsrK` | A decimal number above 0 that sets how random the sequence of each design is. The default is 4. Higher values make the model pick the sequences it rates most likely, so designs repeat more. 1 removes that sharpening and gives the most varied sequences. Values below 1 are allowed but we have not tested them. It does not change how the 3D structure is sampled. |
| Seed | A number that fixes the random choices of a run, so the same seed gives the same designs. |
| Interface error | Protenix's lowest predicted aligned error between antibody and HER2 residues after refolding a design, in ångström. Lower means Protenix is more confident the design fits HER2. |

### What we did

1. **Started from NVIDIA's antibody model** (weight `antibody-2026-10-30`),
   which designs CDR loops on a fixed antibody framework.
2. **Picked training examples from the screen.** We chose a varied set of
   high binders.
3. **Placed each loop on a real structure.** Every chosen loop was put onto
   the crystal structure of trastuzumab bound to HER2 (PDB 1N8Z).
4. **Taught the model to redesign only CDRH3.** The rest of the antibody and
   HER2 stay fixed. This gave the weight `her2-2026-11-07`.
5. **Trained a second weight on pairs.** Starting again from the antibody
   model, we showed it pairs of one high and one low binder and rewarded it
   for preferring the high one. This gave the weight `her2-novel-2026-11-09`.
6. **Checked every model.** Each made 300 designs (seeds 1, 2 and 3, 100
   designs each), except HER2 novel, which made 100 (seed 1). We compared every
   design with the screen and refolded it with Protenix.

### The models

| Model | `--weight` | `sequenceTsrK` | Use it to |
| --- | --- | --- | --- |
| HER2 balanced | `her2-2026-11-07` | `2` | Start here. Many distinct loops, about a fifth of them known binders |
| HER2 conservative | `her2-2026-11-07` | Leave unset | See the loop the model prefers. Few distinct designs, close to the known binders |
| HER2 exploratory | `her2-2026-11-07` | `1` | Find new loops. Almost all are untested sequences |
| HER2 novel | `her2-novel-2026-11-09` | Leave unset | Find new loops with the lowest interface error |
| Antibody | `antibody-2026-10-30` | Leave unset | Redesign the other CDRs, or design antibodies for other targets |
| Release | `release-2026-10-19` | Leave unset | General protein design, not antibodies |

### How they compare

Results on the [HER2 example](Data/12-her2/). Distinct designs is the share of
designs whose CDRH3 appears only once. Interface error is the median over
designs.

| Model | Designs | Distinct designs | Known binders (distinct loops) | Known non-binders | Pass the challenge filter | Interface error (Å) |
| --- | --- | --- | --- | --- | --- | --- |
| Antibody (not fine-tuned) | 300 | 77% | 0% (0) | 0% | 100% | 8.2 |
| HER2 conservative | 300 | 7% | 21% (9) | 0% | 0% | 9.4 |
| HER2 balanced | 300 | 64% | 21% (38) | 0% | 6% | 9.1 |
| HER2 exploratory | 300 | 100% | 0.3% (1) | 0% | 74% | 9.1 |
| HER2 novel | 100 | 90% | 4% (1) | 0% | 86% | 6.8 |

About a fifth of HER2 conservative and balanced designs are known binders. The
untuned model made none. A known binder always fails the challenge filter,
because it is already in the screen. No model made a known non-binder. HER2
exploratory and HER2 novel make mostly new loops that pass the filter. The
screen cannot tell whether those loops bind, because nobody measured them.
HER2 novel passes most often and has the lowest interface error.

### Run a model

1. Set up the CLI and log in as in [CLI setup](#connect-an-agent-or-run-from-the-cli). Run every command
   below from the extracted tutorial folder, the one that holds `Data/` and
   `Settings/`.
2. Check that your deployment lists the HER2 weights:
   `apheris-foundry workflows models --workflow rfd4-proteina-design`.
3. Submit the [HER2 example](Data/12-her2/). This runs HER2 balanced with the
   [HER2 settings](Settings/12-her2.json):

```bash
apheris-foundry workflows run --workflow rfd4-proteina-design \
  --input Data/12-her2 --weight her2-2026-11-07 \
  --param sequenceTsrK=2 --param numReplicates=100 --param batchSize=1 \
  --param seed=1 --param recycleStrategy=high/front_loaded \
  --param refold=true --param refoldTopN=20 --wait
```

4. Download the results, replacing the job ID with the one the run printed:

```bash
apheris-foundry jobs download --id "<design-job-id>" --output runs/her2
```

5. [Evaluate](#evaluate-candidates) the designs.

For another model, change `--weight` and `sequenceTsrK` as in the models table.
For HER2 conservative or HER2 novel, remove `--param sequenceTsrK=2`. The other
parameters are explained in [Parameters](#technical-reference-what-to-pass).

### Keep in mind

- **The screen measured binding, not affinity.** These models propose likely
  binders. Nothing trained them to improve affinity, so use the [SPR data](#her2-hackathon-data) for that.
- **Only CDRH3 changes.** To change other CDRs as well, redesign them with
  the antibody model.
- **Filter before you rank.** Most conservative and balanced loops are
  already in the screen and fail the challenge filter. Apply the filter to
  every design first.
- **HER2 novel was tested on one seed.** Its numbers come from 100 designs.
- **Do not rank on CDRH3 refold agreement.** Protenix does not reproduce
  trastuzumab's own CDRH3 loop, so a mismatch there says little.

## Evaluate candidates

Generation proposes candidates. Refolding checks whether another predictor
recovers their folds and poses. Experiments establish binding and specificity.

### 1. Prepare

The pilot settings enable `refold` and prepare every candidate. Keep
`design/`, `refold/holo/` and `refold/selection.csv`. A failed preparation can
leave valid designs. Read `refold/error.json` and split incompatible batches.

### 2. Predict

Upload `refold/holo/` to **Predict Structure**. Select a model and weight offered
by your deployment. The cofolding modules support these choices:

| Model | Weight build | Matching score label | Uses a template |
| --- | --- | --- | --- |
| OpenFold3 | `of3ob` / `of3p2` | `openfold3-of3ob` / `openfold3-of3p2` | Yes |
| Protenix | `v2` / `v1-default` | `protenix-v2` / `protenix-v1` | Yes |
| Boltz-2 | `boltz2` | `boltz2` | Yes |
| Mol-1 | `base` | `mol1-base` | Yes |
| Boltz-1 | `boltz1` | `boltz1` | No |
| ESMFold2 | `release` | `esmfold2-release` | No |

Models without a template fold the target unguided. Run them with the untemplated
settings below, even for binders.

Mol-1 uses the shared prediction workflow. For Boltz, select
`--model boltz --weight boltz2` explicitly. The optional `weights` field is a
checkpoint-path override. Select build names such as `boltz2` through the client.
Put the [holo model settings](Settings/06-holo-model-params.json) inside `modelParams`:

```json
{"template_paths": ["template.cif"], "write_detailed_scores": true,
 "num_diffusion_samples": 1, "seeds": [42], "query_failures": "skip"}
```

Clients may serialize this object as JSON for `modelParams`. Preserve its keys
and value types. In the Hub CLI, use `--model-params @file.json`, not
`--param modelParams=...`. Keep model and weight selection outside that object.

Templates contain conditioned antigen/framework residues, not generated CDRs.
Monomers have no template: use [untemplated settings](Settings/06-untemplated-model-params.json).
No MSA upload is needed. Optional apo prediction uses those same untemplated
settings and the same model/weights. It does not change automated pass/fail.
Use the template-capable weights above for binder evaluation. Do not rely on
an unspecified model or weight default.

### 3. Score

Upload complete `design/` and holo `predictions/` outputs together to **Score
Refolded Designs**, retaining manifests and `.cbor.gz` detailed scores.
Use this folder layout:

```text
input/
├── design/             # complete design task output
├── predictions/        # complete holo prediction output
└── apo-predictions/    # optional complete apo prediction output
```

Set `cofoldingModel` to the matching label above and `criterion: "auto"`.
This records which model ran. Model selection happens in Predict Structure.
Find the CSV through `score/result.json`. To compare predictors, repeat prediction
and scoring separately on the same designs. Keep each model's scores separate.

| Design | Automated pass |
| --- | --- |
| Monomer | Backbone RMSD ≤ 1.5 Å |
| Protein binder | Binder pTM ≥ 0.8. Interface PAE ≤ 1.5 Å. Target-backbone-aligned binder RMSD ≤ 2.5 Å |
| Antibody | Interface PAE ≤ 2.0 Å. Target-aligned binder RMSD ≤ 2.0 Å |

Read `pass`, `status` and `pass_note`. Empty pass means missing evidence.
Preliminary filter failures cannot pass. Pose scoring needs group-0 target
atoms, and Fv interface metrics include VH–VL contacts. Compare results within
one predictor/protocol. Thresholds were calibrated with upstream's AF3 oracle.
If `refold/error.json` reports a template mismatch, split the designs into
compatible target/framework groups. Keep detailed scores enabled for binder
metrics. An optional `passCriteria` file changes thresholds. Leave it unset
for the vendored criteria.

## About RFD4-Proteina

RFD4-Proteina is a generative protein design model from NVIDIA and the Baker Lab. It designs a protein's
sequence and its full-atom 3D structure together, conditioned on a target you give it. Apheris Foundry runs
it as three workflows:

| Workflow | ID | What it does |
| --- | --- | --- |
| Design Proteins | `rfd4-proteina-design` | Generates designs, and optionally prepares the best ones for refolding |
| Score Refolded Designs | `rfd4-proteina-refold-score` | Scores folding-model refolds of designs against RFD4-Proteina's pass criteria |
| Fine-Tune Protein Design Model | `rfd4-proteina-finetune` | Trains the design model further on your own structures |

### What it designs

- **Antibodies:** VHHs (nanobodies) and paired VH/VL (Fv). It designs new CDRs against an epitope you choose,
  or redesigns selected CDRs of an existing antibody. See [How to design an antibody](#how-to-design-an-antibody).
- **Miniprotein binders** to protein targets.
- **Binders to small molecules, DNA and RNA.**
- **Enzymes** built around a catalytic motif, and **scaffolds** for a given functional motif.
- **Monomers** from scratch.

It can also refine an earlier design (partial diffusion) or design new sequences for a kept backbone
(inverse folding).

## Models available for RFD4-Proteina

RFD4-Proteina uses two kinds of model: a **design model** that generates proteins, and a **folding model**
that refolds each design to check it.

### Design models

Pick one with `--weight` in Design Proteins. Each is its own image build.

| Weight | What it is | Use it for |
| --- | --- | --- |
| `release-2026-10-19` | NVIDIA's general RFD4-Proteina model | Miniprotein binders, monomers, enzymes, motif scaffolds, ligand and DNA binders |
| `antibody-2026-10-30` | NVIDIA's antibody model | VHH and paired VH/VL antibody design against a chosen epitope |
| `her2-2026-11-07` | The antibody model, fine-tuned by Apheris on trastuzumab CDRH3 HER2 binders | Redesigning trastuzumab's CDRH3. `sequenceTsrK` 2 or 1 gives more varied loops. See [HER2 models](#4-redesign-trastuzumab-for-her2) |
| `her2-novel-2026-11-09` | The antibody model, trained by Apheris on pairs of HER2 binders and non-binders | Mostly new trastuzumab CDRH3 loops |
| Your own | A checkpoint from Fine-Tune Protein Design Model | Pass it as `weights` |

With `module-run`, the same models are named `release`, `antibody`, `her2-conservative`, `her2-balanced`,
`her2-exploratory` and `her2-novel` (`--model`), for a weights folder that holds several checkpoints.

### Folding models

Design Proteins prepares the best designs for refolding, Predict Structure refolds them with a folding model,
and Score Refolded Designs scores the result. Score with the label that matches the model you folded with.

| Folding model | Weight | Score label | Uses a template |
| --- | --- | --- | --- |
| OpenFold3 OpenBind | `of3ob` | `openfold3-of3ob` | Yes |
| OpenFold3 preview 2 | `of3p2` | `openfold3-of3p2` | Yes |
| Protenix v2 | `v2` | `protenix-v2` | Yes |
| Protenix v1 | `v1-default` | `protenix-v1` | Yes |
| Boltz-2 | `boltz2` | `boltz2` | Yes |
| Boltz-1 | `boltz1` | `boltz1` | No |
| Mol-1 | `base` | `mol1-base` | Yes |
| ESMFold2 | `release` | `esmfold2-release` | No |

For binders, prefer a model that uses a template: it folds the design against the target in its known
pose. Models without one fold the target unguided.

Settings for each model are in the [technical reference](#technical-reference-what-to-pass).

## How to design an antibody

Use the antibody model, weight `antibody-2026-10-30`, in Design Proteins. It designs new CDR loops against an
epitope you choose and keeps the antibody framework fixed. It handles VHHs (nanobodies) and paired VH/VL (Fv).
For a Fab or IgG, design the Fv and add the constant domains afterwards.

### What to prepare

1. **The antigen** as an mmCIF file. PDB files are rejected.
2. **A framework**: a VHH or VH/VL structure whose framework you want to keep, such as a clinical antibody.
3. **The epitope**: a few antigen atoms the antibody should contact (hotspots).
4. **A length range for each CDR.**

### The design spec

A short JSON or YAML file says what to keep and what to design. From the Fv example
([full file](Data/03-fv/design.json)), which designs six CDRs on adalimumab's
framework against ubiquitin (chain F):

```json
{
  "contig": "F1-76, /0, H1-22, 13-15, H24-37, 9-10, H39-75, 11-22, H77-87, /0, L1-23, 11-14, L25-38, 8-8, L40-71, 8-12, L73-82",
  "conditions": {
    "C_CRD":    {"true": [{"select": "sel('F/*/*/[N,CA,C,O]')"}]},
    "C_CRDGRP": {"1": [{"select": "sel('H/*/[1-22, 24-37, 39-75, 77-87]/[N,CA,C,O]')"},
                       {"select": "sel('L/*/[1-23, 25-38, 40-71, 73-82]/[N,CA,C,O]')"}]},
    "C_SEQ":    {"true": [{"select": "sel('F')"}, {"select": "sel('H/*/[1-22, 24-37, 39-75, 77-87]')"},
                          {"select": "sel('L/*/[1-23, 25-38, 40-71, 73-82]')"}]},
    "C_HOT":    {"true": [{"select": "sel('F/*/8/CD1')"}, {"select": "sel('F/*/70/CG1')"}]},
    "C_CATH":   {"2.60.40": [{"select": "sel('H')"}, {"select": "sel('L')"}]}
  }
}
```

- **`contig`** lays out the chains. Ranges with a chain letter are kept from the input. Bare ranges such as
  `13-15` are designed CDRs of that length. `/0` starts a new chain.
- **`C_SEQ`** keeps the sequence of the antigen and the framework.
- **`C_CRD`** keeps the antigen backbone where it is.
- **`C_CRDGRP`** keeps the framework's internal shape. Put VH and VL in one group so they stay paired.
- **`C_HOT`** marks the epitope atoms.
- **`C_CATH`** marks the antibody chains as an immunoglobulin fold (`2.60.40`).

Residue numbers are the file's own (`label_seq_id`). A VHH spec has one antibody chain and three CDRs.

To redesign selected CDRs of an existing antibody instead, keep every other CDR in `C_SEQ` and `C_CRDGRP`
and leave only the ones to redesign as bare ranges. For trastuzumab's CDRH3 against HER2, the
[HER2 models](#4-redesign-trastuzumab-for-her2) give better starting points than the general antibody model.

### Run it

```bash
apheris-foundry workflows run --workflow rfd4-proteina-design \
  --input Data/03-fv --weight antibody-2026-10-30 \
  --param numReplicates=100 --param batchSize=1 --param seed=1 \
  --param recycleStrategy=high/front_loaded \
  --param refold=true --param refoldTopN=20 --wait
```

Use `recycleStrategy=high/front_loaded` for antibodies. Plan 100 to 200 designs per target: upstream reports
binder pass rates around 8 to 11%. On an A100 a VHH takes about 24 s per design and a VH/VL about 36 s.

### Check the designs

Refold the prepared designs with a folding model and score them: see [Refolding](#check-designs-by-refolding-them).
Look at the antigen contacts in each accepted complex. For an Fv, scoring picks one chain of interest and
counts the other antibody domain as a partner, so a good interface score can reflect VH-VL confidence rather
than antigen binding.

To explore close variants of a promising design, run Design Proteins on its `*_generated.cif` with
`partialTrajectoryFraction` set (see [Refine a binder](#3-refine-a-binder)).

## Check designs by refolding them

A design is worth testing when an independent folding model, given only its sequence, folds it into the
designed complex. Foundry runs this in three steps:

1. **Design Proteins** with `refold=true` prepares the best designs for refolding (the top 20% by default,
   or `refoldTopN`).
2. **Predict Structure** refolds them with a folding model, once bound to the target (holo) and once alone
   (apo).
3. **Score Refolded Designs** scores each refold against RFD4-Proteina's pass criteria, taken from the
   upstream AlphaFold3 check: confidence in the binder, confidence in the interface, and agreement with the
   designed structure.

The folding models and their score labels are listed in [Models](#models-available-for-rfd4-proteina).
For binders, prefer one that uses a template. The cut-offs were calibrated on AlphaFold3 and can shift by
model, so compare pass rates within one model.

Upstream reports binder pass rates of 7.7% to 10.6%, so plan 100 to 200 designs per target. On an A100,
refolding takes about 25 s per design per model, plus 20 s for the apo run.

The full protocol and the exact pass criteria are in [Evaluate candidates](#evaluate-candidates). Upstream's own
metrics, without refolding, are in [Advanced routes](#other-routes).

## HER2 hackathon data

The data is in the hackathon bucket under `s3://apheris-oslo-hackathon/data/`, and the RFD4-Proteina
docs are under `s3://apheris-oslo-hackathon/rfd4-proteina/docs/`. Download all
of it (about 3 GB) with:

```bash
aws s3 sync s3://apheris-oslo-hackathon/data/ hackathon-data/
```

Or fetch only the two HER2 tables (6 MB):

```bash
aws s3 cp s3://apheris-oslo-hackathon/data/her2-trastuzumab/ hackathon-data/her2-trastuzumab/ --recursive
```

| Folder | What it holds | Size |
| --- | --- | --- |
| `her2-trastuzumab/` | The two trastuzumab tables below: FACS binding classes and SPR affinities | 6 MB |
| `zenodo-18390239-ab-ag-complexes/` | Scores and accuracy tables for 1.8 million predicted nanobody-antigen complexes | 0.6 GB |
| `zenodo-10831512-trastuzumab-ngs/` | Ready-made train, validation and test splits of the FACS data, plus earlier HER2 datasets | 2.5 GB |

### Trastuzumab and HER2

Trastuzumab is a clinical antibody that binds HER2, a receptor on some breast cancer cells. Both tables come
from [Chinery et al.](https://www.biorxiv.org/content/10.1101/2024.03.26.586756v2), who changed trastuzumab's
CDRH3 (the third loop of the heavy chain, its main contact with HER2) and measured how the variants bind. The
hackathon organisers at the University of Oslo prepared them as tables. Cite Chinery et al. when you use them.

These two tables are the "provided data" for the challenge filter: a design must differ from every CDRH3 in
both of them (525,063 unique sequences). See [HER2 models](#4-redesign-trastuzumab-for-her2).

#### FACS binding classes

`tz_her2_facs_3classes_524346.csv.zip` holds 524,346 trastuzumab variants, each with a different 10-residue
CDRH3. Each variant was shown on the surface of a cell and sorted by how strongly it bound HER2 (FACS,
fluorescence-activated cell sorting). Use it to train a binder or non-binder classifier, or to check a design
for novelty.

| Column | Meaning |
| --- | --- |
| `cdrh3` | The CDRH3 sequence, always 10 residues |
| `binding_class` | `high` (172,149), `medium` (190,011) or `low` (162,186) HER2 binding |
| `vh_sequence` | The full heavy-chain variable domain (VH) carrying this CDRH3 |
| `vl_sequence` | Trastuzumab's light-chain variable domain (VL), the same in every row |
| `edit_distance` | How many CDRH3 positions differ from trastuzumab's (`WGGDGFYAMD`), 1 to 10 |

The classes say whether a variant binds, not how tightly. Trastuzumab itself is not in the table.

#### SPR affinities

`trastuzumab_her2_spr_all_768.csv` holds 768 designed variants whose binding to HER2 was measured by surface
plasmon resonance (SPR), which reports affinity as a dissociation constant (KD). A lower KD means tighter
binding. 190 rows have a KD. Use it to train or test an affinity predictor, or to rank binders.

| Column | Meaning |
| --- | --- |
| `cdrh3` | The CDRH3 sequence, 9 or 10 residues for trastuzumab variants |
| `vh_sequence`, `vl_sequence` | The full variable domains that were measured |
| `kd_nM` | KD in nanomolar, filled only for `quantified_binding` (0.023 to 13,863 nM, median 64 nM) |
| `binding_result` | `quantified_binding` (190), `no_reportable_kd` (460, measured with no KD reported), `inconclusive` (104) or `not_reported` (14) |

Trastuzumab itself appears 8 times as a reference, with KD 0.03 to 0.18 nM. Another 8 rows are a different
antibody (CDRH3 `ARDRIVDDYYYYGMDV`, different VH and VL) with no KD. Drop them when you model trastuzumab
variants. 37 SPR CDRH3s also appear in the FACS table.

### Antibody-antigen structure predictions

[Smorodina et al.](https://doi.org/10.5281/zenodo.18390239) (CC BY 4.0) folded 106 known nanobody-antigen
pairs and 11,342 shuffled pairs, in which each nanobody is matched with an antigen it does not bind, with
AlphaFold3, Boltz-2 and Chai-1. Their finding: a folding model's interface confidence (ipTM) often fails to
tell a real pair from a shuffled one. Use these tables to check how far to trust a folding model's
confidence when you rank designs.

| File | Contents |
| --- | --- |
| `iptm_confidence_scores.zip` | One ipTM matrix per folding model: a row per nanobody, a column per antigen, each named by PDB ID. The diagonal holds the real pairs |
| `topmodel_structure_accuracy.zip` | A structure accuracy score for each top-ranked prediction, one CSV per folding model |
| `rmsd_between_replicas.zip` | RMSD (how far apart two structures are, in Å) between repeat predictions of the same pair, one CSV per folding model (4.8 GB unzipped) |
| `ab_ag_champloo_graphical_abstract.png` | The study's summary figure |

The predicted structures themselves (about 30 GB per folding model) are on
[Zenodo](https://zenodo.org/records/18390239) only.

### Ready-made training splits

[Mehta et al.](https://doi.org/10.5281/zenodo.10831512) (CC BY 4.0) published the data behind the FACS
table together with the splits they used to train binding classifiers. The bucket holds their `data.zip`
(2.5 GB, 4 GB unzipped). The HER2 parts are under `data/affinity_data/her2/`:

| Folder | Contents |
| --- | --- |
| `her2_aff_large/processed/remove_overlap/clonotype_split/0.7_0.15_0.15/` | The 524,346 FACS variants split 70/15/15 into train, validation and test. Similar CDRH3s are kept in the same split, so a model is tested on sequence families it has not seen. `label` is 1 for high binders |
| `her2_aff_large/processed/remove_overlap/clonotype_split/train*_val*/` | Small training sets (140 to 23,834 sequences) with every other variant as the test set, to test how a model does with little data |
| `shanehsazzadeh_et_al/processed/test.csv` | 198 CDRH3s from an earlier trastuzumab design study, all binders, with an `affinity` value on a log scale (6.2 to 9.0, higher is tighter) |
| `mason_et_al/` | Train, validation and test splits of an earlier trastuzumab CDRH3 binder and non-binder library |

Each folder has a README with its sizes and also holds the authors' trained classifier weights (`.h5`,
`.pkl`). The influenza folders are not relevant to HER2. The raw sequencing reads (about 26 GB of FASTQ
files) are on [Zenodo](https://zenodo.org/records/10831512) only, and you do not need them.

## Technical reference: what to pass

### Design instructions: the uploaded spec

Each top-level design ID maps to `input`, optional `contig`, `conditions` and
`input_as_annotated_cif`. Relative structure paths resolve from the spec's
directory and must stay inside the uploaded tree. Upload every referenced file.
With multiple specs, set workflow `spec` to the chosen relative filename.
The optional top-level `global_args` supplies defaults shared by the design IDs.

| Field / condition | Meaning |
| --- | --- |
| `input` | One CIF/BCIF path or a list of structures with distinct chain IDs |
| `input_as_annotated_cif: true` | Preserve existing conditioning. Default is `false` for freshly prepared inputs |
| `contig` | Retained residue ranges, expandable lengths and `/0` chain breaks |
| `C_SEQ` | Preserve selected residue identities |
| `C_CRD` | Fix selected atoms in absolute coordinates. Group 0 supplies the pose-scoring frame |
| `C_CRDGRP: 1` | Preserve internal geometry while allowing rigid-body placement. Use for framework backbones |
| `C_HOT` | Request contacts to selected target atoms |
| `C_CATH: "2.60.40"` | Supply immunoglobulin fold context on antibody chains |
| `C_RAS` | Exposure bin: `BURIED`, `INTERMEDIATE`, `EXPOSED` or `UNSPECIFIED` |
| `C_HB` | Hydrogen-bond role: `DONOR`, `ACCEPTOR` or `BOTH` |
| `C_PISTACK`, `C_PICATION` | Stacking: `true`. Aromatic/cation role: `AROMATIC`, `CATION` or `BOTH` |
| `C_CENTROID` | Literal `"x,y,z"` chain centroid, covering every atom of every chain |
| `C_IDX: false` | Unindex selected atoms, with a shared `group` label where their relative offsets must remain linked |

CDR lengths and hotspot selections are input conditions, not workflow flags.
An ordinary CIF needs an explicit design problem. Side-chain coordinate
conditioning also reveals residue identity. Backbone-only conditions permit
sequence redesign where sequence is not fixed.
For complete selection syntax and condition values, see the optional online
[spec reference](https://rfd4-proteina.org/latest/reference/yaml-json.html).

### Design Proteins: workflow parameters

| Parameter | Meaning and default |
| --- | --- |
| `input`, `output` | Upload directory and persistent result root. Keep output/work directories outside input |
| `spec` | Relative JSON/YAML spec filename. Inferred for a sole top-level spec |
| `numReplicates` | Designs per input, 1–200. Default `1` |
| `batchSize` | Generation batch size. Default `1` |
| `seed` | Nonnegative integer. Random when omitted |
| `recycleStrategy` | Default `thinking_medium` (`medium/front_loaded`). Use `high/front_loaded` for antibody examples, `medium/midpeak` for enzyme/ligand examples |
| `resampleHotspots` | Default `false`. `true` replaces annotated hotspots with 2–3 sampled nearby atoms |
| `partialTrajectoryFraction` | Omit for fresh generation. Fraction in `(0,1]` covering at least one of 60 steps, on an annotated generated parent |
| `inverseFolding` | Version-dependent fixed-backbone sequence redesign. Requires complete coordinates and a matching module contract |
| `compile` | Default `false`. Compilation adds startup cost per padded length |
| `weights` | Optional compatible flow-checkpoint path. Omission uses the selected build's weights and paired autoencoder |
| `sequenceTsrK` | Decimal number above 0 that sets how random each design's sequence is. Default 4. Higher values repeat the sequences the model rates most likely. 1 removes that sharpening and gives the most varied sequences. Below 1 is allowed but untested. Structure sampling is unchanged. See [HER2 models](#4-redesign-trastuzumab-for-her2) |
| `refold` | Default `false`. `true` prepares prediction inputs after generation, without running prediction |
| `refoldTopN` | Explicit count to prepare. Requires `refold: true`. Otherwise preparation selects the top 20%, rounded up |
| `logLevel` | Workflow logging level. Default `info` |

An antibody pilot, copied from the supplied settings file:

```json
{"numReplicates": 1, "batchSize": 1, "seed": 42,
 "recycleStrategy": "high/front_loaded", "resampleHotspots": false,
 "compile": false, "refold": true, "refoldTopN": 1}
```

Do not combine partial diffusion with hotspot resampling. Use the selected
workflow's camelCase fields here. Raw module snake_case controls and upstream
Hydra overrides are separate interfaces. `inverseFolding` is version-dependent.
See [advanced routes](#other-routes).

### Predict Structure and Score Refolded Designs

| Where to pass it | Fields |
| --- | --- |
| Predict workflow | `input`, `output`, `model`, optional custom checkpoint path `weights`. Select the weight build through the client |
| Predict `modelParams` | `template_paths`: uploaded-relative CIF filenames. `write_detailed_scores`: boolean. `num_diffusion_samples`: positive integer. `seeds`: nonempty list of nonnegative integers. `query_failures`: `fail` or `skip` |
| Score workflow | `input`, `output`, required `cofoldingModel` label. `criterion`: `auto`, `ppi` or `antibody`. Optional uploaded-relative YAML `passCriteria` |

`refold/holo/queries.json` already contains the chain sequences and explicit
`msa_path: null` opt-outs. Upload it with `template.cif` when one was written.
Templates apply to every query in the batch. Use separate prediction and score
runs for each model/weight combination. RFD4 generation checkpoints and folding
model checkpoints are different assets.

## Other design tasks

The same model can preserve functional geometry and design protein around it.
Use **general release** weights and the linked settings:

| Goal | Upload | Settings |
| --- | --- | --- |
| Scaffold an enzyme site | [Annotated M-CSA motif](Data/05-enzyme/) | [Enzyme](Settings/05-enzyme.json) |
| Bind a small molecule | [SAM context](Data/05-ligand/) | [Ligand](Settings/05-ligand.json) |
| Bind DNA | [DNA structure context](Data/05-dna/) | [DNA](Settings/05-dna.json) |

These examples request four designs and preserve the CIF's annotations.
The model generates standard amino acids. Molecular context is supplied.
Check retained geometry, chemistry and clashes. Enzyme activity needs further testing.

The current refold adapter rejects ligand, DNA and RNA chains and has no motif
pass criterion. These exercises stop at design metrics (`refold: false`).

## Other routes

The supplied Hub workflows cover design, prediction and refold scoring.
The module also exposes `finetune` and `metrics` tasks. Run these through a
workflow that exposes them, or inside the supplied module container. Their
snake_case configuration keys are not Design Proteins workflow parameters.

### Fine-tune the generator

Provide a Parquet dataset with `example_id`, `path` and the metadata required by
the upstream PLINDER training recipe. Every referenced CIF must exist under the
`structures` root. Use compatible base weights and the paired autoencoder.

Inside the configured module container, with the dataset mounted at `/data`:

```bash
module-run finetune --input /data/train.parquet --output /output/train \
  --config '{"structures":"/data/cifs","epochs":1,"steps_per_epoch":50,"batch_size":1,"learning_rate":0.00001,"seed":42,"task_mix":"antibody"}'
```

Choose `task_mix: "plinder"` for the general training mix. Antibody training
requires a protein antigen and `_atom_site.ig_region` labels on antibody atoms
(`framework`, `cdr1`–`cdr4`). The autoencoder stays frozen. Training saves regular
and EMA checkpoints under `training/checkpoints/` and lists them in `result.json`.
Use a compatible `*-ema.ckpt` for inference and retain its paired autoencoder.
Assess it on independent data before scaling up.

### Recalculate metrics or cluster designs

Use a directory containing only the intended designs, excluding references
and refold outputs:

```bash
module-run metrics --input /data/designs --output /output/metrics \
  --config '{"metrics_tags":["design","hotspot_conditioning"],"cluster":false}'
```

Optional `task_csv` assigns structures to task groups. `cluster: true` requires
Foldseek through `FOLDSEEK_EXEC`. Read per-design, per-task and aggregate CSVs
from `result.json`, and compare report rows with the input count. Oracle tags
such as `antibody` and `*_refolding` are rejected by this image. Use Predict
Structure and Score Refolded Designs for refolding.

### Fixed-backbone redesign and upstream options

`inverseFolding` is exposed by the inspected workflow and pinned contract, but
the local module's `DesignConfig` lacks it. Confirm the deployed pair supports it.
It needs coordinates for every designed residue and cannot be combined with
expandable segments, partial diffusion or hotspot resampling.

Reward-guided search and metric guidance use upstream configuration beyond
the supplied workflow controls. Folding an existing sequence uses Predict
Structure directly. Context-conditioned design is covered in [other tasks](#other-design-tasks).

## Troubleshooting

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
a failure. See [evaluation](#evaluate-candidates) for the required output layout.

## Adaptyv: a miniprotein example

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

## Sources and validation

### Sources

- [Foundry workflows](https://www.apheris.com/docs/foundry/tasks-and-workflows.html): terminology and execution paths.
- [Hub CLI source](https://github.com/apheris/apheris-foundry-cli/tree/c2dc1779fee383466e49bbd3945414b69e0c989a): inspected login, skills and submission contract. Requires Apheris GitHub access.
- [Proteina module](https://github.com/apheris/apheris-rfd4-proteina): design, training, metrics and refold tasks. Requires Apheris GitHub access.
- [Cofolding source](https://github.com/apheris/apheris-cofolding/tree/958ea8c723c3aa2f6b1f955c29adf35f03e6750c): model capability maps and image builds. Requires Apheris GitHub access. [Bundled model options](Evidence/folding-models.json).
- [Pinned upstream](https://github.com/RosettaCommons/RFD4-Proteina/tree/68058693cb88762a8aaf806571e13b291ce6318a): examples, conditioning and recipes. [retained licence](LICENSE-RFD4.txt).
- [Chinery et al.](https://www.biorxiv.org/content/10.1101/2024.03.26.586756v2): trastuzumab CDRH3 binding screen behind the HER2 models.
- [Aggregate miniprotein results](Evidence/campaign-summary.json): the Adaptyv example's counts and limitations.
- [OKF v0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md): typed Markdown concepts and linked index.

### Package and checks

The HTML includes example ZIP downloads and inline settings. The full package
also contains `Data/`, `Settings/`, [Markdown](foundry.md) and [OKF](index.md).
`manifest.json` records input, settings and evidence hashes.

Checks cover package links, input hashes, parameter contracts, syntax,
interactive navigation, copy fallback and reproducible ZIP extraction.
The commands and packaged inputs were not rerun on a live Foundry deployment.
DOM tests do not verify rendered browser layout or a system clipboard.
Use the running workflow's documentation for its active contract and models.

### Changelog

10 November 2026: add the fine-tuned HER2 models exercise, its trastuzumab
example input and settings, the `her2-2026-11-07` weight and `sequenceTsrK`.

9 November 2026: replace raw-file navigation with inline previews and embedded
input downloads. Add navigation regression tests, troubleshooting and module
training/metrics instructions. Retain the Foundry theme and miniprotein-only
campaign example.
