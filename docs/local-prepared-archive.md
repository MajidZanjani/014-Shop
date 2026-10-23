# Selected local prepared archive command

`run_prepared_archive` executes one explicitly authorized quotation-request envelope against its existing bound private archive root. Current scope is local/synthetic PostgreSQL and fake adapters. Success records technical verification of prepared bytes; retention qualification and business effects remain false. The default `run_worker` probe daemon and image/service entrypoints are separate and unchanged.

## Prerequisites

Use an already configured frozen runtime and an owned isolated synthetic database. Never source the repository `.env` for this rehearsal. The current automated entrypoint is:

```sh
nix develop --max-jobs 1 --cores 4 ./ops/nixos --command python3 scripts/check_backend.py core-local
```

A selected invocation requires all of the following existing records:

- One exact immutable request envelope and its pending archive intent.
- An explicitly initialized private root, retained physical identity and intent binding.
- An unexpired, current, unrevoked authorization for that intent and destination, with the original owner/staff attribution and exact current source permissions.

Exact retained request capture now has an explicit recent-MFA staff preview/form at `/staff/quotation-requests/<quotation UUID>/request-evidence/<business version>/` on the synthetic staff origin, linked from the displayed request scope. It requires the exact private scope grant; version0 explicitly selects the unbound cart. The source digest is private to the protected form and checked inside the durable capture transaction. Explicit same-form resubmission retains the original fact/intent and attribution. This action performs no archive I/O or work authorization. Root initialization/binding and authorization still use internal services exercised by synthetic fixtures; their interactive controls remain pending. Do not manufacture a request/session, edit database rows or create an authorization merely to execute this command. An old capture retry, historical MFA timestamp or successful inspection cannot supply fresh work authority.

## Invocation and result

From the prepared synthetic runtime, select the existing frozen interpreter and exact retained identifiers/root. The variables below are placeholders for that private rehearsal context; this document supplies no production configuration or credentials.

```sh
"${SHOP_FROZEN_PYTHON:?select existing frozen runtime}" backend/manage.py run_prepared_archive \
  --authorization "${SHOP_LOCAL_AUTHORIZATION:?select existing authorization}" \
  --destination "${SHOP_LOCAL_DESTINATION:?select existing bound destination}" \
  --root "${SHOP_LOCAL_ARCHIVE_ROOT:?select existing bound root}"
```

The command requires explicitly selected Django settings/environment and database identity; it does not load `.env`. Identifiers must be canonical UUID strings. Root initialization, adoption, target switching, queue scanning and automatic retries are unavailable. Command options carry no claim token, host binding, envelope payload or business values.

Successful execution exits zero, writes one JSON line to stdout and leaves stderr empty:

```json
{"created":true,"effects_authorized":false,"retention_qualified":false,"status":"local_prepared_verified"}
```

The retained verification means the exact prepared envelope was published/read back and checked against the current claim/source/authorization before its completion transaction committed. It does not approve an offer or authorize acceptance, payment, document issue, licence delivery, support credit or chargeable work. No IDs, paths, tokens, hashes or private values appear in this result.

## Failure and uncertainty

Handled unavailable work exits one with empty stdout and the fixed stderr line `CommandError: Local prepared archive job unavailable`. Malformed/unknown scope, missing/wrong/busy/tampered roots, revoked authority and bounded database lock contention have actual local child-process regression evidence. This generic error intentionally does not distinguish those cases from failure after a claim or physical publication.

| Observation | Operator action |
|---|---|
| Fixed unavailable error | Preserve the original intent, authorization, claims and archive bytes. Reconcile the exact attempt before deciding any subsequent work. |
| Process exit, interruption or lost stdout with no reliable acknowledgement | Treat completion as uncertain; retain the same evidence and reconcile. Do not rerun on the basis of missing output. |
| Existing technical verification | Preserve its original attribution. A repeated command fails without republishing. |
| No recorded verification | Physical bytes or an in-flight attempt may still exist. Absence grants no retry, hold release, lease renewal or target replacement. |

Authorized reconciliation is currently the internal `reconcile_archive_publication(request, intent_id, expected_claim_id)` service. It requires current owner or recent-MFA exact staff scope and returns a fixed observation: `verification_recorded`, `verification_recorded_by_other_claim` or `verification_not_recorded`. It reads committed database evidence without archive I/O and grants no later work capability. A private recent-MFA staff GET is available at `/staff/archive-intents/<intent UUID>/claims/<expected claim UUID>/reconciliation/` on the existing synthetic staff origin. Supply only already retained exact references; these identifiers grant no access by themselves. JSON contains the fixed observation/classification and false effect flags; HTML contains fixed safe wording. The route rejects query parameters and writes and exposes no claim discovery or work controls. A general-purpose operator reconciliation CLI remains pending. Keep private record inspection inside the authorized application workflow; never log envelope bytes, tokens or private business values while investigating.

A fresh deliberate authorization cannot itself settle an uncertain prior attempt. Holds, existing records and physical bytes remain preserved. Reauthorization/retry policy beyond the current selected contract remains pending; do not delete evidence, reset leases, change roots or automate retries to force progress.

## Evidence and pending qualification

The latest local process evidence is recorded in [Plan07-02 process partial](../.planning/phases/07-multi-line-cart-quotations-business-checkout-and-acceptance/07-02-WORKER-PROCESS-PARTIAL.md). Ordinary owned synthetic process tests cover success, duplicate, scope/revocation, root contention/tampering, PostgreSQL lock timeout and physical-root mismatch. Independent transport/runtime/outage/recovery, off-host custody, provider retention and production qualification remain pending. Country/tax and commercial decisions stay deferred. This runbook grants no external service, deployment or protected-host authority.
