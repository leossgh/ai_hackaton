# Theories — what we currently believe

Each theory is a falsifiable claim about how to beat trastuzumab on the three
measured properties. Confidence moves only when an experiment verdict or a
literature pass brings something new, and every move appends a dated line to
that theory's `history` citing the `exp_id` or pass id that caused it. Claims
are never silently edited — supersede them instead.

`confidence`: `high` | `medium` | `low` | `retired`.
`query_terms` drives [`research_pass.py`](research_pass.py); prefix a term with
`patent:` to send it to patentcore instead of biomedcore.

Seeded 2026-11-14 from the 30 cached AMASS queries in
[`../litreview-optimisation/`](../litreview-optimisation/) (pass-001). That
review was still running when these were written, so every confidence here is
provisional and several theories are deliberately stated more strongly than the
evidence yet supports, so that a pass can knock them down.

---

### TH-001 — Diversifying CDRH3 wholesale raises anti-HER2 affinity rather than destroying it, so our <70% CDRH3 identity constraint is an opportunity, not a tax

- **confidence:** high
- **status:** active
- **property:** binding
- **falsified_by:** A design series whose CDRH3 is >30% substituted shows systematically worse SPR KD than trastuzumab, with no high-affinity tail.
- **evidence_for:** PMID:8918938 — sequential VL-CDR3 then VH-CDR3 library mutation of an **anti-c-erbB-2 (HER2)** scFv gave 1230-fold KD improvement to 1.3e-11 M, with a 20 aa VH CDR3, i.e. long enough to tolerate library-scale change; PMID:29702641 — RosettaAntibodyDesign replaced individual CDRs with new **lengths and clusters** and improved affinity **10-50 fold, verified experimentally** on both a lambda and a kappa antibody-antigen complex; PMID:26225765 — targeted CDR3 randomisation of an anti-HER2 antibody optimised therapeutic targeting; PMID:35545451
- **evidence_against:** EXP-002 — wholesale CDRH3 change is no longer epitope-free: 4 substitutions are needed for the identity gate and only 3 CDRH3 positions never contact HER2, so an affinity-motivated redesign necessarily touches a contact (TH-009). The affinity case is strong; the *freedom* is not
- **query_terms:** CDRH3 library randomization affinity gain anti-HER2 scFv; CDR3 diversification picomolar affinity maturation; long CDRH3 20 residue loop tolerance substitution
- **history:**
  - 2026-11-14 created, confidence medium — one strong primary result (8918938) but on C6.5, not trastuzumab, and KD measured by a 1996 method (pass-001)
  - 2026-11-14 medium → **high** (pass-003). PMID:29702641 is a second, independent, experimentally verified result: 10-50 fold affinity gains from replacing whole CDRs including length changes. Combined with PMID:8918938, which is on an anti-HER2 scFv, two primary results now support wholesale CDR change as an affinity route. Note what did *not* move: EXP-002 added counter-evidence that the route is not epitope-free, so this theory is now "CDRH3 redesign can win affinity", not "CDRH3 redesign is safe".

### TH-002 — Affinity gains bought in CDRH3 cost thermostability, so the two prize properties are in direct tension and must be co-optimised, not optimised in sequence

- **confidence:** medium
- **status:** active
- **property:** binding; thermostability
- **falsified_by:** Our top-affinity designs show no Tm penalty relative to trastuzumab, or the penalty is uncorrelated with the number of CDRH3 substitutions.
- **evidence_for:** PMID:30666176 — review of affinity/specificity/stability/solubility trade-offs, states improvements in one property commonly cause deficits in another; PMID:21540796
- **evidence_against:** PMID:40653772 — stabilising framework mutations distal to the CDRs preserved HER2 engagement, which suggests the tension can be *sidestepped* rather than traded (see TH-005)
- **query_terms:** antibody affinity stability trade-off CDR mutation destabilizing; CDR mutation melting temperature penalty scFv; co-optimization affinity stability antibody engineering
- **history:**
  - 2026-11-14 created, confidence medium — the supporting source is a review, not primary measurement; the counter-evidence is primary and trastuzumab-specific (pass-001)

### TH-003 — Arginine-rich designed CDRH3 loops will score well on predicted affinity but fail epitope preservation, because Arg-driven affinity is non-specific

