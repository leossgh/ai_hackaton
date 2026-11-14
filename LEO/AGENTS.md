# Agent rules: Leo's folder

Rules for any agent working in `LEO/` or on the `LEO` branch. These are mine, not the team's.

## Required reading, before you touch anything

**You must read both `AGENTS.md` files. Neither one is sufficient on its own.** Read them in this order, in full, before your first edit, command or commit:

1. **[`../AGENTS.md`](../AGENTS.md)** — the team's shared file at the repo root. The hackathon itself: the two tracks and how they are assigned, the hard constraints `abguard` enforces, the ranking consequences of only 4 designs being tested, the model weights, the pitch criteria. None of that is repeated here.
2. **This file** — how work is organised in `LEO/`: branching, commits, state files.
3. **[`README.md`](README.md)** — the full notes: data, docs, setup, reference, progress log.

Do not skip the root file because this one is "the personal one", and do not skip this one because you read the root file. They cover different things: the root file is *what the problem is*, this file is *how we work on it*. An agent that read only one will either break the workflow or break the science.

Where this file and the root file conflict, this one wins inside `LEO/`. Conflicts are a bug — say so, so one of them gets fixed.

If either file is missing, stop and say so rather than guessing at the rules.

## Scope: you may only write inside `LEO/`

**Everything under `LEO/` is yours to edit. Everything outside it is off limits.** This is a hard rule, not a preference.

Allowed to write:

- Any path under `/home/hackathon/hackathon-team-3/LEO/`.
- Your task's own folder, `LEO/tasks/<short-task-name>/` — see below. Prefer this over writing loose files at the top of `LEO/`.
- Scratch files in the session scratchpad directory, for throwaway intermediates.

**Explicitly denied**, even when it looks harmless or helpful:

| Path | Why |
|---|---|
| `../AGENTS.md`, `../README.md` | Team-shared files. Leo maintains them. |
| `../JAHN/`, `../NICCOLO/`, `../ANDERS/` | Other people's folders. Never, for any reason. |
| Anything else at the repo root | Shared. |
| `~/hackathon-team-3/apheris/rfd4/`, `~/hackathon-team-3/apheris/foundry-assistant/`, `~/hackathon-team-3/apheris/hackathon-data/` | Organiser-supplied and shared across the team. Read freely, write nothing. |
| Another task's folder or state file | Not yours, and it causes merge conflicts. |
| Anything outside the repo, except scratch | Not part of this work. |

Reading outside `LEO/` is fine and often necessary — read `../AGENTS.md`, the organiser docs, previous run outputs. The restriction is on **writing**.

If a task seems to require a change outside `LEO/`, do not make it. Describe the change you would make and why, and let Leo decide. A run that needs to write its outputs somewhere puts them under your task folder, not next to the shared inputs.

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
| `LEO/<task>` | the agent doing the task | commit freely while working | `LEO/tasks/<task>/STATE.md`, kept current |
| `LEO` | the agent, when a feature is finished | after the task works | `LEO/STATE.md`, the roll-up |
| `main` | **only on Leo's explicit request** | never on an agent's own judgment | — |

## Every sub-branch and sub-agent works in its own folder

A new sub-branch creates `LEO/tasks/<short-task-name>/` — same name as the branch — and keeps **all** its files there: scripts, configs, run outputs, notes, its state file. Nothing loose at the top of `LEO/`.

```
LEO/tasks/novelty-filter/
  STATE.md          # required, created in the first commit
  ...               # whatever the task needs
```

One folder per branch, so two branches never touch the same path and never conflict when they merge back into `LEO`. **Never write in another task's folder.** If you need something from one, read it or copy it into yours.

A sub-agent gets its own subfolder under the task that spawned it: `LEO/tasks/<task>/<subagent-name>/`, with its own `STATE.md` on the same rules. The parent task's `STATE.md` says which sub-agents are running and what each is for. Tell every sub-agent its folder and that it may not write outside it — a sub-agent that was not told inherits none of this.

## Every task carries a state file

The first commit on a new sub-branch creates `LEO/tasks/<short-task-name>/STATE.md`. Copy [`tasks/TEMPLATE.md`](tasks/TEMPLATE.md) and fill it in. It must answer, at any moment someone looks:

- **What this task is** — one or two sentences, and why it matters for the submission.
- **Right now** — what the agent is doing this minute, or `idle` / `waiting on X`. Not a plan: the actual current activity.
- **Done so far** — what works and has been verified, with the commit that did it.
- **Blocked** — anything waiting on a person, a download, or a decision, and what would unblock it.
- **Next** — the ordered remaining steps.
- **Log** — one dated line per run, result or dead end, including the failures. A dead end that is written down saves the next agent from repeating it.

Update it whenever the answer to "what are you doing?" changes — before starting a long run, after it finishes, and when hitting a blocker. Commit the update with the work it describes, not as a separate tidy-up at the end.

When the branch merges into `LEO`, fold anything still true into [`STATE.md`](STATE.md) and delete the task's `STATE.md` in the merge commit. `LEO/STATE.md` is the roll-up across all branches; the per-task files are the detail while work is in flight. Keep the rest of the task folder — that is the work.

## Other rules in this folder

- Never commit secrets or API keys, nor `hackathon-data/` or `.venv/`.
- Keep run notes in `LEO/`, not in shared folders or other people's folders.
- Record every design run: input spec, weight image, settings, seed, and resulting scores.
- Do not push without being asked. There is no remote configured yet.
- `../README.md` is a copy of `LEO/README.md` made for the team. It drifts. If you change `README.md` here, say so rather than silently refreshing the copy — that touches a shared file.
