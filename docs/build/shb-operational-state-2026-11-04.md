# SHB operational state — per-file synthetic-vs-real-path inventory (2026-11-04)

Amendment 2026-11-04 §5 identifies seven SHB source files that currently
operate on synthetic fixtures only. This document inventories, per file,
the exact internal guards that keep each file fake-only, and the specific
external input required to lift each guard. Provider-independent portions
that can advance locally now are called out separately per file.

**Scope:** `backend/shop/shb/{catalog, checkout, invitations, views,
services, models, transaction_mail}.py` at HEAD `e3cd133` (R7 closure).

**Not covered here** (R9 — external gates, not closable by this
project): the authorized independent off-host runner; pinned Nix /
source / runtime / native / licence / OCI / CI qualification; actual
commercial / provider / refund / tax / mail / host / ingress / database
/ human / independent-custody / post-backup / transport / restore /
complete-loss qualification; production / bank-sandbox database
connection gate.

**Preservation posture:** no code change by this document. The
production invitation / discount / order / payment / mail machinery
already exists and is already locally verified (558-test SHB shared
lane, 161 browser checks at the retained 9-file private Astro release);
the gates below are the small set of external inputs needed to lift
"synthetic fixture only" into "approved live operation" without
rewriting the application.

---

## 1. `backend/shop/shb/catalog.py`

Per-order pricing and the policy-shape validator. 74 lines.

### Guards keeping it fake-only

| # | Line | Guard | Purpose |
|---|---|---|---|
| 1.1 | `catalog.py:24-31` | `def synthetic_offer():` returning `revision='synthetic-shb-offer-v1'`, `evidence_class='local-synthetic'`, EUR currency, synthetic hourly/tax/bank bounds and all five `synthetic-shb-{terms,privacy,refund,asic-supplement,manual-time}-v1` policy revisions. Docstring: "Deliberately artificial local test values, never selected for live use." | The only offer shape that currently prices a local demo. |
| 1.2 | `catalog.py:45-46` | `quote()` returns `live_payable=False`, `evidence_class='unapproved'`, `status='price_to_be_confirmed'` when `offer is None`. | A null-offer quote is deliberately unpayable. |
| 1.3 | `catalog.py:52` | `require(type(offer) is dict and set(offer)==set(synthetic_offer()))` | Refuses any offer shape that isn't the exact synthetic fixture. |
| 1.4 | `catalog.py:53-55` | `require(offer['evidence_class']=='local-synthetic' and offer['revision']=='synthetic-shb-offer-v1' and offer['currency']=='EUR')` | Explicit synthetic-only accept-list. |
| 1.5 | `catalog.py:62-63` | `require(... offer[key].startswith('synthetic-'))` for `terms_revision`, `privacy_revision`, `refund_revision`, `asic_supplement_revision`, `manual_charging_policy_revision`. | Forces every policy revision identifier to start with `synthetic-`. |
| 1.6 | `catalog.py:74` | Priced output sets `evidence_class='local-synthetic'`, `status='synthetic_estimate'` or `'synthetic_review'`. | Marks the resulting quote as fixture-only. |

### Exact external input required to lift

An approved commercial-adoption record containing:

- Approved base FPGA and ASIC hourly rate, expressed as positive integer
  minor units of a specific currency, with declared bounds that satisfy
  `asic_hourly_minor > fpga_hourly_minor`.
- Approved tax rate in basis points (integer; `0 <= tax_bps <= 100000`).
- Approved rounding mode (currently `'half-up'` is the only accepted
  value — adoption can preserve it or add alternatives).
- Approved bank-payment bounds `bank_min_minor` and `bank_max_minor`,
  provided by the selected bank provider; these constrain every real
  checkout total.
- Non-synthetic identifiers for each of the five policy revisions:
  `terms`, `privacy`, `refund`, `asic_supplement`,
  `manual_charging_policy`. These come from the approved legal /
  operational policy custody record and would replace the current
  `synthetic-*-v1` strings.

Who provides each: SLL commercial (rates, tax, policies); selected bank
(bounds); approved legal review (terms / privacy / refund / asic
supplement / manual charging policy identifiers).

### Provider-independent portions (ready now, no external input needed)

- Shape validation, type guards, bounds checks (`MAX_QUANTITY`,
  `MAX_SAFE_MONEY`).
