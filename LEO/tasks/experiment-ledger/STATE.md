# experiment-ledger

**Branch:** `LEO-experiment-ledger` · **Started:** 2026-11-14 · **Agent:** Claude Opus 5

**Read both agents files:** [`../../../AGENTS.md`](../../../AGENTS.md) (root, shared) ☑ · [`../../AGENTS.md`](../../AGENTS.md) (Leo's) ☑

## Counts

| | |
|---|---|
| Experiments | 2 (`worked` 1, `inconclusive` 1) |
| Theories | 10 active + 1 retired — `low` 0, `medium` 7, `high` 3 |
| Ideas | 9 open/lit-checked, 1 done |
| Research passes | 3 |
| AMASS spend | 5 searches, $0.25 of the ~2,000-search team budget (hard stop at 400) |
| Published | PR #2 **merged** into `main` at `27b6982`; later work goes out as a new PR |

## What this task is

The bookkeeping layer for the design work: an append-only record of every
experiment, a falsifiable theory set that literature and results update, an idea
backlog, and an AMASS autoresearch loop that runs as a required step of the
cycle rather than a one-off review. It exists because 40% of the pitch score is
judgment and 20% is a reproducible repo — both are scored on written reasoning,
not on the designs alone. See [`PROMPT.md`](PROMPT.md) for the full cycle.

## Right now

**Autoresearch loop running** — one pass every 30 minutes (at :07 and :37) until
18:00 local, each pass applying its findings, committing, and pushing to
`fork` (`leossgh/ai_hackaton`), which feeds **open PR #2** against
`niccolocard99/ai_hackaton:main`. Pushes go to `fork`, never `origin`:
`leossgh` has no write access upstream, so each pass extends the PR instead.

## Done so far

| What | Verified how | Commit |
|---|---|---|
| Ledger skeleton: CSV, theories, ideas, standing review, state | `python -I validate.py` passes | initial |
| 8 theories seeded from 30 cached AMASS queries, every claim citing a PMID | abstracts read directly from `cache/`, not from titles | initial |
| EXP-001 backfilled from `LEO/STATE.md` with its five reasons for being unrankable | cross-checked against `runs/her2/scored-boltz2` figures in that file | initial |
| `research_pass.py` runs a scoped pass, caches, tracks spend, writes pass files | pass-001 executed at `--max-new 0`, zero spend | initial |
| Field parser bug fixed: `\s*` swallowed the line after an empty field | 4 of 8 theories had silently lost `query_terms`; re-ran and all 8 parse | initial |

## Blocked

| Item | Blocker | Needed to unblock |
|---|---|---|
| Theory confidence above `medium` | No measured result of our own yet; everything rests on literature | A design run with a recorded hypothesis (IDEA-006 is cheapest) |
| TH-007 / IDEA-003 (thermostability predictor) | All candidates are trained on proxies (TS50), not the Tm Adaptyv measures | A dedicated pass, then a decision |
| EXP-001 promotion from `inconclusive` | Single Boltz-2 seed, 2 of 4 designs refolded, novelty unchecked, `abguard` never run | IDEA-006 plus base validation |
| trialcore evidence | 20 cached records returned empty titles | Re-query or drop the core |

## Next, in order

1. **Hand IDEA-008 to whoever has the GPU.** Substitute A106/M107/D108/Y109 and nothing else: 63.6% CDRH3 identity, track-eligible by arithmetic before any model runs, and the lowest constructible epitope risk. Rank it first unless a model objects.
2. Each pass: scan the repo for new committed results, `--scope` the weakest theory, apply, commit.
3. **IDEA-006 — add a second Boltz-2 seed.** Promoted by TH-011: it measures whether our ranking metric can separate designs at all, and rank order is the real submission output. Cheapest experiment, largest consequence.
4. IDEA-010 — energetics for Y109. The single assumption IDEA-008 rests on, and pass-003 proved the literature will not answer it.
4. IDEA-001 (CDRH3 for binding + framework for Tm) — still the only idea attacking two scored properties at once, and TH-005 is unaffected by EXP-002.
5. Resolve IDEA-003 (thermostability predictor); answer now depends on whether we submit a VHH.

## Log

| Date | Event |
|---|---|
| 2026-11-14 | Branch created from `LEO` in an isolated git worktree, because the litreview agent holds the primary working tree and a branch switch there would have redirected its commits |
| 2026-11-14 | Seeded 8 theories and 7 ideas from the 30 cached AMASS queries; abstracts read directly, since `DIGEST.md` carries titles only |
| 2026-11-14 | pass-001 run at `--max-new 0` (zero spend). Found and fixed a parser bug that had dropped `query_terms` from every theory with no counter-evidence |
| 2026-11-14 | Loop started: 30-minute cadence until 18:00 local, full-apply mode, output to this branch with a PR to `main` |
| 2026-11-14 | pass-002 (live, $0.10, 2 searches): found PMID:41564239, absent from the seeded queries. TH-007 `low` → `medium`; IDEA-003 split by format (`open` → `lit-checked`); `literature/REVIEW.md` §3 rewritten |
| 2026-11-14 | Rebased onto `origin/main` (3cbf4a7), which had moved 5 commits ahead. Noted that `main` lacks `LEO/.gitignore`, so the AMASS key is unprotected on a fresh clone — this branch carries the fix |
| 2026-11-14 | Push blocker resolved: `leossgh` has no write access to `niccolocard99/ai_hackaton`, so forked to `leossgh/ai_hackaton` and opened **PR #2** from the fork. Loop now pushes to `fork` each pass |
| 2026-11-14 | Repo scan of sibling branch `LEO-litreview-optimisation` (commits 9b45cdb, ae2cdef) found measured structural work. Recorded as **EXP-002**: TH-008 **retired**, TH-009 and TH-010 created at `high`, IDEA-004 `done`, IDEA-008/009/010 opened. First theory falsified by evidence rather than downgraded |
| 2026-11-14 | Cadence changed 30 min → 15 min, and a repo-scan step added to each pass so teammates' committed results feed the theories |
| 2026-11-14 | **PR #2 merged** into `main` at `27b6982` (46 files). Branch rebased onto the merge; subsequent passes go out as a new PR |
| 2026-11-14 | pass-003 ($0.15, 3 searches, scoped TH-009): found **nothing** on Y109 energetics — a negative result that escalates IDEA-010 to high. Side effects: TH-001 `medium` → `high` (PMID:29702641, 10-50 fold measured), and new **TH-011** on whether refold scores can separate close designs at all |
