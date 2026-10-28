# Selected local restore staff reset —2026-10-28

Status: local component verified; OPS-02/AUTH-04/UAT-03 and actual/full acceptance remain partial. This is conservative removal of restored local staff authority, not reconstruction of actual post-point revocations or consumed MFA recovery codes.

## Behavior

The earlier startup fence required fresh authentication after synthetic release but left restored staff credentials enabled and their assignments intact. A snapshot from before a revocation could therefore regain old assignments after fresh sign-in. The existing local staff operator already clears seven grant types on reset/revoke; this implementation shares that exact finite removal set.

Only a newly recorded quarantine whose request identity equals configured `LOCAL_RESTORE_ID` disables all restored staff credentials and clears quotation/business, support, delivery, licence-case, support-refund, overpayment and payment-operation assignments. Nonprivate removal counts are retained in the immutable recovery operation. Credential generation/session/challenge invalidation, credential disabling, every assignment removal and the operation record commit in the same PostgreSQL transaction. A failure rolls everything back.

Release never enables credentials or reassigns resources. Existing explicit `local_staff reset` supplies a new private local password, followed by both login factors; it grants no resource assignment. Each resource still requires the existing explicit operator grant. Exact replay of the earlier quarantine returns its original counts without touching fresh credentials, sessions or assignments. Ordinary temporary holds, including later holds after startup completion, retain their grant-preserving behavior. The shared helper is local/fake/PostgreSQL/transaction-only; operator reset/revoke remains scoped to its named user.

Accepted checkout/business/payment/licence/support-work/case history remains unchanged. Existing generation binding continues to invalidate older prepared staff authorizations; it does not issue new authority. Customer sessions/challenges still require fresh verification. Actual customer/resource post-point revocation reconstruction, real MFA recovery/reset and off-host custody remain pending. [Current local procedure](../../../docs/local-recovery.md).

## Evidence

- Pre-fix real-PostgreSQL failure: after matching selected quarantine/release the restored staff credential remained enabled. One test failed in0.686s; `.scratch/staff-restore-baseline.log` retains the result.
- Final focused97 tests pass in30.201s. Eight new tests use a coherent paid-cart/archived grant, committed600-second support work, licence/refund cases and every one of the seven grant types for two staff users. They prove removal counts and unchanged business/money/work/case rows, ordinary/wrong-identity holds, real reset/password/possession-factor login, no resource authority until explicit regrant, replay after reassignment, all-or-nothing failure rollback, per-user operator isolation and helper mode/transaction guards. `.scratch/staff-restore-focused.log` retains the result.
- Current-source `CORE_LOCAL_PASS checks=5 tests=645 duration_seconds=204.753`; enclosing lane206.242s. Real PostgreSQL18.6/UTF8 and frozen Python3.13.16/Django5.2.18 remain; migrations/no drift pass. At most20 labels per120s batch and900s outer are unchanged. No skipped labels or relaxed statement/production/provider bounds. `PENDING_OFF_HOST` remains explicit. `.scratch/staff-restore-core.log` retains the result.
- Fresh supported complete-cart demo and actual loopback proxy/Gunicorn/PostgreSQL pass: `DEMO_ACCESS_PASS checks=148 aliases=2 evidence=local-synthetic-header-level`. Normal staff provision and two-factor purchase paths run through the loopback process; reset/revoke scope is verified by the focused backend suite. This is not a browser-engine or actual restore drill. `.scratch/staff-restore-proxy.log` retains the result.
- Inert app source `/nix/store/gdy1y86qzdagbsz5ypan9a48z7zrzs19-shop-python-source`:276 allowed files,33 templates,1 CSS, exact paths/bytes and no symlinks. Owned new inputs were staged before the Git-backed build. `.scratch/staff-restore-source{,-qualified}.log` retain evidence.
- Prior frontend137/32, catalog117/121 and browser227 retain db56df3 scope; frontend source is unchanged. Worker24/6/adapters6/3 retain their documented earlier scope. No actual qualification is inferred.

The existing pinned frozen-wheel/prepared_database wrappers run the focused modules and complete core-local lane. `/tmp/shop-ledger-proxy.py` runs the supported demo and header-level proxy lane. All newly owned PostgreSQL/app/proxy producers exited; no shared `/tmp` or Nix store cleanup occurred and no protected service was accessed.

## Remaining binding gates

The two reproduced independent local startup/staff-authority gaps are resolved. The grouped [qualification register](13-QUALIFICATION-REGISTER.md) still requires authoritative actual post-point customer/resource revocation and consumed-MFA state, approved channels/custody/retention, selected-bank contracts and scope, and an assigned authorized independent recovery target. No actual completeness, safe-reopen timing, full source acceptance or production authority can be manufactured from these fixtures. Commercial company revisions/approver evidence will be supplied later by the user and remain pending. Continue concrete independent local fixes if a defect or required interface is identified; do not create speculative checks merely to increase counts.
