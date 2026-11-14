---
id: cli-command-tree
type: article
title: Command tree
gloss: The whole foundry-toolkit command tree — the command groups (docker, module, weight, skill, workflow) and the subcommands each one offers (list, get, describe, configure, …), and which groups support list and get.
examples:
- How do I check which version of foundry-toolkit I have installed?
- foundry-toolkit --version gives me an error, why?
- What subcommands are under docker?
- how do i get help for a specific command
- Which command groups support list and get?
- What commands handle authentication to the toolkit itself?
- Does foundry-toolkit have shell completion?
- I want details about a module, do I use get or describe?
---
```
foundry-toolkit
├── login
├── logout
├── whoami
├── docker
│   ├── configure
│   ├── credential
│   ├── static-auth
│   └── help [<command>...]
├── module
│   ├── list
│   ├── describe
│   └── help [<command>...]
├── weight
│   ├── list
│   ├── get
│   └── help [<command>...]
├── skill
│   ├── list
│   ├── get
│   └── help [<command>...]
├── workflow
│   ├── list
│   ├── get
│   └── help [<command>...]
├── version
├── completion <shell>
└── help [<command>...]
```

Every command prints its usage with `-h` or `--help`, and so does the `help`
action; see [Help](#help).

`foundry-toolkit version` prints the CLI version and exits. The root has no
`--version` flag, since the commands that select or stamp an artifact by
version take their own, so `foundry-toolkit --version` is a usage error (exit
`2`). A plain `go build` reports `dev`.

---
