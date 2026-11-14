# README_APHERIS: tools, data and how agents use them

Oslo AI x Antibodies hackathon (14 Nov 2026). Goal: design HER2 antibodies that beat trastuzumab
using Apheris Foundry (RFD4-Proteina) and other tools. **The VM shuts down at the end of Saturday.
Copy anything you want to keep off it before then.**

## 1. What is on this VM

| Thing | Where | Notes |
| --- | --- | --- |
| H100 80GB GPU | `nvidia-smi` | One GPU, shared by the whole team. Run one heavy job at a time |
| Foundry docs | `~/hackathon-team-3/apheris/rfd4/` | Start with `18-vm.md`, then `Tutorial.html`. `index.md` lists every page |
| Hackathon data (4.7 GB) | `~/hackathon-team-3/apheris/hackathon-data/` | Synced from `s3://apheris-oslo-hackathon/data/`. Do not commit it |
| Foundry GUI | not available | The VM has no Foundry Hub, so no web UI. Use the Docker commands below (every UI setting is a flag) |
| Foundry models | Docker images `quay.io/apheris/oslo-hackathon:*` | Already pulled, no Hub or login needed |
| Team repo | `~/hackathon-team-3/` | `AGENTS.md` (rules), `LEO/README.md` (notes and progress log) |
| Offline docs assistant | `~/hackathon-team-3/apheris/foundry-assistant/` | Small local Q&A over the Foundry docs. `make ask Q="..."` (needs llama.cpp, see its README) |
| `foundry-toolkit` CLI | `/usr/local/bin/foundry-toolkit` | `module list`, `module describe`. It is not the Hub CLI (`apheris-foundry`), which does not work here |
| AWS CLI | `aws s3 ...` | Access to `s3://apheris-oslo-hackathon/` works |
| RCSB PDB MCP tools | Claude Code MCP (`mcp__rcsb-mcp__*`) | Search and fetch PDB structures, sequences, UniProt (e.g. HER2, trastuzumab 1N8Z) |
| Challenge PDFs | `~/hackathon-team-3/apheris/challenge/2026-11_Oslo_hackathon_Apheris_challenge.pdf`, `~/hackathon-team-3/apheris/challenge/ai-antibodies-hackathon-apheris.pdf` | Task description and deck |

**`abguard`:** found in the uv cache (`~/.cache/uv/archive-v0/juqsJzrEaedzWbtr/bin/abguard`), not on PATH. See `../AGENTS.md`. Every design must pass it
before submission.

## 2. The data (`~/hackathon-team-3/apheris/hackathon-data/`)

Full column docs: `~/hackathon-team-3/apheris/hackathon-data/README.md` and `~/hackathon-team-3/apheris/rfd4/17-her2-data.md`.

| Folder | Contents |
| --- | --- |
| `her2-trastuzumab/` | `tz_her2_facs_3classes_524346.csv.zip` (524k CDRH3s, binding class high/medium/low) and `trastuzumab_her2_spr_all_768.csv` (768 variants, 190 with KD in nM) |
| `zenodo-10831512-trastuzumab-ngs/data.zip` | Ready train/val/test splits of the FACS data and earlier HER2 sets (4 GB unzipped) |
| `zenodo-18390239-ab-ag-complexes/` | ipTM matrices, structure accuracy, replica RMSD for 1.8M predicted nanobody-antigen complexes |
| `sigma2-ab-ag-champloo/` | Per-sample ipTM, pLDDT, PAE for the same predictions (AF3 real pairs, Chai-1), plus `spr-supplementary/` measured SPR |

The two HER2 tables are the **novelty filter**: a design's CDRH3 must differ from all 525,063
CDRH3s in them. Always check against the full set.

Untrusted-download hygiene: unzip each archive into its own new directory and read it with
`python3 -I`.

## 3. Running the models

Run everything from `~/hackathon-team-3/apheris/rfd4` (it holds `Data/` and `Settings/`).

```bash
cd ~/hackathon-team-3/apheris/rfd4
Q=quay.io/apheris/oslo-hackathon
RUN="docker run --rm --gpus all --shm-size 16g --user $(id -u):$(id -g) -e HOME=/tmp -v /etc/passwd:/etc/passwd:ro -v $PWD:/work -w /work"
```

### Design models (`apheris-rfd4-proteina-v0.3.0-<weight>`)

| Weight | Use |
| --- | --- |
| `her2-novel-2026-11-09` | Mostly new CDRH3 loops with a confident fit to HER2 (best novelty pass rate) |
| `her2-2026-11-07` | Redesign trastuzumab CDRH3. Add `--sequence-tsr-k 2` (balanced) or `1` (exploratory) |
| `antibody-2026-10-30` | VHH, Fv, or any CDR on a fixed framework (also the track for non-CDRH3 changes) |
| `release-2026-10-19` | General: miniproteins, monomers, enzymes, ligand and DNA binders. Weights must first be copied out of an older image, see `~/hackathon-team-3/apheris/rfd4/18-vm.md` "General model" |

Tasks of each image: `design`, `refold-prepare`, `refold-score`, `metrics`, `finetune`.

