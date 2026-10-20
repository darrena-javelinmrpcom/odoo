# Tech Context

Fork of **Odoo 18.0 Community** (`odoo/release.py`: `version_info = (18, 0, 0, FINAL, 0, '')`), remote `github.com/DaKaZ/odoo`, branch `banyan`. The only fork-specific change is commit `8a9ce028 local docker setup` (`Dockerfile`, `docker-compose.yml`, `docker/odoo.conf`).

## Technology Stack

### Language & Runtime
- **Python** — `setup.py` `python_requires='>=3.10'`; `odoo/__init__.py` `MIN_PY_VERSION=(3,10)`, `MAX_PY_VERSION=(3,14)`. Docker image: **Python 3.12** (`python:3.12-slim`).
- **JavaScript** — native ES modules, transpiled server-side by `odoo/tools/js_transpiler.py`. No TypeScript, no npm build step.
- **SCSS** — compiled server-side with libsass. **QWeb XML** templates on both server and client.

### Backend Framework (in-house, `odoo/`)
- **ORM**: `odoo/models.py`, `odoo/fields.py`, `odoo/api.py`, `odoo/osv/` (domain expressions).
- **HTTP**: `odoo/http.py` on Werkzeug 3.0.1; controllers in each addon's `controllers/`.
- **Server**: `odoo/service/server.py` — threaded / prefork / gevent modes; longpolling + websocket via gevent.
- **DB access**: `odoo/sql_db.py` (psycopg2, connection pooling).
- **CLI**: `odoo-bin` + `odoo/cli/` (server, shell, scaffold, …).
- **Modules**: `odoo/modules/` (loader, registry, migrations); `odoo/upgrade/`, `odoo/upgrade_code/`.

### Frontend (`addons/web/static/`)
- **OWL 2.8.2** (`lib/owl/owl.js`) — Odoo's reactive component framework.
- Bootstrap 5.3.3, Popper, Chart.js + Luxon, FullCalendar, DOMPurify, pdf.js, Prism, ACE, zxing, signature_pad; jQuery retained for legacy code.
- **Asset bundling** is server-side: `odoo/addons/base/models/assetsbundle.py` + `ir_asset.py` consume each manifest's `assets` key (`web.assets_backend`, `web.assets_unit_tests`, …). rjsmin for JS, libsass for SCSS, rtlcss (global npm) for RTL.

### Testing Frameworks
- **Python**: Odoo test runner `odoo/tests/` (`TransactionCase`, `HttpCase`, tours, `Form`, tag selector). `freezegun` for time.
- **JS**: **HOOT** (`addons/web/static/lib/hoot`) — current; legacy **QUnit** retained. Tours run via HttpCase + headless Chrome.
- **Lint**: `odoo/addons/test_lint` (pylint, eslint, manifest, pofile, SQL-injection, gettext checkers); `setup.cfg` `[flake8]`.

## Component Structure

| Component | Path | Purpose |
|-----------|------|---------|
| Core framework | `odoo/` | ORM, HTTP, service, tools, CLI, module loader |
| Base addon + framework tests | `odoo/addons/` | `base` plus ~28 `test_*` modules |
| Business apps | `addons/` | **621** modules (each with `__manifest__.py`), incl. 120 `l10n_*` prefixes |
| Entry point | `odoo-bin` | CLI launcher |
| Packaging | `setup/`, `debian/`, `setup.py`, `MANIFEST.in` | deb/rpm/win32 packaging |
| Local docker (fork) | `Dockerfile`, `docker-compose.yml`, `docker/odoo.conf` | Local dev environment |

## Key Dependencies (`requirements.txt`, pinned per Python version — 3.12 values)

| Library | Purpose |
|---|---|
| psycopg2 2.9.9 | PostgreSQL driver |
| Werkzeug 3.0.1 | WSGI / HTTP |
| Jinja2 3.1.2, MarkupSafe 2.1.5 | Templating / escaping |
| lxml 5.2.1 + lxml-html-clean | XML / QWeb views, HTML sanitizing |
| gevent 24.2.1, greenlet 3.0.3 | Longpolling / websocket worker |
| Babel, polib, pytz, python-dateutil | i18n, timezones |
| libsass 0.22.0, rjsmin 1.2.0 | Asset compilation |
| reportlab 4.1.0, PyPDF2 2.12.1, Pillow 10.2.0, qrcode | PDF reports, images |
| openpyxl, xlrd, XlsxWriter, xlwt | Excel import/export |
| cryptography, pyopenssl, passlib | Crypto, password hashing |
| requests, urllib3, zeep | HTTP clients, SOAP |
| python-ldap | `auth_ldap` |
| freezegun | Testing |

External runtime tools: **wkhtmltopdf** (PDF reports — *not* in the Docker image), **rtlcss** + **node-less** (installed).

## Database & Storage
- **PostgreSQL** (>10 supported; Docker uses **postgres:16**).
- **Filestore** under `data_dir` (`/var/lib/odoo` in Docker) — `filestore/<dbname>/`; sessions also under `data_dir`.

## Infrastructure (Local Docker)

