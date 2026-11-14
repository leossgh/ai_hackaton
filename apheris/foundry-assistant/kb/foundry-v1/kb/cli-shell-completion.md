---
id: cli-shell-completion
type: article
title: Shell completion
gloss: '`foundry-toolkit completion <shell>` prints the code that turns on tab completion in `bash`, `zsh`, or `fish`, and nothing else, so a shell can run it at each start. Any other shell, or none, is a usage error (exit `2`). Add the line for your shell to the file it reads:'
examples:
- How do I enable tab completion for foundry-toolkit in bash?
- fish completion setup?
- I ran `foundry-toolkit completion powershell` and it exited with code 2. Why?
- What does tab completion actually complete? Does it do flag values too?
- Why doesn't `--name` complete anything when I press tab?
- What does completion offer for --to versus --to-archive or --policy?
- Completion stopped working after I upgraded and the binary moved. Do I need to change my shell config?
- Why does my script suddenly just print completions instead of running foundry-toolkit commands?
---
`foundry-toolkit completion <shell>` prints the code that turns on tab
completion in `bash`, `zsh`, or `fish`, and nothing else, so a shell can run it
at each start. Any other shell, or none, is a usage error (exit `2`). Add the
line for your shell to the file it reads:

| Shell  | Line                                        | File                                              |
|--------|---------------------------------------------|---------------------------------------------------|
| `bash` | `source <(foundry-toolkit completion bash)` | `~/.bashrc`                                       |
| `zsh`  | `source <(foundry-toolkit completion zsh)`  | `~/.zshrc`                                        |
| `fish` | `foundry-toolkit completion fish \| source` | `~/.config/fish/completions/foundry-toolkit.fish` |

fish loads its file the first time you complete `foundry-toolkit`. The shell
then completes the commands and the flags that `foundry-toolkit` offers, and the
values of a flag or argument that takes one of a few, such as `--log-format`,
`--output-format`, `--maturity`, `--executor`, and the shell of `completion`.
A flag that takes a directory, such as `--to`, completes to the directories
around you, and one that takes a file, such as `--to-archive` or
`--policy`, to files and directories. Any other value, such as `--name`,
completes to nothing, since only a registry knows it. The code names
`foundry-toolkit` alone, not a path, so the shell runs whichever
`foundry-toolkit` it finds on `PATH`, and an upgrade that moves the binary keeps
completion working. Completion needs the binary on `PATH` under that name,
which `go install` and a bare `go build` of `./cmd/foundry-toolkit` give it,
as `task build` does. zsh completes through `bashcompinit`, which shows no
descriptions.

The shell asks for completions as bash's `complete -C` does: a run whose
environment sets `COMP_LINE` prints the completions of that line, with
`COMP_POINT` as the cursor, and runs no command. A script that exports
`COMP_LINE` turns every run into a completion.

---
