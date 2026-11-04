# SHB continuation checkpoint

Current authority: [SHB revision 1.1](../014-Shop-SHB-Proposal-Revision-2026-10-30.md) (product specification).
Current planning/execution precedence: [2026-11-04 amendment](../014-Shop-SHB-Claude-Correction-Prompt-2026-11-04.txt) — supersedes conflicting earlier planning/execution instructions only. STATE.md / ROADMAP.md remain operative.

**Current development focus:** 6 — Invitation scope, verified resources and staff MFA.

**Last fully completed phase:** 1 — documentary authority/reconciliation only.

**Current plan:** 06-01 — protected invitation issuance/reissue, scoped discount revocation and separate protected discount issuance verified locally; actual qualification remains open.

**Execution status:** active — R1 (SHB-13 silent-skip) closed 2026-11-04; three previously-conditional assertions now unconditional and focused test passes (SHB_LOCAL_PASS). Shared retained lane last recorded 640/297 and browser lane 161 at 2026-11-03 against commit b38dc24; neither rerun by R1 per its evidence-to-close criterion. Next action R2 (silent-skip audit across sibling SHB test modules); follow-ups R3..R9 in HANDOFF.md.

**Next implementation task:** R2 — audit sibling SHB test modules (backend/shop/shb/{tests,discount_tests,offer_tests,notification_tests,review_tests,financial_tests,paid_order_tests,recovery_tests}.py) for the silent-skip pattern (try: from X import Y except: Y=None followed by if Y is not None:); fix each or justify explicitly. Follow-up R3..R9 in HANDOFF.md; R9 (external gates and off-host runner) remains external.

**Recorded implementation:** b38dc244f78b32fdf3129f1ae49c5112cb1da2a2

## Remaining SHB implementation (local-now unless marked)

Columns — SHB req or shared invariant · concrete files/components · can be done locally now · external dependency (if any) · evidence to close.

