# C4 Manifest

<!--
  This file is the source of truth for /bmb:c4 idempotency. It tracks every
  source directory the c4-code agent has walked, along with a content hash and
  a pointer to its generated doc. The orchestrator reads this file on every run
  to decide which subtrees to re-walk.

  Hash semantics:
  - `content_hash` is sha-256 of the directory's file inventory line
    (relative file path + size + mtime, sorted) for files matching the include
    patterns. It is NOT a hash of file contents — that would be too expensive
    on large codebases. The included-files signature is sufficient to detect
    add/remove/modify events.
  - When a project is in a git repo with a clean working tree, the orchestrator
    MAY substitute the directory's git tree hash (`git ls-tree -r <commit> -- <dir>`)
    for a more deterministic signature. The chosen strategy is recorded in
    `hash_strategy` for each entry. (Hashes below are the first 16 hex chars of
    sha256(`git ls-tree -r HEAD -- <dir>`).)

  Status semantics:
  - `up-to-date`: hash matches; doc exists; skip on next run
  - `dirty`: hash mismatched; queued for re-walk
  - `new`: directory discovered this run, no prior doc
  - `archived`: directory no longer exists in the source tree; doc moved to
    `archive/` for historical reference
-->

## Run Metadata

- **Plugin Version**: 2.2.1
- **Last Run ID**: c4-20261101-s4l3 (previous: c4-20261031-k7m2)
- **Last Run At**: 2026-11-01T11:22:58Z
- **Hash Strategy**: git-tree
- **Scope**: custom_addons + addons/sale (this run: `--scope addons/sale`, incremental on the custom_addons baseline; the rest of upstream Odoo 18.0, ~3,800 source dirs, is treated as platform)
- **Levels Built**: code,component,container,glossary,context
- **Last Completed Phase**: manifest/index (Step 8) — backlink (8c) + verify (8.5) follow
- **IaC Adapters Used**: docker-compose, dockerfile (CI workflows: none)
- **Approval Mode**: accept-all (user-approved mid-run); WROTE_WITH_OVERRIDES: containers/c4-container-odoo-application-server.md (1 material alteration); glossary COMPLETE_WITH_OVERRIDES (1 ambiguity auto-accepted)

## Counters

| Metric | Value |
|--------|-------|
| Directories walked this run | 28 |
| Directories reused from prior run | 5 |
| Directories archived this run | 0 |
| c4-code docs total | 33 |
| Components | 2 |
| Containers | 2 |
| IaC compute resources | 1 |
| IaC stateful resources | 1 |
| IaC messaging resources | 0 |
| IaC inferred containers (no backing) | 0 |
| Boundary resource types | 3 |
| Entities total | 4 |
| Entities persisted | 4 |
| Entities orphan (no container) | 0 |
| Lifecycle entries total | 1 |
| Lifecycle OWNS claims | 1 |
| Lifecycle CONTRIBUTES claims | 0 |
| Lifecycle CONSUMES claims | 0 |
| Lifecycle conflicts (CONFLICT severity) | 0 |
| Lifecycle orphans (writers but no OWNS) | 0 |
| Lifecycle leaks (CONSUMES claim but writes found) | 0 |
| Image-trace: traced | 1 |
| Image-trace: external | 1 |
| Image-trace: untraceable | 0 |

## Excluded Patterns

The following patterns are excluded from C4 walks (configurable via `/bmb:c4 --exclude <pattern>`):

```
node_modules/
.git/
.venv/
venv/
__pycache__/
build/
dist/
out/
target/
.next/
.nuxt/
coverage/
.cache/
vendor/
```

Include patterns this run: `*.py`, `*.js`, `*.xml`, `*.csv` (Odoo addon: models, OWL/JS tours, XML views/data, access CSVs).

## Code-Level Entries

<!-- AUTO-MANAGED: code-entries -->

