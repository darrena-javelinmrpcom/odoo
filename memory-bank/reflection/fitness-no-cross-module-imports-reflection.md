# Reflection: fitness-no-cross-module-imports - Module isolation fitness function

**Date**: 2026-11-03
**Task Complexity**: Level 1
**Total Phases**: 1 (plus an unplanned validate-and-harden loop)
**Duration**: 2026-11-03 (single day)

## Executive Summary

The task delivered an AST-based fitness function (`scripts/fitness/no-cross-module-imports.py`) that forbids one custom addon importing another addon's Python modules, with a configurable allow-list (`.allow`), `ALLOWED`/`DYNAMIC` reporting, JSON output, and 39 unit tests. Scope grew after the user broadened the ask: an ENFORCED constraint in `systemPatterns.md` and a human-authored rule `agent-rules/odoo-fitness.md` now wire the script to the Code Reviewer as BLOCKING. The original task text had declared both out of scope, so the scope change is a documented deviation, not drift.

The most valuable part was the adversarial validation. The author's 18 unit tests passed throughout, yet five isolated scenario agents (violation, compliant, evasion, false positives, allow-list/CLI) found six real gaps. The evasion agent caught 8 of 11 evasions. The CLI agent found that allow-listed imports passed silently, justification was not enforced, and env or file allow-lists replaced the defaults. All six were fixed in 9be5ca73. Running the fixed script on the real `addons/` tree then exposed a false positive (relative `__import__(..., level=1)`), which was also fixed. The rule, script and reviewer chain was demonstrated end to end: the reviewer found the rule through the index, blocked the violating diff, and approved the clean one.

Open gaps remain and are listed below. They are known and recorded, not hidden.

---

## Dimension 1: Task Implementation Quality

### Requirements Achievement

**Status**: Met, with known open follow-ups.

- stdlib only, `ast`-based, sorted `file:line: message`, exit 0/1/2, default `custom_addons/`, allow-list configurable without code edits: met.
- `custom_addons/` gives 0 violations and 1 allowed (the tests fixture). `addons/` gives 1138 violations, 664 allowed, 1 dynamic, 0 parse errors in 7512 files. The v1 script missed about 30 real attribute-access cases.
- Scratch-violation demonstration: exit 1 with exactly 1 violation, then exit 0 after removal.
- Beyond the original scope: the ENFORCED constraint, the agent rule and the rules-index regeneration.

### Code Quality Assessment

**Overall Rating**: Good

- **Maintainability**: single-file script with a sidecar allow file. The allow file's justification requirement makes exceptions auditable.
- **Architecture**: alias-tracking plus attribute-chain resolution is the right design for `ast` (it handles `from odoo import addons` followed by `addons.x`). Computed names are reported as `MODULE-ISOLATION-DYNAMIC` rather than silently passing, which is the correct bias for a gate.
- **Error handling**: syntax errors are reported without crashing. Defects D1-D3 (below) remain in config and CLI error paths.
- **Testing**: 39 tests, but test quality is only as good as the author's imagination. See the lesson below.

### Technical Decisions

1. AST with alias tracking rather than regex. Correct, and it stayed deterministic.
2. Dynamic imports are flagged when the name is computed. Gained: no silent pass. Cost: some noise (1 on `addons/`).
3. Allow sources are additive, with `--no-default-allow` as the opt-out. This fixed a silent safety downgrade. An override-by-replacement default was the wrong design.
4. A text pre-filter was kept for speed. The script docstring's claim that skipped files "cannot contain a violation" is false (escape bypass, e.g. `\x61ddons`). It is retained as a known weakness.

**Trade-offs**
- Speed against completeness: the pre-filter keeps `addons/` runs at roughly 28-68s over OneDrive (`custom_addons/` is instant) but is bypassable.
- Strictness against noise: forcing a justification gives an audit trail but adds friction for every allow entry.

### What Went Well

1. Independent adversarial agents found six gaps that the same-author unit tests missed, and a re-validation round confirmed the fixes.
2. Running against a large real corpus (`addons/`) surfaced a false positive that no synthetic fixture had.
3. The Code Reviewer discovered the rule through the index without prompting and respected the "do not edit the allow-list" warning.
4. Scenario B's agent blocked on a failed precondition instead of improvising.

### Challenges Encountered

1. The first validation found six gaps. These were fixed with 21 additional tests.
2. The scenarios assumed an addon `banyan_sale_safety` that does not exist at HEAD. An empty leftover directory made it look present. The orchestrator approved a stub scaffold.
3. The scope broadened mid-task, so the task file's "out of scope" line was stale for several commits.

### Technical Debt & Future Work

See "Known open follow-ups".

### Known open follow-ups (not fixed in this task)

- **D1**: a missing default `.allow` file is silently ignored. It should warn, or exit 2 when the file was named explicitly.
- **D2**: a non-UTF-8 allow file produces a traceback and exit 1 instead of a usage error with exit 2.
- **D3**: with `--format json`, argparse errors leave stdout empty. Consumers get no JSON error object.
- **Weak justification check**: a punctuation-only comment counts as a justification.
- **Text pre-filter**: bypassable via escapes, so the "cannot contain a violation" docstring claim is wrong and should be corrected or the filter dropped.
- **Plausible evasion variants still missed** (4 of the 14 agent-invented extras that missed):
  - `getattr(odoo.addons, x)`
  - `sys.modules['odoo.addons.x']`
  - assigned alias `im = importlib.import_module`
  - load-by-path via `spec_from_file_location`

  The other 10 are deliberate obfuscation and were judged out of scope for a reviewer-time gate.
