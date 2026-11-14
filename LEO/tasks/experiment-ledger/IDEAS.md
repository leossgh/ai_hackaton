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

- **status:** open
- **priority:** medium
- **tests:** TH-008
- **cost:** structure analysis; `bsa_1n8z.py` in the litreview folder has started on buried surface area
- **source:** literature
- **evidence:** PMID:12610629
- **notes:** A contact is not a hot spot. Without this, "preserves the epitope" is an assertion. The sibling task already computes BSA, so fold that in rather than redoing it.

### IDEA-005 — Submit a VHH alongside the scFv designs to hedge the track split

- **status:** open
- **priority:** medium
- **tests:** TH-006
- **cost:** one design run plus refold
- **source:** literature
- **evidence:** PMID:37632647
- **notes:** The two tracks have separate prize pots and a team may submit any mix. A VHH is short, so it is comfortably inside the 250 aa limit and has no VH/VL pairing to get wrong.

### IDEA-006 — Re-rank the existing 4 HER2 designs after a second Boltz-2 seed

- **status:** open
- **priority:** high
- **tests:** TH-001
- **cost:** two refold runs on the shared H100
- **source:** experiment
- **evidence:** EXP-001
- **notes:** EXP-001 ranked on a single seed and refolded only 2 of 4 designs. The ranking gap between the two was small (min iPAE 0.310 vs 0.331), which is inside the noise one seed can tell us about. Cheapest way to firm up the one ranking we already have.

### IDEA-007 — Check whether any of our designs sit near a claimed patent sequence

- **status:** open
- **priority:** low
- **tests:**
- **cost:** one patentcore pass
- **source:** literature
- **evidence:**
- **query_terms:** patent: anti-HER2 antibody CDR sequence claim variant; patent: trastuzumab biosimilar CDRH3 sequence claim; patent: computationally designed antibody CDR freedom to operate
- **notes:** The digest already shows a crowded field — `Anti-HER2 antibody variants`, `High-affinity fully-humanized anti-Her2 monoclonal antibody` and ~36 more. Not a hard filter for the hackathon, but "path to value" is 20% of the pitch and freedom-to-operate is part of that answer.
