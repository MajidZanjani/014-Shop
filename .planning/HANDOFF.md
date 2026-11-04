# SHB continuation checkpoint

Current authority: [SHB revision 1.1](../014-Shop-SHB-Proposal-Revision-2026-10-30.md) (product specification).
Current planning/execution precedence: [2026-11-04 amendment](../014-Shop-SHB-Claude-Correction-Prompt-2026-11-04.txt) — supersedes conflicting earlier planning/execution instructions only. STATE.md / ROADMAP.md remain operative.

**Current development focus:** 6 — Invitation scope, verified resources and staff MFA.

**Last fully completed phase:** 1 — documentary authority/reconciliation only.

**Current plan:** 06-01 — protected invitation issuance/reissue, scoped discount revocation and separate protected discount issuance verified locally; actual qualification remains open.

**Execution status:** active — R1 (SHB-13 silent-skip) / R2 (silent-skip audit — zero additional instances) / R3 (8 phantom citations repaired) / R4 (SHB suite symmetry via adding shop.shb.discount_issuance_tests to check_shb.py) all closed 2026-11-04. Shared retained lane last recorded 640/297 and browser lane 161 at 2026-11-03 against commit b38dc24; neither rerun (amendment §8 — the R1-R4 changes do not warrant a multi-minute rerun). Next action R5 (CI core-local lane repair + anonymous-catalog 200 assertion removal in scripts/check_backend.py); follow-ups R6..R9 in HANDOFF.md.

**Next implementation task:** R5 — repair the CI core-local lane in scripts/check_backend.py so it exercises SHB modules and genuinely-shared invariants rather than legacy IP/catalog/support-ledger modules (line 127 labels list), and either re-scope or expect-403 the /api/v1/catalog/ anonymous HTTP 200 assertion that contradicts invitation-only SHB (line 147). Move legacy modules into an explicitly identified historical regression lane. Verify with scripts/check.py all. Follow-up R6..R9 in HANDOFF.md; R9 (external gates and off-host runner) remains external.

**Recorded implementation:** b38dc244f78b32fdf3129f1ae49c5112cb1da2a2

## Remaining SHB implementation (local-now unless marked)

Columns — SHB req or shared invariant · concrete files/components · can be done locally now · external dependency (if any) · evidence to close.