- Quote arithmetic (subtotal / discount / tax / total; half-up
  rounding).
- Variant lookup against the versioned `revision.json` catalog.
- `catalog.canonical(value)` / `catalog.digest(value)` for every
  SHB payload hash — already used by every downstream SHB module.

To lift `catalog.py` guards: replace the hardcoded
`synthetic_offer()` with a selector that reads the approved commercial
record and returns the same dict shape but with non-synthetic
identifiers. The validator (guards 1.3–1.5) must then be relaxed to
accept the approved revision string instead of exactly
`'synthetic-shb-offer-v1'`; the shape-equality check (1.3) and the
startswith-`synthetic-` policy checks (1.5) are the only two that have
hardcoded synthetic text.

---

## 2. `backend/shop/shb/checkout.py`

Minimum-form SHB scope on the shared checkout / acceptance / archive
machinery. 161 lines.

### Guards keeping it fake-only

| # | Line | Guard | Purpose |
|---|---|---|---|
| 2.1 | `checkout.py:21-24` | `def guard():` delegates to `invitations.fixture_guard()`; on `ValueError` raises `ShbError('Live checkout awaits approved commercial and provider configuration.', 503)`. | THE SHB checkout fake-only gate — called by every entry point. |
| 2.2 | `checkout.py:83` | `review_token(...)` calls `guard()` as its first line. | Blocks the FPGA review-token path. |
| 2.3 | `checkout.py:95` | `capture(...)` calls `guard()` as its first line. | Blocks FPGA checkout capture. |
| 2.4 | `checkout.py:149` | `authorize(...)` calls `guard()` as its first line. | Blocks checkout authorization called from the shared payment transaction. |
| 2.5 | `checkout.py:61` | `value()` defaults `policy = policy if policy is not None else catalog.synthetic_offer()`. | The synthetic offer is the only policy that passes `catalog.quote()`'s guards (1.3–1.5 above). |
| 2.6 | `checkout.py:63` | Every non-support document body is literally `'Synthetic test fixture only. No approved legal terms or real purchase.'` | No approved legal text. |
| 2.7 | `checkout.py:67` | Support document body: `'Synthetic manual support terms. SLL tracks time and sends task emails manually; no online balance or SLA.'` | Fixed synthetic text for manual-support terms. |
| 2.8 | `checkout.py:70` | ASIC supplement body: `'Synthetic ASIC terms only: 25-hour bundles ... No tape-out, sign-off, EDA/PDK access or outcome guarantee.'` | Fixed synthetic text for ASIC supplement. |
| 2.9 | `checkout.py:72` | Snapshot sets `'evidence_class':'local-synthetic'`, `'effects_authorized':False`, `'financial_confirmation':False`. | Marks the snapshot as non-live. |
| 2.10 | `checkout.py:79` | Snapshot sets `'support_tracking':'manual-outside-shop'`, `'named_identity_verified':False`. | Carries the manual-support invariant and the invitation-is-not-identity invariant. |
| 2.11 | `checkout.py:122` | `catalog.quote(cleaned['variant'], cleaned['quantity'], offer=catalog.synthetic_offer(), discount_bps=...)` — hardcoded synthetic offer on the committed checkout path. | Same synthetic coupling as 2.5. |

### Exact external input required to lift

- Lift catalog.py §1 first (approved commercial record + policy
  identifiers). This immediately lets `guard()` succeed in a non-fixture
  environment because `invitations.fixture_guard()` will accept the
  live settings. See §3 below for the specific fixture-guard
  settings keys.
- Real legal document bodies for each of `terms`, `support`, `refund`,
  `privacy`, and (for ASIC) `asic` — the text currently hardcoded at
  lines 63 / 67 / 70 must come from the approved legal-policy custody
  record. These replace the fixed synthetic strings.
- The `policy` parameter in `value()` already supports being passed in
  by the caller (line 59), so the lift is straightforward: select the
  approved policy by revision and pass it through.

Who provides each: approved legal review (document bodies); SLL
commercial adoption (lifting the fixture-guard settings — see §3).

### Provider-independent portions (ready now)

- The entire transaction structure: `transaction.atomic(durable=True)`
  with `select_for_update`, SHB identity resolution, submission
  fingerprinting, request-ID uniqueness enforcement, token signing /
  verification with session-digest binding, review-expiry / payment-
  expiry clocks.
