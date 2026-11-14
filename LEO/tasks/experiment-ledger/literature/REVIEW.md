# Standing literature review

The current picture, organised by the three measured properties. Research passes
under [`../research/`](../research/) are the transaction log; this file is the
balance. Every claim cites an AMASS record, and **measured** results are kept
separate from **predicted** ones.

Seeded 2026-11-14 (pass-001) from 30 cached AMASS queries. The sibling task
[`../../litreview-optimisation/`](../../litreview-optimisation/) was still
running when this was written, so this is a first cut and its own digest will
supersede parts of it.

---

## 1. Binding affinity (measured by SPR)

**The strongest transferable result.** Sequential diversification of VL-CDR3 and
then VH-CDR3 in an anti-c-erbB-2 scFv (C6.5) produced a **1230-fold KD
improvement, to 1.3 × 10⁻¹¹ M** (PMID:8918938, measured). The VH CDR3 was 20 aa
and was split across four libraries. This matters for us in a specific way: our
hard constraint forces CDRH3 identity below 70%, and this result says a long
CDRH3 subjected to library-scale change is where the largest affinity gains came
from. The constraint points the same direction the evidence does (TH-001).

Related measured work: targeted CDR3 randomisation of anti-HER2 mAb 1E11
(PMID:26225765); phage display with high-throughput synthesis and sequencing
(PMID:26046845); natural diversity mutagenesis for facile affinity maturation
(PMID:28928732); in vitro CDR mutagenesis (PMID:35545451).

Baseline numbers for trastuzumab and pertuzumab against HER2 ECD exist
(PMID:37569408, measured) — needed as our comparison point, not yet extracted.

**Caveat on cross-paper comparison.** KD values come from different assays and
conditions; `AGENTS.md` and the task description both warn that cross-paper
comparison is often invalid. Our own baseline is the measured trastuzumab SPR
value, not a literature number.

## 2. Epitope preservation (measured by competition against trastuzumab)

**The epitope is reachable by a single domain.** An anti-HER2 **VHH binds the
same epitope as trastuzumab at sub-nanomolar affinity**, confirmed by epitope
mapping plus in-silico docking (PMID:37632647, measured affinity by BLI,
predicted docking). This is an existence proof that epitope preservation does
not require a paired VH/VL interface, which keeps the de novo VHH route open
(TH-006).

**Structural basis — now measured, and the measurement reversed the answer.**
The HER2–Herceptin Fab structure (PMID:12610629) is the source of the domain IV
contact set; the cryo-EM ternary complex (PMID:31042744) adds the arrangement.
EXP-002 measured the contacts directly at 4.5 Å across **8** trastuzumab–HER2
structures (1N8Z, 22GC, 22GE, 6BGT, 6OGE, 7MN8, 8PWH, 8Q6J).

CDRH3 is **WGGDGFYAMDY**, 11 residues, so clearing the `<70%` identity gate
needs **4 substitutions**. From 1N8Z alone, 7 positions look contact-free — but
across all 8 structures only **3 never contact HER2** (A106, M107, D108). 1N8Z
leaves HER2 579–593 unmodelled, and several CDRH3 positions contact there, so
one structure under-counts contacts in exactly the direction that flatters a
design.

**Consequence:** the identity gate and epitope preservation are in quantified
tension — at least one contacting position must be mutated. The cheapest is
**Y109** (contacts in 1 of 8). That yields the recipe A106/M107/D108/Y109
(TH-009, IDEA-008). This retired TH-008, which had named 1N8Z as the authority.

**The HER2 epitope itself:** 34 residues contacted in at least one structure, of
which 6 are contacted in every structure that models them — **P557, E558, P571,
585, Q602, P603** — the core to preserve.

**Interface share:** CDRH3 carries only 12–34% of contacts (26% in 1N8Z), with
H2 at 14–47%, L3 11–29%, L1 5–17%, and framework up to 23%. All four HER2 RFD4
weights redesign CDRH3 only, so our default tooling addresses a minority of the
interface (TH-010, IDEA-009).

