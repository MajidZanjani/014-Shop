# SHB continuation checkpoint

Current authority: [SHB revision 1.1](../014-Shop-SHB-Proposal-Revision-2026-10-30.md). STATE.md / ROADMAP.md remain operative.

**Current development focus:** 6 — Invitation scope, verified resources and staff MFA.

**Last fully completed phase:** 1 — documentary authority/reconciliation only.

**Current plan:** 06-01 — protected invitation issuance/reissue, scoped discount revocation and separate protected discount issuance verified locally; actual qualification remains open.

**Execution status:** paused — explicit user gsd-pause-work during focused lifecycle-test addition after pushed605 tests/161 browser checks through b04b955; two follow-up tests pass focused but remain uncommitted and the shared regression rerun was interrupted mid-run.

**Next implementation task:** After explicit resume, commit the two uncommitted follow-up tests (end-to-end issue→revoke lifecycle in discount_issuance_tests.py; mirror discount-admin nav assertion in discount_admin_tests.py), rerun the shared regression lane (expect607 total: 264 SHB), stage the new focused evidence record and bump test counts/state_head across STATE/PROJECT/ROADMAP/HANDOFF/06-01-PLAN and docs/build/shb-discount-issuance-2026-11-02.md, then push. Normal pinned and actual external gates remain closed.

**Recorded implementation:** a7072ffbfe3664af2764c42954b95c8eae250c26

All three protected staff components for06-01 are ordinarily pushed to origin/main: invitation issuance/reissue4db2586, scoped discount revocation34c0019 and separate scoped discount issuance e5ec3dd; RED7567254/79b78c7/705c2de are also pushed. [Issuance behavior/evidence/commands](../docs/build/shb-invitation-issuance-2026-11-02.md), [current discount revocation behavior/evidence/commands](../docs/build/shb-discount-revocation-2026-11-02.md) and [current discount issuance behavior/evidence/commands](../docs/build/shb-discount-issuance-2026-11-02.md).

Current605 tests/161 actual Chromium checks (71 customer/90 staff, JS/no-JS/320px), focused21 and migration0027/0028/0029/0030/drift pass. Final regression48448c3c and browser45bcdeab bind the new retained source identity. Current browser evidence .scratch/shb-checkout-browser-k67relwn; private9-file Astro release unchanged. No unfinished code/current failure, owned process or async job.

Separate immutable eligibility scopes/exact grants authorize deliberate invitation POST; digest-only intents precede archive/atomic publication, one creating response shows the bearer, and inactive-source reissues retain original clocks. Discount revocation requires its own exact grant/current MFA/epoch/CSRF; archived immutable audit and revocation commit together. It stops new claims while held/accepted offers still accept/pay once at the original concession. Uncertain archive publication followed by rollback stays held with503, never overwritten with fresh bytes. Protected discount issuance now registers synthetic commercial authority (customer/variant/percentage/use-limit/claim-period) as an immutable scope with a per-staff issuance grant distinct from invitation eligibility and revoke grants; digest-only prepared intent precedes atomic DiscountCode publication, the raw code appears once in the issuing response and retries re-use the same intent. Reset/selected restore clear mutable issue/revoke/issuance assignments and retain audit; missing archives hold fixture recovery. No contact adoption, raw-code recovery, real commercial authority/mail/time accounting or customer panel.

All normal pinned Nix/source/runtime/native/licence/OCI/CI and actual company/provider/refund/tax/mail/host/ingress/database/human/independent custody/post-backup/transport/restore/complete-loss qualifications remain open. Independent off-host runner unassigned. No parent SUMMARY/FULL_PASS/count change:11/42 retained summaries and1/14 documentary phases. No .env/unrelated cache access, actual protected/bank/mail/storage/DNS/TLS operation, production/bank-sandbox connection or paid provision.