- Cart / snapshot / checkout integration (`DraftCart`, `CartSnapshot`,
  `SyntheticCheckout`, `SyntheticCheckoutKey`, `SupportCheckout`).
- Discount claim wiring (`DiscountReservation` creation, claim slot
  management).
- Shared-checkout / shared-payment coupling (`shared_checkout.digest`,
  `payment.envelope`, `payment.accept`).
- `session_digest()`, `identity()` (UUID parsing), `lock_customer()`
  (customer row lock with staff/superuser exclusion).

Everything mechanical is live-ready; only the policy-source and the
legal-text source need external input.

---

## 3. `backend/shop/shb/invitations.py`

Reusable bearer entry, Asia/Tbilisi six-month expiry, current-state
session authority. 82 lines.

### Guards keeping it fake-only

| # | Line | Guard | Purpose |
|---|---|---|---|
| 3.1 | `invitations.py:27-30` | `fixture_guard()`: raises `ValueError('synthetic_shb_unavailable')` unless **all** of: `settings.SHOP_ENV in ('local','synthetic')`; `settings.SHB_SYNTHETIC_FIXTURE` is truthy; `settings.LIVE_PAYMENTS_ENABLED` is falsy; each of `PAYMENT_ADAPTER`, `MAIL_ADAPTER`, `STORAGE_ADAPTER` equals `'fake'`. | Settings gate referenced by every SHB fake-only entry point (checkout.py §2, services.py §5, transaction_mail.py §7). |
| 3.2 | `invitations.py:33` | `def issue_fixture(...)` — docstring: "Explicit disposable fixture only; not an actual policy/eligibility issuer." | Test-only invitation-creation helper used by the retained demo. |
| 3.3 | `invitations.py:35` | `issue_fixture()` calls `fixture_guard()` as its first line. | Prevents the test helper from running in production. |
| 3.4 | `invitations.py:43` | `issue_fixture()` hardcodes `eligibility_reference='synthetic-eligibility-v1'`. | Synthetic eligibility identifier. |

### Exact external input required to lift

Note: the **production** invitation-issuance path is NOT `issue_fixture`. It
is `shop.shb.invitation_issuance.register` + the `InvitationIssueGrant` /
`InvitationIssuanceScope` / `InvitationIssue` workflow in `models.py`
(see §6 below — those are already live-ready structures). `issue_fixture`
is a demo helper; the fixture_guard prevents it from running outside
synthetic.

What's needed to lift guard 3.1 so the real SHB routes operate outside
synthetic:

- `settings.SHOP_ENV` set to something other than `'local'` /
  `'synthetic'` (operational decision — e.g., `'production'`).
- `settings.SHB_SYNTHETIC_FIXTURE` False or absent.
- `settings.LIVE_PAYMENTS_ENABLED` True.
- `settings.PAYMENT_ADAPTER='real'` with the selected bank wired up
  (external gate — R9).
- `settings.MAIL_ADAPTER='real'` with the selected mail transport
  wired up (external gate — R9).
- `settings.STORAGE_ADAPTER='real'` with the selected object storage
  wired up (external gate — R9).

Who provides each: user authority + selected bank / mail / storage
providers (R9).

### Provider-independent portions (ready now)

- `six_month_expiry(created)`: Asia/Tbilisi local-calendar six-month
  arithmetic with correct month-end clamping (Aug 31 → Feb 28/29, Mar
  31 → Sep 30, etc.) and leap-year preservation; validated by the
  seven-case suite in `shop.shb.tests` (SHB-12 coverage). Live-ready.
- 32-byte URL-safe random bearer issuance; sha256 digest only; raw
  bearer never stored.
- `exchange(request, token)`: session cycle, SHB-key purge,
  `shb_invitation` / `shb_session_until` / `SESSION_EPOCH`
  installation, session expiry capped by invitation expiry. Live-ready
  — this is the actual production entry point at `/invite/<token>`.
- `eligible(row, at)`: revocation + expiry + customer-active +
  not-staff check, deterministic and framework-independent.
- `current(request, lock=False)`: session-epoch validation, UUID
  parsing, locked-row refresh, deadline check. Already covers every
  invariant the live SHB routes depend on.

