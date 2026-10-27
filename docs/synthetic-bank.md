# Typed synthetic bank boundary

`shop.payments` is an internal local/synthetic fake-provider simulator. It is separate from the old worker `Probe`/`FakeReceipt` rehearsal. It creates no order, acceptance, actual financial confirmation, fulfilment or support credit, and registers no public provider callback endpoint. Assigned private staff routes orchestrate synthetic operations only. All observations and persisted operations remain `local-synthetic`, with financial-confirmation/effect flags false. Production, bank-sandbox, nonfake adapter settings, live payment settings and caller-held/manual database transactions are refused.

`BankStart` supplies a synthetic merchant namespace, UUID reference/idempotency key, three-uppercase currency token and positive integer minor amount bounded by PostgreSQL bigint storage. Currency tokens and sample amounts are fixture data, not approved product prices or real merchant/currency eligibility. `SyntheticCapabilities` documents only the simulator: reference lookup, idempotent start, separate full-amount capture and full-amount refund are implemented. Partial refunds and callbacks are unsupported. Authorization and captured statuses remain distinct. Never copy these capabilities into an actual bank configuration.

## Lost-response rehearsal

Run through a configured local/synthetic Django test or owned development database, outside an outer transaction:

```python
from uuid import uuid4
from shop.payments.bank_contract import BankStart, correlates
from shop.payments.synthetic_bank import start, lookup

request = BankStart('synthetic-demo', uuid4(), uuid4(), 'EUR', 12500)
try:
    observation = start(request, outcome='captured', fault='after_commit')
except TimeoutError:
    observation = lookup(request.merchant, request.reference)

assert correlates(request, observation)
assert observation.financial_confirmation is False
assert observation.effects_authorized is False
```

The `after_commit` fault raises only after the fake-provider transaction commits. Lookup on a new PostgreSQL connection can recover that simulated result without repeating start. The `before_commit` fault creates no fake operation/key. These controlled exceptions are not process/network/outage or recovery qualification. A real timeout is uncertain; no inference that a real provider has or has not processed it follows from either simulation.

The semantic operation is unique by synthetic merchant/reference. Every accepted idempotency-key alias is retained. Same body/reference retries preserve the original provider operation; changed amount/currency/outcome or a key reused for another reference conflicts and rolls back the losing operation. These are deliberate fake-provider guarantees, not evidence that any selected bank supports reference lookup or idempotency. Original start-key replies remain stable on retry. Explicit separate capture/refund mutations retain immutable transition records and advance the simulated provider status.

`correlates` compares exact typed merchant/reference/currency/amount fields and known synthetic status. It is not authentication or payment proof. Caller/domain code still needs approved order/acceptance/attempt/reference identities, recoverable archive-before-dispatch evidence, authorization/cancellation/deadline rechecks, a guarded dispatch claim, authenticated actual-bank observations and full reconciliation before any actual effect. Browser navigation cannot supply money evidence. No automatic retry or actual-bank fallback is provided.

Local evidence comes from real PostgreSQL uniqueness/rollback/concurrency and post-commit readback tests. Actual merchant capability, callbacks, capture/refund, independent runtime/outage, provider and production qualification remain pending. No credentials or protected/external services are required by this simulator.

## Synthetic attempt orchestration

`shop.payments.attempts.prepare(BankStart(...))` retains a fixture request. Merchant/reference and idempotency key identify one exact attempt; changed values or aliases conflict. It is not an approved order or acceptance. No routes or worker commands expose this fixture aggregate.

`dispatch(attempt_id, PreparedArchive(...))` publishes and recovers canonical expected bytes, then commits a row-locked transition from prepared to uncertain before calling the fake provider outside a transaction. Only the caller that wins that transition calls start. Even a pre-provider timeout leaves uncertainty; dispatch never repeats start after the claim. Archive publication/recovery failure before the claim leaves the attempt prepared. Retained receipts remain local prepared evidence, with retention qualification and effects false; there is no production custody/root binding claim.

