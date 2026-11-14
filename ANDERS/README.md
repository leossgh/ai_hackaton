# ANDERS — de novo VHH variant generation

Branch `anders`, synced with `origin/main` at `0097248` (merge on 14 Nov 2026) before
any work started. Everything for this lane lives in this folder; other folders were
read as evidence only, never written.

## What is here

| path | what |
|---|---|
| `STRATEGIES.md` | the strategy document: how to turn a scored/ranked list into de-novo-track VHH variants, and why each choice is what it is |
| `vhh_variants.py` | the tool: `generate` / `demo` / `check`. Generates variants (recombine, extend, mutate, graft), pre-screens with abguard at safety margins, then runs the official `NICCOLO/scripts/check_denovo.py` on the result |
| `demo/ranked.csv` | 12 synthetic VHH parents (CDR-like random fills on the five measured-safe frameworks) |
| `demo/gen/` | output of the happy-path run: 52/52 pre-screen pass, 20/20 official PASS |
| `demo/ranked_real.csv` | adversarial input: 6 real scaffolds with published CDRs — all parents FAIL the de novo gate |
| `demo/gen_real/` | adversarial output: only 14/52 survive pre-screening, 14/14 official PASS |
| `out/` | default target for real runs (empty; next run writes here) |

## Reproduce the demo

```bash
PY=/home/hackathon/.venvs/abguard/bin/python
$PY ANDERS/vhh_variants.py demo ANDERS/demo --seed 1
$PY ANDERS/vhh_variants.py generate ANDERS/demo/ranked.csv -o ANDERS/demo/gen --seed 1
$PY ANDERS/vhh_variants.py generate ANDERS/demo/ranked_real.csv -o ANDERS/demo/gen_real --seed 7
```

## Run notes (provenance, per AGENTS.md)

- **2026-11-14, ~14:00–14:30 Oslo, seed 1** — `demo/gen`: synthetic parents on
  `vhh_6XYF_A / vhh_8E2N_B / vhh_6JB9_A / vhh_8CDS_A / vhh_5VLV_A` frameworks, CDR3
  at recommended+0..4 lengths, strategies `recombine,extend,mutate,graft`, parents-top 6,
  margins identity ≤ 0.62 / CDRH3 ≥ 4. 52 unique candidates, 52/52 pre-screen pass,
  capped at 20 by inherited score, official `check_denovo.py` 20/20 PASS, exit 0.
- **2026-11-14, ~14:30 Oslo, seed 7** — `demo/gen_real`: real published scaffolds as
  parents (all fail the gate: published CDR3s are reference rows; caplacizumab fails
  the 0.62 identity margin). 52 candidates; rescue rates `extend 12/18, graft 2/10,
  mutate 0/18, recombine 0/6`; 14 kept, official 14/14 PASS, exit 0.
- No GPU stage, no model images, no network calls. Inputs to the official checker
  are the committed CSVs; everything else is deterministic given `--seed`.
- Frameworks embedded in the tool are transcribed from
  `../NICCOLO/denovo/scaffolds/SCAFFOLDS.md` (measured there with the real gate);
  gate semantics from `../NICCOLO/denovo/GATE_NOTES.md`. Both are NICCOLO's
  measurements — this folder depends on them but does not re-derive them.

## Limits (do not read past these)

- Passing `check_denovo.py` is the entry ticket, not evidence of binding, epitope
  preservation or thermostability — see `../NICCOLO/PIPELINE.md` §6.
- Inherited parent scores are priors for ordering only; re-rank the shortlist with
  the team's own oracle before submitting.
- The tool ranks variants by inherited parent score when capping to 20; that is a
  placeholder ordering, explicitly not a validated ranker.
