# SHB release requirements

Current authority: [SHB revision 1.1](../014-Shop-SHB-Proposal-Revision-2026-10-30.md), SHA256 `ba801dff4adbfdcfa0f1e43cfe1f2d6963780476867da1b5e6f737230a472b5e`. The user explicitly replaces the earlier active product plan on 2026-10-30. Current routing: [STATE.md](STATE.md) / [ROADMAP.md](ROADMAP.md).

STATE.md and ROADMAP.md own current status. No SHB criterion is complete merely because earlier code/tests exist.

- [ ] **SHB-01**: Load active shop with valid access — Exactly one product and the two exact requested variant labels.
- [ ] **SHB-02**: Visit old IP route or submit old IP SKU — No new IP sale; existing orders/history and contractual obligations remain intact.
- [ ] **SHB-03**: FPGA quantity 1 and 3 — 10/30 hours and authoritative matching prices.
- [ ] **SHB-04**: ASIC quantity 1 and 2 — 25/50 requested hours and Submit Request; no initial payment or completed purchase.
- [ ] **SHB-05**: Invalid quantity, forged price/hours/discount/customer ID — Backend rejects or derives trusted values; no bypass.
- [ ] **SHB-06**: Common form, same-phone choice, conditional tax fields — All six requested fields supported with minimal repetition; no unrelated engineering dossier.
- [ ] **SHB-07**: Eligible FPGA purchase and later top-up — No routine engineer approval; each accepted paid order records its own purchased hours once and is available to staff; no online balance update.
- [ ] **SHB-08**: Unapproved ASIC checkout/API; altered approved scope — Payment blocked; material change requires a new matching approval/offer.
- [ ] **SHB-09**: ASIC approve / clarify / decline / withdraw — Correct state, customer notice and discount reservation treatment; no completed purchase before accepted verified payment.
- [ ] **SHB-10**: Base URL, deep links, static JSON/assets, origin, alternate host — No protected shop data without valid access; no public-origin bypass.
- [ ] **SHB-11**: Invalid/revoked/expired token or surviving browser cookie — Denied using server state, including the next request after revocation.
- [ ] **SHB-12**: Exactly at expiry, month-end and leap year — Correct six-calendar-month rule; no restart from visits or browser-clock changes.
- [ ] **SHB-13**: Valid link reused / scanned by email software — Reuse allowed; GET has no commercial/message side effects.
- [ ] **SHB-14**: Token leakage, caching, different customers and changed contact email — No raw token in normal logs/referrers/bank URLs; no shared-cache or cross-customer/private-data exposure; entering an email does not replace the company's authorized contact.
- [ ] **SHB-15**: Coupon wrong customer/variant, expired, revoked or stacked — Rejected server-side; no access/approval bypass.
- [ ] **SHB-16**: Concurrent one-use coupon claims — At most one live reservation/redemption; Apply alone consumes none.
- [ ] **SHB-17**: ASIC submitted before coupon expiry, reviewed afterward — Discount reservation survives SLL review and appears in the dated offer.
- [ ] **SHB-18**: Declined/withdrawn/expired unpaid offer — Reservation released under policy without extending claim expiry; uncertain payments reconciled first.
- [ ] **SHB-19**: Forged browser success or unauthenticated bank callback — No paid status, accepted purchase or paid-order confirmation.
- [ ] **SHB-20**: Duplicate/out-of-order bank messages and process interruption — Correct final bank/order state, one order finalization, one coupon redemption and repeat-safe transaction notifications carrying the same order reference.
- [ ] **SHB-21**: Uncertain payment dispatch or duplicate real payment — Reconcile; no blind second charge or duplicate purchase; staff can identify the original order.
- [ ] **SHB-22**: Payment notification or ASIC review after invitation expiry — Existing work reconciles/continues; no new checkout through expired access.
- [ ] **SHB-23**: Temporary transaction-mail failure — Order/payment/coupon state retained; paid order remains visible to staff and notification retries do not create a second purchase.
- [ ] **SHB-24**: Manual support-tracking boundary — No online time-ledger mutation, available/used/remaining-hour calculation, support/bundle panel or API, staff time-entry workflow or automated task-usage email. Purchased-hours display remains per order.
- [ ] **SHB-25**: Refund/chargeback with unused or consumed hours — Financial change linked to original order; staff consult manual usage records where needed and inform the support team; no automated time adjustment or erased financial history.
- [ ] **SHB-26**: Invite expires with unused purchased hours — Purchased support remains valid under its terms; support team continues manual tracking and task emails independently.
- [ ] **SHB-27**: JavaScript unavailable; keyboard/mobile flow — Same backend access, price, validation and approval rules; usable forms and clear errors.
- [ ] **SHB-28**: Restore/replay within existing recovery qualification — Invitations retain original expiry/revocation; reconcile post-backup financial/order/coupon events before reopening; preserve order references so staff do not count a replay as a new purchase.
- [ ] **SHB-29**: Missing rates/policies/provider authority — Affected live action fails closed; local implementation still runs with explicit synthetic data.
- [ ] **SHB-30**: Deployment review — All protected existing services unchanged; required isolated/off-host qualification retained.

## Retained shared controls