- **confidence:** medium
- **status:** active
- **property:** binding; epitope
- **falsified_by:** High-Arg CDRH3 designs compete with trastuzumab for HER2 as well as low-Arg designs of matched predicted affinity.
- **evidence_for:** PMID:28778924 — scFv selected under weak specificity selection were enriched in Arg CDR mutations and were poorly specific; affinity of the *specific* variants depended much less on their Arg residues, i.e. over-reliance on Arg for affinity reduces specificity
- **evidence_against:**
- **query_terms:** arginine CDR mutation polyspecificity nonspecific binding antibody; charged residue CDR affinity specificity trade-off; antibody net charge nonspecificity developability
- **history:**
  - 2026-11-14 created, confidence medium — mechanism shown on an anti-amyloid-beta scFv, not HER2; transfer is an assumption (pass-001)

### TH-004 — Selecting designs on predicted CDRH3 loop rigidity is not a useful filter, so we should not spend effort on it

- **confidence:** medium
- **status:** active
- **property:** binding
- **falsified_by:** Rigidity or B-factor based ranking separates our strong from weak binders in the returned assay data.
- **evidence_for:** PMID:29545810 — rigidity theory over thousands of repertoire models found no clear delineation between naive and antigen-experienced antibodies, and only a slight CDR-H3 flexibility decrease in PDB structures; PMID:26132144 and PMID:21287614 argue the opposite and are the minority position by sample size
- **evidence_against:** PMID:26132144 — QSFR analysis found rigidity emerges during affinity maturation in three antibody systems
- **query_terms:** CDRH3 loop flexibility rigidity affinity maturation repertoire; antibody paratope conformational entropy binding; B-factor rigidity antibody affinity prediction
- **history:**
  - 2026-11-14 created, confidence medium — this is a useful *negative* that saves effort if it holds; the literature is genuinely split (pass-001)

### TH-005 — Stability and binding can be decoupled: put all binding risk in CDRH3 and buy back thermostability with framework mutations that do not touch the epitope

- **confidence:** medium
- **status:** active
- **property:** thermostability; epitope
- **falsified_by:** Framework-stabilised variants of our designs lose HER2 competition against trastuzumab, or gain no Tm.
- **evidence_for:** PMID:40653772 — on trastuzumab specifically, computationally designed framework mutations distal to the CDRs were stabilising and preserved HER2 engagement and ADCC; PMID:32336757 — computer-based engineering of thermostabilised antibody fragments; PMID:22272277 — engineered intradomain disulfides stabilised IgG1 Fc
- **evidence_against:** PMID:40653772 — the same work found one light-chain framework mutation that kept antigen binding but lost effector function, so framework changes are not free of functional consequence (harmless for our three properties, which exclude effector function)
- **query_terms:** framework mutation antibody thermostability preserve antigen binding trastuzumab; scFv framework stabilizing mutation melting temperature; consensus framework engineering Fv stability
- **history:**
  - 2026-11-14 created, confidence medium — strongest theory in this set because the evidence is primary, computational-plus-experimental, and on trastuzumab itself (pass-001)

### TH-006 — A VHH can hold trastuzumab's own epitope at sub-nanomolar affinity, so the de novo track is viable without giving up epitope preservation

- **confidence:** medium
- **status:** active
- **property:** binding; epitope
- **falsified_by:** Designed VHHs that score well on min_ipae fail competitive binding against trastuzumab, indicating the epitope needs a paired VH/VL interface.
- **evidence_for:** PMID:37632647 — an anti-HER2 VHH with sub-nanomolar affinity binds the same epitope as trastuzumab, confirmed by epitope mapping and docking
- **evidence_against:**
- **query_terms:** VHH nanobody HER2 trastuzumab epitope competitive binding; single domain antibody domain IV HER2 affinity; nanobody epitope mapping overlap monoclonal
- **history:**
  - 2026-11-14 created, confidence medium — a single existence proof, which is enough to justify the route but not to predict our hit rate (pass-001)

### TH-007 — scFv thermostability is predictable from sequence well enough to rank our designs, which closes the open "no thermostability predictor" decision

