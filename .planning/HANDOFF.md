# SHB continuation checkpoint

Current authority: [SHB revision 1.1](../014-Shop-SHB-Proposal-Revision-2026-10-30.md) (product specification).
Current planning/execution precedence: [2026-11-04 amendment](../014-Shop-SHB-Claude-Correction-Prompt-2026-11-04.txt) — supersedes conflicting earlier planning/execution instructions only. STATE.md / ROADMAP.md remain operative.

**Current development focus:** 6 — Invitation scope, verified resources and staff MFA.

**Last fully completed phase:** 1 — documentary authority/reconciliation only.

**Current plan:** 06-01 — protected invitation issuance/reissue, scoped discount revocation and separate protected discount issuance verified locally; actual qualification remains open.

**Execution status:** active — R1..R7 all closed 2026-11-04. R7 reclassified the SHB retained module set across scripts/check_shb.py and scripts/check_shb_retained.py: 4 IP-era modules (shop.catalog.{checkout,checkout_payment,fulfilment}_tests + shop.worker.statement_mail_tests) moved from mandatory SHB acceptance into a new `--historical` lane (marker SHB_HISTORICAL_PASS / RETAINED_SHB_HISTORICAL_PASS); shop.adapters.evidence_archive_tests retained in SHB shared with an inline PreparedArchive-reuse justification. Verified: `check_shb.py --historical` → SHB_HISTORICAL_PASS tests=82 duration=40.716s; `check_shb.py --shared` → SHB_LOCAL_PASS checks=10 tests=558 shared_tests=252 duration=249.199s. Combined coverage surface = 558 + 82 = 640 tests (matches the 2026-11-03 retained count exactly; no assertion lost). Browser lane 161 remains the 2026-11-03 last-recorded evidence against commit b38dc24 (not rerun). Next action R8 (per-file synthetic-vs-real-path documentation); R9 remains external.

**Next implementation task:** R8 — make remaining operational implementation explicit per-file for `backend/shop/shb/{catalog,checkout,invitations,views,services,models,transaction_mail}.py`. For each file, record a dated note identifying which internal guards keep it fake-only (synthetic fixture guards, synthetic bank/mail/storage adapters, request intake blocks, model constraints) and the exact external input required to lift each guard (ASIC commercial adoption record, selected bank/mail/storage/host provider documentation, approved pricing/currency/terms/legal/policy versions). Provider-independent portions and locally verifiable behavior can advance now; provider-specific code waits on the selected provider's documentation. R9 (external gates and off-host runner) remains external.

**Recorded implementation:** b38dc244f78b32fdf3129f1ae49c5112cb1da2a2

## Remaining SHB implementation (local-now unless marked)

Columns — SHB req or shared invariant · concrete files/components · can be done locally now · external dependency (if any) · evidence to close.

