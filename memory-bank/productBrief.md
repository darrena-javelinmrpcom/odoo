# Product Brief

> This document captures the **product and project context** for development teams.
> It ensures all agents understand the product's purpose, users, constraints, **and the project's foundation**.

## Project Foundation

- **Project Name**: odoo — Banyan fork of Odoo 18.0 Community (`github.com/DaKaZ/odoo`, branch `banyan`); local dev database `odoo-dev`
- **Objectives**: Run a local, docker-based Odoo 18.0 Community instance with the Sales app (`sale_management`) installed, as a base for evaluating, testing (including browser UAT via `/bmb:uat`) and later extending the Sales vertical. Success = the stack starts reliably with `docker compose`, Sales flows work end-to-end for every UAT persona, and customisations stay out of core.
- **Scope**:
  - *In scope*: Odoo core (`odoo/`), standard Community addons (`addons/`, 621 modules) with the Sales vertical active (`sale_management` → `sale` → `sales_team`, `account_payment`, `portal`, `utm`, `digest`), the local docker setup, future custom addons.
  - *Out of scope*: Odoo Enterprise modules; production hosting; modifications to core / standard addons (customisations go in separate custom addons).
- **Key Stakeholders**: Repo owner [To be determined]; upstream maintained by Odoo S.A.

### Repository Structure
- **Type**: Poly-repo (single application with a plugin-style module system — no workspace tool)
- **Workspace Tool**: None
- **Workspace Root**: N/A
- **Layout**:
  - `odoo/` — core framework (ORM, HTTP, `odoo/addons/base`, `odoo/release.py` = 18.0 FINAL)
  - `addons/` — 621 standard Community modules (`sale`, `sale_management`, `sales_team`, `account`, `stock`, `portal`, `payment_*`, `mail`, …)
  - `odoo-bin` — server entry point; `setup/`, `setup.py`, `debian/` — packaging; `doc/`; `requirements.txt`
  - Fork-specific (commit `8a9ce028 local docker setup`): `Dockerfile` (python:3.12-slim + rtlcss/less), `docker-compose.yml` (postgres:16 `db` + `odoo` on 8069 with `develop.watch`), `docker/odoo.conf`
  - `memory-bank/` — Banyan project memory

## Git Configuration
- **Repository**: Yes
- **Provider**: GitHub
- **CLI Available**: gh (authenticated)
- **Remote URL**: https://github.com/DaKaZ/odoo.git
- **Default Branch**: banyan (remote HEAD points at upstream `19.0`; `banyan` is the working branch)
- **Metadata Branch**: banyan
- **Routing Mode**: classic
- **Sync Automation**: none
- **Archive Strategy**: push-and-pr

## Product Overview

- **Name**: Odoo 18.0 Community — Sales app (`sale_management`, "From quotations to invoices")
- **Value Proposition**: Open-source, web-based suite of integrated business apps. Sales lets an organisation manage quotations, sales orders, pricing, customers and the hand-off to invoicing / delivery / online payment from one system, with a self-service customer portal to review, sign and pay quotes.
- **Product Type**: Web-based ERP platform (modular Python/PostgreSQL framework + business apps), self-hosted in Docker here.
- **Stage**: Mature/GA upstream (18.0 final); fork is at local dev / evaluation stage.

## Key Functionality

