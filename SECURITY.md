# Security and Authorized-Use Policy

SkillVenom is a defensive security-awareness and **authorized assessment** library. It exists to help
teams test whether their AI agents correctly treat untrusted content as data and whether their tool,
identity, and audit controls contain agent misbehavior.

## Intended use

- Authorized red-team / purple-team exercises against systems you own or are explicitly permitted to test.
- Security-awareness training and agent-hardening evaluations.
- CI gates that verify an agent refuses injected instructions.

## Rules of engagement

Before any `lab-impact` run, record: the authorized tenant/org/subscription, the dedicated test identity,
the disposable canary targets, the testing window, the approver, evidence-retention rules, and an
emergency contact. Define stop conditions for any unexpected or production target, loss of audit
visibility, or privilege escalation beyond the declared canary.

All scenarios are built so that a **dry-run performs no writes**, and an optional **lab-impact** run can
affect only explicitly declared disposable canary objects, under operator approval, with endpoint-native
auditing preserved.

## What this repository does not contain

- No real credentials, tokens, or secrets. Sensitive-looking strings are **canary markers**.
- No exfiltration to real infrastructure. Destinations are disposable canaries or the reserved
  `.example` domain.
- No detection-evasion or audit-suppression instructions.
- No active/poisoned skills installed into this repository's agent directories. Weaponized `SKILL.md`
  files are inert fixtures inside their scenario folder and are only copied into a disposable target
  workspace for an authorized exercise.

## Do not

Do not use these fixtures against systems you are not authorized to test, do not point them at production
or privileged objects, and do not weaken a connector, broaden an allowlist, or disable auditing to make an
injection succeed. Misuse is outside the purpose of this project.

## Reporting

If you find a scenario that leaks a real secret, targets a non-canary object by default, or can become
operational inside this repository, open an issue marked security or contact the maintainer privately.
