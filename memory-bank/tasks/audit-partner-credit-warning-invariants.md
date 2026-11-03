---
slug: audit-partner-credit-warning-invariants
legacy_id:
feature:
status: BUILD_COMPLETE
---

# audit-partner-credit-warning-invariants: Knowledge-archaeology audit of the partner credit warning

**Complexity**: Level 1
**Status**: BUILD_COMPLETE
**Roadmap**: N/A
**Branch**: task/audit-partner-credit-warning-invariants
**Worktree**: N/A (Level 1 uses direct branch, not worktree)

## Task Description

Run a knowledge-archaeology audit on `_compute_partner_credit_warning` at
`addons/sale/models/sale_order.py:770-781` and its callee `_build_credit_warning_message` at
`addons/account/models/account_move.py:1846-1891`. Surface every implicit invariant a naive refactor
might silently break. For each one give the name, file:line, what would break if it were dropped, and a
confidence rating (HIGH/MED/LOW). Include a "Looks Like an Invariant But Isn't" calibration section and a
"Recommended systemPatterns.md ENFORCED Entries" section. Cover sudo, with_company, with_context,
@api.depends ordering, discarded-return idioms, multi-record vs singleton contracts, currency assumptions,
state-machine gates, boundary conditions, commercial_partner_id rollups, `_()` idioms, and access-control
side effects. Do NOT refactor. Do NOT read `memory-bank/agent-rules/_learned/`. Audience: senior Odoo
developer.

## Implementation Notes

- This is an analysis-only deliverable, with no code changes. The fast-path TDD agent and affected-test run
  were not applicable and were skipped.
- Deliverable: `memory-bank/creative/audit-partner-credit-warning-invariants-knowledge-archaeology.md`
  (invariants across 10 categories, 15 calibration items, 10 latent defects, and 12 proposed ENFORCED entries).
- Rev 2 (2026-11-03): each ENFORCED entry was verified at code level by a dedicated sub-agent (12/12 upheld,
  0 refuted). Corrections were applied throughout and verification results recorded in §5 of the audit doc.
- The proposed `systemPatterns.md` entries are **not applied**. That file is Core State and must go through
  `chore/banyan-admin`.

---

## Execution State

**Build Status**: COMPLETE
**Current Phase**: BUILD_COMPLETE
**Can Resume**: NO

### Active Sub-Agents
(none)

### Completed Steps
- Discovery + clean-tree gate (clean)
- Branch `task/audit-partner-credit-warning-invariants` cut from `origin/banyan`
- Source audit (subjects + partner/sale/account/view/translate/fields/test/custom-addon call sites)
- Audit document written
