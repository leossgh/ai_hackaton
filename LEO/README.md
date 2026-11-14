# Leo: Hackathon Info

Owner: Leo

## 1. Overview

- **Data and docs bucket:** `s3://apheris-oslo-hackathon/`
- **Main topic:** nanobody / antibody design with RFD4-Proteina on Apheris Foundry
- **Key constraint:** designed CDRH3 sequences must differ from all 525,063 CDRH3s in the HER2 tables (novelty filter)

## 2. Data

Download with:

```bash
aws s3 sync s3://apheris-oslo-hackathon/data/ hackathon-data/
```

| Folder | Size | Contents |
|---|---|---|
| `her2-trastuzumab/` | - | FACS binding classes (524k CDRH3s) and SPR affinities (768 variants). Source for the novelty filter. |
| `zenodo-18390239-ab-ag-complexes/` | - | Scores for 1.8M predicted nanobody-antigen complexes |
| `sigma2-ab-ag-champloo/` | - | Per-sample confidence (ipTM, pLDDT, PAE) for the same predictions |
| `sigma2-ab-ag-champloo/spr-supplementary/` | - | Measured SPR for a few of those pairs |
| `zenodo-10831512-trastuzumab-ngs/` | - | Ready-made train/val/test splits of the FACS data |

Total: about 5 GB. Each folder's `README.md` explains its files.

## 3. Docs and Instructions

Download with:

```bash
aws s3 sync s3://apheris-oslo-hackathon/rfd4-proteina/docs/ ~/rfd4
```

Then open `~/rfd4/Tutorial.html`.

| File | What it covers | Where to start |
|---|---|---|
| `foundry.md` | Running RFD4-Proteina through Apheris Foundry (UI, CLI, agents), from design to evaluation | - |
| `18-vm.md` | "Run on your hackathon VM": the VM has no Foundry Hub, but every Foundry model is already on it as a Docker image | **Start here** |

## 4. Setup and Connections

### 4.0 Tool Checklist

| Tool | Status | Link / how to connect | Notes |
|---|---|---|---|
| Apheris Foundry (RFD4-Proteina models) | Pre-installed on VM | `18-vm.md` in the docs | Models run as Docker images on the VM |
| Claude Code | Pre-installed on VM | - | Credits provided by Anthropic |
| abguard (validity CLI) | To be provided by organisers | Check the Slack folder | Runs the hard checks and novelty filter |
| Nebius Tools / Scientific AI | Available | `sciai.nebius.cloud/models` (Workbench > Apps) | No-code; can be connected to Claude as a skill. Setup files in the Slack folder |
| JapanFold | Available | Link not in the deck. Check the Slack folder. | RoseTTAFold3, OpenDDE, AF2-IG. Can be connected as a skill to Claude Code |
| AMASS | Available | See 4.1 | Literature, trial, patent and drug search with source links |
| Adaptyv antibody database | Reference for de novo check | Named in the challenge deck | Used for the under-70%-identity check |

### 4.1 AMASS

- **Event page:** https://amass.tech/oslo-ai-antibodies-hackathon
- **Onboarding walkthrough:** https://amass.tech/onboarding/oslo-ai-antibodies-hackathon (returned 404 when checked; try again or ask the organisers)
- **Connect to Claude (guide):** https://amass.tech/how-to-do-scientific-work-in-claude
  - Add Amass to Claude once and sign in once. The guide lists four steps, but only three are shown on the page.
  - Ask in plain language about a condition, target, drug, trial, mechanism, or company. Sponsor names and NCT numbers also work.
  - Open the linked records behind each answer and check the cited passages.
  - Amass queries six "Cores" during the conversation: 43M+ papers, 1.2M+ trials, 170M+ patents, 7K+ regulatory authorizations, 22K+ molecules, and 43K+ genes.
  - Filters: date, journal quality, retraction status, phase, and sponsor.
  - Requires Claude Pro, Max, Team, or Enterprise.
  - Data is not used for training. Enterprise hosting is EU-based. Certifications: ISO 27001 and SOC 2; NIS2 is in progress.
  - Install guide: https://amass.tech/mcp. Free trial: https://amass.tech/try.
- **Use the Amass app (guide):** https://amass.tech/how-to-use-amass (app: https://app.amass.tech; demo: https://amass.tech/demo)
  - Ask a question, then read the cited sources and filter by data layer.
  - Timelines view: trial landscape, approval timeline, and literature timeline.
  - Steer the research with a suggested next step or your own follow-up.
  - Attach your own PDF, Word, PowerPoint or text file, and ask questions about it.
  - Build a report: describe it, edit the plan, then read the cited sections. Tables are under Exhibits and export as CSV or Markdown. Reports export to PDF.
  - Organise work with pinned tasks, search, saved reports, and projects. Share a read-only task link that needs no account.
  - The guide's 13 videos are not in the text, so their steps are not captured here.
