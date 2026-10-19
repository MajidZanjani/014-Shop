<!-- GSD:project-start source:PROJECT.md -->

## Project

**Synaptic Laboratories IP Shop**

One configurable semiconductor-IP shop for engineers evaluating IP and buyers purchasing a reviewed licence scope. Static product discovery and configuration lead to trial/technical/quote inquiries, accepted-quote payment, explicitly approved direct offers, and tracked manual delivery with private downloads. Staff manage these journeys through MFA-protected browser workflows.

**Core Value:** Turn a reviewed IP configuration into an attributable agreement, verified payment and authorized delivery without losing commercial evidence or duplicating financial/licence effects.

### Constraints

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

<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->

## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `$gsd-fast` for a trivial task inline, with no subagents and no PLAN.md
- `$gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `$gsd-debug` for investigation and bug fixing
- `$gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `$gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
