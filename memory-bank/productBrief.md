# Product Brief

> This document captures the **product and project context** for development teams.
> It ensures all agents understand the product's purpose, users, constraints, **and the project's foundation**.

## Project Foundation

- **Project Name**: odoo (fork `github.com/DaKaZ/odoo`, branch `banyan`)
- **Objectives**: [To be determined — confirm with owner]. The only fork commit is `8a9ce028 local docker setup`, which adds a Docker-based local development environment.
- **Scope**: Upstream Odoo 18.0 Community source, unmodified apart from the Docker setup. Fork purpose (custom modules / evaluation / test bed) is [To be determined].
- **Key Stakeholders**: Upstream: Odoo S.A. Fork owner: DaKaZ. Others [To be determined].

### Repository Structure
- **Type**: Poly-repo (single application with a plugin-style module system — not a workspace-tool mono-repo)
- **Workspace Tool**: None
- **Workspace Root**: N/A
- **Layout**: `odoo/` (core framework + `odoo/addons/base` + framework test modules); `addons/` (621 business modules, 120 `l10n_*` prefixes); `setup/`, `debian/` (packaging); `doc/`; `docker/` (fork config); `odoo-bin` (entry point); `requirements.txt`.

## Git Configuration
- **Repository**: Yes
- **Provider**: GitHub
- **CLI Available**: gh (authenticated)
- **Remote URL**: https://github.com/DaKaZ/odoo.git
- **Default Branch**: banyan (only branch; no `main`)
- **Metadata Branch**: banyan
- **Routing Mode**: classic
- **Sync Automation**: none
- **Archive Strategy**: push-and-pr

## Product Overview

- **Name**: Odoo Server 18.0 (final)
- **Value Proposition**: "A suite of web based open source business apps" — standalone apps that combine into a full ERP/CRM for SMB and mid-market companies.
- **Product Type**: Self-hostable web ERP/CRM platform and modular application framework (Python + PostgreSQL). Community edition, LGPL-3.
- **Stage**: Mature / GA (Production/Stable). SECURITY.md lists 16.0, 17.0, 18.0 as supported.

## Key Functionality

- **CRM & Sales**: `crm`, `sale`, `sale_management`, `sales_team`, margins, loyalty, product matrix, IAP lead enrichment.
- **Accounting & Finance**: `account`, `analytic`, `account_payment`, EDI (UBL/CII, Peppol), check printing, QR payments, tax tools.
- **Inventory & Supply Chain**: `stock`, `stock_account`, landed costs, dropshipping, batch picking, `purchase`, `purchase_requisition`, `delivery`.
- **Manufacturing**: `mrp`, subcontracting, `mrp_account`, `repair`, `maintenance`, product expiry.
- **HR**: `hr`, attendance, leave, contracts, expenses, recruitment, skills, timesheets, work entries, fleet, lunch (no Payroll in Community).
- **Project & Services**: `project`, `project_todo`, `sale_timesheet`, `sale_project`.
- **Website & eCommerce**: `website`, `website_sale`, blog, forum, eLearning, events, jobs, live chat.
- **Point of Sale**: `point_of_sale`, `pos_restaurant`, `pos_self_order`, payment terminals, IoT drivers (`hw_*`).
- **Marketing**: `mass_mailing`, SMS, events, surveys, `link_tracker`, `marketing_card`.
- **Productivity & Platform**: Discuss (`mail`, `bus`), calendar, spreadsheet dashboards, `base_automation`, `base_import`, `data_recycle`, `privacy_lookup`.

## Markets Serviced

- **Primary Market**: Cross-industry SMB and mid-market (distribution, manufacturing, services, retail, hospitality).
- **Secondary Markets**: Non-profits (`membership`), events, education/eLearning, restaurants.
- **Geographic Focus**: Global — 120 `l10n_*` prefixes (~110 countries plus regional packs: EU, GCC, LATAM, OHADA, ANZ).
- **Market Size**: [To be determined]

## Competitive Landscape

- **Direct Competitors**: [To be determined] — commonly SAP Business One, Dynamics 365 Business Central, NetSuite, ERPNext, Sage, Zoho One.
- **Indirect Competitors**: [To be determined] — best-of-breed SaaS (Salesforce, HubSpot, Shopify, QuickBooks/Xero).
- **Key Differentiators**: Open-source LGPL core; modular apps on one shared data model; very broad localization.
- **Competitive Advantages**: [To be determined]

