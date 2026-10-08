# 09. Another Windows PC with WSL

English | [Español](es/09-second-pc.md)

This is a client installation, not another Azure deployment.
Install/verify WSL, Ubuntu and VS Code Windows with the WSL extension. Request
administrator consent and a reboot when required by the official WSL installer.
Install Python, Azure CLI and Copilot CLI inside the intended distribution.

Use a reviewed release/checkpoint of this version in a permanent Linux directory.
Verify its `SHA256SUMS`. Do not copy wrappers referencing the original PC.
Do not copy Azure caches, editor databases, session history or MCP credentials.

```bash
az login --tenant YOUR_TENANT_ID
python3 scripts/foundry.py configure work
python3 scripts/foundry.py doctor work
export PATH="$HOME/.local/bin:$PATH"
copilot-foundry work
code .
```

Verify VS Code is connected to the same WSL distribution and user. Generate a
new [editor import](03-configure-vscode.md), using the destination profile's
actual path. Create fresh local encrypted references, not copied references.

Run a small chat/tool test with a new file. Record which profile/model pairs
were tested; do not equate configuration with runtime validation.
Both PCs share Azure quotas and budget; a new PC does not add capacity.
An old session ID may not exist on the new PC; use available history or a
redacted handoff, not a full private session archive.

MCP servers are optional and separate. Inventory `/mcp` first. Prefer official
Azure, GitHub, filesystem and memory servers; grant only intended directories,
use local authentication and fresh private memory storage. Do not copy another
PC's absolute executable paths or include mail connectors in this setup.
