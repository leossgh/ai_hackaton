# Research pass 006 — 2026-11-14

- **scope:** `auto` (auto: low/untested theories first (7), then unbacked ideas (1))
- **targets:** TH-002, TH-003, TH-004, IDEA-007
- **searches:** 0 cache hits, 3 new, 7 failed, 2 deferred
- **cost this pass:** $0.15
- **cumulative:** 14 searches, $0.70, 0% of the 2000-search team budget

## Failed searches

- `biomedcore` arginine CDR mutation polyspecificity nonspecific binding antibody — HTTP 403
- `biomedcore` charged residue CDR affinity specificity trade-off — HTTP 403
- `biomedcore` antibody net charge nonspecificity developability — HTTP 403
- `biomedcore` CDRH3 loop flexibility rigidity affinity maturation repertoire — HTTP 403
- `biomedcore` antibody paratope conformational entropy binding — HTTP 403
- `biomedcore` B-factor rigidity antibody affinity prediction — HTTP 403
- `patentcore` anti-HER2 antibody CDR sequence claim variant — HTTP 403

## Deferred to a later pass (hit `--max-new`)

- [IDEA-007] `patentcore` trastuzumab biosimilar CDRH3 sequence claim
- [IDEA-007] `patentcore` computationally designed antibody CDR freedom to operate

## Candidate evidence

Term-overlap matches that carry a measured number. These are *candidates*: the agent applying this pass judges them, and only quotes that name an assay become evidence.

### TH-002 — Affinity gains bought in CDRH3 cost thermostability, so the two prize properties are in direct tension and must be co-optimised, not optimised in sequence

- **AMBC_JwGSFsFYuumYi1zgXk0571g2F5A** (2026, 0 cites, 8 keyword hits: affinity, engineering, melting, mutation, optimization, scfv, stability, temperature) — An innovative AI-based platform for antibody stability improvement and affinity optimization.
  - > This approach effectively find a new mutant reduced aggregation under one-week accelerated thermal stress from 100% to less than 5%, while increasing the melting temperature (Tm) by up to ∼10 °C.
- **36683173** (2023, 46 cites, 7 keyword hits: affinity, engineering, melting, mutation, scfv, stability, temperature) — Toward generalizable prediction of antibody thermostability using machine learning on sequence and structure features
  - > Both of these models are trained over temperature-specific data (TS50 measurements) derived from multiple libraries of scFv sequences.
  - > Further, we demonstrate that for an independent mAb with available thermal melting temperatures for 20 experimentally characterized thermostable mutations, these models trained on TS50 data could identify 18 residue positions and 5 identical amino-acid mutations showing remarkable generalizability.
- **23995618** (2013, 34 cites, 6 keyword hits: affinity, engineering, mutation, optimization, scfv, stability) — CDR-restricted engineering of native human scFvs creates highly stable and soluble bifunctional antibodies for subcutaneous delivery
  - > Our final candidate could be formulated in a standard biopharmaceutical platform buffer at 100 mg/ml with<2% high molecular weight species present after 7 weeks at 4 °C and viscosity<15 cP.
- **41928412** (2026, 3 cites, 6 keyword hits: engineering, melting, mutation, optimization, stability, temperature) — Engineering of β-Agarase with Enhanced Thermostability via Multitool Consensus Prediction and Structure-Guided Screening
  - > This yielded mutant M3 (N120S-D243N-Q246A-S287E-A335D), which exhibits an 11 °C higher melting temperature (Tm) and 14-fold longer half-life (t1/2) at 50 °C than the wild-type.
- **22272277** (2012, 63 cites, 5 keyword hits: engineering, melting, mutation, stability, temperature) — Stabilisation of the Fc fragment of human IgG1 by engineered intradomain disulfide bonds
  - > One of these bonds, which connects the N-terminus of the CH3 domain with the F-strand, led to an increase of the melting temperature of this domain by 10°C as compared to the CH3 domain in the context of the wild-type Fc region.
  - > Another engineered disulfide bond, which connects the BC loop of the CH3 domain with the D-strand, resulted in an increase of T(m) of 5°C.
  - > Combined in one molecule, both intradomain disulfide bonds led to an increase of the T(m) of about 15°C.
