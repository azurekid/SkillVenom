<img width="659" height="616" alt="image" src="https://github.com/user-attachments/assets/26346397-c78d-4af1-a30b-42cf477dd4e3" />

# Project SkillVenom: Advanced Agent Exploitation & Cloud Audit Suite

Project **SkillVenom** is a weaponized penetration testing, compliance, and security awareness framework designed to evaluate vulnerabilities in production **AI Agent Architectures**. 

Unlike abstract token simulations, this framework tests against **live corporate sandboxes** (Microsoft Entra ID Tenants, Azure Subscriptions, GitHub Organizations, and Azure DevOps Instances). By pairing standard `.agent.md` or `SKILL.md` open frontmatter configurations with real cloud SDKs, Project SkillVenom demonstrates a critical architectural reality: **the security flaw lies in the cognitive routing of the LLM, which uses its legitimate cloud administrative privileges to execute malicious commands.**

---

## Threat Vector Realities
*   **Identity Trust:** The target agent does not require binary modification, reverse engineering, or classical malware delivery. It executes unauthorized infrastructure shifts using its **legitimate enterprise service principal tokens**.
*   **Command Hijacking:** Attackers leverage advanced **Structural Obfuscation** (Markdown Table breakouts, Fake Stack Traces, and Base64 Lures) to blend malicious instructions into standard engineering logs. The LLM processes these logs as instructions rather than passive text data.
*   **Human Decoying:** The agent is manipulated into generating a fake successful status JSON report for the frontend user interface while simultaneously invoking destructive background tool APIs.

---

## 📂 Repository Architecture

```text
project-skillvenom/
├── README.md                          # Global weaponized suite execution guide
├── skill.md                           # Standardization template for creating new scenarios
├── config/
│   └── .env.template                  # Enterprise connection mapping schema
├── core/
│   ├── __init__.py
│   ├── auth.py                        # Live Entra ID Token Broker & Azure Credential Manager
│   └── engine.py                      # Universal frontmatter parsing engine
└── use-cases/                         # Categorized Live Exploitation Suites
    ├── 01-entra-jit/                  # Live Entra ID Tenant Exploitation
    │   ├── README.md                  # Scenario brief and JIT risk profile
    │   ├── agent.skill.md             # Standard universal frontmatter configuration
    │   ├── live_test.py               # EXECUTES REAL MS GRAPH CALLS
    │   └── payloads/                  
    │       └── 01_table_breakout.txt  # Markdown telemetry matrix exploit
    └── 02-azure-arm/                  # Live Azure Subscription Exploitation
        ├── README.md                  # Scenario brief and Network Security Group risk profile
        ├── agent.skill.md             # Standard universal frontmatter configuration
        ├── live_test.py               # ALTERS LIVE NETWORK SECURITY GROUPS (NSGs)
        └── payloads/                  
            └── 03_stack_trace.log     # System error traceback injection
```

---

## Live Use-Case Folder Standard
Every targeted environment within `use-cases/` is isolated and self-contained to support realistic red-team / audit drills:
*   **`agent.skill.md`**: The system prompt following the `agentskills.io` standard. It contains the YAML frontmatter describing the allowed tool schema. **This file remains completely unmodified during attacks**.
*   **`payloads/`**: Houses text files simulating raw data ingested by the agent (e.g., tickets, log streams, Bicep code). Instructions are nested inside standard data elements to bypass basic keyword blocklists.
*   **`live_test.py`**: The actual execution test harness. It maps the agent parameters to an active LLM session (OpenAI GPT-4o / Anthropic Claude), captures the output state, borrows the authentication token from the central broker, and fires **real API calls** at the cloud tenant.

---
