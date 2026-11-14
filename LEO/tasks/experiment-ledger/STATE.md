# experiment-ledger

**Branch:** `LEO-experiment-ledger` · **Started:** 2026-11-14 · **Agent:** Claude Opus 5

**Read both agents files:** [`../../../AGENTS.md`](../../../AGENTS.md) (root, shared) ☑ · [`../../AGENTS.md`](../../AGENTS.md) (Leo's) ☑

## Counts

| | |
|---|---|
| Experiments | 1 (`inconclusive` 1) |
| Theories | 8 active — `low` 2, `medium` 6, `high` 0 |
| Ideas | 7 open |
| Research passes | 1 |
| AMASS spend | 0 searches, $0.00 of the ~2,000-search team budget |

## What this task is

The bookkeeping layer for the design work: an append-only record of every
experiment, a falsifiable theory set that literature and results update, an idea
backlog, and an AMASS autoresearch loop that runs as a required step of the
cycle rather than a one-off review. It exists because 40% of the pitch score is
judgment and 20% is a reproducible repo — both are scored on written reasoning,
not on the designs alone. See [`PROMPT.md`](PROMPT.md) for the full cycle.

## Right now

**Autoresearch loop running** — one pass every 30 minutes until 18:00 local
(17:00 UTC), each pass applying its findings and committing to this branch.

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
| **Push + PR to `main`** | `git push` to `origin` returns 403: the authenticated account `leossgh` has no write access to `niccolocard99/ai_hackaton`, and `gh` is not installed | Either niccolocard99 adds `leossgh` as a collaborator, or install `gh` (`winget install GitHub.cli`) and fork to `leossgh/ai_hackaton` for a cross-fork PR. Commits are safe locally on `LEO-experiment-ledger` meanwhile |
| Theory confidence above `medium` | No measured result of our own yet; everything rests on literature | A design run with a recorded hypothesis (IDEA-006 is cheapest) |
| TH-007 / IDEA-003 (thermostability predictor) | All candidates are trained on proxies (TS50), not the Tm Adaptyv measures | A dedicated pass, then a decision |
| EXP-001 promotion from `inconclusive` | Single Boltz-2 seed, 2 of 4 designs refolded, novelty unchecked, `abguard` never run | IDEA-006 plus base validation |
| trialcore evidence | 20 cached records returned empty titles | Re-query or drop the core |

## Next, in order

1. Each pass: `--scope` the weakest theory, apply findings, commit.
2. Resolve IDEA-003 (thermostability predictor) — it blocks any S-tier claim.
3. Fold in the sibling [`../litreview-optimisation/`](../litreview-optimisation/) digest once that task finishes; it will supersede parts of `literature/REVIEW.md`.
4. Hand IDEA-001 (CDRH3 for binding + framework for Tm) to whoever has the GPU — it is the only idea that attacks two scored properties at once.

## Log

| Date | Event |
|---|---|
| 2026-11-14 | Branch created from `LEO` in an isolated git worktree, because the litreview agent holds the primary working tree and a branch switch there would have redirected its commits |
| 2026-11-14 | Seeded 8 theories and 7 ideas from the 30 cached AMASS queries; abstracts read directly, since `DIGEST.md` carries titles only |
| 2026-11-14 | pass-001 run at `--max-new 0` (zero spend). Found and fixed a parser bug that had dropped `query_terms` from every theory with no counter-evidence |
| 2026-11-14 | Loop started: 30-minute cadence until 18:00 local, full-apply mode, output to this branch with a PR to `main` |