- **31181988** (2019, 54 cites, 5 keyword hits: affinity, melting, scfv, stability, temperature) — Development of tibulizumab, a tetravalent bispecific antibody targeting BAFF and IL-17A for the treatment of autoimmune disease
  - > The anti-IL-17 scFv showed a high melting temperature (Tm) by differential scanning calorimetry (73.1°C), but also concentration-dependent, initially reversible, protein self-association.

### TH-003 — Arginine-rich designed CDRH3 loops will score well on predicted affinity but fail epitope preservation, because Arg-driven affinity is non-specific

- **35941164** (2022, 27 cites, 5 keyword hits: affinity, binding, charge, charged, residue) — A 33-residue peptide tag increases solubility and stability of Escherichia coli produced single-chain antibody fragments
  - > Here we report that a 33-residue peptide, termed P17 tag, increases the solubility of multiple scFvs produced in Escherichia coli SHuffle strain by up to 11.6 fold.
- **40267400** (2025, 2 cites, 5 keyword hits: affinity, charge, charged, mutation, residue) — Enhanced antibody-mediated cellular cytotoxicity of germline-like anti-HER2 antibodies through a point mutation in complementarity-determining regions
  - > Substitution of aspartic acid with glutamic acid decreased the interaction energies, resulting in a remarkable affinity enhancement of Ab5m-scFv (KD = 0.2 nM) compared with parental Ab5-scFv (KD = 1.5 nM).
- **AMBC_JwGSFsFYuumYi1zgXk0571g2F5A** (2026, 0 cites, 5 keyword hits: affinity, binding, mutation, residue, specificity) — An innovative AI-based platform for antibody stability improvement and affinity optimization.
  - > This approach effectively find a new mutant reduced aggregation under one-week accelerated thermal stress from 100% to less than 5%, while increasing the melting temperature (Tm) by up to ∼10 °C.
- **31181988** (2019, 54 cites, 4 keyword hits: affinity, binding, charge, residue) — Development of tibulizumab, a tetravalent bispecific antibody targeting BAFF and IL-17A for the treatment of autoimmune disease
  - > The anti-IL-17 scFv showed a high melting temperature (Tm) by differential scanning calorimetry (73.1°C), but also concentration-dependent, initially reversible, protein self-association.
- **36683173** (2023, 46 cites, 4 keyword hits: affinity, mutation, residue, specificity) — Toward generalizable prediction of antibody thermostability using machine learning on sequence and structure features
  - > Both of these models are trained over temperature-specific data (TS50 measurements) derived from multiple libraries of scFv sequences.
  - > Further, we demonstrate that for an independent mAb with available thermal melting temperatures for 20 experimentally characterized thermostable mutations, these models trained on TS50 data could identify 18 residue positions and 5 identical amino-acid mutations showing remarkable generalizability.
- **23255066** (2013, 34 cites, 4 keyword hits: affinity, binding, residue, specificity) — Ab initio structure prediction of the antibody hypervariable H3 loop
  - > When the prediction is performed in the crystal environment and including symmetry mates, the median backbone root mean square deviation (RMSD) is 0.5 Å to the crystal structure, with 91% of cases having an RMSD of less than 2.0 Å.
  - > When the prediction is performed in a noncrystallographic environment, where the scaffold is constructed by swapping the H3 loops between homologous antibodies, 70% of cases have an RMSD below 2.0 Å.

### TH-004 — Selecting designs on predicted CDRH3 loop rigidity is not a useful filter, so we should not spend effort on it

- **31181988** (2019, 54 cites, 5 keyword hits: affinity, binding, conformational, factor, loop) — Development of tibulizumab, a tetravalent bispecific antibody targeting BAFF and IL-17A for the treatment of autoimmune disease
  - > The anti-IL-17 scFv showed a high melting temperature (Tm) by differential scanning calorimetry (73.1°C), but also concentration-dependent, initially reversible, protein self-association.
