# System Patterns

Odoo **18.0 Community** (LGPL-3) fork. 621 addon directories under `addons/`; framework core under `odoo/`. Fork-specific additions are limited to `Dockerfile`, `docker-compose.yml`, `docker/odoo.conf`, and the custom addons under `custom_addons/`. First custom addon is live: `custom_addons/sale_credit_limit_warning/`.

## Guiding Principles

| Principle | Rule / Evidence |
|---|---|
| Never modify core | Don't edit `odoo/` or `addons/*`. Extend via `_inherit` (models), `inherit_id` + `<xpath>` (views), asset patching (JS) in a separate custom module — keeps upstream merges clean. |
| Declare every dependency | `__manifest__.py` `depends` (e.g. sale: `['sales_team','account_payment','utm']`); load order from the dependency graph (`odoo/modules/graph.py`). |
| Every model gets access rights | `security/ir.model.access.csv` (`id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink`), listed first in manifest `data`. |
| Row-level isolation via record rules | `security/ir_rules.xml` `ir.rule` with `domain_force` — multi-company `[('company_id','in',company_ids)]`, portal follower rules. |
| Groups defined in XML | `security/res_groups.xml`, loaded before rules and views. |
| Manifest `data` order matters | security → reports → data → wizards → views → menus (last). |
| Translatable strings | `_()` / `_lt()` / `self.env._()`; `i18n/*.po` + `<module>.pot` per module. |
| No string-formatted SQL | Use `odoo.tools.SQL()`; enforced by `test_lint` SQL-injection checker. |
| External IDs everywhere | XML records carry `id=`; cross-module refs use `module.xml_id`. |
| License | `'license': 'LGPL-3'` in each manifest; "Part of Odoo" header. |
| Tests ship with the module | `tests/` (Python), `static/tests/` (Hoot unit tests + tours). |

## Architecture Overview

- **Entry point**: `odoo-bin` → `odoo.cli.main()` (`odoo/cli/command.py`). Subcommands in `odoo/cli/`: `server` (default), `shell`, `scaffold`, `db`, `populate`, `neutralize`, `obfuscate`, `upgrade_code`, `cloc`, `start`, `deploy`, `tsconfig`.
- **Bootstrap**: `odoo/cli/server.py` parses config (`odoo/tools/config.py`) and starts `odoo/service/server.py` (threaded / prefork / gevent).
- **Module loading**: `odoo/modules/registry.py` (per-database registry), `loading.py` (install/update, data files), `graph.py` (dependency order), `migration.py` (version migration scripts), `module.py` (manifests).
- **Core**: `odoo/models.py` (ORM: BaseModel, Model, TransientModel, AbstractModel), `fields.py`, `api.py` (Environment, `depends`/`onchange`/`constrains`/`model_create_multi`), `http.py` (WSGI, `route`, Request, sessions), `sql_db.py`, `osv/expression.py` (domains), `tools/`, `exceptions.py`, `service/` (RPC services).
- **`odoo/addons/base`**: core data model (`ir.*`, `res.*`, users, groups, `ir.rule`, `ir.model.access`); `odoo/addons/test_*` are framework test modules.
- **Web client**: `addons/web` — OWL assets (`static/src`), Hoot framework, controllers (`dataset.py`, `action.py`, `view.py`, `session.py`, `home.py`, `binary.py`, `export.py`, `report.py`, `json.py`).
- **Runtime**: docker compose — `postgres:16` + `odoo` (python:3.12-slim) on 8069; `docker/odoo.conf` with `dev_mode = reload`; `develop.watch` syncs `./addons`, `./custom_addons` and `./odoo`.

## Directory Structure

```
odoo-bin                 entry script
odoo/                    framework: models.py fields.py api.py http.py sql_db.py cli/ modules/ service/ tools/ osv/ tests/
odoo/addons/base         base module (+ odoo/addons/test_* framework test modules)
addons/                  621 standard modules (sale, sale_management, sales_team, web, account, stock, …)
docker/odoo.conf         addons_path = /opt/odoo/addons,/opt/odoo/odoo/addons,/opt/odoo/custom_addons
custom_addons/           project-specific addons (sale_credit_limit_warning)
debian/, setup/, doc/    packaging & docs
memory-bank/             Banyan project memory
```

## Key Patterns

### API surface
- Controllers subclass `http.Controller`; `@http.route(path, type='http'|'json', auth='user'|'public'|'none', methods=…, csrf=…, readonly=…)`.
- Web client JSON-RPC: `/web/dataset/call_kw[/<path>]`, `/web/dataset/call_button` (`addons/web/controllers/dataset.py`).
- External RPC: `/xmlrpc/<service>`, `/xmlrpc/2/<service>`, `/jsonrpc` (`odoo/addons/base/controllers/rpc.py`).
- **No JSON-2 (`/json/2`) API in 18.0** (arrives in 19). `/json/<path>` is a readonly browser JSON view.

