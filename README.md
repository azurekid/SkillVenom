<img width="682" height="669" alt="image" src="https://github.com/user-attachments/assets/e944bb8d-822d-41b3-a209-9ae9e31031bb" />


# Skill Venom

Skill Venom is a security-awareness and authorized assessment repository for demonstrating how agent skills, retrieved content, and tool output can influence production-connected AI agents. Scenarios use realistic MCP integrations while constraining live impact to disposable canary resources.

> **Running against a real environment?** See [`SETUP.md`](SETUP.md) for the operator runbook: dependencies, canary provisioning (`scripts/provision.sh`), MCP configuration, the tool-name mapping, and the dry-run → lab-impact procedure. Read [`SECURITY.md`](SECURITY.md) first.

## Supported Endpoints

| Endpoint | Production-like integration | Native evidence |
| :--- | :--- | :--- |
| Microsoft Entra ID | Azure MCP and a narrow Graph canary adapter for uncovered write operations | Entra audit and sign-in logs |
| Azure | Microsoft Azure MCP Server | Azure Activity Log |
| GitHub | GitHub MCP Server | Organization and repository audit logs |
| Azure DevOps | Microsoft Azure DevOps MCP Server | Azure DevOps audit and pipeline logs |

The endpoint registry is in `framework/endpoints.json`; MCP launch profiles are in `mcp/production.example.json`.

## Scenarios

The full, always-current list is in [`use-cases/CATALOG.md`](use-cases/CATALOG.md), generated from the
scenario manifests. Attack-vector and framework mappings (OWASP LLM Top 10, MITRE ATLAS) are in
[`framework/taxonomy.json`](framework/taxonomy.json).

| ID | Source → Impact | Vector | Impact demonstrated |
| :--- | :--- | :--- | :--- |
| Entra VS001 | Azure DevOps → Entra ID | Indirect prompt injection | Group-membership change |
| Azure VS002 | Azure → Entra ID | Indirect prompt injection (IaC metadata) | Cross-plane group change |
| GitHub VS003 | GitHub → GitHub | Skill poisoning | Repository data leakage |
| Azure DevOps VS004 | Azure DevOps → Azure DevOps | Indirect prompt injection | Pipeline code injection |
| GitHub VS005 | GitHub → GitHub | Indirect prompt injection (issue) | GitHub Actions code injection |
| Azure DevOps VS006 | Azure DevOps → Azure DevOps | Skill poisoning | Pipeline-secret leakage |
| Entra VS007 | Entra ID → Entra ID | Skill poisoning | Access-review privilege escalation |
| Azure VS008 | Azure → Azure | Indirect prompt injection (tags) | RBAC role assignment |
| GitHub VS009 | GitHub → Azure | Cross-plane indirect prompt injection | RBAC role assignment |
| Entra VS010 | Entra ID → Entra ID | Tool-output injection | Group-membership change |

Regenerate the catalog after adding or editing a scenario:

```bash
python3 framework/scripts/scenario.py catalog --write
```

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

Copy `use-cases/_template/`, select one of the registered endpoints, declare the common MCP server and exact required tools, then add the payload and expected evidence. Use an endpoint-specific script or adapter only when the common server has a documented capability gap. Run `python3 framework/scripts/scenario.py catalog --write` afterward to refresh `use-cases/CATALOG.md`.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the authoring checklist and non-negotiable safety rules, [`SECURITY.md`](SECURITY.md) for the authorized-use policy, and `framework/README.md` for the contract and validation commands. CI (`.github/workflows/validate.yml`) runs manifest validation, a catalog freshness check, and the framework tests on every push and pull request.