- **35547916** (2018, 16 cites, 5 keyword hits: affinity, binding, conformational, entropy, factor) — Comparative thermodynamic analysis in solution of a next generation antibody mimetic to VEGF
  - > FpFbeva displayed comparable binding affinity (KD) and binding thermodynamics (ΔH = -25.7 kcal mole-1 and ΔS = 14 kcal mole-1) to bevacizumab (ΔH = -25 kcal mole-1, ΔS = 13.3 kcal mole-1).
- **41193805** (2025, 122 cites, 4 keyword hits: affinity, binding, loop, maturation) — Atomically accurate de novo design of antibodies with RFdiffusion
  - > Although initial computational designs exhibit modest affinity (tens to hundreds of nanomolar Kd), affinity maturation using OrthoRep3 enables production of single-digit nanomolar binders that maintain the intended epitope selectivity.
- **23255066** (2013, 34 cites, 4 keyword hits: affinity, binding, conformational, loop) — Ab initio structure prediction of the antibody hypervariable H3 loop
  - > When the prediction is performed in the crystal environment and including symmetry mates, the median backbone root mean square deviation (RMSD) is 0.5 Å to the crystal structure, with 91% of cases having an RMSD of less than 2.0 Å.
  - > When the prediction is performed in a noncrystallographic environment, where the scaffold is constructed by swapping the H3 loops between homologous antibodies, 70% of cases have an RMSD below 2.0 Å.
- **24492299** (2014, 29 cites, 4 keyword hits: affinity, binding, maturation, repertoire) — In vitro affinity maturation of a natural human antibody overcomes a barrier to in vivo affinity maturation
  - > One high affinity (KD<10 pM) variant was identified that combined the D53N and T55R mutations while avoiding glycosylation of CDR H2.
- **32610044** (2020, 25 cites, 4 keyword hits: affinity, binding, cdrh3, loop) — Computationally Designed Cyclic Peptides Derived from an Antibody Loop Increase Breadth of Binding for Influenza Variants
  - > We designed cyclic peptides that mimic the heavy-chain complementarity-determining region 3 (CDRH3) of anti-influenza broadly neutralizing antibody C05 and show that these peptides bound to HA molecules with <100 nM affinity, comparable with that of the full-length parental C05 IgG.

### IDEA-007 — Check whether any of our designs sit near a claimed patent sequence

- **32610044** (2020, 25 cites, 5 keyword hits: anti, cdrh3, computationally, designed, variant) — Computationally Designed Cyclic Peptides Derived from an Antibody Loop Increase Breadth of Binding for Influenza Variants
  - > We designed cyclic peptides that mimic the heavy-chain complementarity-determining region 3 (CDRH3) of anti-influenza broadly neutralizing antibody C05 and show that these peptides bound to HA molecules with <100 nM affinity, comparable with that of the full-length parental C05 IgG.
- **34392800** (2021, 6 cites, 5 keyword hits: anti, her2, sequence, trastuzumab, variant) — Machine learning modeling to identify affinity improved biobetter anticancer drug trastuzumab and the insight of molecular recognition of trastuzumab towards its antigen HER2
  - > A 100 evolutionary cycles of GA produced the best 100 probable GA-SVR models based on their fitness score (Q2) estimated using a stratified 5 fold cross-validation procedure.
- **42909185** (2026, 0 cites, 5 keyword hits: anti, computationally, her2, sequence, variant) — Structure-guided computational design and mechanistic understanding of the p95HER2-targeting NAZ-mAb antibody and its variants
  - > However, Biacore two-state kinetic analysis revealed weaker affinities than the parental antibody (KD NAZ-mAb v1: 326.1 nM, NAZ-mAb v2: 94.5 nM vs parental NAZ-mAb: 53.3 nM).
- **28750054** (2017, 44 cites, 4 keyword hits: anti, designed, her2, sequence) — Assisted Design of Antibody and Protein Therapeutics (ADAPT)
  - > The platform was tested on three antibody Fab-antigen systems that spanned a wide range of initial binding affinities: bH1-VEGF-A (44 nM), bH1-HER2 (3.6 nM) and Herceptin-HER2 (0.058 nM).
