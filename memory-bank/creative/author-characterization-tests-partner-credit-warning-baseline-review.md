# Baseline Review: sale.order._compute_partner_credit_warning

**Task**: author-characterization-tests-partner-credit-warning
**Date**: 2026-11-03
**Test file**: `custom_addons/banyan_sale_safety/tests/test_partner_credit_warning_characterization.py`
**Method under test**: `addons/sale/models/sale_order.py:771` → `addons/account/models/account_move.py:1846`

Every captured assertion is reviewed against the three-tag rubric. Each test carries the same
tag as a `# REVIEW:` comment in the test file.

| Tag | Meaning |
|---|---|
| ✓ correct | Matches what the system should do, confirmed by docs or business rules |
| ⚠ bug-preserved | Captures a real bug; locked only as a guardrail |
| ❓ unclear | Can't tell from code or docs alone; needs PM confirmation |

**Evidence sources.** The Odoo 18 documentation, queried through context7, does not describe the
credit-limit rules. The field help text in code is the documented intent:
- `res.company.account_use_credit_limit`: "Enable the use of credit limit on partners."
- `res.partner.use_partner_credit_limit`: "Set a value greater than 0.0 to activate a credit limit check"
- `res.config.settings.account_default_credit_limit`: "the default credit limit that will be used on partners that do not have a specific limit"

## Review

| # | Test | Captured | Tag | Rationale |
|---|---|---|---|---|
| A | `test_branch_a_state_sale_returns_empty` | `''` | ❓ unclear | A salesperson editing an over-limit **confirmed** order sees nothing. See Decision 2. |
| B | `test_branch_b_state_cancel_returns_empty` | `''` | ✓ correct | A cancelled order creates no credit exposure. |
| C | `test_branch_c_company_flag_off_over_limit` | `''` | ✓ correct | The feature is turned off by the company setting. |
| D | `test_branch_d_flag_on_no_credit_limit` | `''` | ✓ correct | Field help: a value > 0.0 activates the check, so 0 means no limit. |
| E | `test_branch_e_flag_on_below_limit` | `''` | ✓ correct | Under the limit. |
| F | `test_branch_f_boundary_total_equals_limit` | `''` | ❓ unclear | See Decision 1. |
| G | `test_branch_g_over_limit_only_this_draft_order` | "…(including this document): $ 1,500.00" | ✓ correct | Exposure = credit + credit_to_invoice + this order. |
| H | `test_branch_h_other_confirmed_so_plus_this_document` | "…(including sales orders and this document): $ 1,300.00" | ✓ correct | Uninvoiced confirmed orders count toward exposure. |
| I | `test_branch_i_credit_to_invoice_only_current_amount_zero` | "…(including sales orders): $ 1,500.00" | ✓ correct | The partner is already over the limit from other orders. |
| J | `test_branch_j_posted_invoice_only_current_amount_zero` | "…Total amount due: $ 1,500.00" | ✓ correct | Posted unpaid receivables count. |
| K | `test_branch_k_child_contact_uses_commercial_partner` | Parent's name and limit | ✓ correct | Receivables are tracked on the commercial entity. |
| L | `test_branch_l_state_sent_over_limit` | Same as G | ✓ correct | A sent quotation is still before confirmation. |
| M | `test_branch_m_foreign_currency_non_unit_rate` | TB 2,400 shown as "$ 1,200.00" | ⚠ bug-preserved | See Follow-up. |

**Totals**: 10 ✓ correct · 1 ⚠ bug-preserved · 2 ❓ unclear (13 branch tests, plus 1 harness smoke test that is not reviewed).

## Open decisions for PM (❓)

1. **Boundary (F): reached, or exceeded?** The check is `total_credit <= credit_limit` → no
   warning, so a partner exactly at the limit is not warned. Yet the message says "has
   **reached** its credit limit", and it only appears once the limit is exceeded. Either the
   operator should be `<` or the wording should say "exceeded".
2. **Confirmed orders (A): should the warning appear?** Today only `draft`/`sent` orders warn.
   The Part 3 mutation check showed that just adding `'sale'` to the states double-counts the order:
   a 1,500 order against a 1,000 limit reports **$ 3,000.00**, because the confirmed order sits
   in `credit_to_invoice` **and** in `current_amount`. A correct change would also need
   `exclude_amount`.

## Follow-up (⚠)

- **TASK-FUTURE-CREDIT-CURRENCY**: the warning is always rendered in `company_id.currency_id`,
  never in the order currency. The amount is converted with `amount_total / currency_rate`, so a
  salesperson quoting in TB sees dollar figures that don't match their document total. Locked
  as a guardrail by test M. To file it: `/bmb:task` (Level 1) or `/bmb:roadmap feature create`.

## How to use this baseline

- A failing ✓ test means behavior changed. Investigate before accepting the change.
- A failing ⚠ test is expected when TASK-FUTURE-CREDIT-CURRENCY lands. Update the literal in that PR.
- A ❓ test should be re-tagged ✓ (or changed in a deliberate PR) once the PM decides.
