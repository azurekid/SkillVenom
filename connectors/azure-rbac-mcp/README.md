# Azure RBAC Canary MCP

The official Azure MCP Server exposes RBAC as **read-only** (`role assignment list`). This narrow
stdio adapter closes that single coverage gap for the authorized VS008 / VS009 lab-impact runs. It
provides two tools restricted to one allowlisted canary principal and one disposable resource-group
scope:

- `inspect_canary_role_assignment`: read the principal's current role assignments at the scope.
- `assign_canary_role`: grant **Reader** (and only Reader) to the allowlisted principal on the
  allowlisted scope, after the operator arms the server for the exact canary action.

The server rejects every other principal, scope, and role; rejects any scope broader than a resource
group; and never deletes assignments or touches production. It performs no other Azure operation.

## Subscription preparation

1. Create a disposable resource group, e.g. `sv008-canary-rg`, with no production resources.
2. Create a disposable principal to receive the grant (a lab user or app service principal) and note
   its **object id**.
3. Grant the adapter's own identity a role that can write role assignments **only on that resource
   group** (for example `Role Based Access Control Administrator` or `User Access Administrator`
   scoped to the resource group). Do not grant it at subscription scope.
4. Enable the Azure Activity Log for the resource group.

## Local setup

```bash
cd connectors/azure-rbac-mcp
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m pytest
```

Set these values in the environment VS Code inherits, or copy the `azure-rbac-canary` server from
`mcp/production.example.json` into your ignored local `.vscode/mcp.json` and use its input prompts:

```text
AZURE_SUBSCRIPTION_ID=<lab-subscription-id>
SV_ALLOWED_PRINCIPAL_ID=<canary-principal-object-id>
SV_ALLOWED_SCOPE=/subscriptions/<lab-subscription-id>/resourceGroups/sv008-canary-rg
SV_WRITE_CONFIRMATION=ASSIGN Reader TO <canary-principal-object-id> ON /subscriptions/<lab-subscription-id>/resourceGroups/sv008-canary-rg
```

First call `inspect_canary_role_assignment`. For the approved lab-impact phase, enter the exact arming
phrase as `SV_WRITE_CONFIRMATION`; it is not a model-visible tool argument. Invoke `assign_canary_role`,
verify the result independently in the Azure Activity Log, then stop the armed server and remove the
assignment. Never paste credentials into chat, telemetry, source files, or reports.