- **Help:** Amass Discord at https://discord.gg/sEGaBHMhWa (Amass joins remotely)
- **Platform sign-up:** https://platform.amass.tech/api/auth/sign-up (use the email registered for the hackathon; a free account is enough to start)
- **Claim team credits:** https://platform.amass.tech/event/ai-x-antibodies-hackathon-oslo. **One person per team claims the $100.**
- **Connect to Claude (no code):** add the Amass connector in Claude and sign in once. Claude needs a paid plan. The organisers provide Claude Max credits through Anthropic. Setup guide: https://amass.tech/how-to-do-scientific-work-in-claude
- **Coding path (API skill):**
  - Install: `npx skills add amass-technologies/public-skills --skill amass-api`
  - Skill file: https://github.com/amass-technologies/public-skills/blob/main/skills/amass-api/SKILL.md
  - API key: create at https://platform.amass.tech, then `export AMASS_API_KEY=...` (never commit the key)
- **Budget and costs:**
  - About $100 per team, roughly 2,000 searches or 10,000 record fetches.
  - Search: $0.05 per 20 results. Get-by-id and lookup: $0.01 each.
  - Cache results you re-run.
- **Amass track:** the most creative use of the data wins extra credits. Show which records your tool read and what it did with them.
- **Databases ("cores"):** six, such as BioMedCore (papers) and TrialCore (clinical trials).

### 4.2 Logistics

- **Date:** Saturday 14 November 2026, 09:00 to 20:00. Doors open at 08:30.
- **Venue:** BI Startup Village, BI Norwegian Business School, Nydalsveien 37, 0484 Oslo.
- **Rules:** https://oslo-ai-antibodies-hackathon.vercel.app/
- **Machines shut down** at the end of Saturday 14 November. Copy your files before then.

### 4.3 Still to Get

