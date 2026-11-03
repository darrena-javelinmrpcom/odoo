---
name: Odoo Computed Fields (learned)
globs: ["custom_addons/**/*.py"]
paths: ["custom_addons/"]
topics: ["odoo", "orm", "compute-fields", "testing"]
priority: low
auto_generated: true
derived_from: [sale-credit-limit-warning, audit-partner-credit-warning-invariants]
evidence_count: 2
last_validated: 2026-11-03
---

# Odoo Computed Fields

- List every input field in `@api.depends` for non-stored computes, including fields read through `sudo()`, company-dependent fields (e.g. `partner_id.commercial_partner_id.credit_limit`) and company settings (e.g. `company_id.account_use_credit_limit`). A missing dependency leaves the value stale in the form until reload.
- Test each compute by changing one input and re-reading the field (staleness test), not only by setting values before the first read.
- Don't assume a non-stored compute is recomputed on every read. Odoo 18 caches it for the transaction until a declared dependency changes (`fields.py` compute-on-miss). Its cache is keyed by company/user only if the field declares `@api.depends_context(...)`, and it doesn't inherit that from its inputs. Add `depends_context('company')` when the value depends on company-dependent or company-scoped inputs.