Existing October21 protection/security/financial/recovery requirements remain binding where relevant. Preserve Stalwart, WebAdminProxy, Plesk/WordPress, existing PostgreSQL, Prometheus, Grafana/Grafana-TLS, Blackbox, Alertmanager, MicroVMs, NetBird, Matrix and every pre-existing/uncertain resource in every state. No blanket NixOS activation, protected reload/restart/edit/prune/GC/upgrade/reboot, firewall/DNS/TLS change, real bank/mail action or paid fallback. Inventory all owners/resources read-only, maintain docs/host-protection-inventory.md and docs/shop-resource-allowlist.md, separate database identity and complete activation-impact review before any authorized shop write. Rootless shopsvc directly on mx1, outside claude-dev; one leased worker, independent PostgreSQL, internal Caddy. Proposed host-controlled aggregate 200% CPU, 6G high/8G max, bounded tasks; preserve cpusets/parents/guests. Proposed 80 GiB aggregate ZFS including snapshots/descendants, 50 GiB DB including WAL; account GraphRoot/images/volumes/temp/logs/certificates/spool/backups. Private gra release storage and independent sbg recovery custody; no new production compute/block/IP rental. No host process/control/management mounts in apps. Independent runtime/fault/exhaustion/complete-loss drills require an assigned authorized off-host runner; none is assigned. Production/bank-sandbox database connection gate stays closed until actual identity/all-write/transport/migration/runtime qualification. Prepared evidence is not completion; archive recoverable accepted/order/payment/document effects before use; uncertain bank dispatch cannot authorize a blind retry.

Retain input validation, resource/contact authorization, recent staff MFA, CSRF/origin/host checks, privacy/log redaction, immutable approved money/terms/acceptance, positive database identity/all-write/migration guards, durable outbox/leases, archive-before-effects, exact provider correlation, uncertainty/reconciliation and financial refund history. AUTH-01 deliberate single-use mailbox verification remains for retained private resources; invitations are separately reusable bearer access.

## Previous requirement disposition

| ID | SHB disposition |
|---|---|
| SRC-05 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| FLOW-01 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| FLOW-02 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| FLOW-03 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| FLOW-04 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| FLOW-05 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| FLOW-06 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| FLOW-07 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| FLOW-08 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| SRC-01 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| SRC-02 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| SRC-03 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| SRC-04 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| BUILD-01 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| BUILD-02 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| BUILD-03 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| BUILD-04 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| BUILD-05 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| BUILD-06 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| BUILD-07 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| BUILD-08 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| CAT-01 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| CAT-02 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| CAT-03 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| CAT-04 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| CAT-05 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| SHOP-01 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| SHOP-02 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| SHOP-03 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| SHOP-04 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| SHOP-05 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| DATA-01 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| DATA-02 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| DATA-03 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| DATA-04 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| AUTH-01 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| AUTH-02 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| AUTH-03 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| AUTH-04 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| AUTH-05 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| AUTH-06 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| COM-01 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| COM-02 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| COM-03 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| COM-04 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| COM-05 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| COM-06 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| PAY-01 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| PAY-02 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| PAY-03 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| PAY-04 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| PAY-05 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| BANK-01 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| BANK-02 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| BANK-03 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| BANK-04 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| FUL-01 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| FUL-02 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| FUL-03 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| FUL-04 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| FUL-05 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| FUL-06 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| HOST-01 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| HOST-02 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| HOST-03 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| HOST-04 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| HOST-05 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| HOST-06 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| HOST-07 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| HOST-08 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| HOST-09 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| OPS-01 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| OPS-02 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| OPS-03 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| OPS-04 | Deferred IP/time-accounting scope; original evidence/contracts preserved, no dedicated SHB launch gate |
| OPS-05 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| OPS-06 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| OPS-07 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| OPS-08 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| UAT-01 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| UAT-02 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| UAT-03 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| UAT-04 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| UAT-05 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| REL-01 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| REL-02 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| REL-03 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| REL-04 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |
| REL-05 | Retained shared control, re-scoped to SHB; original text/evidence preserved in archive; no new approval inferred |

SHB records only bundle size, quantity and hours bought in each order. SLL manually tracks used/remaining FPGA/ASIC hours and manually emails each task outside the shop. Preserve historical code/data/accepted obligations. Automated time credits/debits/reservations, cumulative balances, customer support/bundle panels/APIs, staff time entry and task-usage-email generation are deferred and are not SHB launch dependencies.

## Traceability

| Requirement | Primary phase | Status |
|---|---|---|
| SHB-01 | Phase 3 | Pending revised evidence |
| SHB-02 | Phase 4 | Pending revised evidence |
| SHB-03 | Phase 3 | Pending revised evidence |
| SHB-04 | Phase 3 | Pending revised evidence |
| SHB-05 | Phase 3 | Pending revised evidence |
| SHB-06 | Phase 4 | Pending revised evidence |
| SHB-07 | Phase 10 | Pending revised evidence |
| SHB-08 | Phase 7 | Pending revised evidence |
| SHB-09 | Phase 7 | Pending revised evidence |
| SHB-10 | Phase 4 | Pending revised evidence |
| SHB-11 | Phase 6 | Pending revised evidence |
| SHB-12 | Phase 4 | Pending revised evidence |
| SHB-13 | Phase 6 | Pending revised evidence |
| SHB-14 | Phase 6 | Pending revised evidence |
| SHB-15 | Phase 7 | Pending revised evidence |
| SHB-16 | Phase 7 | Pending revised evidence |
| SHB-17 | Phase 7 | Pending revised evidence |
| SHB-18 | Phase 7 | Pending revised evidence |
| SHB-19 | Phase 8 | Pending revised evidence |
| SHB-20 | Phase 8 | Pending revised evidence |
| SHB-21 | Phase 8 | Pending revised evidence |
| SHB-22 | Phase 8 | Pending revised evidence |
| SHB-23 | Phase 10 | Pending revised evidence |
| SHB-24 | Phase 10 | Pending revised evidence |
| SHB-25 | Phase 10 | Pending revised evidence |
| SHB-26 | Phase 10 | Pending revised evidence |
| SHB-27 | Phase 4 | Pending revised evidence |
| SHB-28 | Phase 12 | Pending revised evidence |
| SHB-29 | Phase 14 | Pending revised evidence |
| SHB-30 | Phase 11 | Pending revised evidence |
