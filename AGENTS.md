# AGENTS.md

Starting context for any agent working in this repo. Read this first, then `LEO/README.md` for the full notes.

## What this project is

Team entry for the Oslo AI × Antibodies hackathon (Saturday 14 November 2026). The goal is to design HER2 antibodies that beat trastuzumab, using Apheris Foundry (RFD4-Proteina models) and other tools. Each design is scored against a measured trastuzumab baseline on three properties: binding (SPR), epitope preservation (competitive binding against trastuzumab), and thermostability (direct measurement). Adaptyv expresses designs cell-free and runs the assays; results arrive after the event.

## The two tracks are assigned, not chosen

`abguard` decides each design's track from its sequence. The team does not pick.

- Identity to nearest known antibody **under 70%** → **de novo** track.
- Everything else → **optimisation** track.
- A design is **never moved between tracks**. If it misses its own track's criteria it is rejected, not reclassified.
- A team may submit **any mix** of the two. The tracks are scored independently, with a separate prize pot each.

So "which track are we doing?" is the wrong question. The right one is "what is each design's identity to known antibodies, and does it then pass that track's extra check?"

## Hard constraints (all enforced by `abguard`)

`immunum` first strips tags and linkers to extract the antibody sequence. Then:

**Shared checks, every design**
- Numbering confidence at least 0.1 (is it an antibody?)
- Format is VHH, scFv or Fab
- Total length at most 250 aa (single scFv or VHH, or VH and VL combined)
- No unpaired cysteines

**Identity comparison is type-aware**
- A VHH is compared against known VHHs and heavy chains.
- An scFv or Fab is split into paired chains and compared as paired antibodies.

**De novo track, extra check**
- At least 2 CDRH3 mutations away from trastuzumab

**Optimisation track, extra checks**
- CDRH3 identity to trastuzumab strictly under 70%
- **Strictly more than 2** point mutations from any provided data point

> **Off-by-one warning.** Page 2 of the task description says "at least 2 mutations", but the flowchart and the hard-filter list both say *more than* 2. Use **3 as the minimum** for optimisation designs so nothing is lost to the stricter reading.

**Novelty set**
- A design's CDRH3 must differ from all **525,063** CDRH3s in the HER2 tables (`hackathon-data/her2-trastuzumab/`). The 524,346 figure elsewhere is the FACS variant count, a different number for a different purpose.

**RFD4-Proteina input rules**
- PDB files are rejected. Use annotated CIF/BCIF, compressed CIF, or a structure directory.
- Pass the design spec file as `input`, not its parent folder. The parent folder silently ignores `contig` and `conditions`.
- Start at `batchSize 1` for the longest input to avoid running out of GPU memory.

**Deadline**
- The VM shuts down at the end of Saturday 14 November. Copy anything worth keeping before then.

## Only 4 designs are guaranteed to be tested

This governs every ranking decision.

- The team submits a **ranked list of up to 20** designs. Only the **top N** goes to the lab, so rank order is the real output.
- **4 designs are tested whatever happens.**
- Pitch placement adds: 1st +12 (16 total), 2nd +8 (12 total), 3rd +4 (8 total). Each of 6 judges nominates a favourite for +2.
- Ranking after testing counts **S-tier** designs (better on all three properties) first, then A-tier (two), then B-tier (one). Ten designs that each improve one property lose to two that improve all three.

Assume 4 tested. Optimise for a handful of designs that plausibly win on all three properties, not for volume or maximum novelty.

## Pitch day is 40% judgment, 20% reproducible repo

| Weight | Criterion |
|---|---|
| 40% | Judgment — clear reasoning behind the molecules chosen |
| 20% | Execution — a reproducible pipeline in a GitHub repo |
| 20% | User fit — what the design is for, and who needs it |
| 20% | Path to value — a credible route to real use |

Two consequences for agents: **record the reasoning** behind every design that makes the shortlist, and **keep the pipeline runnable end to end** from this repo. Both are directly scored.

## Where things are

