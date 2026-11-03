---
slug: author-characterization-tests-partner-credit-warning
legacy_id:
feature:
status: BUILD_COMPLETE
---

# author-characterization-tests-partner-credit-warning: Characterization tests for sale.order._compute_partner_credit_warning

**Complexity**: Level 1
**Status**: BUILD_COMPLETE
**Roadmap**: N/A
**Branch**: task/author-characterization-tests-partner-credit-warning
**Worktree**: N/A (Level 1 uses direct branch, not worktree)

## Task Description

Author CHARACTERIZATION tests for `sale.order._compute_partner_credit_warning` in a new test
addon at `custom_addons/banyan_sale_safety/tests/`.

These are NOT unit tests. Read the method to discover its behavioral branches, then capture
what it currently returns for each one, byte-for-byte. Do NOT assert what it SHOULD return.

- Use `self.assertEqual` on the full string (no `assertIn`, no `assertRegex`).
- Lock language to `en_US` via a new environment, not attribute assignment:
  `cls.env = cls.env(context=dict(cls.env.context, lang='en_US'))`
  (`Environment.context` is a frozendict and envs are cached by context; assigning
  `self.env.context = {...}` mutates a shared env in place.)

### Part 1: Set up the test addon
`custom_addons/banyan_sale_safety/` with `tests/`: empty harness, `characterization` tag, install.

## Implementation Notes

- Path deviation from original brief: `custom_addons/` (custom addons convention, on
  `addons_path`) instead of `addons/` (Odoo core addons).
- Target: `addons/sale/models/sale_order.py:771` (not overridden in `custom_addons/`).
  Top-level branches:
  1. `state` not in (`draft`, `sent`) -> `''`
  2. `company_id.account_use_credit_limit` False -> `''`
  3. Otherwise -> `account.move._build_credit_warning_message(order.sudo(),
     current_amount=amount_total / currency_rate)` (`addons/account/models/account_move.py`),
     whose own sub-branches (limit not exceeded, exceeded, partner vs company limit,
     commercial partner/parent, current amount contribution) produce the strings to lock.
- Reference fixtures: core test `addons/sale/tests` `TestSaleOrderCreditLimit`.
- Test tag selector syntax: `[-][tag][/module][:Class][.method]`.
- Run command:
  `docker compose exec odoo python odoo-bin -c /etc/odoo/odoo.conf -d odoo-test -i banyan_sale_safety --test-tags characterization/banyan_sale_safety --stop-after-init --http-port=8070 --log-level=test`
  (`docker cp` the addon into the container or rebuild first; code is not bind-mounted.)

## Test Strategy

### File Organization
- **New files**:
  - `custom_addons/banyan_sale_safety/__init__.py` (empty)
  - `custom_addons/banyan_sale_safety/__manifest__.py` (`depends: ['sale']`, 18.0.1.0.0, LGPL-3)
  - `custom_addons/banyan_sale_safety/tests/__init__.py`
  - `custom_addons/banyan_sale_safety/tests/test_partner_credit_warning_characterization.py`
    (`@tagged('post_install', '-at_install', 'characterization')`)

### What NOT to Test
- Correctness of the message: characterization captures current output only.
- UI rendering of the banner: covered by `sale_credit_limit_warning` tours.

---

## Execution State

**Build Status**: BUILD_COMPLETE
**Current Phase**: PART2_COMPLETE
**Can Resume**: YES

### Active Sub-Agents
(none)

### Completed Steps
- Part 1 (test addon harness): BUILD_COMPLETE. `custom_addons/banyan_sale_safety` created; installs on `odoo-test`; tag selector `characterization/banyan_sale_safety` runs 1 smoke test (`test_harness_lang_locked`), 0 failed, 0 errors. Next: Part 2 (characterization test methods).
- Part 2 (characterization tests): BUILD_COMPLETE. Branches A-M all covered (13 tests + smoke test), all reachable; 0 failed, 0 errors on two consecutive runs. Notes (recorded, not fixed): A/B/C/D/E/F capture `''`; A/B short-circuit in the sale.order compute (never reach `_build_credit_warning_message`); `with_company` on line 773 is a no-op; child contact (K) uses commercial partner's name and limit, ignoring the child's own limit.