```bash
# 100 CDRH3 designs against HER2 (~30 s each)
$RUN $Q:apheris-rfd4-proteina-v0.3.0-her2-novel-2026-11-09 module-run design \
  --input Data/12-her2/her2_cdrh3.yaml --output runs/her2/design \
  --num-replicates 100 --seed 1 --recycle-strategy high/front_loaded
```

Pass the **spec file** (`.yaml`/`.json`) as `--input`, not its folder. PDB files are rejected; use CIF/BCIF.
Outputs: `runs/<name>/design/generation/inference_samples/*/*_generated.cif` and
`.../inference_metrics/per_example_metrics.csv`.

Other inputs: `Data/03-vhh/` (VHH), `Data/03-fv/design.json` (paired VH/VL) with the antibody image.
Refine a design: `--input <design.cif> --partial-trajectory-fraction 0.4`. Keep a backbone, new
sequences: `--inverse-folding true`.

### Folding models for refolding (check designs)

Boltz-2 (`apheris-boltz-v1.3.0-boltz2`), OpenFold3 (`apheris-openfold3-v1.3.0-of3ob`, `-of3p2`),
Protenix (`apheris-protenix-v1.3.0-v2`, `-v1-default`), Mol-1 (`apheris-mol1-v1.3.0-base`),
Boltz-1, ESMFold2 (`apheris-esmfold2-v1.4.0-release`). Template-capable models see the known HER2 structure.

Three steps: `refold-prepare` (pick top N) -> run a folding model -> `refold-score`. Full commands
are in `~/hackathon-team-3/apheris/rfd4/18-vm.md`. Quick end-to-end test with 4 designs:

```bash
cd ~/hackathon-team-3/apheris/rfd4 && bash Scripts/run-her2.sh all      # N=, TOPN=, OUT=, IMG= env vars override defaults
```

For HER2 the `pass` column stays empty by design. Rank on `min_ipae` (lower is better), `iptm`,
`binder_plddt`, and compare scores only within one folding model.

## 4. How agents (Claude Code, Codex, Copilot) interact with the tools

Everything is a shell command or file, so any agent with Bash can drive it. There is no daemon or API.

1. **Read first:** `~/hackathon-team-3/AGENTS.md`, then `LEO/README.md`, then `~/hackathon-team-3/apheris/rfd4/18-vm.md`.
2. **Docs lookup:** grep `~/hackathon-team-3/apheris/rfd4/*.md` (`index.md` lists pages with questions each answers), or
   `cd ~/hackathon-team-3/apheris/foundry-assistant && make ask Q="..."` for the local assistant.
3. **Data analysis / ML:** use Python (`pixi` is installed under `~/.pixi`, `uv` is available). Work in
   your own dir, e.g. `~/hackathon-team-3/<YOURNAME>/`. Keep scratch output out of shared folders.
4. **Running models:** `docker run` with `$RUN` above. Write outputs under `runs/<descriptive-name>/`.
   Run long jobs in the background and poll the log. Only one GPU, so queue jobs rather than overlap them.
5. **Structures and literature:** RCSB MCP tools for PDB entries, sequences and annotations. AMASS
   (literature, patents) is read from `AMASS_API_KEY` in the environment; never write the key to disk or git.
6. **Record every run** (rules from `AGENTS.md`): inputs, weight image, flags, seed, scores, in the
   owner's folder.
7. **Keep tracks separate:** Optimisation (mutate trastuzumab, CDRH3 identity to trastuzumab < 70%,
   at least 2 mutations from every sequence in the data) and De novo (VHH/scFv/Fab, < 70% identity to any
   known antibody) use separate folders.

### Hard constraints on any design

- CDRH3 differs from all 525,063 CDRH3s in the provided HER2 tables.
- Format VHH, scFv or Fab, no unpaired cysteines, total length <= 250 aa, immunum numbering confidence >= 0.1.
- Passes `abguard` (see Open items).

Do not commit or push unless asked. Do not commit secrets, `hackathon-data/`, or `.venv/`.

## 5. Suggested workflow

1. Smoke test: `bash Scripts/run-her2.sh all`.
2. Analyse FACS and SPR data (class balance, position-wise residue preferences, edit-distance effects).
3. Train a binder classifier / affinity regressor on the clonotype splits (and the 190 SPR KDs).
4. Generate many designs with `her2-novel` (and `her2` for a balanced mix).
5. Novelty-filter against all 525,063 CDRH3s, then refold with 2+ folding models and rank on
   `min_ipae`, `iptm`, `binder_plddt`, plus your classifier score.
6. Check the folding-model trust caveat using the champloo data (ipTM often does not separate real from shuffled pairs).
7. `abguard` the shortlist and write it up.

## 6. Open items

- `abguard` runs from the uv cache; consider putting it on PATH.
- Smoke test (`run-her2.sh all`) was started at setup; check `runs/her2/scored-boltz2/refold_metrics.csv`.
- `release-2026-10-19` weights have not been extracted yet.
- Local docs assistant needs llama.cpp and two GGUFs in `~/hackathon-team-3/apheris/foundry-assistant/models/` (not verified).
