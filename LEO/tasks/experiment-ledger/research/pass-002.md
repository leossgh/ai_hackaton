# Research pass 002 — 2026-11-14

- **scope:** `TH-007` (explicit scope TH-007)
- **targets:** TH-007
- **searches:** 2 cache hits, 0 new, 0 failed, 1 deferred
- **cost this pass:** $0.00
- **cumulative:** 2 searches, $0.10, 0% of the 2000-search team budget

## Deferred to a later pass (hit `--max-new`)

- [TH-007] `biomedcore` TEMPRO nanobody Tm protein embedding prediction

## Candidate evidence

Term-overlap matches that carry a measured number. These are *candidates*: the agent applying this pass judges them, and only quotes that name an assay become evidence.

### TH-007 — scFv thermostability is predictable from sequence well enough to rank our designs, which closes the open "no thermostability predictor" decision

- **41564239** (2026, 0 cites, 8 keyword hits: accuracy, embedding, learning, machine, melting, nanobody, temperature, thermostability) — Thermostability Prediction Powered by Synergistic Deep Learning at Experimental and Theoretical Levels for Nanobodies
  - > Benefiting from the two synergistic models, a more reliable screening criterion (Tm > 65 °C and Qclass IV) is proposed for determining highly thermostable nanobodies.
- **36683173** (2023, 46 cites, 6 keyword hits: learning, machine, melting, scfv, temperature, thermostability) — Toward generalizable prediction of antibody thermostability using machine learning on sequence and structure features
  - > Both of these models are trained over temperature-specific data (TS50 measurements) derived from multiple libraries of scFv sequences.
  - > Further, we demonstrate that for an independent mAb with available thermal melting temperatures for 20 experimentally characterized thermostable mutations, these models trained on TS50 data could identify 18 residue positions and 5 identical amino-acid mutations showing remarkable generalizability.
- **39154093** (2024, 15 cites, 6 keyword hits: embedding, melting, nanobody, temperature, tempro, thermostability) — TEMPRO: nanobody melting temperature estimation model using protein embeddings
  - > Our results indicate the efficacy of protein embeddings in reliably predicting the Tm of sdAbs with mean absolute error (MAE) of 4.03 °C and root mean squared error (RMSE) of 5.66 °C, thus offering a valuable tool for the optimization of nanobodies for various biomedical and therapeutic applications.
- **40079266** (2025, 19 cites, 5 keyword hits: accuracy, learning, melting, predictor, temperature) — Seq2Topt: a sequence-based deep learning predictor of enzyme optimal temperature
  - > In comparison with existing models, a new model developed in this study, Seq2Topt, reached a superior accuracy on ${T}_{opt}$ prediction just using protein sequences (RMSE = 12.26°C and R2 = 0.57), and could capture key protein regions for enzyme ${T}_{opt}$ with multi-head attention on residues.
  - > Additionally, accurate deep learning predictors of enzyme optimal pH (Seq2pHopt, RMSE = 0.88 and R2 = 0.42) and melting temperature (Seq2Tm, RMSE = 7.57 °C and R2 = 0.64) were developed based on the model architecture of Seq2Topt, suggesting that the development of Seq2Topt could potentially give rise to a useful prediction platform of enzymes.
- **35361835** (2022, 14 cites, 5 keyword hits: accuracy, learning, machine, scfv, temperature) — Machine learning modeling for solubility prediction of recombinant antibody fragment in four different E. coli strains
  - > The concentration of soluble scFv reached 112.4 mg/L at the optimum condition and strain (induction at cell density 0.6 with 0.4 mM IPTG for 24 h at 23 °C in Origami).
- **35509940** (2022, 4 cites, 5 keyword hits: accuracy, machine, melting, temperature, validation) — A low-cost 3D-printable differential scanning fluorometer for protein and RNA melting experiments
  - > Airflow heating and inline temperature control by thermistors enabled high-accuracy temperature management in PCR tubes (±0.1 °C) allowing us to perform high-resolution thermal shift assays (TSA) from exemplary biological applications.

## Proposed updates

The agent driving this pass fills this in and applies it, then records the move in each theory's history with this pass id.

| Target | Proposed change | Justified by |
|---|---|---|
| TH-007 | confidence `low` → `medium`; add the format-dependence caveat to `evidence_against` | PMID:39154093 gives MAE 4.03 °C on Tm itself; PMID:36683173 recovered 18/20 known thermostable positions on a held-out mAb; but PMID:39154093 and PMID:41564239 are sdAb-only |
| IDEA-003 | status `open` → `lit-checked`; split the recommendation by format | Same records. VHH → TEMPRO + the `Tm > 65 °C` criterion; scFv → TS50-trained models only, declare as a weakness |
| `literature/REVIEW.md` §3 | rewrite: a predictor now exists for sdAbs with a stated error bar; the gap is scFv-specific | PMID:41564239 was not in the 30 seeded queries — this pass found it |

**Applied** 2026-11-14 by Claude Opus 5. Not relevant: PMID:40079266 (enzyme
optimal temperature, not antibodies), PMID:35361835 (solubility, not Tm),
PMID:35509940 (a DSF instrument, not a predictor). All three matched on
keywords and carried numbers, which is exactly the noise the agent filters.

