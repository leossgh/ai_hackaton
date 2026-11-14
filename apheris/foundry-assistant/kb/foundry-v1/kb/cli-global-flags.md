---
id: cli-global-flags
type: article
title: Global flags
gloss: Every command takes the global flags, before or after its name. Here and below, a flag overrides its environment variable, and takes one value, so a flag given twice is a usage error (exit `2`). A variable set to the empty string counts as unset, so the flag keeps its default.
examples:
- What does the --log-format flag do?
- How do I set the log format with an environment variable?
- Can I put global flags after the command name?
- I passed --log-format twice and got exit code 2. why?
- FOUNDRY_LOG_FORMAT is set to an empty string, what format will I get?
- '`foundry build --log-format=` fails with exit 2'
- Why does my script fail when I use --name "$NAME" and NAME isn't set?
- which wins, the flag or the env var?
---
Every command takes the global flags, before or after its name. Here and
below, a flag overrides its environment variable, and takes one value, so a
flag given twice is a usage error (exit `2`). A variable set to the empty
string counts as unset, so the flag keeps its default. A flag given the empty
string, as `--name=` or `--name ""`, is a usage error (exit `2`): leave the
flag out instead. A script's `--name "$NAME"` with `NAME` unset then fails
rather than selecting every name.

<!-- flags: --log-format -->

| Flag           | Default | Environment          | Description                                                           |
|----------------|---------|----------------------|-----------------------------------------------------------------------|
| `--log-format` | `human` | `FOUNDRY_LOG_FORMAT` | Format of the notices, warnings, and errors on stderr: human or json. |

<!-- end flags -->

[Diagnostics on stderr](#diagnostics-on-stderr) shows both formats.

---