| # | Deliverable | SHB ref | Files / components | Local now | External dep | Evidence to close |
|---|---|---|---|---|---|---|
| R1 | ✅ **CLOSED 2026-11-04** — SHB-13 silent-skip fixed; focused `shop.shb.tests.InvitationTests.test_shb_13_valid_link_reuse_and_scanner_get_has_no_side_effect` passes with the three previously-conditional assertions (DiscountReservation / PaidOrder / PurchaseNoticeDelivery) now unconditional. `SHB_LOCAL_PASS checks=4 tests=10 shared_tests=0 duration_seconds=12.391`. | SHB-13 | `backend/shop/shb/tests.py:251-300` (changed import to `from .models import Invitation,SupportRequest,DiscountReservation,PaidOrder,PurchaseNoticeDelivery`; removed both `try/except` guards and both `if X is not None:` wrappers around the assertions) | ✅ | — | Done |
| R2 | ✅ **CLOSED 2026-11-04 (by audit)** — grep across the 8 SHB test files (`^\s*[A-Z][A-Za-z_,]*\s*=\s*None`, `if X is not None: self.assert`) returned zero silent-skip instances; the SHB-13 pattern R1 fixed was the sole occurrence. Remaining `try:` blocks are either `try: HTTP action except Exception: assert on type(error).__name__` (valid for DisallowedHost) or `try: ... finally: connections.close_all()` concurrency wrappers with no `except`. | SHB-13, SHB-14, SHB-25, SHB-26 (candidate scope) | `backend/shop/shb/{tests,discount_tests,offer_tests,notification_tests,review_tests,financial_tests,paid_order_tests,recovery_tests}.py` | ✅ | — | Done |
| R3 | ✅ **CLOSED 2026-11-04** — 8 phantom citations repaired in `.planning/REQUIREMENTS.md` and `docs/build/shb-complete-explicit-coverage-2026-11-03.md`. Real method names identified via `git show <sha> -- 'backend/shop/shb/*.py' \| grep '^+\s*def test'` against each SHB-NN's recorded commit. Every new citation grep-verifies 1 hit in `backend/shop/shb/paid_order_tests.py`. Enclosing class is `PaidOrderTests` for all 8. No duplicate tests added. Coverage doc gains an R3 repair note. | SHB-07, SHB-19, SHB-20, SHB-21, SHB-22, SHB-23, SHB-24, SHB-26 (traceability only) | `.planning/REQUIREMENTS.md`, `docs/build/shb-complete-explicit-coverage-2026-11-03.md` | ✅ | — | Done |
| R4 | ✅ **CLOSED 2026-11-04** — `shop.shb.discount_issuance_tests` added to `scripts/check_shb.py:49` labels list. Diff against `scripts/check_shb_retained.py:164` now shows only structural differences (nested list vs flat list); module content identical. Focused verification: `check_shb.py --test-label shop.shb.discount_issuance_tests` ran 22 tests in 9.929s, `SHB_LOCAL_PASS checks=4 tests=31 shared_tests=0 duration_seconds=22.095`. | SHB-15/16/17 regression integrity | `scripts/check_shb.py`, `scripts/check_shb_retained.py` | ✅ | — | Done |
| R5 | ✅ **CLOSED 2026-11-04** — `scripts/check_backend.py` rewritten with module-level `SHB_LABELS`, `SHARED_INVARIANT_LABELS`, `CORE_LOCAL_LABELS`, `CORE_HISTORICAL_LABELS`; new `core-historical` argparse lane preserves legacy modules; HTTP probes updated: `/api/v1/catalog/` 200→403 (invitation-only per SHB middleware PROTECTED), `/purchase/simple/` 200→403, `/purchase/cart/` + `/purchase/request-quotation/` 401→404 (OLD_SALES), `/api/v1/configurations/validate/` 405→404; batch size 20→10, per-batch timeout 120s→300s (SHB adds ~274s load). Verified: `CORE_LOCAL_PASS checks=5 tests=659 duration_seconds=284.938`; zero FAIL/ERROR across two confirming runs. | SHB-01..04, SHB-06, SHB-10, SHB-11, SHB-14, SHB-27 + shared security/payment/archive invariants | `scripts/check_backend.py` | ✅ | — | Done |
| R6 | ✅ **CLOSED 2026-11-04** — `.github/workflows/development.yml:91` swap landed: `(['python3','scripts/demo_purchase_flow.py'],900,'PURCHASE_FLOW_DEMO_PASS')` → `(['python3','scripts/demo_shb.py','--check'],900,'SHB_DEMO_PASS')`. Surrounding bounded-timeout / marker-check / outer Nix shell preserved unchanged. `scripts/demo_purchase_flow.py` retained on disk as historical regression (amendment §3; separately invokable from `docs/local-development.md`). Verified under the pinned Nix shell: `demo_shb.py --help` renders; `demo_shb.py --check` emits `SHB_DEMO_PASS checks=17 evidence=local-synthetic-header-level fpga=review asic=submitted payment=not_exercised manual_time_tracking=true`. | SHB-02 (old IP route rejection), SHB-24 (manual support boundary) | `.github/workflows/development.yml:91`, `scripts/demo_shb.py`, `scripts/demo_purchase_flow.py` (historical) | ✅ | — | Done |
| R7 | ✅ **CLOSED 2026-11-04** — `scripts/check_shb.py` and `scripts/check_shb_retained.py` rewritten with module-level `SHB_LABELS`, `SHB_SHARED_LABELS` (5 batches with inline SHB-reuse rationale each), `HISTORICAL_TRANSACTION_TESTS`, `HISTORICAL_LABELS`; new `--historical` argparse flag on both scripts. 4 IP-era modules (3 catalog + worker.statement_mail) moved out of mandatory SHB acceptance; `shop.adapters.evidence_archive_tests` retained in shared with inline PreparedArchive-reuse rationale; `shop.worker.tests.OwnershipTests` retained with outbox-ownership rationale. SHB batch timeout 120s→300s. Verified: `--historical` → SHB_HISTORICAL_PASS tests=82 duration=40.716s; `--shared` → SHB_LOCAL_PASS tests=558 shared_tests=252 duration=249.199s. Combined surface = 558 + 82 = 640 (matches the 2026-11-03 retained count exactly). | SHB-24 (manual support boundary) + shared security/payment/archive invariants | `scripts/check_shb.py`, `scripts/check_shb_retained.py` | ✅ | — | Done |
| R8 | Make remaining operational implementation explicit — document, per file, what is synthetic-fixture-only vs ready for the real path, with the exact missing provider specification where blocked | SHB-04/08/09 (ASIC adoption), SHB-07/15/16 (eligibility/discounts), SHB-19..22 (payment/reconcile), SHB-23 (transaction mail), SHB-28 (restore), SHB-29 (fail-closed), SHB-11/30 (private release / protected host) | `backend/shop/shb/{catalog,checkout,invitations,views,services,models,transaction_mail}.py`, private release / archive / storage integration | partial — provider-independent portions and locally verifiable behavior can advance now; provider-specific code waits on the selected provider's documentation | ASIC commercial adoption, selected bank, selected mail transport, selected object storage, selected deployment host | For each file: a dated note identifying which internal guards keep it fake-only and the exact external input required to lift each guard |
| R9 | Preserve all external gates — pinned Nix/source/runtime/native/licence/OCI/CI qualification; actual commercial/provider/refund/tax/mail/host/ingress/database/human/independent-custody/post-backup/transport/restore/complete-loss qualification; authorized independent off-host runner | SHB-28/29/30 and shared infrastructure controls | all `ops/**`, `docs/host-protection-inventory.md`, `docs/shop-resource-allowlist.md` | ❌ | user authority for each gate; off-host runner assignment | per-gate owner-recorded decision; not fabricated by this project |

