# UAT Report: Customer Credit Limit Warning Banner

**Journey**: sale-credit-limit-warning-credit-banner-user-journey
**Run Date**: 2026-10-31T13:00:00Z
**Run ID**: uat-20261031-a7c3
**Task**: sale-credit-limit-warning
**Feature**: sale-credit-limit-warning
**Sections Run**: happy, mobile
**Environment**: http://localhost:8069 (DB odoo-dev)
**UAT Agent Version**: bmb 2.2.1
**Result**: PASS_WITH_RECOMMENDATIONS
**UX check**: skipped (flag); ux-patterns hash: n/a

**Counts**: Required=0  Recommended=1  Optional=0
**Confidence Distribution**: high=1  medium=0  low=0

**Artifacts**: memory-bank/uat/artifacts/uat-20261031-a7c3/

---

## Summary

The happy and mobile sections were walked as the admin persona against odoo-dev. All six reported happy-path steps (no banner at 50%, yellow at 900 and at exactly 1000, red at 1200, banner gone at 400, live red banner while the record is unsaved then discard) passed their Verify items, and the mobile check confirmed the red banner is full width, does not overlap the status bar or sheet, and produced no JS errors. No Required findings. The one Recommended finding is a test-infrastructure coverage gap: the 375x667 viewport could not be achieved (inner width stayed 929), so Odoo's small-screen layout (<768px) was never exercised. The negatives and errors sections, axe-core, and the salesman persona were not covered in this run (see below).

---

## Findings

### Required (0)

None.

### Recommended (1)

#### UAT-REC-01 — Mobile viewport (375x667) not achievable; narrow-layout not verified
- **Severity**: Recommended
- **Confidence**: high
- **Section**: mobile
- **Step(s)**: Step 1 (Open S00001, set line qty to 1200, save)
- **Persona**: admin
- **Source**: walker
- **Classification**: test-infrastructure coverage gap (not a product defect)
- **What happened**: The browser window could not be made narrower than innerWidth 929, so the Odoo small-screen layout was not tested. The banner was checked at 929px only.
- **Expected**: innerWidth 375
- **Observed**: innerWidth 929, innerHeight 883 (outerWidth 516)
- **Repro**:
  1. resize_window 375x667
  2. read window.innerWidth
- **Evidence**: screenshot `artifacts/uat-20261031-a7c3/mobile-step1-after.jpg`
- **Suggested fix**: Re-run with device emulation / DevTools mobile mode, or check manually on a real narrow viewport.
- **References**: none

### Optional (0)

None.

---

## Journey Coverage

### Section: happy (serial)
Journey step 1 (create quotation, customer Deco Addict) is not reported as a separate walker step; the order S00001 was handed off and used from step 2. Setup was done via ORM (see Run Notes).
- [✓] Step 2: qty 500 saved, no banner — PASS
- [✓] Step 3: qty 900, single alert-warning, four lines correct, between statusbar and sheet — PASS
- [✓] Step 4: qty 1000, still alert-warning at exact limit — PASS (no screenshot captured; no finding raised)
- [✓] Step 5: qty 1200, single alert-danger, "exceeds", 1,200.00 figures — PASS
- [✓] Step 6: qty 400, banner gone — PASS
- [✓] Step 7: live update unsaved shows red banner; discard restores 400 with no banner — PASS

### Section: mobile (parallel)
- [!] Step 1: red banner full width, four lines readable, no horizontal scroll (scrollWidth 929 <= innerWidth 929) — PASS at 929px only, DEVIATION ([UAT-REC-01])
- [!] Step 2: no overlap with status bar/sheet (statusbar bottom 153.75 < alert top 161.75; alert bottom 261.75 < sheet top 269.75); no JS errors — PASS at 929px only, DEVIATION ([UAT-REC-01])

### Section: negatives (not run)
- [—] N1: Salesman without accounting rights — NOT COVERED (AC-ERROR-1)
- [—] N2: Confirmed order shows no banner — NOT COVERED (AC-HAPPY-4)

### Section: errors (not run)
- [—] E1: New quotation with no customer — NOT COVERED (AC-ERROR-2, AC-HAPPY-3d)
- [—] E2: Customer with no credit limit — NOT COVERED (AC-HAPPY-3a)

Acceptance-criteria traceability: happy section covers AC-ENTRY-1, AC-HAPPY-1, AC-HAPPY-2, AC-HAPPY-3c, AC-HAPPY-7 (per journey doc). Out of UAT scope by design: AC-HAPPY-6, AC-ERROR-4, AC-ERROR-3, AC-HAPPY-5 (covered by Python tests).

---

## Run Notes and Deviations

1. Setup data (credit-limit setting, Deco Addict limit 1000, UAT No Limit Co, Credit Warning Demo Product at 1.00 with no tax) was created by the happy walker via ORM JSON-RPC from the logged-in admin session rather than UI clicks; verified by read-back. Setup is a precondition, not under test.
2. Auth: the Chrome session was pre-authenticated as admin; no `.auth/` token files and no `$TEST_ADMIN_PW` exist. The salesman persona was not exercised (negatives not in this run; `sales@example.com` does not exist in odoo-dev).
3. axe-core was not run by either walker; no accessibility results exist for this run. Console pattern read (error|Error|Traceback) showed no errors.
4. Mobile walker could not achieve 375x667 (see UAT-REC-01).
5. Sections walked: happy, mobile (project default). Not walked: negatives (N1, N2) and errors (E1, E2).
6. Evidence gate: no findings dropped. All referenced artifacts exist on disk. Walker JSONs were already stripped of reasoning fields.

---

## UX Pattern Conformance

UX check: skipped (flag `--skip-ux-check`); ux-patterns hash: n/a. No conformance table produced.

---

## Next Action

Required findings == 0: UAT PASS (with recommendations). The E2E test specification will be produced by the spec writer at:
```
memory-bank/uat/spec-sale-credit-limit-warning-e2e.md
```

Recommended next steps:
- Optionally re-run mobile with true device emulation to close UAT-REC-01, and walk `negatives` and `errors` sections (needs a salesman test account) to cover AC-ERROR-1, AC-HAPPY-4, AC-ERROR-2, AC-HAPPY-3a/d.
- Then:
```
/bmb:build sale-credit-limit-warning
```
This will implement the E2E spec using the project's test framework (see techContext.md).
