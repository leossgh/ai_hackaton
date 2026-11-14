# Ideas — the backlog

Things we have not tested, so none are lost and none are tried twice. An idea
becomes an experiment by getting an `exp_id`; it dies by getting
`status: dropped` **with a reason**, which is itself a result worth keeping.

`status`: `open` | `lit-checked` | `running` | `done` | `dropped`.
`source`: `literature` (a research pass raised it) | `experiment` (a result
suggested it) | `team`.

---

### IDEA-001 — Split the design budget: CDRH3 diversity for binding, framework mutations for Tm, in the same molecule

- **status:** open
- **priority:** high
- **tests:** TH-005; TH-002
- **cost:** one design run on `antibody-2026-10-30` (framework-capable) plus one on `her2-novel-2026-11-09`, then refold both
- **source:** literature
- **evidence:** PMID:40653772
- **notes:** The HER2 images only redesign CDRH3, so the framework half needs `antibody-2026-10-30`. This is the only idea here that attacks two scored properties at once, which is what S-tier requires.

### IDEA-002 — Cap arginine content in designed CDRH3 and check whether it costs predicted affinity

- **status:** open
- **priority:** medium
- **tests:** TH-003
- **cost:** post-hoc filter over an existing design set, no GPU
- **source:** literature
- **evidence:** PMID:28778924
- **notes:** Cheap — it is a filter over designs we already have. If high-Arg designs dominate the top of the min_ipae ranking, that is a warning that the ranking is rewarding non-specific binding.

### IDEA-003 — Choose the thermostability predictor and commit to it

- **status:** lit-checked
- **priority:** high
- **tests:** TH-007
- **cost:** one research pass plus setup; no GPU
- **source:** team
- **evidence:** PMID:36683173; PMID:39154093; PMID:41564239
- **query_terms:** scFv Tm predictor validation benchmark antibody fragment; nanobody thermostability deep learning screening criterion
- **notes:** Named as an open decision in `AGENTS.md`. Two of the three scored properties have no built-in proxy and this is the cheaper one to fix. Blocking for any S-tier claim. **pass-002 split this in two:** for a **VHH** submission use TEMPRO (PMID:39154093, MAE 4.03 °C) cross-checked against the `Tm > 65 °C` criterion in PMID:41564239 — both sdAb-specific and both reporting on Tm directly. For an **scFv** there is still no Tm-trained predictor; the best available is the TS50-trained pair in PMID:36683173, which recovered 18 of 20 known thermostable positions on a held-out mAb. Recommendation: if we submit a VHH, this decision is effectively closed; if scFv only, flag the predictor as a known weakness in the pitch rather than overclaiming.

### IDEA-004 — Extract per-residue energetic contributions at the 1N8Z interface, not just the contact list

- **status:** done
- **priority:** medium
- **tests:** TH-009; TH-010
- **cost:** structure analysis; `bsa_1n8z.py` in the litreview folder has started on buried surface area
- **source:** literature
- **evidence:** PMID:12610629; EXP-002
- **notes:** A contact is not a hot spot. Without this, "preserves the epitope" is an assertion. The sibling task already computes BSA, so fold that in rather than redoing it. **Done by EXP-002** (sibling branch, commits 9b45cdb and ae2cdef): per-position contact geometry across 8 structures. It retired TH-008 and produced TH-009 and TH-010. Energetics are still missing — a contact frequency is not a hot spot — so the remaining half is IDEA-010.

### IDEA-005 — Submit a VHH alongside the scFv designs to hedge the track split

- **status:** open
- **priority:** high
- **tests:** TH-006; TH-012
- **cost:** one design run plus refold
- **source:** literature
- **evidence:** PMID:37632647; PMID:39154093; PMID:40814020
- **query_terms:** anti-HER2 nanobody VHH design affinity epitope; single domain antibody cell-free expression yield
- **notes:** The two tracks have separate prize pots and a team may submit any mix. A VHH is short, so it is comfortably inside the 250 aa limit and has no VH/VL pairing to get wrong. **Promoted to high by pass-004 (TH-012):** a VHH is the only format where we can both predict thermostability (TEMPRO, sdAb-only, MAE 4.03 °C) and claim better structure-prediction accuracy (AF3 2.2 Å vs 2.9 Å). Of the three scored properties, that covers the two with no built-in proxy. Counter-consideration recorded in TH-012: a single domain forgoes the light-chain CDRs that carry 45% of trastuzumab's interface contacts.

### IDEA-006 — Establish the seed-to-seed error bar on min_ipae before ranking anything on it