| # | Deliverable | SHB ref | Files / components | Local now | External dep | Evidence to close |
|---|---|---|---|---|---|---|
| R1 | ✅ **CLOSED 2026-11-04** — SHB-13 silent-skip fixed; focused `shop.shb.tests.InvitationTests.test_shb_13_valid_link_reuse_and_scanner_get_has_no_side_effect` passes with the three previously-conditional assertions (DiscountReservation / PaidOrder / PurchaseNoticeDelivery) now unconditional. `SHB_LOCAL_PASS checks=4 tests=10 shared_tests=0 duration_seconds=12.391`. | SHB-13 | `backend/shop/shb/tests.py:251-300` (changed import to `from .models import Invitation,SupportRequest,DiscountReservation,PaidOrder,PurchaseNoticeDelivery`; removed both `try/except` guards and both `if X is not None:` wrappers around the assertions) | ✅ | — | Done |
| R2 | ✅ **CLOSED 2026-11-04 (by audit)** — grep across the 8 SHB test files (`^\s*[A-Z][A-Za-z_,]*\s*=\s*None`, `if X is not None: self.assert`) returned zero silent-skip instances; the SHB-13 pattern R1 fixed was the sole occurrence. Remaining `try:` blocks are either `try: HTTP action except Exception: assert on type(error).__name__` (valid for DisallowedHost) or `try: ... finally: connections.close_all()` concurrency wrappers with no `except`. | SHB-13, SHB-14, SHB-25, SHB-26 (candidate scope) | `backend/shop/shb/{tests,discount_tests,offer_tests,notification_tests,review_tests,financial_tests,paid_order_tests,recovery_tests}.py` | ✅ | — | Done |
| R3 | ✅ **CLOSED 2026-11-04** — 8 phantom citations repaired in `.planning/REQUIREMENTS.md` and `docs/build/shb-complete-explicit-coverage-2026-11-03.md`. Real method names identified via `git show <sha> -- 'backend/shop/shb/*.py' \| grep '^+\s*def test'` against each SHB-NN's recorded commit. Every new citation grep-verifies 1 hit in `backend/shop/shb/paid_order_tests.py`. Enclosing class is `PaidOrderTests` for all 8. No duplicate tests added. Coverage doc gains an R3 repair note. | SHB-07, SHB-19, SHB-20, SHB-21, SHB-22, SHB-23, SHB-24, SHB-26 (traceability only) | `.planning/REQUIREMENTS.md`, `docs/build/shb-complete-explicit-coverage-2026-11-03.md` | ✅ | — | Done |
| R4 | ✅ **CLOSED 2026-11-04** — `shop.shb.discount_issuance_tests` added to `scripts/check_shb.py:49` labels list. Diff against `scripts/check_shb_retained.py:164` now shows only structural differences (nested list vs flat list); module content identical. Focused verification: `check_shb.py --test-label shop.shb.discount_issuance_tests` ran 22 tests in 9.929s, `SHB_LOCAL_PASS checks=4 tests=31 shared_tests=0 duration_seconds=22.095`. | SHB-15/16/17 regression integrity | `scripts/check_shb.py`, `scripts/check_shb_retained.py` | ✅ | — | Done |
| R5 | Repair the CI core-local lane so it exercises the SHB application and relevant shared invariants rather than legacy IP/catalog/package/support-ledger/licence-change modules; remove the anonymous `/api/v1/catalog/` 200 assertion that contradicts invitation-only SHB behavior | SHB-01..04, SHB-06, SHB-10, SHB-11, SHB-14, SHB-27 + shared security/payment/archive invariants | `scripts/check_backend.py:127` (module list), `:147` (catalog HTTP assertion) | ✅ for code; CI pass only after R6 | — | `check.py all` exercises the SHB modules; move dedicated deferred-IP/time-accounting modules into an explicitly identified historical regression lane that remains green but is not mandatory for SHB acceptance |
| R6 | Replace `demo_purchase_flow.py` invocation in the development workflow with an SHB demo path (`demo_shb.py` or equivalent) so the development CI does not create old IP sales, licence entitlements, reference-design deliveries or support credits as part of its mandatory pass | SHB-02 (old IP route rejection), SHB-24 (manual support boundary) | `.github/workflows/development.yml:91`, `scripts/demo_shb.py`, `scripts/demo_purchase_flow.py` (retained as historical regression, not mandatory) | ✅ for code; ordinary CI pass once the SHB demo path exists | — | Development workflow runs an SHB-scoped demo; legacy demo remains runnable as historical regression |
| R7 | Audit `check_shb_retained.py` for legacy fulfilment / automated support-statement modules that belong in the historical regression lane rather than SHB acceptance; preserve the assertions (do not delete), move or tag with specific justification | SHB-24 (manual support boundary) | `scripts/check_shb_retained.py:164` module list | ✅ | — | SHB lane module list contains only modules that exercise SHB-reachable code paths or shared invariants reused by SHB; each retained legacy module has a one-line justification |
| R8 | Make remaining operational implementation explicit — document, per file, what is synthetic-fixture-only vs ready for the real path, with the exact missing provider specification where blocked | SHB-04/08/09 (ASIC adoption), SHB-07/15/16 (eligibility/discounts), SHB-19..22 (payment/reconcile), SHB-23 (transaction mail), SHB-28 (restore), SHB-29 (fail-closed), SHB-11/30 (private release / protected host) | `backend/shop/shb/{catalog,checkout,invitations,views,services,models,transaction_mail}.py`, private release / archive / storage integration | partial — provider-independent portions and locally verifiable behavior can advance now; provider-specific code waits on the selected provider's documentation | ASIC commercial adoption, selected bank, selected mail transport, selected object storage, selected deployment host | For each file: a dated note identifying which internal guards keep it fake-only and the exact external input required to lift each guard |
| R9 | Preserve all external gates — pinned Nix/source/runtime/native/licence/OCI/CI qualification; actual commercial/provider/refund/tax/mail/host/ingress/database/human/independent-custody/post-backup/transport/restore/complete-loss qualification; authorized independent off-host runner | SHB-28/29/30 and shared infrastructure controls | all `ops/**`, `docs/host-protection-inventory.md`, `docs/shop-resource-allowlist.md` | ❌ | user authority for each gate; off-host runner assignment | per-gate owner-recorded decision; not fabricated by this project |

