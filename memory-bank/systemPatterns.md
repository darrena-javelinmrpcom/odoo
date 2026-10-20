# System Patterns

Odoo **18.0 Community** (LGPL-3) fork. 621 addon directories under `addons/`; framework core under `odoo/`. Fork-specific additions are limited to `Dockerfile`, `docker-compose.yml`, `docker/odoo.conf`.

## Guiding Principles

| Principle | Description |
|---|---|
| Modular addons | Every feature is an installable module with explicit `depends` in `__manifest__.py`; `odoo/modules/graph.py` + `loading.py` load in dependency order. |
| Extend, don't modify | Models via `_inherit`, views via XPath `inherit_id`, JS via `patch()` + registries, controllers via subclassing. Keep core/upstream files untouched so upstream merges stay clean. |
| Declarative data | Views, menus, actions, security, crons, sequences are XML/CSV listed in the manifest `data` key (security first, menus last), loaded by `odoo/tools/convert.py`. |
| Layered security | Model ACLs (`security/ir.model.access.csv`), groups (`res_groups.xml`), record rules (`ir_rules.xml`), field `groups=`, `auth=` on routes. Every new model needs an ACL row. |
| i18n everywhere | User-facing strings via `_()` (Python, literal strings only) / `_t()` (JS); per-module `i18n/<module>.pot` + `.po`. |
| ORM-first data access | Logic runs on recordsets through the Environment. Raw SQL only via `odoo.tools.SQL` — never string-formatted SQL. |
| Licensing | LGPL-3; files carry the "Part of Odoo. See LICENSE file for full copyright and licensing details." header. |
| Tests ship with code | Each module has `tests/` (Python) and `static/tests/` (HOOT + tours). |

## Architecture Overview

Monolithic Python WSGI server on PostgreSQL:

- **Entry**: `odoo-bin` → `odoo.cli.main()` → subcommand in `odoo/cli/` (server, shell, scaffold, db, populate, neutralize, upgrade_code, …).
- **Request flow**: `odoo/http.py` `Application` → `Request` → `HttpDispatcher` (`type='http'`) or `JsonRPCDispatcher` (`type='json'`) → `@route` endpoint on a `Controller` subclass, executing against `request.env`.
- **Registry**: `odoo/modules/registry.py` — one model registry per database, built from the installed-module dependency graph.
- **Web client**: `addons/web` — OWL 2 SPA talking to the server mainly via `/web/dataset/call_kw` (JSON-RPC ORM calls) through `orm` / `rpc` services.
- **External API**: XML-RPC `/xmlrpc/2/{common,object,db}` and JSON-RPC `/jsonrpc` (`odoo/addons/base/controllers/rpc.py`), backed by `odoo/service/{common,db,model,security}.py`.
- **Server modes**: threaded (default), prefork (`--workers`), gevent for longpolling/websocket (`odoo/service/server.py`).

## Directory Structure

```
odoo-bin                  Launcher
odoo/                     Framework core (18.0: no odoo/orm/ package yet)
  models.py               BaseModel / Model / TransientModel / AbstractModel, recordset ops
  fields.py               Field types, Command (x2many)
  api.py                  Environment, decorators
  http.py                 Controller, route, Request, Dispatchers, Application
  sql_db.py               psycopg2 cursor + pooling
  exceptions.py           UserError, ValidationError, AccessError, …
  osv/expression.py       Domain → SQL
  cli/                    CLI subcommands (+ templates for scaffold)
  service/                server.py + RPC services
  modules/                manifest, graph, loading, registry, migration, neutralize
  tools/                  config, convert, translate, safe_eval, sql, misc, float_utils, js_transpiler, …
  tests/                  Test framework (common.py, case.py, form.py, loader.py, tag_selector.py)
  addons/base/            base module (res.*, ir.*)
  addons/test_*/          ~28 framework self-test modules (test_new_api, test_http, test_inherit, test_lint, …)
  upgrade_code/           Source-rewrite scripts
addons/                   621 modules (web, mail, account, sale, stock, mrp, website, l10n_*, …)
setup/, debian/           Packaging
docker/odoo.conf          Fork dev config
doc/cla/                  Contributor License Agreements
```

## Key Patterns

### Module Anatomy (reference: `addons/sale`)
- `__manifest__.py`: name, version, category, `depends`, `data` (ordered), `assets`, `license`.
- `__init__.py` imports `models`, `controllers`, `wizard`, `report`.
- `models/` — one file per model or extended model (`sale_order.py`, `res_partner.py`).
- `wizard/` — TransientModels + views. `report/` — SQL-view models + QWeb reports.
- `controllers/` — `http.Controller` subclasses.
- `views/*_views.xml`, `*_menus.xml`; `security/`; `data/` (crons, sequences, mail templates); `demo/`.
- `static/src/{js,xml,scss,views,img}`; `static/tests/` (`*.test.js`, `mock_server/`, `tours/`).
- `i18n/*.po` + `<module>.pot`. Optional `migrations/<version>/{pre,post,end}-*.py`.

### ORM Inheritance
- **New model**: `_name = 'x.y'`, `_description`, optional mixins `_inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin', …]`.
- **Extension (in place)**: `_inherit = 'res.partner'` without `_name`; chain `super()`.
- **Delegation**: `_inherits = {'parent.model': 'fk_field'}`.
- **Types**: `models.Model`, `TransientModel` (wizards), `AbstractModel` (mixins).
- **Decorators**: `@api.depends`, `@api.constrains`, `@api.onchange`, `@api.model`, `@api.model_create_multi`, `@api.ondelete`.
- **Recordsets**: iterate `for rec in self`; `env['model']`, `env.ref('xmlid')`, `with_context` / `with_company` / `sudo()`; `Command.create/link/set` for x2many; domains as tuple lists.

