---
quick_id: 261023-ina
status: complete
---
# Typed durable synthetic bank boundary

Implemented a typed durable local-synthetic bank adapter, separate from worker probes. Immutable-by-service fake operations and retained key aliases arbitrate merchant/reference/key retries and conflicts; explicit post-commit timeout can be reconciled by no-write reference lookup across connections. Exact typed correlation never confirms actual money; database/observation flags remain false. CORE_LOCAL_PASS5 checks/297 tests (283 Django plus14 Gunicorn),80.242s; PostgreSQL18.6/UTF8, payments0001/catalog0012 application and no-drift pass. Exact source /nix/store/87iyj21lmi0pmbqf52iyyvx68pvy1ygf-shop-python-source176 files23 templates/no symlinks.

Added shop.payments with BankStart/BankObservation/SyntheticCapabilities, strict synthetic merchant/UUID/currency-token/positive-bigint amount validation, immutable provider-operation creation and retained key aliases. Semantic uniqueness covers merchant/reference; keys cannot be reused for another operation, including concurrent losing-reference rollback. Captured/authorized/declined/pending statuses remain distinct; no state promotion on retry. Before-commit timeout writes nothing; after-commit response loss retains the fake result for lookup. Adapter rejects real modes, live/nonfake settings and outer/manual transactions. Capabilities for separate capture/refund/callbacks remain false. No public route, order/acceptance, actual merchant capability, financial confirmation, entitlement or actual bank I/O. Old Probe/FakeReceipt/default worker unchanged.

## Verification

Nine new real-PostgreSQL tests cover strict immutable capabilities/nonfinancial flags, same/different-key aliases/body conflicts, lookup after committed response loss on a new connection with no writes, precommit loss/distinct statuses, four-way semantic contention, colliding key/two references with no orphan row, identity/amount/currency/type correlation, environment/transaction guards and database constraints. Focused9 Django plus14 Gunicorn=23 tests/7.555s passes. Final retained full297/80.242s passes with5 checks/no skips; catalog0012 and new payments0001 apply with no model drift. Exact176-file23-template/no-symlink source compared by paths/bytes. Nix emitted an ignored local eval-cache busy diagnostic during parallel build/develop; both source build and full test command completed successfully. No new third-party dependency or frontend/proxy changes/rerun.

The new app migration is generated from the pinned Django runtime on a fresh owned synthetic PostgreSQL cluster. Exceptions model response loss, not actual process/network/outage/recovery qualification. Correlation is not authentication, actual payment evidence or approval. Documentation: [synthetic-bank](../../../docs/synthetic-bank.md).

## Remaining domain gates

Phase08 is now In Progress for this independent adapter slice, not complete. Payment preparation/order/acceptance/reference/qualified archive integration, guarded dispatch, actual authenticated financial observations, callback inbox, reconciliation/finance exceptions and capture/refund workflows remain pending. All live/source/legal/tax/merchant/host/recovery gates remain intact; no fabricated approved order or policy.

Next: Plan the local-synthetic payment-attempt/reconciliation slice against the new typed fake-bank boundary and existing prepared archive primitives. Define immutable expected merchant/currency/amount/reference, uncertain/observed/reconciled states and no-blind-retry claim arbitration before implementation. Retain separate order/acceptance/archive/approval prerequisites and synthetic-only classification; no fake result can mark a real order paid or grant rights. Source permits independent synthetic work while live tax/legal inputs remain pending. Continue substantive work without per-task context-clear requests; no actual external/host operations authorized.