Still missing: per-residue **energetics**. Contact frequency is geometry, not
binding free energy, and Y109 is precisely the position the recipe sacrifices
(IDEA-010). A contact is not a hot spot.

**A failure mode to design against.** Arg-enriched CDR mutations raise affinity
but cost specificity: scFv selected under weak specificity pressure were
Arg-enriched and poorly specific, and alanine scanning showed their affinity
depended heavily on those Arg residues, whereas genuinely specific variants did
not (PMID:28778924, measured). Since epitope preservation is scored by
*competition*, a design that gains affinity non-specifically can win on SPR and
still fail the epitope assay (TH-003).

## 3. Thermostability (directly measured)

**Updated by pass-002.** A usable predictor exists, but only for single-domain
antibodies, so the answer depends on which format we submit.

*For a VHH.* TEMPRO predicts sdAb Tm from protein embeddings with **MAE
4.03 °C, RMSE 5.66 °C** (PMID:39154093, predicted-vs-measured) — an error bar on
the exact quantity Adaptyv measures, which is what a ranking needs. A 2026
synergistic deep-learning model adds an explicit screening criterion, **Tm >
65 °C and Qclass IV**, for calling a nanobody highly thermostable
(PMID:41564239). pass-002 found that record; it was absent from the 30 seeded
queries.

*For an scFv.* Still no Tm-trained predictor. The best available is a
pre-trained language model plus a Rosetta-feature CNN, trained on **TS50**
rather than Tm (PMID:36683173, predicted). Its transfer is better than the
proxy caveat suggests: on an independent mAb with 20 experimentally
characterised thermostable mutations, the TS50-trained models identified **18 of
the residue positions and 5 identical amino-acid mutations**. Cross-correlation
methods for therapeutic thermal stability are newer and unvalidated here
(PMID:41072360).

**Consequence for the pitch.** If we submit a VHH, TH-007/IDEA-003 is
effectively closed and we can defend the ranking. If we submit scFv only, the
predictor stays a declared weakness rather than a claim.

**The route that does not need a predictor.** On **trastuzumab itself**,
computationally designed **framework mutations distal to the CDRs** were
stabilising while preserving HER2 engagement and ADCC (PMID:40653772, measured
and computational). Engineered intradomain disulfides stabilised IgG1 Fc
(PMID:22272277, measured); thermostabilised antibody fragments have been built
computationally (PMID:32336757). Caution from the same paper: one light-chain
framework mutation retained antigen binding but **lost effector function** —
irrelevant to our three scored properties, but a reminder that framework changes
have non-local consequences.

Watch the hard constraint: any stabilising disulfide must not leave an unpaired
cysteine, which `abguard` rejects outright.

## 4. The trade-off, which is the real design problem

The field-level claim is that improving one antibody property commonly degrades
another — affinity, specificity, stability and solubility are coupled
(PMID:30666176, review; PMID:21540796). This is a review, so it is weaker
evidence than it looks.

Against it sits PMID:40653772, which is primary, trastuzumab-specific, and
suggests the tension can be **sidestepped by localisation**: take binding risk in
CDRH3, buy stability back in the framework, keep them spatially separate. That is
TH-005 and IDEA-001, and it is currently our best route to an S-tier design —
the only one that plausibly improves more than one scored property at once.

## 5. Settled negatives (things not to spend effort on)

**Loop rigidity is not a usable filter.** Rigidity-theory analysis across
thousands of repertoire models found no clear flexibility difference between
naive and antigen-experienced antibodies, and only a slight CDR-H3 decrease
across PDB structures (PMID:29545810). The opposing result (PMID:26132144,
three antibody systems; PMID:21287614) is smaller-sample. The literature is
genuinely split, so ranking designs on predicted rigidity is not defensible
(TH-004).

## 6. Prior art