## Key Personas

### Primary Users

| Persona | Role | Goals | Pain Points | Success Metrics |
|---------|------|-------|-------------|-----------------|
| Internal User | `base.group_user` | Run daily operations in installed apps | [To be determined] | [To be determined] |
| App User | e.g. `sales_team.group_sale_salesman`, `account.group_account_invoice`, `stock.group_stock_user`, `mrp.group_mrp_user` | Role-specific work (quotes, invoices, picks, MOs) | [To be determined] | [To be determined] |
| App Manager | e.g. `group_sale_manager`, `group_account_manager`, `stock.group_stock_manager` | Configure, approve, report | [To be determined] | [To be determined] |

### Secondary Users

| Persona | Role | Goals |
|---------|------|-------|
| Portal User | `base.group_portal` | View/pay invoices, sign quotes, follow orders/projects |
| Public Visitor | `base.group_public` | Browse website, shop, register for events |
| POS Cashier | POS user group | Process in-store / restaurant sales |

### Administrators/Operators

| Persona | Role | Responsibilities |
|---------|------|------------------|
| Settings Admin | `base.group_system` | System settings, technical config, modules |
| Access Rights Admin | `base.group_erp_manager` | Users, groups, companies |
| DB / Server Operator | holder of `admin_passwd` | Create/backup/restore databases, deploy |

## User Flows

- **Primary Flow**: Lead → Opportunity → Quotation → Sales Order → Delivery / Manufacturing Order → Invoice → Payment → Reconciliation.
- **Onboarding**: Create DB via database manager → install apps → configure company + localization (chart of accounts) → invite users.
- **Key Workflows**: Procure-to-pay (RFQ → PO → Receipt → Bill → Payment); eCommerce (cart → online payment → order → delivery); POS session (open → sell → close → accounting); HR (recruitment → employee → timesheets/leave → expenses); Project (task → timesheet → invoice).

## Success Metrics & KPIs

### Business Metrics
- [To be determined]

### Product Metrics
- [To be determined]

### Technical Metrics
- [To be determined]

## Non-Functional Requirements

### Performance
- **Response Time**: [To be determined] — default `limit_time_real=120s` per request.
- **Throughput**: [To be determined] — prefork via `--workers` (default 0 = threaded), `max_cron_threads=2`.
- **Concurrent Users**: [To be determined] — real-time bus/websocket on gevent worker (`gevent_port` 8072).
- **Page Load Time**: [To be determined] — bundled assets, OWL web client.

### Scalability
- **Users / Data Volume / Growth / Peak Load**: [To be determined]. Horizontal scaling via workers and multiple instances behind a proxy on one PostgreSQL; attachments in filestore (optional Azure/GCS cloud storage).

### Security
- **Authentication**: Password (passlib), TOTP 2FA (`auth_totp*`), passkeys (`auth_passkey`), OAuth (`auth_oauth`), LDAP (`auth_ldap`), API keys, `auth_signup`.
- **Authorization**: RBAC via `res.groups` + model ACLs (`ir.model.access.csv`), record rules (`ir.rule`), multi-company rules, field-level `groups=`; CSRF on POST routes; HTML sanitization.
- **Compliance**: [To be determined] — GDPR tooling exists (`privacy_lookup`, `data_recycle`).
- **Data Classification**: [To be determined] — handles PII, financial, HR data.
- **Encryption**: In transit via reverse proxy/TLS (not configured in the fork). At rest: [To be determined].

### Availability & Reliability
- **Uptime / RTO / RPO / DR**: [To be determined]
- **Backup Strategy**: [To be determined] — built-in DB manager dump/restore; Docker data in `pg-data` + `odoo-filestore` volumes.

### Data & Privacy
- **Data Residency / Retention / Privacy Requirements**: [To be determined]
- **PII Handling**: PostgreSQL + filestore; `privacy_lookup` locates/erases a person's records.
- **Data Portability**: Export, `base_import`, XML-RPC/JSON-RPC.

### Accessibility
- **Target Compliance**: [To be determined]
- **Key Requirements**:
  - [ ] Screen reader compatibility
  - [ ] Keyboard navigation (web client hotkeys exist)
  - [ ] Color contrast compliance
  - [ ] Focus indicators
  - [ ] Alt text for images
  - [ ] Captions for video/audio

