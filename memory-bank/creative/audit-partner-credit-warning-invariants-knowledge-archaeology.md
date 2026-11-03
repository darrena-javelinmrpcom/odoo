# Knowledge-Archaeology Audit — Partner Credit Warning

**Task**: `audit-partner-credit-warning-invariants` (Level 1, analysis only — no code changed)
**Date**: 2026-11-03
**Odoo**: 18.0 Community (`odoo/release.py:15`)
**Audience**: senior Odoo developer
**Subjects**:
- `sale.order._compute_partner_credit_warning`, `addons/sale/models/sale_order.py:770-781`
- `account.move._build_credit_warning_message`, `addons/account/models/account_move.py:1846-1891`

**Supporting code read** (the invariants live in these, not only in the two subjects):
`addons/account/models/partner.py` (`credit`, `credit_to_invoice`, `credit_limit`, `_commercial_fields`),
`addons/sale/models/res_partner.py:80-107` (sale's `_compute_credit_to_invoice`),
`addons/sale/models/sale_order.py:207-211, 446-454` (`currency_rate`),
`addons/sale/models/account_move.py:167-185` (`_get_partner_credit_warning_exclude_amount`),
`addons/account/models/account_move.py:1819-1839` (the sibling invoice-side caller),
`addons/sale/views/sale_order_views.xml:301-305`, `addons/account/views/account_move_views.xml:838-842`,
`odoo/fields.py:1856-1872` (`_String` cache conversion), `odoo/tools/translate.py:571-632` (`_()` resolution),
`addons/sale/tests/test_credit_limit.py`, and the in-repo consumer `custom_addons/sale_credit_limit_warning/`.

`memory-bank/agent-rules/_learned/` was **not** read, as instructed.

---

## 0. The code under audit

```python
# addons/sale/models/sale_order.py
770  @api.depends('company_id', 'partner_id', 'amount_total')
771  def _compute_partner_credit_warning(self):
772      for order in self:
773          order.with_company(order.company_id)
774          order.partner_credit_warning = ''
775          show_warning = order.state in ('draft', 'sent') and \
776                         order.company_id.account_use_credit_limit
777          if show_warning:
778              order.partner_credit_warning = self.env['account.move']._build_credit_warning_message(
779                  order.sudo(),  # ensure access to `credit` & `credit_limit` fields
780                  current_amount=(order.amount_total / order.currency_rate),
781              )
```

```python
# addons/account/models/account_move.py
1846 def _build_credit_warning_message(self, record, current_amount=0.0, exclude_current=False, exclude_amount=0.0):
1861     partner_id = record.partner_id.commercial_partner_id
1862     credit_to_invoice = partner_id.credit_to_invoice - exclude_amount
1863     total_credit = partner_id.credit + credit_to_invoice + current_amount
1864     if not partner_id.credit_limit or total_credit <= partner_id.credit_limit:
1865         return ''
1866     msg = _('%(partner_name)s has reached its credit limit of: %(credit_limit)s', ...,
1869             credit_limit=formatLang(self.env, partner_id.credit_limit, currency_obj=record.company_id.currency_id))
1871     total_credit_formatted = formatLang(self.env, total_credit, currency_obj=record.company_id.currency_id)
1872-1891  four-way branch on (credit_to_invoice > 0, current_amount > 0) → msg + '\n' + _(...)
```

### Data-flow summary

```
total_credit = credit(commercial partner, posted unreconciled receivables, env.company root tree, company ccy)
             + credit_to_invoice(commercial partner, SOs in state 'sale' of env.company, grouped by partner_invoice_id, converted @ today)
             − exclude_amount (always 0 from sale.order)
             + current_amount (this SO's amount_total, tax-incl., converted to company ccy @ date_order rate)
warn  ⇔  credit_limit ≠ 0  AND  total_credit > credit_limit        (credit_limit: company-dependent Float, company ccy)
```

---

## 1. Invariants

Confidence key: **HIGH** = proven by code paths and/or a test pins it. **MED** = follows from code reading but depends on runtime context (web client company selection, data shape). **LOW** = plausible, edge-case only.

### A. Access control / `sudo`

#### A1. The record passed to the helper must be `sudo()`'d, not the helper's `self`
- **Where**: `sale_order.py:779` (`order.sudo()`); field groups at `account/models/partner.py:517-527`.
- **Invariant**: `credit`, `credit_to_invoice`, `credit_limit` carry `groups='account.group_account_invoice,account.group_account_readonly'`. The helper reads them via `record.partner_id.commercial_partner_id`, so the privilege comes from **the `record` argument's env**, not from `self` (`self.env['account.move']` is deliberately *not* sudo'd).
- **What breaks if dropped**: a salesman without accounting rights gets an `AccessError` while the SO form loads (and during every onchange that recomputes `amount_total`). `test_credit_limit_access` (`sale/tests/test_credit_limit.py:344-366`) pins this. A refactor that writes `self.env['account.move'].sudo()._build...(order, ...)` *looks* equivalent but is not: the helper never reads partner fields through `self`.
- **Confidence**: HIGH

