# Typed synthetic bank boundary

`shop.payments` is an internal local/synthetic fake-provider simulator. It is separate from the old worker `Probe`/`FakeReceipt` rehearsal. It creates no order, acceptance, actual financial confirmation, fulfilment or support credit, and registers no HTTP endpoint. All observations and persisted operations remain `local-synthetic`, with financial-confirmation/effect flags false. Production, bank-sandbox, nonfake adapter settings, live payment settings and caller-held/manual database transactions are refused.

`BankStart` supplies a synthetic merchant namespace, UUID reference/idempotency key, three-uppercase currency token and positive integer minor amount bounded by PostgreSQL bigint storage. Currency tokens and sample amounts are fixture data, not approved product prices or real merchant/currency eligibility. `SyntheticCapabilities` documents only the simulator: reference lookup and idempotent start are implemented; separate capture, refunds and callbacks are unsupported. Authorization and captured statuses remain distinct. Never copy these capabilities into an actual bank configuration.

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

The semantic operation is unique by synthetic merchant/reference. Every accepted idempotency-key alias is retained. Same body/reference retries preserve the original provider operation; changed amount/currency/outcome or a key reused for another reference conflicts and rolls back the losing operation. These are deliberate fake-provider guarantees, not evidence that any selected bank supports reference lookup or idempotency. Stored operation status does not advance implicitly on a retry; later authorization/capture/refund lifecycle operations are unimplemented.

`correlates` compares exact typed merchant/reference/currency/amount fields and known synthetic status. It is not authentication or payment proof. Caller/domain code still needs approved order/acceptance/attempt/reference identities, recoverable archive-before-dispatch evidence, authorization/cancellation/deadline rechecks, a guarded dispatch claim, authenticated actual-bank observations and full reconciliation before any actual effect. Browser navigation cannot supply money evidence. No automatic retry or actual-bank fallback is provided.

Local evidence comes from real PostgreSQL uniqueness/rollback/concurrency and post-commit readback tests. Actual merchant capability, callbacks, capture/refund, independent runtime/outage, provider and production qualification remain pending. No credentials or protected/external services are required by this simulator.

## Synthetic attempt orchestration

`shop.payments.attempts.prepare(BankStart(...))` retains a fixture request. Merchant/reference and idempotency key identify one exact attempt; changed values or aliases conflict. It is not an approved order or acceptance. No routes or worker commands expose this fixture aggregate.

`dispatch(attempt_id, PreparedArchive(...))` publishes and recovers canonical expected bytes, then commits a row-locked transition from prepared to uncertain before calling the fake provider outside a transaction. Only the caller that wins that transition calls start. Even a pre-provider timeout leaves uncertainty; dispatch never repeats start after the claim. Archive publication/recovery failure before the claim leaves the attempt prepared. Retained receipts remain local prepared evidence, with retention qualification and effects false; there is no production custody/root binding claim.

`reconcile(attempt_id, archive)` recovers exact retained bytes and looks up the original reference. No observation leaves uncertainty. A mismatched observation fails closed. A correlated observation records the provider operation and distinct status (authorized/captured/declined/pending) as observed; all financial/effect flags remain false. Observed does not mean paid. Conflicting later observations are rejected rather than silently replacing history. No automatic retry, callback, evolving provider lifecycle or actual commerce integration is implemented. Such integration still requires separately approved immutable order/acceptance scope, live archive authority and dispatch eligibility rechecks.


## Pre-dispatch cancellation, expiry and recovery inspection

`prepare(request, expires_at=aware_datetime)` binds an explicit synthetic dispatch deadline to exact replay identity and canonical archived bytes. UTC-equivalent instants replay; a changed or omitted retained deadline conflicts. Undated legacy fixtures retain their original canonical bytes and no inferred deadline. This deadline describes the fixture's dispatch eligibility only; it is not quote validity or a provider session expiry.

`cancel(id)` and `expire(id)` arbitrate under the same row lock as dispatch. Expiry uses PostgreSQL wall-clock time after acquiring the lock. A due prepared attempt becomes expired; cancellation of a still eligible prepared attempt becomes cancelled. Both terminal states preserve their original stop time on retry and cannot dispatch, reconcile or accept observations. A due deadline takes precedence when cancellation checks eligibility. Calls to expire an undated/not-yet-due or already dispatched attempt leave it unchanged.

Dispatch checks expiry before archive I/O and again under the final claim lock after recovering the expected bytes. Cancellation can win while archive I/O is in progress; recovered prepared bytes alone never grant a send. An orphaned prepared archive may remain after cancellation/expiry, without a persisted receipt or dispatch authority. If the uncertain claim commits first, cancellation is refused even if the provider call has not begun; only lookup reconciliation remains available. No cancellation/refund is sent to a provider.

`inspect(id)` returns a fixed immutable metadata record with state, deadline, stop time, whether a prepared deadline is currently due, provider status and whether lookup is the recovery path. It locks the row for a consistent point-in-time read but performs no writes, archive I/O or provider call. Retry, financial-confirmation and effects flags are always false; the report grants no future action authority. Inspection can report expiry due without persisting expiry. These internal services retain local/synthetic and outer-transaction guards and have no HTTP/worker exposure.

### Local inspection command

From an already configured local/synthetic development environment, run `python manage.py inspect_synthetic_payment --attempt <canonical-UUID>`. It reads one known attempt and emits a closed JSON metadata record. It provides no dispatch, cancellation, expiry, archive-recovery or reconciliation switch; it cannot contact the simulator or grant retry authority. Output omits the attempt/reference/key/merchant, amounts, provider operation IDs, receipts and archive paths. Existing PostgreSQL connect/statement timeouts bound database waits.

Unknown/malformed IDs, service guards, database failures and lock timeouts produce the fixed command error `Local synthetic payment inspection unavailable`. Invalid live environment settings can be rejected earlier by the existing Django startup gate, before this command is loaded; that existing startup refusal is distinct from the command error. The command is local development tooling, without staff authorization or production/operator qualification.
