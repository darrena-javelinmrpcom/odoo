# Archive: Fitness function for module isolation

## Metadata
- Task: fitness-no-cross-module-imports
- Complexity: Level 1
- Completed: 2026-11-03
- Branch: task/fitness-no-cross-module-imports
- Reflection: memory-bank/reflection/fitness-no-cross-module-imports-reflection.md

## Summary
An executable check that custom Odoo addons never import another addon's Python code (the
correct route is `self.env['model.name']`), wired to the Code Reviewer as a BLOCKING check on
every build, and validated by independent agents in isolated worktrees.

## Solution
- `scripts/fitness/no-cross-module-imports.py`: stdlib, `ast`-based. Catches import statements at
  any nesting, `odoo.addons.<x>` reached through `import odoo` / `from odoo import addons`
  aliases, and `importlib.import_module` / `__import__` (literal or `+`-folded names; computed
  names flagged `MODULE-ISOLATION-DYNAMIC`). Exit 0 clean / 1 violations / 2 usage error.
  `--format json`. Default scan `custom_addons/`.
- Allow-list `scripts/fitness/no-cross-module-imports.allow`: every rule needs a justification;
  allow-listed hits are reported as `ALLOWED`; extra sources (env, `--allow-file`, `--allow`) add
  to the default. Default rule: `tests/**: odoo.addons.*.tests.common`.
- `memory-bank/agent-rules/odoo-fitness.md` (high, human-authored): the Code Reviewer runs the
  script over all of `custom_addons/` and treats non-zero exit as BLOCKING. Indexed in
  `agent-rules-index.md`. `systemPatterns.md` lists module isolation as ENFORCED.
- Validation: 5 scenario agents in sparse worktrees + the Code Reviewer on two diffs. Found 6 gaps
  (all fixed in 9be5ca73) and a real-corpus false positive (fixed). Re-run: evasion and
  allow-list scenarios pass. 39 unit tests.

## Files Changed
- `scripts/fitness/no-cross-module-imports.py` - the fitness function
- `scripts/fitness/no-cross-module-imports.allow` - allow-list with justified default rule
- `scripts/fitness/test_no_cross_module_imports.py` - 39 unittest cases
- `memory-bank/agent-rules/odoo-fitness.md` - Code Reviewer wiring (BLOCKING)
- `memory-bank/systemPatterns.md` - Fitness Functions table (module isolation ENFORCED)
- `memory-bank/agent-rules-index.md` - index
- `memory-bank/agent-rules/_learned/fitness-functions.md`, `git-worktrees.md` - new learned rules

## Results
- `custom_addons/`: 0 violations, 1 allowed (tests fixture).
- `addons/` (Odoo core, comparison only): 1138 violations, 664 allowed, 1 dynamic, 0 parse errors in 7512 files.

## Known open follow-ups (candidate Level 1 task)
- D1: missing default `.allow` is silently ignored.
- D2: non-UTF-8 allow file -> traceback and exit 1 (should be exit 2).
- D3: argparse errors with `--format json` leave stdout empty.
- Punctuation-only comments count as a justification.
- Text pre-filter is bypassable (e.g. `\x61ddons`); the docstring claim that skipped files cannot contain a violation is false.
- Plausible evasions not yet caught: `getattr(odoo.addons, x)`, `sys.modules['odoo.addons.x']`,
  `im = importlib.import_module` aliasing, loading by path via `spec_from_file_location`.

## Notes
- The workshop slide named `addons/banyan_*/`; in this repo custom addons live in `custom_addons/`.
- Harness `isolation: "worktree"` fails here without `core.longpaths true` (now set repo-locally).
