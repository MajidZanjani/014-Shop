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
