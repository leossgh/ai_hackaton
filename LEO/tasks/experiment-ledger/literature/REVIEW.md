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
