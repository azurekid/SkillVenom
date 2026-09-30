<img width="682" height="669" alt="image" src="https://github.com/user-attachments/assets/e944bb8d-822d-41b3-a209-9ae9e31031bb" />


# SkillVenom

SkillVenom is a security-awareness and authorized assessment repository for demonstrating how agent skills, retrieved content, and tool output can influence production-connected AI agents. Scenarios use realistic MCP integrations while constraining live impact to disposable canary resources.

## Supported Endpoints

| Endpoint | Production-like integration | Native evidence |
| :--- | :--- | :--- |
| Microsoft Entra ID | Azure MCP and a narrow Graph canary adapter for uncovered write operations | Entra audit and sign-in logs |
| Azure | Microsoft Azure MCP Server | Azure Activity Log |
| GitHub | GitHub MCP Server | Organization and repository audit logs |
| Azure DevOps | Microsoft Azure DevOps MCP Server | Azure DevOps audit and pipeline logs |

The endpoint registry is in `framework/endpoints.json`; MCP launch profiles are in `mcp/production.example.json`.

## Scenarios

| ID | Source | Impact | Vector |
| :--- | :--- | :--- | :--- |
| Entra VS001 | Azure DevOps telemetry | Entra ID | Markdown table indirect prompt injection |
| Azure VS002 | Bicep pull-request metadata | Entra ID | ARM/Bicep metadata contamination |

## Scenario Layout

```text
use-cases/<endpoint>/<scenario>/
├── scenario.json       # Endpoint, MCP dependencies, modes, evidence, and canaries
├── README.md           # Threat model and operator runbook
├── payloads/           # Untrusted retrieved content, logs, tickets, and attachments
├── weaponized-skill/   # Inert malicious skill fixtures for skill-poisoning scenarios
└── scripts/            # Optional setup, evidence, or cleanup helpers
```

Trusted evaluator and authoring workflows belong in `.agents/skills/`. Weaponized skills remain inert inside their scenario. Copy a fixture into a disposable target workspace's `.agents/skills/` directory only for an authorized exercise; use `.github/skills/` only when a host does not scan the generic location.

## Run a Scenario

```bash
python3 framework/scripts/scenario.py validate --all
python3 framework/scripts/scenario.py plan use-cases/entra/vs001/scenario.json --mode dry-run
```

You can also invoke `/run-skillvenom-scenario` in VS Code with the manifest path and mode.

## Authoring Personas

Invoke `/use-case-orchestrator` with the source endpoint, impact endpoint, and idea. It runs the specialist personas in order:

| Stage | Persona | Responsibility |
| :--- | :--- | :--- |
| 1 | Scenario architect | Manifest, threat model, and runbook |
| 2 | Payload author | Inert source content and skill fixtures |
| 3 | Endpoint integrator | MCP servers, tools, canaries, and evidence |
| 4 | Safety reviewer | Contract, trust-boundary, and activation review |

The individual skills remain available for a targeted revision. They author repository artifacts only; hostile fixtures remain inactive until copied into a disposable target workspace.

Every scenario must provide a zero-write `dry-run`. A `lab-impact` mode is optional and must declare disposable canary targets, require operator approval, preserve endpoint-native auditing, and use a least-privileged identity. Payloads never contain credentials or approval values.

## Add a Scenario

Copy `use-cases/_template/`, select one of the registered endpoints, declare the common MCP server and exact required tools, then add the payload and expected evidence. Use an endpoint-specific script or adapter only when the common server has a documented capability gap.

See `framework/README.md` for the contract and validation commands.
