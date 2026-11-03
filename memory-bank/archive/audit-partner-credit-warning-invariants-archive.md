# Archive: Knowledge-archaeology audit of the partner credit warning

## Metadata
- Task: audit-partner-credit-warning-invariants
- Complexity: Level 1 (analysis only, no code changes)
- Branch: task/audit-partner-credit-warning-invariants (off origin/banyan)
- Completed: 2026-11-03

## Summary
Audited Odoo 18's `sale.order._compute_partner_credit_warning` (`addons/sale/models/sale_order.py:770-781`) and its callee `account.move._build_credit_warning_message` (`addons/account/models/account_move.py:1846-1891`). The audit records every implicit invariant a naive refactor could silently break, with file:line, failure mode, and confidence.

## Solution
- Rev 1 (80401fbb) contained:
  - 29 invariants across 10 categories: access/sudo, company context, state gates, `commercial_partner_id`, currency, boundaries, `_()`, singleton contracts, depends/cache semantics, and the return-value/view contract
  - a "Looks Like an Invariant But Isn't" calibration section
  - latent defects
  - 12 proposed `systemPatterns.md` ENFORCED entries
- Rev 2 (914f0fed): one refute-oriented sub-agent per ENFORCED entry checked it against source only. All 12 were upheld (3 TRUE, 9 TRUE WITH CAVEATS, 0 FALSE).
  - Withdrawn: A2's language rationale for not sudo-ing the helper, and I2's "recomputed on read" claim.
  - Corrected: F1's "UI-only" description of `use_partner_credit_limit`.
  - Re-rated: L1, for multi-currency mislabelling.
  - Added: L7–L10 (negative limits, receivables posted on contacts, no `depends_context`, missing dependencies on the invoice side).
- Reflection: b1fd7e27.

## Files Changed
- `memory-bank/creative/audit-partner-credit-warning-invariants-knowledge-archaeology.md`: the deliverable (rev 2)
- `memory-bank/tasks/audit-partner-credit-warning-invariants.md`: task file
- `memory-bank/reflection/audit-partner-credit-warning-invariants-reflection.md`: reflection
- `memory-bank/agent-rules/_learned/odoo-compute-fields.md`: +1 bullet (non-stored cache semantics, `depends_context`), evidence_count 2
- `memory-bank/agent-rules/_learned/verification-and-research.md`: new (refute-oriented code-level verification; `git grep` in sub-agents)
- No source code changed.

## Notes
- **Follow-up (not done here):** apply the 12 verified ENFORCED entries in audit §4 to `memory-bank/systemPatterns.md`. That file is Core State, so it should go through a separate reviewed change.
- **Follow-up candidates:** latent defects L1 (MED–HIGH, discarded `with_company` plus multi-currency mislabelling), L2, and L7 are worth their own tasks. Each fix is a behaviour change and needs its own test.
- `/bmb:rules-index` has not been run on this project (no `agent-rules-index.md` exists). Run it to index the learned rules.
- Workflow friction recorded in the reflection: `/bmb:task` has no analysis-only path, and audit documents have no dedicated memory-bank bucket.