- **25043744** (2014, 22 cites, 4 keyword hits: anti, computationally, designed, sequence) — Computational design of protein antigens that interact with the CDR H3 loop of HIV broadly neutralizing antibody 2F5
  - > MultiGraft Interface generated an epitope-scaffold that bound 2F5 with subnanomolar affinity (K(D) = 400 pM) and that interacted with the antibody CDR H3 loop through computationally designed contacts.
- **37396255** (2023, 14 cites, 4 keyword hits: anti, designed, trastuzumab, variant) — Molecular Dynamics-Based Design and Biophysical Evaluation of Thermostable Single-Chain Fv Antibody Mutants Derived from Pharmaceutical Antibodies
  - > Trastuzumab scFv variants were prepared by using an Escherichia coli expression system, and the melting temperature-measured as a thermostability index-was 5 °C higher than that of the wild-type trastuzumab scFv, while the antigen-binding affinity was unchanged.

## Proposed updates

The agent driving this pass fills this in and applies it, then records the move in each theory's history with this pass id.

| Target | Proposed change | Justified by |
|---|---|---|
| TH-002 | confidence `medium` → **`low`** | Three sources against it. EXP-005: CDRH3 is thermostability-inert, so an affinity gain bought there cannot cost Tm. AMBC_JwGSFsFYuumYi1zgXk0571g2F5A: Tm up to ~10 °C higher with aggregation falling 100% → <5% *while* optimising affinity. PMID:23995618: CDR-restricted scFv engineering gave 100 mg/ml formulation with <2% HMW after 7 weeks. **Downgraded, not retired** — EXP-005's Tm is predicted and out-of-domain, and we have no measured Tm for any CDRH3 variant |
| IDEA-016 | **new**, priority `medium` | PMID:31181988 — an anti-IL-17 scFv with Tm 73.1 °C by DSC still showed concentration-dependent self-association, so Tm alone does not clear developability. Nothing in the backlog covered expression/solubility, and an unexpressed design is unmeasurable rather than merely bad |
| `research_pass.py` | stop the fetch loop on a credits 403 instead of retrying each query | This pass made **seven** doomed calls after the first one reported exhausted credits |

**Applied** 2026-11-14 by Claude Opus 5.

> ## ⛔ AMASS credits exhausted
>
> After 3 successful searches this pass, the API returned HTTP 403:
> `{"error":{"status":403,"code":"FORBIDDEN","message":"You are out of API credits. Please top up your API credits."}}`
>
> This ledger has spent **14 searches / $0.70**, so the ~2,000-search team
> budget was consumed elsewhere — the sibling literature task ran ~30 queries
> plus a full-text corpus fetch, which costs far more per record than a search.
> Top up at <https://platform.amass.tech/settings/credits>.
>
> **The loop is not dead.** Step A, the repo scan, is free and has produced
> every one of EXP-002 through EXP-005 — all four of the ledger's substantive
> results came from reading teammates' commits, not from AMASS. Passes continue
> with Step A only until credits return.

**Discarded, with reasons:**

- **PMID:41928412** — β-agarase thermostability (+11 °C Tm, 14× half-life). An *enzyme*, wrong molecule class entirely.
- **PMID:22272277** — intradomain disulfides stabilising IgG1 **Fc** by +10/+5/+15 °C. Real and already cited by TH-005, but out of scope for our formats: Adaptyv expresses scFv, VHH or Fab, none of which contain an Fc. Worth recording so nobody chases it.
- **PMID:36683173** — already carried by TH-016's lineage; re-matched, no new information.
- **PMID:31181988 (partly)** — kept for IDEA-016, but its Tm/self-association result is about developability, not the affinity–stability trade-off TH-002 asserts.
| TH-003 | _pending_ | _pending_ |
| TH-004 | _pending_ | _pending_ |
| IDEA-007 | _pending_ | _pending_ |