#### A2. `self.env` (non-sudo) must stay the formatting and translation env
- **Where**: `sale_order.py:778` (`self.env['account.move']`), `account_move.py:1866-1871` (`_()` and `formatLang(self.env, ...)`).
- **Invariant**: language for `_()` comes from the caller frame's `self.env.lang` (`translate.py:581-585`), and `formatLang` uses `self.env` for number/date locale. Today that is the real user's env. `sudo()` keeps the context in 18.0, so lang survives, but routing through an env built from the superuser uid (e.g. `api.Environment(cr, SUPERUSER_ID, {})`, or a cron/queue env without `lang`) falls through to `_get_uid` → superuser's language (`translate.py:596-605`, which comments on exactly this pitfall).
- **What breaks if dropped**: the banner renders in the admin's language and number format instead of the user's.
- **Confidence**: MED

#### A3. The `sudo` silently widens `credit_to_invoice` past record rules, and that is intended
- **Where**: `sale/models/res_partner.py:89-96` (`self.env['sale.order'].search(...)` runs in the sudo env inherited from the partner record).
- **Invariant**: the credit exposure is partner-wide, so it must include **all** salespeople's confirmed orders. Without sudo, a salesman restricted to "Own Documents Only" would see only their own SOs in that search.
- **What breaks if dropped**: if someone relaxes the field `groups` to avoid the sudo, `credit_to_invoice` undercounts for restricted users. The warning would then depend on who is looking, and nothing would error.
- **Confidence**: HIGH

#### A4. The sudo'd read is a deliberate, bounded information disclosure
- **Where**: `sale_order.py:779`; contrast `account_move_views.xml:838` (the invoice banner is `groups=`-gated) with `sale_order_views.xml:301-305` (the SO banner is **not** gated).
- **Invariant**: non-accounting users see the partner's credit limit and total exposure (formatted) on the SO, but never the raw fields. The string is the only channel.
- **What breaks if changed**: adding a `groups=` to the SO banner "for consistency with account" hides the warning from salesmen, who are its primary audience. Going the other way and exposing `credit`/`credit_limit` as related fields on `sale.order` leaks them through RPC.
- **Confidence**: HIGH

### B. Company context

#### B1. Effective company for all partner-side figures is `env.company`, not `order.company_id`
- **Where**: `sale_order.py:773` (discarded `with_company` return, see §2.1); `partner.py:373-381` (`@api.depends_context('company')`, `child_of env.company.root_id`); `sale/models/res_partner.py:85-90` (`company = self.env.company`); `partner.py:524-527` (`credit_limit` is `company_dependent`).
- **Invariant (as-built behaviour)**: `credit`, `credit_to_invoice`, and `credit_limit` are all evaluated in the user's **current** company, whatever the order's company. Only the feature gate (`order.company_id.account_use_credit_limit`, line 776) and the display currency (`record.company_id.currency_id`, line 1869) use the order's company.
- **What breaks if "preserved" naively**: nothing changes as long as users work in a single company. In multi-company setups (user active in B, opening an SO of A with both allowed), the banner mixes A's gate and currency with B's limit, receivables and SO backlog. A refactor that fixes this (rebinding `order = order.with_company(order.company_id)`, or `partner.with_company(company).sudo()` as `custom_addons/sale_credit_limit_warning/models/sale_order.py:45` does) **is a behaviour change**. It needs its own test and must not be passed off as a no-op cleanup. `test_credit_limit_multi_company` (`test_credit_limit.py:46-73`) pins the partner-side context semantics.
- **Confidence**: HIGH for the code fact. MED for user-visible impact, because it depends on which company the web client puts first in `allowed_company_ids` when opening a cross-company record.

#### B2. The feature gate is checked twice, in two different companies
- **Where**: `sale_order.py:776` (`order.company_id.account_use_credit_limit`) and `sale/models/res_partner.py:86-87` (`self.env.company.account_use_credit_limit`, early `return` → `credit_to_invoice = False`).
- **Invariant**: both flags must be on for the SO backlog to count. If the order's company has the flag on but the user's current company does not, the warning still appears but silently excludes all confirmed-not-invoiced SOs.
- **What breaks if dropped**: removing the caller-side gate (line 776) because "the partner compute already checks it" shows warnings in companies with the feature off, using `credit` alone (that compute has no gate). Removing the partner-side gate makes the expensive SO search run on every partner read.
- **Confidence**: HIGH

