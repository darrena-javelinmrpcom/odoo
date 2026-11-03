# User Journey: Customer Credit Limit Warning Banner

**Task**: sale-credit-limit-warning
**Feature**: sale-credit-limit-warning
**Source**: acceptance criteria in `memory-bank/tasks/sale-credit-limit-warning.md` + Week 4 workshop UAT briefing (slides 55, 59)
**Environment**: dev — `http://localhost:8069`, database `odoo-dev`
**Created**: 2026-10-31

## Journey Overview

A user building a quotation sees a colour-coded banner at the top of the Sale Order form when the customer is approaching (yellow, ≥ 80%) or over (red, > 100%) their credit limit, and no banner otherwise. The banner is computed and live; it recomputes when lines or customer change.

**Success statement**: before sending or confirming a quotation, the user can tell from the form alone whether this order pushes the customer near or over their credit limit, with concrete figures.

## Test Accounts Used

| Role     | Account             | Used in                         |
|----------|---------------------|---------------------------------|
| admin    | admin               | Setup, Happy, Mobile, Errors    |
| salesman | sales@example.com   | Negative N1 only                |

Auth references come from `memory-bank/uat-config.md` Persona Map. The `sales@example.com` user does **not** exist in `odoo-dev` as of 2026-10-31. If it is missing, N1 is reported BLOCKED (a setup gap, not a product defect).

## Expected Banner Contents

Company currency is **GBP**. Amounts are formatted by `formatLang` (e.g. `£ 1,000.00`; the space may be a non-breaking space). Outstanding receivables for the freshly-created customer are £ 0.00, so `total = order total`.

- **Yellow** (`div.alert.alert-warning[role=alert]`), when `800 ≤ total ≤ 1000`:
  - `Deco Addict is approaching its credit limit of £ 1,000.00.`
  - `Outstanding receivables (incl. confirmed orders to invoice): £ 0.00`
  - `This order: £ <order total>`
  - `Total after this order: £ <order total>`
- **Red** (`div.alert.alert-danger[role=alert]`), when `total > 1000`: headline `Deco Addict exceeds its credit limit of £ 1,000.00.` plus the same three lines.
- **None**, when `total < 800`: no credit banner of either colour, and core's own yellow "credit limit" banner is not shown either.
- Exactly **one** credit banner is visible at a time. It sits between the status bar (header) and the form sheet.

## Setup (once per run, Actor: admin)

Each step is idempotent: reuse a record if it already exists.

1. Log in at `/web/login` as admin.
2. **Enable the feature switch**: Settings → Invoicing (or Accounting) → *Customer Payments* → tick **Sales Credit Limit** → Save. Leave the default credit limit empty or 0.
   - Without this switch, no banner ever appears (by design: gated on `account_use_credit_limit`).
3. **Customer**: Contacts → New → Company **Deco Addict** → Save. Then open the *Invoicing / Accounting* tab and set **Credit Limit = 1000** → Save.
4. **Second customer (no limit)**: Contacts → New → Company **UAT No Limit Co** (credit limit left at 0) → Save.
5. **Product**: Sales → Products → New → Name **Credit Warning Demo Product**, Sales Price **1.00**, Customer Taxes **empty** (remove any default tax) → Save.

**Verify (setup)**
- [ ] Settings saved without error; Sales Credit Limit is ticked
- [ ] Deco Addict shows Credit Limit 1,000.00
- [ ] Product price 1.00 with no customer taxes

## Happy Path (Actor: admin)

Covers AC-ENTRY-1, AC-HAPPY-1, AC-HAPPY-2, AC-HAPPY-3c, AC-HAPPY-7.

1. Sales → Quotations → **New**. Customer: **Deco Addict**.
2. Add a line: **Credit Warning Demo Product**, quantity **500**. Confirm the line has no tax and the untaxed total equals the taxed total (£ 500.00). Save (Ctrl+S or the save icon). The order gets a number (e.g. S00001).
   - **Expected: NO banner** (50% of limit).
3. Change quantity to **900**. Save.
   - **Expected: YELLOW banner** with headline "approaching", This order £ 900.00, Total after this order £ 900.00, Outstanding £ 0.00.
