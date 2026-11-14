# Research pass 005 — 2026-11-14

- **scope:** `TH-013` (explicit scope TH-013)
- **targets:** TH-013
- **searches:** 0 cache hits, 3 new, 0 failed, 0 deferred
- **cost this pass:** $0.15
- **cumulative:** 11 searches, $0.55, 0% of the 2000-search team budget

## Candidate evidence

Term-overlap matches that carry a measured number. These are *candidates*: the agent applying this pass judges them, and only quotes that name an assay become evidence.

### TH-013 — Structure-based interface scores cannot rank HER2 CDRH3 designs, and the topmodel score is actively misleading

- **37880344** (2023, 34 cites, 6 keyword hits: alphafold, binder, complex, interface, rate, score) — Peptide binder design with inverse folding and protein structure prediction
  - > Successful binders (predicted interface RMSD ≤ 2 Å) are designed towards 185 (6.5%) heteromeric and 42 (3.6%) homomeric protein interfaces with ESM-IF1 compared with 18 (1.5%) using ProteinMPNN from 100 samples.
- **42906387** (2026, 0 cites, 6 keyword hits: alphafold, benchmark, complex, rate, screening, validation) — AlphaFold-driven structure-based drug discovery: Capabilities, benchmarks and limitations for medicinal chemistry
  - > Even though AlphaFold has substantially advanced the field for example, in a prospective screen against the G protein-coupled receptor (GPCR) TAAR1, docking to AlphaFold2 models gave a 60% hit rate versus 22% for a homology model and a workflow combining an AlphaFold model with generative chemistry against the kinase CDK20 yielded a compound with an IC50 of 33.4 nM and an approximately eightfold antiproliferative selectivity window between cell lines-problems related to protein flexibility, conformational changes of proteins due to ligands, binding affinity prediction and biological complexity cannot be neglected and predicted structures still require experimental validation before guiding synthesis.
- **29702641** (2018, 230 cites, 5 keyword hits: benchmark, complex, decoy, interface, rate) — RosettaAntibodyDesign (RAbD): A general framework for computational antibody design
  - > We tested RAbD experimentally on both a lambda and kappa antibody-antigen complex, successfully improving their affinities 10 to 50 fold by replacing individual CDRs of the native antibody with new CDR lengths and clusters.
- **37650367** (2023, 66 cites, 5 keyword hits: alphafold, complex, interface, rate, score) — Integrating deep learning, threading alignments, and a multi-MSA strategy for high-quality protein monomer and complex structure prediction in CASP15
  - > For 47 free modeling targets in CASP15, the final models predicted by D-I-TASSER showed average TM-score 19% higher than the standard AlphaFold2 program.
  - > For the 38 complex targets, DMFold-Multimer generated models with an average TM-score of 0.83 and Interface Contact Score of 0.60, both significantly higher than those of competing complex prediction tools.
- **40814020** (2025, 42 cites, 5 keyword hits: alphafold, complex, iptm, rate, screening) — What does AlphaFold3 learn about antibody and nanobody docking, and what remains unsolved?
  - > With twenty seeds, AF3 achieves a median unbound CDR H3 RMSD accuracy of 2.9 Å ... and 2.2 Å ... for antibodies and nanobodies, respectively.
- **37248282** (2023, 307 cites, 4 keyword hits: alphafold, benchmark, error, rate) — ImmuneBuilder: Deep-Learning models for predicting the structures of immune proteins
  - > For example, on a benchmark of 34 recently solved antibodies, ABodyBuilder2 predicts CDR-H3 loops with an RMSD of 2.81Å, a 0.09Å improvement over AlphaFold-Multimer, while being over a hundred times faster.
  - > Similar results are also achieved for nanobodies, (NanoBodyBuilder2 predicts CDR-H3 loops with an average RMSD of 2.89Å, a 0.55Å improvement over AlphaFold2) and TCRs.

## Proposed updates

The agent driving this pass fills this in and applies it, then records the move in each theory's history with this pass id.

| Target | Proposed change | Justified by |
|---|---|---|
| TH-013 | **no confidence change.** History line recording that no published validation of ipTM/ipAE as a *binder screen* turned up | Three targeted searches returned loop-accuracy benchmarks, a CASP complex-prediction paper and a small-molecule docking review — nothing measuring whether interface confidence scores separate binders from non-binders. Our own EXP-003 decoy control is currently the best evidence we have on this question, which raises rather than lowers the value of IDEA-012 |
| IDEA-013 | **new**, priority `medium` | PMID:37880344 — ESM-IF1 produced successful binder designs (predicted interface RMSD ≤2 Å) toward **185 of ~2,850 heteromeric interfaces (6.5%)** against **18 (1.5%)** for ProteinMPNN from 100 samples, a ~4× difference at the inverse-folding step we currently plan to run with ProteinMPNN |
| de novo ranking gap | recorded in `literature/REVIEW.md` as an open gap, not a theory | TH-014's sequence ranker is label-dependent and the optimisation track is the only place labels exist. Nothing in this pass offers a ranking method for de novo designs |

**Applied** 2026-11-14 by Claude Opus 5.

**Discarded, with reasons:**

- **PMID:42906387** — AlphaFold-driven drug discovery review. Its 60%-vs-22% hit rate is **small-molecule docking** against a GPCR, and the CDK20 result is a compound IC50. Wrong modality: ligand docking to a predicted pocket says nothing about protein–protein interface confidence scores.
- **PMID:37650367** — CASP15 general-complex TM-score. Already discarded for the same reason in pass-004; re-matched on keywords, still the wrong measurement.
- **PMID:29702641, PMID:40814020, PMID:37248282** — already carried by TH-001, TH-011 and TH-012. Re-matched, no new information.
- **PMID:37880344 (partly)** — kept for IDEA-013, but note its "successful" means **predicted** interface RMSD ≤2 Å, not measured binding. It is not evidence that structure scores rank binders; if anything it is another case of a predicted metric standing in for an unmeasured one.