#### B3. The helper has no feature gate of its own; gating is the caller's job
- **Where**: `account_move.py:1846-1865`, versus the callers at `sale_order.py:775-777` and `account_move.py:1829-1832`.
- **Invariant**: `_build_credit_warning_message` returns a warning for any partner with `credit_limit ≠ 0` that is over the limit, whether or not `account_use_credit_limit` is set. It is a pure formatter, not a policy check.
- **What breaks if dropped**: a new caller (report, portal, POS, a custom module) that reuses the helper without re-implementing the state and company gate shows warnings in companies with the feature off, and on confirmed or cancelled documents.
- **Confidence**: HIGH

### C. State-machine gates

#### C1. `state in ('draft', 'sent')` excludes the order from its own backlog (no double-count)
- **Where**: `sale_order.py:775` and `sale/models/res_partner.py:95` (`('state', '=', 'sale')`).
- **Invariant**: `credit_to_invoice` only counts `state == 'sale'` orders, and `current_amount` is only added while the SO is draft or sent. The two sets are disjoint, so the SO is counted exactly once.
- **What breaks if dropped**: widening the gate to include `'sale'` (a common request: "keep showing the warning after confirmation") counts a confirmed SO twice, once in `credit_to_invoice` and once as `current_amount`. The banner overstates exposure by the order total. The invoice side solves the same problem with `exclude_amount` (`sale/models/account_move.py:167-185`). The SO side has no equivalent, and `exclude_amount` is always 0 here.
- **Confidence**: HIGH

#### C2. Cancelled or locked orders show no warning; the field is reset first
- **Where**: `sale_order.py:774` (unconditional `= ''` before the gate).
- **Invariant**: every record in `self` gets a value assigned. Non-stored computes **must** assign on every path or the ORM raises `ValueError: Compute method failed to assign`.
- **What breaks if dropped**: moving the reset into an `else:` branch and missing a path (e.g. an early `continue` for a missing partner) crashes the form on read.
- **Confidence**: HIGH

#### C3. Invoice-side sibling gate: `draft` + `out_invoice` only
- **Where**: `account_move.py:1829-1831`.
- **Invariant**: credit notes and vendor bills never warn. `current_amount` is always positive on invoices. A refactor that "unifies" the two callers into one gate must keep these conditions separate: SO uses `('draft', 'sent')`, invoice uses `== 'draft'` and `out_invoice`.
- **What breaks if dropped**: refunds (`out_refund`) would add their amount to exposure instead of reducing it, because `tax_totals` amounts are unsigned.
- **Confidence**: HIGH

### D. Field rollups (`commercial_partner_id`)

#### D1. All partner figures must be read on the commercial partner
- **Where**: `account_move.py:1861`; `sale/models/res_partner.py:83-84` (`commercial_partners = self.commercial_partner_id & self`, returns immediately for non-commercial partners), `:107` (`partner.commercial_partner_id.credit_to_invoice +=`); `partner.py:743` (`credit_limit` in `_commercial_fields`).
- **Invariant**: `credit_to_invoice` is **only** non-zero on commercial partners, by construction. `credit` is effectively commercial-only too: receivable lines carry the commercial partner. `credit_limit` is synced down from the commercial entity.
- **What breaks if dropped**: `record.partner_id.credit_to_invoice` on a contact (e.g. "John @ Company A") is always 0, so the SO backlog vanishes from the total. `test_commercial_partner_credit` (`test_credit_limit.py:368-404`) pins this.
- **Confidence**: HIGH

#### D2. The warning keys on `partner_id`, but the backlog keys on `partner_invoice_id`
- **Where**: `account_move.py:1861` (`record.partner_id.commercial_partner_id`) and `sale/models/res_partner.py:91-93, 97-98` (search and group by `partner_invoice_id`).
- **Invariant (implicit asymmetry)**: an SO's exposure is attributed to its **invoice address's** commercial entity once confirmed, but its draft warning is evaluated against the **customer's** commercial entity. When both share a commercial partner (the normal case) this is invisible.
- **What breaks if "fixed" on one side**: switching the helper to `record.partner_invoice_id`, which `sale.order` has and `account.move` does not, changes which limit is checked for every SO with a third-party invoice address. The helper is shared with `account.move`, so this would also need a hasattr or a polymorphic hook. Switching the backlog to `partner_id` changes historic exposure figures on partner forms.
- **Confidence**: MED (the code fact is certain; real impact only shows with cross-entity invoice addresses)