**All of the invitation surface is live-ready.** The `fixture_guard()`
exists to prevent the test-only `issue_fixture()` helper and the
synthetic test-adjacent code paths from running when the operator has
not completed the operational-settings adoption. The production
`invitation_issuance.register` path does not call `fixture_guard` and
is already covered by `InvitationIssuanceScope` / `InvitationIssueGrant`
authority.

---

## 4. `backend/shop/shb/views.py`

Private SHB form / review / persisted ASIC request; no live purchase.
247 lines.

### Guards keeping it fake-only

| # | Line | Guard | Purpose |
|---|---|---|---|
| 4.1 | `views.py:60` | `fixture = getattr(settings, 'SHB_SYNTHETIC_FIXTURE', False) and settings.SHOP_ENV in ('local', 'synthetic')` | Context flag: fixture mode detected. |
| 4.2 | `views.py:86` | `if not fixture: raise services.ShbError('Live request intake awaits its approved privacy and operational configuration.', 503)` on the `submit` action (ASIC submission). | Explicit block for live ASIC request intake. |
| 4.3 | `views.py:115` | `value = discounts.preview(request, data) if data['discount_code'] else catalog.quote(data['variant'], data['quantity'], offer=catalog.synthetic_offer() if fixture else None)` | Preview quote passes the synthetic offer only in fixture mode; otherwise `None` and the resulting quote is unpayable (catalog guard 1.2). |
| 4.4 | `views.py:118` | `if fixture and data['variant']=='shb-fpga-10h':` — FPGA review-token generation only runs in fixture mode. | No live checkout review token. |

### Exact external input required to lift

- Lift catalog.py §1 (approved commercial record) — immediately fixes
  4.3 and 4.4 because `catalog.quote()` will then accept the approved
  offer shape.
- Lift the settings-level fixture-guard (invitations.py §3.1) — this
  switches 4.1's `fixture` to False and lets 4.2's non-fixture branch
  reach `services.submit_asic` with live settings.
- `services.submit_asic` itself has a parallel gate (services.py §5.2
  below) — same lift applies.

Who provides each: user authority (fixture flag off, SHOP_ENV off
`local`/`synthetic`); SLL commercial + legal (approved privacy /
operational configuration); approved commercial record (catalog.py §1).

### Provider-independent portions (ready now)

- All HTTP parsing: method / content-type guards, file-upload refusal,
  CSRF, protected-form shape, query-param whitelist, UUID validation.
- Form handling: `ShopForm`, `OfferForm`, cleaned-data flow.
- Template rendering: `shb/shop.html`, `shb/offer.html`,
  `shb/payment.html` with Content-Security-Policy, `Cache-Control:
  no-store`, `Referrer-Policy: no-referrer`.
- Invitation-exchange entry point (`invite` view) — live-ready.
- Catalog JSON surface (`catalog_json`) — live-ready.
- Protected static asset serving (`static_asset`) with manifest-
  approved SHA256 — live-ready.
- Offer withdrawal (`offer_page` POST with `action=withdraw`) — uses
  `lifecycle.customer_withdraw` which is live-ready.
- Payment page (`payment_page`) — uses shared `checkout_payment.pay` /
  `reconcile` which are live-ready once the bank adapter is real.
- Revised-request page (`revised_request_page`) — session-authorized
  revision link; live-ready.

**Only the ASIC submit action and the FPGA review-token preview are
fixture-gated.** The rest of the views surface already operates live
once settings are lifted.

---

## 5. `backend/shop/shb/services.py`

Request capture that extends the existing quotation record; no
payment or time grant. 77 lines.

### Guards keeping it fake-only

| # | Line | Guard | Purpose |
|---|---|---|---|
| 5.1 | `services.py:1` | Module docstring: "Current request capture extends existing quotations; no payment or time grant." | Explicit scope statement — no time entitlement, no grant of live purchase authority. |
| 5.2 | `services.py:27` | `invitations.fixture_guard()  # Actual intake/privacy/operational adoption is pending.` — first line of `submit_asic`. | Hard gate for the ASIC request-capture flow. |
| 5.3 | `services.py:52` | `catalog.quote(cleaned['variant'], cleaned['quantity'], offer=catalog.synthetic_offer(), discount_bps=...)` — hardcoded synthetic offer. | Same synthetic coupling as checkout.py §2.11. |
| 5.4 | `services.py:55-59` | Payload fields: `'evidence_class':'local-synthetic'`, `'intake_privacy_revision':'synthetic-shb-privacy-v1'`, `'purchase_acceptance':False`, `'financial_confirmation':False`, `'effects_authorized':False`. | Payload carries the fake-only / unaccepted-purchase invariants. |