The patent space is crowded: `Anti-HER2 antibody variants`
(AMPC_aBuqIb7Kktf9HPDjGEDYn4Wxb7c), `High-affinity fully-humanized anti-Her2
monoclonal antibody` (AMPC_GF5vxHlt1UERW9h4xHZMPZMjinX), hersintuzumab
(AMPC_NMYwLlcDmraSyiFzNAYRlUdejqy) and ~35 more in the digest. Not a hackathon
filter, but "path to value" is 20% of the pitch score (IDEA-007).

## 7. Known gaps

| Gap | Why it matters | Owner |
|---|---|---|
| No trastuzumab Fab/scFv Tm baseline extracted | We cannot say "more thermostable" without it | open |
| No per-residue energetics at the 1N8Z interface | "Preserves the epitope" stays an assertion | IDEA-004 |
| Thermostability predictor unchosen | One of three scored properties has no proxy | IDEA-003 |
| Cell-free expression determinants not extracted | A design that does not express is unmeasurable | open |
| trialcore records returned empty titles | 20 records are unusable as cited | open |

## 8. Can we trust the ranking? (added by pass-003)

Rank order is the real submission output — only ~4 designs are tested — so the
reliability of the metric we rank on matters more than any single score.

**Loop prediction accuracy is the limiting factor.** Median backbone RMSD for
CDR H3 loop prediction is **2.4 Å for medium (10–11 residue) loops**
(PMID:19062174, benchmark), and trastuzumab's CDRH3 is 11 aa. Ab initio H3
prediction reaches **0.5 Å** median RMSD when run *in the crystal environment
with symmetry mates*, but without that context only **70% of cases fall under
2.0 Å** (PMID:23255066, benchmark). Both are older methods than the co-folding
stack we use, and ours takes a template, so these are upper bounds on the error
rather than estimates of it — but nothing here supports separating designs on
small score differences.

For contrast, EXP-001 ranked two designs on a **0.021** min_ipae gap from a
**single** Boltz-2 seed, with no error bar established for either the seed or
the model. That is the gap TH-011 says we cannot currently defend, and IDEA-006
is the cheap test.

**Method note worth keeping:** RosettaAntibodyDesign improved affinity **10–50
fold, experimentally verified**, by replacing individual CDRs with new lengths
and clusters (PMID:29702641). This is the second independent primary result
supporting wholesale CDR replacement as an affinity route, alongside the
1230-fold anti-c-erbB-2 result (PMID:8918938) — which is why TH-001 moved to
`high`. It also raises CDR *length* change as a lever we have not considered.

**A gap literature cannot close.** Three targeted searches found nothing on the
energetic contribution of trastuzumab's CDRH3 Tyr109, or of any individual
trastuzumab paratope residue. Y109 is the one contact the IDEA-008 recipe
sacrifices, so this has to be computed, not looked up (IDEA-010, now high
priority).

### 8a. Prediction accuracy, now measured on modern co-folding models (pass-004)

pass-003 left an open caveat: its RMSD figures came from homology and ab initio
loop modelling, not from the co-folding stack we use. pass-004 closed it.

| Method | CDR-H3 RMSD | Source |
|---|---|---|
| **AlphaFold3**, 20 seeds, antibodies | **2.9 Å** median | PMID:40814020 |
| **AlphaFold3**, 20 seeds, nanobodies | **2.2 Å** median | PMID:40814020 |
| ABodyBuilder2, 34 recent antibodies | 2.81 Å | PMID:37248282 |
| AlphaFold-Multimer (same benchmark) | 2.90 Å | PMID:37248282 |
| NanoBodyBuilder2, nanobodies | 2.89 Å | PMID:37248282 |
| ABlooper, Rosetta Antibody Benchmark | 2.49 Å | PMID:35099535 |
| ABlooper, its 75% most confident | **2.05 Å** | PMID:35099535 |
| Homology modelling, 10–11 residue loops | 2.4 Å | PMID:19062174 |

