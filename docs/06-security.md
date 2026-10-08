# 06. Security and publication

English | [Español](es/06-security.md)

Keep real profiles, subscription/tenant IDs, resource names, endpoints, emails,
logs, imports and reports outside the repository. Operational identifiers are
not necessarily credentials, but are still private under this project's policy.
Use synthetic examples; never copy an operational walkthrough into public docs.

Configuration is validated JSON, never `source` or `eval`. Keys travel in
memory over HTTPS, not in process arguments or shared files. Child-tool filtering
is not isolation from root or another process controlled by the same user.
Do not use shell tracing, dump request bodies, or upload complete session logs.

Runtime users need read access. Writers and infrastructure operators require
separate scoped permissions; no tool grants Owner to fix an error.
Do not weaken tenant policy or firewall rules to make a test pass.

VS Code must create its own encrypted secrets on each machine. Do not edit or
copy `state.vscdb`, fabricate references or use an arbitrary extension's secret
namespace as a replacement for the editor's core credential service.

## Before publication

```bash
python3 scripts/check_public.py
gitleaks dir . --redact --no-banner
gitleaks git . --redact --no-banner
```

The privacy checker detects selected operational patterns; Gitleaks detects
credential patterns. Neither proves that every possible secret is absent.
Review the staged diff and release contents. Never stage with an unreviewed
`git add .`; never export all local Git refs or use `git push --mirror`.
Private checkpoints can exist even when their files are untracked.

Keep GitHub secret scanning and push protection enabled. CI must not receive
Azure secrets or run live provisioning from pull requests. If a secret was
published, revoke/rotate first; agree any history rewrite separately. Deletion
from the latest commit does not remove forks, caches or earlier history.

See [SECURITY.md](../SECURITY.md) for confidential reporting.
