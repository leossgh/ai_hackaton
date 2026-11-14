# Measured trastuzumab–HER2 interface, computed from PDB 1N8Z

**This is measurement, not literature mining.** Every number below is computed from the deposited
coordinates of **PDB 1N8Z** — "Crystal structure of extracellular domain of human HER2 complexed
with Herceptin Fab", 2.5 Å — by [`interface_1n8z.py`](../interface_1n8z.py) and
[`paratope_budget.py`](../paratope_budget.py). Reproduce with:

```bash
curl -o 1n8z.cif https://files.rcsb.org/download/1N8Z.cif
python interface_1n8z.py 1n8z.cif 4.5 > interface_1n8z.txt
python paratope_budget.py interface_1n8z.txt
```

**Method:** heavy-atom contacts ≤ 4.5 Å, first model, standard residues. Chains: **A** = light chain
(214 res), **B** = heavy chain (220 res), **C** = HER2 ECD (581 res, numbered 1–607).
**Numbering below is 1N8Z author numbering (sequential), NOT Kabat.** CDRs were located by substring
search on the deposited sequence, so no numbering scheme is assumed.

This closes the gap that all five literature passes flagged as unanswerable: *"no trastuzumab
paratope residue list, no per-CDR energy budget, nothing supporting or refuting the 70% threshold."*

## 1. Trastuzumab CDR sequences (as deposited)

| CDR | Chain | Residues | Len | Sequence |
|---|---|---|---|---|
| **H3** | B | **99–109** | **11** | **`WGGDGFYAMDY`** |
| H2 | B | 50–65 | 16 | `RIYPTNGYTRYADSVK` |
| H1 | B | 31–35 | 5 | `DTYIH` |
| L1 | A | 24–34 | 11 | `RASQDVNTAVA` |
| L2 | A | 50–56 | 7 | `SASFLYS` |
| L3 | A | 89–97 | 9 | `QQHYTTPPT` |

## 2. The per-CDR interface budget

42 antibody–HER2 residue contact pairs, 20 paratope residues.

| CDR | Contact pairs | Share | Contacting residues |
|---|---|---|---|
| **H3** | 11 | **26%** | TRP99, GLY103, PHE104, TYR105 |
| H2 | 10 | 24% | ARG50, TYR52, TYR57, THR58, ARG59 |
| L3 | 8 | 19% | HIS91, TYR92, THR93, THR94 |
| L1 | 7 | 17% | ASP28, ASN30, THR31, ALA32 |
| L2 | 4 | 10% | SER50, PHE53 |
| H1 | 2 | 5% | TYR33 |

**Heavy-chain CDRs 55% · light-chain CDRs 45%.**

**CDRH3 is the largest single contributor but carries only about a quarter of the interface.**
74% of contacts come from the other five CDRs, and the light chain alone carries 45%. This is the
quantitative version of the inference drawn from the ~50 aa epitope: **the unchanged CDRs are a
substantial anchor, so a CDRH3 rewrite is not betting the whole paratope.**

*Caveat: contact count is a geometric proxy, not an energy. A single buried hydrogen bond can outweigh
several van der Waals contacts. Treat these shares as "how much of the interface geometry is at risk",
not as ΔΔG.*

## 3. THE DESIGN UNLOCK: only 4 of 11 CDRH3 positions touch HER2

| Pos | aa | HER2 contact | Partners (min heavy-atom distance, Å) |
|---|---|---|---|
| 99 | W | **contact** | PHE573 4.05, PRO572 4.14 |
| 100 | G | free | — |
| 101 | G | free | — |
| 102 | D | free | — |
| 103 | G | **contact** | **LYS593 2.42**, ASP570 3.66, ILE591 3.74, PRO579 4.50 |
| 104 | F | **contact** | LYS593 4.27 |
| 105 | Y | **contact** | PRO571 3.32, PHE573 3.44, ASP570 3.50, PRO572 4.00 |
| 106 | A | free | — |
| 107 | M | free | — |
| 108 | D | free | — |
| 109 | Y | free | — |

**Identity arithmetic:** CDRH3 is 11 residues, so k substitutions leave (11−k)/11 identity.
k=3 → 72.7% (**fails**, still ≥70%). **k=4 → 63.6% (passes).**

**Contact-free positions available: 7 (G100, G101, D102, A106, M107, D108, Y109).
Substitutions required: 4.**

> **⇒ `<70%` CDRH3 identity is reachable by mutating contact-free positions alone — 4 of 7 available,
> without touching a single HER2-contacting residue.**

This is the central design result. The track rule that looked like a forced trade-off between
novelty and binding is, on this structure, **satisfiable without sacrificing any measured contact.**

**Load-bearing CDRH3 residues, in order of risk if changed:**
1. **GLY103** — 4 contacts including **the shortest contact in the entire interface (2.42 Å to
   LYS593)**. A glycine making the closest approach means minimal side-chain room: almost any
   substitution adds bulk where there is none to spare. **Treat as untouchable.**
2. **TYR105** — 4 contacts (D570, P571, P572, F573). Aromatic packing against a proline-rich surface.
3. **TRP99** — 2 contacts, and it is the conserved CDRH3-base tryptophan that
   [the loop-design literature](04-prediction-tools-and-developability.md) says extends the kinked
   β-bulge via an H-bond and CH/π interaction. **Structural and contact role — untouchable.**