### HTTP Controllers
`@http.route('/path/<int:id>', type='http'|'json', auth='user'|'public'|'none', methods=[...], website=True)` on `Controller` subclasses. Extend existing controllers by subclassing (e.g. `CustomerPortal(payment_portal.PaymentPortal)`). JSON routes use JSON-RPC 2.0 envelopes.

### Frontend
- ES modules with `/** @odoo-module **/`; imports `@web/...`, `@odoo/owl`, `@<module>/...`.
- OWL components paired with XML QWeb templates; registration via `registry.category(...)`; services via `useService`.
- Assets declared in manifest `assets` (`web.assets_backend`, `web.assets_frontend`, `web.assets_unit_tests`, …).
- Vendored libs in `addons/web/static/lib` (owl, hoot, luxon, bootstrap, Chart, fullcalendar, legacy qunit).

### Shared Utilities
- Python: `odoo.tools` (`float_compare`/`float_round`, `format_date`, html helpers, `SQL`, `safe_eval`, `ormcache`).
- Shared models: `base` (res.partner, res.users, res.company, ir.*); mixins `mail.thread`, `portal.mixin`, `utm.mixin`.
- JS: `@web/core/*` (registry, `_t`, rpc, orm service, hooks, dialogs).

## Code Organization Patterns

- **Languages**: Python 3 (backend), JavaScript ES modules (frontend), XML (views/data/QWeb), SCSS, CSV.
- **TypeScript is not used** for new files (`odoo/cli/tsconfig.py` only generates an IDE `tsconfig.json`). No type-check gate.
- **New module shape**: `python odoo-bin scaffold <name> <dir>` → `__manifest__.py`, `__init__.py`, `models/`, `views/`, `security/ir.model.access.csv`, `controllers/`, `demo/`; add `tests/` (imported in `tests/__init__.py`) and `static/src` as needed. Custom modules go in `addons/` or a separate directory appended to `addons_path`.

| Directory / role | Default extension(s) |
|---|---|
| `__manifest__.py`, `__init__.py` | `.py` |
| `models/`, `wizard/`, `report/` (logic) | `.py` |
| `controllers/` | `.py` |
| `views/`, `wizard/*_views.xml`, `report/*.xml` | `.xml` |
| `security/` | `ir.model.access.csv` + `.xml` |
| `data/`, `demo/` | `.xml` (occasionally `.csv`) |
| `i18n/` | `.po`, `.pot` |
| `static/src/**` | `.js` + `.xml` (templates) + `.scss` |
| `static/description` | `.png` / `.svg`, `index.html` |
| `tests/` | `test_*.py`, `common.py` |
| `static/tests/` | `*.test.js` (legacy `*_tests.js` exist) |
| `static/tests/tours/` | `*.js` |
| `static/tests/mock_server/` | `.js` |
| `migrations/<ver>/` | `pre-*.py`, `post-*.py` |

## Testing Patterns

- **Location**: Python tests in `<module>/tests/`; every `test_*.py` **must** be imported in `tests/__init__.py` or it won't run. JS tests in `<module>/static/tests/`.
- **File mapping**: feature/flow-based test files (e.g. `test_sale_flow.py`, `test_access_rights.py`), not one-per-source-file.
- **Naming**: `test_*.py`; JS `*.test.js`.
- **Grouping**: `TransactionCase` classes grouped by business scenario; methods `test_<behaviour>`.
- **Nesting**: shallow — one class level.
- **Setup sharing**: heavy `setUpClass` with `cls.env`; shared fixtures in `tests/common.py` (e.g. `TestSaleCommonBase` on `AccountTestInvoicingCommon`).
- **Framework & assertions**: Odoo test runner on `unittest` — `TransactionCase` (savepoint rollback per test), `SingleTransactionCase`, `HttpCase` (live server + headless Chrome, `url_open`, `start_tour`), `Form` (onchange simulation). JS: HOOT (`test`, `expect`) + `@web/../tests/web_test_helpers` (`mountView`, `contains`, `defineModels`, `onRpc`).
- **Tags**: `@tagged('post_install', '-at_install')` dominant for flow/HttpCase/tour tests; `at_install` default; custom tags allowed (`'-standard', 'external'`).
- **Mocking**: `unittest.mock.patch`, `self.patch(...)`, `freeze_time`, `mute_logger`, `assertQueryCount`, `with_user`; JS `mock_server` models + `onRpc`.
- **Scope**: integration-heavy against real PostgreSQL (business flows, access rights, controllers, reports); few pure unit tests; tours for E2E UI.
- **Ratio**: `sale` ≈ 1.15:1 test LOC to source LOC (~9.3k vs ~8.1k), 28 test modules + 7 tours.
- **Not tested**: vendored JS libs; packaging (`setup/`, `debian/`); the fork's Docker setup.
- **Run**: `python odoo-bin -d testdb -u <mod> --test-tags /<mod> --stop-after-init` (throwaway DB; `--test-tags` implies `--test-enable`). Docker: `docker compose run --rm odoo python odoo-bin -c /etc/odoo/odoo.conf -d test -i <mod> --test-tags /<mod> --stop-after-init`.
- **Reference examples**: `odoo/addons/test_*` (test_new_api, test_http, test_inherit, test_performance).
