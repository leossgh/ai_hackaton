# Task: experiment ledger + AMASS autoresearch loop

The bookkeeping layer for our design work: a record of every experiment we run,
what we learned, a living set of theories, and an AMASS literature step that
feeds both. Nothing here runs a model or designs a sequence — it is the memory
the design work writes into, and the loop that keeps that memory current.

## Why this exists

Only ~4 designs get tested, and 40% of the pitch score is judgment — the
reasoning behind the molecules we chose. That reasoning has to be written down as
we go, not reconstructed on Saturday night. This folder is that write-down: the
audit trail from "the literature says X" to "we believed X" to "we tested X" to
"X was wrong, here is why".

## The cycle — these are the steps, in this order

Every experiment goes through all six. The literature step is not optional and
not a one-off at the start; it runs before we spend GPU time and again after we
get a result.

1. **Pick** — take an idea from [`IDEAS.md`](IDEAS.md), or add one.
2. **Literature check (AMASS autoresearch).** Before running anything: has this
   been done, measured, or ruled out already? `python -I research_pass.py
   --scope <TH-nnn|IDEA-nnn>`. Record the pass id in the experiment's
   `lit_checked`. If the literature already answers the question, the idea
   closes without burning GPU — verdict `closed-by-literature`, which is a
   result, not a non-event.
3. **Hypothesise** — write the falsifiable sentence and the `exp_id` row
   *before* the run.
4. **Run** — the design/fold/score work, or the manual steps. Base validation
   (root `AGENTS.md`) wherever sequences are involved.
5. **Literature re-check (AMASS autoresearch).** With the result in hand:
   `--scope EXP-nnn`. Does the literature explain it, contradict it, or now read
   differently? A surprising number is a prompt to search again, not just to log.
6. **Update** — write `experiments/EXP-nnn.md`, move the affected theories'
   confidence with a cited history line, append any new ideas the result suggests.

Skipping step 2 or 5 is allowed only when the search cap is spent, and then
`lit_checked` says `skipped:budget`. [`validate.py`](validate.py) fails any row
that has a verdict with an empty `lit_checked`.

## The files

| File | What it holds |
|---|---|
| [`experiments.csv`](experiments.csv) | One append-only row per thing we tried. Correct history by adding a superseding row, never by editing. |
| `experiments/EXP-nnn.md` | The long form: what we expected, what the literature said, what happened, **why**, what it implies. Failures in full detail — a written-down dead end is the highest-value thing here. |
| [`THEORIES.md`](THEORIES.md) | What we currently believe. Falsifiable claims with confidence, evidence for and against, and a cited history of every confidence move. |
| [`IDEAS.md`](IDEAS.md) | The backlog, so nothing is lost and nothing is tried twice. Dropped ideas keep their reason. |
| [`literature/REVIEW.md`](literature/REVIEW.md) | The standing review by measured property. Pass files are the transaction log; this is the balance. |
| `research/pass-NNN.md` + `.json` | One research pass: queries, cache hits, spend, candidate evidence, applied updates. |
| `research/spend.json` | Cumulative AMASS spend against the ~2,000-search team budget. |
| [`STATE.md`](STATE.md) | Current counts, what is running, what is blocked. |

## How the loop divides the work

[`research_pass.py`](research_pass.py) is the **data layer**: it picks the
scope, spends AMASS searches, caches everything, and extracts candidate evidence
— sentences carrying a measured number, matched to a theory by term overlap. It
deliberately does **not** decide what to believe. A regex can find a KD value;
it cannot weigh evidence.

The **agent** driving the loop does the judgment: reads the pass file, decides
which candidates are real evidence, and applies the result to `THEORIES.md`,
`IDEAS.md` and `literature/REVIEW.md`, citing the pass id in each history line.

Auto mode **applies** — it does not queue proposals for a human to approve.
That was a deliberate choice: a continuous loop that only proposes just builds a
pile nobody reads. The safeguard is not a human gate, it is the audit trail —
every change is a commit on a branch, with the evidence it came from named in
the file.

## Rules

- Append-only ids. `EXP-001`, `TH-001`, `IDEA-001`, `pass-001` are permanent addresses.
- No experiment without step 2. No theory move without a cited `exp_id` or pass id.
- Hypothesis before result. A row whose `hypothesis` was written after the metrics is not evidence.
- Every number cites its artefact path; every literature claim cites its AMASS record; measured and predicted never share a cell.
- A design is not a candidate until it passes BASE VALIDATION (root `AGENTS.md`). An experiment that produced sequences records the validation report path in `outputs`, or states it has not been run.
- Never commit `AMASS_API_KEY` or anything matching `*_key.txt`.
- Run `python -I validate.py` before every commit.

## Budget

~2,000 AMASS searches for the whole team, credits shared, $0.05 per 20 results.
Each pass is capped at 10 new searches (`--max-new`), the count is logged in the
pass file, and the cumulative total lives in `research/spend.json`. A pass that
would exceed its cap defers the remaining queries and says so rather than
trimming silently.

## Operating mode

Set 2026-11-14: passes run **every 30 minutes until 18:00 local**, each one
applying its findings and committing. Output goes to the `LEO-experiment-ledger`
branch and reaches `main` by pull request, never by direct push.
