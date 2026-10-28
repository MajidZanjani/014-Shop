# Quotation capture and private reads across local recovery — 2026-10-28

Status: concrete local quotation recovery gap reproduced and fixed. Focused166/32.359s, current backend752/5/234.449s, supported proxy148/2 and exact276-file source pass. Actual recovery and full Phase13 acceptance remain pending.

Implementation `c356d75b13c66f3f58bb98069bfb18e652dfeb67` is committed locally and recorded in the quick completion artifacts. This evidence is local/synthetic only; Git refs determine actual remote synchronization.

## Behavior

Original product at3611e38 relied on entry-only customer access. Normal CSRF-checked JSON/native parsing could precede quarantine or completed quarantine/release, after which capture still created a request/key, returned an existing private quotation or bound a second key to the same snapshot. Private API list/detail and native capture-page/error reads also survived the reset.

Each HTTP capture alias now passes its originating request into the existing capture transaction. That transaction locks the valid epoch before cart/quotation work and materializes the result while locked. API list/detail and native capture-page/error reads acquire the same epoch before private resource queries; native rendering stays inside its bounded read transaction. Stale calls return fixed verification_required403/no-store without a private form. No enclosing transaction wraps the independent capture service or provider I/O.

Fresh verification resumes exact request/key identities. A second key still binds the same snapshot without another quotation. Later cart/catalog edits preserve historical retries and current staff-review history. Owner/cross-cart filters, normal CSRF, strict parsers,20-row API list bound, immutable snapshots and trusted no-request fixture calls retain their contracts. No approved offer, acceptance, payment, licence or support credit is created by quotation capture.

## Evidence

- Original product at3611e38:26 tests/34 failed assertions in4.574s, `.scratch/quotation-recovery-baseline.log`. Response and committed request/key/cart/snapshot/review facts are separate assertions; no test errors. Trusted internal calls and fresh historical replay already pass on the original code.
- Guarded original-source control:26 tests/34 failed assertions in4.479s, `.scratch/quotation-recovery-final-baseline.log`. `.scratch/quotation-recovery-control.py` substitutes only quotation_views.py/quotation_capture.py from3611e38; `.scratch/quotation-recovery-control.log` confirms both fixed byte sequences restored exactly. No test errors.
- Fixed focused166 tests/32.359s, `.scratch/quotation-recovery-focused.log`. All26 recovery cases and existing quotation/API/native/history/cart/draft/access/effect/startup regressions pass. Independent PostgreSQL NOWAIT probes observe55P03 before resource queries and at JSON serialization/native rendering. Fresh historical replay retains captured lines and review events after later cart/catalog changes.
- Current-source `CORE_LOCAL_PASS checks=5 tests=752 duration_seconds=234.449`, `.scratch/quotation-recovery-core.log`. Frozen Python3.13.16/Django5.2.18/PostgreSQL18.6/UTF8, migrations/no drift and existing process bounds pass. The lane explicitly retains `PENDING_OFF_HOST`.
- Supported complete-cart customer/staff demo through owned loopback proxy/Gunicorn/PostgreSQL: `DEMO_ACCESS_PASS checks=148 aliases=2 evidence=local-synthetic-header-level`, `.scratch/quotation-recovery-proxy.log`. Existing staff two-factor/resource scope, once-only grants/support and staged delivery retain scope. This is header-level local evidence, not actual browser/financial/recovery qualification.
- Inert source `/nix/store/bd5xqx82naciws21ywcspgzn6b7jsbjn-shop-python-source`:276 exact allowed files/33 templates/1 CSS/no symlinks, `.scratch/quotation-recovery-source-path`, source-build.log and source-qualified.log. Four planning/inventory tests plus planning/source-authority/diff checks pass. Unchanged frontend/browser/worker lanes retain earlier source scopes and were not repeated for this quotation transaction change.

Focused command: `TMPDIR="$PWD/.scratch/auth-unicode-tmp" nix develop --offline ./ops/nixos#backend --command python3 .scratch/quotation-recovery-focused.py focused`. Baseline mode selects the26 recovery cases; original control uses quotation-recovery-control.py. Complete core uses the retained /tmp/shop-dispatch-core.py; supported HTTP uses the unchanged .scratch/support-recovery-proxy.py; exact source uses .scratch/check-recovery-commit-source.py with .scratch/quotation-recovery-source-path. Retained hash-checked cached wheels and owned disposable PostgreSQL are used. Per-test processes remain120 seconds/at-most20 labels; core outer bound stays900 seconds. Shared /tmp is untouched.

## Remaining work

Read-only source review found a separate finite observation in native quotation history, timeline and document-preview pages: each uses only entry authorization before private queries/rendering. Reproduce those actual aliases and cursor reads under a new GSD task before edits; they are not reproduced, designed or fixed by this batch.

No model, migration, dependency, runtime pin, timeout, public route or external/protected operation changed. Local database serialization does not qualify actual transport, post-point customer/resource/revocation/MFA reconciliation, custody or independent off-host recovery. Company commercial revision/approver information will be supplied later; do not re-ask or infer approval. All actual gates remain pending under the [finite register](13-QUALIFICATION-REGISTER.md); no full Phase13 SUMMARY or actual recovery qualification.