### Exact external input required to lift

Identical to views.py §4:

- Lift the settings-level fixture-guard (invitations.py §3.1).
- Lift the catalog.py synthetic-offer requirement (catalog.py §1) — the
  approved commercial record provides the offer dict shape and
  replaces the hardcoded `synthetic_offer()` call at 5.3.
- Approved intake-privacy revision identifier to replace the hardcoded
  `'synthetic-shb-privacy-v1'` at 5.4.

Who provides each: same as §4.

### Provider-independent portions (ready now)

- `SupportRequest` creation with payload / sha256 / revision /
  immutable editable=False fields.
- Revision linking via `revisions.authorized`, `revisions.validate`,
  `revisions.link`.
- Discount claim reservation (`discounts.claim` + `discounts.reserve`)
  with `DiscountReservation`.
- Submission / fingerprint flow (`_submission`, `_previous`) with
  idempotent retry semantics on the `(invitation, request_id)` unique
  constraint.
- Quotation integration (`QuotationRequest`, `DraftCart`,
  `CartSnapshot`).
- Transaction-mail queueing (`queue('request-received', saved)`) —
  live-ready once the mail adapter is real (transaction_mail.py §7).

---

## 6. `backend/shop/shb/models.py`

Immutable Postgres CheckConstraints + model shape. 464 lines.

### Synthetic-only CheckConstraints (require SQL migration to lift)

| # | Line | Constraint | What it enforces |
|---|---|---|---|
| 6.1 | `models.py:55` + `:68` | `DiscountCode.evidence_class` default `'local-synthetic'`; constraint `shb_discount_synthetic_only`: `evidence_class='local-synthetic', policy_revision='synthetic-shb-discounts-v1'`. | Every stored discount code is explicitly local-synthetic. |
| 6.2 | `models.py:367` + `:372` | `InvitationIssuanceScope.evidence_class` default `'local-synthetic'`; constraint `shb_issue_scope_synthetic`: `evidence_class='local-synthetic', eligibility_reference__regex=r'\S', company_name__regex=r'\S'`. | Every stored invitation-eligibility scope is local-synthetic (the shape invariants — non-blank eligibility / company — remain valid live). |
| 6.3 | `models.py:432` + `:440` | `DiscountIssuanceScope.evidence_class` default `'local-synthetic'`; constraint `shb_discount_issue_scope_synthetic`: `evidence_class='local-synthetic'`. | Every stored discount-issuance commercial scope is local-synthetic. |

### Exact external input required to lift

Approved identifiers for the approved versions of each policy/scope:

- A non-synthetic string for `DiscountCode.policy_revision` (6.1) —
  the approved live discount policy version identifier.
- An approved `evidence_class` value for all three scopes. Candidates:
  `'approved-live-v1'`, a date-stamped `'approved-2026-11-DD'`, or a
  policy-hash-prefixed identifier. Operational decision.

Lift mechanism: three forward SQL migrations. Each migration:

1. Drops the `shb_*_synthetic*` CheckConstraint.
2. Replaces it with a new check that accepts the approved
   `evidence_class` (either as an open set — `evidence_class__regex`
   — or an exact match on the chosen approved identifier).
3. Optionally keeps `local-synthetic` as a permitted value for
   replay / regression, or explicitly rejects it on production
   databases.

Who provides each: SLL commercial adoption (new identifiers);
approved migration-review path (migration authorship + review); the
independent off-host runner (R9) for actually applying the migration
on the production database.

### Provider-independent portions (ready now — no lift needed)

Every other model constraint is deliberately preserved live:

- Digest-shape regex `^[a-f0-9]{64}$` on every `sha256` field.
- Bounded percentages (`1 <= percentage_bps <= 9999`).
- Bounded use limits (`1 <= use_limit <= 100`).
- Bounded slot numbers (`1 <= slot <= 100`).
- Bounded claim periods (`1 <= claim_period_days <= 365`).
- State enums on every `SupportRequest` / `SupportOffer` /
  `*Delivery` / `DiscountReservation` / etc. table.