**"Can be done locally now"** means: no .env, no real credentials, no production/bank-sandbox connection, no protected-host/mail/storage/DNS/TLS action, no paid provisioning. Preparing reviewable artifacts before separately required approval is authorized.

## Next action

**R5 — Repair the CI core-local lane to exercise SHB modules and remove the anonymous-catalog HTTP 200 assertion.** Two sub-changes in `scripts/check_backend.py`:

1. **`:127` labels list.** Currently selects ~60 `shop.catalog.*`, `shop.worker.*`, `shop.payments.*` modules and zero `shop.shb.*` modules. Reconcile to exercise `shop.shb` + genuinely-shared invariants (identity/CSRF/archive/payment-callback safety/worker durability). Move dedicated deferred-IP/time-accounting modules into an explicitly identified historical regression lane that remains green but is not mandatory for SHB acceptance. Do not delete tests; move them.
2. **`:147` HTTP probe.** Currently asserts `/api/v1/catalog/` returns 200 anonymously, contradicting invitation-only SHB behavior. Either re-scope the probe to an invitation-authenticated fixture or expect 403/404 anonymously while preserving the existing authentication-authorization assertions elsewhere.

Verify with `python3 scripts/check.py all` under the pinned Nix shell (required CI gate; multi-minute rerun is warranted by this behavior change per amendment §8).

Rationale per the amendment §3: the required CI lane must exercise the actual SHB application, not legacy IP/catalog/package modules. R5 is the largest local-now item; after R5 the development-workflow fix (R6) lifts the `demo_purchase_flow.py` IP rehearsal out of mandatory CI.

Follow-up order after R5: R6 (development workflow reconciliation) → R7 (SHB retained-lane legacy-module audit) → R8 (per-file operational-implementation documentation). R9 remains external.

## Preserved context (pre-amendment)

The 16-commit SHB-NN tagging session that landed on 2026-11-03 (final docs rollup `3116f19`, followed by pause `b38dc24`) produced real, running assertions in the shared retained regression lane. That evidence stands for what it actually measures: at the recorded source identity, the retained lane runs 640 tests (297 SHB-tagged) to green in ~274 s and the browser lane runs 161 checks to green against the retained 9-file private Astro release. The amendment does **not** invalidate that evidence; it corrects the derivative claim that every SHB-01..30 has unconditional explicit coverage.

Decisions from that session retained unchanged:
- Composite SHB-01/02/03/04/06 coverage test (five clauses on the `/shop/` HTTP boundary).
- SHB-30 covered at code-boundary level only (host-service import test); deployment review is an external gate.
- SHB-29 submit-boundary assertion only (PAYMENT_ADAPTER='real' branch deliberately out of scope for submit).
- Progress reporting framed around SHB completion, not the 14-phase `percent` field.

## Operational boundaries (unchanged)

No .env read, real credentials, actual bank/mail/storage/protected-host/DNS/TLS operation, production/bank-sandbox connection or paid provision. Unrelated `http_cache.sqlite` stays untouched. Pre-existing untracked dotfiles and `.claude/`, `.idea/`, `.mcp.json`, `.vscode/`, `.gitconfig`, `.gitmodules` remain untracked. The eight `docs/evidence/shb/retained-tests/*.json` intermediates from `--test-label` runs are not load-bearing and may stay uncommitted.

Ordinary non-force sync to origin/main after each project commit remains authorized. No subagent request for this quick task.