- **Corpus note**: `addons/` shows 1138 violations by design (Odoo core cross-imports). It is a comparison baseline, not a target.

---

## Dimension 2: Claude Code Ecosystem Effectiveness

Metrics are unavailable: no `.agent-logs/claude/by-task/fitness-no-cross-module-imports/` exists. Findings below come from session facts supplied by the orchestrator.

### Build Session Analysis

- Sub-agents: 5 scenario agents in the first round, a re-validation round (C and E re-run), plus the build-code-reviewer-agent on diffs A and B.
- Guard FAILs / re-invocations: none recorded in the task file. The "re-invocations" here were deliberate re-validation, not recovery from a guard flag. The six gaps were found by the adversarial agents, not by `commit-guard`.
- No tool-count table, because no logs exist.

### Worktree isolation on Windows, OneDrive and large repos

- `isolation: "worktree"` failed. Odoo test-fixture filenames exceed MAX_PATH ("Filename too long"). It left 5 orphan `worktree-agent-*` branches that had to be deleted. Repo-local `git config core.longpaths true` fixes the error.
- Even with that fix, a full worktree is 43,128 tracked files inside OneDrive. Five of them would be about 215k files syncing.
- Workaround: orchestrator-created detached sparse worktrees (`custom_addons`, `scripts`, `memory-bank`, 91 files) under `worktree_root` (`~/banyan-wt/odoo/`, outside OneDrive), with agents told to use absolute paths. This worked well, and everything was removed afterwards.

### Subagent precondition handling

The scenarios were written against an addon that did not exist. The failure was in the orchestrator's precondition check, not in the agents. Scenario B's agent correctly reported BLOCKED rather than improvising, which is the desired behavior.

### Reviewer rule discovery

The rule to index to script to reviewer chain worked. The reviewer found `odoo-fitness.md` via `agent-rules-index.md` and ran the script over all of `custom_addons/`. It reported BLOCKING with the `self.env['model']` fix and approved the compliant diff with "module isolation: clean". Generating the index was necessary (commit d1455527). Without it the rule would not have been discoverable.

### Command Workflow Evaluation

**Workflow Efficiency**: Good. Level 1 `task -> build -> reflect` was appropriate, but the task grew beyond Level 1 in practice (new rule, systemPatterns change, a multi-agent validation harness). Classification was accurate at plan time and stale by the end.

### Memory-Bank Corrections (from Guardrail Misses)

None, in the sense of guard FAILs: no guardrail misses were recorded this build.

Advisory items from the other findings, for a human or `/bmb:archive` to decide:

| File and section | Current | Suggested correction | Evidence |
|---|---|---|---|
| tasks/fitness-no-cross-module-imports.md (Implementation Notes) | "Slide 35 ... out of scope" | Annotate that the rule and systemPatterns entry were added after the user broadened the ask | Scope note, commits 8e19f136 and d1455527 |
| techContext.md (dev environment / Windows notes) | No mention of long paths | Document `git config core.longpaths true` and that harness worktree isolation is unusable on this repo as-is | Orphan `worktree-agent-*` branches |

### Suggested Improvements to Claude Code System

**High Priority**
1. Make harness `isolation: "worktree"` support sparse checkout, or fail fast with a clear error and no orphan branches. On a 43k-file repo it should not be the default path.
2. Have BMB doctor warn on Windows when `core.longpaths` is unset, and warn when `worktree_root` is inside a cloud-synced folder.

**Medium Priority**
1. Give validation scenario briefs a precondition step: verify that referenced fixtures (addons, files) exist at HEAD before dispatching agents.
2. Add an "adversarial validation" pattern for fitness functions to the build or verify docs: one scenario each for violation, compliant, evasion, false positives and config/CLI, followed by a corpus run on real code.

**Low Priority**
1. Offer a first-class `fitness` rule type that registers a script as a BLOCKING reviewer check, so the human-authored rule file does not have to be hand-wired.

---

## Key Learnings

### Extractable Learnings (for Continuous Learning)

- **testing-patterns** (`scripts/fitness/`, static-analysis gates): Validate any gate with independent adversarial agents (violation, compliant, evasion, false-positive, config/CLI scenarios) and a run over a large real corpus, because same-author unit tests miss gaps.
- **config-design** (`scripts/fitness/`, allow-lists): Make allow-list sources additive with an explicit opt-out; never let an env var or CLI flag silently replace the default exceptions.
- **tooling** (`git worktree`, Windows or OneDrive): On Windows set `core.longpaths true` before creating worktrees of large repos, and use detached sparse worktrees outside OneDrive for agent isolation.

### Learned Rules Applied

No learned rules were loaded for this task. Human-authored `agent-rules/odoo-fitness.md` was created by this task and exercised by the Code Reviewer, as described above.

### For Claude Code Workflow

1. Check the preconditions of every scenario in the orchestrator before fan-out. A shared bad assumption wastes N agents.
2. Level 1 tasks can quietly turn into Level 2-3 work. Revisit complexity when the scope broadens.

---

## Conclusion

The function does what it was asked to do, and the evidence is stronger than a unit-test suite alone would give. The independent validation caught six defects and one real-corpus false positive. The open items are narrow and named: CLI and config error paths, a bypassable pre-filter, and four plausible evasion variants. None blocks use as a reviewer-time gate, but the pre-filter docstring claim should be corrected.

**Overall Task Success**: Success, with known open follow-ups.

**Overall Workflow Effectiveness**: Moderately effective. The BMB rule-to-reviewer chain was strong. Harness worktree isolation on Windows with large repos was a significant friction point.

**Recommendation**: Ready to archive. Triage the D1-D3 and pre-filter follow-ups as a separate Level 1 task.