- Archive-gate constraints (`shb_closure_archive_gate`,
  `shb_offer_publication`, `shb_request_closing_archive`,
  `shb_issue_publication_archive`,
  `shb_discount_issue_publication_archive`,
  `shb_invitation_revocation_archive`,
  `shb_discount_revocation_archive`, `shb_refund_review_archived`,
  `shb_refund_handoff_archived`): every archived record must have a
  non-empty `archive_receipt` before its `applied_at` / `published_at`
  / effects can be written. These preserve the "archive before
  effects" invariant and remain correct for live operation.
- Append-only / editable=False on every durable record
  (`InvitationIssue`, `DiscountIssue`, `*Revocation`, `PaidOrder`,
  `*Capture`, etc.).
- Uniqueness constraints on retry keys (`shb_request_retry_unique`,
  `shb_checkout_retry`, `shb_offer_retry`, `shb_issue_retry_once`,
  `shb_discount_issue_retry_once`, etc.) — the idempotency guarantees
  for the SHB workflow.
- `shb_discount_one_claim_target` (reservation claims exactly one of
  `request` or `checkout`), `shb_discount_held_until_matched` (state
  transitions require matching release-review / release-closure /
  consumed-order evidence).

**The three synthetic-only constraints are the entire delta between
the live models and the fixture models.** Everything else — shape,
invariants, archive-gate semantics, state machines, idempotency,
append-only — is production-ready.

---

## 7. `backend/shop/shb/transaction_mail.py`

Ordinary customer / request mail on the existing worker; durable fake
capture only. 158 lines.

### Guards keeping it fake-only

| # | Line | Guard | Purpose |
|---|---|---|---|
| 7.1 | `transaction_mail.py:19` | `FLAGS = {'evidence_class':'local-synthetic', 'financial_confirmation':False, 'effects_authorized':False}`. | Every notice payload carries the fake-only flags. |
| 7.2 | `transaction_mail.py:22-24` | `def guard():` calls `checkout.guard()` **and** checks `settings.MAIL_ADAPTER != 'fake'` → raises `ShbError('synthetic_transaction_notice_required', 503)`. Double gate. | Blocks every notice / claim / capture / dispatch path unless BOTH the commercial fixture-guard is in fixture mode AND the mail adapter is the fake. |
| 7.3 | `transaction_mail.py:62` | Every notice payload includes `'actual_email_sent': False`. | Marks the notice as never actually dispatched. |
| 7.4 | `transaction_mail.py:107` | Capture proof includes `'status':'durably-captured', 'actual_email_sent':False`. | Capture proof explicitly says no real email was sent. |

### Exact external input required to lift

- A selected mail transport (SMTP server, SMTP-over-TLS or managed
  provider API) — this is R9's "selected mail transport provider"
  gate.
- Updated adapter wiring: when `settings.MAIL_ADAPTER='real'`, a real
  SMTP / API adapter replaces the `shop.adapters.fake_mail` provider.
- Approved recipient-validation policy (DMARC alignment, bounce
  handling, unsubscribe handling, data-retention policy).
- Transport security review (DKIM key custody, SPF record, TLS
  requirements).
- Lift of the commercial fixture-guard (invitations.py §3.1) —
  `checkout.guard()` is the first check in `guard()`, so even after
  the mail adapter is real, the commercial gate must also be lifted.

Who provides each: R9 (mail transport selection + adapter author);
SLL operational review (recipient / bounce / DKIM / SPF policy).

