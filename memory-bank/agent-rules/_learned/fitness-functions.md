---
name: Fitness Functions (learned)
globs: ["scripts/fitness/**"]
paths: ["scripts/fitness/"]
topics: ["fitness-function", "static-analysis", "allow-list", "testing"]
priority: low
auto_generated: true
derived_from: [fitness-no-cross-module-imports]
evidence_count: 1
last_validated: 2026-11-03
---

# Fitness Functions

- Validate a new or changed gate with independent adversarial scenarios (violation, compliant, evasion, false positives, config/CLI), each run by a separate agent that did not write the gate, plus a run over a large real corpus. Same-author unit tests miss gaps.
- Make allow-list sources additive (default file + env + CLI) with an explicit opt-out flag. Never let an env var or flag silently replace the default exceptions.
- Report allow-listed hits (with rule and justification) instead of dropping them, and reject allow rules that have no justification.
