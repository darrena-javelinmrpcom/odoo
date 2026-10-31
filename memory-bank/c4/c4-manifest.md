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
- **Last Run ID**: c4-20261031-k7m2
- **Last Run At**: 2026-10-31T12:00:00Z
- **Hash Strategy**: git-tree
- **Scope**: custom_addons (user-selected; full repo is ~3,800 source dirs of upstream Odoo 18.0, treated as platform)
- **Levels Built**: code,component,container,glossary,context
- **Last Completed Phase**: Annotation (Step 7) → manifest/index (Step 8)
- **IaC Adapters Used**: docker-compose, dockerfile (CI workflows: none)

## Counters

| Metric | Value |
|--------|-------|
| Directories walked this run | 5 |
| Directories reused from prior run | 0 |
| Directories archived this run | 0 |
| c4-code docs total | 5 |
| Components | 1 |
| Containers | 2 |
| IaC compute resources | 1 |
| IaC stateful resources | 1 |
| IaC messaging resources | 0 |
| IaC inferred containers (no backing) | 0 |
| Boundary resource types | 3 |
| Entities total | 1 |
| Entities persisted | 1 |
| Entities orphan (no container) | 1 |
| Lifecycle entries total | 0 |
| Lifecycle OWNS claims | 0 |
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
| sale-credit-limit-warning | code/c4-code-custom_addons-sale_credit_limit_warning.md; code/c4-code-custom_addons-sale_credit_limit_warning-models.md; code/c4-code-custom_addons-sale_credit_limit_warning-static-tests-tours.md; code/c4-code-custom_addons-sale_credit_limit_warning-tests.md; code/c4-code-custom_addons-sale_credit_limit_warning-views.md | (empty — no Lifecycle Signals in constituents) | 2026-10-31T12:00:00Z | up-to-date | [components/c4-component-sale-credit-limit-warning.md](components/c4-component-sale-credit-limit-warning.md) |

<!--
  Lifecycle Hash = sha256 of the concatenation of every constituent c4-code
  doc's Lifecycle Signals subsections (sorted by doc path), plus the per-entity
  USER-MANAGED `lifecycle-notes-*` block bodies preserved in the per-component
  doc (sorted by entity slug). When this hash is unchanged from the prior run
  AND every constituent code doc is up-to-date, the per-component lifecycle
  synthesis is skipped.

  Grouping rule (deterministic): one component per Odoo addon directory under
  custom_addons/ (the addon's root + all subdirectories).
-->

<!-- /AUTO-MANAGED: component-entries -->

## Container-Level Entries

<!-- AUTO-MANAGED: container-entries -->

| Container | Class | Primary IaC Resource | Image Trace | Components | Last Synthesized | Status | Doc |
|-----------|-------|---------------------|-------------|------------|------------------|--------|-----|
| Odoo Application Server | Compute | docker-compose.services.odoo | traced (Dockerfile) | sale-credit-limit-warning | 2026-10-31T12:00:00Z | up-to-date | [containers/c4-container-odoo-application-server.md](containers/c4-container-odoo-application-server.md) |
| PostgreSQL Database | Stateful | docker-compose.services.db | external (postgres:16) | (none) | 2026-10-31T12:00:00Z | up-to-date | [containers/c4-container-postgresql-database.md](containers/c4-container-postgresql-database.md) |

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
| 2026-10-31T12:00:00Z | 7577ff4695a34d5857845ae2a1885536bb2e13dc50d1ea03071eb657a31c2703 | 1 | 1 | 1 | none | COMPLETE (1 warning: SaleOrder has no container_hint) | [c4-entities.md](c4-entities.md) |

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
| Last run | 2026-10-31T12:00:00Z |
| Terms input hash | 21a0f04204ba6d3d0e37af2d42b68384086264bd87df37c43dcc3fca79a2dcc5 |
| Status | COMPLETE |
| Canonical count | 10 |
| Ambiguity count (pending) | 0 |
| Ambiguity count (ratified this run via carryover) | 0 |
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
| 2026-10-31T12:00:00Z | COMPLETE | [c4-context.md](c4-context.md) |

<!-- /AUTO-MANAGED: context-entry -->

## Tracked Input Hashes

<!-- AUTO-MANAGED: tracked-inputs -->

| Input | sha256 (first 16) | Affects |
|-------|-------------------|---------|
| memory-bank/productBrief.md | 17524a670078fc4e | Context |
| memory-bank/techContext.md | b22be0e9d1937203 | Container (hash taken after this run's annotation) |
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
