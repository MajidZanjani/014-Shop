# Synaptic Laboratories IP Shop

## What This Is

One configurable semiconductor-IP shop for engineers evaluating IP and buyers purchasing a reviewed licence scope. Static product discovery and configuration lead to trial/technical/quote inquiries, accepted-quote payment, explicitly approved direct offers, and tracked manual delivery with private downloads. Staff manage these journeys through MFA-protected browser workflows.

## Core Value

Turn a reviewed IP configuration into an attributable agreement, verified payment and authorized delivery without losing commercial evidence or duplicating financial/licence effects.

## Business Context

- **Customer**: Engineering evaluators and licensed organizations; SLL staff review and fulfil orders.
- **Revenue model**: One approved licence scope per configured line, quantity 1; quote-led sales and approved direct offers.
- **Success metric**: A complete verified quote-to-delivery journey with recoverable acceptance/payment/document/grant evidence; no numerical sales target supplied.
- **Strategy notes**: Root proposal and handoff dated 2026-10-19.

## Requirements

### Validated

(None yet — no application exists; the supplied audit is evidence, not shipped functionality.)

### Active

- [ ] Preserve the complete source audit and separate proposed/approved source-to-shop changes.
- [ ] Make Markdown the catalog authority with strict contracts and matching browser/server rules.
- [ ] Deliver accessible static discovery/configuration and durable trial/quote inquiry journeys.
- [ ] Protect guest resources and staff workflows with scoped sessions and mandatory staff MFA.
- [ ] Freeze quote/order/terms evidence and compute authoritative money.
- [ ] Handle payments, manual fulfilment and financial documents durably and idempotently.
- [ ] Prepare isolated publication, backups, financial recovery and evidence-led release readiness.

Detailed testable scope: REQUIREMENTS.md. Task dependencies and acceptance: ROADMAP.md and original handoff T01–T14.

### Out of Scope

- Automated licence generation, subscriptions/renewals, saved cards, FX/multiple live currencies, complex promotions and organization accounts — explicitly excluded v1.
- Additional purchasable services, marketing analytics, customer uploads, service workers, full WordPress/historical Monday migration — require later scope.
- Redis/Celery, CMS, proprietary identity/analytics SaaS, SSR/runtime Astro/Node — outside the selected architecture.

## Context

Read both source documents completely (299 + 1789 lines), including appendices A–C. They define future work, not implemented or tested services. Reuse 53 unique field records, 16 ordered lists/127 options, 242 country/phone rows and nine exercised branch predicates; untested server validation and memory re-add retention remain unverified. Preserve stable source/shop/change-set IDs and all F-01–F-14 mappings. Shop changes remain pending approval; planning is not commercial approval.

Repository initially contains README and the two source documents, no application or existing GSD project. Source hashes and the canonical D-01–D-09 register are retained under .planning/SOURCES.md and docs/decisions.md. No broad source re-audit is needed. Current dependency/price/OS facts must be verified during their implementation tasks; this planning pass reuses supplied research and does not revalidate its external claims.

## Constraints

- **Architecture**: Static Astro + selected React islands; Django/Gunicorn + PostgreSQL; one leased DB outbox worker. Django owns /inquiry/simple/.
- **Authority**: Ordinary Markdown/YAML compiles immutable public/private revisions. Admin cannot create a competing mutable catalog. Backend owns validation, pricing, permission and payment decisions.
- **Commercial**: One English product and one activated currency; actual SKU/release/prices/seller/tax/bank/terms unknown. Default valid configuration is awaiting_review, null price and disabled live purchase. Safety selections request requirements, not certifications.
- **Profiles**: Immutable sll-trial-form-2026-10-19; proposed sll-shop-form-v1; pending sll-source-to-shop-v1. Protected approval records authorize production changes; editable frontmatter cannot approve itself.
- **Financial safety**: Archive recoverable snapshots before bank operations, document issuance or delivery activation. Keep prepared/completed evidence separate. An uncertain outcome cannot authorize a second charge.
- **Isolation**: Proposed separate new OVH VM with native NixOS/systemd, public GRA objects and private off-region SBG evidence/backups. Existing dedicated services stay outside the task boundary. Customer/staff hostnames are proposed, not deployed.
- **Recovery**: Proposed 15-minute DB RPO and four-hour restore after operator start; measure full outage and bank-dependent reopening separately. VM/Caddy remains a shared availability dependency.
- **Evidence**: Real PostgreSQL for locks; distinguish synthetic/fake bank, selected-bank sandbox, actual OVH and production proof. No invented acceptance, legal, compatibility or vendor guarantees.
- **Authorization**: Current instruction authorizes reading and planning. Implementation and external provisioning/cutover/mail/payment operations are not performed by this planning task.
- **Estimate**: Supplied full scope 40–65 engineer-days, scoped tests included, excluding external waiting/legal work. Supplied hosting estimate is historical planning input, not a current account quote.

## Key Decisions

| Decision | Rationale | Outcome |
|---|---|---|
| Adopt the supplied Django/static Astro architecture for planning | IP-specific commercial and fulfilment workflows dominate retail features | Proposed baseline from sources |
| Quote-led v1 plus approved direct offers | Scope/rights/pricing need explicit review | Proposed baseline from sources |
| Preserve T01–T14 as draft roadmap phases | Retains acceptance/evidence traceability and actual dependencies | Retained by user on 2026-10-19 |
| Reuse dated audit and research | Explicit source direction avoids redundant investigation | Sources read; no new live audit |
| Separate local progress from external proof | Missing bank/legal/cloud inputs block only affected capabilities | Required source boundary |

## Evolution

At each phase transition, update validated/active/out-of-scope requirements, record decisions and review this description. At milestone boundaries, review core value, scope, business context and operational reality. Preserve source evidence and append decisions rather than rewriting historical approval.

---
*Last updated: 2026-10-19 after initialization; user selected autonomous, 14 phases, parallel execution, commit and sync.*
