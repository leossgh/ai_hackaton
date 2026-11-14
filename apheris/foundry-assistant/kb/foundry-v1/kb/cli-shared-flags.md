---
id: cli-shared-flags
type: article
title: Shared flags
gloss: '`list`, `get`, and `module describe` take these to narrow the artifacts they act on. `list` prints every match; `get` and `module describe` need exactly one, so they take a bare `--latest` for the most recent version and refuse a count over 1.'
examples:
- How do I get just the most recent version with `get`? It complains when I match more than one artifact.
- difference between --version 1.2.3 and --version =1.2.3 in list?
- I set FOUNDRY_USERNAME and FOUNDRY_PASSWORD but pass --registry otherwise.. why is it reading anonymously?
- How can I pass my registry password without it showing up in the process list?
- What does the error `--username/--password require --registry` mean?
- How do I save an artifact with its signatures to a file and load it later without a registry?
- --to-archive exits with code 9, why?
- my --from-archive - run with a big artifact fails or runs out of space, what's going on?
---
### Selection flags

`list`, `get`, and `module describe` take these to narrow the artifacts they
act on. `list` prints every match; `get` and `module describe` need exactly
one, so they take a bare `--latest` for the most recent version and refuse a
count over 1. They also take `--version 1.2.3` as that release alone, where
`list` adds its suffixed variants, such as `1.2.3-of3ob`.

<!-- flags: module list --name --contract --maturity --version --repository --latest -->

| Flag           | Description                                                                                                                                                                                                                                                                          |
|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--name`       | Only include artifacts with this name.                                                                                                                                                                                                                                               |
| `--contract`   | Only include artifacts for this contract.                                                                                                                                                                                                                                            |
| `--maturity`   | Minimum maturity level to include: poc (proof of concept), research-preview, or generally-available.                                                                                                                                                                                 |
| `--version`    | Only include versions satisfying this semver constraint, e.g. '>= 1.2.0, < 2.0.0', '~1.2.x', '^1.2.3', or an exact '=1.2.3'; a suffixed version, such as 1.2.3-of3ob, matches only when the constraint names one. A bare '1.2.3' lists the release and every suffixed variant of it. |
| `--repository` | Only include the copies in this repository, host included, e.g. quay.io/acme/mine: picks one copy of an artifact that several repositories publish.                                                                                                                                  |
| `--latest`     | Keep only the N most recent versions of each artifact: `--latest` N (or `--latest=N`) for N, a bare `--latest` for the single most recent.                                                                                                                                           |

<!-- end flags -->

A `--repository` value starts with its host: its first segment holds a `.` or
`:`, or is `localhost`.

Without `--latest`, `list` keeps every version. `--latest` applies after the
other selection flags, and a `list` that combines them says so in a notice. It counts versions, so every entry of a kept version
stays. A `list` notes a kept version that several repositories publish: a
`notice:` when the copies are identical, and a `warning:` when their metadata
or digests differ, which makes them separate entries.

### Registry flags

Every `list`, `get`, and `module describe` reads the registry that
`--registry` names, anonymously or with `--username` and `--password` as HTTP
Basic auth, or else the one that `foundry-toolkit login` stored. With neither,
the command fails and says to log in, as it does, before any request, with a
stored login whose token has expired and can't [renew](#renewal) (exit
`3`).

<!-- flags: module list --registry --username --password --password-stdin --concurrency -->

| Flag               | Default | Environment           | Description                                                                                                                                                                                |
|--------------------|---------|-----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--registry`       | —       | `FOUNDRY_REGISTRY`    | Registry host to connect to directly, in place of the stored login credential; anonymously unless `--username`/`--password` are given.                                                     |
| `--username`       | —       | `FOUNDRY_USERNAME`    | Username for registry Basic auth. Requires `--registry` and `--password`. The variable binds to `FOUNDRY_REGISTRY`; see Credentials from the environment in foundry-toolkit help.          |
| `--password`       | —       | `FOUNDRY_PASSWORD`    | Password or token for registry Basic auth. Requires `--registry` and `--username`. The variable binds to `FOUNDRY_REGISTRY`; see Credentials from the environment in foundry-toolkit help. |
| `--password-stdin` | —       | —                     | Read the password or token from stdin instead of `--password`, keeping it out of argv and the environment.                                                                                 |
| `--concurrency`    | `32`    | `FOUNDRY_CONCURRENCY` | Maximum concurrent registry requests, at least 1.                                                                                                                                          |

