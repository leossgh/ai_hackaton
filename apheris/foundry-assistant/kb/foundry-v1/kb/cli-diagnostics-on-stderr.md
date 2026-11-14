---
id: cli-diagnostics-on-stderr
type: article
title: Diagnostics on stderr
gloss: 'Results go to stdout: a listing, a module''s description, the `whoami` report, an archive, or, from `get`, the image''s reference, pinned to its digest without a tag, as in `quay.io/acme/mine@sha256:…`.'
examples:
- Which output goes to stdout and which goes to stderr?
- how do i get stderr messages as json for my CI job?
- What do the JSON level values INFO, WARN and ERROR map to?
- I set NO_COLOR but still get colors with CLICOLOR_FORCE. Which wins?
- What does the error record look like in JSON, and how can a program tell what failed without parsing msg?
- why does list or get warn about 'breaks 2 metadata rules'?
- In JSON mode, what extra field does the metadata warning have?
- Does --log-format json change what happens with usage errors or Ctrl-C?
---
Results go to stdout: a listing, a module's description, the `whoami` report,
an archive, or, from `get`, the image's reference, pinned to its digest
without a tag, as in `quay.io/acme/mine@sha256:…`. `login`, `logout`, and the
`docker` commands print a confirmation instead: one line, or one per item that
`logout` or a `--remove` removed. Everything else goes to stderr, a message
per line, with any further lines indented: notices, warnings, and the error of
a failed command, after its usage for a usage error.

| Message     | Human prefix     | JSON `level`     | Meaning                                                            |
|-------------|------------------|------------------|--------------------------------------------------------------------|
| Notice      | `notice:`        | `INFO`           | The command did what you asked, and here's a side effect.          |
| Warning     | `warning:`       | `WARN`           | The result may not be what you meant.                              |
| Error       | `error:`         | `ERROR`          | The command failed; the [exit code](#exit-behaviour) says why.     |

The default `human` format prints each message behind its prefix:

```
notice: --latest is applied after --name; keeping the 1 most recent version(s) of what remains
error: no weights matched the given selection
```

A color terminal shows `notice:` dim, `warning:` yellow, and `error:` red. A
non-empty `NO_COLOR` turns color off, even beside `CLICOLOR_FORCE`, as does
`TERM=dumb`; `CLICOLOR_FORCE` turns it on where stderr isn't a terminal.

`--log-format json` prints one JSON object per line instead, for CI jobs and
log collectors, with `time` (RFC 3339), `level`, and `msg`, the human line
without its prefix. A notice or a warning adds its facts as attributes, such
as `registry`, `images`, or `kind`, the artifact's group, so a program needn't
parse `msg`. An error adds `exit-code`, and `condition`, the code's name in
[Exit behaviour](#exit-behaviour):

```
{"time":"2026-01-02T15:04:05.123+01:00","level":"INFO","msg":"--latest is applied after --name; keeping the 1 most recent version(s) of what remains"}
{"time":"2026-01-02T15:04:05.456+01:00","level":"ERROR","msg":"no weights matched the given selection","exit-code":6,"condition":"no-match"}
```

`list` and `get` warn about an artifact whose version annotation is missing or
names another version than its tag, or whose maturity is no level
foundry-toolkit knows. They still read it as annotated, since the tag decides
which version a selection matches, and `get` warns before it writes. One warning
names every broken rule, for the publisher to fix, and its JSON record adds
`fields`, the annotation keys at fault:

```
warning: weights odd v1.0.0 at quay.io/acme/mine@sha256:… breaks 2 metadata rules: org.opencontainers.image.version: want the tag's version v1.0.0, found "v2.0.0"; net.apheris.maturity-level: want poc, research-preview, or generally-available, found "beta"
```

- `--log-format` covers stderr alone; stdout takes `--output-format`.
- In `json`, stderr carries only records, so a usage error prints no usage.
- A command line that doesn't parse reports its error in JSON under
  `--log-format json`, wherever the flag stands, or `FOUNDRY_LOG_FORMAT=json`.
- An interrupted run (exit `130`) logs nothing, in either format.

---
