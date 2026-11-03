---
slug: fitness-no-cross-module-imports
legacy_id:
feature:
status: BUILD_COMPLETE
---

# fitness-no-cross-module-imports: Fitness function for module isolation

**Complexity**: Level 1
**Status**: BUILD_COMPLETE
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

**Build Status**: BUILD_COMPLETE
**Current Phase**: BUILD_COMPLETE
**Can Resume**: NO

### Active Sub-Agents
(none)

### Completed Steps
- RED then GREEN: scripts/fitness/test_no_cross_module_imports.py, 18 tests, all passing; script scripts/fitness/no-cross-module-imports.py + .allow file created.
- Run a (custom_addons/): exit 0, 0 violations in 7 files. Run b (addons/, comparison): exit 1, 1108 violations in 7512 files (~19s). Run c (scratch violation in sale_credit_limit_warning/models): exit 1 with exactly 1 violation; after deleting scratch file: exit 0.