| # | Deliverable | SHB ref | Files / components | Local now | External dep | Evidence to close |
|---|---|---|---|---|---|---|
| R1 | ✅ **CLOSED 2026-11-04** — SHB-13 silent-skip fixed; focused `shop.shb.tests.InvitationTests.test_shb_13_valid_link_reuse_and_scanner_get_has_no_side_effect` passes with the three previously-conditional assertions (DiscountReservation / PaidOrder / PurchaseNoticeDelivery) now unconditional. `SHB_LOCAL_PASS checks=4 tests=10 shared_tests=0 duration_seconds=12.391`. | SHB-13 | `backend/shop/shb/tests.py:251-300` (changed import to `from .models import Invitation,SupportRequest,DiscountReservation,PaidOrder,PurchaseNoticeDelivery`; removed both `try/except` guards and both `if X is not None:` wrappers around the assertions) | ✅ | — | Done |
| R2 | Audit sibling SHB test modules for the same silent-skip pattern (`try: from X import Y except: Y=None` followed by `if Y is not None:`) | SHB-13, SHB-14, SHB-25, SHB-26 (candidate scope — scan all `backend/shop/shb/*_tests.py`) | `backend/shop/shb/{tests,discount_tests,offer_tests,notification_tests,review_tests,financial_tests,paid_order_tests,recovery_tests}.py` | ✅ | — | grep audit report; any found instance fixed with explicit import; focused rerun of affected tests |
| R3 | Repair REQUIREMENTS.md and `docs/build/shb-complete-explicit-coverage-2026-11-03.md` citations — link each SHB-NN row to a test method that actually exists in source (SHB-07/19/20/21/22/23/24/26 currently cite nonexistent `test_shb_NN_*` names; real tests live under their original names in `backend/shop/shb/paid_order_tests.py` at the commits already recorded) | SHB-07, SHB-19, SHB-20, SHB-21, SHB-22, SHB-23, SHB-24, SHB-26 (traceability only) | `.planning/REQUIREMENTS.md`, `docs/build/shb-complete-explicit-coverage-2026-11-03.md` | ✅ | — | Each SHB-NN row cites a test name `grep -Rn` returns from the source tree; no new/duplicate tests added |
| R4 | Reconcile the SHB suite definition across supported runners — `scripts/check_shb.py:49` currently omits `shop.shb.discount_issuance_tests`; `scripts/check_shb_retained.py:164` includes it | SHB-15/16/17 regression integrity | `scripts/check_shb.py`, `scripts/check_shb_retained.py` | ✅ | — | Both scripts enumerate the same SHB module list (minus any explicitly justified difference); focused run of each script |
| R5 | Repair the CI core-local lane so it exercises the SHB application and relevant shared invariants rather than legacy IP/catalog/package/support-ledger/licence-change modules; remove the anonymous `/api/v1/catalog/` 200 assertion that contradicts invitation-only SHB behavior | SHB-01..04, SHB-06, SHB-10, SHB-11, SHB-14, SHB-27 + shared security/payment/archive invariants | `scripts/check_backend.py:127` (module list), `:147` (catalog HTTP assertion) | ✅ for code; CI pass only after R6 | — | `check.py all` exercises the SHB modules; move dedicated deferred-IP/time-accounting modules into an explicitly identified historical regression lane that remains green but is not mandatory for SHB acceptance |
| R6 | Replace `demo_purchase_flow.py` invocation in the development workflow with an SHB demo path (`demo_shb.py` or equivalent) so the development CI does not create old IP sales, licence entitlements, reference-design deliveries or support credits as part of its mandatory pass | SHB-02 (old IP route rejection), SHB-24 (manual support boundary) | `.github/workflows/development.yml:91`, `scripts/demo_shb.py`, `scripts/demo_purchase_flow.py` (retained as historical regression, not mandatory) | ✅ for code; ordinary CI pass once the SHB demo path exists | — | Development workflow runs an SHB-scoped demo; legacy demo remains runnable as historical regression |
| R7 | Audit `check_shb_retained.py` for legacy fulfilment / automated support-statement modules that belong in the historical regression lane rather than SHB acceptance; preserve the assertions (do not delete), move or tag with specific justification | SHB-24 (manual support boundary) | `scripts/check_shb_retained.py:164` module list | ✅ | — | SHB lane module list contains only modules that exercise SHB-reachable code paths or shared invariants reused by SHB; each retained legacy module has a one-line justification |
| R8 | Make remaining operational implementation explicit — document, per file, what is synthetic-fixture-only vs ready for the real path, with the exact missing provider specification where blocked | SHB-04/08/09 (ASIC adoption), SHB-07/15/16 (eligibility/discounts), SHB-19..22 (payment/reconcile), SHB-23 (transaction mail), SHB-28 (restore), SHB-29 (fail-closed), SHB-11/30 (private release / protected host) | `backend/shop/shb/{catalog,checkout,invitations,views,services,models,transaction_mail}.py`, private release / archive / storage integration | partial — provider-independent portions and locally verifiable behavior can advance now; provider-specific code waits on the selected provider's documentation | ASIC commercial adoption, selected bank, selected mail transport, selected object storage, selected deployment host | For each file: a dated note identifying which internal guards keep it fake-only and the exact external input required to lift each guard |
| R9 | Preserve all external gates — pinned Nix/source/runtime/native/licence/OCI/CI qualification; actual commercial/provider/refund/tax/mail/host/ingress/database/human/independent-custody/post-backup/transport/restore/complete-loss qualification; authorized independent off-host runner | SHB-28/29/30 and shared infrastructure controls | all `ops/**`, `docs/host-protection-inventory.md`, `docs/shop-resource-allowlist.md` | ❌ | user authority for each gate; off-host runner assignment | per-gate owner-recorded decision; not fabricated by this project |

**"Can be done locally now"** means: no .env, no real credentials, no production/bank-sandbox connection, no protected-host/mail/storage/DNS/TLS action, no paid provisioning. Preparing reviewable artifacts before separately required approval is authorized.

## Next action

**R2 — Audit sibling SHB test modules for the same silent-skip pattern.** Grep `backend/shop/shb/{tests,discount_tests,offer_tests,notification_tests,review_tests,financial_tests,paid_order_tests,recovery_tests}.py` for the pattern `try: from X import Y except: Y=None` followed by `if Y is not None:`. For each match, either (a) replace with the correct unconditional import if the symbol actually lives in the named module, or (b) keep the guard and add an explicit docstring justification naming the scenario it protects (e.g. a module that is intentionally optional in some test runs). Verify any fixed test with its focused run.

Rationale per the amendment §4: "Fix that import and make the required assertion unconditional; remove similar silent assertion omissions where directly encountered." R1 already removed the two directly-encountered silent-skip instances in SHB-13's scanner test. R2 generalises that to the rest of the SHB test tree in case the same pattern was copy-pasted.

Follow-up order after R2: R3 (citation repair) → R4 (suite symmetry) → R7 (SHB lane module audit) → R5 + R6 (CI/development workflow reconciliation) → R8 (operational-implementation documentation). R9 remains external.

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
