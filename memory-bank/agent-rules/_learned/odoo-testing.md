---
name: Odoo Testing (learned)
globs: ["custom_addons/**/tests/*.py", "addons/**/tests/*.py"]
paths: ["custom_addons/"]
topics: ["odoo", "testing", "characterization", "docker", "mutation-testing"]
priority: low
auto_generated: true
derived_from: [author-characterization-tests-partner-credit-warning]
evidence_count: 1
last_validated: 2026-11-03
---

# Odoo Testing

- `--test-tags` syntax is `[-][tag][/module][:Class][.method]`: write `characterization/banyan_sale_safety`, never `/banyan_sale_safety:characterization` (that selects a CLASS). Tests only run for modules installed/updated in the same run, so pass `-i`/`-u <addon>`. A wrong selector silently runs 0 tests: always confirm the `N tests` count in the log.
- Docker Odoo here is not bind-mounted: `docker compose exec odoo rm -rf <container addon path>`, then `docker compose cp` after every edit. Run a second `odoo-bin` with `--stop-after-init --http-port=8070` (the main server holds 8069).
- In Git Bash on Windows, prefix `docker compose exec ... /etc/...` commands with `MSYS_NO_PATHCONV=1` or the path is rewritten to a Windows path (exit 2).
- Characterization tests: `assertEqual` on full literal strings captured from the actual failure diff (placeholder, run, paste), never hand-derived. Write non-ASCII as escapes (`'\xa0'` from formatLang, `'\n'`). Tag each test `correct` / `bug-preserved` / `unclear`.
- Prove a safety net with a mutation check: change the real source, copy it into the container, expect exactly the targeted test to fail, `git checkout` to revert, re-run green, confirm `git status` is clean. Never commit the mutation.
