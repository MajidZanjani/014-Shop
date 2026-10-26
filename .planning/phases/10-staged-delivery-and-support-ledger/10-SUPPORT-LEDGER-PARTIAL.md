# Synthetic support ledger — 2026-10-26

Partial execution of10-02; source FLOW-07/FUL-04–06. Current routing: STATE.md/ROADMAP.md. Full plan/phase acceptance remains pending.

## Implemented local behavior

Each existing archived complete-cart grant remains exactly36000 integer seconds/package once, without expiry or renewed licence rights. One grant/owner at a time: no automatic pooling/sharing. Append-only reservation/release/work/correction/statement events carry ordered revisions and hashes, exact request keys, attributed actor and archive receipts. PostgreSQL locks serialize the owner/grant and recent-MFA credential/resource grant. Triggers reject UPDATE/DELETE of ledger history; unique revision/request constraints reject duplicates. Maximum10000 events/grant; archive byte limits remain in force and fail closed.

Reservations allocate available seconds; release frees the unused portion. Work requires recent local staff MFA and an explicit exact-grant assignment. Simulated completion evidence publishes and recovers before work spending commits. Corrections retain the original record and archive explicit reverse/replace operations atomically; concurrent corrections cannot reverse the same work twice or take reserved credit. Zero replacement reverses a spend; subsequent corrections target the replacement event.

Statements retain the prior committed revision/hash and task/cumulative/reserved/remaining usage. Full source grant and ledger evidence recover before publication; prepared orphan evidence after rollback is not a committed debit or published statement. Actual technical completion is never inferred from synthetic completion flags.

Customer support page links from the existing payment/fulfilment page; closed JSON/form commands, CSRF, same-origin form policy, no-store, resource ownership and owner-safe summaries remain. Staff support page requires separate staff host/recent MFA/exact grant. local_staff grant-support/revoke-support uses --checkout; staff reset/revoke clears support grants. No new portal, engineering questionnaire, EDA execution, real email or actual spending.

## Verification

- Pinned Python3.13.16, Django5.2.18 and owned PostgreSQL18.6/UTF8; catalog0017 applies; no migration drift.
- Focused13 ledger tests pass,4.136s: competing reservations/work/corrections; exact retries/conflicts; archive-before-debit and rollback/retry; archive failure/readback failure; immutable DB history; integer bounds/owner/production denial; scoped MFA expiry/revocation; customer/staff forms, JSON, privacy and CSRF; operator reset clears support authority.
- Full CORE_LOCAL_PASS checks=5 tests=391 duration_seconds=103.505; existing prior-phase suites included. Independent off-host recovery remains unexecuted.
- Actual loopback proxy/Gunicorn/owned PostgreSQL DEMO_ACCESS_PASS checks=66 aliases=2 evidence=local-synthetic-header-level; support reservation/release exact retries, redirects/balances and null-origin rejection added to existing flow.
- Inert source artifact /nix/store/wxsbfqy1z83gyxr9s891ppym6cy8qb95-shop-python-source:215 exact path/byte files,27 templates,1 CSS,no symlinks. No OCI/runtime/distribution/production qualification inferred.
- Normal wheel download was truncated. Task-owned cache retrieved the exact reviewed wheel URLs with a cache-bypass query, verified every existing SHA256 and used the unchanged hash-locked installer. /tmp capacity was insufficient; tests used new owned project .scratch roots and cleaned their clusters/runtime directories. No pins or existing resources changed/pruned.

## Remaining

Integrate the ledger into the supported complete-cart demo and retain acceptance mapping. Actual SLL work/owner/scope/commercial/terms approvals, qualified staff MFA/retention, actual completion archives, final real statements/mail, keys/private package delivery and external/runtime/recovery qualifications remain pending. Local ledger credit is never actually spendable. Counts stay1/14 phases,11/29 plan records; no SUMMARY completion is fabricated.
