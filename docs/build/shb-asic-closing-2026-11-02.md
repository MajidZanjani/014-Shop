# SHB unaccepted ASIC withdrawal, final expiry and reviewed reissue

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), including Appendix A. This continues existing07-04 inline after the [matching offer](shb-asic-offers-2026-11-02.md) slice. Evidence is local and synthetic; actual commercial/provider/runtime/independent qualifications remain pending.

## Implemented behavior

Assigned staff with current recent MFA and the exact private request grant can record a reasoned withdrawal before acceptance, finally expire an unaccepted dated offer, or close an offer for explicit reviewed replacement. A current same-company/project ASIC invitation can deliberately withdraw its unaccepted offer through a separate CSRF-protected native form, without entering or exposing saved billing/contact information. The stored actor records bearer attribution and explicitly denies named-identity verification. GET creates no closing, coupon or message effect.

A RequestClosure is an immutable deliberate intent on the existing request/offer, rather than a manufactured checkout acceptance. Its archive retains the complete original request/offer payloads, hashes, revision/review version, actor/reason, exact concession identity and requested result. The committed intent fences offer issuance, review, checkout capture and acceptance before archive I/O. PostgreSQL independently enforces this fence. Only successful archive recovery followed by atomic application closes the exact offer/request and releases the matching hold. An interrupted archive leaves the hold reserved and the intent resumable through the existing worker. A saved closing action may finish after session expiry; it cannot authorize new offers or charges.

Withdrawal and final unpaid expiry release the concession once without changing its original new-claim deadline or the invitation's lifetime. The existing worker selects unaccepted expired offers for final closing, and leaves accepted checkouts to their established safe cancellation/expiry or bank reconciliation. Accepted/paid and uncertain payment paths cannot enter pre-acceptance closing. The application now returns a controlled conflict if closing wins between checkout capture and acceptance; the independent database guard remains active.

Replacement closes the old payable offer while preserving the one original request hold. A fresh attributed technical review is required before a new dated revision can be issued. Old price/scope/document/approval/archive evidence remains unchanged. Reissue after final expiry also requires fresh review and uses a new offer and explicit customer acceptance; a released concession is not silently reclaimed or extended. A failed unpublished preparation can be abandoned without fabricating an issue timestamp or published archive receipt.

The assigned staff page contains native reasoned closing controls. The customer offer form includes deliberate withdrawal and explains that changed work or quantity needs fresh review/acceptance. Editing an offered request in place remains forbidden. A complete linked material-request-revision/resubmission workflow and ordinary request/customer notices remain open.

## Verification

The initial one-target PostgreSQL test failed on HTTP404 versus201 after valid request capture and exact assigned recent MFA. GSD returned RED_EVIDENCE_OK; [unchanged actual RED report](../evidence/shb/asic-lifecycle-red-2026-11-02.json). Test/resume commit15963fb is pushed.

Seventeen focused lifecycle tests pass. They cover archived withdrawal, exact retry, archive interruption/worker completion, unchanged-scope replacement and fresh review, failed preparation abandonment, accepted/uncertain denial, current scope/MFA/CSRF/live guards, SQL release/history rejection, customer withdrawal and acceptance races, final expiry and reviewed reissue without reclaiming a released code.

Positive final-expiry tests seed explicitly synthetic pre-existing backdated snapshots in the disposable test database. The offer's normal issuance trigger is bypassed only for fixture construction and restored before tested closing/reissue writes. These tests do not claim that14 days actually elapsed or that historical issuance was independently qualified. The negative premature-expiry case and all tested workflow writes use normal PostgreSQL guards. Shared payment/security checks remain unchanged.

Full unchanged-source run: **475 tests passed**, none failed or skipped:132 SHB,95 access/recovery,104 payment,30 staff review/navigation,24 local worker/statement-mail,75 preserved transaction/archive,9 source/catalog and6 actual `unshare --net` adapter cases. Django check, all additive migrations and schema drift checks passed. [Final regression/source record](../evidence/shb/retained-tests/0878205ba00917fcf22d8995f581f432fa27ef822a1a31e9dd5befe5a16aee50.json). Both final records bind identical336 backend/eight-script hashes. Planning activity3 tests and both required planning checks pass.

Actual Chromium151.0.7922.173/Node24.15.0 passed65 checks in JavaScript/no-JavaScript modes at320px. The native form deliberately withdraws one ASIC offer in each mode with no contact prefill or browser persistence. Persisted browser results include6 ASIC requests,6 shared checkout/acceptances,4 fake bank operations/paid orders,2 safe accepted FPGA cancellations,2 archived unaccepted ASIC withdrawals with2 matching releases,4 durable support-team fake purchase-notice captures and0 historical fulfilments. [Browser/source record](../evidence/shb/retained-tests/74c7b3f4501a67b7ecbe5c61b916c2f5717cc1c211d216b5fb6033865abac7eb.json). Private empty screenshots: `.scratch/shb-checkout-browser-r0xnug6l`.

Development failures were corrected before qualification: a new SQL CASE expression needed parentheses; a nullable related offer needed `select_for_update(of=('self',))`; historical fixture setup needed to flush deferred constraints before restoring its trigger; native form tests use both ordinary URL-encoded and multipart-without-files forms. None was substituted for intended RED evidence or counted as a pass.

## Reproduce

From the repository root, with the retained exact tools and unchanged private release:

```sh
python3 scripts/check_shb_retained.py --shared
python3 scripts/check_shb_retained.py --browser --release .scratch/shb-private-resume-t2p3r5cc/release --browser-binary /nix/store/53p8msmqxpi829zdrw6qkvaamidxy9cj-chromium-151.0.7922.173/bin/chromium --browser-node /nix/store/5a8ysg1jnj8jmzzyfcfw7rvpvnp5rfpa-nodejs-24.15.0/bin/node
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

Changed runtime files: [lifecycle.py](../../backend/shop/shb/lifecycle.py), [models.py](../../backend/shop/shb/models.py), additive SHB0015/0016 migrations, offer/staff review/views/templates, existing staff routes and worker services. Both ordinary and retained SHB check scripts include [lifecycle_tests.py](../../backend/shop/shb/lifecycle_tests.py); the existing demo/browser scripts exercise withdrawal. No second worker or commerce platform was introduced.

The retained lane remains separate synthetic evidence. Normal pinned Nix/source packaging cannot resolve the previously recorded missing dependencies; no pins or host permissions were changed. Real company approvals and provider/mail/host/ingress/database/native/licence/OCI/CI/independent/recovery/human qualification remain pending in the single [decision register](../decisions.md). The authorized off-host runner is still unassigned. No real credentials, bank/mail/storage/protected-host/DNS/TLS action or paid provision occurred; `.env` and `http_cache.sqlite` were untouched.

No full parent SUMMARY, phase completion or SHB acceptance checkbox is warranted. Counts remain11/42 retained summary records and1/14 documentary phases. Orders still record only their own bundle size, quantity and hours; no support-time ledger, balance panel or task-email automation is connected.
