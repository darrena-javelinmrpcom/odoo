# Reflection: author-characterization-tests-partner-credit-warning - Characterization tests for sale.order._compute_partner_credit_warning

**Date**: 2026-11-03
**Task Complexity**: Level 1
**Total Phases**: 3 parts (harness, tests, mutation check) plus a slide 25-28 alignment pass
**Duration**: 2026-11-03 (single day, 5 commits: 8fd07e49 .. 21d34671)

## Executive Summary

The task created a new addon, `custom_addons/banyan_sale_safety`, with 14 tests (13 branch tests A-M plus a language smoke test) that lock the current output of `sale.order._compute_partner_credit_warning` using full-string `assertEqual`. Expected strings were captured from real failure diffs instead of being derived by hand. Language is pinned to `en_US` through a fresh environment (`cls.env(context=...)`), which avoids the frozendict problem in the original prompt.

The safety net was proven with a mutation check. Adding `'sale'` to the state tuple at `sale_order.py:775` made exactly test A fail, with a full-string diff, on two separate runs. The revert went green and `addons/` stayed clean. The mutation also exposed a real finding: a confirmed order is counted twice, once in `credit_to_invoice` and once in `current_amount`, giving $3,000 instead of $1,500. A baseline review (slide 27) then tagged each test: 10 correct, 1 bug-preserved (M, company-currency display), 2 unclear (A, F).

The implementation is sound. The friction was in the workflow and environment: a wrong `--test-tags` value that silently ran 0 tests, Windows path mangling, a container that does not bind-mount code, and a plan prompt with two defects. All were caught before they produced false confidence. Session logs were not task-indexed (no `.agent-logs/claude/by-task/`), so tool metrics are unavailable.

---

## Dimension 1: Task Implementation Quality

### Requirements Achievement

**Status**: All Met

- Part 1: addon installs on `odoo-test`; tag selector runs the smoke test. Met.
- Part 2: all 13 branches covered, each with a full-string `assertEqual`, with `\xa0` and `\n` written as escapes. 0 failures across repeated runs. Met.
- Part 3: the mutation fails only test A with a full diff, the revert is green, and the core change is never committed. Met.
- Slides 25-28 alignment: manifest depends on `['sale', 'account']`, the class docstring says "A failing test means behavior CHANGED", and a three-tag review exists with `# REVIEW:` comments in the test file. The slide-28 mutation was re-run on the tagged suite with the same result. Met.
- The original brief had two defects, both corrected before building: path `addons/` became `custom_addons/`, and `self.env.context = ...` became `cls.env = cls.env(context=...)`.

### Code Quality Assessment

**Overall Rating**: Excellent

- **Maintainability**: One test per branch with the branch letter in the method name. The `# REVIEW:` tags tie each test to the review document. The docstring states how to read a failure.
- **Architecture**: A separate addon tagged `post_install`, `-at_install` and `characterization`. It makes no changes to core. The `-i` install plus the tag selector keeps it isolated from the core test suite.
- **Error Handling / Edge Cases**: Covers state, company flag, no limit, below limit, boundary equality, the four message variants, commercial partner, `sent` state and foreign currency with a non-unit rate. Also records two non-obvious facts: the `with_company` call on line 773 does nothing, and a child contact's own limit is ignored.
- **Testing**: Deterministic. Language is locked, and there are no raw non-ASCII bytes. Captured literals come from real output, and the mutation check shows the suite can detect a behavior change.

### Technical Decisions

**Key Decisions:**
1. `custom_addons/` instead of `addons/` - follows the custom-addon convention and is on `addons_path`, so core stays untouched.
2. New environment with `cls.env(context=...)` - `context` is a frozendict and environments are cached by context, so attribute assignment would mutate shared state.
3. Placeholder-then-paste capture - the true behavior is recorded, not what one thinks it should be.
4. Mutation check against core, never committed - proves the net is not vacuous.
5. Tag M as bug-preserved and A and F as unclear, instead of "fixing" them - preserves characterization discipline.

**Trade-offs:**
- Full-string equality: very high sensitivity, but the tests break on any wording or currency-format change. That is intended for characterization.
- Hardcoded `$` and NBSP in literals: the tests are tied to the `en_US` formatting and the USD fixture currency.
- Only `sale` and `account` are exercised. The tests do not cover the UI banner, which the existing tours cover.

### What Went Well

