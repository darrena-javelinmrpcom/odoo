---
name: E2E Testing (learned)
globs: ["**/tests/tours/*.js", "**/tests/test_*e2e*.py", "*.test.*"]
paths: ["custom_addons/"]
topics: ["e2e", "testing", "uat", "odoo-tours"]
priority: low
auto_generated: true
derived_from: [sale-credit-limit-warning]
evidence_count: 1
last_validated: 2026-10-31
---

# E2E Testing

- Before writing an E2E spec or tour, verify the runtime environment: browser binary in the test image (Odoo `HttpCase` needs Chromium), the `websocket-client` Python package (without it Odoo silently skips browser tests), and the seed or demo data the journey assumes.
- Confirm DOM selectors against the live page before encoding them. In Odoo 18 forms, `.o_form_sheet_bg` wraps the status bar and banners; the sheet itself is `.o_form_sheet`.