- **confidence:** medium
- **status:** active
- **property:** thermostability
- **falsified_by:** The chosen predictor's ranking shows no correlation with the measured Tm values Adaptyv returns.
- **evidence_for:** PMID:39154093 — TEMPRO predicts single-domain antibody Tm from protein embeddings with **MAE 4.03 °C, RMSE 5.66 °C**, i.e. a stated error bar on the quantity Adaptyv actually measures; PMID:41564239 (2026) — synergistic deep-learning nanobody thermostability prediction proposing a concrete screening criterion, **Tm > 65 °C and Qclass IV**; PMID:36683173 — PTLM and Rosetta-feature CNN classify thermostable scFv variants, and on an independent mAb with 20 characterised thermostable mutations the TS50-trained models recovered **18 of the residue positions and 5 identical amino-acid mutations**
- **evidence_against:** PMID:36683173 — trained on TS50, a proxy, not Tm, and out-of-distribution generalisation is explicitly qualified; the two strongest predictors (PMID:39154093, PMID:41564239) are **nanobody/sdAb-specific**, so they only apply to a VHH submission, not to an scFv
- **query_terms:** scFv thermostability prediction machine learning validation Tm; antibody melting temperature predictor benchmark accuracy; TEMPRO nanobody Tm protein embedding prediction
- **history:**
  - 2026-11-14 created, confidence low — this is the team's named open decision and the candidates are all trained on proxies; needs a pass of its own (pass-001)
  - 2026-11-14 low → **medium** (pass-002). Two things changed. TEMPRO now gives us a numeric error bar on predicted Tm (MAE 4.03 °C), which is what a ranking needs; and PMID:36683173's 18-of-20 position recovery is stronger transfer evidence than the TS50 caveat alone suggested. Not `high`, because the predictor choice turns out to be **format-dependent**: TEMPRO and PMID:41564239 are nanobody-only, so an scFv submission still rests on TS50-trained models. This splits IDEA-003 into a VHH answer and an scFv answer.

### TH-008 — The 1N8Z contact residues define which CDRH3 positions are load-bearing for the epitope, so a design that preserves those contacts preserves the epitope

- **confidence:** retired
- **status:** retired
- **property:** epitope
- **falsified_by:** Designs that conserve the 1N8Z contact set still lose competitive binding, or designs that break it still win it. — **Falsified before any design, by structure: see EXP-002.**
- **evidence_for:** PMID:12610629 — structure of HER2 with the Herceptin Fab, the source of the contact set; PMID:31042744 — cryo-EM of the HER2-trastuzumab-pertuzumab complex
- **evidence_against:** EXP-002 — 1N8Z alone labels 7 CDRH3 positions contact-free, but across 8 trastuzumab-HER2 structures only 3 never contact HER2. 1N8Z has unmodelled HER2 regions (102-110, 303-305, 361-364, 581-590) and several CDRH3 positions contact residues in 579-593, so a single-structure contact set under-counts contacts in the direction that flatters the design
- **query_terms:** trastuzumab HER2 contact residues 1N8Z interface paratope; alanine scanning trastuzumab HER2 hot spot energetic contribution; buried surface area shape complementarity HER2 antibody interface
- **history:**
  - 2026-11-14 created, confidence low — we have the structure but have not yet extracted a per-residue energetic contribution, and a contact is not the same as a hot spot (pass-001)
  - 2026-11-14 **retired** (EXP-002). Not downgraded but retired: the claim names 1N8Z as the authority, and 1N8Z is demonstrably insufficient. Superseded by TH-009 (which positions are safe) and TH-010 (how much of the interface CDRH3 even covers). Kept rather than deleted because the failure mode — concluding from one crystal structure with gaps — is the lesson.

### TH-009 — The <70% CDRH3 identity gate cannot be met without mutating at least one HER2-contacting position, and the cheapest one to sacrifice is Y109