### E. Currency

#### E1. Every term of `total_credit` must be in company currency
- **Where**: `sale_order.py:780` (`amount_total / currency_rate`); `sale_order.py:446-454` (`currency_rate` = rate *from company ccy to order ccy*); `sale/models/res_partner.py:101-106` (`_convert` → `company.currency_id`); `partner.py:388` (`amount_residual`, company ccy); `account_move.py:1869, 1871` (`currency_obj=record.company_id.currency_id`).
- **Invariant**: division by `currency_rate` (not multiplication) converts order currency to company currency. The formatter labels everything with the company currency, and `credit_limit` is a plain `Float` (`partner.py:524`) that is implicitly in company currency.
- **What breaks if dropped**:
  - Passing `amount_total` raw: a 2:1 foreign-currency order counts double. `test_credit_limit_multicurrency` (`test_credit_limit.py:151-189`) pins `amount_total / currency_rate == 55` and the `$ 55.00` string.
  - Inverting to `* currency_rate`: wrong by rate².
  - Formatting with `record.currency_id` (the SO currency) to be "user-friendly": company-currency numbers get the foreign symbol.
- **Confidence**: HIGH

#### E2. The SO term and the backlog term use different rate dates
- **Where**: `sale_order.py:453` (rate at `date_order`) and `sale/models/res_partner.py:105` (`_convert` at `context_today`).
- **Invariant (as-built)**: a draft SO is valued at its order-date rate, then revalued at today's rate once confirmed. The total can jump at confirmation even though nothing else changed.
- **What breaks if "harmonised"**: replacing line 780 with `order.currency_id._convert(order.amount_total, company_ccy, company, today)` changes figures for back-dated or long-lived quotations, and adds currency rounding (next item). Not wrong, but a behaviour change that needs its own test.
- **Confidence**: MED

#### E3. `amount_total / currency_rate` is unrounded, and the threshold compare is raw float
- **Where**: `sale_order.py:780` (`currency_rate` has `digits=0`, `sale_order.py:207-211`) and `account_move.py:1864` (`<=` without `float_compare`).
- **Invariant**: the test fixtures use exact binary-representable rates (2.0). With real rates (e.g. 1.0837), the quotient carries noise in the 1e-12 range, so an order that should land *exactly* on the limit can land a hair over and trigger the warning.
- **What breaks if changed**: switching to `_convert` (rounded) or `float_compare(..., precision_rounding=company_ccy.rounding)` moves the boundary. That is arguably a fix, but it changes outcomes right at the limit.
- **Confidence**: MED

#### E4. `currency_rate` is assumed non-zero
- **Where**: `sale_order.py:780`.
- **Invariant**: `_get_conversion_rate` returns 1.0 for same-currency and falls back to 1.0 when no rate exists, so in core flows the divisor is never 0. `currency_rate` is `store=True, precompute=True`, so it is also populated in onchange for new records.
- **What breaks if dropped**: if a refactor makes `currency_rate` non-precomputed or lazily computed, or data is imported with `currency_rate = 0`, you get a `ZeroDivisionError` in a compute, which breaks the form for everyone. Core has no guard. The custom addon adds one (`custom_addons/.../models/sale_order.py:39`; test sets `currency_rate = 0.0` at `test_credit_limit_warning.py:227`).
- **Confidence**: MED (latent; not reachable in core flows without bad data)

#### E5. `current_amount` is tax-inclusive, but the backlog filter keys on untaxed
- **Where**: `sale_order.py:780` (`amount_total`); `sale/models/res_partner.py:94` (`untaxed_amount_to_invoice > 0` as the *filter*) and `:100` (`amount_to_invoice`, tax-incl., as the *sum*).
- **Invariant**: exposure is measured tax-inclusive (that is what the customer will owe). The untaxed filter only decides which orders are eligible. `test_credit_limit_access` relies on adding a tax to push the SO over the limit (`test_credit_limit.py:361-366`).
- **What breaks if dropped**: switching `current_amount` to `amount_untaxed` "because the filter is untaxed" makes the warning fire later than invoices, which use `tax_totals['total_amount']`, also tax-inclusive (`account_move.py:1833-1834`).
- **Confidence**: HIGH

### F. Boundary conditions

