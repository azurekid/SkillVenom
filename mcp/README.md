# MCP Profiles

`production.example.json` shows the preferred server for each supported endpoint:

| Endpoint | Preferred server | Authentication |
| :--- | :--- | :--- |
| Azure | Microsoft Azure MCP Server | Azure identity chain |
| Entra ID | Azure MCP plus the narrow canary adapter when Graph write coverage is required | Azure identity chain or dedicated lab application |
| GitHub | GitHub's hosted MCP server | Native GitHub OAuth |
| Azure DevOps | Microsoft Azure DevOps MCP Server | Microsoft identity flow |

Copy only the servers needed for a demo into `.vscode/mcp.json`. The npm package versions in the example were verified on 2026-09-30; review and deliberately update those pins as part of normal dependency maintenance.

Prefer managed identity, workload identity federation, native OAuth, or existing developer CLI sessions. Avoid long-lived personal access tokens and client secrets. Endpoint policy and identity permissions must constrain writes independently of model instructions.

Not every common MCP server exposes every high-impact operation. Add a narrow adapter only for a documented coverage gap, enforce exact target allowlists, and keep that adapter shared across scenarios for the endpoint.