4. **PHE104** — 1 contact (K593 4.27 Å), the weakest of the four. The most plausible candidate if a
   contacting position must change.

## 4. HER2 epitope (measured)

19 residues in contact, spanning **557–605** — **49 residues end to end for 19 actual contacts, i.e.
strongly discontinuous:**

`PRO557, GLU558, ASP560, GLN561, LYS569, ASP570, PRO571, PRO572, PHE573, PRO579, ILE591, LYS593,
ASP596, GLU598, ALA600, GLN602, PRO603, CYS604, PRO605`

**This independently confirms the "discontinuous epitope spanning nearly 50 amino acids" claim** that
previously rested on a single un-peer-reviewed conference abstract
([findings 02](02-epitope-preservation.md)). Now measured.

**Division of labour across the epitope:**
- **Heavy chain** engages the **557–593** half (P557, E558, D560, Q561, D570, P571, P572, F573, P579, I591, K593).
- **Light chain** engages the **560–605** half (D560, K569, P571, P572, D596, E598, A600, Q602, P603, C604, P605).
- **ASP560, PRO571 and PRO572 are contacted by both chains** — shared hot spots.
- The epitope is **proline-rich** (P557, P571, P572, P579, P603, P605) and **charge-dense**
  (D560, K569, D570, K593, D596, E598, E558). This corroborates the "electrostatics-dominant" finding
  (pmid 23955267) and argues strongly for **preserving net charge and polar character** in any
  rewritten CDRH3 face.

## 5. ⚠ A published residue list that does not survive checking

[findings 02](02-epitope-preservation.md) recorded HER2 contact loops at **991–995, 1004–1007 and
1027–1037** from an MM-GBSA conference abstract (doi 10.1096/fasebj.31.1_supplement.775.23), which
claimed to analyse 1N8Z.

**Those numbers are not compatible with this structure.** 1N8Z's HER2 chain is numbered 1–607, and the
measured interface is 557–605. Residues 991–1037 lie far beyond the extracellular domain — in
full-length HER2 (1255 aa) that region is intracellular/kinase. Either the abstract used a different
numbering convention it did not state, or the numbers are wrong.

**Do not use 991–995 / 1004–1007 / 1027–1037 in any design or pitch.** Use the measured 557–605 set.
This is exactly why that finding was flagged "computational, conference abstract, verify".

## 6. What this still does not give us

- **No energies.** Contact counts are geometry. A per-residue ΔΔG budget needs FoldX/Rosetta/MM-GBSA
  on these coordinates, or an experimental alanine scan. **This is the obvious next computation**, and
  it can run on the structure we now have.
- **No buried surface area.** The script counts contacts, not BSA. Adding an SASA calculation would
  give per-CDR Å² — a better proxy for energetic weight than contact count.
- **One crystal structure, one conformation.** CDR loops interconvert on µs–ms timescales
  (pmid 32264741), so a single pose understates the ensemble. Higher-resolution cryo-EM coordinates
  exist (**3.1–3.2 Å**, pmid 41538393) and should be cross-checked.
- ~~The 4.5 Å cutoff is a choice.~~ **Checked — see §7. The conclusion is robust.**
- **Does not prove the epitope survives.** Preserving contacts is necessary, not sufficient — the
  rewritten loop must still fold and dock the same way, which only the competition assay settles.

## 7. Cutoff sensitivity — the conclusion is robust

The 4.5 Å cutoff is a choice, so the whole analysis was re-run at 4.0, 5.0 and 5.5 Å.

| Cutoff | Pairs | CDRH3 share | CDRH3 contacting positions | Contact-free positions |
|---|---|---|---|---|
| 4.0 Å | 32 | 22% | G103, Y105 | **9** |
| **4.5 Å** | **42** | **26%** | W99, G103, F104, Y105 | **7** |
| 5.0 Å | 47 | 26% | W99, G103, F104, Y105 | **7** |
| 5.5 Å | 61 | 30% | W99, **D102**, G103, F104, Y105 | **6** |

**At every cutoff tested, at least 6 contact-free CDRH3 positions remain and only 4 are needed.**
The design conclusion does not depend on the cutoff choice.

**Robust free set — contact-free at *all* cutoffs from 4.0 to 5.5 Å (6 positions):**

> ### `G100, G101, A106, M107, D108, Y109`

**Use these.** `D102` is contact-free at 4.5 Å but picks up contacts at 5.5 Å, so it is the one
position to avoid despite appearing free in the headline analysis. Four substitutions drawn from the
six robust positions give **63.6% CDRH3 identity with no measured HER2 contact disturbed at any
cutoff.**

Other stable observations across cutoffs:
- **CDRH3's share grows with cutoff (22% → 30%)** — it sits slightly further from HER2 than H2/L3 on
  average, consistent with its contacts being peripheral rather than buried.
- **H3 and H2 are consistently the top two heavy-chain contributors**; L1 and L3 trade places.
- **Heavy:light stays near 50:50 to 55:45** at every cutoff — the light chain's anchor role is real.
- At ≥5.0 Å, framework residues appear (TYR49, and ARG66 at 5.5 Å) — worth noting as near-interface
  positions that should not be touched by framework stability engineering.
