# Configuration-draft commands and private reads across local recovery — 2026-10-28

Status: concrete local draft recovery gap reproduced and fixed. Focused135 tests/26.803s, current backend726/5/229.455s, supported demo/proxy148/2 and exact276-file source pass. Actual recovery and full Phase13 acceptance remain pending.

Implementation: `82fa759cdda37bb22406b5ced6ac7ca6ff372a98`, committed locally. This is local/synthetic evidence only; actual synchronization comes from Git refs.

## Behavior

Configuration-draft save/list/get relied on local_customer at entry. A quarantine or completed quarantine/release after ordinary JSON evaluation could still create a draft or expose its exact-retry payload. List/get could return private owner records after recovery between entry authorization and the query.

Each bounded draft transaction now calls the existing current_session_epoch(lock=True) predicate before private queries. List/get serialize their response while holding that epoch; save/replay check inside the original storage transaction and serialize there too. All stale cases return only the fixed verification_required403/no-store error. No private response is materialized outside its authorized database operation.

Fresh verification resumes the same retained identity/content without another row. Current-catalog admission order remains unchanged: even an exact existing retry still returns stale_catalog409 after the current catalog changes, as it did before this fix. Owner filters, conflicting-request rejection,20-row list bound, normal CSRF, configuration validation and unaccepted local-only scope remain. This does not turn a saved draft into acceptance, financial evidence, a host binding or rights.

The epoch lock serializes these bounded local database operations with recovery. Actual transmission, confidential channels, post-point customer/resource/MFA reconstruction, custody and independent off-host restore remain unqualified. No model, migration, dependency, runtime pin, timeout, public route or external/protected operation is added.

## Evidence

- Original product at5a1f5ea:10 tests/13 failed assertions in1.363s, `.scratch/draft-recovery-baseline.log`. Normal CSRF-checked JSON parsing/evaluation precedes the controlled quarantine or quarantine/release. New draft rows, exact-retry disclosure and private list/get data reproduce the gap. Response and committed-row assertions are separate. No baseline test errors; the existing catalog-admission case already passes.
- Original-source control after the fix: the same10-test fixture fails13 assertions in1.388s, `.scratch/draft-recovery-final-baseline.log`. `.scratch/draft-recovery-control.py` substitutes only views.py from5a1f5ea and restores fixed bytes in a guarded finally block; `.scratch/draft-recovery-control.log` confirms exact restoration. No baseline test errors.
- Fixed focused135 tests pass in26.803s, `.scratch/draft-recovery-focused.log`. All10 new cases cover saves/replays, held/released epochs, private list/get, fresh verified retry identity, unchanged current-catalog admission and independent PostgreSQL55P03 lock observations before all draft queries. Existing pure catalog/form, owner/Unicode/CSRF/race, cart/native/quotation and access/effect/startup recovery regressions pass in the same run. The controlled baseline restores that exact fixed source.
- Current-source `CORE_LOCAL_PASS checks=5 tests=726 duration_seconds=229.455`, `.scratch/draft-recovery-core.log`. Frozen Python3.13.16/Django5.2.18/PostgreSQL18.6/UTF8, migrations/no drift and existing bounds pass. The lane explicitly retains `PENDING_OFF_HOST`.
- Supported complete-cart customer/staff demo and owned loopback proxy/Gunicorn/PostgreSQL: `DEMO_ACCESS_PASS checks=148 aliases=2 evidence=local-synthetic-header-level`, `.scratch/draft-recovery-proxy.log`. Existing staff two-factor/resource scope, once-only grants/support and staged delivery remain. Header-level evidence is not an actual browser/financial/recovery qualification.
- Inert source `/nix/store/y8zmxl80nqnp4hwxxbpipgq1vyr8ral7-shop-python-source`:276 exact allowed files/33 templates/1 CSS/no symlinks. `.scratch/draft-recovery-source-path`, `.scratch/draft-recovery-source-build.log` and `.scratch/draft-recovery-source-qualified.log` retain exact path/build/byte evidence. Unchanged frontend/browser/worker lanes retain their earlier scopes and were not repeated for this draft transaction change.

Focused command: `TMPDIR="$PWD/.scratch/auth-unicode-tmp" nix develop --offline ./ops/nixos#backend --command python3 .scratch/draft-recovery-focused.py focused`. Baseline mode selects the10-case fixture; the guarded original-source control uses `.scratch/draft-recovery-control.py`. Full core uses `/tmp/shop-dispatch-core.py`; HTTP uses the unchanged `.scratch/support-recovery-proxy.py`; exact source uses `.scratch/check-recovery-commit-source.py .scratch/draft-recovery-source-path`. Retained hash-checked wheels and owned disposable PostgreSQL are used. Per-process tests remain120 seconds/at-most20 labels and core outer900 seconds. Shared /tmp remains untouched.

## Remaining work

A finite read-only audit found the separate quotation source observation: quotations passes only(request.user,value) to capture_quotation after JSON parsing, and quotation_capture uses its separately imported alias after native payload parsing. The service locks the cart without an originating customer epoch; list/detail and native capture-page reads also follow only entry authorization. This is not reproduced, designed or fixed. Start a new GSD task and establish original PostgreSQL behavior before changes; preserve exact snapshot/key retry and staff-review history.

All company commercial revision/approver inputs will be supplied later; do not re-ask or infer approval. Actual channels/custody/retention, post-point customer/resource/MFA/source evidence, selected-bank/provider authority, assigned independent runtime/recovery target and formal decisions remain pending under the [finite register](13-QUALIFICATION-REGISTER.md). No full Phase13 SUMMARY or actual recovery qualification.
