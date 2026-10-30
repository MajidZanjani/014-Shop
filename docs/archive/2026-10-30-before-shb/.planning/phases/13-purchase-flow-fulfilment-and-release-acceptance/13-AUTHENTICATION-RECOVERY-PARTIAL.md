# Authentication crossing quarantine — local partial evidence

2026-10-28; quick261028-aq1 under13-01 task5, OPS-02/AUTH-01/AUTH-03/UAT-03. Continues the verified d3ea121 effect-admission component and492c67b task record. Commercial revisions/approver evidence remain pending by user instruction.

## Reproduced defect and fix

The original normal customer CSRF/code flow consumes a challenge, then logs in outside its challenge transaction. A controlled pause at that login allowed local quarantine and matching synthetic release to finish first. The original verified code then logged in and received the freshly released epoch. The new regression fails on the original implementation: old code authenticated after recovery release. This is an observed local race, not a claim about actual restored production access.

Customer code capture/verification and both staff authentication factors now hold durable local admissions for their entire authentication body. Quarantine closes new admission and reports any active authentication scopes. Synthetic release refuses unfinished authentication, alongside existing worker/provider scopes. Authentication additionally requires its original unheld admission epoch before returning. A changed epoch/hold returns a fixed private recovery503, including the existing customer form route; it cannot report a stale successful verification or captured code as current access. Existing login signal/session-generation authorization remains server-owned.

No new public recovery route, channel or MFA bypass. Existing parsers, throttles/attempt limits, one-use codes, password and possession factors, session/CSRF rotation and exact resource checks remain. Two older customer TestCase fixtures now use TransactionTestCase so the actual service retains its autocommit/durable-transaction requirement. No production guard is relaxed for test transactions. Actual MFA recovery codes, external revocation reconciliation, startup/traffic/egress isolation, off-host complete-loss recovery and safe reopening remain unqualified.

## Local verification

Original-code baseline:1 test fails in0.174s, with authenticated=true after the controlled quarantine/release. Retained log .scratch/auth-recovery-baseline.log; this failure is not a pass.

Final focused access/recovery/consumer regression:63 PostgreSQL tests pass in17.695s. Six new tests cover the reproduced customer JSON flow, the no-JavaScript form flow with visible fixed recovery guidance, customer capture finishing after quarantine, staff password capture and second-factor verification crossing the hold, refused synthetic release while those scopes run, stale code denial, fresh customer/both-staff-factor recovery and fixed outer-transaction denial without a challenge/admission. Existing source/attempt/CSRF/Unicode/MFA/resource and effect-boundary tests pass in that run.

Pinned Django5.2.18 generates/applies access0007_authentication_effect_kinds on disposable PostgreSQL18.6; no drift. The existing one-way admission-history trigger remains. Inert source /nix/store/9ky12djzmparnw62ip6d5692w4yrqklv-shop-python-source matches272 allowlisted files/33 templates/1 CSS byte for byte, no symlinks. Final CORE_LOCAL_PASS checks=5 tests=624 duration_seconds=194.530, enclosing196.00292526604608s, failures0. Sequential supported complete-cart/two-factor/proxy passes DEMO_ACCESS_PASS checks=148 aliases=2 evidence=local-synthetic-header-level. All scoped producers completed; no actual/full recovery acceptance is inferred.

## Reproduction and boundaries

Owned TMPDIR .scratch/auth-unicode-tmp and the frozen ops/nixos#browser shell remain; the full shared128MiB /tmp is untouched. .scratch/auth-recovery-{baseline,migration,focused}.py use only newly disposable PostgreSQL and the existing retained locked-wheel cache. Full/proxy wrappers remain /tmp/shop-dispatch-core.py and /tmp/shop-ledger-proxy.py. Logs .scratch/auth-recovery-{baseline,migration,focused,core,proxy,source,source-qualified}.log retain exact attempts. Existing120-second Django batches/900-second enclosing core limits and request/provider/database bounds are unchanged.

All evidence is local/synthetic. No actual mail, bank, host, DNS/TLS, deployment, restoration or new commercial/legal approval. Prior worker24/6 and network-isolated adapters6/3 retain their d3ea121 scope; frontend132/parity117 and browser224 retain their earlier source scope. This task adds no new browser/hosted-CI/formal or full phase acceptance.
