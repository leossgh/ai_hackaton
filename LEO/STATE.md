# Leo: Current State

Snapshot of what is running, what has finished, and what is blocked. Written 2026-11-14, times in UTC as shown in the logs. Update it whenever a run starts, finishes or fails.

This is the roll-up across the whole `LEO` branch. Work in flight on a sub-branch lives in its own folder under [`LEO/tasks/`](tasks/) with its own `STATE.md`; those fold into this one when the branch merges. See [`AGENTS.md`](AGENTS.md) for the branching and scope rules.

## Right now

- **No agent work is running in this folder.** Other Claude Code sessions are open on this VM, but nothing in the logs shows them writing to `LEO/`.
- **Branch:** `LEO`, at `1bfcab0`. `main` is at the same commit.
- **Uncommitted:** this file (`LEO/STATE.md`) only.

## Finished runs

A HER2 CDRH3 pipeline ran on the VM. It lives in `~/rfd4/runs/her2/`, not in this folder. Its script is `~/rfd4/Scripts/run-her2.sh`, and it was not started by this session. The log does not say who started it.

| Stage | Folder | Time (UTC) | Result |
|---|---|---|---|
| design | `runs/her2/design` | 09:58 to 10:01 | 4 replicates, image `her2-novel-2026-11-09`, seed 1, `high/front_loaded` recycling, batch size 1 |
| prepare | `runs/her2/prepared` | 10:01 | Top 2 designs prepared for refolding (`apo` and `holo` inputs) |
| predict | `runs/her2/boltz2` | 10:01 to 10:02 | Boltz-2 refolds of `her2_cdrh3_2` and `her2_cdrh3_3` |
| score | `runs/her2/scored-boltz2` | 10:02:42 | `refold_metrics.csv` written; `pass` column empty, as expected for HER2 |

### Scores from `refold_metrics.csv`

| Design | binder pLDDT | min iPAE | iPTM | pTM | binder pTM |
|---|---|---|---|---|---|
| `her2_cdrh3_2` | 95.6 | 0.331 | 0.946 | 0.961 | 0.991 |
| `her2_cdrh3_3` | 98.5 | 0.310 | 0.965 | 0.972 | 0.993 |

Ranking on `min_ipae`, `iptm` and `binder_plddt` (the rule from the task description) puts `her2_cdrh3_3` first. Both have min iPAE under 0.35, which is very low, so the ranking gap is small.

### Problems to fix before trusting these numbers

1. **Target-aligned RMSD is undefined.** The scorer reports fewer than 3 target atoms fixed in absolute coordinates. Only the backbone RMSD (1.04 Å for design 2) is valid. Do not rank on RMSD until this is fixed.
2. **Novelty is unchecked.** Both designs' CDRH3s are new sequences, but the HER2 tables are not on this VM (`hackathon-data/` is missing), so we cannot confirm they differ from the 525,063 known CDRH3s. Check this before any ranking.
3. **Only 2 of 4 designs were refolded**, because `TOPN=2` was set. The other 2 have not been scored.
4. **Only one Boltz-2 seed (42)** was used. Scores from one seed are not reliable on their own.
5. **abguard has not been run.** It is not installed on this VM, so the hard checks (format, length, cysteines, identity to known antibodies, track assignment) have not been applied to these designs.

## Blocked

| Item | Blocker | Needed to unblock |
|---|---|---|
| Novelty filter | `hackathon-data/` not synced | `aws s3 sync s3://apheris-oslo-hackathon/data/ hackathon-data/` |
| abguard checks | CLI not on the VM | Slack folder download |
| AMASS searches | `AMASS_API_KEY` not set; credits not claimed | Sign up and claim credits (one person per team) |
| JapanFold | No link or login recorded | Slack folder or organisers |
| Participant guide | Page fetch returned empty | Open it in a browser and paste the text |
| Thermostability predictor | None chosen | Team decision |

## Next steps, in order

1. Sync `hackathon-data/` and run the novelty check against the 525,063 HER2 CDRH3s.
2. Install and run abguard on the 4 designs.
3. Refold the other 2 designs and add a second seed for the top candidates.
4. Fix the target-aligned RMSD setup, or drop that metric from the ranking.
5. Write the ranked list and the reasoning behind it, since 40% of the pitch score is judgment.

## Log

| Date | Event |
|---|---|
| 2026-11-14 | HER2 design, prepare, Boltz-2 predict and score run completed in `~/rfd4/runs/her2` (started by an unknown session) |
| 2026-11-14 | This file created |