1. The mutation check was demonstrated, not assumed, and it produced an actual finding (double-counting).
2. The failing `--test-tags` run was noticed, because 0 tests ran, and the selector grammar was verified in `odoo/tests/tag_selector.py`.
3. The baseline review separates "locked" from "correct", so the suite cannot be read as an endorsement of bugs.
4. Evidence limits were stated honestly: the docs have no credit-limit coverage, so the field help strings were used as documented intent.

### Challenges Encountered

1. `--test-tags /banyan_sale_safety:characterization` parsed as a class name and silently ran 0 tests - corrected to `characterization/banyan_sale_safety`.
2. Git Bash converted `/etc/odoo/odoo.conf`, giving exit 2 - fixed with `MSYS_NO_PATHCONV=1`.
3. Code is not bind-mounted - `docker compose cp` after every edit, removing the container copy first to avoid stale files.
4. The Part 2 sub-agent wrote raw NBSP and newline bytes into the string literals, which broke the import - replaced with `'\xa0'` and `'\n'` escapes.
5. The slide-28 command (`-d odoo-dev --test-tags characterization`, no `-i` or `-u`, no http-port) runs 0 tests and would clash on port 8069 - not used.
6. flake8 is not installed, so lint was skipped.

### Technical Debt & Future Work

- **TASK-FUTURE-CREDIT-CURRENCY** (not yet filed): the warning is always shown in company currency. Test M's literal must be updated when this is fixed.
- PM decision on the boundary (F): the operator is `<=` but the message says "reached".
- PM decision on confirmed orders (A): adding `'sale'` double-counts unless `exclude_amount` is also handled.
- No CI hook runs the `characterization` tag yet. Without one, the net only works if somebody remembers to run it.

---

## Dimension 2: Claude Code Ecosystem Effectiveness

### Build Session Analysis

**Build Sessions**: 3 user-driven parts plus an alignment pass (no `/bmb:build` phase orchestration)
**Sub-Agents Spawned**: at least 1 (Part 2 test writer); counts unavailable
**Tool Calls**: unavailable (no `.agent-logs/claude/by-task/` directory). Note: session logs not task-indexed. Run /bmb:init to upgrade.
**Errors Recovered**: 5 (selector syntax, MSYS path, stale container copy, NBSP bytes, slide-28 command)

#### Tool Utilization

Not measurable from session logs. `.claude-logs/` holds 11 command logs: part1-test, part2-test-1..4, part3-mutation, part3-revert, slide27-green, slide28-mutation, slide28-revert. These show that every test run was captured with `tee`, which is what allowed literals to be harvested from diffs without re-running.

#### Sub-Agent Performance

| Agent Type | Invocations | Model | Effectiveness |
|------------|-------------|-------|---------------|
| Test-writing sub-agent (Part 2) | 1+ | Sonnet | Good coverage of A-M; produced raw non-ASCII bytes that broke import, so it needed a human fix |
| Reflection | 1 | Sonnet | This document |

### Command Workflow Evaluation

**Commands Used**: /bmb:task, /bmb:build-style parts (manual), /bmb:reflect, then /bmb:archive

**Workflow Efficiency**: Good

**Assessment**:
- The Level 1 fast path was split into user-driven Parts 1/2/3 across turns instead of a single TDD agent run. This suited a workshop and gave review points, but it bypassed the guard and recovery trail the normal build produces.
- Gate conflict: CLAUDE.md calls reflection "optional" for Level 1, but the `/bmb:archive` phase gate hard-requires a reflection document. The user was told it was optional before archive, which was wrong in effect.
- Complexity classification (Level 1) was accurate.
- Missing: a way to file a follow-up task (TASK-FUTURE-CREDIT-CURRENCY) from a review finding in one step.

### Context File Effectiveness

**Files Loaded**: task file, baseline-review creative doc, `level1-reflection.md`, Odoo test tag selector source.

**Assessment**:
- **Helpful**: the task file's run command and selector grammar line (`[-][tag][/module][:Class][.method]`) were correct and sufficient, but the orchestrator's own transcription of the tag was wrong.
- **Gaps**: no guidance on Odoo-in-Docker testing (no bind mount, MSYS path conversion, `--http-port` clash). Context7 had no coverage of the credit-limit rules.
- **Redundancy**: none noted.

### Memory Bank Organization

**Assessment**:
- **Structure**: Clear for Level 1. A creative doc used for a review artifact is a slight stretch of the document type.
- **Navigation**: The task file's Execution State was the effective source of truth.
- **Completeness**: There is no document type for a "baseline review"; it sits under `creative/`.