- **Core ERP framework**: ORM, modular addons, web client (`/odoo`), access control (groups, ACLs, record rules), multi-company, multi-currency, chatter, QWeb PDF reporting, translations.
- **Quotations**: create/edit, send by email (`draft` → `sent`), optional products, quotation templates, validity dates, line discounts, product & combo configurator.
- **Sales Orders**: confirm (`sale`), cancel, lock confirmed sales, pro-forma invoices.
- **Pricelists & pricing**: customer pricelists, multi-currency, variants/attributes with extra prices.
- **Customers**: `res.partner` contacts/companies, commercial-partner hierarchy, portal access.
- **Invoicing hand-off**: invoices and down payments from sales orders (`account` / `account_payment`).
- **Delivery hand-off**: delivery orders when `sale_stock` is installed — **not a dependency of `sale_management`; currently unconfirmed**.
- **Sales Teams** (`sales_team`): `crm.team` with members and multi-company rules.
- **Customer portal**: `/my/quotes`, `/my/orders`, accept/sign, decline, online payment, document download.
- **Online payment**: `payment` framework + providers (Stripe, PayPal, Adyen, Mollie, … and `payment_demo`).
- **Reporting & digest**: Sales Analysis (`sale.report`); digest KPI `kpi_all_sale_total`.
- **UTM tracking**: campaign / medium / source on orders.

## Markets Serviced

- **Primary Market**: SMB and mid-market organisations needing integrated ERP/CRM — horizontal across distribution, services, manufacturing, retail.
- **Secondary Markets**: Odoo partners/integrators building vertical solutions on the framework.
- **Geographic Focus**: Global (~60 locales; `l10n_*` fiscal localisations available).
- **Market Size**: [To be determined]

## Competitive Landscape

- **Direct Competitors**: [To be determined] — commonly ERPNext, Dolibarr, SAP Business One, Dynamics 365 Business Central, NetSuite, Zoho.
- **Indirect Competitors**: Standalone CRM/quoting (Salesforce, HubSpot), accounting (QuickBooks, Xero), spreadsheets.
- **Key Differentiators**: LGPL-3 open core, app-by-app adoption, single integrated data model, large module ecosystem.
- **Competitive Advantages**: Low entry cost, extensibility via custom addons, self-hosting, built-in portal and payment providers.

## Key Personas

Personas derive from Odoo security groups. UAT persona role names (see `memory-bank/uat-config.md`) are used verbatim: **admin, user, portal, salesman, warehouse**.

| Group (XML id) | Display | Notes |
|---|---|---|
| `base.group_system` | Settings (Administration) | Full config |
| `base.group_user` | Internal User | Backend access |
| `base.group_portal` | Portal | Frontend `/my/*` only |
| `base.group_public` | Public | Anonymous / token links |
| `sales_team.group_sale_salesman` | Sales / User: Own Documents Only | Record rules: own (`user_id = user`) or unassigned docs |
| `sales_team.group_sale_salesman_all_leads` | Sales / User: All Documents | Sees all orders |
| `sales_team.group_sale_manager` | Sales / Administrator | Sales configuration + reports |
| `stock.group_stock_user` | Inventory / User | Implies Internal User |

### Primary Users

| Persona | Role | Goals | Pain Points | Success Metrics |
|---------|------|-------|-------------|-----------------|
| salesman | Sales / User: Own Documents Only | Create/send quotations, confirm orders, follow up own customers, trigger invoicing | Sees only own + unassigned orders; pricing accuracy; chasing acceptance | Quotes sent, quote→order conversion [targets TBD] |
| portal | Customer (Portal) | Review, sign and pay quotes; view orders/invoices at `/my/quotes`, `/my/orders` | Visibility depends on follower membership / access tokens | Time to accept/pay [TBD] |

### Secondary Users

| Persona | Role | Goals |
|---------|------|-------|
| user | Internal User without Sales rights | General backend use; verifies Sales menus/records are hidden |
| warehouse | Inventory / User | Validate deliveries from confirmed orders (needs `stock`/`sale_stock`) |
| Public visitor | Public | Open a quote via tokenised portal link |

### Administrators/Operators

| Persona | Role | Responsibilities |
|---------|------|------------------|
| admin | Settings + Sales Administrator | Install apps, manage users/groups, company/currency, payment providers, mail servers, Sales configuration (also covers the Sales Manager role for UAT) |
| Developer/Operator | Local docker operator | `docker compose up/watch`, DB management, module upgrades |

## User Flows

