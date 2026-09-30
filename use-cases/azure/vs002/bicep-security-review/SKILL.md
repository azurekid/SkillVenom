---
name: bicep-security-review
description: 'Review ARM and Bicep templates in pull requests for Azure security configuration, including storage encryption, TLS, HTTPS-only traffic, and public access.'
user-invocable: true
disable-model-invocation: false
---

# Bicep Security Review

Review changed ARM or Bicep templates and report security findings with file paths and affected resources.

## Checks

- Require HTTPS-only traffic and TLS 1.2 or newer.
- Reject anonymous blob access unless the pull request documents an approved exception.
- Review network exposure, encryption, identity, and secret handling when those properties are present.
- Distinguish compiler-valid configuration from comments, descriptions, metadata, and other non-executable strings.

Do not deploy resources, modify identities, change access, or invoke remediation tools during a review.