---
slug: sale-credit-limit-warning
feature: sale-credit-limit-warning
status: PLANNING_COMPLETE
---

# sale-credit-limit-warning: Customer Credit Limit Warning

**Complexity**: Level 2 (inherited from sale-credit-limit-warning)
**Status**: PLANNING_COMPLETE
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

## Specification

**Feature Type**: End-User Feature
**Primary Persona**: salesman (`sales_team.group_sale_salesman`, UAT account `sales@example.com`) — creates and sends quotations and wants to know, before sending/confirming, whether this order pushes the customer near or over their credit limit. Secondary: admin (Sales Administrator).
**Creative Exploration Needed**: No — the five open decisions are resolvable by confirmation (see Scope Boundaries); no UX or algorithm exploration is required.

### Invocation Method
- **Location**: Sales Order / Quotation form (`sale.order`, form view `sale.view_order_form`, `addons/sale/views/sale_order_views.xml:251`). Banner sits between the `<header>` status bar and the `<sheet>` — exactly where core's `partner_credit_warning` banner renders (`:301-305`).
- **Element**: Bootstrap alert `div` (`alert alert-warning` for yellow, `alert alert-danger` for red, `role="alert"`) wrapping `<field name="credit_warning_message"/>`. Added by an inherited view in the new addon using `<xpath expr="//field[@name='partner_credit_warning']/parent::div" position="after">` (core's div has no id/name, so it is addressed via its child field).
- **Visibility**: conditional — shown only when `credit_warning_level` is `warning` (yellow) or `danger` (red). Two sibling divs, each `invisible="credit_warning_level != '<level>'"`; a hidden `<field name="credit_warning_level" invisible="1"/>` must be in the view so the `invisible=` expressions can evaluate (Odoo 18 requirement). The existing core div is hidden with `<attribute name="invisible">1</attribute>`; the `partner_credit_warning` field intentionally stays in the view (core test `test_credit_limit_access` reads it through `Form`).
- **Navigation**: Sales app → Quotations (`/odoo/action-sale.action_quotations_with_onboarding`) → open any quotation or click New → pick customer / add lines. No new menu or button.
- **Confidence**: HIGH — pattern copied from core banner and sibling alert divs (`sale_order_views.xml:301-321`); colour classes are standard Bootstrap alert classes already used across `addons/account/views/account_move_views.xml`.

### Success Criteria
- **User sees**: on a draft/sent quotation, a yellow banner (customer between 80% and 100% of limit after this order) or red banner (customer over limit after this order) at the top of the form with four lines: headline naming the customer and the credit limit, outstanding receivables, this order's amount, total after this order. No banner otherwise. Exactly one credit banner is ever visible (core's yellow banner is hidden).
- **Verifiable at**: Sale Order form at `http://localhost:8069` (salesman and admin personas); `sale.order.credit_warning_message` / `credit_warning_level` in an Odoo shell or Python test.
- **Data persisted**: none. `credit_warning_message` (Text) and `credit_warning_level` (Selection `warning`/`danger`) are computed, `store=False`; no DB columns, no new models, no ACL rows. Reads existing `res.partner.credit`, `credit_to_invoice`, `credit_limit` (`addons/account/models/partner.py:517-527`) and `sale.order.amount_total`, `currency_rate`.
- **Observable within**: immediate — banner recomputes in the form on change of customer or order lines (standard onchange), no save required.

### Acceptance Criteria

Notation: `total = credit + credit_to_invoice + amount_total / currency_rate` (company currency); `limit = commercial_partner.credit_limit`.

#### AC-ENTRY-1: Banner appears at the top of the quotation form and replaces core's banner
**Priority**: MUST
**Given** the addon is installed and a salesman opens a draft quotation whose customer is over limit
**When** the form renders
**Then** exactly one credit banner is visible, located between the status bar and the form sheet; it is a red `alert-danger` div containing the new message; core's yellow `partner_credit_warning` banner is not visible; the resolved form arch (`get_view`) contains both new divs and the hidden `credit_warning_level` field

#### AC-HAPPY-1: Yellow banner when total is above 80% and at most 100% of the limit
**Priority**: MUST
**Given** customer limit 1,000.00, outstanding (credit + credit_to_invoice) 700.00, draft quotation of 150.00 (total 850.00)
**When** the user views the quotation
**Then** `credit_warning_level == 'warning'`, an `alert-warning` banner is shown, and the message equals (amounts via `formatLang` in company currency):
`<Customer> is approaching its credit limit of $ 1,000.00.` / `Outstanding receivables (incl. confirmed orders to invoice): $ 700.00` / `This order: $ 150.00` / `Total after this order: $ 850.00`
**And** at exactly total == 1,000.00 the banner is still yellow (red requires strictly over limit)

