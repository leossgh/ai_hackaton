---
id: cli-reading-with-static-registry-credentials
type: article
title: Reading with static registry credentials
gloss: 'The read commands also take the [registry flags](#registry-flags) from their variables, so a host with HTTP Basic auth needs no `foundry-toolkit login`:'
examples:
- How do I use foundry-toolkit read commands without running `foundry-toolkit login`?
- what does FOUNDRY_CONCURRENCY do?
- How can I list only the newest version of every published module?
- What fields are in each entry of the module list output, and which are always there?
- What does the `images` list contain in module list output?
- How do I filter modules by version range or maturity?
- Why does `get` fail saying an artifact is ambiguous?
- Can I download a module with `foundry-toolkit module get`?
---
The read commands also take the [registry flags](#registry-flags) from their
variables, so a host with HTTP Basic auth needs no `foundry-toolkit login`:

```bash
export FOUNDRY_REGISTRY="<registry host>"     # such as quay.io
export FOUNDRY_USERNAME="<registry username>" # or robot name
export FOUNDRY_PASSWORD="<password or token>"
export FOUNDRY_CONCURRENCY=64                 # optional: lists large catalogs faster
```

### Discovering artifacts

List the newest version of each published module:

```bash
foundry-toolkit module list --latest
```

stdout gets a YAML sequence, one mapping per module. Each entry starts with
`name` and `kind`, the command group, which select it again, as in
`module list --name <name>`. `images` lists, in catalog order, each repository
that publishes the module with the same metadata and digest, pinned to the
digest, without a tag, as in `module describe`. Each other key takes the name of
the flag that filters or stamps it. `name`, `kind`, `images`, and `version`
appear in every entry; `title`, `description`, `revision`, `maturity`,
`contract`, and `tasks` appear only when the artifact sets them.

```yaml
- name: <module-name>
  kind: module
  images:
    - <registry>/<org>/<repo>@sha256:<digest>
    - <registry>/<org>/<other-repo>@sha256:<digest>
  title: …
  description: …
  version: …
  revision: …
  maturity: …
  contract: …
  tasks:
    <task-name>:
      description: …
      input: …
      output: …
```

Copies with the same metadata but different digests are an illegal state:
they stay separate entries, and `get` fails on them as ambiguous.

Narrow the list with the [selection flags](#selection-flags):

```bash
foundry-toolkit module list --name <name>
foundry-toolkit module list --maturity generally-available --latest
foundry-toolkit module list --version '>= 1.2.0, < 2.0.0'
foundry-toolkit module list --contract <contract> --latest
```

The other kinds work the same way, with `get` to download. A module has no
`get`, since Docker pulls it;
[`module describe`](#foundry-toolkit-module-describe) exports its contract
instead.

---