- **status:** open
- **priority:** high
- **tests:** TH-001; TH-011
- **cost:** two refold runs on the shared H100
- **source:** experiment
- **evidence:** EXP-001
- **query_terms:** folding model seed variance interface score reproducibility; antibody antigen co-folding template confidence metric
- **notes:** EXP-001 ranked on a single seed and refolded only 2 of 4 designs. The gap was 0.021 min_ipae (0.310 vs 0.331) — inside the noise one seed can tell us about. **pass-003 raised the stakes** (TH-011: predicted H3 conformation for an 11-residue loop is good to only ~2 Å), and **pass-004 rescoped this idea**: PMID:40814020 needed **twenty** seeds to establish AlphaFold3's median CDR-H3 accuracy. Two seeds would not give an error bar either. So this is no longer "add a second seed" — it is: refold one design across as many Boltz-2 seeds as the shared H100 allows (5 at minimum, more if cheap), report the **spread** of min_ipae, and only then decide whether any gap between designs is real. Rank order is the submission output, so a metric without an error bar is the single largest hole in the pipeline. Runs on one design, so it is cheap.

### IDEA-007 — Check whether any of our designs sit near a claimed patent sequence

- **status:** open
- **priority:** low
- **tests:**
- **cost:** one patentcore pass
- **source:** literature
- **evidence:**
- **query_terms:** patent: anti-HER2 antibody CDR sequence claim variant; patent: trastuzumab biosimilar CDRH3 sequence claim; patent: computationally designed antibody CDR freedom to operate
- **notes:** The digest already shows a crowded field — `Anti-HER2 antibody variants`, `High-affinity fully-humanized anti-Her2 monoclonal antibody` and ~36 more. Not a hard filter for the hackathon, but "path to value" is 20% of the pitch and freedom-to-operate is part of that answer.

### IDEA-008 — Design the minimal-risk CDRH3 variant: substitute A106, M107, D108, Y109 and nothing else

- **status:** open
- **priority:** high
- **tests:** TH-009
- **cost:** one `her2-novel-2026-11-09` design run with CDRH3 positions constrained, then refold and score
- **source:** experiment
- **evidence:** EXP-002
- **query_terms:** CDRH3 position restricted library design epitope retention; conservative CDR substitution affinity retention antibody
- **notes:** The one design in the backlog whose track eligibility is arithmetically guaranteed before any model runs: 4 substitutions on an 11-residue CDRH3 gives 63.6% identity, clearing the `<70%` gate, while sacrificing only Y109, which contacts HER2 in 1 of 8 structures. Every other contacting position is spared. This is the design to rank first unless a model says otherwise, because its epitope risk is the lowest we can construct and we can defend the choice position by position in the pitch.

### IDEA-009 — Redesign H2 or L3 with `antibody-2026-10-30` instead of chasing CDRH3

- **status:** open
- **priority:** medium
- **tests:** TH-010
- **cost:** one design run on a weight we have not used yet, plus refold; higher risk of wasted GPU
- **source:** experiment
- **evidence:** EXP-002
- **query_terms:** CDR H2 redesign affinity antibody engineering; light chain CDR L3 contribution antigen binding affinity maturation
- **notes:** H2 carries 14-47% of interface contacts and L3 11-29%, comparable to or exceeding H3's 12-34%. All four HER2 weights redesign CDRH3 only, so the obvious tool is aimed at a minority of the interface. `antibody-2026-10-30` is the only weight that can touch other CDRs. Risk: it is not HER2-tuned, so novelty and interface quality are unproven for this target, and the `<70% CDRH3 identity` gate still has to be met by CDRH3 changes regardless. Treat as the exploratory slot, not a core submission.

### IDEA-010 — Get per-residue energetics for the CDRH3 contacts, not just contact frequency

- **status:** open
- **priority:** high
- **tests:** TH-009
- **cost:** computational alanine scan or MM-GBSA style decomposition on 1N8Z; no GPU needed for the cheap version
- **source:** experiment
- **evidence:** EXP-002
- **query_terms:** computational alanine scanning antibody antigen interface energy decomposition; MM-GBSA per residue binding free energy antibody
- **notes:** TH-009's weak point, stated in its own `evidence_against`: contact frequency across crystal structures is geometry, not energy. Y109 contacts in only 1 of 8 structures, but a rare contact can still be energetically load-bearing, and Y109 is the one position the IDEA-008 recipe sacrifices. If an energetic estimate says Y109 is a hot spot, IDEA-008 needs a different fourth substitution — and there is no safe alternative, which would make the tension in TH-009 sharper rather than looser.
