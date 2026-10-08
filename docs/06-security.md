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

## Public-access security posture

This is a **repository assessment, not an Azure compliance attestation**.
It compares the current Python client and Bicep templates with the locally
supplied *Guia_acceso_publico_Copilot_Azure_OpenAI* (public access, P01-P16)
and *Informe_seguridad_Copilot_Azure_OpenAI* (historical findings H01-H08,
private-network alternative, T01-T16). Those Word files contain document
metadata and media and are deliberately excluded from publication.
The historical report assessed revision `445a8ca`; the comparison here uses
revision `33d2421`. No live subscription, firewall, Copilot session or VS Code
installation was audited. "Implemented" below means a property of source
code, **not** a claim about deployed resources or end-to-end data routing.

The supported public design has two distinct choices:

| Network profile | Azure OpenAI **and** Key Vault | Remaining exposure |
|---|---|---|
| `public_selected_ips` (preferred with stable egress) | Public endpoints, default deny, explicitly approved public egress IPv4 ranges on each resource | A valid stolen key can still be used from an allowed IP; vault IP rules do not constrain use of a copied inference key. |
| `public_any_ip` (only with documented risk acceptance) | Public endpoints reachable from any IP; authentication still required on both services | A stolen key can be used from any IP until revoked; prioritize short revocation times, dedicated resources and monitoring. |

The template expresses these profiles with `allowPublicAccess: false` plus
nonempty `allowedIPs`, or `allowPublicAccess: true`, respectively. They are
network settings, not authentication modes. The current client uses **Entra
identity to read Key Vault**, then an **Azure OpenAI API key for inference**.
`disableLocalAuth: false` is required by this key-based path. It does not
provide individual Entra attribution for subsequent inference requests;
do not claim Entra-only inference or turn off local authentication without a
tested client migration. Private Endpoints, private DNS and access from a
private network are a stronger **alternative architecture**, not a
prerequisite or a feature of the current Bicep template.

| Area and guide finding | Status and evidence | Gap / closure |
|---|---|---|
| H01 tool approvals | **Implemented in docs/client:** no default `--allow-all`; ordinary Copilot tool approval still applies. | **Pending:** test workspace isolation and outbound restrictions against file, shell, MCP and extension tools. The Azure firewall does not govern these flows. |
| H02 endpoint | **Implemented in code:** `scripts/foundry.py` requires an HTTPS Azure OpenAI host and checks it against the approved ARM resource. | **Unverified end-to-end:** test actual TLS, redirects and destination of every client feature; ARM matching is not a network egress policy. |
| H03-H05 JSONC, `source`, vault failure | **Implemented in code:** the Python launcher parses JSON, never sources `.env`, does not rewrite Copilot's JSONC, and stops on invalid configuration or vault errors/empty secret. | **Pending:** run negative integration tests on supported client versions; historical Bash reproductions are not evidence of a current exploit. |
| H06 key precedence/lifetime | **Partially implemented:** selected inherited provider variables are removed, the key is fetched on each launch and is not put in arguments or saved to a shared file. | **Residual:** the running Copilot process receives the key in its environment. Verify inherited settings and child processes, rotate both the vault secret **and** underlying Azure OpenAI key, and test active-session revocation. |
| H07 effective provider | **Not verified:** `doctor` checks identity, ARM endpoint and deployments but neither reads the key nor performs inference; `--smoke-test` sends one small request directly, not through Copilot. | **Gate:** verify actual CLI, subagent, auxiliary-model and VS Code routes by version/profile, including conflicting `providers.json`, with synthetic content. |
| H08 network/observability | **Declared, not verified in Azure:** `infra/resources.bicep` sets public access with default deny and IP rules for newly created resources, Key Vault RBAC/purge protection/90-day retention; provisioning reviews what-if. | **Pending:** reused resources' network rules/RBAC are not enforced by this template. Check each live firewall and role assignment. No diagnostic settings or security alerts are provisioned; assign an owner and configure/test both. |
| Vault bypass | **Declared, not verified:** new vaults use `networkAcls.bypass: 'AzureServices'`. | **Pending:** justify each trusted-service exception or narrow it; it is not an unrestricted bypass for all Azure services. Confirm effective rules on existing vaults separately. |
| Data and endpoint controls | **Not evaluable here:** no tenant configuration, device posture, data retention/residency or egress inventory was examined. | **Gate:** classify allowed data, approve deployment/SKU processing geography, verify device encryption/patching and inventories for GitHub, extensions, MCP and tools. `.gitignore` does not prevent an agent from reading a local file. |
| Limits and response | **Partial:** deployment TPM is checked for launch; optional budgets send notifications, not hard stops. | **Pending:** define incident owner, revocation time, quotas, alert delivery and a tested stop procedure before sustained use. |

**Acceptance gates (public profile).** The infrastructure owner records P01
(no private networking introduced by the plan) and the actual settings on
*both* services; P05 tests denied IPs **only** for `public_selected_ips`,
whereas P06/P07 prove access with a valid key and rejection without one from
an alternate IP for `public_any_ip`. The client owner runs P02 (streaming,
tools and subagents), P03 (missing/invalid key) and P04 (Entra identity without
vault access: no key issued and no inference; an already copied key still works
until rotated), P08-P10 (destination/TLS, vault failure, conflicting/invalid
configuration), P12-P13 (key regeneration and intact JSONC) and P15 (canary
credential absent from logs). P11 (token renewal) applies to a **future
Entra-based inference client**, not the current API-key inference path.
Security/operations owners run P14 (file and network egress isolation) and
P16 (measurable throttling/alert delivered to the named responder). Also
retain the historical report's T07 (provider conflict), T12 (outbound
destination) and T16 (concurrent configuration integrity) as open tests.
Mocks cover code failure paths, **not** the cloud, provider selection,
streaming, editor persistence or revocation. Use synthetic data; keep
versions, results and operational identifiers in a private evidence store.
Do not promote internal/customer data to this workflow until the applicable
gates pass and the residual risk of the selected public profile is accepted.

Microsoft references: [Foundry Tools network rules](https://learn.microsoft.com/azure/ai-services/cognitive-services-virtual-networks),
[Key Vault network security](https://learn.microsoft.com/azure/key-vault/general/network-security),
[Key Vault security practices](https://learn.microsoft.com/azure/key-vault/general/secure-key-vault#network-security).
The [Azure OpenAI security baseline](https://learn.microsoft.com/security/benchmark/azure/baselines/azure-openai-security-baseline)
also recommends restricted networks, least privilege and resource logs, but
warns that its benchmark version may contain outdated guidance.

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