**"Can be done locally now"** means: no .env, no real credentials, no production/bank-sandbox connection, no protected-host/mail/storage/DNS/TLS action, no paid provisioning. Preparing reviewable artifacts before separately required approval is authorized.

## Next action

**R8 — Make remaining operational implementation explicit per-file for the seven SHB source files that currently operate on synthetic fixtures only.** The amendment §5 enumerates:

- `backend/shop/shb/catalog.py` — live approved-offer selection is explicitly pending; pricing accepts synthetic policies only
- `backend/shop/shb/checkout.py` — checkout requires the fake-only fixture guard and constructs synthetic terms/order snapshots
- `backend/shop/shb/invitations.py` — issues digest-only durable intent against synthetic fixture data
- `backend/shop/shb/views.py` — live ASIC request intake is explicitly blocked
- `backend/shop/shb/services.py` — companion to views; same real-ASIC block
- `backend/shop/shb/models.py` — discount/issuance records have synthetic-only constraints
- `backend/shop/shb/transaction_mail.py` — fake capture rather than actual mail transport

Approach:

1. For each file, read the current implementation and identify every guard/constraint that keeps it fake-only. Record the exact line numbers.
2. For each guard, name the specific external input required to lift it (ASIC commercial adoption record with approved base hourly rate; selected bank provider documentation; selected mail transport specification; selected object storage specification; selected deployment host inventory). Where a guard is provider-independent and can advance locally now, note that and record the scope of what can be built.
3. Capture the per-file state in a dated note under `docs/build/shb-operational-state-2026-11-04.md` (new file) with one section per source file, listing guards and their required external lift inputs.
4. Cross-reference the notes from each source file's docstring or module-level comment where it aids readers; do not duplicate the full text.
5. Verification: no code change in this task — it's a documentation-and-inventory task. `grep` the notes against the actual source to confirm every guard cited exists at the recorded line.

Rationale: amendment §5 explicitly identifies this as pending implementation work. Separating provider-independent vs provider-specific scope lets the FPGA path advance independently of ASIC commercial adoption and lets locally-verifiable behaviour advance independently of bank/mail/storage/host selection.

Follow-up: R9 (external gates and off-host runner) remains external — not closable by this project.

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
