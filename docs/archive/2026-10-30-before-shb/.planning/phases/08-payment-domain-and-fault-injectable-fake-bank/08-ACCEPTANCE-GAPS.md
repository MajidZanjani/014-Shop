# Phase8 acceptance-gap audit — 2026-10-26

Audited implementation ad101646725aa6ee2707f1132deea6ac8b98eb22 and planning anchor c830297. Authority: October21 handoff §146/T08, amended ROADMAP PAY-01–05 and final purchase-flow revision2. Retained evidence: typed synthetic bank/attempt lifecycle/controls, complete-cart acceptance/payment, notification inbox and scoped overpayment investigation. Backend509 tests/worker24/proxy132 are local evidence, not actual financial/provider qualification.

| Requirement | Implemented local evidence | Remaining gap / acceptance boundary |
|---|---|---|
| PAY-01 | Immutable accepted checkout, one canonical attempt/reference, archive/readback before prepared→uncertain claim; deadline/cancel/dispatch holds rechecked after archive wait | Actual approved order/live activation/merchant/terms authority and qualified archive custody remain pending; synthetic holds are not production approval |
| PAY-02 | Claim commits before fake call; pre/post-commit loss remains uncertain; lookup-only recovery; customer navigation cannot confirm money | Actual hosted redirect/provider uncertainty/reference guarantees and independently qualified recovery pending |
| PAY-03 | Strict typed exact correlation; immutable retained inbox results; bounded single-worker leases and fence; hints supply no status | Direct dispatch and manual reconcile only retain the current attempt projection, without a separate archived normalized observation receipt. Actual callback authentication/key rotation/replay/provider semantics pending |
| PAY-04 | Exact retries, reorder/duplicate hints, explicit dual-capture local investigation and recent-MFA exact-pair review; one intended licence/support grant | Actual transaction attribution and unequal/partial amount policy remain unknown; matching values alone cannot establish attribution. Actual refund authority remains null |
| PAY-05 | Archived start request before supported synthetic start, cancellation/expiry/archive-failure/ambiguous success tests | Direct observation journal missing. Evolving authorization/capture/refund operation intents/history, documented qualified capabilities, and off-host recovery remain pending. Fake separate capture/refund/callback capability remains false |

## Selected independent local work

Plan08-02 adds immutable archived normalized observation receipts shared by direct dispatch, manual reconciliation and inbox lookup. Provider I/O stays outside locks/transactions. Receipt and current attempt projection commit atomically; archive failure leaves uncertainty rather than inferred success. Exact repeated observation uses the original receipt; lookup miss never confirms money. SQL immutability, archive readback, scope correlation, short leased-worker fences and real-PG concurrency tests remain required.

Existing observed rows are historical projections. Do not invent a prior response receipt, provider event time or receipt coverage for them. A new typed lookup may retain a newly observed fact after upgrade; old response provenance remains unqualified. Missing retained evidence must fail closed. Journal/DB suffix-loss recovery is not proved by local SQL triggers.

This is a remaining local PAY-03/PAY-05 implementation gap, not a reason to introduce refund capability, provider status progression or generic actual bank authority. Those require their separate plan/contracts and actual qualification. Actual provider/merchant/callback/financial/attribution/refund/legal/runtime/host/retention/full-pool-loss gates remain pending. No external or protected operation is authorized.

08-01 local tasks1–4 now implemented/verified/audited; full acceptance remains pending. Next execute08-02. New planned record changes project denominator to35, with11 completed records; Phase8 full acceptance0/2, Phase10 full acceptance0/6 and project fully completed phases1/14. Counts are not engineering effort.

08-02 execution update: immutable shared direct/manual/inbox observation journal is now implemented locally; integrated verification is in progress. See08-OBSERVATION-JOURNAL-PARTIAL.md. The table above records the audited pre-journal baseline. Actual gates remain unchanged. Next independent local design candidate: bounded synthetic authorization-to-capture intents/history, without pre-claiming provider/capture/refund capability.

Final08-02 resolution: shared archived direct/manual/inbox journal verified (backend525, combined focused58/all16 journal cases, worker24, proxy132/2 aliases and253-file exact source). The selected local receipt gap is closed for its documented synthetic scope. Actual gates in the baseline table remain pending. Next plan bounded synthetic authorization/capture operation intents/history before implementation; fake separate capture/refund/callback capabilities remain unchanged until a separately tested simulator contract exists.

##08-03 resolution —2026-10-27

Bounded v2 simulator full capture/refund intents, immutable transition/result history, forward projection and known stale-fact replay are now implemented and locally verified. Default-deny commercial revision consumption feeds existing synthetic checkout. [Final evidence](08-03-VERIFICATION-PARTIAL.md). Earlier table and capability statements record their dated baseline. Actual provider/callback/partial-refund/merchant/commercial/retention/runtime/recovery/activation gates remain pending; no full Phase8 acceptance.
