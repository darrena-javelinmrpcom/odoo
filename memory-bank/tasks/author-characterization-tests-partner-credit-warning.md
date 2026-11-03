---
slug: author-characterization-tests-partner-credit-warning
legacy_id:
feature:
status: COMPLETE
---

# author-characterization-tests-partner-credit-warning: Characterization tests for sale.order._compute_partner_credit_warning

**Complexity**: Level 1
**Status**: COMPLETE
**Reflection**: memory-bank/reflection/author-characterization-tests-partner-credit-warning-reflection.md
**Archived**: memory-bank/archive/author-characterization-tests-partner-credit-warning-archive.md
**Completed**: 2026-11-03
**Latest Commit**: 14dedad8
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

### Part 2: Characterization tests
One test per branch A-M (state sale/cancel over limit, flag off, no limit, below, equal,
the four "Total amount due" variants, commercial partner, sent, foreign currency). Full-string
`assertEqual` literals captured from the actual failure diff; `\xa0` and `\n` as escapes.

### Part 3: Prove the safety net (mutation check, never committed)
Change `addons/sale/models/sale_order.py:775` from `order.state in ('draft', 'sent')` to
`order.state in ('draft', 'sent', 'sale')`, copy into the container, run: test A must fail
with a full-string diff and all others pass. Revert with `git checkout`, copy back, re-run
green, confirm `addons/` is clean.

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

**Build Status**: IDLE
**Current Phase**: COMPLETE
**Can Resume**: NO

### Active Sub-Agents
(none)

### Completed Steps
- Part 1 (test addon harness): BUILD_COMPLETE. `custom_addons/banyan_sale_safety` created; installs on `odoo-test`; tag selector `characterization/banyan_sale_safety` runs 1 smoke test (`test_harness_lang_locked`), 0 failed, 0 errors. Next: Part 2 (characterization test methods).
- Part 2 (characterization tests): BUILD_COMPLETE. Branches A-M all covered (13 tests + smoke test), all reachable; 0 failed, 0 errors on two consecutive runs. Notes (recorded, not fixed): A/B/C/D/E/F capture `''`; A/B short-circuit in the sale.order compute (never reach `_build_credit_warning_message`); `with_company` on line 773 is a no-op; child contact (K) uses commercial partner's name and limit, ignoring the child's own limit.
- Part 3 (mutation check): PASS. With `'sale'` added to the state tuple at `sale_order.py:775`, the suite reported `1 failed, 0 error(s) of 14 tests`; only `test_branch_a_state_sale_returns_empty` failed, with actual `'Charact Partner has reached its credit limit of: $\xa01,000.00\nTotal amount due (including sales orders and this document): $\xa03,000.00'`. The total is 3,000 because a confirmed order counts twice (`credit_to_invoice` + `current_amount`). After the revert: `0 failed, 0 error(s) of 14 tests`; `git status` clean, core change never committed. All DONE WHEN criteria met.
- Workshop slides 25-28 alignment: manifest depends now `['sale', 'account']`; class docstring "A failing test means behavior CHANGED". Baseline review (slide 27) in `creative/author-characterization-tests-partner-credit-warning-baseline-review.md`: 10 correct, 1 bug-preserved (M, company-currency display; follow-up TASK-FUTURE-CREDIT-CURRENCY), 2 unclear (A confirmed state, F boundary), each tagged `# REVIEW:` in the test file. Slide 28 mutation re-run on the tagged suite: `1 failed ... of 14` (only test A), revert gives `0 failed, 0 error(s) of 14 tests`, `addons/` clean. Next: `/bmb:reflect`, then `/bmb:archive`.
- Reflection Agent: COMPLETE (2026-11-03) - Output: memory-bank/reflection/author-characterization-tests-partner-credit-warning-reflection.md. Task Quality: Excellent; Ecosystem Effectiveness: Moderately Effective.