`reconcile(attempt_id, archive)` recovers exact retained bytes and looks up the original reference. No observation leaves uncertainty. A mismatched observation fails closed. A correlated observation records the provider operation and distinct status (authorized/captured/declined/pending) as observed; all financial/effect flags remain false. Observed does not mean paid. Correlated forward status transitions retain journal history. Exact previously journaled authorized/captured observations may replay without downgrading a later refunded projection; unknown regressions fail closed. There is no automatic retry or public callback. Existing synthetic checkout fixtures integrate this boundary; actual commerce requires separately approved immutable order/acceptance scope, live archive authority and dispatch eligibility rechecks.


## Pre-dispatch cancellation, expiry and recovery inspection

`prepare(request, expires_at=aware_datetime)` binds an explicit synthetic dispatch deadline to exact replay identity and canonical archived bytes. UTC-equivalent instants replay; a changed or omitted retained deadline conflicts. Undated legacy fixtures retain their original canonical bytes and no inferred deadline. This deadline describes the fixture's dispatch eligibility only; it is not quote validity or a provider session expiry.

`cancel(id)` and `expire(id)` arbitrate under the same row lock as dispatch. Expiry uses PostgreSQL wall-clock time after acquiring the lock. A due prepared attempt becomes expired; cancellation of a still eligible prepared attempt becomes cancelled. Both terminal states preserve their original stop time on retry and cannot dispatch, reconcile or accept observations. A due deadline takes precedence when cancellation checks eligibility. Calls to expire an undated/not-yet-due or already dispatched attempt leave it unchanged.

Dispatch checks expiry before archive I/O and again under the final claim lock after recovering the expected bytes. Cancellation can win while archive I/O is in progress; recovered prepared bytes alone never grant a send. An orphaned prepared archive may remain after cancellation/expiry, without a persisted receipt or dispatch authority. If the uncertain claim commits first, cancellation is refused even if the provider call has not begun; only lookup reconciliation remains available. No cancellation/refund is sent to a provider.

`inspect(id)` returns a fixed immutable metadata record with state, deadline, stop time, whether a prepared deadline is currently due, provider status and whether lookup is the recovery path. It locks the row for a consistent point-in-time read but performs no writes, archive I/O or provider call. Retry, financial-confirmation and effects flags are always false; the report grants no future action authority. Inspection can report expiry due without persisting expiry. These internal services retain local/synthetic and outer-transaction guards and have no HTTP/worker exposure.

### Local inspection command

From an already configured local/synthetic development environment, run `python manage.py inspect_synthetic_payment --attempt <canonical-UUID>`. It reads one known attempt and emits a closed JSON metadata record. It provides no dispatch, cancellation, expiry, archive-recovery or reconciliation switch; it cannot contact the simulator or grant retry authority. Output omits the attempt/reference/key/merchant, amounts, provider operation IDs, receipts and archive paths. Existing PostgreSQL connect/statement timeouts bound database waits.

Unknown/malformed IDs, service guards, database failures and lock timeouts produce the fixed command error `Local synthetic payment inspection unavailable`. Invalid live environment settings can be rejected earlier by the existing Django startup gate, before this command is loaded; that existing startup refusal is distinct from the command error. The command is local development tooling, without staff authorization or production/operator qualification.


### Retained synthetic dispatch holds

`set_hold(id, held=bool, expected_revision=int, command_id=UUID)` is an internal local fixture control. It retains one event and advances the attempt control revision under the same lock as dispatch. New controls require prepared state and the current revision. An exact command retry returns its original event, including after a later control or dispatch; it never reapplies the original target. Changing a retained command's target/base or submitting a new stale release fails closed. Concurrent distinct commands at one revision have one winner; concurrent exact retries retain one event.

Dispatch checks the current held flag before archive I/O and again after recovery, with due expiry taking precedence. A hold that wins before the claim prevents sending; a later hold cannot cancel an uncertain operation. A separately revision-checked release permits a fresh eligibility check for an otherwise prepared attempt. Hold controls do not change canonical request bytes or clear cancellation/expiry/uncertainty. Inspection reports the current held flag and revision, without command IDs or control history values. No command or HTTP endpoint mutates holds.

