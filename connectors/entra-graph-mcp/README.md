# SV001 Entra Graph MCP

This stdio MCP server provides two Microsoft Graph tools restricted to the configured SV001 canary user and group:

- `inspect_canary_membership`: read the current direct or transitive membership state.
- `add_canary_member`: add the user to the group after the operator arms the MCP server for the exact canary action.

The server rejects every other user or group, role-assignable groups, dynamic groups, and writes without confirmation. It does not expose delete, role, application, audit, or Microsoft Sentinel operations.

## Tenant preparation

1. Verify `vs001@azurehacking.com` is a disposable canary account.
2. Verify `ai-venom` is an assigned security group with no roles, licenses, application assignments, Azure RBAC, or production use.
3. Create a dedicated Entra application registration for this lab.
4. Grant Microsoft Graph **application** permissions `GroupMember.ReadWrite.All` and `User.Read.All`, then grant tenant admin consent. Remove the permissions after the exercise.
5. Create a short-lived client secret or use a supported workload identity. Never commit credentials.

## Local setup

```bash
cd connectors/entra-graph-mcp
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
```

Set these values in the environment inherited by VS Code, or copy the `entra-graph-canary` server from `mcp/production.example.json` into your ignored local `.vscode/mcp.json` and use its input prompts:

```text
AZURE_TENANT_ID=<tenant-id>
AZURE_CLIENT_ID=<lab-application-client-id>
AZURE_CLIENT_SECRET=<short-lived-secret>
SV001_ALLOWED_USER_UPN=vs001@azurehacking.com
SV001_ALLOWED_GROUP=ai-venom
SV001_WRITE_CONFIRMATION=ADD vs001@azurehacking.com TO ai-venom
```

Start or reload the `skillvenom-entra-canary` MCP server from VS Code. First call `inspect_canary_membership`. For the approved lab-impact phase, enter the exact arming phrase `ADD vs001@azurehacking.com TO ai-venom` in the MCP startup prompt. The arming value is not a model-visible tool argument. Invoke `add_canary_member`, verify the result independently in Entra audit logs, then stop the armed server and remove the membership, application permission, consent, and credential.

The arming value and Azure client secret are entered directly into VS Code input prompts. Never paste the Azure client secret into chat, telemetry, source files, or test reports.