- **`Dockerfile`**: `python:3.12-slim`; apt build deps (libxml2/xslt, ldap/sasl, ssl, jpeg, pq, ffi, zlib), `npm`, `node-less`, xfonts, `npm i -g rtlcss`; `WORKDIR /opt/odoo`; `pip install -r requirements.txt`; `COPY . .` (source baked in); `EXPOSE 8069`; `CMD python odoo-bin -c /etc/odoo/odoo.conf`. Gaps: no wkhtmltopdf, no Chromium, no `.dockerignore`, runs as root.
- **`docker-compose.yml`**:
  - `db` — `postgres:16`, `POSTGRES_USER/PASSWORD=odoo`, volume `pg-data`, no host port.
  - `odoo` — built from `.`, port **8069:8069** (8072 websocket not exposed), `./docker/odoo.conf:/etc/odoo/odoo.conf:ro`, volume `odoo-filestore:/var/lib/odoo`, `PYTHONDONTWRITEBYTECODE=1`.
  - `develop.watch` — `./addons` and `./odoo` sync+restart; `requirements.txt` → rebuild.
- **`docker/odoo.conf`**: `addons_path=/opt/odoo/addons,/opt/odoo/odoo/addons`, `data_dir=/var/lib/odoo`, `db_host=db`, `db_user=odoo`, `dev_mode=reload`, no `db_name` (database manager at `/web/database/manager`). Dev-only credentials — never deploy.

## Development Commands

### Docker (primary)
```bash
docker compose up --build            # build + start db + odoo → http://localhost:8069
docker compose watch                 # live dev: sync addons/ + odoo/ and restart
docker compose logs -f odoo
docker compose exec odoo bash
docker compose down                  # -v also drops pg-data + odoo-filestore volumes
```
Source is copied into the image (not bind-mounted): code changes reach the container only via `docker compose watch` or a rebuild.

### Native
```bash
pip install -r requirements.txt
python odoo-bin --addons-path=addons,odoo/addons -d <db> -r odoo -w odoo --db_host=localhost --dev=reload,qweb,xml
python odoo-bin scaffold <module> <dir>
python odoo-bin shell -d <db>
```

### Testing
Tests need a throwaway database; always pass `--stop-after-init`.
```bash
# install + test a module inside the container
docker compose exec odoo python odoo-bin -c /etc/odoo/odoo.conf -d test_db \
  -i <module> --test-enable --stop-after-init --log-level=test

# upgrade existing db, run only selected tests
... -d test_db -u <module> --test-tags /<module> --stop-after-init

# tag syntax: [-][tag][/module][:Class][.method]
--test-tags /sale:TestSaleOrder.test_x
--test-tags post_install,-at_install
--test-tags /web.test_js             # JS suite via headless Chrome (needs Chromium — not in image)
--test-file path/to/test.py
```
- JS unit tests in browser: run server in dev mode, log in, open `http://localhost:8069/web/tests` (HOOT); legacy QUnit at `/web/tests/legacy`.
- Lint: `python odoo-bin -d test_db -i test_lint --test-tags /test_lint --stop-after-init`

### Linting / Formatting
- **Python**: `setup.cfg` `[flake8]`; canonical checks are the pylint tests in `test_lint`. No ruff/pyproject.
- **JS**: tooling in `addons/web/tooling/` (ESLint + Prettier: 4-space, double quotes, width 100).
  ```bash
  bash addons/web/tooling/enable.sh    # installs root package.json/eslint config + lint-staged pre-commit hook
  npm run lint-diff | npm run format-diff | npm run lint-all
  bash addons/web/tooling/disable.sh
  ```

## Test Strategy
- Python: `TransactionCase` (rolled-back per test) for unit/ORM logic; `HttpCase` for controllers and tours; `@tagged('post_install', '-at_install')` for tests that need all modules loaded.
- JS: HOOT unit tests in `static/tests/*.test.js`; tours for end-to-end UI flows.
- Run the narrowest scope possible: `-u <module> --test-tags /<module>` against a disposable DB. Full-suite runs across 621 addons are impractical locally.
- Known environment gaps: no Chromium (tours/`test_js` cannot run in the container), no wkhtmltopdf (PDF reports render as HTML).

## CI/CD
- `.github/` contains only `PULL_REQUEST_TEMPLATE.md` and `ISSUE_TEMPLATE/` — **no workflows**. Upstream Odoo uses its own runbot (not in repo). All tests/lint are run manually.
- `.weblate.json` — translation config inherited from upstream.

## Coding Conventions
- Commit format (Odoo standard): `[TAG] module: short summary` (≤50 chars), blank line, body explaining *why*. Tags: `[FIX] [REF] [ADD] [REM] [REV] [MOV] [REL] [IMP] [MERGE] [CLA] [I18N] [PERF]`.
- Python: PEP8 + Odoo pylint rules — no SQL string formatting (use `SQL()`), `_()`/`_lt` only with literal strings, call `super()` in overrides.
- Contribution guidelines: `CONTRIBUTING.md` → https://github.com/odoo/odoo/wiki/Contributing.