Note on guard 7.2's structure: the check `if settings.MAIL_ADAPTER !=
'fake': raise` currently rejects the live path. Once a real mail
adapter is wired, this check must be updated to accept
`settings.MAIL_ADAPTER in ('fake', 'real')` or equivalent. That is a
single-line code change, authored at the same time as the real-adapter
integration (R9-scope work).

### Provider-independent portions (ready now)

- The entire lease-based worker claim pattern: `claim()`,
  `capture()`, `complete()` with `select_for_update(skip_locked=True)`
  / `Q(state='claimed', lease_until__lte=Now())` round-robin,
  bounded attempts, held-state terminal state.
- Idempotent notice construction with UUID5-stable keys
  (`uuid.uuid5(uuid.NAMESPACE_URL, 'sll-shb-transaction:' + event +
  ':' + str(source.pk))`).
- Archive-before-commit pattern: `archive.publish(notice.pk, raw)`
  then `payment.recover(archive, receipt, notice.pk, raw)` BEFORE the
  final `TransactionNoticeCapture.create`.
- The `local_effect('shb-notice-run', guard=guard, held_result=False)`
  wrapper for exactly-once dispatch across worker restarts.
- Notice payload construction for every event:
  `request-received`, `request-question`, `request-declined`,
  `offer-issued`, `request-closed`, `checkout-closed`,
  `purchase-confirmed` — six real customer-facing notice shapes, each
  constructed deterministically from the source record's signed
  payload.
- State machine `pending → claimed → captured → held` with bounded
  retries (`attempts <= max_attempts`) and lease expiry
  (`lease_until > Now()`).

**The dispatcher is production-ready.** The two lift points (the
`MAIL_ADAPTER != 'fake'` check at 7.2 and the `actual_email_sent:
False` flag at 7.3 / 7.4) are the entire delta between the fixture
dispatcher and a live one. Once the real adapter exists, the flags
become `actual_email_sent: True` (set by the adapter after transport
success) and the hardcoded `False` becomes a per-notice dispatched-
state field.

---

## Summary table

| File | Guards | Primary external lift input | Secondary lift inputs | Provider-independent surface |
|---|---|---|---|---|
| `catalog.py` | 6 | Approved commercial record (rates, tax, policy identifiers, bank bounds) | — | Shape validation, quote arithmetic, variant lookup, canonical digest |
| `checkout.py` | 11 | Lifted `catalog.py` guards + real legal document bodies | Settings-level fixture-guard lift (via `invitations.py` §3.1) | Entire transaction / snapshot / token / cart / discount-claim mechanism |
| `invitations.py` | 4 | Settings: `SHB_SYNTHETIC_FIXTURE=False` + `LIVE_PAYMENTS_ENABLED=True` + adapters all `'real'` (R9 dependencies) | — | `six_month_expiry`, bearer issuance, session exchange, revocation / expiry / eligibility — all live |
| `views.py` | 4 | Lift settings-level fixture-guard + `catalog.py` guards | — | All HTTP parsing, forms, templates, invite exchange, catalog JSON, static assets, payment page, offer page, revision page |
| `services.py` | 4 | Same as `views.py` + approved `intake_privacy_revision` identifier | — | `SupportRequest` creation, revision linking, discount reservation, quotation integration, transaction-mail queue |
| `models.py` | 3 | Approved `evidence_class` identifier(s) + three forward SQL migrations | Independent off-host runner for applying migrations on production DB (R9) | Every other constraint (digest shape, bounds, state enums, archive gates, append-only, idempotency) |
| `transaction_mail.py` | 4 | Selected mail transport + real adapter + single-line update to `guard()`'s adapter check (R9) | Lifted `checkout.guard()` (via `catalog.py` + `invitations.py`) | Entire lease-based worker, idempotent notice construction, archive-before-commit pattern, six notice shapes, state machine |

## Classification

- **Local-now (no external input needed):** Every provider-independent
  portion above. ~95% of the 1263 total lines across the seven files.
- **Local-now after a single operational decision:** The fixture-guard
  settings in `invitations.py §3.1` can be flipped once SLL agrees on
  `SHOP_ENV`, `SHB_SYNTHETIC_FIXTURE=False`, and `LIVE_PAYMENTS_ENABLED=True`.
- **Blocks on approved commercial record:** `catalog.py §1` guards 1.1,
  1.4, 1.5 (synthetic offer shape, revision strings) and the three
  `models.py` CheckConstraints. Unblock once legal / commercial /
  pricing / terms are signed off.
- **Blocks on R9 (external gates):** Adapter selection (bank, mail,
  storage, host) for `invitations.py §3.1`'s adapter checks and
  `transaction_mail.py §7.2`'s mail-adapter check. Off-host runner for
  the three SQL migrations.

No code change by this document. Every guard cited above
grep-verifies in the actual source at the recorded line number
(verified 2026-11-04T08:45:00+00:00 — see R8 closure evidence in
HANDOFF.json).