- **confidence:** high
- **status:** active
- **property:** epitope; binding
- **falsified_by:** A design substituting only A106/M107/D108 passes abguard's CDRH3 identity check (it should not: 3/11 = 72.7%), or a design that also substitutes Y109 loses competitive binding against trastuzumab while one sparing Y109 retains it.
- **evidence_for:** EXP-002 — CDRH3 is WGGDGFYAMDY (11 aa, 99-109), so <70% identity needs 4 substitutions (4/11 = 63.6%); across 8 trastuzumab-HER2 structures at 4.5 A only A106, M107 and D108 never contact HER2 (0/8 each), while Y109 contacts in 1/8, G101 2/8, G100 3/8, F104 4/8, W99 5/8, D102 6/8, G103 7/8, Y105 7/8
- **evidence_against:** Contact frequency across crystal structures is a geometric proxy, not an energetic one. A 1-of-8 contact may still be energetically important, and no alanine scan has been run to rule that out (IDEA-008)
- **query_terms:** antibody paratope contact conservation across crystal structures; CDR position energetic hot spot alanine scan contribution; crystal packing artefact antibody antigen contact variability
- **history:**
  - 2026-11-14 created at confidence **high** (EXP-002). Unusually high for a new theory because the claim is arithmetic plus measured geometry across 8 independent structures, not an inference: 4 substitutions are required and only 3 safe positions exist. The design recipe A106/M107/D108 + Y109 follows directly. What is *not* high-confidence is the assumption that sacrificing a 1-of-8 contact is harmless, which is why the theory names Y109 explicitly so it can be falsified.
  - 2026-11-14 **no change**, and that is the finding (pass-003). Three targeted searches plus the full cache turned up nothing on the energetic contribution of trastuzumab CDRH3 Tyr109, or of any individual trastuzumab paratope residue. The literature cannot settle whether sacrificing Y109 is safe, so IDEA-010 is escalated to high priority: if we want that answer we have to compute it. The theory stands on geometry alone, which is exactly as strong as it was before.

### TH-010 — CDRH3-only redesign can address at most a third of the trastuzumab-HER2 interface, so CDRH3 is the wrong place to look for large binding gains

- **confidence:** high
- **status:** active
- **property:** binding
- **falsified_by:** CDRH3-only designs show SPR improvements over trastuzumab comparable to what CDR-wide or framework-inclusive redesign achieves.
- **evidence_for:** EXP-002 — per-CDR share of interface contacts across 8 structures: H3 12-34% (26% in 1N8Z), H2 14-47%, L3 11-29%, L1 5-17%, L2 0-30%, framework up to 23% (6BGT); heavy-chain CDRs carry 55% and light-chain CDRs 45% in 1N8Z
- **evidence_against:** Interface share counts contacts, not binding energy; a minority of contacts can carry a majority of the affinity. PMID:8918938 got a 1230-fold KD gain from VL-CDR3 and VH-CDR3 libraries alone, which shows CDR3s can dominate affinity even when they do not dominate contact count
- **query_terms:** antibody interface contact share CDR contribution binding energy; CDR H2 L3 contribution affinity antigen; framework contact antigen antibody interface contribution
- **history:**
  - 2026-11-14 created at confidence **high** for the measurement, which is unambiguous across 8 structures (EXP-002). The *strategic* reading is weaker and the counter-evidence says so: PMID:8918938 is a direct case of CDR3 libraries delivering a 1230-fold gain. Practical consequence: all four HER2 RFD4 weights redesign CDRH3 only, so the tool set available to us works on a minority of the interface. If we want more, it needs `antibody-2026-10-30` on other CDRs (IDEA-009).

### TH-011 — Refold scores cannot separate close CDRH3 designs, because predicted conformation for an 11-residue H3 loop is only accurate to roughly 2 A

- **confidence:** medium
- **status:** active
- **property:** binding
- **falsified_by:** Repeated folding of the same design across seeds and models gives min_ipae spreads much smaller than the score gaps we are ranking on, or the returned SPR values track the predicted ranking.
- **evidence_for:** PMID:19062174 — median backbone RMSD of CDR H3 loop prediction is **2.4 A for medium (10-11 residue) loops**, and trastuzumab's CDRH3 is 11 aa; PMID:23255066 — ab initio H3 prediction reaches 0.5 A median RMSD **in the crystal environment with symmetry mates**, but without that context only 70% of cases fall under 2.0 A; EXP-001 — the two refolded designs differed by just 0.021 min_ipae on a single Boltz-2 seed, a gap with no established error bar
- **evidence_against:** Both RMSD figures come from homology and ab initio loop modelling, not from the co-folding models we actually use (Boltz-2, OpenFold3, Protenix), which take a template and may do better on a grafted loop in a fixed framework
- **query_terms:** CDRH3 loop conformation prediction accuracy RMSD benchmark; Boltz AlphaFold interface pAE reliability antibody antigen; folding model seed variance interface confidence score
- **history:**
  - 2026-11-14 created, confidence medium (pass-003). Found while looking for something else: the question "can we trust the ranking?" matters more than any single score, because only ~4 designs are tested and rank order is the real output. The two RMSD studies are older methods than our folding stack, hence medium not high. The cheap test is IDEA-006, which already exists: add a second Boltz-2 seed and see whether the 0.021 gap in EXP-001 survives.
