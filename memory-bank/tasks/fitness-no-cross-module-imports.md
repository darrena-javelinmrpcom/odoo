---
slug: fitness-no-cross-module-imports
legacy_id:
feature:
status: COMPLETE
---

# fitness-no-cross-module-imports: Fitness function for module isolation

**Complexity**: Level 1
**Status**: COMPLETE
**Archived**: memory-bank/archive/fitness-no-cross-module-imports-archive.md
**Completed**: 2026-11-03
**Latest Commit**: d4295c54
**Reflection**: memory-bank/reflection/fitness-no-cross-module-imports-reflection.md
**Roadmap**: N/A
**Branch**: task/fitness-no-cross-module-imports
**Worktree**: N/A (Level 1 uses direct branch, not worktree)

## Task Description

Author a fitness function for 'module isolation' (Week 5 workshop, slide 36).

**Principle**: custom addons (every addon under `custom_addons/`, i.e. any directory with a
`__manifest__.py`) MUST NOT directly import from another addon's Python modules.

- **Forbidden**: `from odoo.addons.<other_addon>.models.<thing> import <Class>`, also
  `import odoo.addons.<other>...` and `from odoo.addons import <other>`.
- **Correct**: `self.env['model.name']`.
- **Exception (allow-list)**: inside a `tests/` folder, importing another addon's test fixtures
  from `odoo.addons.<X>.tests.common` is allowed. (User decision, 2026-11-03: this is the
  standard Odoo way to reuse test fixtures.)

**Location**: `scripts/fitness/no-cross-module-imports.py`.

**Designed for the Code Reviewer to run on every build**:
- stdlib only; parses with `ast`, not regex
- deterministic, sorted output as `file:line: message`
- exit 0 clean / 1 violations / 2 usage error
- takes one or more paths (default `custom_addons/`)
- allow-list configurable without editing code

**Run and show output**: against `custom_addons/`, and against `addons/` for comparison.
Demonstrate the catch with a temporary scratch violation, then remove it (slide 37).

## Implementation Notes

- Slide deviation: the slide says `addons/banyan_*/`. In this repo `addons/` is Odoo core and
  custom addons live in `custom_addons/` (on `addons_path`), so the default scan is `custom_addons/`.
- Known existing import: `custom_addons/sale_credit_limit_warning/tests/test_credit_limit_warning.py:6`
  `from odoo.addons.sale.tests.common import TestSaleCommon`. It is allowed by the
  tests-fixture exception, so the expected result on `custom_addons/` is 0 violations.
- Relative imports (`from . import models`, `from ..models import x`) and an addon importing
  its own package (`odoo.addons.<self>...`) are allowed.
- Slide 35 also lists a systemPatterns ENFORCED entry and an `agent-rules/odoo-fitness.md`
  rule; those are out of scope here (slide 36 = the script only).

## Test Strategy
- New test file: `scripts/fitness/test_no_cross_module_imports.py` (stdlib `unittest`, temp-dir
  fixture addons). It covers: forbidden `from` / `import` / `from odoo.addons import x` forms,
  self-import allowed, relative imports allowed, tests.common allowed only under `tests/`,
  a custom allow-list, sorted output, exit codes 0/1/2, syntax-error files reported (not crashing).
- Run: `python -m unittest scripts/fitness/test_no_cross_module_imports.py`

---

## Execution State

**Build Status**: IDLE
**Current Phase**: COMPLETE
**Current Step**: Archive - COMPLETE
**Step Started**: 2026-11-03
**Can Resume**: NO

### Active Sub-Agents
(none)

### Completed Steps
- RED then GREEN: scripts/fitness/test_no_cross_module_imports.py, 18 tests, all passing; script scripts/fitness/no-cross-module-imports.py + .allow file created.
- Run a (custom_addons/): exit 0, 0 violations in 7 files. Run b (addons/, comparison): exit 1, 1108 violations in 7512 files (~19s). Run c (scratch violation in sale_credit_limit_warning/models): exit 1 with exactly 1 violation; after deleting scratch file: exit 0.
- 2026-11-03 isolated validation (5 sparse worktrees, scenarios A-E + Code Reviewer on A and B): A violation PASS (reviewer BLOCKING), B compliant PASS (reviewer APPROVE), D false positives PASS; C evasion FAIL 8/11, E allow-list partial. Gaps found: (1) `from odoo import addons` / `import odoo` attribute access, (2) `importlib.import_module` / `__import__`, (3) allow-listed imports passed silently, (4) no justification enforcement, (5) no JSON output, (6) `FITNESS_ALLOWLIST` / `--allow-file` replaced the default allow-list.
- Gap fixes: alias-tracked attribute chains, import_module/__import__ calls (literal and `+`-folded names; computed names flagged MODULE-ISOLATION-DYNAMIC; relative `level>=1` skipped), widened text pre-filter, ALLOWED lines with rule + justification, justification required (exit 2), `--format json`, additive allow sources + `--no-default-allow`. Tests: 39, all passing. custom_addons/: exit 0, 0 violations, 1 allowed (tests fixture). addons/ (comparison): 1138 violations, 664 allowed, 1 dynamic, 0 parse errors in 7512 files. Rule, allow file header and systemPatterns entry updated.
- Re-validation after gap fixes (fresh sparse worktrees): C evasion PASS (cases 1-11 all caught, benign file clean; 14 of 28 extra agent-invented variants missed: plausible = `getattr(odoo.addons, x)`, `sys.modules['odoo.addons.x']`, assigned alias `im = importlib.import_module`, load-by-path `spec_from_file_location`; rest deliberate obfuscation; text pre-filter bypassable by escapes like `\x61ddons`, so its "cannot contain a violation" docstring claim is false). E allow-list PASS on R1-R4 + 39 unit tests; new defects D1 (missing default .allow silently ignored), D2 (non-UTF-8 allow file -> traceback, exit 1 instead of 2), D3 (argparse errors with --format json leave stdout empty); weak: punctuation-only comment counts as justification. These are KNOWN OPEN follow-ups, not fixed in this task.
- Prerequisites verified for REFLECT (Level 1, no multi-phase roadmap; status BUILD_COMPLETE; branch not behind origin/banyan).
- Reflection Agent: COMPLETE (2026-11-03) - Output: memory-bank/reflection/fitness-no-cross-module-imports-reflection.md (Task Quality: Good; Ecosystem: Moderately effective)
- Archive: COMPLETE (2026-11-03) - memory-bank/archive/fitness-no-cross-module-imports-archive.md; learned rules added: _learned/fitness-functions.md, _learned/git-worktrees.md (additive, no merges/retirements)
