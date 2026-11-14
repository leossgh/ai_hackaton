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

## 4. Tasks and Ideas

Goal: do interesting things with the data.

- [ ] Data analysis on the HER2 binding classes and SPR affinities
- [ ] Binding prediction
- [ ] Bring in other models that seem promising
- [ ] Design CDRH3s with RFD4-Proteina and pass the novelty filter against the 525,063 HER2 CDRH3s

## 5. Progress Log

| Date | Item | Status |
|---|---|---|
| 2026-11-14 | Hackathon info added to this folder | Done |
