# UAT Configuration

This file is created and maintained by `/bmb:uat-init`. It carries project-specific UAT infrastructure (base URLs, persona credentials, auth strategy, viewport presets, isolation strategy).

**Companion file**: `memory-bank/projectConfig.md` `## UAT` section carries project-wide *ergonomic* defaults (default sections, artifact git policy). Keep secrets/infra here; keep ergonomics there.

---

**Status**: Configured
**Last Updated**: 2026-10-20

## Environments

| Name     | Base URL                | Default |
|----------|-------------------------|---------|
| dev      | http://localhost:8069   | yes     |

> `/bmb:uat` refuses to run against environments where `name == "prod"`. There is no override flag — production UAT must be intentionally invoked via a separate (future) command.

## Auth

- **Strategy**: token+fallback
  - `token` — inject localStorage/cookies from `.auth/<persona>.json`, hard-reload. Fastest.
  - `login` — drive the IDP UI. Slower but resilient to expired tokens.
  - `token+fallback` (default) — try token first; on auth failure or 401, fall back to `login` and cache fresh tokens back to `.auth/<persona>.json`.
- **Credential vault**: `.auth/` (must be in `.gitignore` — covered by the `.*` dotfiles rule)
- **Token file pattern**: `.auth/<persona>.json`
- **Login URL**: `/web/login`
- **Login selectors** (only when strategy includes `login`):
  - username: `input[name="login"]`
  - password: `input[name="password"]`
  - submit:   `button[type="submit"]`
  - post-login wait: url matches `/odoo`

## Persona Map

Each row maps a persona role discovered in `productBrief.md` → a test account → an auth reference (token path or env var name for password).

| Role             | Test Account                  | Auth Reference                           |
|------------------|-------------------------------|------------------------------------------|
| admin            | admin                         | .auth/admin.json or $TEST_ADMIN_PW       |
| user             | testuser@example.com          | .auth/user.json or $TEST_USER_PW         |
| portal           | portal@example.com            | .auth/portal.json or $TEST_PORTAL_PW     |
| salesman         | sales@example.com             | .auth/salesman.json or $TEST_SALES_PW    |
| warehouse        | stock@example.com             | .auth/warehouse.json or $TEST_STOCK_PW   |

## Viewports

| Name    | Width | Height | Default For      |
|---------|-------|--------|------------------|
| desktop | 1280  | 720    | all non-mobile   |
| mobile  | 375   | 667    | mobile section   |

## Execution

- **max_parallel_tabs**: 4
- **isolation_strategy**: auto          # auto | same-persona-only | incognito
  - `auto` (default) — probes incognito support at run start; falls back to `same-persona-only` if unavailable. Today this always falls back; the Claude-in-Chrome MCP does not yet expose incognito tab creation.
  - `same-persona-only` — explicit conservative. Walkers with the same resolved persona run in parallel; walkers with different personas serialize.
  - `incognito` — reserved for a future Claude-in-Chrome release. Selecting today errors at the phase gate.
- **auth_cookies_to_clear**:            # cookie names to scrub between persona groups
    - session_id
- **logout_url**: /web/session/logout   # path to hit for forced logout (or empty to skip)
- **screenshot_retention**: keep 10 most recent runs
- **default_timeout_ms**: 15000
- **ux_pattern_check**: enabled

## Notes

- The credential vault directory MUST be added to `.gitignore`. UAT artifacts may include screenshots that contain test-account PII; configure `artifact_git_policy` in `projectConfig.md` accordingly.
- `--persona-override` flags warn when the supplied address does not match the project's documented test-account pattern. Update the Persona Map rather than relying on overrides for repeated runs.
- Odoo specifics: the `user`, `portal`, `salesman` and `warehouse` accounts must be created in the dev database with matching access groups (Internal User; Portal; Sales / User: Own Documents Only; Inventory / User). The token file for each persona holds the Odoo `session_id` cookie.
