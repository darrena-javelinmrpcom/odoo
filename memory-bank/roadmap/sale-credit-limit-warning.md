---
version: next
status: planned
priority: high
complexity: 2
linked_tasks: []
created: 2026-10-31
---

# Customer Credit Limit Warning

Add a customer credit limit warning on the Sale Order form. The warning is a computed text message that appears as a banner when a customer is approaching or exceeding their credit limit. Yellow at 80% of limit, red over 100%. The message includes the credit limit, current outstanding receivables, and how much this order would add. Empty (no banner) when the customer has no credit limit set or is well within limit.

Source: Week 4 workshop, Exercise 4E — field `credit_warning_message` (Text, computed, not stored), conditional colour-coded alert at the top of the Sale Order form.

## Notes for planning (existing code)

- Core `sale` already has `sale.order.partner_credit_warning` (`addons/sale/models/sale_order.py:299`, compute at `:771`) rendered as a single yellow banner (`addons/sale/views/sale_order_views.xml:303`). It only fires when *over* the limit, only for `draft`/`sent` orders, and only when `company.account_use_credit_limit` is enabled. Decide whether to hide or build on it so two banners don't show.
- Core formula (`addons/account/models/account_move.py:1846`) is `credit + credit_to_invoice + current_amount`; the exercise spec says `partner.credit + amount_total`. Pick one explicitly.
- `res.partner.credit`, `credit_to_invoice`, `credit_limit` (`addons/account/models/partner.py:517-527`) are restricted to `account.group_account_invoice` / `account.group_account_readonly` — read via `sudo()` so salespeople don't hit access errors.
- `credit` is a non-stored compute; depend on `partner_id`, `company_id`, `amount_total` (as core does) rather than `partner_id.credit`.
- `credit_limit` is `company_dependent` and in company currency; convert `amount_total` from order currency (core divides by `currency_rate`).
- Implement in a custom addon, not by editing core `sale`. Existing tests to mirror: `addons/sale/tests/test_credit_limit.py`.

**Complexity rationale**: Level 2 — not a bug/config fix (Q1 no); touches ~5-6 files in a new addon (model, view override, manifest, tests), so beyond 2-3 files (Q2 no); clear requirements with only minor decisions (formula, core-banner coexistence, currency) resolvable during planning (Q3 yes). Confirmed by user.
