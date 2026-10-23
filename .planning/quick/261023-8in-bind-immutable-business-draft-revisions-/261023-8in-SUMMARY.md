---
quick_id: 261023-8in
status: complete
implementation_commit: abdb159021358645206cc3ac4864bf447a8b4a2c
---
# Immutable business revisions in quotation review

Implemented explicit owner preview/confirmation attaching saved private business revisions to append-only quotation scopes. Captured cart parents and retry uniqueness remain intact. Exact retries reconcile without rewinding; stale confirmations conflict; repeating the current attachment creates only a retry alias. Later business edits do not change an attachment.

New business scopes require fresh review. Legacy scope0 digests and prior decisions remain unchanged; review counters remain monotonic. Dedicated private staff reads and new bound-scope decisions require recent local MFA rehearsal, parent assignment and an explicit exact-current-scope business grant. New attachments do not inherit private grants. Ordinary summaries and inaccessible historical private digests are masked. Dereferencing checks matching business/cart ownership, including inconsistent database links.

Country registration/tax/deployment choices remain null/disabled, explicitly deferred to a later step by the user on 2026-10-23. No commercial authority, offers, acceptance, payment or support credit enabled.

## Verification

- Final core-local:97 tests, five checks, fresh owned real PostgreSQL18.6; migrations/system/drift checks pass. Final run21.821 seconds. Earlier87/95/96 runs superseded.
- Frontend104 Node tests plus proxy1; Astro18 files, zero errors/warnings/hints; static three-page build and import/output privacy checks pass.
- Ten new tests cover attachment retries/CAS/concurrency, ownership/CSRF/parser/mode boundaries, exact private grants/revocation, legacy hash/history preservation, scope-specific status reset, immutable values and cross-owner-link denial.
- Attachment-versus-review race permits only the previously authorized scope decision or rejection. Owner race fixture calls the view directly with explicit verification; CSRF/host boundaries have separate tests. No new live HTTP or browser qualification claimed. Prior15-observation staff HTTP evidence retains its original scope.
- git diff --check passed. No demo started, manual credential access, external operations, agents or asynchronous jobs in this slice.

## Limits and continuation

Local/synthetic evidence only. Human review of recent quotation/staff/business slices remains pending. Country/tax, real staff MFA/delivery/recovery, financial effects, durability and full commercial/release qualification remain pending. Database outage/recovery unexecuted; no FULL_PASS. Hosted CI unverified. Progress unchanged:1/14 phases (rounded7%),10/20 planned records; Phase02 remains8/18.

Next independent local step: assess source-backed document/declaration preview prerequisites for exact captured scopes, preserving unknown terms/prices as pending and keeping acceptance disabled. Country/tax choices remain explicitly deferred. No deployment or provider authority inferred.
