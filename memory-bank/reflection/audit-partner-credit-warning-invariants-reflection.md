# Reflection: audit-partner-credit-warning-invariants - Partner credit warning knowledge-archaeology audit

**Date**: 2026-11-03
**Task Complexity**: Level 1 (analysis-only, no code change)
**Total Phases**: 0 build phases (analysis + verification pass, 2 commits)
**Duration**: single session; commits 80401fbb (rev 1) and 914f0fed (rev 2)

## Executive Summary

The task audited the Odoo 18 partner credit warning (`sale.order._compute_partner_credit_warning`, `addons/sale/models/sale_order.py:770-781`, and `account.move._build_credit_warning_message`, `addons/account/models/account_move.py:1846-1891`). The deliverable is `memory-bank/creative/audit-partner-credit-warning-invariants-knowledge-archaeology.md`. Rev 2 holds 29 invariants across 10 categories, each with file:line, failure mode and confidence, plus 15 calibration items, 10 latent defects, 12 proposed `systemPatterns.md` ENFORCED entries and a section 5 verification table. (Rev 1 had 12 calibration items and 6 latent defects.)

> Provenance note (orchestrator): the Reflection Agent wrote this from the orchestrator's task history and `git log`, without reading the deliverable. The orchestrator corrected the counts above against rev 2.

The checklist the user asked for (sudo, with_company, with_context, depends ordering, discarded return, singleton contracts, currency, state gates, boundaries, commercial_partner_id, `_()`, access control) is covered. Rev 1 contained four factual errors that only surfaced when 12 refute-oriented sub-agents checked each ENFORCED entry at code level. Rev 2 corrected them and added new findings. The proposed `systemPatterns.md` entries were deliberately not applied because they are Core State and need `chore/banyan-admin`.

No guard FAILs or Recovery Ladder re-invocations occurred (no `/bmb:build` ran). The one process miss was `/bmb:archive` halting at the phase gate (no reflection, no Latest Commit field). That is a gate working as designed, but it exposes a workflow mismatch (below).

---

## Dimension 1: Task Implementation Quality

### Requirements Achievement
**Status**: All Met (after rev 2).
All requested invariant classes are covered with line-level evidence. The line ranges were independently confirmed correct by the user. Verification result: 12/12 entries upheld (3 TRUE, 9 TRUE WITH CAVEATS, 0 FALSE).

### Accuracy (rev 1 vs rev 2)
**Overall Rating**: Good. Rev 1 was usable but not trustworthy until verified. Rev 2 is solid.

Errors in rev 1 caught only by verification:
- A2: rationale "keep helper self non-sudo so lang is the user's" was wrong. `sudo()` preserves context and uid.
- I2: "non-stored = recomputed on read" was wrong. Non-stored computes are cached per transaction, and the field has no `depends_context` for company.
- F1: `use_partner_credit_limit` called "UI-only", but its inverse writes `credit_limit`.
- G1: the staticmethod failure was understated. Outside a request you get untranslated English.

New findings from verification: negative `credit_limit` always warns; receivables posted on contacts rather than the commercial partner are missed; the invoice compute lacks depends; L1 multi-currency mislabelling raises its severity.

Pattern: the errors were all in *rationale/mechanism* claims (why something is done, how caching behaves), not in "what the code does" claims. In the first pass the orchestrator read only narrow slices of the framework (`fields.py` string cache conversion, `translate.py` `_get_lang`). The ORM mechanisms behind the wrong claims were inferred from convention, not read from source: `sudo()` context preservation in `api.py`, the non-stored compute cache path in `fields.py`/`models.py`, and the inverse of `use_partner_credit_limit`.

### Evidence Quality
Strong: file:line for every invariant, plus confidence labels. Weakness: one verifier's repo-wide XML grep timed out, so a consumer-usage claim had a gap until closed with `git grep`.

### Technical Decisions
1. Placed the audit under `creative/` since no `audit/` or `analysis/` bucket exists. Workable, but the doc type is misfiled semantically.
2. Per-claim refute-oriented verification (one agent per ENFORCED entry, no Markdown reading) before treating the doc as authoritative. Cost: 12 agents. Payoff: 4 corrections plus 4 new findings. High value.
3. Withheld Core State edits (`systemPatterns.md`) from the task branch, honouring branch routing.

### What Went Well
1. Independent refute-oriented verification found real errors and extended the findings.
2. User's challenge to verify line ranges and the code-only constraint on verifiers prevented laundering of rev 1's own prose into "confirmation".
3. Slug-collision detection avoided clobbering an existing task.

