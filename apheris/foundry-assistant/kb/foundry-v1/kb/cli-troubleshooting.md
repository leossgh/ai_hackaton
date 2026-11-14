---
id: cli-troubleshooting
type: article
title: Troubleshooting
gloss: 'The registry rejected the username and password, or the stored login: they''re wrong, expired, rotated, or lack access, and the command exits `3`. Check the registry, username, and password, or run `foundry-toolkit login` again, and suspect an outage only if valid credentials fail too.'
examples:
- My read command exits with code 3 and says authentication failed. What should I check?
- I ran a read with just --registry and got exit code 8 instead of 3. Why?
- Getting "--username and --password must be given together"
- how do i check whether im logged in and who as?
- whoami --check exits 3. What now?
- I'm on a remote machine over SSH and the browser login never completes. How do I fix it?
- First login prints "your registry access is being set up; waiting up to 90 s". Is something wrong?
- Login failed with "robot … isn't set up on the registry after 90 s". What should I do?
---
### A read command fails to authenticate (401 / 403)

The registry rejected the username and password, or the stored login: they're
wrong, expired, rotated, or lack access, and the command exits `3`. Check the
registry, username, and password, or run `foundry-toolkit login` again, and
suspect an outage only if valid credentials fail too.

A read without a credential, as with `--registry` alone, that the registry
refuses exits `8`, not `3`: it rejected no credential. Pass `--username` and
`--password`, or drop `--registry` to read with the stored login.

### Half-specified credentials are rejected

`--username and --password must be given together` and
`--username/--password require --registry` mean a partial set: give
`--registry`, `--username`, and `--password`, or their variables, or none.

### Am I logged in, and as whom?

`foundry-toolkit whoami` shows the stored login, when its token expires, an
hour after login or its last renewal, and whether it renews, and `--check`
tries it against the registry. An expired login that can't renew exits `3`,
as does a login the registry rejects on `--check`: run `foundry-toolkit login`
again. A login that renews lasts until the tenant ends its refresh token; see
[Renewal](#renewal).

### Logging in over SSH

`login` listens for Auth0's redirect on `127.0.0.1:9993` of the remote
machine, but your browser runs on yours. Forward the port, then open the URL
from the `notice:` locally:

```bash
ssh -L 9993:127.0.0.1:9993 <host>
foundry-toolkit login …
```

### The first login waits

A first login to an organization has Apheris create your robot on the
registry, so `login` prints `notice: your registry access is being set up;
waiting up to 90 s` and retries until the robot exists; Ctrl-C ends the wait
(exit `130`). After 90 seconds, it fails with `robot … isn't set up on the
registry after 90 s: your access is still being provisioned` (exit `5`): log
in again after a minute, and contact Apheris if it keeps failing. Any other
answer from the registry, such as a rejected token, fails the login at once.