| Path | Contents |
|---|---|
| `LEO/README.md` | Full notes: data, docs, setup, rules, submission, tasks, progress log |
| `LEO/docs/` | The two challenge PDFs (deck and task description) |
| `LEO/.venv/` | Python venv with `pypdf` (git-ignored) |
| `hackathon-data/` | **Not synced yet.** `aws s3 sync s3://apheris-oslo-hackathon/data/ hackathon-data/`. Never commit it. |
| `~/rfd4/` | **Not synced yet.** `aws s3 sync s3://apheris-oslo-hackathon/rfd4-proteina/docs/ ~/rfd4`. Start with `18-vm.md`, then `Tutorial.html`. |
| `~/foundry-assistant/` | Offline Foundry docs assistant (`make ask Q="..."`), models already in place |

Check whether the two synced paths exist before assuming their contents. Neither was present as of 2026-11-14.

## Models and weights

Foundry models run as Docker images on the VM. Pick the RFD4-Proteina weight by image:

| Image | Use |
|---|---|
| `release-2026-10-19` | General proteins and miniproteins |
| `antibody-2026-10-30` | Design or redesign CDRs on a fixed framework; the only option for CDRs other than CDRH3 |
| `her2-2026-11-07` | Redesign trastuzumab's CDRH3. `--sequence-tsr-k 2` (balanced) or `1` (exploratory) |
| `her2-novel-2026-11-09` | Mostly new CDRH3 loops; best measured novelty pass rate (86%) and lowest interface error (6.8 Å) |

The HER2 images only redesign CDRH3. Note the tradeoff: `her2-2026-11-07` conservative hits 21% known binders but **0%** pass the novelty filter, so its best-scoring designs are exactly the ones that get rejected. Filter for novelty **before** ranking, never after.

Check designs with `refold-prepare` → fold with a Predict Structure model → `refold-score`. Rank on `min_ipae`, `iptm` and `binder_plddt`; the pass column stays empty for the HER2 exercise. For binders prefer a folding model that **takes a template** (OpenFold3, Protenix, Boltz-2, Mol-1), because ESMFold2 and Boltz-1 have no template support and ESMFold2 folds the target unguided.

## Developability: two of three properties have no built-in proxy

The RFD4-Proteina metrics only speak to binding. Thermostability and epitope preservation do not appear in them, and a design that fails to express cannot be measured at all. There is no hard filter for expression, but Adaptyv reports expression success improved when participants scored candidates with **Aggrescan 3D**, **SoluProt**, **NetSolP**, and **ProteinMPNN with soluble weights**. No thermostability predictor is provided; choosing one is an open decision.

## Tools and accounts

- **AMASS:** literature, trial, patent and drug search. One person per team claims the $100 credits. The API key comes from the `AMASS_API_KEY` environment variable. Never write a key into the repo. Budget is roughly 2,000 searches; cache anything re-run.
- **Nebius Tools, JapanFold:** see `LEO/README.md` section 4. Setup files are in the Slack folder.
- **Claude Code:** pre-installed on the VM.

## Rules for agents

- Never commit secrets or API keys, nor the `hackathon-data/` and `LEO/.venv/` folders.
- Do not commit or push unless asked. End commit messages with a `Co-Authored-By:` line naming the model you are actually running as.
- Record every design run: input spec, weight image, settings, seed, and resulting scores. Put run notes in the owner's folder, not in shared folders.
- Keep each design's provenance and its **predicted** track (from its identity numbers) with the design. The real track assignment only comes from `abguard`, so treat local labels as predictions and verify them.
- When something is blocked or unclear, record it in the progress log in `LEO/README.md` rather than guessing.
- Prefer verifying a rule against `LEO/docs/*.pdf` over trusting a summary, including this one. The PDFs contradict themselves in at least one place (the mutation count).

## Open items

- Participant field guide did not load when fetched. Open it in a browser and add its contents to `LEO/README.md`.
- The developability write-up linked from the task description ("check the whole write-up here") is not captured. Find it on the hackathon site.
- JapanFold link and login are not yet recorded.
- `abguard` CLI and Nebius setup files are in the Slack folder. Install and test `abguard` early: it is the gate on every submission.
- AMASS onboarding walkthrough link returned 404.
- No thermostability predictor chosen.
