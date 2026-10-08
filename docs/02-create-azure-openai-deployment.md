# 02. Optional Bicep infrastructure

English | [Español](es/02-create-azure-openai-deployment.md)

Reusing resources is the default. Provisioning creates billable resources and
requires separate permission from client installation. No live cloud test is
part of the default test suite.

Copy `examples/provision.example.json` **outside this repository**. Replace the
synthetic identities, resource names and region. The example reuses an existing
account/vault and deploys no models: it is not a ready-made infrastructure plan.

For new resources set the corresponding `use_existing_*` flags to false.
Set `create_resource_group` only when needed. Supply public IPv4 `allowed_ips`,
or explicitly accept broad network reachability with `allow_public_access`.
New vaults have RBAC, 90-day retention and purge protection; understand the
irreversible protection before approving creation.

Inspect model availability without inference:

```bash
python3 scripts/foundry.py catalog --subscription YOUR_SUBSCRIPTION_ID --location YOUR_REGION --model gpt-5-mini
```

Each `deployments` entry requires `model`, `version`, `deployment`, `sku`,
`capacity` (positive integer) and `allow_global` (boolean).
Use an actual catalog version and SKU. `GlobalStandard` requires `allow_global: true`;
a resource's location does not constrain global processing to that region.
`Standard` and `DataZoneStandard` have different availability/quota.
No provisioned-capacity SKU or implicit spillover is supported.

Limits from a model card are not allocation units. Preflight sums requested
capacity per model/SKU within this subscription and checks available quota.
ARM validates capacity. Missing minimum metadata is not permission to assume
the catalog's default is the minimum.

`reader_object_id` optionally creates **Secrets User**, never a writer role.
Leave it empty if access is managed externally. `budget_amount: 0` disables
budget creation. Otherwise set a first-of-month `budget_start` and private
`budget_emails`; amount uses the subscription's billing currency. Alerts do
not stop spending and existing budgets must not be overwritten.

```bash
python3 scripts/provision.py plan "$HOME/.config/my-foundry-input/provision.json" --report "$HOME/foundry-plan.json"
python3 scripts/provision.py apply "$HOME/.config/my-foundry-input/provision.json" --approval "$HOME/foundry-plan.json" --confirm YOUR_SUBSCRIPTION_ID --report "$HOME/foundry-apply.json"
```

Read the private plan's complete `changes` and warnings before applying.
The approval covers manifest/template hashes and the what-if result; changed
state requires a new plan. Reports must be new files outside the repository.
Only Create/NoChange/Ignore results are accepted: changes to existing resources,
deletions and opaque what-if results stop the operation. This is not a general
resource-management or resize tool. Matching previously created deployments
can be reused; unowned accounts are never silently adopted as new ones.

Bicep runs incrementally. No secret values appear in parameters or outputs.
After confirmed deployment, [initialize Key Vault](07-portable-keyvault-bootstrap.md).
A failed/partial apply must be inspected in ARM before retrying; do not delete
pre-existing resources as rollback. Preserve private reports and resource identity.

Sources: [Bicep](https://learn.microsoft.com/azure/azure-resource-manager/bicep/overview),
[what-if](https://learn.microsoft.com/azure/azure-resource-manager/bicep/deploy-what-if).