### Internationalization (i18n)
- **Supported Languages**: ~58 catalogs in `addons/web/i18n`; translations via Transifex/Weblate.
- **Localization Needs**:
  - [x] Currency formatting (multi-currency)
  - [x] Date/time formatting
  - [x] Number formatting
  - [x] RTL support (rtlcss; ar, he, fa)
  - [x] Cultural considerations (~110 country packs)

### Browser/Platform Support
- **Browsers**: Modern evergreen browsers.
- **Mobile**: Responsive web client / PWA.
- **Server**: Linux/Windows/macOS; fork uses `python:3.12-slim` + Postgres 16.

## Integration Points

### External Systems

| System | Purpose | Protocol | Direction |
|--------|---------|----------|-----------|
| PostgreSQL 16 | Primary datastore | libpq | Both |
| Mail servers | Outgoing mail + incoming gateway (`mail`, `fetchmail`) | SMTP/IMAP | Both |
| Google / Microsoft 365 | Calendar sync, OAuth mail | REST/OAuth2 | Both |
| Payment providers | Adyen, Stripe, PayPal, Mollie, Razorpay, Mercado Pago, … | REST + webhooks | Both |
| POS terminals | Adyen, Stripe, Six, Viva Wallet, … | REST / IoT | Both |
| Peppol | E-invoicing via Odoo EDI proxy | Proxy/AS4 | Both |
| Odoo IAP | Enrichment, SMS, snailmail, autocomplete | JSON-RPC | Outbound |
| Cloud storage | Azure Blob, GCS attachments | REST | Outbound |

### APIs Consumed

| API | Provider | Purpose |
|-----|----------|---------|
| IAP services | Odoo S.A. | Enrichment, SMS credits |
| OAuth2 / OIDC | Google, Microsoft, others | SSO |
| LDAP | Corporate directory | Authentication |

### APIs Provided

| API | Purpose | Consumers |
|-----|---------|-----------|
| XML-RPC (`/xmlrpc/2/common`, `/xmlrpc/2/object`) | External ORM access | Integrations, scripts |
| JSON-RPC (`/jsonrpc`, `/web/dataset/call_kw`) | Web client + external access | Web client, integrations |
| HTTP controllers / website routes | Web, portal, webhooks | Browsers, payment providers |
| Websocket bus (`/websocket`) | Real-time notifications, Discuss | Web client |

### Data Sources

| Source | Type | Frequency |
|--------|------|-----------|
| PostgreSQL | Database | Real-time |
| Filestore (`/var/lib/odoo`) | File | Real-time |
| Incoming mail | Mail gateway | Batch (cron) |
| CSV/XLSX import | File | On demand |

## Constraints & Assumptions

### Business Constraints
- Fork purpose, goals and timeline: [To be determined — confirm with owner].
- Community/LGPL only — Enterprise features (Studio, Payroll, most carriers, Helpdesk) unavailable.

### Technical Constraints
- Python 3.12, PostgreSQL 16, Node/rtlcss/less for assets.
- Docker setup is dev-only: `dev_mode=reload`, Compose Watch on `addons/` + `odoo/`, port 8069 only, threaded mode (no websocket port).
- Working tree lives in OneDrive: very large file count makes filesystem scans and sync slow.

### Assumptions
- The fork tracks upstream 18.0 closely; upstream remote and sync strategy [To be determined].
- Customizations should live in separate modules rather than patching core. [To be confirmed]
- Used for local development/evaluation, not production.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Weak dev credentials committed in `docker/odoo.conf` | High | High if exposed | Never deploy this config; use secrets; `list_db=False` in prod |
| Fork drifts from upstream 18.0 security fixes | Medium | High | Regularly merge from odoo/odoo 18.0 |
| Core modifications complicate upgrades | Medium | High | Keep customizations in separate modules |
| Dev config mistaken for production-ready | Medium | Medium | Separate prod config (workers, proxy_mode, TLS) |
| OneDrive sync conflicts on git tree | Medium | Medium | Move repo off synced folder |
| Unclear fork purpose/scope | High | Medium | Confirm with owner |

## Open Questions

- [ ] What is the purpose of the `banyan` fork?
- [ ] Which apps and localizations are in scope?
- [ ] Is there a production deployment target (SLA, backup, hosting)?
- [ ] Upstream sync policy and target Odoo version?
- [ ] Are Enterprise or OCA addons planned?

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2026-10-20 | /bmb:init | Initial creation (brownfield exploration) |

## Last Refreshed

2026-10-20