<!-- end flags -->

`--registry` and `FOUNDRY_REGISTRY` take a host alone, such as `quay.io` or
`localhost:5000`: a scheme, a path, or a name without a `.` or `:` that isn't
`localhost` is a usage error (exit `2`). Taking the registry from
`FOUNDRY_REGISTRY` prints `notice: using registry "…" from FOUNDRY_REGISTRY;
this bypasses any stored login credential`; unset it to read with the stored
login. The `docker` commands' `--registry` differs; see
[`docker`](#foundry-toolkit-docker).

#### Credentials from the environment

`FOUNDRY_USERNAME` and `FOUNDRY_PASSWORD` stand in for `--username` and
`--password`, so the CLI takes both or neither: one alone is a usage error
(exit `2`). They bind to `FOUNDRY_REGISTRY`, so a pair exported for one
registry never reaches another. What a command does with a credential depends
on where it comes from and on the registry the command reads:

| Credential                                   | Registry                            | Result                                                                                                         |
|----------------------------------------------|-------------------------------------|----------------------------------------------------------------------------------------------------------------|
| Both from the environment                    | The `FOUNDRY_REGISTRY` host         | The pair applies.                                                                                              |
| Both from the environment                    | Another host, named by `--registry` | A `notice:` says the CLI ignores the pair, and it reads anonymously.                                           |
| Both from the environment                    | None                                | A `notice:` says the CLI ignores the pair, and it reads with the stored login; without one, the error says so. |
| `--username` and `--password`                | A host named by `--registry`        | The flags win, and go to that host as given.                                                                   |
| One flag, and the other from the environment | Not the `FOUNDRY_REGISTRY` host     | Usage error (exit `2`).                                                                                        |

A `--username` or `--password` flag with no registry at all is a usage error
too (`--username/--password require --registry`).

The environment and `--password-stdin` keep the password out of argv, which any
local user can read. `--password-stdin` drops a trailing newline, overrides
`FOUNDRY_PASSWORD`, and excludes `--password` (exit `2`):

```bash
printf '%s' "$TOKEN" | foundry-toolkit weight list --registry <host> --username <robot> --password-stdin
```

### Archive flags

`get` also reads and writes **Foundry OCI archives**: an artifact and its
cosign signatures in one uncompressed `.tar`, in the OCI image layout. An
archive keeps the exact manifest, so the digest and every signature survive
the round trip, and holds the metadata first, so reading what it holds skips
the content.

<!-- flags: weight get --to-archive --from-archive -->

| Flag             | Description                                                                                                                                    |
|------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| `--to-archive`   | File to write the artifact to as a Foundry OCI archive, its signatures included, or - for stdout. An existing file is refused, never replaced. |
| `--from-archive` | Foundry OCI archive to read the artifact from instead of the registry, or - for stdin; no registry is contacted.                               |

<!-- end flags -->

- `--to-archive -` writes to stdout unless that's a terminal. An existing
  `--to-archive` file exits `9` before any registry request; a new one gets
  mode `0666`, less the umask.
- `--from-archive` ignores the [registry flags](#registry-flags) and their
  variables, whatever their values, with a notice when the command line names
  one. The selection flags choose among what the archive holds, so another
  kind, or an artifact they exclude, is no match (exit `6`).
- `--from-archive -` copies stdin to `$TMPDIR`, or `/tmp`, first, for random
  access, so it needs that much free space; where `/tmp` lives in memory,
  point `TMPDIR` at a disk for a large artifact. It refuses a terminal on
  stdin (exit `2`), and an interrupt ends the copy at once, though the
  producer writes on or sits idle.
- An unreadable, malformed, or tampered archive exits `13`; a missing
  `--from-archive` path exits `2`.
- An archive whose name a ref reads in part as a digest or a tag, such as
  `out@v1:final`, exits `13` too: rename it without `@` or `:`.

```bash
# Take the newest weights offline, signatures included…
foundry-toolkit weight get --name embeddings --latest --to-archive embeddings.tar
# …and read them back with no registry.
foundry-toolkit weight get --from-archive embeddings.tar --to out
```

skopeo reads an archive as `oci-archive:embeddings.tar:embeddings-v1.0.0`, as
in `skopeo inspect` or `skopeo copy`, and umoci reads it once `tar -xf`
extracts it.

---
