# Private package access across local recovery —2026-10-28

Status: concrete local package authority gap reproduced, fixed and verified; focused136 tests, current backend657/5 and exact source pass. Actual recovery, confidential material delivery and full acceptance remain pending.

Implementation: `7e410f97160abf2b92cb9ce25fa1b392928141a2`, committed and pushed.

## Behavior

The package services previously relied on the request's cached session key after the view's customer check. A request already admitted before local quarantine could still issue a new bearer or consume an existing download after quarantine or release. A newly selected external restore identity also failed to stop these cached service calls before explicit quarantine.

Both existing package transactions now require a current customer epoch in PostgreSQL locking mode before any owner/resource work. The epoch remains locked through bounded fake-local archive verification and transaction commit, serializing quarantine with the operation. A stale/missing epoch or pending selected restore produces the existing opaque `download_unavailable` denial, with no grant or consumption effect. Ordinary epoch authorization remains read-only and never initializes a row. The locking mode requires an active PostgreSQL transaction.

Epoch-before-owner ordering avoids a new cycle through quarantine's epoch/credential locks and staff work waiting for an owner. Current owner/resource, archive, artifact/version, delivery hold, session, expiry and single-use checks remain. No model, migration, dependency, middleware, public route or actual bank/mail/network archive operation was added. [Local recovery procedure](../../../docs/local-recovery.md).

The lock covers the local domain transaction, not transmission of prepared response bytes or actual process/traffic quiescence. It neither reconstructs actual customer revocations nor qualifies confidential technical intake, actual materials/keys, custody, retention or independent restore.

## Evidence

- Initial original-code diagnostic: five tests/nine failures in2.011s; `.scratch/package-recovery-baseline.log`.
- Final original-code baseline: seven tests/nine failures in2.733s; `.scratch/package-recovery-order-baseline.log`. Separate held/released requests issue or consume despite stale authority; selected-startup cases also change grant state. A second PostgreSQL connection can obtain the epoch row before owner work and during archive verification, showing the missing serialization. These are controlled cached domain-request fixtures, not a live restoration or independent network-transport drill.
- Fixed focused136 tests pass in48.674s; `.scratch/package-recovery-focused.log`. Seven added tests cover both operations after quarantine/release, selected startup before quarantine, unchanged denied access state, fresh-session recovery with old bearer rejection, and independent NOWAIT probes before owner work and during real local archive verification. Existing package/delivery, recovery/startup/staff reset, authentication and effect admission tests pass in the same run.
- Inert source `/nix/store/f55y76z7s505bkmhb79wgwip3zq7sv2g-shop-python-source`:276 exact allowed files/33 templates/1 CSS/no symlinks. `.scratch/package-recovery-source-{build,qualified}.log` and `.scratch/package-recovery-source-path` retain the exact source evidence.
- Current-source `CORE_LOCAL_PASS checks=5 tests=657 duration_seconds=209.468`; enclosing lane211.004s, zero failures. Frozen Python3.13.16/Django5.2.18 and real PostgreSQL18.6/UTF8 retain their exact identity; migrations/no drift and unchanged test bounds pass. `.scratch/package-recovery-core.log` retains the explicit `PENDING_OFF_HOST` qualification boundary. No unchanged browser/frontend/proxy lane is rerun for this internal package boundary; their prior evidence retains its exact recorded scope.

Baseline/focused commands use `.scratch/package-recovery-focused.py baseline|focused` within the unchanged `ops/nixos#backend` shell and existing hash-checked cached-wheel/prepared_database setup. The core lane uses `/tmp/shop-dispatch-core.py` around `scripts/check_backend.py core-local`. Owned TMPDIR is `.scratch/auth-unicode-tmp`; at-most20 labels/120-second batches and900-second outer remain. No shared cleanup or protected/external operation.

## Remaining work

The finite [qualification register](13-QUALIFICATION-REGISTER.md) retains every actual revocation/MFA/channel/custody/runner/provider/formal/commercial gate. Company commercial inputs will be supplied later and remain pending. No full Phase13 SUMMARY or actual recovery qualification is justified.

Next independent review: `support_views.handle` checks the customer before parsing a POST, then passes a cached owner into ledger/follow-up services. Reproduce quarantine after the normal command parser returns but before the service starts; inspect whether reservation/release/context can commit. This source observation is not yet a reproduced support defect or implemented support fence.
