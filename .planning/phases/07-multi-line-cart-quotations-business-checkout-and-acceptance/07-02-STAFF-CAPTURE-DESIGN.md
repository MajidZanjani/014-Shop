> Final purchase-flow revision2 supersedes conflicting future requirements in this earlier design. Use [current clauses](../../PURCHASE-FLOW-AMENDMENT.md) and the updated07-02–04 plans. Historical critique/evidence below does not require universal per-sale approval, a technical dossier/portal or actual commercial inputs before independent synthetic work. No old next-action paragraph routes execution.

# Explicit local staff prepared-request capture — proposed contract

Current implementation8ba45cc provides a private exact-attempt observation route. Prepared request capture itself remains an internal atomic service. Add a deliberate local staff preview/capture form that makes that existing evidence step reviewable, while leaving root initialization/binding, worker authorization/claims, archive I/O and commercial actions unavailable.

## Scope and deliberate action

Use the existing separate synthetic staff URL configuration. Proposed route: GET/POST /staff/quotation-requests/<quotation UUID>/request-evidence/<business version>/. Require recent staff MFA and the existing producer's exact retained quotation/business grant on every operation. Business version0 is the explicitly unbound retained cart scope; positive versions refer to exact retained business attachments. Never silently switch an old link to the current scope. Label the selected retained cart/business revision clearly and link only from staff details to their displayed scope. A later attachment does not rewrite the selected scope.

GET privately reconstructs the exact source bytes through prepare_request_envelope, shows only safe scope references and fixed pending/effect wording, and renders a deliberate “Capture prepared request evidence” form. No capture or other domain write on GET. Add CSRF and one expected source SHA256 hidden field; never render payload, private business values, host IDs, raw keys, tokens or staff MFA metadata. The expected digest stays within this protected form; omit it from confirmation, ordinary summaries, URLs, session state and logs.

POST accepts bounded application/x-www-form-urlencoded fields only: action=capture, expected_source_sha256 and the middleware CSRF token. Reject extra/duplicate fields, query parameters, malformed digest, unsupported methods and oversized body. Keep enforced CSRF and no-store/no-referrer/restrictive form/self CSP. No JavaScript/browser storage. No root path, destination identity, worker grant or token inputs.

## Atomic stale-preview/retry behavior

Extend capture_request_envelope with an optional expected_source_sha256 argument, preserving existing internal callers. Validate it as a lower-case64-character hex digest. Compare with the actual digest of locked/reconstructed source bytes inside the existing durable capture transaction, before creating or returning a fact/intent. A changed preview conflicts without writes; no outer view transaction around this owned service. Scope/permission/source failures remain safe unavailable; stale digest maps to fixed conflict. Do not return the actual digest or raw database/provider exception.

Success renders the exact selected retained scope and a fixed “Captured” or “Original capture retained” confirmation from CaptureReference.created. A same-form refresh/retry returns the same semantic capture with original IDs/actor/MFA attribution, never a second intent or refreshed authority. A lost response has no automatic effectful retry; explicit resubmission of the exact form is safe under the existing unique scope arbitration. Do not claim this is a completed/qualified archive: the intent remains pending/unbound with false retention/effect flags.

## Verification and review before execution

Before implementation critique these boundaries: (1) source digest checked under the same locks/transaction as insert/replay; (2) explicit retained scope never silently retargets; (3) strict form/CSRF and current exact permission on preview, capture and retry; (4) confirmation preserves original capture attribution; (5) no archive/worker/domain effects. Resolve any contradiction before editing runtime code. No commercial/source approval is inferred from this local design.

Use real owned PostgreSQL and actual local staff password/private-code login. Test GET/no writes; POST strict inputs/CSRF; digest mismatch and stale source/no writes; replay/original actor; exact historical grants, removed grants, stale MFA and ownership changes; source/unavailable failures and no private confirmation values. Existing capture concurrency tests must still pass. Stage new source files before the Git-backed Nix artifact build; exact source/template comparison is mandatory. Existing source artifact/257-test evidence remains historical until new checks pass.

No new model/migration, worker capability, country/tax policy, offer, acceptance, payment, support right or external operation. Production staff access/transport and all independent runtime/provider/recovery gates remain pending. If implementation needs a broader mutation or new authority, retain it as a separate pending design.

## Inline pre-execution critique — 2026-10-23

All five boundaries checked against envelope_capture.py, request_envelope.py and existing staff forms. Digest comparison belongs after locked reconstruction/validation and before either replay lookup or insert in the durable capture transaction. Explicit integer route scope is passed unchanged; no current-scope lookup in the handler. Existing producer rechecks recent MFA/credential and exact retained grant under locks on POST/retry. GET uses the same producer; CSRF and strict bounded form parsing apply to POST. Existing CaptureReference.created selects confirmation without replacing actor/MFA or returning private IDs/digests. No archive or worker import is needed. Confirmation uses route scope after commit, avoiding a second source read after a successful capture. Existing pending or held intents can be replayed, so confirmation must say pending or held, rather than promise an existing intent is always pending/unbound. No broadening of authority/model/commercial scope required.
