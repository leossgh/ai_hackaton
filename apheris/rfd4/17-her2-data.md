---
type: Reference
title: HER2 hackathon data
description: What data is available for the Oslo HER2 hackathon, what each file contains, and where to download
  it. Trastuzumab FACS binding classes for 524,346 CDRH3 variants, SPR affinities for 768 designs, and public antibody-antigen
  structure predictions.
questions:
- What data is available for the HER2 hackathon?
- Where do I download the trastuzumab FACS and SPR data?
- What do the columns in the HER2 datasets mean?
- Can I train an affinity predictor on the hackathon data?
tags:
- rfd4-proteina
- foundry
status: draft
sources:
- resource: https://github.com/apheris/apheris-rfd4-proteina
  title: Foundry RFD4-Proteina module docs
---

# HER2 hackathon data

The data is in the hackathon bucket under `s3://apheris-oslo-hackathon/data/`, and the RFD4-Proteina
docs are under `s3://apheris-oslo-hackathon/rfd4-proteina/docs/`. Download all
of it (about 5 GB) with:

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
| `sigma2-ab-ag-champloo/` | Confidence scores (ipTM, pLDDT, PAE) for every sample of the same predictions | 1.8 GB |
| `zenodo-10831512-trastuzumab-ngs/` | Ready-made train, validation and test splits of the FACS data, plus earlier HER2 datasets | 2.5 GB |

## Trastuzumab and HER2

Trastuzumab is a clinical antibody that binds HER2, a receptor on some breast cancer cells. Both tables come
from [Chinery et al.](https://www.biorxiv.org/content/10.1101/2024.03.26.586756v2), who changed trastuzumab's
CDRH3 (the third loop of the heavy chain, its main contact with HER2) and measured how the variants bind. The
hackathon organisers at the University of Oslo prepared them as tables. Cite Chinery et al. when you use them.

These two tables are the "provided data" for the challenge filter: a design must differ from every CDRH3 in
both of them (525,063 unique sequences). See [HER2 models](12-her2.md).

### FACS binding classes

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

### SPR affinities

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

## Antibody-antigen structure predictions

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

### Confidence scores for every sample

The same study's raw confidence output for every predicted sample is in the
[NIRD research data archive](https://archive.sigma2.no/dataset/ab_ag_champloo)
([doi:10.11582/2026.owjnnp5q](https://doi.org/10.11582/2026.owjnnp5q)). Each pair was predicted 50 times.
Each JSON file is one sample's confidence output: ipTM, pTM, the ranking score, per-residue pLDDT and the
PAE matrix. Use it to compute your own interface scores from the PAE (the paper uses ipSAE), or to see how
much a model's confidence varies between samples of the same pair.

The bucket holds the smaller archives, 1.8 GB in all:

```bash
aws s3 sync s3://apheris-oslo-hackathon/data/sigma2-ab-ag-champloo/ hackathon-data/sigma2-ab-ag-champloo/
```

| File | Contents | Size |
| --- | --- | --- |
| `af3_real_per_replica_confidence_metrics.tar.zst` | AlphaFold3, real pairs (123 systems in the authors' README) | 1.3 GB |
| `chai1_all_per_replica_confidence_metrics.zip` | Chai-1, real and shuffled pairs | 0.5 GB |
| `README.txt` | The authors' description: folder layout, naming and citation | 5 KB |
| `table_of_contents_10.11582_2026.owjnnp5q.csv` | Every file in the archive, with its size and MD5 | 2 KB |

Two archives are too large for the bucket. Download them from the archive only if you need them:

| File | Contents | Size |
| --- | --- | --- |
| [`af3_shuffled_per_replica_confidence_metrics.tar.zst`](https://data.archive.sigma2.no/dataset/9f1b7a69-e062-4c21-a490-8d42bb826212/download/af3_shuffled_per_replica_confidence_metrics.tar.zst) | AlphaFold3, shuffled pairs | 163 GB |
| [`boltz2_all_per_replica_confidence_metrics.zip`](https://data.archive.sigma2.no/dataset/9f1b7a69-e062-4c21-a490-8d42bb826212/download/boltz2_all_per_replica_confidence_metrics.zip) | Boltz-2, all pairs | 1.7 TB, more than your VM's disk |

Unpack the AlphaFold3 archives with `zstd` (`sudo apt install zstd` if it is missing):

```bash
tar --use-compress-program=unzstd -xf af3_real_per_replica_confidence_metrics.tar.zst
```

Inside, `confidences/real/` holds the real pairs and `confidences/dreamy/` the shuffled ones ("dreamy" is
the study's name for shuffled pairs). Each pair is a folder `system_<nanobody index>_<antigen index>_<nanobody PDB>_<antigen PDB>`,
for example `system_53_13_7xtp_5mje`, holding `seed-1_sample-0.json` to `seed-1_sample-49.json`.

The AlphaFold3 files fall under the [AlphaFold 3 output terms](https://github.com/google-deepmind/alphafold3/blob/main/OUTPUT_TERMS_OF_USE.md):
non-commercial research only. Cite [Smorodina et al.](https://doi.org/10.64898/2026.03.02.709004) and
[AlphaFold3](https://doi.org/10.1038/s41586-024-07487-w) when you use them.

## Ready-made training splits

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