### Models
- `class SaleOrder(models.Model): _name = 'sale.order'; _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin', …]` — mixins via `_inherit` list.
- Extension: class with `_inherit = 'res.partner'` and no `_name`. Delegation via `_inherits`.
- `AbstractModel` for mixins/report models; `TransientModel` for wizards.
- Business logic in computed fields (`@api.depends`), `@api.constrains`, `@api.onchange`.

### Views & data
- XML `ir.ui.view` (form/list/kanban/search), `ir.actions.*`, `menuitem`; inheritance via `inherit_id` + `<xpath>`.
- QWeb for reports and portal templates.
- `data/` XML for crons, sequences, mail templates, config parameters; demo data under manifest `demo`.

### Frontend assets
- Declared in manifest `assets` (`web.assets_backend`, `web.assets_frontend`, `web.assets_tests`, `web.assets_unit_tests`).
- ES modules importing `@web/…` / `@<module>/…`; registration via `registry.category(...)`; OWL components paired with `.xml` templates.

## Code Organization Patterns

- **Primary languages**: Python (backend), JavaScript ES modules (OWL frontend), XML (views/data/templates), SCSS (styles), CSV (ACLs).
- `.js` is the standard frontend extension (no TypeScript); no build step — assets bundled at runtime.
- `git ls-files addons/sale` extension counts: py 66, po 63, xml 52, js 45, scss 10, csv 1, pot 1.

| Directory | Dominant extension(s) | Notes |
|---|---|---|
| `__manifest__.py`, `__init__.py` | .py | Manifest dict; `__init__` imports `models`, `controllers`, `wizard`, `report` |
| `models/` | .py | One file per model / inherited model |
| `views/` | .xml | `<model>_views.xml`, `*_menus.xml`, portal templates |
| `security/` | .csv + .xml | `ir.model.access.csv`, `res_groups.xml`, `ir_rules.xml` |
| `data/` | .xml | Crons, sequences, mail templates, demo |
| `controllers/` | .py | `http.Controller` subclasses |
| `wizard/` | .py + .xml | TransientModel + `*_views.xml` |
| `report/` | .py + .xml | SQL-view report models + QWeb templates |
| `static/src/js/<component>/` | .js + .xml (OWL) + .scss | One folder per component / field widget |
| `static/tests/` | `*.test.js` (Hoot), `tours/*.js`, `mock_server/mock_models/*.js` | Legacy `*_tests.js` = QUnit |
| `tests/` | .py | `test_*.py`, `common.py` fixtures |
| `i18n/` | .po + .pot | |

### Custom module shape (as built)
Top-level `custom_addons/` is wired in: `/opt/odoo/custom_addons` is in `addons_path` (`docker/odoo.conf`), and `develop.watch` has a sync+restart entry for `./custom_addons` (`docker-compose.yml`; `COPY . .` also bakes it into the image).

`custom_addons/sale_credit_limit_warning/` is the reference layout:
- `__manifest__.py` — `depends: ['sale']`, `data: ['views/sale_order_views.xml']`, `license: 'LGPL-3'`, `installable: True`. No `security/` directory because it adds no models.
- `models/sale_order.py` — `_inherit = 'sale.order'` extension.
- `views/sale_order_views.xml` — form inheritance.
- `tests/` — `test_credit_limit_warning.py`, imported from `tests/__init__.py`.

Add `security/`, `data/`, `controllers/`, `static/`, `i18n/` only when the addon needs them (a new model requires `security/ir.model.access.csv`, listed first in `data`).

**Compute fields (non-stored)**
- Use `store=False` for display-only warnings; one shared `_compute_credit_warning` fills several fields (e.g. `credit_warning_message`, `credit_warning_level`).
- Declare every input in `@api.depends`, including related paths (`partner_id.commercial_partner_id.credit_limit`, `company_id.account_use_credit_limit`). Add `@api.depends_context('company')` when the value is company-dependent.
- Read company-dependent partner accounting fields with `partner.with_company(company).sudo()`. The `credit*` fields are accounting-only, so a salesman would otherwise raise `AccessError`. The company comes from the order, not the user's current company.
- Reset the output fields at the top of the loop and `continue` on every early exit, so the field never renders `False`/`None` as text. Degrade silently (no exception) for a missing partner, zero rate or no lines.

**View inheritance that replaces a core banner**
- To swap out a core element, set `invisible="1"` on its parent `div` via `<xpath>` (`attributes`). Keep the core field itself in the arch, because other code and tests still read it through the form.
- Add the replacement banners with `position="after"`. Each uses `invisible="<field> != '<value>'"` and needs a hidden helper field (`invisible="1"`) for the expression to evaluate.

**Tests**
- `@tagged('post_install', '-at_install')` on a `TestSaleCommon` subclass, run via `--test-tags` (see `techContext.md` § Development Commands).
- Assert both the computed values and the view arch (`get_view(view_type='form')`) so XML regressions fail the suite.

## Testing Patterns

a. **Location**: Python tests in `<module>/tests/`, imported in `tests/__init__.py`; JS in `<module>/static/tests/`. Framework tests in `odoo/tests/` and `odoo/addons/test_*`.

