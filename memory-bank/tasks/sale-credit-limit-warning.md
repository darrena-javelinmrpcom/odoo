---
slug: sale-credit-limit-warning
feature: sale-credit-limit-warning
status: INITIALIZED
---

# sale-credit-limit-warning: Customer Credit Limit Warning

**Complexity**: Level 2 (inherited from sale-credit-limit-warning)
**Status**: INITIALIZED
**Roadmap**: sale-credit-limit-warning
**Branch**: feature/sale-credit-limit-warning
**Worktree**: N/A (primary checkout — `docker compose up --watch` syncs `./addons` from here)

## Task Description

Add a customer credit limit warning on the Sale Order form. The warning is a computed text message that appears as a banner when a customer is approaching or exceeding their credit limit. Yellow at 80% of limit, red over 100%. The message includes the credit limit, current outstanding receivables, and how much this order would add. Empty (no banner) when the customer has no credit limit set or is well within limit.

Source: Week 4 workshop, Exercise 4E — field `credit_warning_message` (Text, computed, not stored), conditional colour-coded alert at the top of the Sale Order form.

### Notes from discovery (existing code)

- Core `sale` already has `sale.order.partner_credit_warning` (`addons/sale/models/sale_order.py:299`, compute at `:771`) rendered as a single yellow banner (`addons/sale/views/sale_order_views.xml:303`). Fires only when *over* the limit, only for `draft`/`sent`, only when `company.account_use_credit_limit` is enabled.
- Core formula (`addons/account/models/account_move.py:1846`) = `credit + credit_to_invoice + current_amount`; exercise spec = `partner.credit + amount_total`.
- `res.partner.credit`, `credit_to_invoice`, `credit_limit` (`addons/account/models/partner.py:517-527`) are restricted to accounting groups → read via `sudo()`.
- `credit` is a non-stored compute; `credit_limit` is `company_dependent`, company currency. Order amount must be converted from order currency.
- Implement in a custom addon, not by editing core `sale`. Tests to mirror: `addons/sale/tests/test_credit_limit.py`.

---

## Execution State

**Build Status**: RUNNING
**Current Phase**: PLAN
**Current Step**: Planning in progress
**Can Resume**: YES

### Active Sub-Agents
(none)

### Completed Steps
- Step 0.1: Task auto-provisioned from feature sale-credit-limit-warning
