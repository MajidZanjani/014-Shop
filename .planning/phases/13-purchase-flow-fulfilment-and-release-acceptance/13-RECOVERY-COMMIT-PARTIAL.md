# Committed local recovery transitions —2026-10-28

Status: the concrete local transaction gap is reproduced, fixed and verified by the current full backend, focused checks and exact source comparison. OPS-02/AUTH-04/UAT-03 and actual/full acceptance remain partial.

Implementation: `e71e2f22d3a5846a46a00bae75179143d2ce0870`, committed and pushed.

## Behavior and scope

Previously, the internal local recovery function could nest its transaction inside a caller's atomic block or a manually managed transaction. It returned successful quarantine/release results while an independent PostgreSQL connection still saw the pre-transition state. A caller rollback could then discard the reported transition and its session/challenge/credential changes.

The function now requires autocommit outside an enclosing transaction, returning fixed `AccessRecoveryError('recovery_transaction_active')` before any changes when that condition is absent. Its own durable atomic block commits before returning a result. Mode/adapters, exact disposable database and role checks, immutable operation identities, selected-restore staff reset, current-hold and unfinished-effect checks remain. Failed top-level operations still roll back all their changes. Successful exact retries continue to return retained results without repeating invalidation.

This is a local commit/visibility contract. It does not establish independent retention, actual access revocation completeness, MFA-code recovery, traffic/egress isolation or safe reopening. No HTTP recovery route, production adapter, dependency or migration was added. [Local procedure](../../../docs/local-recovery.md).

## Evidence

- Original-code PostgreSQL baseline: four failures in1.552s, covering quarantine and release under caller atomic and manual transactions. Each case first verified that a second connection retained the full prior fixture state while the function had returned success. `.scratch/recovery-commit-baseline.log` retains the failures.
- Fixed focused102 tests pass in32.272s. Five new tests cover both denied transaction modes/actions, unchanged fixture state before rollback and after the caller exits, and independently visible committed transitions and exact retries. Existing recovery, selected-startup/staff-reset, customer/staff authentication and effect-drain cases remain. Fixture snapshots are compared as digests so private session/challenge contents are not printed. `.scratch/recovery-commit-focused.log` retains the result.
- Current-source `CORE_LOCAL_PASS checks=5 tests=650 duration_seconds=206.973`; enclosing lane208.488s, no failures. Real PostgreSQL18.6/UTF8, frozen Python3.13.16/Django5.2.18, migrations/no drift and unchanged at-most20-label/120-second batches/900-second outer. `.scratch/recovery-commit-core.log` retains the complete result and explicit `PENDING_OFF_HOST` marker.
- Inert source `/nix/store/7gwgkrw185x778n4va9ia6v554bn2p3x-shop-python-source` matches all276 allowed files/33 templates/1 CSS byte for byte, with no symlinks. `.scratch/recovery-commit-source-build.log`, `recovery-commit-source-path` and `recovery-commit-source-qualified.log` retain the build and comparison. No runtime image or deployed service is qualified by this source-only build.
- Prior proxy148/2, frontend137/32 and browser227 retain their recorded preceding scope. No unchanged browser/frontend/proxy lane is repeated for this internal transaction-only change.

Commands use owned `.scratch/auth-unicode-tmp`, the unchanged `ops/nixos#backend` shell and existing hash-checked cached-wheel/prepared_database setup. The baseline/focused wrapper is `.scratch/recovery-transaction-focused.py baseline|focused`; the complete lane is the existing `/tmp/shop-dispatch-core.py` wrapper around `scripts/check_backend.py core-local`. Per-test-process120-second and enclosing900-second core bounds remain. No shared temporary cleanup or protected/external operation is part of this work.

## Remaining actual prerequisites

The finite [qualification register](13-QUALIFICATION-REGISTER.md) remains binding: authoritative post-point customer/resource revocations and consumed-MFA state, approved channels/custody/retention, selected-bank specifications/authority, assigned independent runtime/recovery target and formal human/release evidence. Company commercial revisions/approver evidence will be supplied later and remain pending. This local fix neither supplies those facts nor completes Phase13 or actual recovery acceptance.
