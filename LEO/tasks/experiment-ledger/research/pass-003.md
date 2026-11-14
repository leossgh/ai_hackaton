# Research pass 003 — 2026-11-14

- **scope:** `TH-009` (explicit scope TH-009)
- **targets:** TH-009
- **searches:** 0 cache hits, 3 new, 0 failed, 0 deferred
- **cost this pass:** $0.15
- **cumulative:** 5 searches, $0.25, 0% of the 2000-search team budget

## Candidate evidence

Term-overlap matches that carry a measured number. These are *candidates*: the agent applying this pass judges them, and only quotes that name an assay become evidence.

### TH-009 — The <70% CDRH3 identity gate cannot be met without mutating at least one HER2-contacting position, and the cheapest one to sacrifice is Y109

- **42968171** (2026, 0 cites, 6 keyword hits: alanine, antigen, crystal, paratope, position, scan) — Affinity-tuned anti-idiotypic masking enables protease-activatable HER2-targeting antibodies with an optimized masked-unmasked dynamic range
  - > BLI analysis further showed detectable HER2 binding of MMP-9-treated dAb(W104F)-MMP-9-4D5scFv, with an apparent KD of 10.0 nM, whereas dAb(WT)-MMP-9-4D5scFv and uncleaved dAb(W104F)-MMP-9-4D5scFv showed no detectable binding under the same assay conditions.
- **20403153** (2010, 23 cites, 5 keyword hits: antigen, crystal, packing, position, structures) — The kinetics of antibody binding to Plasmodium falciparum VAR2CSA PfEMP1 antigen and modelling of PfEMP1 antigen packing on the membrane knobs
  - > CONCLUSIONS: High avidity is required to achieve the strongest binding to VAR2CSA PfEMP1, but the structures that display PfEMP1 also tend to inhibit cross-linking between PfEMP1 antigens, by holding many binding epitopes at distances beyond the 15-18 nm sweep radius of an antibody.
- **19324053** (2009, 43 cites, 4 keyword hits: antigen, crystal, packing, structures) — Energy-based analysis and prediction of the orientation between light- and heavy-chain antibody variable domains
  - > When applied to antibody homology models generated from templates with 55-75% sequence identity, we predict the V(L):V(H) orientation of 20 antibodies with an average/median RMSD of 2.1/1.6 A to the crystal structures.
- **29702641** (2018, 230 cites, 3 keyword hits: antigen, contact, structures) — RosettaAntibodyDesign (RAbD): A general framework for computational antibody design
  - > We tested RAbD experimentally on both a lambda and kappa antibody-antigen complex, successfully improving their affinities 10 to 50 fold by replacing individual CDRs of the native antibody with new CDR lengths and clusters.
- **19062174** (2009, 188 cites, 3 keyword hits: antigen, crystal, structures) — Toward high-resolution homology modeling of antibody Fv regions and application to antibody-antigen docking
  - > The median root mean square deviation (rmsd) of the antigen binding pocket comprised of all the CDR residues was 1.5 A with 80% of the targets having an rmsd lower than 2.0 A.
  - > The median backbone heavy atom global rmsd of the CDR H3 loop prediction was 1.6, 1.9, 2.4, 3.1, and 6.0 A for very short (4-6 residues), short (7-9), medium (10-11), long (12-14) and very long (17-22) loops, respectively.
- **23255066** (2013, 34 cites, 3 keyword hits: antigen, crystal, structures) — Ab initio structure prediction of the antibody hypervariable H3 loop
  - > When the prediction is performed in the crystal environment and including symmetry mates, the median backbone root mean square deviation (RMSD) is 0.5 Å to the crystal structure, with 91% of cases having an RMSD of less than 2.0 Å.
  - > When the prediction is performed in a noncrystallographic environment, where the scaffold is constructed by swapping the H3 loops between homologous antibodies, 70% of cases have an RMSD below 2.0 Å.

## Proposed updates

The agent driving this pass fills this in and applies it, then records the move in each theory's history with this pass id.

| Target | Proposed change | Justified by |
|---|---|---|
| TH-009 | **no confidence change.** History line recording that the search found nothing on Y109 energetics | Nothing in 3 searches + full cache addresses the energetic contribution of trastuzumab CDRH3 Tyr109, or of any specific trastuzumab paratope residue |
| IDEA-010 | priority `medium` → `high` | Literature cannot settle Y109. If we want the answer we must compute it, and it is the one assumption IDEA-008 rests on |
| TH-001 | confidence `medium` → `high`; add PMID:29702641 | RosettaAntibodyDesign replaced individual CDRs with new lengths and clusters and improved affinity **10–50 fold, experimentally verified** on two antibody-antigen complexes. Independent of PMID:8918938 (1230-fold on anti-c-erbB-2, i.e. HER2), so two primary results now support wholesale CDR change as an affinity route |
| TH-011 | **new**, confidence `medium` | PMID:19062174: median backbone RMSD for H3 loop prediction is **2.4 Å for 10–11 residue loops** — our CDRH3 is 11. PMID:23255066: ab initio H3 prediction reaches 0.5 Å median *in the crystal environment* but only 70% under 2.0 Å without it |

**Applied** 2026-11-14 by Claude Opus 5.

**Discarded, with reasons** — all four matched on keywords and carried numbers,
which is exactly the noise this step exists to filter:

- **PMID:42968171** — the `dAb(W104F)` mutation with apparent KD 10.0 nM is in the anti-idiotypic *masking* domain antibody, not in trastuzumab. The paper does use 4D5scFv (trastuzumab), so it may be worth revisiting for the "path to value" framing (protease-activatable HER2 targeting), but it says nothing about trastuzumab paratope energetics.
- **PMID:20403153** — *Plasmodium falciparum* VAR2CSA. Wrong antigen, and the measurement is avidity and epitope spacing, not per-residue contribution.
- **PMID:19324053** — VL:VH orientation prediction. Relevant to modelling accuracy generally, not to which CDRH3 position is load-bearing.
- **PMID:29702641 (partly)** — kept as evidence for TH-001, but its CDR-cluster grafting result says nothing about Y109 specifically.