These are append-only-by-service fixture control records, without staff attribution, live approval/activation or production archive authority. Actual commercial/source/recovery holds and their protected approvals remain separate pending work. No synthetic control can authorize actual commerce.

## Final purchase-flow rehearsal

The final26October amendment reuses this existing adapter/claim boundary for the [owned synthetic purchase/staged-delivery demo](purchase-flow.md). Actual orders, commercial approvals, acceptance and real ledger/delivery remain pending; synthetic fixture balances/entitlements cannot authorize actual effects.

### Archived normalized observation receipts

New direct dispatch responses, manual reconciliation lookups and inbox lookups retain immutable normalized receipts before updating the attempt projection. Each exact observation has a stable identity within its attempt. Repeating it reuses the original receipt; a missing lookup is a separate inert fact and never clears prior capture or confirms money. Receipt revisions/hash links start at the retained request digest. Strict typed correlation remains. The v2 lifecycle below permits bounded status progression and explicit capture/refund intents; public callbacks remain unsupported.

Provider I/O remains outside database transactions/locks. Receipt bytes archive/read back before receipt/projection commit. If archive publication fails after the fake provider captured, the attempt stays uncertain: dispatch cannot start again, and typed lookup is the recovery path. Inbox workers recheck the lease after journal archive waits; stale workers cannot publish a receipt, result or projection. Prepared bytes after DB failure are inert and require identical retained scope on recovery.

`python manage.py inspect_synthetic_observations --attempt <canonical-UUID>` verifies retained request/receipt bytes and the immutable chain under the attempt lock. It emits only counts, retained statuses/miss presence and false financial/effect/retry flags. It performs no provider calls or writes, and prints no identifiers, amount, currency, merchant, reference, key, receipt or archive path. It requires the configured existing local checkout archive root. Unknown IDs, absent evidence, production/live modes and database/archive errors fail closed with a fixed error.

Existing observed projections are not backfilled as if their original responses were retained. A later typed lookup may retain a newly observed fact; inspection never claims original-response coverage or a provider event time. SQL immutability is not independent suffix-loss recovery or qualified retention. All evidence remains local-synthetic; actual merchant/provider/authentication/financial/capture/refund/recovery qualification is pending.


## V2 capture and refund operations

`shop.payments.operations` binds each synthetic intent to an existing immutable accepted checkout and its exact archived attempt. Local operator `local_staff grant-payment` assigns an existing staff user one acceptance and one kind (`capture` or `refund`); `revoke-payment`, staff reset and revoke remove that authority. The private `/staff/payments/` queue and assigned detail forms require recent MFA and current exact-resource authorization. Use `python manage.py local_staff --help` for the closed operator argument contract. No browser field selects an amount, currency, merchant or provider reference.

`prepare` archives and reads back an immutable attributed intent before retaining its prepared dispatch record. Capture requires an authorized attempt; refund requires a captured attempt. Both operate on the entire original amount. `dispatch` commits a single uncertain claim before calling the simulator outside database locks. A timeout, including before simulated commit, never releases that claim. The assigned staff route returns409 `payment_operation_uncertain_use_lookup`; a later dispatch retry remains inert and only reconciliation performs lookup. `reconcile` looks up the exact retained mutation; a miss stays uncertain. A typed result archives before result, journal and projection publication. Repeated dispatch cannot invoke another mutation.

Provider transitions and intent/results are immutable. Original start-key replies remain stable after capture/refund, and old known journal facts cannot downgrade the current projection. These are simulator guarantees only. Refund leaves existing captured grant history, licence records, delivered material history and support accounting unchanged; it creates no new grant or automatic revocation/reversal. An order refunded before its first grant cannot provision from refunded status. Financial policy fields remain null, financial/effect flags false, and actual provider operations remain disabled pending verified contract, commercial approval and qualification.