| Directory | Hash Strategy | Content Hash | Last Walked | Status | Doc |
|-----------|--------------|--------------|-------------|--------|-----|
| addons/sale | git-tree | 3da2ff385548fd85 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale.md](code/c4-code-addons-sale.md) |
| addons/sale/controllers | git-tree | ba9c7ef2025a3df0 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-controllers.md](code/c4-code-addons-sale-controllers.md) |
| addons/sale/data | git-tree | 5bd511e84c04bbf7 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-data.md](code/c4-code-addons-sale-data.md) |
| addons/sale/models | git-tree | 99548521fdbd136b | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-models.md](code/c4-code-addons-sale-models.md) |
| addons/sale/report | git-tree | 07f381479d604b68 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-report.md](code/c4-code-addons-sale-report.md) |
| addons/sale/security | git-tree | efba957c9aaee81f | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-security.md](code/c4-code-addons-sale-security.md) |
| addons/sale/static/src/js | git-tree | e4f9e78c80600c53 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-src-js.md](code/c4-code-addons-sale-static-src-js.md) |
| addons/sale/static/src/js/badge_extra_price | git-tree | c33875c41160f345 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-src-js-badge_extra_price.md](code/c4-code-addons-sale-static-src-js-badge_extra_price.md) |
| addons/sale/static/src/js/combo_configurator_dialog | git-tree | f41ab2166989524f | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-src-js-combo_configurator_dialog.md](code/c4-code-addons-sale-static-src-js-combo_configurator_dialog.md) |
| addons/sale/static/src/js/models | git-tree | b52af28105bfed26 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-src-js-models.md](code/c4-code-addons-sale-static-src-js-models.md) |
| addons/sale/static/src/js/product | git-tree | 7fbb23a0f969aae7 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-src-js-product.md](code/c4-code-addons-sale-static-src-js-product.md) |
| addons/sale/static/src/js/product_card | git-tree | c75cdd5e50609366 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-src-js-product_card.md](code/c4-code-addons-sale-static-src-js-product_card.md) |
| addons/sale/static/src/js/product_configurator_dialog | git-tree | e187a2c406377efd | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-src-js-product_configurator_dialog.md](code/c4-code-addons-sale-static-src-js-product_configurator_dialog.md) |
| addons/sale/static/src/js/product_list | git-tree | fc87230f3f5a3cb7 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-src-js-product_list.md](code/c4-code-addons-sale-static-src-js-product_list.md) |
| addons/sale/static/src/js/product_template_attribute_line | git-tree | 2fce1304554e9595 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-src-js-product_template_attribute_line.md](code/c4-code-addons-sale-static-src-js-product_template_attribute_line.md) |
| addons/sale/static/src/js/quantity_buttons | git-tree | 07406e944b3e776e | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-src-js-quantity_buttons.md](code/c4-code-addons-sale-static-src-js-quantity_buttons.md) |
| addons/sale/static/src/js/sale_action_helper | git-tree | b65b187228d6be69 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-src-js-sale_action_helper.md](code/c4-code-addons-sale-static-src-js-sale_action_helper.md) |
| addons/sale/static/src/js/sale_order_line_field | git-tree | 98436806af1ae711 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-src-js-sale_order_line_field.md](code/c4-code-addons-sale-static-src-js-sale_order_line_field.md) |
| addons/sale/static/src/js/tours | git-tree | 2e1e074e23876dd5 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-src-js-tours.md](code/c4-code-addons-sale-static-src-js-tours.md) |
| addons/sale/static/src/views/sale_onboarding_kanban | git-tree | 2fb0f8ef7a1d8f09 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-src-views-sale_onboarding_kanban.md](code/c4-code-addons-sale-static-src-views-sale_onboarding_kanban.md) |
| addons/sale/static/src/views/sale_onboarding_list | git-tree | afb94ccf0e1cd65c | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-src-views-sale_onboarding_list.md](code/c4-code-addons-sale-static-src-views-sale_onboarding_list.md) |
| addons/sale/static/src/xml | git-tree | f7c8b32ccd7148f4 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-src-xml.md](code/c4-code-addons-sale-static-src-xml.md) |
| addons/sale/static/tests | git-tree | d6dd25c43c64bf32 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-tests.md](code/c4-code-addons-sale-static-tests.md) |
| addons/sale/static/tests/mock_server/mock_models | git-tree | 2739b72a91bb84d7 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-tests-mock_server-mock_models.md](code/c4-code-addons-sale-static-tests-mock_server-mock_models.md) |
| addons/sale/static/tests/tours | git-tree | af45800f074ba3c3 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-static-tests-tours.md](code/c4-code-addons-sale-static-tests-tours.md) |
| addons/sale/tests | git-tree | 890ba7843757feab | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-tests.md](code/c4-code-addons-sale-tests.md) |
| addons/sale/views | git-tree | de64ced4d34e2023 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-views.md](code/c4-code-addons-sale-views.md) |
| addons/sale/wizard | git-tree | b317ea138901ab00 | 2026-11-01T11:22:58Z | up-to-date | [code/c4-code-addons-sale-wizard.md](code/c4-code-addons-sale-wizard.md) |
| custom_addons/sale_credit_limit_warning | git-tree | 045b2f687b757f64 | 2026-10-31T12:00:00Z | up-to-date | [code/c4-code-custom_addons-sale_credit_limit_warning.md](code/c4-code-custom_addons-sale_credit_limit_warning.md) |
| custom_addons/sale_credit_limit_warning/models | git-tree | e8b3f8af4e4cfe4f | 2026-10-31T12:00:00Z | up-to-date | [code/c4-code-custom_addons-sale_credit_limit_warning-models.md](code/c4-code-custom_addons-sale_credit_limit_warning-models.md) |
| custom_addons/sale_credit_limit_warning/static/tests/tours | git-tree | 955c3b845feac20e | 2026-10-31T12:00:00Z | up-to-date | [code/c4-code-custom_addons-sale_credit_limit_warning-static-tests-tours.md](code/c4-code-custom_addons-sale_credit_limit_warning-static-tests-tours.md) |
| custom_addons/sale_credit_limit_warning/tests | git-tree | 6885b89b5c53544f | 2026-10-31T12:00:00Z | up-to-date | [code/c4-code-custom_addons-sale_credit_limit_warning-tests.md](code/c4-code-custom_addons-sale_credit_limit_warning-tests.md) |
| custom_addons/sale_credit_limit_warning/views | git-tree | 8a3d097e3abde865 | 2026-10-31T12:00:00Z | up-to-date | [code/c4-code-custom_addons-sale_credit_limit_warning-views.md](code/c4-code-custom_addons-sale_credit_limit_warning-views.md) |

