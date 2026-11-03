---
name: code-archaeology
description: "Audit a brownfield method for hidden invariants before anyone refactors it: surfaces the implicit contracts (sudo, company context, @api.depends, currency, state gates, boundaries, rollups, i18n, access control) a naive change would silently break, with file:line evidence and confidence ratings. Trigger on: 'audit X for invariants', 'what would break if I refactored X', 'knowledge archaeology', 'surface hidden contracts in X', 'what are the implicit rules in X', 'is it safe to change X'."
---

# Code Archaeology Audit

Read-only analysis that turns a method's tacit knowledge into an explicit, verifiable list of
invariants. The output feeds characterization tests and `systemPatterns.md` ENFORCED entries.

## When to use

- A brownfield method (Odoo core or a custom addon) is about to be refactored, overridden, or
  extended, and nobody can say for sure what it guarantees.
- Before writing characterization tests: the audit tells you which behaviors to lock.
- Before proposing a fitness function or ENFORCED rule for an area of the code.

**Not for:** greenfield code you are writing now, pure style review, or bug hunting. Latent defects
get noted, not fixed.

## The Audit Prompt: Four Parts

Fill in all four. If the user's request leaves one blank, infer it from context and state the
assumption at the top of the output.

1. **Target**: the method(s) under audit as `model._method` plus `path:start-end`, and any
   callee that carries the logic (for example a `_build_*` helper on another model). Read the
   supporting code as well: field definitions, overrides in other addons, views that bind the field,
   existing tests, and every call site in `custom_addons/`. The invariants often live there.
2. **What to surface**: every implicit invariant a naive refactor might silently break. For
   each one: name, `file:line`, what breaks if it is dropped, and confidence (HIGH / MED / LOW).
3. **Output format**: the four sections under *Output Format* below, in that order.
4. **Constraints**: see *Constraints*. Analysis only.

## Invariant Categories

Sweep every category. If one doesn't apply, say "none found" and give the reason in a line. Don't
skip it silently.

| # | Category | Look for |
|---|----------|----------|
| A | `sudo` / ACL | What the sudo widens past record rules; which record gets sudo'd vs. `self`; info disclosure that is intended vs. accidental |
| B | `with_company` / `with_context` | Effective company (`env.company` vs `record.company_id`); context keys read downstream; feature gates checked in which company |
| C | `@api.depends` / ORM cache | Missing or over-broad depends; `depends_context`; reset-before-compute; batch vs per-record recompute |
| D | Discarded-return idioms | Calls made for side effects, `ensure_one()` used as an assertion, `filtered()` results thrown away |
| E | Multi-record vs singleton contracts | Batch-safe compute vs singleton helper; N+1 calls; `self` model-level vs record-level |
| F | Currency | Company vs document currency; rate date; rounding (`float_compare` vs raw `>`); tax-inclusive vs untaxed mixes; division by a rate |
| G | State-machine gates | Which `state` / `move_type` values enable the logic; reset paths for cancelled or locked records |
| H | Boundary conditions | `0` as a sentinel ("no limit"), `>` vs `>=`, negative values netting off, empty recordsets |
| I | Field rollups | `commercial_partner_id` vs `partner_id` vs `partner_invoice_id`; which key each figure uses |
| J | i18n | `_()` lexical module resolution; separate msgids joined together; named placeholders with pre-formatted values |
| K | Return-value / view coupling | Empty string vs `False`; views that use `invisible="not field"`; consumers in other addons |

## Output Format

Write the audit to `memory-bank/creative/<task-slug>-knowledge-archaeology.md` when you're inside a
BMB task. Otherwise return it inline. Start with a header that gives the target, Odoo version, date,
and the supporting files read. Then add:

### 1. Real Invariants
Group by category letter (A1, A2, B1 ...). Each entry: **name**, `file:line`, the guarantee in one
sentence, *what breaks if dropped* (a concrete failure, not "may cause issues"), and confidence.
**Aim for 15 invariants.** Fewer than 10 means the sweep was too shallow. Go back to the supporting code.

### 2. Looks Like an Invariant But Isn't
Calibration. These are things a reader would assume are load-bearing but aren't, each with the evidence
that shows it's incidental. **Minimum 3 entries; aim for 5.** This section is what makes the HIGH
ratings in §1 believable.

### 3. Can't Verify
Claims you suspect but couldn't confirm from source alone: runtime config, data-dependent behavior,
upstream intent. Give each the experiment or test that would settle it. Also list latent defects you
noticed here, marked *not fixed*.

### 4. Recommended ENFORCED Entries
Proposed bullets for `systemPatterns.md` § ENFORCED. Each one should be testable and name the
invariant IDs it protects. Flag any that could become a fitness-function script under
`scripts/fitness/`. **Aim for 6–12 ENFORCED entries.**

## Constraints

- **Do not refactor or edit code.** Analysis only. The deliverable is the document.
- **Cite source, not memory.** Every invariant needs a `file:line` you actually read in this
  session. If you can't cite it, it goes in §3.
- **Don't read `memory-bank/agent-rules/_learned/`** unless the user asks. The audit should come
  from the code, not from earlier conclusions.
- **Don't apply the ENFORCED entries.** `systemPatterns.md` is Core State and goes through
  `chore/banyan-admin`. Propose them; a human applies them.
- **Verify before claiming HIGH.** For each §4 entry, re-read the cited lines (or dispatch one
  independent sub-agent per entry that reads only source, never Markdown) and record upheld or
  refuted. Downgrade or withdraw anything refuted.
- Write for a senior Odoo developer: be terse, give no ORM tutorials, and explain the *why*.

## After the audit

Suggested next steps:
1. Lock the HIGH invariants with characterization tests (`custom_addons/<addon>/tests/`).
2. Promote the scriptable ENFORCED entries into `scripts/fitness/` plus an `agent-rules/` file.
