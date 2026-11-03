# Agent Rules Index

Generated: 2026-11-03T16:20:00Z
Indexed: 3 rules (1 human-authored, 2 learned) | Rejected: 0 (unsafe) | Warnings: 0

## Validation Summary

### Health Check
- Total rules: 3
- Human-authored rules: 1
- Learned rules (auto-generated): 2
- Estimated max context: ~70 lines (OK). Worst case is a `custom_addons/**/tests/test_*e2e*.py` file, which matches all three rules.
- Conflicts detected: 0. `odoo-fitness.md` and `_learned/odoo-compute-fields.md` share the glob `custom_addons/**/*.py` but their instructions don't overlap (they add to each other).

### ⚠️ Warnings
(none)

### 🚫 Rejected Rules (Unsafe)
(none)

---

## Rules by File Pattern

| Pattern | Rule | Priority | Lines |
|---------|------|----------|-------|
| `custom_addons/**/*.py` | [odoo-fitness.md](agent-rules/odoo-fitness.md) | high | 38 |
| `custom_addons/**/*.py` | [odoo-compute-fields.md](agent-rules/_learned/odoo-compute-fields.md) (learned) | low | 16 |
| `**/tests/tours/*.js` | [e2e-testing.md](agent-rules/_learned/e2e-testing.md) (learned) | low | 16 |
| `**/tests/test_*e2e*.py` | [e2e-testing.md](agent-rules/_learned/e2e-testing.md) (learned) | low | 16 |
| `*.test.*` | [e2e-testing.md](agent-rules/_learned/e2e-testing.md) (learned) | low | 16 |

## Rules by Path

| Path Contains | Rule | Priority | Lines |
|---------------|------|----------|-------|
| `custom_addons/` | [odoo-fitness.md](agent-rules/odoo-fitness.md) | high | 38 |
| `scripts/fitness/` | [odoo-fitness.md](agent-rules/odoo-fitness.md) | high | 38 |
| `custom_addons/` | [odoo-compute-fields.md](agent-rules/_learned/odoo-compute-fields.md) (learned) | low | 16 |
| `custom_addons/` | [e2e-testing.md](agent-rules/_learned/e2e-testing.md) (learned) | low | 16 |

## Rules by Topic

| Keywords | Rule | Priority |
|----------|------|----------|
| odoo, fitness-function, module-isolation, code-review, architecture | [odoo-fitness.md](agent-rules/odoo-fitness.md) | high |
| odoo, orm, compute-fields, testing | [odoo-compute-fields.md](agent-rules/_learned/odoo-compute-fields.md) (learned) | low |
| e2e, testing, uat, odoo-tours | [e2e-testing.md](agent-rules/_learned/e2e-testing.md) (learned) | low |

---

## Conflict Resolutions

| Topic | Winner | Overrides |
|-------|--------|-----------|
| (none) | | |

**Note:** `_learned/odoo-testing.md` (from `author-characterization-tests-partner-credit-warning`, PR #3)
isn't on this branch yet. Re-run `/bmb:rules-index` once PR #3 and this branch are both merged.
