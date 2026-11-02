# Protected SHB invitation revocation

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), including Appendix A. This continues existing 06-01. Invitation revocation was enforced on customer requests, but staff had no protected action to record it.

## Result

The existing staff application now lists only explicitly assigned invitations and offers a native revocation form. Every read and mutation requires current recent MFA and the exact invitation grant. Native and JSON submissions share the same service, CSRF protection and closed field set. Staff can inspect the original company/mode/expiry scope; no bearer, token digest, customer history or private contact prefill is returned. GET creates no revocation, replacement invitation, order or notification.

Before changing the invitation, the service archives an attributed audit containing the original scope/clocks, request identity, reason, staff credential generation and MFA time. It rechecks current epoch, MFA and assignment after archive I/O. The audit and revocation timestamp commit together. SQL guards require current exact staff scope, reject audit edits/deletion, and prevent an audit from committing without its matching invitation state. Exact retries retain one event and one timestamp; changed commands conflict. Archive failure leaves the invitation active. NUL input is rejected before archive or PostgreSQL JSON storage.

Revocation denies the existing invitation and surviving customer sessions on their next protected request. Original expiry, submitted ASIC review, coupon reservation, accepted orders, payment/reconciliation identities and support hours remain separate. Staff review continues using its own grants. The service does not issue/renew invitations, send mail, calculate time, move a customer, or create commercial approval. Existing manually revoked invitations remain valid historical records; no retrospective audit is invented for them.

The existing synthetic staff operator adds/removes exact invitation grants; staff reset and selected restore clear this new mutable scope alongside existing grants. Recovery checks retained revocation archives and their original timestamp/scope. Missing bytes keep fixture release closed. This cannot establish complete post-backup history or actual reopening authority.

Current code: [service](../../backend/shop/shb/invitation_admin.py), [staff views](../../backend/shop/shb/invitation_admin_views.py), [PostgreSQL tests](../../backend/shop/shb/invitation_admin_tests.py), additive SHB migrations 0023/0024, existing models/staff routes/templates/operator/reset and recovery assessment. Both existing SHB runners include the tests and support exact `--test-label` selection without claiming the shared lane.

## Executed evidence

The actual [RED record](../evidence/shb/invitation-admin-red-2026-11-02.json) executes one authenticated staff assertion after successful setup/migrations. It fails because staff home lacks Assigned invitations; there is no import/discovery/fixture error. RED commit `ca66362d6176591ad2262488a8fc5a6c45243c33` is ordinarily pushed to origin/main. The owned raw diagnostic remains `.scratch/shb-invitation-admin-red-2026-11-02.log`.

Seventeen focused PostgreSQL cases initially pass: staff navigation, assigned secret-free reads/no GET effects, exact retries and customer denial with continued review, scope/cursor denial, recent MFA/live guard, native CSRF, malformed fields, archive failure, grant/MFA changes during archive I/O, SQL immutability/atomicity, concurrent retries, reset/grants, quarantine/recovery, missing archive and legacy revocation. [Initial focused record](../evidence/shb/retained-tests/184463fab835347cf48ad2b1ac674b1a1694fe71bd63d9b471f62eaf0194370d.json) contains 26 tests including nine source/catalog controls. An intermediate [543-test shared record](../evidence/shb/retained-tests/d37dd00411eeb4023edce5150762f181dc74642397f6053369aed014aeb82d7b.json) and [123-check browser record](../evidence/shb/retained-tests/529b2624c002c3f359e991c684e1061be54cf89e434f2deb58f570937d5a3d38.json) precede the final NUL-input guard/regression. Those records retain their exact prior hashes.

Final actual Chromium 151.0.7922.173 / Node 24.15.0 passes **123 browser checks**: 71 customer and 52 staff checks, each lane in JS/no-JS modes at 320px. Both staff modes submit the native revocation form, observe CSRF denial, and retain the original expiry. Two customer sessions opened before revocation then receive 403 on their next protected request. Existing purchase/refund/handoff scenarios still verify unchanged original order, coupon and notice facts. [Final browser/source record](../evidence/shb/retained-tests/88fba02799ceb5de1f3650598871aae724adf8a99a904da68da54203b6260c32.json); private evidence `.scratch/shb-checkout-browser-ss83c58x`.

The final shared lane passes **543 tests**, none failed/skipped: 200 SHB including all 17 invitation-administration cases, 95 access/recovery, 104 payment, 30 staff review/navigation, 24 worker/statement-mail, 75 preserved transaction/archive, nine source/catalog and six actual `unshare --net` adapter cases. Django check, additive migrations 0023/0024 and migration-drift checks pass. [Final regression/source record](../evidence/shb/retained-tests/36d8f0f157241d73cffee09cfee8e1611c56ae4d75a0b7d63e977b786f9bb9e6.json) binds exactly the same 357 backend/eight-script hashes as the final browser record. Planning activity three tests and both planning checks pass. All owned test/browser/Gunicorn/disposable database contexts completed.

## Reproduce

```sh
python3 scripts/check_shb_retained.py --test-label shop.shb.invitation_admin_tests.InvitationAdminTests
python3 scripts/check_shb_retained.py --shared
python3 scripts/check_shb_retained.py --browser --release .scratch/shb-private-resume-t2p3r5cc/release --browser-binary /nix/store/53p8msmqxpi829zdrw6qkvaamidxy9cj-chromium-151.0.7922.173/bin/chromium --browser-node /nix/store/5a8ysg1jnj8jmzzyfcfw7rvpvnp5rfpa-nodejs-24.15.0/bin/node
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

These are separate retained-tool local synthetic results. Normal pinned Nix/source/runtime/native/licence/OCI/CI and actual provider/mail/host/ingress/database/human/independent recovery qualification remain open. The private Astro release is unchanged. All new action flags remain explicitly synthetic with no actual invitation authority, real mail or commercial effect. No production/bank-sandbox database connection, host/DNS/TLS/storage/bank action, `.env`/unrelated cache access or paid provision occurred. The independent off-host runner is unassigned. Company inputs arrive later through the single [decision register](../decisions.md); no repeated request. Parent plans and counts remain open: 11/42 summary records and 1/14 documentary phases, with no new SUMMARY or FULL_PASS.