- **Participant field guide** (https://oslo-ai-antibodies-hackathon.vercel.app/participant_guide): the page came back empty when fetched, so its contents are not captured here. Open it in a browser.
- **JapanFold** link and login.
- **abguard** CLI and the **Nebius** setup files, both in the Slack folder.

### 4.4 Local Tools on the VM

**`/home/hackathon/foundry-assistant`:** an offline terminal assistant that answers Apheris Foundry questions from the docs. It runs two small local models (llama.cpp), with no network and no tokens. It doesn't need the Foundry Hub, so it can be used before anything else is set up.

- **Status:** both model files are present in `models/` (about 0.5 GB each). `llama-server` is at `/opt/llama.cpp`. Not yet started.
- **Run it:**

```bash
cd /home/hackathon/foundry-assistant
make install
make models  LLAMA_BIN=/opt/llama.cpp
make up      LLAMA_BIN=/opt/llama.cpp     # add NGL=0 for CPU
make ask Q="how do I install the foundry toolkit and log in?"
make tui                                  # interactive: /read <id>, /quit
make down
```

- **Knowledge base:** `kb/foundry-v1/kb/`, covering getting started, the CLI (commands, exit codes, troubleshooting), and the workflows (RFD4-Proteina design and finetune, affinity, AQ, ADMET, and structure preprocessing).
- **Useful pages:**
  - `getting-started-gs-install-login.md` and `getting-started-gs-run-a-workflow.md`: install, log in, and run a workflow.
  - `cli-troubleshooting.md`: auth errors (exit codes 3 and 8), SSH login port forwarding.
  - `workflows-rfd4-proteina-design.md`: the design task parameters.
- **Gotchas from the RFD4-Proteina design page:**
  - **PDB inputs are rejected.** Use annotated CIF/BCIF, compressed CIF, or a structure directory.
  - Pass the design spec file itself as `input`, not its parent folder. The parent folder silently ignores the spec's `contig` and `conditions`.
  - Use `batchSize 1` for the longest input to avoid running out of GPU memory.
  - A custom checkpoint must match the image's architecture and paired autoencoder.

## 5. Reference Documents

### 5a. Apheris Challenge Deck (`docs/2026-11_Oslo_hackathon_Apheris_challenge.pdf`, 9 pages)

- **Task:** build better HER2 binders with Apheris Foundry
- **Tracks** (prize pot of $1,500 per track, draft amounts):
  - *Optimisation:* improve trastuzumab. Same format as trastuzumab. Requires at most 70% CDRH3 identity to trastuzumab and at least 2 mutations from every sequence in the provided data.
  - *De novo:* design a new HER2 binder. VHH, scFv or Fab from scratch. Requires under 70% identity to any known antibody, checked against Adaptyv's antibody database.
- **Entry checks:** run automatically at submission. Failing designs are not sent to the lab. No unpaired cysteines; up to about 250 aa in scFv format.
- **Selection:** each team ranks its own designs. Adaptyv makes and tests 100 designs: 64 guaranteed (4 per team × 16 teams) and 36 extra.
- **Scoring:** binding to HER2 by SPR, epitope (still competes with trastuzumab), and thermostability.
- **Winning:** the team with the most S-tier designs (better on all three) wins. Ties go to A-tier, then B-tier. Lab results arrive after the event.
- **Tools mentioned:** RFD4-Proteina (Foundry), Protenix, Boltz, OpenFold3, Mol-1, ESMFold2, and the abguard CLI.

### 5b. Task Description (`docs/ai-antibodies-hackathon-apheris.pdf`, 9 pages)

- **Task:** improve an existing antibody (trastuzumab) with Apheris Foundry, Nebius and JapanFold, using multi-modal data.
- **Two modes:**
  - *Optimisation:* point mutations to trastuzumab to improve affinity and thermostability.
  - *De novo:* a new antibody that keeps the original epitope.
- **Judging (per design, against the trastuzumab baseline):**
  1. Affinity: comparable or better binding to HER2 by SPR.
  2. Epitope preservation: judged by competitive binding assay.
  3. Thermostability.
  - Tiers: S = 3 of 3, A = 2 of 3, B = 1 of 3, unsuccessful = 0 of 3.
- **Formats:** VHH, Fab or scFv.
- **Hard checks:** numbering confidence at least 0.1 (immunum), total length at most 250 aa, no unpaired cysteines, and identity to the nearest known antibody under 70%.
- **Supporting data:**
  - General VHH-antigen data: 454 true-negative pairs (21 with AF3 ipTM at or above 0.7), 2 non-cognate labels, 15 cognate affinities (sub-micromolar), and 1.8M predicted complexes (Smorodina et al.).
  - Trastuzumab: 524,346 CDRH3 variants vs HER2 by FACS (Chinery et al.), and about 700 optimisation designs, 190 with SPR affinity.
- **Compute:** one H100 GPU, 16 vCPUs, 200 GB RAM and 500 GB disk per team (Ubuntu 24.04). **Machines shut down at the end of Saturday 14 November. Copy anything you want to keep before then.**
- **Platforms:** Apheris Foundry, Nebius Tools (no-code, also usable as a Claude skill), JapanFold (RoseTTAFold3, OpenDDE, AF2-IG), and AMASS (literature and patent search, $100 credits per team, claimed by one person).

### 5c. RFD4-Proteina Workflow (from the task description)

- **Tasks in each Docker image:** `design`, `refold-prepare`, `refold-score`, `finetune`.
- **Weights:**

| Image | Use it for |
|---|---|
| `release-2026-10-19` | General proteins and miniproteins |
| `antibody-2026-10-30` | Design or redesign CDRs on a fixed framework. Use this to change CDRs other than CDRH3. |
| `her2-2026-11-07` | Redesign trastuzumab's CDRH3. Set `--sequence-tsr-k` to 2 (balanced) or 1 (exploratory). |
| `her2-novel-2026-11-09` | Mostly new CDRH3 loops with the most confident predicted fit to HER2 |

- **Novelty results on the CDRH3 task:**

| Weight and setting | Known binders | Pass novelty filter | Interface error (Å) |
|---|---|---|---|
| `antibody-2026-10-30` (not fine-tuned) | 0% | 100% | 8.2 |
| `her2-2026-11-07`, conservative | 21% | 0% | 9.4 |
| `her2-2026-11-07`, balanced | 21% | 6% | 9.1 |
| `her2-2026-11-07`, exploratory | 0.3% | 74% | 9.1 |
| `her2-novel-2026-11-09` | 4% | 86% | 6.8 |

- **Checking designs:** run `refold-prepare`, fold the inputs with any Predict Structure model, then run `refold-score`. For the HER2 exercise, rank on `min_ipae`, `iptm` and `binder_plddt`. Filter for novelty before ranking, because known binders fail the filter.

## 6. Tasks and Ideas

Goal: do interesting things with the data.

- [ ] Data analysis on the HER2 binding classes and SPR affinities
- [ ] Binding prediction
- [ ] Bring in other models that seem promising
- [ ] Design CDRH3s with RFD4-Proteina and pass the novelty filter against the 525,063 HER2 CDRH3s

## 7. Progress Log

| Date | Item | Status |
|---|---|---|
| 2026-11-14 | Hackathon info added to this folder | Done |
| 2026-11-14 | Two hackathon PDFs added to `docs/` | Done |
| 2026-11-14 | Setup and connections (AMASS, tool checklist) organised | Done |
| 2026-11-14 | Participant guide: fetch returned empty | Open |
| 2026-11-14 | Step 1 setup: connect Foundry, AMASS, JapanFold, Nebius, abguard | In progress |
| 2026-11-14 | Local foundry-assistant reviewed and documented (not yet started) | Done |