b. **File mapping / naming**: `test_<feature>.py` with `Test<Feature>` classes — feature-based, not one-per-source-file. Shared fixtures in `tests/common.py` (e.g. `SaleCommon`, `TestSaleCommon`). JS: `*.test.js` (Hoot), tours in `static/tests/tours/*.js`.

c. **Base classes**: `TransactionCase` (each test rolled back), `HttpCase` (browser, `url_open`, `start_tour`), domain bases (`AccountTestInvoicingCommon`, `BaseUsersCommon`, `MailCommon`, `HttpCaseWithUserPortal`, `PaymentHttpCommon`), combined via multiple inheritance.

d. **Grouping**: by behaviour/business scenario within a feature class; shallow (class → test methods).

e. **Tagging**: `@tagged('post_install', '-at_install')` is ubiquitous; custom tags select via `--test-tags`.

f. **Setup sharing**: `@classmethod setUpClass(cls)` builds records once per class via `cls.env[...]` / `cls.env.ref(...)`; test users created with group xml-ids.

g. **UI tours**: `registry.category("web_tour.tours").add(name, {steps})`; run from Python with `self.start_tour("/odoo", "tour_name", login="admin")`; assets in `web.assets_tests`.

h. **Mocking**: Hoot mock server + mock models for JS; Python relies on real ORM in a rolled-back transaction, `freezegun`, `patch`/`mute_logger` helpers.

i. **Scope emphasis**: integration-heavy (ORM + DB in TransactionCase); tours for UI flows; Hoot unit tests for widgets.

j. **Ratio (addons/sale)**: 28 test files, ~9,340 test lines vs ~7,940 source py lines (~1.2:1). JS: 4 unit/helper + 7 tours + 4 mock models vs 44 src JS files.

k. **Not tested much**: `.po` content, pure view XML layout (validated at install via RNG only), SCSS, demo data (load-only), most crons and mail templates. No coverage tooling; no CI in the fork. Chrome is not in the docker image, so tours/headless Hoot can't run in-container.

**Running**: see `techContext.md` § Development Commands (`--test-enable --test-tags /<module>[:Class.method]`, separate `odoo-test` DB, `--http-port=8070` when the main server is running).

<!-- AUTO-MANAGED: c4-architecture-start -->
## C4 Architecture

<!--
  This section is auto-managed by /bmb:c4. Run /bmb:c4 to refresh.
  Do not hand-edit between the AUTO-MANAGED markers — edits are overwritten.
-->

This project's architecture is documented at four progressively zoomed-in C4 levels:

| Level | Audience | Document |
|-------|----------|----------|
| 1. Context | Everyone | [memory-bank/c4/c4-context.md](./c4/c4-context.md) — system purpose, personas, externals |
| 2. Container (index) | Tech-aware stakeholders | [memory-bank/c4/c4-container.md](./c4/c4-container.md) — one-line-per-container index |
| 2. Container (diagram) | Tech-aware stakeholders | [memory-bank/c4/c4-container-relationships.md](./c4/c4-container-relationships.md) — system-wide topology + cross-container matrix |
| 2. Container (detail) | Developers | [memory-bank/c4/containers/](./c4/containers/) — per-container deep-dive (always-on) |
| 3. Component (index) | Developers | [memory-bank/c4/c4-component.md](./c4/c4-component.md) — components grouped by container |
| 3. Component (diagram) | Developers | [memory-bank/c4/c4-component-relationships.md](./c4/c4-component-relationships.md) — cross-component dependency graph |
| 3. Component (detail) | Developers | [memory-bank/c4/components/](./c4/components/) — per-component deep-dive |
| 4. Code | Developers maintaining specific code | [memory-bank/c4/code/](./c4/code/) — per-directory docs |

**Entry point**: [memory-bank/c4/c4-index.md](./c4/c4-index.md)

### How Agents Should Use the C4 Docs

- **Planning agents** (`/bmb:plan`): read `c4-context.md` and `c4-container.md` to ground plans in the existing system shape. Drill into specific components only when the task affects them.
- **TDD Agent** (`/bmb:build`): when introducing or modifying a component, read its `components/c4-component-<name>.md` first. Update the affected component doc as part of the build (or rerun `/bmb:c4` after the build).
- **TDD Agent**: use `c4-component.md` (the lean index) to find which component owns the code under test, then read its `components/c4-component-<name>.md` detail doc for interface signatures and integration points worth covering.
- **Reflection Agent**: cite C4 levels when reflecting on architectural drift ("This task added cross-container traffic not yet in c4-container.md").
- **UAT Walker**: use `c4-container.md` to identify which container's UI surface a journey is walking.

### Refresh Cadence

`/bmb:c4` is idempotent. Re-run when:
- A new component, service, or container is introduced
- Deployment topology changes (split, merge, new datastore, new external integration)
- Before a major release that needs current architecture artifacts
- After significant refactors

It only re-walks subtrees whose source-directory hashes have changed.

**Last refreshed**: 2026-11-01T11:22:58Z
**Plugin version**: 2.2.1

<!-- AUTO-MANAGED: c4-architecture-end -->
