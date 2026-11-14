# Agent rules: Leo's folder

Rules for any agent working in `LEO/` or on the `LEO` branch. These are mine, not the team's — the shared project context is in [`../AGENTS.md`](../AGENTS.md) and the full notes in [`README.md`](README.md). Read all three; where this file and the shared one differ, this one wins inside `LEO/`.

## Branching: `LEO` is the working main

Treat `LEO` as the main branch for day-to-day work. `main` is the team-facing branch and is off limits without Leo's explicit permission.

**Every new task starts on its own sub-branch of `LEO`.**

```bash
git checkout LEO
git pull --ff-only          # if a remote exists
git checkout -b LEO/<short-task-name>
```

Name the branch `LEO/<short-task-name>`, e.g. `LEO/novelty-filter`, `LEO/boltz-seeds`, `LEO/abguard-setup`. One task, one branch.

**Commit as you go.** Do not leave work uncommitted between steps. Each commit is one coherent change, with a message saying what and why. End commit messages with a `Co-Authored-By:` line naming the model you are actually running as.

**When the feature is finished, merge it back into `LEO`.**

```bash
git checkout LEO
git merge --no-ff LEO/<short-task-name>
git branch -d LEO/<short-task-name>
```

Use `--no-ff` so the branch point stays visible in the history. Delete the sub-branch after merging. If a task is abandoned, say so and leave the sub-branch in place rather than deleting unmerged work.

**Never merge into `main` on your own.** Merging `LEO` into `main` requires Leo to ask for it explicitly, each time. "I finished the feature" is not permission. If you think a merge to `main` is due, say so and wait.

| Branch | Who merges into it | When | State file |
|---|---|---|---|
| `LEO/<task>` | the agent doing the task | commit freely while working | `LEO/state/<task>.md`, kept current |
| `LEO` | the agent, when a feature is finished | after the task works | `LEO/STATE.md`, the roll-up |
| `main` | **only on Leo's explicit request** | never on an agent's own judgment | — |

## Every sub-branch carries its own state file

The first commit on a new sub-branch creates `LEO/state/<short-task-name>.md` — same name as the branch. One file per branch, so two sub-branches never collide when they merge back into `LEO`. Never edit another branch's state file.

Copy [`state/TEMPLATE.md`](state/TEMPLATE.md) and fill it in. It must answer, at any moment someone looks:

- **What this task is** — one or two sentences, and why it matters for the submission.
- **Right now** — what the agent is doing this minute, or `idle` / `waiting on X`. Not a plan: the actual current activity.
- **Done so far** — what works and has been verified, with the commit that did it.
- **Blocked** — anything waiting on a person, a download, or a decision, and what would unblock it.
- **Next** — the ordered remaining steps.
- **Log** — one dated line per run, result or dead end, including the failures. A dead end that is written down saves the next agent from repeating it.

Update it whenever the answer to "what are you doing?" changes — before starting a long run, after it finishes, and when hitting a blocker. Commit the update with the work it describes, not as a separate tidy-up at the end.

When the branch merges into `LEO`, fold anything still true into [`STATE.md`](STATE.md) and delete the per-branch file in the merge commit. `STATE.md` is the roll-up across all branches; the per-branch files are the detail while work is in flight.

## Other rules in this folder

- Never commit secrets or API keys, nor `hackathon-data/` or `.venv/`.
- Keep run notes in `LEO/`, not in shared folders or other people's folders.
- Record every design run: input spec, weight image, settings, seed, and resulting scores.
- Do not push without being asked. There is no remote configured yet.
- `../README.md` is a copy of `LEO/README.md` made for the team. It drifts. If you change `README.md` here, say so rather than silently refreshing the copy — that touches a shared file.