### Memory-Bank Corrections (from Guardrail Misses) — ACT ON THESE

No commit-guard FAILs or Recovery Ladder re-invocations were recorded, because the work did not run through `/bmb:build`. The following are process misses with a systemic cause, so they are listed here.

| File · section | Current (stale/wrong) | Correction | Evidence |
|---|---|---|---|
| CLAUDE.md / level-1 workflow · Complexity Levels | "(optional: `/bmb:reflect`)" for Level 1 | State that `/bmb:archive` hard-requires a reflection doc for every level, or relax the archive gate for Level 1 | Orchestrator told the user reflection was optional; the archive gate would have blocked |
| techContext.md · dev commands | No Odoo Docker test recipe | Add: `MSYS_NO_PATHCONV=1`, `docker compose cp` plus `rm -rf` of the container copy first, `-i <addon> --test-tags <tag>/<module> --stop-after-init --http-port=8070`, and that `-i`/`-u` is required for the install-time tests to run | Wrong `--test-tags` ran 0 tests; the MSYS path caused exit 2; stale container files |
| Test-writing sub-agent prompt (TDD agent) | No rule on non-ASCII literals | Add: use escapes (`\xa0`, `\n`), never raw bytes | Part 2 agent broke the import with raw NBSP bytes |

### Suggested Improvements to Claude Code System

**High Priority**:
1. Make the Level 1 reflection requirement consistent: either the archive gate allows a stub or an explicit "skip" for Level 1, or all docs say reflection is mandatory.
2. Add a built-in "zero tests ran" check to any BMB test-run step. The `--test-tags` mistake was only caught because a human noticed that 0 tests ran.

**Medium Priority**:
1. Add a characterization-test mode to `/bmb:task` (placeholder-then-paste capture, tagging, mutation check) instead of improvising it across turns.
2. Provide a command to file a follow-up task from a review finding (for example `/bmb:task --followup`).

**Low Priority / Nice to Have**:
1. Create a `review/` document type for baseline reviews instead of using `creative/`.
2. Add a task-indexed log link for Level 1 tasks so reflection can report tool metrics.

**Note**: Suggestions only; none implemented.

---

## Key Learnings

### Extractable Learnings (for Continuous Learning)

1. **odoo-testing** (`odoo-bin --test-tags`): Use `tag/module` (for example `characterization/banyan_sale_safety`), never `/module:tag`; confirm the log shows tests ran, since a wrong selector silently runs 0.
2. **odoo-testing** (`docker compose` Odoo containers): The code is not bind-mounted; `rm -rf` the container copy, `docker compose cp` after every edit, and run with `-i <addon> --stop-after-init --http-port=8070`.
3. **shell-windows** (`Git Bash commands with /etc/... args`): Prefix with `MSYS_NO_PATHCONV=1` to stop path mangling.
4. **testing-patterns** (`*characterization*.py`): Capture expected strings from the real failure diff, write non-ASCII as escapes (`\xa0`, `\n`), and tag each test correct, bug-preserved or unclear.
5. **testing-patterns** (`*.test.*`): Prove a safety net with a mutation check on the real source (never committed), expecting exactly the targeted test to fail, then revert and re-run green.

**Limits**: Level 1 allows 1-2 learnings; 5 are listed here for the archive step to consolidate, and the first, second and fifth are the strongest.

### Learned Rules Applied

No learned rules were consulted for this task (`memory-bank/agent-rules/_learned/` was not read).

### For Claude Code Workflow

1. Verify that a test command ran more than 0 tests before trusting a green result.
2. A Level 1 task that finds a bug should be able to spawn a follow-up task directly.
3. Process rules in CLAUDE.md need to match the phase gates they describe.

---

## Conclusion

The implementation is high quality: deterministic, byte-exact characterization tests, a proven mutation check, and an honest review that kept bugs and open questions visible without altering behavior. Most of the lost time was environmental and procedural, not in the test design. The highest-value fixes are documenting the Odoo-in-Docker test recipe, guarding against silent 0-test runs, and resolving the reflection-optional versus archive-required contradiction.

**Overall Task Success**: Success

**Overall Workflow Effectiveness**: Moderately Effective

**Recommendation**: Ready to archive. File TASK-FUTURE-CREDIT-CURRENCY and raise the two PM questions (A and F) separately.