Four independent methods spanning 2009–2025 land in a 2.4–2.9 Å band. That
convergence makes it a property of the problem, not of any one tool, so
**TH-011 moved to `high`**. Ranking designs on a 0.021 min_ipae gap, as EXP-001
did, is indefensible.

Two things survive:

- **Confidence-based filtering.** ABlooper's error drops 2.49 → 2.05 Å on its
  most confident 75%, so a model's own confidence carries signal. Discarding a
  bottom quartile is defensible; separating two close designs is not.
- **Seeds are the instrument.** AF3 needed **twenty** seeds for its median. We
  used one. IDEA-006 is rescoped accordingly: measure the spread first.

**Caveat we are carrying ourselves:** every figure above is unbound or apo loop
geometry. None of them measures interface-score reproducibility, which is what
we actually rank on. The inference from loop RMSD to min_ipae noise is ours,
not the papers'. It is recorded in TH-011's `evidence_against`.

**The VHH convergence.** AF3 predicts nanobody CDR-H3 better than antibody
CDR-H3 (2.2 vs 2.9 Å), and TEMPRO predicts sdAb Tm with a stated error bar
while no scFv equivalent exists. Two of the three scored properties are
therefore better covered for a VHH than for an scFv — hence TH-012 and the
promotion of IDEA-005. Honest counterweight, also recorded: ImmuneBuilder finds
*no* nanobody advantage (2.89 vs 2.81 Å), and a single domain gives up the
light-chain CDRs that carry 45% of trastuzumab's interface contacts.

## 9. How to rank: measured, and it changes the pipeline (EXP-003, pass-005)

**Structure scores do not rank binders on this target.** Real-vs-shuffled
discrimination, measured on HER2 systems over thousands of decoy pairs
(EXP-003, measured):

| Model | ipTM AUROC | topmodel AUROC |
|---|---|---|
| AF3 | 0.754 | 0.397 |
| **Boltz-2** | **0.645** | 0.443 |
| Chai-1 | 0.568 | 0.492 |

The topmodel score is below random **and inverted** — shuffled medians exceed
real ones. Boltz-2 ipTM has a real median of 0.911 against a shuffled median of
0.884, and **94.3% of 8,190 shuffled pairs score ≥0.7**. EXP-001's ipTM values
of 0.946 and 0.965 therefore sit inside the decoy distribution; they were never
evidence of binding (TH-013).

**A sequence model does rank them.** With Hamming ≤2 clusters held out together
and everything re-reported on the ≥3-mutation band `abguard` forces us into
(EXP-003, measured): binder classifier AUROC **0.915**, log10 KD ranker Spearman
**+0.622**, and a top-20 median true KD of **1.42 nM** against 86 nM across the
set — about 60×, recovering the 0.023 nM best binder (TH-014). Quote those
figures, not the ungrouped 0.99s.

**Per-position measured preferences** cover 10 of our 11 CDRH3 positions
(TH-015, measured): F at 99, **Q or E at 102** (log10 KD 0.15/0.18, the largest
gain in the loop), L at 106, V at 108, with wild-type already best at 104, 105
and 107. Caveat that keeps TH-015 at `medium`: the standout residues rest on
n=4–5 against n=104–128 for the wild-type residues they beat. And the dataset
is a 10-mer, so it says nothing about **Y109** — the one position TH-009's
recipe sacrifices.

**Two open gaps, stated rather than papered over:**

1. **De novo has no ranker at all.** TH-014 is label-dependent and labels exist
   only for CDRH3 variants on the trastuzumab framework. pass-005 searched for a
   validated interface-score screen and found none — no published work measuring
   whether ipTM or ipAE separates binders from non-binders. For de novo designs
   we currently have no defensible ranking method, only a filter.
2. **Nobody has validated the score we were using.** That the literature offers
   no decoy-control benchmark for ipTM screening is why IDEA-012 makes the
   control a standing rule: shuffle the pairings, score both sets, check they
   separate. It costs almost nothing and it is the difference between a number
   and a measurement.
