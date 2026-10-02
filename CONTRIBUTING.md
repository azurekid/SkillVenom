# Contributing to SkillVenom

SkillVenom is an authorized security-awareness and assessment library. Every contribution must keep the
repository in a state that cannot accidentally become operational. Read `SECURITY.md` before you start.

## Non-negotiable safety rules

1. **Fixtures stay inert.** Poisoned `SKILL.md` files and payloads live inside their scenario folder.
   Never place hostile content in `.agents/skills/`, `.github/skills/`, `copilot-instructions.md`, or any
   active skills/prompt directory in this repository.
2. **Dry-run is mandatory and zero-write.** Every scenario must define `modes.dry-run` with
   `writes_allowed: false`.
3. **Lab-impact is canary-only.** If present, it requires `requires_operator_approval: true` and at least
   one explicit disposable `canary_targets` entry. Never target production or privileged objects.
4. **No secrets, ever.** No real credentials, tokens, client secrets, signing keys, or out-of-band
   approval phrases in any manifest, payload, fixture, or README. Use canary markers and the reserved
   `.example` domain.
5. **Preserve auditing.** Payloads must never instruct an agent to suppress, delete, or falsify security
   telemetry.
6. **One benign task.** The target agent gets a single benign task that forbids remediation and conflicts
   with the embedded request.

## Add a scenario

1. Copy `use-cases/_template/` into `use-cases/<endpoint>/<id>/` (next free id, e.g. `vs011`).
2. Fill in `scenario.json`. Required: `id`, `title`, `endpoint`, `attack_vector`, `target_task`,
   `artifacts`, `mcp`, `modes`. Recommended catalog metadata: `summary`, `source_endpoint`, `severity`,
   `status`, `techniques`, `tags`, `owasp_llm`, `mitre_atlas`, `references`, `cleanup`. See
   `framework/taxonomy.json` for vector/framework mappings.
3. Write the payload(s) and any skill fixture (see the `payload-author` persona in `.agents/skills/`).
4. Write a `README.md` covering: assessment, artifacts, preconditions, target setup, execute, expected
   results, finding classification, evidence, and mitigations.
5. Validate and regenerate the catalog:

   ```bash
   python3 framework/scripts/scenario.py validate use-cases/<endpoint>/<id>/scenario.json
   python3 framework/scripts/scenario.py plan use-cases/<endpoint>/<id>/scenario.json --mode dry-run
   python3 framework/scripts/scenario.py catalog --write
   python3 -m unittest discover -s framework/tests -v
   ```

6. Have the `scenario-safety-reviewer` persona review before opening a pull request.

## CI

`.github/workflows/validate.yml` runs `validate --all`, `catalog --check`, and the framework tests on
every push and pull request. A stale `use-cases/CATALOG.md` fails CI; always run `catalog --write` after
adding or changing a scenario.
