# Generating de novo-track trastuzumab VHH variants from a scored/ranked list

Anders folder, 14 Nov 2026. This document is the strategy; `vhh_variants.py` is the
implementation; `demo/` holds two end-to-end validation runs whose outputs all PASS
`NICCOLO/scripts/check_denovo.py`.

Everything about the gate below is a **measured** fact from this VM, not a reading of
the task PDF: see `../NICCOLO/denovo/GATE_NOTES.md` (how `abguard` really computes
identity and CDRH3 novelty) and `../NICCOLO/denovo/scaffolds/SCAFFOLDS.md` (4530
random-CDR fills scored with the real gate).

## 0. The gate in one paragraph

- **Identity** is a pooled Levenshtein ratio over the immunum IMGT Fv against
  **trastuzumab's 120-aa VH only** (a VHH is scored on its heavy chain alone; no VL
  term). De novo needs **< 0.70 strictly** — a design measuring exactly 0.700000 was
  classed `novel` and failed.
- **CDRH3 novelty** is Levenshtein **≥ 2 edits from all 610,109 reference loops**;
  trastuzumab's own `SRWGGDGFYAMDY` is one more reference row, and the 524k FACS
  variants densely cover its single-mutant neighbourhoods. Anything within ~2 edits
  of a published HER2 loop is dead on arrival.
- **Hard checks:** canonical AAs, ≤ 250 aa, no unpaired cysteines, numbering
  confidence ≥ 0.1, exactly one domain for a VHH, unique ids.
- **Margins used here** (from `../NICCOLO/denovo/gate.py`): identity ≤ 0.62 and CDRH3
  ≥ 4 edits from trastuzumab *and* the whole reference set — so a re-numbering, a
  refold or a reference refresh cannot flip the verdict.

## 1. What the ranked list is allowed to mean

The input is any CSV with `sequence_id, heavy_sequence` plus, optionally, a score
column (`min_ipae`, `iptm`, `binder_plddt`, anything). Three rules:

1. **The score picks parents and builds the CDR position matrix. Nothing more.**
   Variants inherit the parent score as a *prior* and must be re-scored by whatever
   oracle produced the list. The submission CSV never claims the inherited score is
   evidence.
2. **The SPR pre-filter does not apply here.** `../NICCOLO/eda/prefilter.py` was
   trained on 732 variants that all share trastuzumab's VH/VL framework — its
   AUROC 0.927 / Spearman +0.687 is measured on that framework only, and the ranker
   has **no demonstrated power ≥ 5 substitutions from its training set**. A VHH on a
   different framework is exactly that regime. Do not feed VHH variants to it.
3. **Fold confidence is a weak prior at best.** In the CDRH3-optimisation regime
   every fold metric landed at chance and ipTM ≥ 0.7 passed 100% of true
   non-binders (n=60/180, Boltz-2 and Protenix). For de novo whole-binder redesign
   the published benchmark gives AF3 ipTM AUROC 0.75, Boltz-2 0.64 — real but weak.
   Use as one input to ordering, never as a gate.

## 2. The strategies

All four are implemented and selectable (`--strategies recombine,extend,mutate,graft`).
Each variant carries its strategy, parents and inherited score in `variants_meta.csv`,
and the final list is re-verified with the official checker.

### S1 — CDR recombination onto the lead framework

Framework from the best-ranked parent; each CDR drawn independently from the top-K
pool. Combines loop content the generator never sampled together, while every piece
has ranked parentage.

- Buys: new CDR combinations at zero framework risk; identity moves only via the CDRs.
- Risk: **cannot rescue a parent whose CDR3 is prior art** — it ships whole CDR3s.
  Measured: 0/6 rescues in the adversarial run.
- Use when: several top parents already clear the gate; you want combinational
  coverage around them.

### S2 — CDR3 apex extension (+4/+6/+8 residues, midpoint insertion)

The single most measured lever on this VM: identity is a Levenshtein ratio whose
denominator only grows with loop length, and each inserted residue is one guaranteed
edit against trastuzumab's Fv and against every reference loop. The scaffold study
found **+12–16 residues** is what clears even an *own-parent* 70% bar at a kept
framework (so ~29–35-residue CDR3s), and trastuzumab identity only improves as CDR3
grows — no trade-off except loop designability.

- Buys: identity margin, CDRH3 distance margin, and a longer apical surface (camelid
  CDR3s routinely reach this length and often carry the paratope).
- Risk: very long loops stress numbering and designability; capped here at 40 residues
  (numbering confidence was measured to hold through +20 extensions).
- Use when: parents sit near either margin, or you need to pull a prior-art-adjacent
  CDR3 away from the reference set. **The only strategy that rescued published-CDR
  parents (12/18)** in the adversarial run.

### S3 — PSSM-guided CDR point diversification

1–3 substitutions per variant (CDR3-weighted), replacement residues sampled from a
per-position tally over the ranked list's top parents, backstopped by a CDR-like
composition. Cysteine is never introduced or removed by construction (CDR alphabet
excludes C), so framework cysteine parity is preserved.

- Buys: local walk around proven-ish loops; every substitution also lowers identity.
- Risk: **cannot rescue prior-art CDR3s** (1–2 edits leave it within the dense
  single-mutant neighbourhoods; measured 0/18).
- Use when: parents are novel and safe, and the ranked list is deep enough that the
  PSSM means something (≥ ~10 parents).

### S4 — Scaffold hopping (graft onto a different measured VHH framework)