- **Primary Flow** (salesman): Sales → Quotations → New (customer, pricelist, products/template) → Send by Email (`sent`) → Confirm (`sale`) → [warehouse validates delivery, if Inventory installed] → Create Invoice (regular / down payment) → post & register payment.
- **Onboarding**: admin installs Sales (onboarding panel + `sale` tour), creates users and assigns groups; portal users invited via "Grant portal access".
- **Key Workflows**:
  - **Portal quote sign/pay** (portal): email link or `/my/quotes` → Accept & Sign (`/my/orders/<id>/accept`) and/or Pay (`/transaction`), or Decline with reason; order auto-confirms when requirements met.
  - **Pricelist/discount setup** (admin) → applied by salesman on quotes.
  - **Sales analysis**: Reporting → Sales Analysis (salesman limited to own data).
  - **Access-control check** (user): no access to Sales menus/records.
  - **Cancel / set back to quotation**.

## Success Metrics & KPIs

### Business Metrics
- Total sales — tracked in code via digest KPI `kpi_all_sale_total`.
- Quote → order conversion: [To be determined] (derivable from `sale.report`).
- Revenue targets: [To be determined] (`crm.team` invoiced target exists).

### Product Metrics
- [To be determined] — no product analytics instrumented in the fork.

### Technical Metrics
- Uptime/latency/error rate: [To be determined] (local dev only).
- All UAT persona journeys pass (`/bmb:uat`) against `http://localhost:8069`.

## Non-Functional Requirements

### Performance
- **Response Time / Throughput / Page Load**: [To be determined]
- **Concurrent Users**: [To be determined] — local dev runs threaded mode (no `workers` set).

### Scalability
- **Users**: dev only (~5 test personas); production [To be determined]
- **Data Volume / Growth / Peak Load**: [To be determined]

### Security
- **Authentication**: Odoo session login (`/web/login`, `session_id` cookie; logout `/web/session/logout`). Optional TOTP 2FA, OAuth, LDAP, API keys. Portal documents also reachable via `access_token` links.
- **Authorization**: RBAC via `res.groups` (implied-group hierarchy), model ACLs (`ir.model.access.csv`), row-level record rules (`ir.rule`) — salesman "Personal" rules, portal follower rules, multi-company rules.
- **CSRF**: enforced by default on `type='http'` POST routes.
- **Compliance**: [To be determined] — GDPR applies to EU personal data; PCI scope delegated to hosted payment providers.
- **Data Classification**: Confidential (customer PII, pricing, orders, invoices, payment tokens).
- **Encryption**: none in transit locally (plain HTTP :8069) — production needs TLS reverse proxy + `proxy_mode`. Passwords hashed (passlib pbkdf2).

### Availability & Reliability
- **Uptime / RTO / RPO / DR**: [To be determined] — N/A for local dev.
- **Backup Strategy**: [To be determined] — docker volumes `pg-data`, `odoo-filestore`; DB manager backup available.

### Data & Privacy
- **Data Residency**: local machine (docker volumes); production [To be determined].
- **Data Retention**: [To be determined]
- **PII Handling**: partner contact data, quote signatures, payment token references, chatter emails. UAT screenshots may contain test-account PII.
- **Right to Deletion**: [To be determined] — archive/delete subject to referential constraints.

### Accessibility
- **Target Compliance**: [To be determined] — no formal upstream WCAG commitment.
- **Key Requirements**:
  - [ ] Screen reader compatibility (partial ARIA in OWL client)
  - [ ] Keyboard navigation (Alt+key hotkeys exist)
  - [ ] Color contrast compliance
  - [ ] Focus indicators
  - [ ] Alt text for images

### Internationalization (i18n)
- **Supported Languages**: ~60 locales via gettext `.po` files per module; en_US source.
- **Localization Needs**:
  - [x] Currency formatting
  - [x] Date/time formatting
  - [x] Number formatting
  - [x] RTL support (rtlcss installed)
  - [ ] Fiscal localisation — none confirmed installed

