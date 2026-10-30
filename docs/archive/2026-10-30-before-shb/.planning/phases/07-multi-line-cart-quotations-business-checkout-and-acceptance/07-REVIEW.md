---
phase: 07-multi-line-cart-quotations-business-checkout-and-acceptance
reviewed: 2026-10-23T12:37:09Z
depth: deep
files_reviewed: 17
files_reviewed_list:
  - backend/shop/access/archive_observation.py
  - backend/shop/access/journey_tests.py
  - backend/shop/access/management/commands/local_staff.py
  - backend/shop/access/request_evidence.py
  - backend/shop/access/request_evidence_tests.py
  - backend/shop/access/staff_auth.py
  - backend/shop/access/staff_middleware.py
  - backend/shop/access/templates/access/request_evidence.html
  - backend/shop/catalog/business_scope.py
  - backend/shop/catalog/envelope_capture.py
  - backend/shop/catalog/envelope_capture_tests.py
  - backend/shop/catalog/models.py
  - backend/shop/catalog/request_envelope.py
  - backend/shop/catalog/request_envelope_tests.py
  - backend/shop/config/staff_local.py
  - backend/shop/config/staff_synthetic.py
  - backend/shop/staff_urls.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 07: bounded capture/status review

Reviewed implementation 35cb252 at checkpoint HEAD 79a6d29; intervening changes are planning only. Inline GSD review, without delegated agents or external reviewer lanes. This report covers the exact prepared capture/status slice, not all Phase 07 deliverables.

## Narrative Findings (AI reviewer)

No demonstrated defect found within the reviewed local contract. No runtime changes or speculative fixes made.

| Boundary | Source and regression evidence |
|---|---|
| Commit and lock lifetime | Capture and observation reject outer transactions/manual autocommit and own durable transactions. Nested producer credential/quotation/cart locks survive through fact/intent inspection. Existing real-PostgreSQL tests establish actual blocking with pg_blocking_pids and distinguish capture commit from rollback. |
| Current authorization | Producer repeats recent-MFA credential checks after locking the enabled generation with current active/staff account predicates. Supported operator reset/revoke and grant changes serialize through credential then quotation locks. Exact historical business grants are required; version zero explicitly selects the unbound scope. Reads never follow a later attachment silently. |
| Consistency and attribution | Shared retained_intent checks deterministic identity, schema, owner, exact bytes/hash/length and constrained pending/held intent flags. Missing envelope alone means absent; missing intent or altered source is unavailable. Existing capture/retry/owner-versus-staff tests preserve original actor/MFA and one semantic fact/intent without rewriting. Attribution is append-only by supported service, not a claim of protection against arbitrary privileged database writes. |
| Closed outputs | Status GET projects only fixed labels/JSON and false qualification/effect flags. Handler responses are private, no-store/no-referrer, with form-action none for observation. Template emits no observation form, digest, payload, actor/MFA or worker capability. Earlier middleware retains its own refusal contract. Preview digest is intentionally confined to the CSRF-protected explicit capture form. |
| No additional authority | Status calls no capture or archive operation. Existing SQL-write guards, storage-call traps and supported mixed/support-only journeys verify unchanged facts/private files and no work records. Customer/production routes remain excluded. A committed observation grants no retry, worker, retention, offer or commercial permission. |

## Verification and limits

Fresh owned synthetic PostgreSQL: `nix develop --max-jobs 1 --cores 4 ./ops/nixos --command python3 scripts/check_backend.py core-local` passed: CORE_LOCAL_PASS checks=5 tests=272 duration_seconds=70.325 (258 Django tests and 14 Gunicorn observations). The producer requires PostgreSQL 18.6/UTF8, migration application and no model drift. No skipped checks. No source changes, migration or additional tests; prior exact source-package evidence remains unchanged and was not rebuilt.

Static lock tracing corroborates supported credential/grant mutation serialization; this run does not add an independent process-level credential-revocation race qualification. Prepared database facts are not proof of physical archive completion. No browser, real staff transport/MFA, outage, provider, off-host, restore or production qualification. Country/tax, commercial prerequisites and full 07-02 acceptance remain pending. Phase completion counts remain unchanged.
