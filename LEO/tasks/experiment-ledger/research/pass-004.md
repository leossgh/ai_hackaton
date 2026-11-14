# Research pass 004 — 2026-11-14

- **scope:** `TH-011` (explicit scope TH-011)
- **targets:** TH-011
- **searches:** 0 cache hits, 3 new, 0 failed, 0 deferred
- **cost this pass:** $0.15
- **cumulative:** 8 searches, $0.40, 0% of the 2000-search team budget

## Candidate evidence

Term-overlap matches that carry a measured number. These are *candidates*: the agent applying this pass judges them, and only quotes that name an assay become evidence.

### TH-011 — Refold scores cannot separate close CDRH3 designs, because predicted conformation for an 11-residue H3 loop is only accurate to roughly 2 A

- **40814020** (2025, 42 cites, 8 keyword hits: accuracy, alphafold, antigen, boltz, loop, model, rmsd, seed) — What does AlphaFold3 learn about antibody and nanobody docking, and what remains unsolved?
  - > With twenty seeds, AF3 achieves a median unbound CDR H3 RMSD accuracy of 2.9 Å ... and 2.2 Å ... for antibodies and nanobodies, respectively.
- **37248282** (2023, 307 cites, 7 keyword hits: accuracy, alphafold, antigen, benchmark, loop, model, rmsd) — ImmuneBuilder: Deep-Learning models for predicting the structures of immune proteins
  - > For example, on a benchmark of 34 recently solved antibodies, ABodyBuilder2 predicts CDR-H3 loops with an RMSD of 2.81Å, a 0.09Å improvement over AlphaFold-Multimer, while being over a hundred times faster.
  - > Similar results are also achieved for nanobodies, (NanoBodyBuilder2 predicts CDR-H3 loops with an average RMSD of 2.89Å, a 0.55Å improvement over AlphaFold2) and TCRs.
- **19062174** (2009, 188 cites, 7 keyword hits: accuracy, antigen, benchmark, conformation, loop, model, rmsd) — Toward high-resolution homology modeling of antibody Fv regions and application to antibody-antigen docking
  - > The median root mean square deviation (rmsd) of the antigen binding pocket comprised of all the CDR residues was 1.5 A with 80% of the targets having an rmsd lower than 2.0 A.
  - > The median backbone heavy atom global rmsd of the CDR H3 loop prediction was 1.6, 1.9, 2.4, 3.1, and 6.0 A for very short (4-6 residues), short (7-9), medium (10-11), long (12-14) and very long (17-22) loops, respectively.
- **35099535** (2022, 156 cites, 7 keyword hits: accuracy, antigen, benchmark, confidence, loop, model, rmsd) — ABlooper: fast accurate antibody CDR loop structure prediction with accuracy estimation
  - > On the models of the Rosetta Antibody Benchmark, ABlooper makes predictions with an average CDR-H3 RMSD of 2.49 Å, which drops to 2.05 Å when considering only its 75% most confident predictions.
- **29702641** (2018, 230 cites, 6 keyword hits: antigen, benchmark, conformation, interface, loop, model) — RosettaAntibodyDesign (RAbD): A general framework for computational antibody design
  - > We tested RAbD experimentally on both a lambda and kappa antibody-antigen complex, successfully improving their affinities 10 to 50 fold by replacing individual CDRs of the native antibody with new CDR lengths and clusters.
- **37650367** (2023, 66 cites, 6 keyword hits: accuracy, alphafold, folding, interface, model, score) — Integrating deep learning, threading alignments, and a multi-MSA strategy for high-quality protein monomer and complex structure prediction in CASP15
  - > For 47 free modeling targets in CASP15, the final models predicted by D-I-TASSER showed average TM-score 19% higher than the standard AlphaFold2 program.
  - > For the 38 complex targets, DMFold-Multimer generated models with an average TM-score of 0.83 and Interface Contact Score of 0.60, both significantly higher than those of competing complex prediction tools.

## Proposed updates

The agent driving this pass fills this in and applies it, then records the move in each theory's history with this pass id.

| Target | Proposed change | Justified by |
|---|---|---|
| TH-011 | confidence `medium` → **`high`**; the "older methods than our stack" caveat is removed | PMID:40814020 — **AlphaFold3**, a modern co-folding model of the same class as Boltz-2, achieves median unbound CDR-H3 RMSD **2.9 Å with twenty seeds**. Corroborated by PMID:37248282 (ABodyBuilder2 2.81 Å on 34 recent antibodies, 0.09 Å better than AlphaFold-Multimer) and PMID:35099535 (ABlooper 2.49 Å) |
| TH-011 | `evidence_against` rewritten | PMID:35099535 — ABlooper's RMSD drops 2.49 → **2.05 Å on its 75% most confident predictions**, so a model's own confidence does carry signal. Confidence-based *filtering* is defensible even where fine *ranking* is not |
| IDEA-006 | rescoped from "add a second seed" to **multi-seed with reported spread**; stays `high` | PMID:40814020 used **20** seeds to reach its median. EXP-001 used 1. Two seeds would still not establish an error bar |
| TH-012 | **new**, confidence `medium` | Two independent legs now favour a VHH over an scFv: Tm is predictable for sdAbs only (PMID:39154093, MAE 4.03 °C) and CDR-H3 structure prediction is **more accurate for nanobodies — 2.2 Å vs 2.9 Å** (PMID:40814020) |
| IDEA-005 | priority `medium` → `high` | Same. The VHH hedge is now supported by tooling accuracy, not just by the existence proof in PMID:37632647 |

**Applied** 2026-11-14 by Claude Opus 5.

**Discarded, with reasons:**

- **PMID:37650367** — CASP15 D-I-TASSER / DMFold-Multimer. Reports TM-score 0.83 and Interface Contact Score 0.60 on general protein complexes, not antibody CDR-H3 accuracy. Wrong measurement for this theory, and general-complex TM-score says nothing about an 11-residue loop.
- **PMID:29702641** — already carried by TH-001; its CDR-cluster grafting result is about affinity gain, not prediction accuracy.
- **PMID:19062174** — already carried by TH-011 from pass-003; re-matched, no new information.

