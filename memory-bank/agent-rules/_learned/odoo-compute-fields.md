---
name: Odoo Computed Fields (learned)
globs: ["custom_addons/**/*.py"]
paths: ["custom_addons/"]
topics: ["odoo", "orm", "compute-fields", "testing"]
priority: low
auto_generated: true
derived_from: [sale-credit-limit-warning]
evidence_count: 1
last_validated: 2026-10-31
---

# Odoo Computed Fields

- List every input field in `@api.depends` for non-stored computes, including fields read through `sudo()`, company-dependent fields (e.g. `partner_id.commercial_partner_id.credit_limit`) and company settings (e.g. `company_id.account_use_credit_limit`). A missing dependency leaves the value stale in the form until reload.
- Test each compute by changing one input and re-reading the field (staleness test), not only by setting values before the first read.
