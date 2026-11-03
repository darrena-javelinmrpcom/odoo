# Archive: Characterization tests for sale.order._compute_partner_credit_warning

## Metadata
- Task: author-characterization-tests-partner-credit-warning
- Complexity: Level 1
- Completed: 2026-11-03
- Branch: task/author-characterization-tests-partner-credit-warning → PR to `banyan`
- Reflection: memory-bank/reflection/author-characterization-tests-partner-credit-warning-reflection.md
- Baseline review: memory-bank/creative/author-characterization-tests-partner-credit-warning-baseline-review.md

## Summary
Locked the current behavior of `sale.order._compute_partner_credit_warning`
(`addons/sale/models/sale_order.py:771`) and its callee
`account.move._build_credit_warning_message` (`addons/account/models/account_move.py:1846`)
with byte-for-byte characterization tests in a new test-only addon. This was a safety net
before any change to that method. It follows workshop slides 25-28 (harness, prompt, baseline
review, prove it works).

## Solution
- **Part 1, harness**: addon `custom_addons/banyan_sale_safety`. Tests are tagged
  `post_install`, `-at_install`, `characterization`. The language is locked with
  `cls.env = cls.env(context=dict(cls.env.context, lang='en_US'))`, because context is an
  immutable frozendict, so the slide's `self.env.context = {...}` was corrected.
- **Part 2, characterization**: 13 branch tests (A-M) plus a language smoke test, 14 in total.
  Each asserts the full string with `assertEqual`. The literals were captured from the real
  failure diffs, with NBSP and newline written as `\xa0` / `\n` escapes.
- **Part 3, baseline review**: 10 correct, 1 bug-preserved (M: the warning always shows the
  company currency), 2 unclear (A: confirmed orders get no warning; F: `<=` at the boundary
  versus the "reached" wording). Each test carries a `# REVIEW:` tag.
- **Part 4, mutation check**: adding `'sale'` to the state tuple at `sale_order.py:775` failed
  exactly test A (twice). After the revert all tests passed and `addons/` was clean; the
  mutation was never committed. It also showed that a confirmed order would be counted twice
  (`credit_to_invoice` + `current_amount`, $3,000 against $1,500).

## Verification
`docker compose exec odoo python odoo-bin -c /etc/odoo/odoo.conf -d odoo-test -u banyan_sale_safety --test-tags characterization/banyan_sale_safety --stop-after-init --http-port=8070 --log-level=test`
→ `0 failed, 0 error(s) of 14 tests` (repeated runs, deterministic).

## Files Changed
- `custom_addons/banyan_sale_safety/__init__.py`: empty
- `custom_addons/banyan_sale_safety/__manifest__.py`: test-only addon, depends `sale`, `account`
- `custom_addons/banyan_sale_safety/tests/__init__.py`: test import
- `custom_addons/banyan_sale_safety/tests/test_partner_credit_warning_characterization.py`: 14 tests
- `memory-bank/creative/author-characterization-tests-partner-credit-warning-baseline-review.md`
- `memory-bank/agent-rules/_learned/odoo-testing.md`: new learned rule

## Notes
- **Open follow-up**: TASK-FUTURE-CREDIT-CURRENCY (show the warning in the order currency),
  not yet filed. When it lands, test M's literal must change.
- **PM decisions pending**: A (should confirmed orders warn? fixing it needs `exclude_amount`)
  and F (should a total exactly at the limit warn, or should the wording say "exceeded"?).
- **Gotchas**: a wrong `--test-tags` value, or running without `-i`/`-u`, silently runs 0 tests.
  Git Bash needs `MSYS_NO_PATHCONV=1`. The container code is not bind-mounted.
- **Process gap**: `CLAUDE.md` calls reflection optional at Level 1, but the `/bmb:archive`
  phase gate requires it.