#### F1. `credit_limit == 0` means "no limit", not "zero tolerance"
- **Where**: `account_move.py:1864` (`not partner_id.credit_limit`).
- **Invariant**: a falsy limit disables the check. `use_partner_credit_limit` (`partner.py:528-531, 714-723`) is a UI-only toggle between the partner's value and the company fallback (`account_default_credit_limit`). The helper never reads the toggle.
- **What breaks if dropped**: changing it to `credit_limit is None` or `credit_limit < 0` makes every partner with the default 0 limit warn on every order.
- **Confidence**: HIGH

#### F2. Reaching the limit exactly is allowed; only exceeding warns
- **Where**: `account_move.py:1864` (`total_credit <= credit_limit` → no warning).
- **Invariant**: `test_warning_on_invoice_with_downpayment` and related tests create an SO "to reach (but not exceed)" the limit and expect no warning (`test_credit_limit.py:80, 121`).
- **What breaks if dropped**: flipping to `<` because the message says "has *reached*" breaks those tests and changes the trigger point by one unit.
- **Confidence**: HIGH

#### F3. Negative components are allowed and net off
- **Where**: `account_move.py:1862-1863`.
- **Invariant**: `credit` is negative when the customer has an unapplied credit balance. `credit_to_invoice - exclude_amount` can go negative on over-invoiced SOs. `current_amount` can be negative on an SO made entirely of discount or refund lines. All of these reduce exposure.
- **What breaks if dropped**: clamping terms with `max(0, ...)` to "sanitise" them ignores customer prepayments and credit notes, which produces false warnings. Note that the sale-side `exclude_amount` override *does* clamp its own input (`sale/models/account_move.py:177-179`), on purpose and only there.
- **Confidence**: MED

#### F4. Message-variant selection uses strict `> 0`, independently of the threshold
- **Where**: `account_move.py:1872, 1877, 1882`.
- **Invariant**: the suffix ("including sales orders", "this document", both, or neither) reflects which components are *positive*, not which are non-zero. On the SO path `current_amount > 0` is almost always true, so in practice the SO banner only ever shows the "this document" or "sales orders and this document" variants.
- **What breaks if dropped**: collapsing the branches into one templated string loses the four distinct msgids (see G2). Changing to `!= 0` yields "including sales orders" for a negative backlog.
- **Confidence**: HIGH (strings pinned at `test_credit_limit.py:130-131, 187-188, 264-265, 271-272, 332-333`)

### G. Translation idioms