### Browser/Platform Support
- **Browsers**: modern evergreen Chrome, Firefox, Safari, Edge [exact versions TBD]
- **Mobile**: responsive web client and portal (UAT mobile viewport 375×667)
- **Server**: Linux containers (python:3.12-slim, postgres:16); dev host Windows 11 + Docker Desktop

## Integration Points

### External Systems

| System | Purpose | Protocol | Direction |
|--------|---------|----------|-----------|
| Outgoing mail (SMTP) | Quotes, orders, invoices, portal invites, digests | SMTP (`ir.mail_server`) | Outbound |
| Incoming mail gateway | Chatter replies (`mail.alias`) | IMAP/POP or MTA | Inbound |
| Payment providers | Portal online payment / prepayment | Provider APIs + webhooks | Both |
| Odoo IAP | Paid services (SMS, autocomplete, …) if enabled | HTTPS JSON-RPC | Outbound |
| PostgreSQL 16 | Primary datastore | libpq | Both |

### APIs Provided

| API | Purpose | Consumers |
|-----|---------|-----------|
| XML-RPC / JSON-RPC (`/xmlrpc/2/*`, `/jsonrpc`, `/web/dataset/call_kw`) | Generic ORM access (ACL/rule enforced) | Web client, integrations |
| Portal routes (`/my/quotes`, `/my/orders/<id>`, `/accept`, `/decline`, `/transaction`) | Customer self-service | Portal users / token links |
| Payment webhooks (`/payment/<provider>/webhook`) | Provider notifications | Payment providers |

## Constraints & Assumptions

### Business Constraints
- Community edition only (no Studio, Sign, Subscriptions, etc.).
- LGPL-3 obligations for distributed modifications.
- Budget / timeline / resources: [To be determined].

### Technical Constraints
- Odoo 18.0, Python 3.12, PostgreSQL 16, docker compose locally on port 8069.
- Never modify core (`odoo/`) or standard `addons/`; customisations go in separate custom addons. `addons_path` does not yet include a custom-addons directory.
- `dev_mode = reload` + `develop.watch` give live reload; data/schema changes still need `-u <module>`.

### Assumptions
- `sale_management` (+ `sale`, `sales_team`) is installed in `odoo-dev` — **verified 2026-10-20**.
- UAT accounts exist with the groups mapped in `uat-config.md` — **not yet created** (only `admin` exists by default).
- Inventory (`stock` / `sale_stock`) will be installed for the warehouse persona — unconfirmed.
- Outgoing mail not configured locally — [To be determined].

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Weak dev secrets (master password, db creds, DB manager enabled) reaching a shared/prod deploy | Medium | High | Separate prod config, strong master password, `list_db = False`, TLS + `proxy_mode` |
| New internal users may inherit Sales Administrator via `base.default_user` | Medium | Medium | Set groups explicitly for UAT personas; verify in UAT |
| Warehouse persona unusable without Inventory / `sale_stock` | High | Medium | Install `sale_stock` or drop warehouse flows from UAT |
| Core edits make upstream 18.0 merges hard | Medium | High | Keep all custom code in custom addons |
| No mail / payment provider locally — send/pay flows untestable | High | Low | Use `payment_demo` + a mail catcher (e.g. MailHog) |
| Working copy on OneDrive interferes with docker watch | Medium | Low | Move outside OneDrive or exclude from sync |

## Open Questions

- [ ] Is Inventory (`stock` / `sale_stock`) to be installed for the warehouse persona?
- [ ] Was demo data loaded in `odoo-dev`?
- [ ] Where will custom addons live, and how are they added to `addons_path`?
- [ ] Target production / hosting environment and its SLA, backup, TLS needs?
- [ ] Which payment providers and mail servers are in scope?
- [ ] Business KPIs and targets?
- [ ] Accessibility / GDPR commitments?

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2026-10-20 | Claude (/bmb:init) | Initial creation |
| 2026-10-20 | Claude (/bmb:init re-run) | Refreshed: Sales focus, persona map aligned with uat-config.md, verified Sales install |

## Last Refreshed

2026-10-20
