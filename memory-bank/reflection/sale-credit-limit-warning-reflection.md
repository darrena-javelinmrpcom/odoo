# Reflection: sale-credit-limit-warning - Customer Credit Limit Warning

**Date**: 2026-10-31
**Task Complexity**: Level 2
**Phases**: 3 built (2 planned + 1 post-UAT E2E phase)
**Duration**: 2026-10-31 (single day, plan through E2E)

## Summary

A custom addon `custom_addons/sale_credit_limit_warning/` adds computed `credit_warning_message` and `credit_warning_level` fields to `sale.order`. An inherited form view shows two colour-coded banners: yellow at 80% or more of the limit (inclusive, per HITL gate #1) and red over 100%. The core `sale` banner is hidden. The work also added the `custom_addons` infrastructure and put Chromium and `websocket-client` in the Docker image. All ACs are met. Tests: 15/15 addon tests (14 compute/view tests and 1 browser tour) and core `TestSaleOrderCreditLimit` 7/7 green. UAT result was PASS_WITH_RECOMMENDATIONS (Required=0, Recommended=1). A manual browser re-check of the 500/900/1200/400 thresholds passed.

Task implementation quality: **Good**. Ecosystem effectiveness: **Moderately Effective**.

Build session logs: `.agent-logs/claude/by-task/sale-credit-limit-warning/` does not exist, so no tool-call counts are reported. No metrics are fabricated. Process facts below come from the orchestrator and from git/task-file evidence.

## What Went Well
- Discovery found that core `sale` already has a partial credit banner. The feature was built as an addon on top of it (override or hide) rather than by editing core. Core regression tests (7) stayed green.
- The human gates caught real issues. Gate #1 settled the 80% inclusive boundary. Gate #2 produced `32f7a5a8`, which fixed the compute `@api.depends` so it covers credit limit, credit and the company setting. Without that fix the banner would have been stale after those values changed.
- Sudo reads for accounting-restricted fields and currency conversion were identified at plan time.
- UAT and the E2E spec led to a runnable HttpCase + web_tour test, so the browser journey is now regression-protected.

## Challenges
- **Status not promoted after Phase 2.** The header stayed PLANNING_COMPLETE while Execution State said BUILD_COMPLETE, and `/bmb:uat` reads the header. It was promoted manually in `ea1cfd0f`.
- **Windows path rewriting.** The module-upgrade command from the workshop slides failed in Git Bash because MSYS rewrote `/etc/odoo/odoo.conf`. `MSYS_NO_PATHCONV=1` fixed it.
- **UAT gates blocked twice.** There was no journey doc (Level 2 skips `/bmb:creative`) and no `ux-patterns.md`. A hand-written journey doc and `--skip-ux-check` got past them.
- **Environment assumptions did not hold.** `odoo-dev` had no demo data, GBP rather than USD, the credit setting off, and no sales user. The journey doc had to include setup, and the walker used JSON-RPC.
- **UAT coverage was thin.** Mobile was walked at 929px only, because the 375x667 resize was not achievable (UAT-REC-01). axe-core was not run. The negatives and errors sections were not walked. There were no `.auth` tokens, so a pre-logged-in Chrome session was reused.
- **Phase 3 environment gaps.** Chrome was missing from the image (DECISION_NEEDED, and the human chose to add Chromium to the Dockerfile). `websocket-client` was also needed, otherwise Odoo silently skips browser tests. A selector guessed in the spec (`.o_form_sheet_bg`) was wrong and was corrected to `.o_form_sheet`.
- **Phase 3 skipped review gates.** It skipped the code-review and build-verifier agents; the build ran the tests itself.
- **Bookkeeping drift.** Phase 3 is not in the task's `### Phases` checklist.
- **Browser dialog.** Ctrl+S with no field focused opened Chrome's native "Save page as" dialog and froze the MCP tab.
- **Origin not pushable.** Origin (DaKaZ/odoo) is not writable, so all work is local and the push and PR steps were skipped.
- **`artifact_git_policy` mismatch.** `memory-bank/uat/artifacts/` was not gitignored despite `artifact_git_policy: ignore`, and untracked files there would trip the uncommitted-memory-bank HALT. It was added to `.gitignore`.

## Guardrail Misses & Root-Cause Analysis
The Guard & Recovery Log is "(none)", so there were no commit-guard FAILs or recorded re-invocations. However, there were two un-guarded misses:
1. The `@api.depends` omission, found by a human at gate #2 and not by tests or review. The tests passed because they set values before reading. A staleness test (change limit or setting, then re-read) was missing from the TDD brief.
2. Phase 3 skipped review and verifier agents without a recorded override. Nothing deterministic enforces the pipeline after a DECISION_NEEDED resume. This is probably an orchestrator-resume path issue rather than agent error.

## Lessons Learned
- A non-stored compute that reads sudo-only or company-dependent fields needs explicit depends on every input, and a test that mutates an input and re-reads.
- Specs written for E2E should state selectors as "verify against the DOM", not as guesses.
- Environment prerequisites (browser, `websocket-client`, demo data, currency) should be verified before the spec and journey are written, not after.

## Action Items
- Add Phase 3 to the task's `### Phases` checklist and the Guard & Recovery Log (record the skipped review and verifier), or run `/bmb:verify` on the final diff.
- Run the deferred UAT items when feasible: real 375px mobile, axe-core, and the negatives/errors sections.
- Find a writable remote and push the branch and open the PR.
- Optionally add `memory-bank/uat/artifacts/` to `.gitignore` in baseline.

## Memory-Bank Corrections
None identified from guard flags, since none fired. For consideration: `techContext.md` could note that browser tours need Chromium and `websocket-client` in the image, that `custom_addons` is the addon path, and the MSYS_NO_PATHCONV=1 requirement on Windows Git Bash. Those belong in Core State and are applied at archive or by a human.

## Claude Code Ecosystem Observations

### What Worked Well
- The HITL gates (#1 to #3) in the workshop flow caught real defects and decisions early.
- Discovery of the existing core banner during planning prevented a duplicate implementation.
- The `/bmb:uat` to E2E-spec to `/bmb:build` pipeline produced a working browser test.
- The DECISION_NEEDED return to the human for the Chrome decision was the right escalation.

### Friction Points
- **Status promotion**: the header status is not auto-promoted to BUILD_COMPLETE after build, and UAT depends on it.
- **Journey doc at Level 2**: UAT requires a journey doc, but Level 2 skips `/bmb:creative`, so the doc is hand-written.
- **`ux-patterns.md`**: it is required by UAT but absent by default.
- **Environment assumptions**: the workshop assumes demo data, USD and a sales user. Real instances differ, and there is no precheck.
- **Git Bash**: slide commands with absolute container paths break under MSYS.
- **Mobile viewport**: `resize_window` cannot reach 375x667.
- **Ctrl+S**: Ctrl+S in Chrome froze the MCP tab.
- **Phase tracking**: post-UAT E2E phases are not appended to the task's Phases list.
- **Review gates**: they can be bypassed in the post-DECISION_NEEDED resume path.
- **`artifact_git_policy`**: `ignore` is not applied to `.gitignore` automatically.

### Suggestions for Improvement
> **Note**: These are suggestions only. Do NOT implement changes.

- **Auto-promote task header**: have `/bmb:build` set the header Status when the final phase completes.
- **UAT journey for Level 2**: generate a lightweight journey doc from the ACs, or let `/bmb:uat` accept the ACs directly.
- **`/bmb:uat` environment preflight**: check demo data, currency and settings, and offer to emit setup steps.
- **E2E phase append**: have the post-UAT build append "Phase N: E2E" to `### Phases` and run the full review and verifier gates.
- **`artifact_git_policy: ignore`**: write the ignore entry at init or upgrade.
- **Windows note**: add `MSYS_NO_PATHCONV=1` to workshop and doc commands.
- **E2E spec writer**: mark guessed selectors as unverified.
- **Mobile UAT**: support a real device emulation mode for viewport tests.
- **UAT guidance**: warn against Ctrl+S, or use a save-free approach.

## Key Learnings

### Extractable Learnings
- **odoo-compute-fields** (`custom_addons/**/*.py`): List every input field in `@api.depends` for non-stored computes (including sudo-read, company-dependent and setting fields), and test by mutating an input then re-reading.
- **e2e-testing** (`**/tests/tours/*.js`, `*.test.*`): Verify the runtime environment (browser binary, websocket client, seed data) and DOM selectors before writing the E2E spec.

### Learned Rules Applied
No learned rules available.

### For Claude Code Workflow
1. Header Status and Execution State must stay in sync, or gates mis-fire.
2. Every build phase, including post-UAT E2E, should run the full review and verify pipeline and be tracked in Phases.

## Conclusion
The feature works and is well tested. The notable process gaps were status drift, skipped Phase 3 gates, and a UAT flow that needed hand-authored inputs and covered fewer sections than planned. Recommend archiving after recording the Phase 3 tracking and gate deviation in the task file.

**Overall Task Success**: Success
**Overall Workflow Effectiveness**: Moderately Effective
**Recommendation**: Ready to archive (remote push is blocked: origin is not writable)
