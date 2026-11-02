# Protected SHB invitation issuance and reissue

Authority: [SHB revision1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), fully read including Appendix A; existing06-01 continues inline. Real company/eligibility/commercial inputs remain pending in [the single decision register](../decisions.md). This component is guarded local synthetic implementation.

The existing staff application gains explicitly assigned issuance scopes. An immutable scope binds an established customer, legal-company name, eligibility reference, project and allowed modes. Staff forms cannot create or edit those facts. An exact revocation grant cannot issue an invitation. Every read/action uses current recovery epoch, recent MFA and the separate exact issuance grant. The issuing staff member receives an exact revocation assignment for the new invitation. The local operator assigns the existing issuance scope; staff resets and selected restores clear mutable grants while retaining historical records.

Deliberate native/JSON POST prepares one attributed digest-only intent with server time, the six-calendar-month Asia/Tbilisi expiry, reason and original request identity. It commits before archive I/O. Publication archives and verifies those exact bytes, rechecks current authority, then atomically creates the matching invitation and records publication. Archive failure/interruption leaves the same prepared intent and no active invitation. An exact retry completes that intent without generating another token or restarting its clock. Prepared native retry controls carry only the original command.

The successful creating POST alone returns its32-random-byte bearer in a no-store/no-referrer private response. Raw bearers never enter the intent, archive, normal database, cookie, redirect or browser-storage APIs. GET and exact retries expose metadata, never the bearer/digest. A lost response cannot recover the bearer. If the already published invitation is inaccessible, staff must explicitly revoke it before deliberately replacing it. No automatic replacement or mail exists.

A replacement requires a revoked or expired invitation with the exact customer/company/project/eligibility/modes. It records a distinct issue and leaves the original invitation clocks, revocation and prior requests/orders/coupons/notices intact. One source has one replacement intent; a different command cannot silently replace it again. Existing accepted offers retain their separate access/payment rules. No history grant, contact adoption, commercial approval, customer panel or time-accounting mutation is added.

Additive PostgreSQL0025/0026 retain immutable scope/audit data, validate current exact issue authority and synthetic flags, bind calendar clocks, and allow only the one prepared-to-published transition against the matching invitation. Recovery validates retained original issuance evidence; missing published archive bytes hold fixture release. Prepared intent assessment does not establish complete post-backup recovery or authorize real retry/reopening. A credential reset can leave an old prepared intent held rather than promote its prior authority.

## Verification

Actual RED [record](../evidence/shb/invitation-issuance-red-2026-11-02.json): one focused PostgreSQL test failed at404 versus200 for the missing issuance-scope route after successful setup/migrations. RED7567254 is committed and ordinarily pushed. Private diagnostic: .scratch/shb-issuance-red-2026-11-02.log.

First focused implementation run applied0025/0026 and passed schema drift, then reported34 tests with two failed expectations and one fixture error. Corrections preserve existing302 invitation entry, restore fresh MFA before separately testing the closed fixture gate, and account for rollback of the injected grant deletion. The next [46-check focused record](../evidence/shb/retained-tests/d7b258bd373821bbdd8235ae033e7817e3ecbe46a47b0795ab4d8af295569823.json) and [137-check browser record](../evidence/shb/retained-tests/9d3bb6f29b16c3b15775d18ce7995a30f12c79fe46a4ce30e40279e39c72ed9a.json) bind the same intermediate373 source hashes.

The first shared lane passed220 SHB cases, then failed two of95 access/recovery cases because legacy exact reset-count assertions omitted the new empty grant set. Those assertions now include it. A new selected-restore case verifies clearing an actual issuance grant while retaining its audit. Inline review also added a deferred commit guard: silently omitting the publication update must roll back the newly active invitation. Exceptions and deliberate omission are both tested.

Final focused verification passes **48 tests**:39 actual PostgreSQL issuance/revocation cases and nine source/catalog checks. Django system check,0025/0026 and migration drift pass. [Final focused record](../evidence/shb/retained-tests/44338ca135f22f58d11d2a904a28a188bb80a88414646f37bef0a987860f4d96.json). The final shared lane passes **565 tests**, none failed/skipped:222 SHB,95 access/recovery,104 payment,30 staff,24 worker/statement-mail,75 shared transactions/archive, nine source/catalog and six actual network-isolated adapters. [Final regression/source record](../evidence/shb/retained-tests/2028fdfde6332f22a78c601cf8215db7b642376763fca84fef10bb5048c0b29d.json).

Final actual Chromium151.0.7922.173/Node24.15.0 passes **137 checks**:71 customer/66 staff, JS/no-JS/320px. Two native inactive-source replacements display one-time bearers; exact form retries show none. CSRF denial and clean browser storage/layout pass. Backend inspection validates both retained issue archives and original source expiry/revocation. Old customer sessions stay denied and original purchase/coupon/notice/refund/handoff facts are unchanged. [Final browser/source record](../evidence/shb/retained-tests/11620cba8b55f8c1870147621b01ac8ab30cd31957c5e2a0a57043b6b9541a88.json); private evidence .scratch/shb-checkout-browser-rqbnhvgi. Final focused/regression/browser records bind identical365 backend/eight-script hashes. Intermediate records retain their original hashes. Planning activity3 tests pass; both required planning checks are run before commit. All owned contexts completed; no async job.

## Reproduce

```sh
python3 scripts/check_shb_retained.py --test-label shop.shb.invitation_issuance_tests.InvitationIssuanceTests --test-label shop.shb.invitation_admin_tests.InvitationAdminTests
python3 scripts/check_shb_retained.py --shared
python3 scripts/check_shb_retained.py --browser --release .scratch/shb-private-resume-t2p3r5cc/release --browser-binary /nix/store/53p8msmqxpi829zdrw6qkvaamidxy9cj-chromium-151.0.7922.173/bin/chromium --browser-node /nix/store/5a8ysg1jnj8jmzzyfcfw7rvpvnp5rfpa-nodejs-24.15.0/bin/node
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

These use retained local tools; they do not qualify the normal pinned Nix/source/runtime/native/licence/OCI/CI path. Actual company/provider/tax/refund/mail/host/ingress/database/human/independent custody/restore/complete-loss gates remain open. The independent off-host runner is unassigned. No .env, real credential, production/bank-sandbox connection, host/DNS/TLS/bank/mail/storage operation or paid provision. The private Astro release is unchanged; unrelated http_cache.sqlite remains untouched. Scoped discount issue/revoke administration follows. No parent SUMMARY/FULL_PASS/count change:11/42 retained records and1/14 documentary phases.
