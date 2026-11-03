---
name: Odoo Fitness Functions
globs: ["custom_addons/**/*.py"]
paths: ["custom_addons/", "scripts/fitness/"]
topics: ["odoo", "fitness-function", "module-isolation", "code-review", "architecture"]
priority: high
---

# Odoo Fitness Functions (human-authored)

ENFORCED constraints from `memory-bank/systemPatterns.md` § Fitness Functions. Each one is a
script, and a non-zero exit is a contract violation, not a style note.

## Code Reviewer: run on every build

When the change touches anything under `custom_addons/` (or `scripts/fitness/`), run:

```
python scripts/fitness/no-cross-module-imports.py custom_addons/
```

- Always scan **all of `custom_addons/`**, not only the files in the diff. A cross-module import
  added in an earlier change still has to surface.
- **Exit 1** → report every printed `MODULE-ISOLATION`, `MODULE-ISOLATION-DYNAMIC` and
  `MODULE-ISOLATION-ERROR` line as a **BLOCKING** finding, with its `file:line`. The fix is
  `self.env['model.name']` (or an `_inherit` extension), not a direct
  `from odoo.addons.<other>... import ...`, an `odoo.addons.<other>` attribute reach, or an
  `importlib` / `__import__` call.
- **Exit 2** → usage or allow-list error (including an allow rule without a justification
  comment). Report it as BLOCKING; the check did not run.
- **Exit 0** → note "module isolation: clean" in the review.
- **`ALLOWED` lines** are allow-listed imports. They don't fail the run, but if the diff adds or
  changes an allow rule, list the new `ALLOWED` lines and their justification in the review so a
  human signs off.
- `--format json` gives the same result as one JSON document (`exit_code`, `files_scanned`,
  `violations`, `allowed`).
- Never treat a skipped run as a pass. If the script cannot run, say so explicitly.

## Implementing agents (TDD / build)

- Don't import another addon's Python modules from a custom addon. Reach other models with
  `self.env['model.name']`, and extend them with `_inherit`.
- Allowed: relative imports inside the addon, `odoo.addons.<own_addon>...`, and test fixtures
  `odoo.addons.<X>.tests.common` from inside `tests/`.
- **Do not edit `scripts/fitness/no-cross-module-imports.allow` to make a violation pass.** Fix
  the import. A justified exception needs a comment and reviewer sign-off in the PR.
