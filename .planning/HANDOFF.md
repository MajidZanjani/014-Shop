# SHB continuation checkpoint

Current authority: [SHB revision 1.1](../014-Shop-SHB-Proposal-Revision-2026-10-30.md). STATE.md / ROADMAP.md remain operative.

**Current development focus:** 6 — Invitation scope, verified resources and staff MFA.

**Last fully completed phase:** 1 — documentary authority/reconciliation only.

**Current plan:** 06-01 — protected invitation issuance/reissue and scoped discount revocation verified locally; protected discount issuance/actual qualification open.

**Execution status:** paused — explicit user gsd-pause-work after pushed protected invitation issuance/reissue and discount revocation;583 tests/147 browser checks retained; discount issuance and actual qualification remain open.

**Next implementation task:** After explicit resume, inspect existing discount fixture issuance and invitation intent/scope patterns, then implement protected discount issuance with separate explicit synthetic customer/variant/percentage/use-limit/claim-period authority and a durable digest-only intent/one-time code response. Preserve original clocks and held concessions; invitation/revocation grants and entered contact never establish commercial authority.

**Recorded implementation:** 34c00196f5a9c0b3e43155927c2ee7ad561f800d

Both protected staff components are ordinarily pushed to origin/main: invitation issuance/reissue4db2586 and scoped discount revocation34c0019; RED7567254/79b78c7 are also pushed. [Issuance behavior/evidence/commands](../docs/build/shb-invitation-issuance-2026-11-02.md) and [current discount behavior/evidence/commands](../docs/build/shb-discount-revocation-2026-11-02.md).

Current583 tests/147 actual Chromium checks (71 customer/76 staff, JS/no-JS/320px), focused27 and migration0027/0028/drift pass. Final regression12bf40be/browserafbf8802/focusede82a8d31 bind identical372 backend/eight-script hashes. Earlier issuance565/137 records retain their exact373-source identity. Current browser evidence .scratch/shb-checkout-browser-aryd5bay; private9-file Astro release unchanged. No unfinished code/current failure, owned process or async job. Only unrelated http_cache.sqlite was untracked before checkpoint metadata.

Separate immutable eligibility scopes/exact grants authorize deliberate invitation POST; digest-only intents precede archive/atomic publication, one creating response shows the bearer, and inactive-source reissues retain original clocks. Discount revocation requires its own exact grant/current MFA/epoch/CSRF; archived immutable audit and revocation commit together. It stops new claims while held/accepted offers still accept/pay once at the original concession. Uncertain archive publication followed by rollback stays held with503, never overwritten with fresh bytes. Reset/selected restore clear mutable issue/revoke assignments and retain audit; missing archives hold fixture recovery. No contact adoption, raw-code recovery, real commercial authority/mail/time accounting or customer panel.

Protected discount issuance remains next; current helpers are fixture-only. It needs independent explicit customer/variant/percentage/use/claim-period authority, a digest-only prepared intent before archive/publication, one-time raw response and exact retry/uncertainty behavior. Reuse the invitation intent pattern without treating eligibility/revocation grants as commercial authority. Company inputs arrive later in docs/decisions.md without repeated requests.

All normal pinned Nix/source/runtime/native/licence/OCI/CI and actual company/provider/refund/tax/mail/host/ingress/database/human/independent custody/post-backup/transport/restore/complete-loss qualifications remain open. Independent off-host runner unassigned. No parent SUMMARY/FULL_PASS/count change:11/42 retained summaries and1/14 documentary phases. No .env/unrelated cache access, actual protected/bank/mail/storage/DNS/TLS operation, production/bank-sandbox connection or paid provision. This is an explicit user pause. Exact context percentage is unavailable. Resume with $gsd-resume-work.
