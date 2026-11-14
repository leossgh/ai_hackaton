---
id: cli-commands
type: article
title: Commands
gloss: 'Log in through the browser and store a registry credential: sign in to Auth0 (Authorization Code with PKCE), then exchange the OIDC token, through federation, for an ephemeral Quay robot token.'
examples:
- Where does foundry-toolkit login save my credential and what's in it?
- I'm SSHed into a remote box and login can't complete in the browser. What do I do?
- login failed with exit code 4. What does that mean?
- How can I make a script run login only if I'm not logged in?
- when does my token get renewed automatically?
- Can I copy credential.json to another machine so I'm logged in on both?
- What does foundry-toolkit logout remove, and does it log me out of my other machines?
- How do I set up docker pull to use my Foundry login?
---
### `foundry-toolkit login`

Log in through the browser and store a registry credential: sign in to Auth0
(Authorization Code with PKCE), then exchange the OIDC token, through
federation, for an ephemeral Quay robot token.

`login` opens the sign-in page and names its URL in a `notice:`, for when no
browser opens. Auth0 redirects to a listener on `127.0.0.1:9993` on the
machine that runs `login`; over SSH, forward that port first (see
[Logging in over SSH](#logging-in-over-ssh)). On success, stdout gets only
`Logged in to <organization> as <robot>. Credential stored.`; without an
entitlement, the error says how to request access. Both name the organization
when the access token does.

You sign in to one organization, the one `--auth0-organization` names or the
one you pick, and the access token's registry access claim names your robot
and registry host there. Without the claim, your account isn't entitled to
Foundry there (exit `4`). A claim this build can't read, of a later version or
with only unsupported principals, fails with a hint to upgrade foundry-toolkit,
and a malformed one names the bad field (exit `5`). A first login waits for
the registry to set up your robot; see
[The first login waits](#the-first-login-waits).

The credential goes to `<user-config-dir>/foundry/credential.json`, such as
`~/.config/foundry/credential.json`, with mode `0600` in a `0700` directory.
It holds only the registry host, the robot, the token, and, in RFC 3339 UTC,
when `login` obtained the token, `obtained-at`, and when it expires,
`expires-at`; the read commands use it unless given `--registry`. The
registry's catalog, not the file, decides which repositories you can read.
Where the tenant grants offline access, it also holds Auth0's refresh token,
`refresh-token`, with the tenant and the client that issued it,
`auth0-domain` and `auth0-client-id`; it keeps no access token, and no
command prints the refresh token. One process at a time writes the file,
under an advisory lock on `credential.lock` beside it, which a writer waits
for up to a minute.

A `login` over a stored one revokes the stored one's refresh token once it
saves the new credential, as [`logout`](#foundry-toolkit-logout) does, so a copy
of the old file stops renewing too. A `notice:` says whether it could; when
the revocation fails, as when Auth0 doesn't answer, the token lasts until the
tenant's lifetime for it ends, and `login` still succeeds.

The expiry is the token's own lifetime, from its `iat` and `exp` claims,
counted from when `login` asked for it, so a skewed clock moves it along. A
`notice:` names it, as in `the token expires at 2026-10-02T14:05:12Z, in
1h0m0s`. A token without the claims has no recorded expiry.

#### Renewal

A command that sends the stored token, the Docker credential helper too,
renews the login once the token has less than half its lifetime left, 30
minutes of the hour: it trades the refresh token at Auth0 for an access
token, and that at the registry for a new robot token, then saves both, so
you sign in again only once the tenant ends the refresh token. The renewal
holds the file's lock and rereads the file first, so parallel pulls renew
once.

- A renewal that fails while the token holds is a `notice:`, and the command
  sends the token.
- Once the token has expired, the failure is the command's: a refresh token
  Auth0 refuses, as once its lifetime ends, or a claim that now names another
  robot or host, exits `3` and drops the refresh token; a claim that's gone
  exits `4`; and an Auth0 or registry that doesn't answer, `5`.
- Each renewal retires the refresh token it presents, and Auth0 ends the
  login of a retired one that comes back, so a copy of `credential.json` on
  another machine ends the login on both at the next renewal.
- A login without a refresh token, or a token without a recorded expiry,
  renews nothing, and a command refuses it once it has expired.

```
foundry-toolkit login \
  [--auth0-domain <domain>] \
  [--auth0-client-id <id>] \
  [--auth0-audience <audience>] \
  [--auth0-scope "openid profile offline_access"] \
  [--auth0-connection <connection>] \
  [--auth0-organization <org_XXXX>]
```

<!-- flags: login --auth0-domain --auth0-client-id --auth0-audience --auth0-scope --auth0-connection --auth0-organization -->

| Flag                   | Default                         | Environment                  | Description                                                                                   |
|------------------------|---------------------------------|------------------------------|-----------------------------------------------------------------------------------------------|
| `--auth0-domain`       | —                               | `FOUNDRY_AUTH0_DOMAIN`       | Auth0 tenant domain, e.g. apheris.eu.auth0.com; required unless the build has one.            |
| `--auth0-client-id`    | —                               | `FOUNDRY_AUTH0_CLIENT_ID`    | Auth0 application (public client) ID; required unless the build has one.                      |
| `--auth0-audience`     | —                               | `FOUNDRY_AUTH0_AUDIENCE`     | Auth0 API audience the access token is requested for; required unless the build has one.      |
| `--auth0-scope`        | `openid profile offline_access` | `FOUNDRY_AUTH0_SCOPE`        | OAuth scope requested at /authorize; without offline access, the login gets no refresh token. |
| `--auth0-connection`   | —                               | `FOUNDRY_AUTH0_CONNECTION`   | Route login straight to a named Auth0 connection (most specific override).                    |
| `--auth0-organization` | —                               | `FOUNDRY_AUTH0_ORGANIZATION` | Route login to a specific Auth0 organization (org_XXXX) when no connection is set.            |

<!-- end flags -->

A flag or variable overrides the built-in tenant. A release build carries the
Apheris tenant, so a bare `foundry-toolkit login` works; another build needs the
domain, client ID, and audience, and names any missing (exit `2`).

`login --help` lists only `--auth0-connection` and `--auth0-organization`, the
two that a user chooses. The other four flags work all the same. A
connection routes the sign-in ahead of an organization, so a command line
that gives `--auth0-organization` beside a connection logs a `notice:` that
it ignores the organization.

---

### `foundry-toolkit logout`

Remove the stored login: `credential.json`, and every static `auths` entry in
Docker's `config.json` of the kind [`docker static-auth`](#foundry-toolkit-docker-static-auth)
writes: an exact copy of its robot and token, under any host, and the
registry's entry of its robot, under its host or a legacy key, with any token,
as a renewal replaces the token an entry embeds. It
revokes the login's refresh token, if it holds one, at the tenant that issued
it, waiting up to 10 seconds. That ends this login, and any copy of its file,
but not your logins on other machines, which each hold a refresh token of
their own. With no stored login, it prints
`Not logged in; nothing to remove.` and exits `0`.

```
foundry-toolkit logout
```

It prints a line per item removed, and leaves, with a `notice:`:

- a static `auths` entry for the registry that holds another credential, such
  as your own `docker login`;
- the `docker configure` helper and shim, which hold no secret
  (`docker configure --remove` uninstalls them);
- a refresh token it couldn't revoke, as when Auth0 doesn't answer, which
  lasts until the tenant's lifetime for it ends;
- the token at the registry, which a client can't revoke: it expires at the
  time the `notice:` names, about an hour after login, and an expired one
  gets no notice.

A malformed `credential.json` goes too, with a notice that `logout` didn't look
for static Docker entries. A file it can't remove exits `9`; a Docker config it
can't edit fails before the credential goes, so the next `logout` still finds
the static entries. `logout` takes no flags.

---

### `foundry-toolkit whoami`

Show the stored login, never its token: the registry, the robot, the
credential's path, when the CLI last stored it, when its token expires, and
whether it renews. With no stored login, it prints nothing and exits `3`,
and with an expired one that can't renew, it prints the report, then exits
`3`, so a script can gate on it:
`foundry-toolkit whoami >/dev/null || foundry-toolkit login …`.

```
foundry-toolkit whoami \
  [--check] \
  [--output-format yaml|json]
```

```yaml
registry: quay.io
robot: pharmax+bob
credential: /home/me/.config/foundry/credential.json
stored-at: "2026-10-02T13:05:12Z"
expires-at: "2026-10-02T14:05:12Z"
renewable: true
```

<!-- flags: whoami --check --output-format -->

| Flag              | Default | Environment             | Description                                                                                   |
|-------------------|---------|-------------------------|-----------------------------------------------------------------------------------------------|
| `--check`         | —       | —                       | Also authenticate against the registry with the login, and count the repositories it can see. |
| `--output-format` | `yaml`  | `FOUNDRY_OUTPUT_FORMAT` | Format of the result on stdout: yaml or json.                                                 |

<!-- end flags -->

- A login without a recorded expiry, as an earlier build stored it, has no
  `expires-at`, and a `notice:` says the expiry is unknown; tokens last about
  an hour.
- An expired login that can renew gets a `notice:` that the next command
  renews it, and exits `0`; `--check` renews it first.
- An expired login that can't renew fails with `the stored login expired at
  <time>: run foundry-toolkit login`, after the report, and `--check` sends no
  request.
- `stored-at` is the credential's `obtained-at`, so a copied or restored file
  reports when `login` or a renewal stored it, not the copy's time. A login
  without one, as an earlier build stored it, reports the file's modification
  time.
- The YAML quotes `stored-at` and `expires-at`, so a parser reads strings, as
  from the JSON, not timestamps.
- With `FOUNDRY_REGISTRY` set, a `notice:` says the read commands bypass this
  login, or, for a value that isn't a host alone, that they refuse it, with
  any user and password the value carries masked.
- With `--check`, the report adds `repositories:`, the number of repositories
  the login shows. The report prints first, then a rejected login exits `3`,
  with the hint to log in again, and an unreachable registry `8`.

---

### `foundry-toolkit docker`

Let Docker, and compatible tools such as `podman`, `nerdctl`, and BuildKit,
pull Foundry images with the stored login, through a credential helper.

```bash
foundry-toolkit login             # store the ephemeral credential
foundry-toolkit docker configure  # install and register the credential helper
docker pull quay.io/<org>/<repo>:<name>-v<semver>
```

Both commands below file `--registry` under the host alone, as Docker looks it
up: `https://quay.io` becomes `quay.io`, and a name without a `.` or `:` that
isn't `localhost` is no host (exit `2`). Their `--registry` ignores
`FOUNDRY_REGISTRY`, since the helper serves only the stored login's host.
Neither edits what you or another tool wrote, nor sets Docker to use the
stored login for a host where Docker's config shows another login (exit `9`).
Each `--remove` undoes only its own command's work, prints a line per item
removed, and writes nothing when there's nothing to remove.

#### `foundry-toolkit docker configure`

Install the `docker-credential-foundry` shim, and register it for the registry
under `credHelpers` in Docker's `config.json`. It's a one-time, idempotent
step: the helper reads the credential on every pull, so it survives re-logins,
and `config.json` holds no token. The shim runs `foundry-toolkit` by the path
it ran from, so run it again after moving or renaming the binary.

```
foundry-toolkit docker configure \
  [--registry <host>] \
  [--bin-dir <dir>] \
  [--remove]
```

<!-- flags: docker configure --registry --bin-dir --remove -->

| Flag         | Description                                                                                                                                                                                                                                                   |
|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--registry` | Registry host in Docker's config to register the helper for; defaults to the stored credential's host, else quay.io. Unlike the read commands' `--registry`, it doesn't fall back to `FOUNDRY_REGISTRY`: the helper serves only the stored credential's host. |
| `--bin-dir`  | Directory to install the docker-credential-foundry shim into; defaults to `<config-dir>/foundry/bin`.                                                                                                                                                         |
| `--remove`   | Undo configuration: remove the credHelpers entry, and the installed shim unless another host's entry still names the helper.                                                                                                                                  |

<!-- end flags -->

Docker finds the shim only with `--bin-dir` on `PATH`, so while it's missing
there, a `notice:` says to add it. A host other than the stored login's gets a
`warning:`, since the helper serves nothing there, and `configure` refuses a
host another tool's credential helper serves (exit `9`).

Docker asks the helper before it reads `auths` or a `credsStore`, so the
helper replaces any login Docker holds for the host, your own `docker login`
included, and `docker login` to the host fails while the helper serves it.
`configure` refuses a host whose `auths` entry holds a login other than the
stored one's (exit `9`), until `docker logout <host>` removes it, and when
Docker's config names a `credsStore`, whose logins `auths` may not show, a
`warning:` says the helper now outranks it.

#### `foundry-toolkit docker credential <action>`

The credential-helper protocol entry point that the installed shim calls, not
you, so the usage leaves it out; `foundry-toolkit docker help credential` still
shows it. It reads a server URL on stdin and writes the credential JSON,
`credentials not found in native keychain`, or, for an expired login that
can't renew, an error that names the expiry and says to run
`foundry-toolkit login`, to stdout. It renews a login due for it first.
Docker prints that error with the failed pull, where the not-found answer
would pull anonymously.

```
foundry-toolkit docker credential <get|store|erase|list|version>
```

| Arg            | Description                                                                                                                                                                                                                                                                                                                                |
|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `<action>`     | `get` returns the robot token for the credential's own registry only; `list` maps that registry to the robot; `store` and `erase` refuse, since `login` and `logout` manage the login, so `docker logout` warns rather than report a login removed that the helper still serves; `version` prints the helper's name and the CLI's version. |

#### `foundry-toolkit docker static-auth`

A fallback where a credential helper on `PATH` is impractical: write a static
Base64 auth entry into Docker's `config.json`, as `docker login` does. The
entry embeds the ephemeral token, so it **expires with the token**, about an
hour after login, at the time its `notice:` names; run the command again
before then, or prefer `docker configure`. It renews
a login due for it first, and an expired login that can't renew writes
nothing (exit `3`). Docker never reads the entry for a host that a credential
helper serves, through `credHelpers` or Docker Desktop's `credsStore`, so the
command refuses such a host (exit `9`), as it does a host that holds your own
login, under the host or a legacy key such as `https://quay.io/v1/`.

```
foundry-toolkit docker static-auth \
  [--registry <host>] \
  [--remove]
```

<!-- flags: docker static-auth --registry --remove -->

| Flag         | Description                                                                                                                                                                                                                                  |
|--------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--registry` | Registry host whose entry `--remove` cleans; defaults to the stored credential's host, else quay.io. A write goes to the stored credential's host alone. Unlike the read commands' `--registry`, it doesn't fall back to `FOUNDRY_REGISTRY`. |
| `--remove`   | Remove the static auth entry instead of writing it.                                                                                                                                                                                          |

<!-- end flags -->

A write to a host other than the stored login's is a usage error (exit `2`),
since the entry holds that login's token. `--remove` deletes only the entries
that hold the stored login's robot, under the host or a legacy key for it, and
prints a line for each.

---

### Artifact commands

The `module`, `weight`, `skill`, and `workflow` groups each serve one kind of
artifact, and a command behaves the same in every group that offers it, but
for what this table says:

| Group          | Called in messages     | Commands                             | Layout rule, which `get` checks (exit `11`)                                             |
|----------------|------------------------|--------------------------------------|-----------------------------------------------------------------------------------------|
| `module`       | module                 | `module list`, `module describe`     | — (a container image, which Docker pulls: see [`docker`](#foundry-toolkit-docker))      |
| `weight`       | weights                | `weight list`, `weight get`          | none                                                                                    |
| `skill`        | agent skill            | `skill list`, `skill get`            | **a `SKILL.md` at its top, whatever else sits beside it**                               |
| `workflow`     | Nextflow workflow      | `workflow list`, `workflow get`      | `main.nf`, `modules.yaml`, and contract snapshots, and no generated file                |

Below, `<kind>` stands for the group, so `foundry-toolkit <kind> get` covers
`weight get`, `skill get`, and `workflow get`.

---

### `foundry-toolkit <kind> list`

List the artifacts of the group's kind in the repositories you can access. It
takes the [selection flags](#selection-flags) and the
[registry flags](#registry-flags).

```
foundry-toolkit <kind> list \
  [--describe] \
  [--no-index] \
  [<selection flags>] \
  [<registry flags>] \
  [--output-format yaml|json]
```

<!-- flags: module list --output-format --describe --no-index -->

| Flag              | Default | Environment             | Description                                                                                            |
|-------------------|---------|-------------------------|--------------------------------------------------------------------------------------------------------|
| `--output-format` | `yaml`  | `FOUNDRY_OUTPUT_FORMAT` | Format of the result on stdout: yaml or json.                                                          |
| `--describe`      | —       | —                       | Include each module's full task schema.                                                                |
| `--no-index`      | —       | —                       | Read every artifact's manifest instead of each repository's metadata index, which can lag a moved tag. |

<!-- end flags -->

`--describe`, which only `module list` takes, adds each module's full task
contract to the end of its entry, as `schema`, so agents can compare
candidates.

stdout gets a YAML sequence, one mapping per artifact, or a JSON array of the
same objects; an empty listing is `[]` in both.

Where a repository holds a metadata index, one document of the metadata of the
artifacts in it, a listing reads that in place of their manifests, and reads
the manifest of each artifact the index lacks. A tag moved since the index's
last rebuild lists with its earlier metadata and digest until the next one, and
`--no-index` reads every manifest instead. An index that fails to read costs
only time: a notice names it, and the listing reads that repository's
manifests. Where `--name` and `--version` keep two tags or fewer of a
repository, the listing reads their manifests, which costs fewer requests.

```bash
foundry-toolkit module list --describe --output-format json
```

With `--describe`, a missing or malformed contract fails with exit `11` and no
partial listing. A module whose `tasks` annotation doesn't parse fails
`module list` with exit `11`, naming the module for its publisher to fix; until
then, `--name` lists another module without reading that one.

---

### `foundry-toolkit module describe`

Export one module's full contract, from `net.apheris.foundry.schemas`, with
its digest-pinned image references and the image's Foundry metadata. It reads
only the manifest and the image config: it never pulls layers or runs a
container. It takes the [selection flags](#selection-flags), or `--image`,
which also reaches an image outside the catalog's naming, and the
[registry flags](#registry-flags).

```bash
foundry-toolkit module describe --name apheris-protenix --version 0.17.0 > description.json
```

<!-- flags: module describe --image -->

| Flag      | Description                                                                      |
|-----------|----------------------------------------------------------------------------------|
| `--image` | Read this image tag or digest directly; cannot be combined with selection flags. |

<!-- end flags -->

- It writes JSON, `{"images": ["...@sha256:..."], "schema": {...}, "metadata": {...}}`,
  where `images` lists every identical copy.
- On success, a `notice:` names the module, the version, and the images it
  described, which the JSON leaves out, so you learn which version `--latest`
  took. An `--image` by digest, or by a tag other than `NAME-vVERSION`, takes
  the name from the schema's module and the version from the image; without
  either, the notice names the images alone.
- `metadata` maps each `apheris.foundry.` and `net.apheris.foundry.` key, such
  as `apheris.foundry.weights`, `apheris.foundry.default-weight`, or
  `apheris.foundry.capabilities`, to its string value, but for the contract's
  (`net.apheris.foundry.schemas`, `apheris.foundry.schemas`) and
  `net.apheris.foundry.tasks`; an image without any leaves it out. A manifest
  annotation wins over the config label of the same key, and an index takes
  its linux/amd64 image's labels, if it has one. A workflow's contract
  snapshot, `contracts/<choice>.json`, is this output for its pinned image.
- A model image's metadata follows the rules its image build checks:
  `apheris.foundry.capabilities` holds a JSON array of strings,
  `apheris.foundry.predict-params-defaults` a JSON object, and
  `apheris.foundry.weights` a nonempty JSON array of weights, each with a
  `version` and an absolute `path`, at most one marked `default`;
  `apheris.foundry.default-weight` names a weight's `version`, the one marked
  `default` if any. A value breaking a rule logs a `warning:`, and the
  description exports it as read.
- No match, or an `--image` that names no manifest, exits `6`, and ambiguity
  `7`. A missing or malformed contract exits `11`, as does an index whose
  platform images differ in Foundry contract or metadata, or that nests
  another index.

---

### `foundry-toolkit <kind> get`

Download one artifact's files into the `--to` directory, or into an archive
with `--to-archive` (see [Archive flags](#archive-flags)). `get` creates the
directory if needed and never replaces a file: when an entry it would write
exists, it writes nothing and exits `9`, as it does, before any registry
request, for a `--to` that names a file.

`get` takes the [selection flags](#selection-flags), which must match exactly
one artifact; for several, the error lists them so you can narrow it, as with
`--version` or `--latest`. It also takes the [registry flags](#registry-flags).

On success, a `notice:` says what `get` wrote from which image, naming the
version `--latest` took, and stdout prints that image's reference, pinned to
its digest, so a script can read again exactly what `get` wrote. With
`--to-archive -`, stdout carries the archive
instead; with `--from-archive -`, stdout stays empty, and the notice names the
image `oci-archive:stdin@sha256:…`.

Identical copies in several repositories are one match: `get` downloads the
first in catalog order, pinned to the digest it listed, and names it in a
`notice:`. Copies that differ are separate matches, so `get` fails as
ambiguous (exit `7`) until a flag such as `--contract` or `--repository` picks
one. `--repository` picks a copy either way, so a script needn't rely on
catalog order.

Before writing, `get` checks the content, and writes nothing to `--to` when it
breaks a rule that [exit `11`](#exit-behaviour) lists, such as a link, a name
that leaves `--to`, more than 50 GiB, or the kind's layout rule.
`workflow get` also compiles the workflow; see
[Rendering a workflow](#rendering-a-workflow).

```
foundry-toolkit <kind> get \
  (--to <dir> | --to-archive <file>) \
  [--from-archive <file>] \
  [<selection flags>] \
  [<registry flags>]
```

<!-- flags: weight get --to --to-archive --from-archive -->

| Flag             | Description                                                                                                                                                                                                    |
|------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--to`           | Directory to write the artifact contents to; created if missing. Exactly one of `--to` and `--to-archive` is required. An entry the artifact would write that already exists there is refused, never replaced. |
| `--to-archive`   | File to write the artifact to as a Foundry OCI archive, its signatures included, or - for stdout. An existing file is refused, never replaced.                                                                 |
| `--from-archive` | Foundry OCI archive to read the artifact from instead of the registry, or - for stdin; no registry is contacted.                                                                                               |

<!-- end flags -->

#### Rendering a workflow

`workflow get` compiles each task's wrapper beside `main.nf`, from the pinned
contract snapshots that `modules.yaml`, which every workflow needs, names.
Without `--policy`, the result is a compiled package, ready to mount into Hub,
which prepares it for its own compute classes, or to prepare later. With a
deployment's compute-class policy, it runs as it lands: `get` also writes
`tasks.config`, which binds each task to its image, the default choice in
`modules.yaml`, and to its resource requests, and `resources.json`, which
records the defaults, the policy, and the effective requests. A contract
snapshot whose model metadata breaks a rule that
[`module describe`](#foundry-toolkit-module-describe) warns about logs a
`warning:` naming the task and the image choice, one that no image choice
names logs a `warning:` naming the file, and `get` compiles the workflow
anyway.

A deployment fetches a workflow once with `--to-archive`, then reads it with
`--from-archive` on every use, with no registry, so a version tag that moves
later can't change what runs.

```bash
# Once, with registry access: the workflow and its signatures.
foundry-toolkit workflow get \
  --name aqcell \
  --version 1.0.0 \
  --to-archive aqcell.tar
# On every use: read the archive offline, and render it.
foundry-toolkit workflow get \
  --from-archive aqcell.tar \
  --policy policy.json \
  --to aqcell
nextflow -C runtime.config,aqcell/tasks.config run aqcell/main.nf
```

`runtime.config` holds the executor, authentication, and mount settings, which
a policy leaves out. A minimal policy for local runs gives limits to the
compute class that each task names, `cpu` for AQCell:

```json
{
  "version": 1,
  "classes": {
    "cpu": {
      "limits": {"cpus": 8, "memory_mib": 16384, "gpus": 0}
    }
  }
}
```

A class may also cap a task's disk with `limits.disk_mib`, which, omitted or
`0`, sets no limit; cap how many of a task's processes run at once with a
positive `max_forks`; raise a task's requests to a floor with `overrides`
(`cpus`, `memory_mib`); and, for `k8s`, place its tasks with `node_selector`,
`tolerations`, `gpu_resource`, `shm_mib`, and `pod.priority_class_name`. Any
other field fails to parse. A local GPU class sets `limits.gpus` alone, and
the runtime config maps the accelerator counts to GPU access, such as Docker's
`--gpus`. Nextflow 26.04 doesn't allocate local GPUs among concurrent tasks,
so serialize GPU use or isolate devices.

```
foundry-toolkit workflow get \
  (--to <dir> [--policy <file> [--executor local|k8s]] | --to-archive <file>) \
  [--from-archive <file>] \
  [<selection flags>] \
  [<registry flags>]
```

<!-- flags: workflow get --policy --executor -->

| Flag         | Default | Description                                                                                                                                                                                        |
|--------------|---------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--policy`   | —       | JSON compute-class policy to prepare the compiled workflow for: get also writes tasks.config and resources.json beside its main.nf; needs `--to`. Without it, get compiles the task wrappers only. |
| `--executor` | `local` | Execution backend the rendered resources must suit: local or k8s; needs `--policy`.                                                                                                                |

<!-- end flags -->

- A flag without the one it needs, and a policy file that `get` can't read or
  parse, are usage errors (exit `2`), before any registry request.
- Later failures write nothing to `--to`. A policy that can't serve a task,
  as one without its compute class, with limits below its requests, or with
  Kubernetes placement under `local`, exits `2`. An invalid manifest or
  contract, a missing `main.nf`, or a generated file in the source (a wrapper,
  an old lock, `tasks.config`, or `resources.json`) exits `11`, and a wrapper
  it can't write `9`.

---
