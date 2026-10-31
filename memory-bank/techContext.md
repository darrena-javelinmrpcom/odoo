# Tech Context

Fork of **Odoo 18.0 Community** (`odoo/release.py`: `version_info = (18, 0, 0, FINAL, 0, '')`), remote `github.com/DaKaZ/odoo`, branch `banyan`. The only fork-specific change is commit `8a9ce028 local docker setup` (`Dockerfile`, `docker-compose.yml`, `docker/odoo.conf`). ~621 modules under `addons/`. Active dev database: `odoo-dev` with the Sales app (`sale_management`) installed.

## Technology Stack

| Layer | Technology | Version / Notes |
|---|---|---|
| Backend language | Python | Supported 3.10–3.14 (`odoo/__init__.py`); container runs **3.12** (`python:3.12-slim`) |
| Backend framework | Odoo ORM + HTTP (Werkzeug) + QWeb server rendering | `odoo/` core, `odoo/addons/base`; entry `odoo-bin` |
| Frontend framework | OWL (Odoo Web Library) | **2.8.2**, vendored `addons/web/static/lib/owl/owl.js` |
| Templates / views | XML (QWeb, views, data) | `views/`, `data/`, `static/src/**/*.xml` per addon |
| Styling | SCSS (libsass), Bootstrap; LESS + rtlcss for RTL | Bootstrap vendored in `addons/web/static/lib/bootstrap` |
| Vendored JS libs | luxon, Chart.js, fullcalendar, jquery, dompurify, pdfjs, popper, prismjs, ace, zxing | `addons/web/static/lib/` (no root `package.json`) |
| Python tests | `odoo.tests` (unittest-based) | TransactionCase, HttpCase, tours |
| JS tests | **Hoot** (+ hoot-dom, hoot-mock), legacy QUnit | `*.test.js`; runner at `/web/tests` |
| Linting | flake8 (`setup.cfg`); Odoo `test_lint` module (pylint/eslint checkers) | Lint tools not installed in the image |
| Database | PostgreSQL **16** | psycopg2 2.9.9 |
| File storage | Odoo filestore | `data_dir=/var/lib/odoo` (volume `odoo-filestore`) |

## Key Dependencies (requirements.txt, Python 3.12 pins)

- **psycopg2 2.9.9** — PostgreSQL driver
- **Werkzeug 3.0.1** — WSGI/HTTP under `odoo.http`
- **lxml 5.2.1** (+ lxml-html-clean) — XML views/QWeb/data parsing, HTML cleaning
- **Jinja2 3.1.2, MarkupSafe 2.1.5** — templating helpers
- **Babel 2.10.3, polib, pytz** — i18n, `.po` files, timezones
- **libsass 0.22.0, rjsmin** — SCSS compile, JS minify for asset bundles
- **reportlab 4.1.0, PyPDF2 2.12.1, qrcode, Pillow 10.2.0** — PDF reports, barcodes, images. **wkhtmltopdf is NOT installed in the image** → QWeb PDF rendering limited.
- **openpyxl, xlrd, XlsxWriter, xlwt** — spreadsheet import/export
- **gevent 24.2.1 / greenlet 3.0.3** — longpolling/websocket (bus)
- **cryptography, pyopenssl, passlib** — crypto, TLS, password hashing
- **requests 2.31.0** — outbound HTTP (IAP, integrations)
- **python-ldap, zeep, python-stdnum, num2words, freezegun** — LDAP auth, SOAP, number validation, amount-in-words, time freezing in tests

## Build Tools & Packaging

- **pip** from `requirements.txt` (Dockerfile). `setup.py` (setuptools; version from `odoo/release.py`).
- **npm** (container only) installs `rtlcss` globally.
- `setup/` (package builders for Debian/Fedora/Windows), `debian/` packaging, `.weblate.json` translations config.

## Infrastructure & Local Environment

**Dockerfile** (`python:3.12-slim`, WORKDIR `/opt/odoo`): apt build deps (libxml2/libxslt/libldap/libsasl2/libssl/libjpeg/libpq/libffi/zlib dev headers), npm, node-less, xfonts, fontconfig; `npm i -g rtlcss`; `pip install -r requirements.txt` (cached layer); `COPY . .`; EXPOSE 8069; CMD `python odoo-bin -c /etc/odoo/odoo.conf`. No Chrome/Chromium.

**docker-compose.yml**:
- `db`: `postgres:16`, `POSTGRES_USER=odoo`, `POSTGRES_DB=postgres`, volume `pg-data`
- `odoo`: local build, `depends_on: db`, `8069:8069`, `./docker/odoo.conf` → `/etc/odoo/odoo.conf:ro`, volume `odoo-filestore` → `/var/lib/odoo`, `PYTHONDONTWRITEBYTECODE=1`
- `develop.watch`: `./addons` → `/opt/odoo/addons` (sync+restart), `./custom_addons` → `/opt/odoo/custom_addons` (sync+restart), `./odoo` → `/opt/odoo/odoo` (sync+restart), `requirements.txt` → rebuild

**Important**: source is **baked into the image** (`COPY . .`), not bind-mounted. Only `docker compose watch` syncs `./addons`, `./custom_addons` and `./odoo` into the running container. `docker compose run` uses image-time code — prefer `exec` while watch is running, or rebuild.

## Environment Configuration