#### AC-HAPPY-2: Red banner when total exceeds the limit
**Priority**: MUST
**Given** customer limit 1,000.00, outstanding 700.00, draft quotation of 400.00 (total 1,100.00)
**When** the user views the quotation
**Then** `credit_warning_level == 'danger'`, an `alert-danger` banner is shown, and the message headline reads `<Customer> exceeds its credit limit of $ 1,000.00.` followed by the same three figure lines (outstanding 700.00, this order 400.00, total 1,100.00)
**And** a customer already over limit with a 0.00 order still shows red (total = outstanding > limit)

#### AC-HAPPY-3: No banner when there is no limit, the feature is off, or the customer is well within limit
**Priority**: MUST
**Given** any of: (a) customer `credit_limit` is 0; (b) company `account_use_credit_limit` is False; (c) total <= 80% of limit (including exactly 80.00% — yellow requires strictly above); (d) order has no customer
**When** the quotation is viewed
**Then** `credit_warning_message` is an empty string, `credit_warning_level` is falsy, and neither new banner nor core banner is visible

#### AC-HAPPY-4: Banner is limited to quotations (draft/sent)
**Priority**: MUST
**Given** an order that would otherwise be red (total > limit)
**When** the order state is `sale` (confirmed), `done` or `cancel`
**Then** no banner is shown (a confirmed order's amount is already inside `credit_to_invoice`, so adding it again would double-count); in `draft` and `sent` the red banner is shown

#### AC-HAPPY-5: Message reflects real receivables and confirmed-uninvoiced orders (stub detection)
**Priority**: MUST
**Given** a customer with limit 1,000.00, a posted unpaid invoice of 300.00 (`credit`), a confirmed uninvoiced order of 400.00 (`credit_to_invoice`) and a new draft quotation of 200.00
**When** the quotation is evaluated, then the invoice is paid (partner caches invalidated), then the quotation amount is changed to 500.00
**Then** the first message shows outstanding 700.00 / this order 200.00 / total 900.00 (yellow); after payment outstanding is 400.00 / total 600.00 (no banner); after the amount change total is 900.00 again (yellow) with this order 500.00. The message must change whenever any of the three inputs changes — not a fixed string

#### AC-HAPPY-6: Order amount is converted to company currency
**Priority**: MUST
**Given** company currency USD, a pricelist in a currency with rate 2.0, customer limit 50.00, no other receivables
**When** the quotation total is 45.00 in order currency (22.50 in company currency), then raised to 110.00 (55.00 in company currency)
**Then** at 22.50 there is no banner (45% of limit); at 110.00 the banner is red and `This order:` / `Total after this order:` show 55.00 (converted via `amount_total / currency_rate`, not 110.00), the limit is shown as 50.00 in company currency (mirrors `addons/sale/tests/test_credit_limit.py::test_credit_limit_multicurrency`)

#### AC-HAPPY-7: Banner updates live while editing the quotation
**Priority**: SHOULD
**Given** a draft quotation open in the form with a customer limit of 1,000.00 and outstanding 700.00
**When** the user adds a line taking the order from 100.00 to 400.00, then changes the customer to one with no limit
**Then** the banner moves none → yellow/red → none without saving the record (compute depends on `partner_id`, `company_id`, `state`, `amount_total`, `currency_rate`)

#### AC-ERROR-1: Salesman without accounting rights gets the banner instead of an access error
**Priority**: MUST
**Given** an internal salesman who is in neither `account.group_account_invoice` nor `account.group_account_readonly`, and a customer over limit
**When** the salesman opens or edits the quotation (Python: `Form(order.with_user(salesman))`)
**Then** no `AccessError` is raised and the red banner with correct figures is shown (partner fields are read with `sudo()`; mirrors core `test_credit_limit_access`)

#### AC-ERROR-2: Computation degrades silently on incomplete orders
**Priority**: MUST
**Given** a new unsaved quotation with no customer, or an order with `currency_rate == 0`, or an order with no lines
**When** the form renders or the compute runs
**Then** no exception or traceback; `credit_warning_message` is `''` (no division by zero, no `False`/`None` rendered as text)

#### AC-ERROR-3: Installing the addon does not regress core credit-limit behaviour
**Priority**: MUST
**Given** the addon is installed alongside `sale`
**When** `addons/sale/tests/test_credit_limit.py` (class `TestSaleOrderCreditLimit`) is run
**Then** all of its tests still pass unchanged (core `partner_credit_warning` values and its invoice warnings are untouched; the field stays in the form view)

#### AC-ERROR-4: Multi-company — limit and receivables are read in the order's company
**Priority**: SHOULD
**Given** a customer with different `credit_limit` per company (company-dependent) and a user whose current company differs from the order's company
**When** the order's warning is computed
**Then** limit, `credit` and `credit_to_invoice` are read with `with_company(order.company_id)` (core discards that call's result at `sale_order.py:773`, so its context is the user's company); message uses the order company's limit and currency

#### AC-ASYNC-1: Not applicable
**Priority**: COULD
**Given** the computation is synchronous and non-stored
**When** the order or customer data changes
**Then** the banner reflects it on the next recompute/refresh; there is no background job, notification or pending state

### Scope Boundaries
- **In scope**:
  - New custom addon `sale_credit_limit_warning` (depends: `sale`) extending `sale.order` with `credit_warning_message` (Text, compute, `store=False`) and a supporting `credit_warning_level` (Selection `warning`/`danger`, compute, `store=False`) filled by one shared compute method.
  - Inherited form view: two alert divs after core's banner div, core div hidden, hidden level field.
  - Python tests in the addon (`tests/test_credit_limit_warning.py`, `@tagged('post_install', '-at_install')`, base `odoo.addons.sale.tests.common.TestSaleCommon`) covering every MUST/SHOULD AC.
  - Infra to make the first custom addon loadable (see Decision 4).
  - Translatable message strings via `self.env._()`; amounts via `odoo.tools.misc.formatLang`.
- **Out of scope**: blocking confirmation / hard credit stop; approval workflow; editing credit limits or the company `account_use_credit_limit` / default-limit settings (existing Accounting settings); invoice-form warning (core already does it); quotation list indicators, portal view, PDF/email; per-order override of the warning; configurable thresholds (80% is a constant — may become a company setting later); changes to core `sale` / `account`; stored/searchable warning fields; JS/OWL components; the `warehouse`/`portal` personas.
- **Dependencies**: `sale` (and transitively `account`, `account_payment`); company setting `account_use_credit_limit` (Settings → Accounting → Customer Payments → Sales Credit Limit); `res.partner` accounting fields; running Odoo stack from `docker compose watch`.
- **NFR implications**: Security — the message exposes credit limit and receivables to salespeople lacking accounting groups; this matches core behaviour (core test asserts it) and is accepted, nothing is stored. i18n — strings wrapped for translation. Observability/12-factor — no config or logging needed; the 80% threshold is a code constant (flagged as hard-coded value; acceptable for a business rule, confirm). Performance — one `credit` SQL query + one `credit_to_invoice` search per order per recompute, same cost class as core; compute guarded to draft/sent and to setting on so confirmed orders never query.

**Decisions for human confirmation** (recommendation | confidence):

1. **Formula** — Use core's `credit + credit_to_invoice + amount_total/currency_rate`, not the slide's `credit + amount_total`. | **HIGH**. The slide formula ignores confirmed-but-not-yet-invoiced orders (`credit_to_invoice`), the main source of exposure for a Sales user, and would disagree with core's own banner for the same customer (customer could show red in core and nothing in ours). The slide's wording ("current outstanding receivables") is still honoured because the message labels the figure "Outstanding receivables (incl. confirmed orders to invoice)". Use `partner.commercial_partner_id` as core does. Caveat: `credit_to_invoice` is only populated when the company setting is on (`addons/sale/models/res_partner.py:86`), reinforcing Decision 3.
2. **Coexistence with core banner** — Hide core's div with `invisible="1"` in our inherited view; keep `partner_credit_warning` in the view (do not `replace` the div). | **MEDIUM-HIGH**. Hiding avoids two stacked banners; keeping the field in the arch keeps core's `test_credit_limit_access` (`order_form.partner_credit_warning`) working when the addon is installed (replace would remove the field from the view and break `Form` access). Cost: core still computes its field on form load (negligible). Alternative (leave both) rejected: red case would duplicate the same warning. Our red state is a strict superset of core's trigger (`total > limit`), so no information is lost.
3. **Gating** — Gate on `company.account_use_credit_limit` **and** `state in ('draft', 'sent')`, like core. | **HIGH** for state (confirmed orders are already inside `credit_to_invoice`; adding `amount_total` again double-counts), **MEDIUM-HIGH** for the setting (it is the company master switch; `credit_to_invoice` is not computed when it is off, `credit_limit` fields are hidden in the partner form when off, and the workshop spec's "empty when no limit set" is still satisfied). Alternative: ignore the setting and key only on `credit_limit > 0` — rejected as inconsistent with the Accounting settings UI.
4. **Addon name / location** — `custom_addons/sale_credit_limit_warning/` at repo root, as recommended in `memory-bank/systemPatterns.md` § "New custom module shape" (also closes the productBrief open question on where custom addons live). Requires two infra edits: add `/opt/odoo/custom_addons` to `addons_path` in `docker/odoo.conf` (bind-mounted read-only, restart needed), and a `develop.watch` `sync+restart` entry for `./custom_addons` → `/opt/odoo/custom_addons` in `docker-compose.yml` (Dockerfile `COPY . .` already bakes it into the image; no `.dockerignore` exists). Then Apps → Update Apps List and install in `odoo-dev`. Module layout: `__init__.py`, `__manifest__.py` (`depends: ['sale']`, `license: 'LGPL-3'`, data: `views/sale_order_views.xml`), `models/{__init__,sale_order}.py`, `views/sale_order_views.xml`, `tests/{__init__,test_credit_limit_warning}.py`. | **MEDIUM**. Alternative: `addons/sale_credit_limit_warning/` needs no infra change and is picked up by the existing watch, but mixes custom code into the 621-module upstream tree, against the "customisations in separate custom addons" principle. Human to pick; if `addons/` is chosen the infra edits drop out of scope.
5. **Message text** — Plain Text, four lines, company currency via `formatLang`, translatable. | **MEDIUM** (wording is a product choice; structure is HIGH).
   - Yellow (`warning`): `{partner} is approaching its credit limit of {limit}.` / `Outstanding receivables (incl. confirmed orders to invoice): {outstanding}` / `This order: {order_amount}` / `Total after this order: {total}`
   - Red (`danger`): `{partner} exceeds its credit limit of {limit}.` + same three lines
   - `{partner}` = `commercial_partner_id.name`; `{outstanding}` = `credit + credit_to_invoice`; `{order_amount}` = `amount_total / currency_rate`; `{total}` = sum; all as `formatLang(self.env, x, currency_obj=company.currency_id)`.
   - Thresholds: level `danger` if `total > limit`; `warning` if `total > 0.8 * limit`; else none. Empty message when `limit <= 0`. Percentage is deliberately not shown (avoids rounding edge cases at 80%/100%).

**Other implementation notes for the plan** (non-binding): compute with `@api.depends('partner_id', 'company_id', 'state', 'amount_total', 'currency_rate')` + `@api.depends_context('company')`; read partner as `order.partner_id.commercial_partner_id.with_company(order.company_id).sudo()`; keep the message and level in one `_compute_credit_warning` that sets both fields so they cannot disagree. Tests run in `odoo-test` DB per `techContext.md` (`--test-tags /sale_credit_limit_warning`, `--http-port=8070`); Chrome is absent in the container, so banner visibility/colour is covered by arch assertions + a `/bmb:uat` salesman walk, not a tour.

### Creative Exploration Needed
Specification is concrete — proceed to implementation planning. The only items needing the human are the five confirmable decisions above (lowest confidence: Decision 4 addon location, MEDIUM; Decision 5 wording, MEDIUM).

**Human review (2026-10-31)**: Specification APPROVED as written. All five decisions accepted: (1) core formula `credit + credit_to_invoice + amount_total/currency_rate`; (2) hide core banner, keep its field in the arch; (3) gate on `account_use_credit_limit` + `state in ('draft','sent')`; (4) addon at `custom_addons/sale_credit_limit_warning/` with the two infra edits; (5) message text as drafted. Taxonomy lint: CLEAN.

## Test Strategy

### Approach
- **Emphasis**: integration (ORM `TransactionCase` against a real DB, rolled back per test) — matches systemPatterns § Testing Patterns (i). No tours/Hoot: Chrome is absent from the image; UI colour/visibility covered by `get_view` arch assertions + `/bmb:uat`.
- **Target test count**: 14 (multi-component feature: model compute + view inheritance + regression guard).
- **Base class**: `odoo.addons.sale.tests.common.TestSaleCommon` (same as core `addons/sale/tests/test_credit_limit.py`), `@tagged('post_install', '-at_install')`. Fixtures in `setUpClass`: enable `company.account_use_credit_limit`, set `partner_a.credit_limit = 1000`, a salesman user without accounting groups (as core `test_credit_limit_access`).
- **Run command** (throwaway DB, main server keeps 8069):
  `docker compose exec odoo python odoo-bin -c /etc/odoo/odoo.conf -d odoo-test -i sale_credit_limit_warning --test-enable --test-tags /sale_credit_limit_warning --stop-after-init --http-port=8070 --log-level=test`
  Regression: same with `--test-tags /sale:TestSaleOrderCreditLimit` and `-i sale_credit_limit_warning` (AC-ERROR-3). Tee output to `.claude-logs/`.

### File Organization
- **New test files**: `custom_addons/sale_credit_limit_warning/tests/test_credit_limit_warning.py` (`TestCreditLimitWarning` — all compute + view ACs); `custom_addons/sale_credit_limit_warning/tests/__init__.py`.
- **Extend existing**: none — core `addons/sale/tests/test_credit_limit.py` is run unchanged as the regression guard (never modify core).

### What NOT to Test
- Bootstrap colour rendering / pixel position — framework CSS; covered by arch assertion (class names) + UAT.
- `res.partner.credit` / `credit_to_invoice` computation itself — core `account`/`sale` responsibility, already tested upstream.
- Translations (`.po`) — no `i18n/` shipped in this task.
- Core `partner_credit_warning` value — asserted by core's own tests (AC-ERROR-3 runs them).
- AC-ASYNC-1 — explicitly not applicable (synchronous, non-stored).

### Per-Phase Test Guidance
- **Phase 1 (11 tests)** — compute logic on `sale.order`:
  1. yellow at 850/1000 with exact four-line message (AC-HAPPY-1); 2. boundary: total == 1000 is yellow, total == 800 is empty (AC-HAPPY-1/3c); 3. red at 1100 with headline text (AC-HAPPY-2); 4. red with 0.00 order when outstanding already > limit (AC-HAPPY-2); 5. empty when `credit_limit` 0 / setting off / no partner (AC-HAPPY-3a,b,d); 6. empty for `sale`/`cancel` states, red for `sent` (AC-HAPPY-4); 7. stub detection — posted invoice 300 + confirmed uninvoiced order 400 + quote 200, then pay invoice, then change quote amount; message changes each time (AC-HAPPY-5); 8. multicurrency rate 2.0 (mirror `test_credit_limit_multicurrency`) (AC-HAPPY-6); 9. `Form` onchange: add line / change partner updates level without save (AC-HAPPY-7); 10. salesman without accounting groups — `Form(order.with_user(salesman))` no AccessError, red shown (AC-ERROR-1); 11. no exception + `''` for new record without partner, `currency_rate == 0`, no lines (AC-ERROR-2). (AC-ERROR-4 multi-company covered inside test 10's fixture via `with_company` read where feasible; otherwise a 12th test if setup is cheap.)
- **Phase 2 (3 tests)** — view + regression:
  12. `get_view(view_type='form')` arch contains the `alert-warning` and `alert-danger` divs with `credit_warning_message`, the hidden `credit_warning_level` field, and core's banner div has `invisible="1"` (AC-ENTRY-1); 13. `partner_credit_warning` still present in arch and readable via `Form` (AC-ENTRY-1 / AC-ERROR-3 guard); 14. core suite `TestSaleOrderCreditLimit` green with addon installed (AC-ERROR-3, run as separate command — counted as a verification step).

## Implementation Roadmap

### New Source Files (pin path + extension)
- [ ] `custom_addons/sale_credit_limit_warning/__init__.py` — imports `models`
- [ ] `custom_addons/sale_credit_limit_warning/__manifest__.py` — `name`, `version: '18.0.1.0.0'`, `depends: ['sale']`, `data: ['views/sale_order_views.xml']`, `license: 'LGPL-3'`, `installable: True`, `auto_install: False` (no security CSV: no new models)
- [ ] `custom_addons/sale_credit_limit_warning/models/__init__.py` — imports `sale_order`
- [ ] `custom_addons/sale_credit_limit_warning/models/sale_order.py` — `_inherit = 'sale.order'`; fields `credit_warning_message` (Text, compute, store=False), `credit_warning_level` (Selection `[('warning','Warning'),('danger','Danger')]`, compute, store=False); single `_compute_credit_warning` with `@api.depends('partner_id', 'company_id', 'state', 'amount_total', 'currency_rate')` + `@api.depends_context('company')`; module constant `CREDIT_WARNING_THRESHOLD = 0.8`
- [ ] `custom_addons/sale_credit_limit_warning/views/sale_order_views.xml` — `ir.ui.view` id `view_order_form_credit_limit_warning`, `inherit_id="sale.view_order_form"`; xpath on core banner div → `invisible="1"`; two alert divs + hidden level field after it
- [ ] `custom_addons/sale_credit_limit_warning/tests/__init__.py` — imports `test_credit_limit_warning`
- [ ] `custom_addons/sale_credit_limit_warning/tests/test_credit_limit_warning.py` — `TestCreditLimitWarning(TestSaleCommon)`
- [ ] extend `docker/odoo.conf` — `addons_path = /opt/odoo/addons,/opt/odoo/odoo/addons,/opt/odoo/custom_addons`
- [ ] extend `docker-compose.yml` — `develop.watch` entry `action: sync+restart`, `path: ./custom_addons`, `target: /opt/odoo/custom_addons`

### Subtasks
- [ ] Infra: odoo.conf `addons_path` + compose watch entry; restart with rebuild so `custom_addons/` exists in the container (image is `COPY . .`; watch only syncs on change) — `docker compose up --watch --build` (stop the running watch first)
- [ ] Addon skeleton (manifest, inits) — confirm module appears after Apps → Update Apps List
- [ ] Model: compute both fields from `order.partner_id.commercial_partner_id.with_company(order.company_id).sudo()`; guard state/setting/partner/limit/`currency_rate`; message via `self.env._()` + `formatLang(..., currency_obj=company.currency_id)`
- [ ] View inheritance (Phase 2)
- [ ] Install in `odoo-dev` (`-i sale_credit_limit_warning --stop-after-init --no-http`, then restart) and enable Settings → Accounting → Sales Credit Limit for manual check / UAT
- [ ] Update memory bank (systemPatterns: first custom addon + `custom_addons/` live; techContext: addons_path + watch entry) — Documentation agent

### Dependencies
- Phase 2 depends on Phase 1 fields existing (view references them).
- Infra change requires stopping the background `docker compose up --watch` and restarting with `--build`; `odoo.conf` is mounted read-only so the new `addons_path` needs a container restart.
- External: none. Git: origin `DaKaZ/odoo` is not pushable — commits stay local (push/PR skipped; see roadmap session notes).

### Observability Requirements
- **Applies**: No — no HTTP handlers, workers, or external calls; pure ORM compute rendered in an existing view. Observability standards (OTel/structured logging) are not applicable to Odoo addon compute fields; Odoo's own `_logger` is not needed (no error paths to log — AC-ERROR-2 degrades to `''`).

### API Requirements
- **REST API**: No. **GraphQL API**: No. (Fields become readable over existing JSON-RPC automatically; no contract change.)

### Phases
- [ ] Phase 1: Infra + addon skeleton + compute fields (`credit_warning_message`, `credit_warning_level`) with 11 TDD tests — ACs HAPPY-1..7, ERROR-1, ERROR-2, ERROR-4
- [ ] Phase 2: Inherited form view (two colour-coded banners, core banner hidden), install in `odoo-dev`, view tests + core regression run, memory-bank docs — ACs ENTRY-1, ERROR-3; final phase delivers the full entry-to-success flow (open quotation → see yellow/red banner)

## Creative Phases

- None required (Level 2, spec all HIGH/MEDIUM-HIGH confidence, human approved; MEDIUM items — addon location, wording — resolved by human decision).

---

## Execution State

**Build Status**: IDLE
**Current Phase**: BUILD
**Last Completed**: PLAN (2026-10-31)
**Can Resume**: NO

### Active Sub-Agents
(none)

### Completed Steps
- Step 0.1: Task auto-provisioned from feature sale-credit-limit-warning
- Step 3: Spec Writer Agent (sonnet) - COMPLETE; taxonomy lint CLEAN; human APPROVED
- Steps 4-6: Codebase analysis, implementation plan (2 phases, 14 tests) - COMPLETE

### Session Notes
- Feature branch was cut from local `chore/banyan-admin` (local `banyan` + roadmap commit), not `origin/banyan`: origin (`DaKaZ/odoo`) has no memory bank and is not pushable by this user. Push/PR steps are skipped until a writable remote exists.
