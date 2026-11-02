# Protected scoped discount revocation

Authority: [SHB revision1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), including Appendix A; existing06-01/07-02 continue inline after pushed invitation issuance4db2586. Real discount defaults/adoption remain pending in the single [decision register](../decisions.md).

The existing staff application lists exact assigned discounts and exposes native/JSON revocation. Current recovery epoch, recent MFA, exact grants, CSRF and a closed field set protect every action. GET reveals no raw code/verifier or private contact history and creates no revocation, replacement or notification. A revocation assignment cannot issue a code or approve a concession.

The service archives an attributed immutable decision containing the original customer/variant/percentage/policy/use-limit/claim-clock scope, staff credential generation/MFA, request identity and bounded reason. It rechecks authority after archive I/O. SQL requires current exact staff scope, append-only audit and the matching revocation timestamp in one commit. Exact committed retries preserve one event; changed commands conflict. Archive failure leaves the code active. If publication succeeded but a later transaction failed, different bytes for that same archive identity remain held with503: no overwrite, fresh timestamp substitution or blind retry is allowed.

Revocation stops new claims immediately while preserving existing reservations, offers and accepted order prices. It neither releases limited-use capacity nor reprices a purchase, renews a deadline, issues a replacement or reactivates a refunded code. Ordinary synthetic paid-order finalization still consumes the original held concession once. No new time-accounting or customer panel is added.

The local operator adds/removes exact discount grants. Reset and selected restore clear mutable grants while retaining audits. Recovery checks original discount evidence/clocks; missing published bytes hold fixture release. Historical manually revoked codes remain historical without invented audit. No actual discount authority, mail, post-backup completeness or real reopening is inferred.

## Verification

RED79b78c7 is ordinarily pushed: one authenticated staff assertion fails because Assigned discounts is absent. [Actual RED record](../evidence/shb/discount-admin-red-2026-11-02.json), private diagnostic .scratch/shb-discount-admin-red-2026-11-02.log. No import/setup failure.

The first focused run applied0027/0028 and passed schema drift. It ran16 cases with two failed expectations and one fixture error: combined fault cases reused a deliberately immutable orphan archive, and recovery assessment was attempted before quarantine. Fault cases now isolate their own fixtures and explicitly assert the existing503 uncertainty hold; recovery inspection follows quarantine. The original reserved ASIC offer already passed its acceptance/payment regression at the unchanged875000 synthetic minor-unit total and50 hours. Final focused verification passes **27 checks**:17 discount-administration cases, one staff-navigation assertion and nine source/catalog checks. [Focused source record](../evidence/shb/retained-tests/e82a8d31e4cee66b558548a10df7ca26446f94e5447b8e599f3ed06cb1595324.json).

The final shared lane passes **583 tests**, none failed/skipped:240 SHB,95 access/recovery,104 payment,30 staff,24 worker/statement-mail,75 shared transactions/archive, nine source/catalog and six actual network-isolated adapter cases. Django check,0027/0028 and migration drift pass. [Final regression/source record](../evidence/shb/retained-tests/12bf40be73b635be6c478375030776b711118323f4f3c9ec5db43a2695e35264.json).

Actual Chromium151.0.7922.173/Node24.15.0 passes **147 checks**:71 customer/76 staff, JS/no-JS/320px. Both native discount revocations enforce CSRF, retain original claim clocks and hide codes/verifiers; backend inspection validates the two archives. Existing native invitation reissue/retry, customer-session denial, FPGA/ASIC purchases, refunds and original coupon/order/notice facts remain intact. [Final browser/source record](../evidence/shb/retained-tests/afbf88024a843a4444b21f055e5f73567bebb5d52941c3c5275628a838601ae6.json); private evidence .scratch/shb-checkout-browser-aryd5bay. All three records bind identical372 backend/eight-script hashes. Planning activity3 tests pass and both planning checks run before commit. All owned contexts completed; no async job.

## Reproduce

```sh
python3 scripts/check_shb_retained.py --test-label shop.shb.discount_admin_tests.DiscountAdminTests --test-label shop.shb.invitation_admin_tests.InvitationAdminTests.test_staff_home_exposes_scoped_discount_administration
python3 scripts/check_shb_retained.py --shared
python3 scripts/check_shb_retained.py --browser --release .scratch/shb-private-resume-t2p3r5cc/release --browser-binary /nix/store/53p8msmqxpi829zdrw6qkvaamidxy9cj-chromium-151.0.7922.173/bin/chromium --browser-node /nix/store/5a8ysg1jnj8jmzzyfcfw7rvpvnp5rfpa-nodejs-24.15.0/bin/node
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

Protected discount issuance remains follow-up work with separate customer/mode/percentage/use/period authority. Existing fixture helpers are not commercial adoption; revocation and invitation grants cannot authorize issuance. Company inputs arrive later without repeated requests. All normal pinned Nix/source/runtime/native/licence/OCI/CI and actual company/provider/refund/tax/mail/host/ingress/database/human/independent custody/post-backup/transport/restore/complete-loss qualification remain open. The independent off-host runner is unassigned. No real credentials/.env, production/bank-sandbox connection, host/DNS/TLS/bank/mail/storage operation or paid provision. The private Astro release and unrelated http_cache.sqlite remain unchanged. Parent counts stay11/42 retained summaries and1/14 documentary phases; no new SUMMARY/FULL_PASS.

Implementation `34c00196f5a9c0b3e43155927c2ee7ad561f800d` is committed and ordinarily pushed to origin/main. The user explicitly requested $gsd-pause-work after the push; synchronized handoffs retain the next protected discount issuance task and all current gates.