4. Change quantity to **1000**. Save.
   - **Expected: still YELLOW** (exactly at limit; red requires strictly over).
5. Change quantity to **1200**. Save.
   - **Expected: RED banner** with headline "exceeds", This order £ 1,200.00, Total £ 1,200.00.
   - Take a screenshot of the form with the red banner visible (key evidence).
6. Change quantity to **400**. Save.
   - **Expected: banner GONE.**
7. Live update (no save): change quantity to **1200**, then click outside the line without saving.
   - **Expected: RED banner appears before saving.** Then discard changes.

**Verify (happy)**
- [ ] Step 2: no `.alert-warning` / `.alert-danger` credit banner in the form
- [ ] Steps 3–4: exactly one `.alert-warning` banner; text matches the four lines above with correct figures
- [ ] Step 5: exactly one `.alert-danger` banner; headline says "exceeds"; figures correct
- [ ] Step 6: no credit banner
- [ ] Step 7: banner updates without a save
- [ ] Banner position is between the status bar and the sheet, never inside the sheet
- [ ] No traceback dialog, no red error toast, and no JS errors in the console (filter: `error|Error|Traceback`)
- [ ] Figures are real numbers, not placeholders or `False`

**Cleanup (happy)**: Leave the quotation in draft. It is reused by Mobile and by Negative N2 below; it is cancelled at the end.

## Mobile (Actor: admin, viewport 375×667)

1. Open the Deco Addict quotation from the happy path. Set quantity to **1200** and save.
2. Scroll to the top of the form.

**Verify (mobile)**
- [ ] Red banner visible, full width, text wraps; all four lines readable without horizontal scroll
- [ ] Banner does not overlap the status bar or action buttons

**Cleanup (mobile)**: none.

## Negative / Access-Denied Paths

### N1: Salesman without accounting rights (Actor: salesman) — AC-ERROR-1

Precondition: `sales@example.com` exists with *Sales: User: Own Documents Only* and no Invoicing/Accounting group. If the account is missing, report BLOCKED.

1. Log in as sales@example.com.
2. Sales → Quotations → New. Customer **Deco Addict**, line **Credit Warning Demo Product** qty **1200**. Save.

**Verify (N1)**
- [ ] No "Access Error" / permission dialog on open, edit or save
- [ ] Red banner shown with the same figures as happy step 5

**Cleanup (N1)**: Cancel this quotation (Cancel button). If a confirmation dialog appears, it is an Odoo in-page modal, not a native browser dialog.

### N2: Confirmed order shows no banner (Actor: admin) — AC-HAPPY-4

1. Open the Deco Addict quotation with qty 1200 (red banner showing).
2. Click **Confirm**.

**Verify (N2)**
- [ ] After confirmation (state Sales Order), no credit banner is visible

**Cleanup (N2)**: Cancel the confirmed order (Cancel button). After cancellation, still no banner.

## Error Scenarios

### E1: New quotation with no customer (Actor: admin) — AC-ERROR-2, AC-HAPPY-3d

1. Sales → Quotations → New. Do not pick a customer.
2. Add a line **Credit Warning Demo Product** qty 1200 (do not save; saving without a customer is a normal required-field validation).

**Verify (E1)**
- [ ] No traceback or error dialog from the banner computation
- [ ] No credit banner shown

**Cleanup (E1)**: Discard the unsaved record.

### E2: Customer with no credit limit (Actor: admin) — AC-HAPPY-3a

1. Sales → Quotations → New. Customer **UAT No Limit Co**, line **Credit Warning Demo Product** qty **5000**. Save.

**Verify (E2)**
- [ ] No credit banner despite the large total

**Cleanup (E2)**: Cancel the quotation.

## Out of Scope for UAT

- Multi-currency conversion (AC-HAPPY-6), multi-company (AC-ERROR-4) and the core regression suite (AC-ERROR-3): covered by the addon's Python tests.
- Payment/invoice-driven changes (AC-HAPPY-5): covered by Python tests. Too costly to stage through the UI.
- Turning the Sales Credit Limit setting back off: optional manual check (no banner expected).

## Final Cleanup

- Cancel any remaining UAT quotations created in this run.
- Leave Deco Addict, UAT No Limit Co, the demo product and the setting in place for re-runs.
