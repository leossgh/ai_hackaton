---
id: cli-help
type: article
title: Help
gloss: Every command's usage is reachable two ways. `<command> --help`, or `-h`, prints it and exits, as in `foundry-toolkit weight get --help`. The `help` action prints the usage of the command path it names, from the root as `foundry-toolkit help [<command>...]`, or from a group, as `docker help`…
examples:
- How do I see the usage for a specific command like weight get?
- what does a bare `foundry-toolkit help` do?
- Is there a difference between `foundry-toolkit help module list` and `foundry-toolkit module help list`?
- Which command groups support their own help action?
- how do i get help for a whole group, e.g. module?
- In the usage line, what do angle brackets and square brackets mean?
- The usage for `get` shows `--to` and `--to-archive` under [flags] but I thought one was required. Why?
- -h vs --help, any difference?
---
Every command's usage is reachable two ways. `<command> --help`, or `-h`,
prints it and exits, as in `foundry-toolkit weight get --help`. The `help`
action prints the usage of the command path it names, from the root as
`foundry-toolkit help [<command>...]`, or from a group, as `docker help`,
`module help`, `weight help`, `skill help`, and `workflow help` do. A bare
`foundry-toolkit help` prints this README.

```
foundry-toolkit help module list # usage of module list
foundry-toolkit module help list # the same
foundry-toolkit module help      # usage of the module group
```

The usage line shows a required argument as a placeholder, such as `<shell>`
on `completion`, and an optional one in brackets, such as `[<action>]` on
`docker credential`. Either-or flags, such as `--to` and `--to-archive` on
`get`, stay under `[flags]`, since neither alone is mandatory; their help says
to give exactly one.

---