<!-- /AUTO-MANAGED: code-entries -->

## Component-Level Entries

<!-- AUTO-MANAGED: component-entries -->

| Component | Constituent Code Docs | Lifecycle Hash | Last Synthesized | Status | Doc |
|-----------|----------------------|----------------|------------------|--------|-----|
| sale | 28 docs: code/c4-code-addons-sale*.md (every Code-Level Entry under addons/sale) | sale.order lifecycle (OWNS; 5 transitions) — recompute on next run | 2026-11-01T11:22:58Z | up-to-date | [components/c4-component-sale.md](components/c4-component-sale.md) |
| sale-credit-limit-warning | code/c4-code-custom_addons-sale_credit_limit_warning.md; code/c4-code-custom_addons-sale_credit_limit_warning-models.md; code/c4-code-custom_addons-sale_credit_limit_warning-static-tests-tours.md; code/c4-code-custom_addons-sale_credit_limit_warning-tests.md; code/c4-code-custom_addons-sale_credit_limit_warning-views.md | (empty — no Lifecycle Signals in constituents) | 2026-10-31T12:00:00Z | up-to-date | [components/c4-component-sale-credit-limit-warning.md](components/c4-component-sale-credit-limit-warning.md) |

<!--
  Lifecycle Hash = sha256 of the concatenation of every constituent c4-code
  doc's Lifecycle Signals subsections (sorted by doc path), plus the per-entity
  USER-MANAGED `lifecycle-notes-*` block bodies preserved in the per-component
  doc (sorted by entity slug). When this hash is unchanged from the prior run
  AND every constituent code doc is up-to-date, the per-component lifecycle
  synthesis is skipped.

  Grouping rule (deterministic): one component per Odoo addon directory under
  custom_addons/ or addons/ (the addon's root + all subdirectories).
-->

<!-- /AUTO-MANAGED: component-entries -->

## Container-Level Entries

<!-- AUTO-MANAGED: container-entries -->

| Container | Class | Primary IaC Resource | Image Trace | Components | Last Synthesized | Status | Doc |
|-----------|-------|---------------------|-------------|------------|------------------|--------|-----|
| Odoo Application Server | Compute | docker-compose.services.odoo | traced (Dockerfile) | sale, sale-credit-limit-warning | 2026-11-01T11:22:58Z | up-to-date (WROTE_WITH_OVERRIDES) | [containers/c4-container-odoo-application-server.md](containers/c4-container-odoo-application-server.md) |
| PostgreSQL Database | Stateful | docker-compose.services.db | external (postgres:16) | (none) | 2026-11-01T11:22:58Z | up-to-date | [containers/c4-container-postgresql-database.md](containers/c4-container-postgresql-database.md) |

<!-- /AUTO-MANAGED: container-entries -->

## Entity-Aggregation Entry

<!--
  AUTO-MANAGED by the orchestrator after Step 5b.5 (entity aggregation).
  Records the last run of the c4-entity-aggregator agent and the input
  hash that gates re-dispatch. When the input_hash matches the prior
  run's value AND c4-entities.md exists, Step 5b.5 is skipped.

  input_hash = sha256(
    sorted(c4-code Entities sections) ⊕
    sorted(container inventory rows: resource_id + class) ⊕
    sorted(USER-MANAGED data-classification-overrides blocks)
  )
-->

<!-- AUTO-MANAGED: entity-aggregation-entry -->

| Last Run | Input Hash | Entities Total | Persisted | Orphan | Compliance Scope | Status | Doc |
|----------|-----------|---------------:|----------:|-------:|------------------|--------|-----|
| 2026-11-01T11:22:58Z | 20dd298337ecae706e1dbbf0b71d6582d9688cf291504f04274832e0d8917652 | 4 | 4 | 0 | GDPR, CCPA | COMPLETE (4 warnings, see Coverage Notes) | [c4-entities.md](c4-entities.md) |

<!-- /AUTO-MANAGED: entity-aggregation-entry -->

## Glossary Entry

<!--
  AUTO-MANAGED by the orchestrator after Step 5b.7 (glossary aggregation).
  Records the last run of the c4-glossary-aggregator agent and the input
  hash that gates re-dispatch. When the terms_input_hash matches the prior
  run's value AND c4-glossary.md exists AND --refresh-from is not
  `glossary | component | code`, Step 5b.7 is skipped.

  terms_input_hash = sha256(
    sorted(c4-code-*.md Terms sections) ⊕
    sorted(c4-component-*.md Glossary sections, including USER-MANAGED
           bounded-context-exclusivity blocks)
  )
-->

<!-- AUTO-MANAGED: glossary-entry -->

| Field | Value |
|---|---|
| Last run | 2026-11-01T11:22:58Z |
| Terms input hash | 12b0e43ec8fafd29e6d5329150c68a9805aad43eecf170935bc23ef805f9fa07 |
| Status | COMPLETE_WITH_OVERRIDES |
| Canonical count | 220 |
| Ambiguity count (pending) | 0 |
| Ambiguity count (ratified this run via carryover) | 0 |
| Ambiguity count (auto-accepted this run, accept-all) | 1 (is_configurable / is_configurable_product → is_configurable) |
| Bounded-context exclusions | 0 |
| USER-MANAGED decisions carried over | 0 |
| Doc path | memory-bank/c4/c4-glossary.md |

<!-- /AUTO-MANAGED: glossary-entry -->

## Infrastructure Resources (IaC Inventory)

<!--
  AUTO-MANAGED: produced by the c4-container agent's master pass and persisted
  by the orchestrator. The c4-verifier (iac mode) re-walks IaC files independently
  and cross-checks against this list — discrepancies surface as INVENTORY_DRIFT.

  Compute / Stateful / Messaging classifications follow the taxonomy in
  ${CLAUDE_PLUGIN_ROOT}/context/c4-iac-adapters.md.
-->

<!-- AUTO-MANAGED: iac-inventory -->

| Resource ID | Type | Class | IaC Source | Image / Runtime | Maps to Container | Status |
|-------------|------|-------|-----------|-----------------|-------------------|--------|
| docker-compose.services.odoo | Compose service | Compute | docker-compose.yml:11 (secondary: Dockerfile:1, docker/odoo.conf, volume odoo-filestore) | build `.` / `Dockerfile` → traced; Python 3.12 (python:3.12-slim) + Odoo 18.0; port 8069 published | odoo-application-server | active |
| docker-compose.services.db | Compose service | Stateful | docker-compose.yml:2 (secondary: volume pg-data) | `postgres:16` → external; port 5432 internal only | postgresql-database | active |

<!-- /AUTO-MANAGED: iac-inventory -->

## Pending Approvals

<!--
  Files where the c4-container or c4-context agent's regeneration would have
  removed or materially altered existing entries, and either (a) the user
  deferred a decision, or (b) /bmb:c4 ran with --reject-all.

  The .proposed.md and .pending-approval.md files persist on disk until the
  user reconciles them manually (or reruns with --accept-all to override).

  Empty when no approvals are pending.
-->

<!-- AUTO-MANAGED: pending-approvals -->

| File | Proposed Content | Diff Report | Removals | Material Alterations | Reason |
|------|-----------------|-------------|---------:|---------------------:|--------|
| (none) | | | | | |

<!-- /AUTO-MANAGED: pending-approvals -->

## Boundary Infrastructure

<!--
  Non-container IaC resources counted at synthesis time. Informational; not
  used for verification gates. Useful for tracking the operational/security
  surface that surrounds the C4 containers.
-->

<!-- AUTO-MANAGED: boundary-infra -->

| Resource Type | Count | IaC Sources | Note |
|---------------|-------|-------------|------|
| Compose named volume | 2 | docker-compose.yml:41-42 (`pg-data`, `odoo-filestore`) | Persistent DB data + Odoo filestore |
| Compose config mount | 1 | docker/odoo.conf | Contains plaintext dev credentials (values not recorded) |
| Compose published port | 1 | docker-compose.yml:17 (8069) | Plain HTTP; no TLS proxy |

<!-- /AUTO-MANAGED: boundary-infra -->

## Context Entry

<!-- AUTO-MANAGED: context-entry -->

| Last Synthesized | Status | Doc |
|------------------|--------|-----|
| 2026-11-01T11:22:58Z | COMPLETE | [c4-context.md](c4-context.md) |

<!-- /AUTO-MANAGED: context-entry -->

## Tracked Input Hashes

<!-- AUTO-MANAGED: tracked-inputs -->

| Input | sha256 (first 16) | Affects |
|-------|-------------------|---------|
| memory-bank/productBrief.md | 17524a670078fc4e | Context |
| memory-bank/techContext.md | 2d3098e986b3d3f5 | Container (hash taken after this run's annotation) |
| Dockerfile | 1eee44f349f32756 | Container + IaC Inventory |
| docker-compose.yml | c613576647ecca9f | Container + IaC Inventory |
| docker/odoo.conf | 941e8e4a7683adeb | Container + IaC Inventory |

<!-- /AUTO-MANAGED: tracked-inputs -->

## Inputs Tracked for Higher-Level Refresh

When any of the following inputs change, the orchestrator marks the corresponding higher-level doc as `dirty`:

| Input | Affects | Reason |
|-------|---------|--------|
| `memory-bank/productBrief.md` (personas, NFRs) | Context | Personas drive context-level diagrams |
| **All IaC files** (per the adapter glob in `${CLAUDE_PLUGIN_ROOT}/context/c4-iac-adapters.md`) | Container + IaC Inventory | Container topology = IaC inventory; any IaC change can add/remove/rename containers |
| `memory-bank/techContext.md` (component structure) | Container | Tech-stack mapping |
| Any constituent code-level entry | Component | Component is a synthesis of its code docs |
| Any constituent component | Container | Container groups components (and their per-component "Likely deployment" hints feed inferred-container detection) |
| Any constituent c4-code Entities section | Entity-Aggregation Entry | Entity rollup is regenerated when any source entity changes |
| Container inventory (resource_ids) | Entity-Aggregation Entry | Container_hint resolution depends on canonical inventory |
| Any constituent c4-code Lifecycle Signals subsection | Component (Entity Lifecycles) | Per-component lifecycle synthesis is regenerated when any source lifecycle signal changes |
| Any per-component Entity Lifecycles claim | Component master-index (cross-component-lifecycle-conflicts blocks) + verifier (lifecycle pass) | Cross-component reconciliation depends on the union of all per-component claims |