#### G1. `_()` must be called lexically inside a method of an `odoo.addons.account` module
- **Where**: `account_move.py:1866, 1873, 1878, 1883, 1888`; `translate.py:501-535` (module is derived from the caller frame's `__name__` or file), `:571-585` (lang from frame locals: `context`, `kwargs['context']`, then `self.env`).
- **Invariant**: the msgids are exported to and translated in **`account`**'s `.po` files. The frame must have a local `self` with an `.env`.
- **What breaks if dropped**:
  - Moving the helper into `sale` (or a custom addon) re-homes the msgids. Existing `account` translations stop applying until the new module's `.pot` is exported and translated.
  - Turning it into a `@staticmethod` or module-level function removes `self` from the frame, so lang resolution falls back to `request.env` and then `uid` (`translate.py:589-605`). It works in HTTP requests but not in crons, tests, or shell.
  - Adding a local variable named `context` or `kwargs` inside the helper hijacks lang resolution (`translate.py:573-578`).
  - The safe modernisation is `self.env._(...)` in place, not relocation.
- **Confidence**: HIGH for module re-homing. MED for the staticmethod case (it partially works under HTTP).

#### G2. Two independently translated msgids, joined with `'\n'`
- **Where**: `account_move.py:1873, 1878, 1883, 1888` (`msg + '\n' + _(...)`).
- **Invariant**: translators see the headline and the four suffixes as five separate msgids. The `'\n'` is rendered as a line break because the field is `fields.Text` and the widget preserves newlines.
- **What breaks if dropped**: merging into a single msgid orphans every existing translation. Changing the field to `Html`, or rendering via `t-out` in a Markup context, collapses the newline. Changing `'\n'` to `<br/>` puts literal markup in a `Text` field.
- **Confidence**: HIGH (merge breaks translations). MED (rendering).

#### G3. Named placeholders with already-formatted values
- **Where**: `account_move.py:1867-1870, 1874-1875`.
- **Invariant**: `%(credit_limit)s` and `%(total_credit)s` receive **strings** from `formatLang` (with currency symbol, locale grouping, NBSP `\xa0`), not floats. The tests assert the `\xa0`.
- **What breaks if dropped**: passing raw floats loses currency formatting and locale separators. Switching to positional `%s` breaks translations that reorder placeholders.
- **Confidence**: HIGH

### H. Multi-record vs singleton contracts

#### H1. The helper is singleton-on-`record`, model-level on `self`
- **Where**: `account_move.py:1846, 1861, 1869`.
- **Invariant**: `record` must be a single record. `record.partner_id` on a multi-record set raises `ValueError: Expected singleton`. `self` is used only for `.env` and is in practice an **empty** `account.move` recordset (`self.env['account.move']`, `sale_order.py:778`). Despite the missing `@api.model`, it is an `@api.model`-style helper that takes a polymorphic `record` (anything with `partner_id` and `company_id`).
- **What breaks if dropped**: adding `self.ensure_one()` "for safety" crashes the sale caller, where `self` is empty. Batching callers by passing `orders` instead of `order` crashes. Narrowing `record` to `account.move` (type hints, `record._name` checks) breaks the sale caller.
- **Confidence**: HIGH

#### H2. The compute is batch-safe, but the helper is N-call
- **Where**: `sale_order.py:772-781`.
- **Invariant**: the compute is called on arbitrary recordsets (list views, `read` of many SOs) and must loop. Each iteration triggers `credit` and `credit_to_invoice` on one commercial partner. The ORM's prefetch on the sudo'd partner set amortises `credit` (one SQL over the prefetched partner ids, `partner.py:374-400`). `credit_to_invoice` runs one `sale.order` search per partner batch.
- **What breaks if dropped**: "optimising" by computing a per-partner aggregate outside the loop and **reusing it across orders of different companies** returns the wrong company's figures (see B1). That optimisation is only valid if keyed by `(commercial_partner, company)`.
- **Confidence**: MED

#### H3. Positional parameter order and the dead `exclude_current` keyword are public API
- **Where**: `account_move.py:1846` (`record, current_amount=0.0, exclude_current=False, exclude_amount=0.0`); the docstring (`:1851-1852`) marks `exclude_current` DEPRECATED. The body never reads it.
- **Invariant**: third-party modules may call the helper positionally (`(rec, amt, False, excl)`) or with `exclude_current=True`. It is silently ignored but must remain accepted.
- **What breaks if dropped**: removing the parameter raises `TypeError` in any OCA or custom caller that still passes it, and shifts positional `exclude_amount` into the wrong slot. Re-implementing it ("finally honour `exclude_current`") changes totals for callers that have passed it for years with no effect.
- **Confidence**: HIGH (signature contract). LOW (that callers exist outside this repo; none in-repo, by grep).

### I. `@api.depends` and ORM cache semantics

#### I1. `amount_total` in `@api.depends` is what drives the live onchange banner
- **Where**: `sale_order.py:770`.
- **Invariant**: in the form view, editing a line changes `amount_total`, which triggers this compute in the onchange round-trip, so the banner appears or disappears as you type. `test_credit_limit_access` (`test_credit_limit.py:353-366`) asserts this through `Form`.
- **What breaks if dropped**: removing `amount_total` (e.g. switching to `order_line.price_total` without `amount_total`) stops the live update. The banner then only refreshes on save or reload.
- **Confidence**: HIGH

#### I2. The dependency list is intentionally partial. Non-stored means "recomputed on read".
- **Where**: `sale_order.py:299-300` (no `store=True`) and `:770` (no `state`, `currency_rate`, `partner_id.commercial_partner_id`, `company_id.account_use_credit_limit`).
- **Invariant**: because the field is non-stored, `@api.depends` only governs in-transaction cache invalidation and onchange triggering, not persistence. Partner-side inputs (`credit`, `credit_to_invoice`) are themselves non-stored and context-dependent, so declaring them would not help anyway.
- **What breaks if changed**: making the field `store=True` (e.g. to filter or search SOs "over limit") turns the partial depends into a **correctness** bug. The stored value would never update when another invoice is posted or another SO confirmed, because those are cross-record dependencies the depends list cannot express. In-transaction staleness after `action_confirm()` (`state` not declared) is the only practical consequence today. It is masked in the UI by the reload after a button click.
- **Confidence**: HIGH (store=True hazard). LOW (the in-transaction staleness matters to tests only).

#### I3. `currency_rate` missing from depends: a pure currency change does not refresh the banner
- **Where**: `sale_order.py:770`.
- **Invariant (as-built)**: changing pricelist usually reprices lines and so changes `amount_total`, which hides the gap. Changing `date_order` alone, which moves `currency_rate`, does **not** retrigger the onchange.
- **What breaks if "fixed"**: adding `currency_rate` and `state` is safe and strictly better. It is listed so that a refactorer does not take the current list as deliberate.
- **Confidence**: MED

### J. Return-value contract and view coupling

#### J1. Must return `''`, never `False` or `None`
- **Where**: `account_move.py:1865`, `sale_order.py:774`; `fields.py:1856-1858` (`_String.convert_to_cache`: `False`/`None` → `None` → read as `False`); `sale_order_views.xml:303` and `account_move_views.xml:840` (`invisible="partner_credit_warning == ''"`).
- **Invariant**: the views test **string equality with `''`**, not falsiness. `''` survives the cache as `''`. `False` and `None` become `None` and read back as `False`, and `False == ''` is false in the view expression evaluator.
- **What breaks if dropped**: a refactor that does `return False` or `return None` (or `or False`) shows an **empty yellow alert box** on every non-over-limit SO and invoice. Tests asserting `== ''` (`test_credit_limit.py:121, 172`) also fail.
- **Confidence**: HIGH

#### J2. The field name, its parent `div`, and the English headline are pinned by an in-repo consumer
- **Where**: `custom_addons/sale_credit_limit_warning/views/sale_order_views.xml:10, 13` (`//field[@name='partner_credit_warning']/parent::div`); `custom_addons/sale_credit_limit_warning/tests/test_credit_limit_warning.py:273, 289` (asserts the core field exists in the arch and contains `'has reached its credit limit'`).
- **Invariant**: renaming the field, re-wrapping the alert (e.g. into an `<alert>` widget without a parent `div`), or rewording the en_US headline breaks the custom addon's view inheritance at install/upgrade (a missing xpath target is fatal) or its test.
- **What breaks if dropped**: a module upgrade failure in this fork, not just a cosmetic regression.
- **Confidence**: HIGH

---

## 2. Looks Like an Invariant But Isn't (calibration)

These are things a careful reader is likely to "preserve" or "fix" for the wrong reason.

1. **`order.with_company(order.company_id)` (`sale_order.py:773`, twin at `account_move.py:1827`)**: a discarded-return no-op. `with_company` returns a new recordset, the result is thrown away, and `order` and the later `order.sudo()` keep the original env. The line **guarantees nothing**. Removing it is behaviour-neutral. *Fixing* it (rebinding) is a real behaviour change (see B1). Do not cite this line as evidence that the code is company-scoped.
2. **The `# ensure access to credit & credit_limit fields` comment (`:779`) understates the sudo's reach**: it also bypasses record rules in the `credit_to_invoice` SO search (A3) and covers `credit_to_invoice`, not just the two fields named. The comment is not a complete description of the privilege boundary.
3. **`exclude_current` (`account_move.py:1846`)**: looks like a live flag. It is dead (never read). The *signature slot* is the invariant (H3); its *semantics* are not.
4. **`use_partner_credit_limit` and `show_credit_limit` (`partner.py:528-534`)**: look like gates the helper should respect. They are UI-only. The helper's only gate is `credit_limit` truthiness (F1), plus the caller's company flag.
5. **The `@api.depends` list (`:770`)**: looks like the authoritative input set. It is not, and it cannot be (I2). Adding `state` and `currency_rate` is safe. Taking the existing list as intentional is the mistake.
6. **`self` being an `account.move` recordset**: looks like the helper is invoice-specific or needs `ensure_one()`. `self` is only an env carrier. Converting to `@api.model` is safe. Calling it on `record` (e.g. `order._build...`) is **not** possible, because the method lives on `account.move`.
7. **`partner_name=partner_id.name` uses the sudo'd record**: looks like a leak. Partner names are readable by any internal user anyway. Not an access concern.
8. **`record.company_id.currency_id` read via sudo**: same. Company currency is globally readable. The sudo is incidental here.
9. **"Has reached" wording vs the `>` trigger (F2)**: the wording looks like a spec for `>=`. It is copy, and the tests pin `>`. Don't "align" the code to the message.
10. **Tax-inclusive `amount_total` vs the `untaxed_amount_to_invoice > 0` filter (E5)**: looks like an inconsistency to unify. The filter is eligibility, the sum is exposure. Both are intentional.
11. **`account_move.py`'s sibling compute uses `total_amount_currency` vs `total_amount` depending on currency (`:1833`)**: looks like the SO side should mirror it. The SO side does the conversion via `currency_rate` instead. Both produce company currency (E1). Don't port one idiom to the other without re-checking that the result is company currency.
12. **Branch-ordering of the four message variants (`:1872-1891`)**: looks order-sensitive. It isn't, because the conditions are mutually exclusive as written. What matters is the strict `> 0` and the five msgids (F4, G2), not the `if` order.

---

## 3. Latent defects surfaced (not fixed, per instructions)

For triage. Each is a behaviour change if addressed and needs its own task and test.

| # | Defect | Location | Severity |
|---|---|---|---|
| L1 | Discarded `with_company`: partner figures evaluated in `env.company`, not the order's company | `sale_order.py:773`, `account_move.py:1827` | MED (multi-company only) |
| L2 | Gate split across two companies (order flag vs env flag) silently drops the SO backlog | `sale_order.py:776` vs `sale/models/res_partner.py:86` | MED |
| L3 | Raw float compare + unrounded division at the limit boundary | `sale_order.py:780`, `account_move.py:1864` | LOW |
| L4 | No zero guard on `currency_rate` | `sale_order.py:780` | LOW (bad data only) |
| L5 | `currency_rate`/`state` absent from `@api.depends` (stale onchange and in-transaction staleness) | `sale_order.py:770` | LOW |
| L6 | `partner_id` vs `partner_invoice_id` asymmetry between warning and backlog | `account_move.py:1861` vs `sale/models/res_partner.py:91-98` | LOW–MED |

The in-repo `custom_addons/sale_credit_limit_warning` already addresses L1 (`with_company(company).sudo()` on the partner), L4 (rate guard), and L5 (depends includes `state`, `currency_rate`) for its own banner. It leaves the core field in place (J2).

---

## 4. Recommended `systemPatterns.md` ENFORCED Entries

Proposed for the **Compute fields (non-stored)** block in `memory-bank/systemPatterns.md`. That file is Core State, so add it via `chore/banyan-admin` → `banyan`. Not applied by this task.

```markdown
### ENFORCED — Partner credit / credit-limit warnings

- **ENFORCED: sudo the record, not the helper.** When calling `account.move._build_credit_warning_message`,
  pass `record.sudo()`; keep `self.env['account.move']` non-sudo so `_()`/`formatLang` use the user's lang.
  (`sale_order.py:778-779`; `test_credit_limit.py::test_credit_limit_access`)
- **ENFORCED: `with_company()` returns a new recordset — always rebind.** `rec.with_company(c)` on its own
  line is a no-op. Write `rec = rec.with_company(c)` or chain it into the read. Never cite a discarded
  `with_company` as evidence of company scoping. (`sale_order.py:773`, `account_move.py:1827`)
- **ENFORCED: read credit figures on `commercial_partner_id`.** `credit_to_invoice` is only ever non-zero on
  commercial partners. (`sale/models/res_partner.py:83-84,107`; `test_commercial_partner_credit`)
- **ENFORCED: all credit-total terms are in company currency.** Convert document amounts with
  `amount_total / currency_rate` (SO) or the company-currency `tax_totals` key (invoice); format with
  `company_id.currency_id`. Guard `currency_rate` against 0 in new code.
- **ENFORCED: no double-counting across the state gate.** A document contributing `current_amount` must not
  also be in `credit_to_invoice` (`state == 'sale'`) — widen the SO gate only together with an
  `exclude_amount` equivalent.
- **ENFORCED: callers own the feature gate.** `_build_credit_warning_message` has no
  `account_use_credit_limit` / state check; every caller must apply both.
- **ENFORCED: credit-warning Text fields return `''`, never `False`/`None`.** Views test
  `invisible="<field> == ''"`; a falsy non-string renders an empty alert. (`fields.py:1856-1858`)
- **ENFORCED: `credit_limit == 0` means disabled; only `total > limit` warns (reaching is allowed).**
- **ENFORCED: keep translatable strings in their owning module and inside a method with `self`.**
  Don't move `_()` calls across modules or into staticmethods; don't merge separately-translated msgids;
  prefer `self.env._()` for new code.
- **ENFORCED: don't remove or repurpose deprecated helper parameters** (e.g. `exclude_current`) — keep
  the positional slot and keyword accepted.
- **ENFORCED: never make a credit-warning compute `store=True`.** Its true inputs are cross-record
  (other invoices/SOs) and cannot be expressed in `@api.depends`.
- **ENFORCED: core field `sale.order.partner_credit_warning` and its parent `div` are an extension point**
  for `custom_addons/sale_credit_limit_warning` (xpath + test); don't rename/re-wrap without updating it.
```

Note for the reviewer: the existing `systemPatterns.md` text "Read company-dependent partner accounting fields with `partner.with_company(company).sudo()` … The company comes from the order" already states the *intended* rule. Core violates it (L1), so the ENFORCED `with_company` entry adds the "rebind" wording. Without that wording, someone could copy the core idiom and believe they had complied.