The five frameworks marked safe-with-extended-CDR3 in the scaffold study are embedded
in the tool (`vhh_6XYF_A`, `vhh_8E2N_B`, `vhh_6JB9_A`, `vhh_8CDS_A`, `vhh_5VLV_A`).
Each hop grafts a parent's CDRs onto a different real, numbered, obscure-parent
framework.

- Buys: structural diversity per hit; a different FR is worth ~30–40 edits of
  identity headroom; trastuzumab identities of these frameworks measure 52–59%.
- Risk: CDR-framework compatibility (a VHH CDR3 that packs against FR2 in one
  scaffold may not in another) — a refold question, not a gate question; numbering
  confidence stays high because every framework is a real VHH.
- Use when: building a submission family around one hit, or pushing identity margin
  down without touching loop content.

### S5 — Consensus backcross (documented, not implemented)

Build a per-position consensus of the top-N, then backcross divergent positions to
the best parent's residues. Worth it only with a much deeper ranked list (RFD4 at
hundreds of replicates); with 6 parents it degenerates to S1. Re-open if the campaign
produces ≥ 50 scored parents.

## 3. Screening cascade — cheapest first, and never rank before novelty

1. **Free rules** on every candidate: canonical AAs, ≤ 250 aa, even cysteine count,
   uniqueness. (Done in-process; drops cost nothing.)
2. **Real-gate pre-screen with margins**: `abguard.annotate.annotate` with the full
   bundled reference (the same code path `check_denovo.py` uses) at ~0.25 s/design —
   identity ≤ 0.62, CDRH3 ≥ 4 edits from trastuzumab and the reference set, no hard
   errors, de novo class.
3. **Official verdict**: `NICCOLO/scripts/check_denovo.py --strict-exit` on the final
   table. The pre-screen is a strict subset of this by construction, so the official
   run is a confirmation, not a surprise.

The her2-2026-11-07 lesson applies to the *variant* stage too: filter for novelty
before ranking, never after — the best-scoring variants are exactly the ones closest
to prior art.

## 4. Evidence: the two demo runs (committed under `demo/`)

| run | parents | candidates | pre-screen | official `check_denovo.py` |
|---|---|---|---|---|
| `demo/gen` (synthetic CDRs on 5 frameworks, parents already novel) | 12 (top 6 used) | 52 | **52/52** | **20/20 PASS, exit 0** |
| `demo/gen_real` (real published CDRs; **all 6 parents fail the gate**) | 6 | 52 | 14/52 | **14/14 PASS, exit 0** |

The adversarial run is the interesting one — per-strategy rescue rates for prior-art
parents: `extend 12/18`, `graft 2/10`, `mutate 0/18`, `recombine 0/6`. The tool
emitted only the passers and the official checker confirmed every one; nothing that
failed the pre-screen reached the submission table.

## 5. Pitfalls the tool encodes so you don't have to remember them

- **Cysteine parity**: the CDR alphabet excludes C, so parity stays decided by the
  two conserved framework cysteines. (The one scaffold in the library with a
  built-in odd cysteine, `vhh_5IVN_A`, is simply not embedded.)
- **CDRH3 distance is Levenshtein, not Hamming** — a length change is an edit, which
  is why S2 buys distance so cheaply.
- **Identity 0.70 fails** (measured), so the internal ceiling is 0.62.
- **Own-parent identity is not enforced by abguard** — it measures trastuzumab only.
  The team's own risk bar (see SCAFFOLDS.md) prefers obscure-parent frameworks and
  extended CDR3s; both are built into the defaults here.
- **Only 4 designs are guaranteed tested** and the submission list caps at 20: the
  generator defaults to `--max-output 20` and orders by inherited score, but the
  *ranked list* is the real deliverable — re-order after your own oracle, and record
  the reasoning per shortlisted design (40% of pitch day is judgment).

## 6. What this deliberately does not do

- No binding, epitope or thermostability prediction for de novo VHHs — no validated
  oracle exists on this VM (`../NICCOLO/PIPELINE.md` §6: epitope preservation has no
  predictor at all; CDRH3 cannot move NanoMelt Tm beyond its error bar).
- No expression/developability scoring (Aggrescan 3D, SoluProt, NetSolP,
  ProteinMPNN-soluble are not installed).
- No GPU stage — this is the cheap loop. The expensive part (RFD4 re-design /
  refold of the shortlist) stays where it is, on the shared H100, one job at a time.

## 7. Run it

```bash
PY=/home/hackathon/.venvs/abguard/bin/python   # the interpreter that has abguard

# synthetic dry run (reproduces demo/gen)
$PY ANDERS/vhh_variants.py demo ANDERS/demo --seed 1
$PY ANDERS/vhh_variants.py generate ANDERS/demo/ranked.csv -o ANDERS/demo/gen --seed 1

# real use: your scored/ranked list, one command
$PY ANDERS/vhh_variants.py generate runs/<your-run>/scored.csv -o ANDERS/out \
    --score-col min_ipae --lower-is-better --parents-top 6 --max-output 20

# re-check any submission table with the official gate
$PY ANDERS/vhh_variants.py check DESIGNS.csv -o report.csv
```

Outputs per run: `variants.csv` (the 5-column submission table), `variants_meta.csv`
(strategy, parents, inherited score, measured identity/CDRH3 distances — the
provenance record AGENTS.md requires), `variants_denovo_report.csv` (the official
checker's report, verbatim).
