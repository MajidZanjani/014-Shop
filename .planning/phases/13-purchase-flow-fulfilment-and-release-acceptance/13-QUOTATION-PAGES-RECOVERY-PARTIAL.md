# Native quotation page reads across local recovery — 2026-10-28

Status: native quotation history/cursor, timeline and document-preview gaps reproduced and fixed locally. Focused126/27.980s, current backend761/5/234.820s, supported proxy148/2 and exact276-file source pass. Actual recovery/full Phase13 acceptance remains pending.

Implementation `49f714b29db41962701c1f127196e226f81c3418` is committed and recorded in quick completion artifacts. Git refs determine actual remote synchronization.

## Behavior

Original product at224f87e checked local_customer only at entry. Quarantine or completed quarantine/release after that check still allowed private history, an owner-specific cursor lookup, timeline events and source document preview to render. Immutable cart/request/key/review facts did not change, and fresh verification restored normal reads.

Each handler now opens a bounded read transaction, locks the originating epoch before private queries, including cursor anchoring, and materializes HTML while locked. Stale reads return fixed verification_required403/no-store without the private quotation identifier. Bounded keyset pagination, committed-prefix timeline events/current status, source declarations/preview scope, owner/cross-cart filters, read-only immutable history and existing successful headers retain their contracts. No provider or independent durable service runs under these locks.

## Evidence

- Original224f87e PostgreSQL control:9 tests/9 failed assertions in1.367s, no test errors, `.scratch/quotation-page-recovery-baseline.log`. Separate response/fact checks cover held/released history, cursor, timeline and document preview.
- Guarded original-source control:9 tests/9 failures in1.434s, no errors, `.scratch/quotation-page-recovery-final-baseline.log`. `.scratch/quotation-page-recovery-control.py` substitutes only the three product files from224f87e; control.log confirms all fixed byte sequences restored exactly.
- Fixed focused126 tests/27.980s, `.scratch/quotation-page-recovery-focused.log`. Existing history pagination/concurrent insertion/ownership, timeline committed-prefix/review/privacy, document declarations/scope/business metadata, quotation/API/native/business/access/recovery/startup tests pass. Independent PostgreSQL NOWAIT probes observe55P03 before all page resource queries and during rendering, including cursor anchoring.
- Current-source `CORE_LOCAL_PASS checks=5 tests=761 duration_seconds=234.820`, `.scratch/quotation-page-recovery-core.log`; frozen Python3.13.16/Django5.2.18/PostgreSQL18.6/UTF8, migrations/no drift and existing process bounds pass. `PENDING_OFF_HOST` remains explicit.
- Supported complete-cart customer/staff proxy/Gunicorn/PostgreSQL: `DEMO_ACCESS_PASS checks=148 aliases=2 evidence=local-synthetic-header-level`, `.scratch/quotation-page-recovery-proxy.log`. No actual browser/financial/recovery qualification is inferred.
- Inert source `/nix/store/gg70qr3r7vpxipnl9669qlv52q0kphsa-shop-python-source`:276 exact files/33 templates/1 CSS/no symlinks. `.scratch/quotation-page-recovery-source-path`, source-build.log and source-qualified.log retain build/byte evidence. Four planning/inventory tests, planning/source-authority and diff checks pass. Unchanged frontend/browser/worker lanes retain earlier scopes and were not repeated for this bounded read change.

Focused command: `TMPDIR="$PWD/.scratch/auth-unicode-tmp" nix develop --offline ./ops/nixos#backend --command python3 .scratch/quotation-page-recovery-focused.py focused`; baseline selects the9 recovery cases. Guarded control uses quotation-page-recovery-control.py. Complete core uses retained /tmp/shop-dispatch-core.py, HTTP uses unchanged .scratch/support-recovery-proxy.py and exact source uses .scratch/check-recovery-commit-source.py with the retained source-path. Cached hash-checked wheels and owned disposable PostgreSQL are used. Tests remain120 seconds/at-most20 labels; core outer remains900 seconds. Shared /tmp is untouched.

## Remaining work

Finite read-only source review found separate cached-authority business draft/save/private-read and quotation business-attachment boundaries in business_views.py/business_binding_views.py. These are unreproduced/unimplemented; start a new GSD task and establish original normal-form PostgreSQL behavior before edits, preserving immutable facts, exact retry, source/schema/CAS order and cleaned-only redisplay.

No model, migration, dependency, runtime pin, timeout, public route or external/protected operation changed. Local read serialization does not qualify actual transmission, access channels, post-point customer/resource/revocation/MFA reconciliation, custody or independent off-host recovery. Company commercial inputs will be supplied later; do not re-ask. All actual/formal/full acceptance gates remain pending under the [finite register](13-QUALIFICATION-REGISTER.md); no full Phase13 SUMMARY.
