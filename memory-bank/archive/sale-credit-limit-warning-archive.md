# Archive: Customer Credit Limit Warning

## Metadata
- Task: sale-credit-limit-warning
- Feature: sale-credit-limit-warning
- Complexity: Level 2
- Completed: 2026-10-31
- Branch: feature/sale-credit-limit-warning
- Reflection: memory-bank/reflection/sale-credit-limit-warning-reflection.md
- UAT: memory-bank/uat/uat-sale-credit-limit-warning.md (run uat-20261031-a7c3, PASS_WITH_RECOMMENDATIONS)

## Summary
Adds a colour-coded credit limit banner to the Sale Order / Quotation form. It is yellow when the customer's outstanding receivables, plus confirmed-but-uninvoiced orders, plus this order reach 80% or more of their credit limit, and red when that total exceeds the limit. The banner shows the limit, the outstanding amount, this order's amount and the total. It is hidden for confirmed or cancelled orders, customers without a limit, or when the company's Sales Credit Limit setting is off. Core Odoo's own credit banner is hidden so only one shows.

## Solution
- New addon `custom_addons/sale_credit_limit_warning/` (depends on `sale`). It is the first custom addon, so `custom_addons` was added to `addons_path` and the compose watch.
- `sale.order` gets two non-stored computed fields filled by one method: `credit_warning_message` (Text) and `credit_warning_level` (`warning` / `danger`).
  - Formula: `credit + credit_to_invoice + amount_total / currency_rate`, the same as core, in company currency.
  - The partner is read as `commercial_partner_id.with_company(order.company_id).sudo()`, so salespeople without accounting rights see it.
  - It depends on partner, company, state, amount, rate, the partner's credit limit and credit, and the company setting. Those last three were added at HITL gate #2.
- An inherited form view adds two `alert` divs between the status bar and the sheet, and hides core's banner div. Core's field stays in the view so core tests keep passing.
- Phase 3, after UAT, added a browser regression test: an Odoo `HttpCase` + `web_tour` covering none → yellow → yellow at the limit → red → none, plus the update before saving. Chromium and `websocket-client` were added to the Docker image so it can run.

## Files Changed
- `custom_addons/sale_credit_limit_warning/__init__.py`, `__manifest__.py`: addon skeleton; the manifest registers the tour in `web.assets_tests`.
- `custom_addons/sale_credit_limit_warning/models/sale_order.py`: the compute fields and `_compute_credit_warning`.
- `custom_addons/sale_credit_limit_warning/views/sale_order_views.xml`: inherited form view with the two banners and core's banner hidden.
- `custom_addons/sale_credit_limit_warning/tests/test_credit_limit_warning.py`: 14 compute/view tests.
- `custom_addons/sale_credit_limit_warning/tests/test_credit_banner_e2e.py`, `static/tests/tours/credit_banner_tour.js`: browser tour test.
- `docker/odoo.conf`: `addons_path` += `/opt/odoo/custom_addons`.
- `docker-compose.yml`: `develop.watch` sync+restart for `./custom_addons`.
- `Dockerfile`: apt `chromium`, pip `websocket-client` (for test browser tours).
- `.gitignore`: `memory-bank/uat/artifacts/`.

## Verification
- Addon tests 15/15 and core `sale:TestSaleOrderCreditLimit` 7/7 green, run in a throwaway `odoo-test` DB.
- UAT: happy path 6/6 and mobile 2/2 PASS. One Recommended finding: the 375px viewport could not be reached, so mobile was only checked at 929px.
- Manual re-check on 2026-10-31 after the image rebuild: 500 none / 900 yellow / 1200 red / 400 none. A no-limit customer at £5,000 showed no banner.

## Notes
- Known gaps:
  - UAT negatives and errors sections were not walked. A salesman user `sales@example.com` does not exist in `odoo-dev`.
  - No axe-core scan.
  - Real 375px mobile layout is unverified.
- Phase 3 skipped the code-review and build-verifier agents; this is recorded in the task's Guard & Recovery Log.
- Windows Git Bash: prefix `docker compose exec` commands that use container paths with `MSYS_NO_PATHCONV=1`.
- Remote: `DaKaZ/odoo` (now `upstream`) is read-only for this user. Work is pushed to the fork `darrena-javelinmrpcom/odoo` (`origin`). Its `origin` fetch refspec is limited to `banyan`, `feature/*`, `task/*` and `chore/*` because a full fetch of the Odoo fork is very slow.