### Challenges
1. Rev 1 mechanism errors, resolved via verification and rev 2.
2. Subagent grep timeout on a large repo, resolved with `git grep` by the orchestrator.
3. Archive gate halt, resolved by running reflection.

### Technical Debt & Future Work
- 12 proposed ENFORCED entries not yet in `systemPatterns.md`; apply via `chore/banyan-admin` (archive may handle).
- Latent defects (negative limit, contact-posted receivables, missing depends, multi-currency labelling) are not fixed. The in-repo consumer `custom_addons/sale_credit_limit_warning` should be reviewed against the corrected I2/A2 mechanisms.

---

## Dimension 2: Claude Code Ecosystem Effectiveness

### Build Session Analysis
No `.agent-logs/claude/by-task/audit-partner-credit-warning-invariants/` directory exists, so metrics are from the orchestrator's account only. Build sessions: 0. Sub-agents: 12 general-purpose verification agents (all returned; 1 hit a grep timeout). Fast-path TDD agent and affected-test run skipped as N/A. Tool-level counts are unavailable.

### Command Workflow Evaluation
**Workflow Efficiency**: Fair.
- `/bmb:task` is built for code fixes. For analysis-only work its TDD fast path is N/A and the task has no build phase, so "Latest Commit" and BUILD_COMPLETE-style fields are never populated.
- `/bmb:archive` gate requires a reflection even for L1 and a Latest Commit field; both were absent, so archive halted. Correct per gate, but it forces a detour for a legitimate task type.
- No home for audit docs: `creative/` was used. A `memory-bank/audit/` or `analysis/` type (or a task `kind: analysis` that skips TDD and sets Latest Commit from the last commit) would fit.
- Complexity Level 1 was accurate for effort-to-change but understates the verification effort (12 agents).

### Context File Effectiveness
Level 1 reflection context was sufficient. Gap: nothing guides how to verify an analytical deliverable (refute-oriented, code-only verifiers, mechanism vs behaviour claims).

### Memory Bank Organization
Branch routing worked (Work-Specific on task branch, Core State proposals deferred). Missing document type for analysis/audit deliverables.

### Memory-Bank Corrections (from Guardrail Misses)
None, no guard FAILs or re-invocations. (The archive halt is a workflow-shape issue, not a stale-guidance miss.)

### Suggested Improvements to Claude Code System
**High Priority**:
1. `/bmb:task` analysis mode: detect analysis-only intent, skip TDD fast path, record a Latest Commit on commit so archive's gate passes, and let reflection be optional or auto-lightweight.
2. Add an audit/analysis document bucket (e.g. `memory-bank/audit/<slug>-*.md`) in the Work-Specific taxonomy.

**Medium Priority**:
1. Provide a reusable "refute-oriented verifier" agent prompt template (read code only, try to falsify one claim, return TRUE / TRUE WITH CAVEATS / FALSE with file:line).
2. Advise verifiers to use `git grep` (or scoped paths) rather than repo-wide file-type greps in large repos to avoid timeouts.

**Low Priority**:
1. Have archive's gate message explain how to satisfy it for analysis-only tasks.

---

## Key Learnings

## Extractable Learnings

- **verification** (`analysis/audit docs`): Verify rationale and mechanism claims about framework behaviour (caching, sudo, context) against framework source with a refute-oriented agent, since behaviour claims survive review far better than mechanism claims.
- **odoo-orm** (`addons/**/models/*.py`): Do not assume non-stored computed fields are recomputed on read; they are cached per transaction and need `depends_context` to vary by company or user.
- **tooling** (`large repos`): Use `git grep` or path-scoped searches in sub-agents instead of repo-wide file-type greps, which time out.

### Learned Rules Applied
Not consulted (user explicitly forbade reading `agent-rules/_learned/` for this task).

### For Claude Code Workflow
1. Analysis-only tasks need a first-class path through task, archive gate and storage location.
2. Independent per-claim verification should be a standard step for any doc that proposes ENFORCED/Core State rules.

---

## Conclusion

The audit is accurate and useful to a senior Odoo developer after rev 2, and verification demonstrably paid for itself (4 corrections, 4 new findings). The workflow friction was structural: the task and archive machinery assume code deliverables.

**Task Quality Rating**: Good (Excellent post-verification; rev 1 alone would have shipped four wrong mechanism claims)
**Ecosystem Effectiveness Rating**: Moderately Effective
**Overall Task Success**: Success
**Recommendation**: Ready to archive; follow up separately to apply the 12 ENFORCED entries to `systemPatterns.md` via `chore/banyan-admin`.
