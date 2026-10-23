# Exact retained staff capture observation — proposed local contract

## Concrete need

The explicit digest-bound form safely reconciles an uncertain response by deliberate resubmission. Staff currently have no no-write observation of whether an exact retained request capture is recorded. Provide that narrow database observation without expanding root/work controls. This proposal does not qualify archives or authorize offers; critique required before implementation.

## Scope and service boundary

Proposed GET-only `/staff/quotation-requests/<quotation UUID>/request-evidence/<business version>/status/` on the existing separate synthetic staff app. Scope is exactly the route version, including explicit unbound version0; never silently follow current attachments. Recent staff MFA, enabled account/credential and exact current grant for the retained scope are mandatory on every observation.

Use a dedicated read-only service owning a short transaction. Reuse prepare_request_envelope inside that transaction so existing credential/quotation/cart locks remain held through receipt inspection. Validate/reconstruct current exact source, compute deterministic envelope identity and compare any retained RequestEnvelope owner/schema/payload/hash/size with the exact locked source. Validate the associated intent with the same pending/held, local-prepared-v1, local-synthetic/prepared and false retention/effect checks as capture. Missing envelope is `capture_not_recorded`; valid matching fact+intent is `capture_recorded`. A fact with missing/inconsistent intent, altered source or invalid flags is unavailable, never absent. Never call capture_request_envelope from GET or mutate/repair anything. Do not infer completed physical archive from a capture fact.

Keep form preview separate: this route should not emit source bytes/digest, IDs for envelope/intent/actor/MFA, root/destination/token/claim/lease, business values or work capability. Exact quotation/business references already in the private route need not be echoed in JSON. No discovery/listing endpoint and no archive I/O. No row rewrites, root binding, intent hold clearing, authorization refresh or automatic resubmission.

## Closed responses and navigation

Closed JSON: fixed `capture_not_recorded` or `capture_recorded`, `evidence_class=local-synthetic`, `evidence_kind=prepared`, `retention_qualified=false`, `effects_authorized=false`. HTML fixed safe labels and links to the exact version preview and request details only. Explain that no capture record does not authorize work, and recorded capture is prepared database evidence only. Link from the preview/confirmation to this same exact scope status, without hashes or command parameters. No forms on the status page.

Reject query parameters and non-GET methods. Fixed private403/404/503 errors without diagnostics; preserve middleware boundary. no-store/no-referrer/Vary Cookie/default-none CSP/form-action none/frame-ancestors none/base-uri none for handler responses. Local/fake-adapter restrictions remain inherited from the producer; customer and production routing remains closed.

## Required pre-execution critique

Inspect actual producer/capture/model/staff middleware and existing archive-observation patterns. Resolve: (1) read service lock lifetime and no outer capture transaction; (2) exact retained scope and no owner/private scope widening; (3) missing versus corrupt/inconsistent record distinction; (4) closed result projection and no work authority; (5) uncertainty/concurrency observations are committed database facts only, never physical retention or retry authorization. If this duplicates an existing suitable route/service, reuse it rather than adding a second authority path. No runtime implementation from this proposal before critique.

## Verification

Owned real PostgreSQL; actual password/private-code staff login and CSRF capture setup. Observe before capture, then after supported capture and after deliberate same-form retry. No record/file changes and no archive calls. Unknown scope, exact historical scope after new attachment, changed owner, removed grant, revoked credential/stale MFA and production/customer exclusion. Corrupt/missing intent and source mismatch return unavailable without writes. Verify safe JSON/HTML/headers/query/method/error responses. A deterministic lock-wait test should demonstrate observation waits for in-flight capture commit and reports committed result, without claiming real transport/process/outage qualification. Keep the current mixed/support-only supported journeys passing; no direct model writes in those journeys. Full core-local and exact allowlisted Nix source proof precede commit. All commercial/domain/source/external acceptance gates remain pending.