`docker/odoo.conf` (mounted read-only):
- `addons_path = /opt/odoo/addons,/opt/odoo/odoo/addons,/opt/odoo/custom_addons`
- `data_dir = /var/lib/odoo`
- `db_host = db`, `db_port = 5432`, `db_user = odoo`
- `dev_mode = reload` (Python auto-reload; XML/data still needs `-u` or `dev_mode=xml`)
- No `dbfilter`, `list_db`, `workers`, log options → threaded mode, DB manager enabled
- **Secrets**: `admin_passwd` (master password) and `db_password` are trivial dev defaults committed in plain text; `POSTGRES_PASSWORD` inline in compose. Local use only — never reuse in a deployed environment.
- DB `odoo-dev` is not created by compose; it was created at runtime (UI / CLI).

### Local requirements
- Docker Desktop with Compose ≥ 2.22 (for `develop.watch`).
- Non-docker: Python 3.10–3.13, `pip install -r requirements.txt`, local PostgreSQL, `npm i -g rtlcss`. Docker is the supported path.

## Development Commands

### Stack lifecycle
```bash
docker compose up -d --build        # build + start db and odoo
docker compose watch                # dev loop: sync+restart on ./addons, ./odoo
docker compose ps
docker compose logs -f odoo
docker compose restart odoo
docker compose down                 # stop (volumes kept)
docker compose down -v              # DESTRUCTIVE: drops DB + filestore volumes
```

### Shells / DB
```bash
docker compose exec odoo bash                                    # WORKDIR /opt/odoo
docker compose exec db psql -U odoo -d odoo-dev
docker compose exec odoo python odoo-bin shell -c /etc/odoo/odoo.conf -d odoo-dev --no-http
```

### Install / upgrade modules
The main server already listens on 8069 in the container — a second `odoo-bin` via `exec` needs `--no-http` or another `--http-port`.
```bash
docker compose exec odoo python odoo-bin -c /etc/odoo/odoo.conf -d odoo-dev -i <module> --stop-after-init --no-http
docker compose exec odoo python odoo-bin -c /etc/odoo/odoo.conf -d odoo-dev -u <module> --stop-after-init --no-http
docker compose restart odoo
```
Browser alternatives: Apps → Upgrade; developer mode at `http://localhost:8069/web?debug=1`.

### Python tests
`--test-tags` syntax: `[-][tag][/module][:Class][.method]`. HttpCase/tour tests need HTTP → use a free port.
```bash
docker compose exec odoo python odoo-bin -c /etc/odoo/odoo.conf -d odoo-test -i <module> \
  --test-enable --test-tags /<module> --stop-after-init --http-port=8070 --log-level=test
#   ... --test-tags /<module>:TestClassName
#   ... --test-tags /<module>:TestClassName.test_method
#   ... --test-tags post_install/<module>
```
Prefer a throwaway DB (`odoo-test`) over `odoo-dev` for test runs.

Tests only run for modules being upgraded or installed in that run, so pass `-u` for the module under test and for any core module whose tests you want:
```bash
# custom addon (sale_credit_limit_warning)
docker compose exec odoo python odoo-bin -c /etc/odoo/odoo.conf -d odoo-test -u sale_credit_limit_warning \
  --test-tags /sale_credit_limit_warning --stop-after-init --http-port=8070 --log-level=test
# core regression for the credit-limit behaviour the addon relies on
docker compose exec odoo python odoo-bin -c /etc/odoo/odoo.conf -d odoo-test -u sale \
  --test-tags /sale:TestSaleOrderCreditLimit --stop-after-init --http-port=8070 --log-level=test
```

### JS unit tests (Hoot)
- Specs: `addons/*/static/tests/**/*.test.js`; helpers `addons/web/static/tests/web_test_helpers.js`.
- Interactive: log in as admin → `http://localhost:8069/web/tests` (legacy QUnit at `/web/tests/legacy`).
- Headless via `addons/web/tests/test_js.py` (`WebSuite.test_unit_desktop`) — **requires Chrome, which the image lacks**; tours and headless Hoot tests skip/fail in the container.

### Lint
```bash
docker compose exec odoo python odoo-bin -c /etc/odoo/odoo.conf -d odoo-test -i test_lint \
  --test-enable --test-tags /test_lint --stop-after-init --no-http
```
pylint/eslint are not installed in the image; corresponding checks skip.

## Linting & Conventions

- `setup.cfg` `[flake8]` (excludes `.git, .tx, debian, doc, setup`; RST docstring checks). No ruff / pyproject / pylintrc / prettier / editorconfig.
- `odoo/addons/test_lint`: pylint with Odoo checkers (SQL injection, gettext, unlink override), eslint (ES2022 modules), manifest/i18n/route/override-signature checks.
- `CONTRIBUTING.md` → Odoo wiki; PR template at `.github/PULL_REQUEST_TEMPLATE.md`.
- Conventions: `_()` / `self.env._()` for translatable strings; never format SQL strings (use `SQL()`); tests in `<module>/tests/test_*.py` imported in `tests/__init__.py`; HttpCase tagged `post_install, -at_install`.

## CI/CD

- **No CI workflows** — `.github/` has only the upstream PR template and issue templates (upstream uses runbot).
- Any CI for `banyan` (flake8, Python tests, Hoot) must be added. No build/deploy pipeline.

## UAT

- Config: `memory-bank/uat-config.md` — dev URL `http://localhost:8069`, auth token+fallback via `/web/login`, personas admin / user / portal / salesman / warehouse.
