# Final purchase flow — revision2

Authority: [complete26October amendment](../014-Shop-Board-Support-Amendment-2026-10-26.md); [phase/task clauses](../.planning/PURCHASE-FLOW-AMENDMENT.md). Current evidence and remaining work: [.planning/STATE.md](../.planning/STATE.md).

## Implemented local path

The existing React configurator and Django `/purchase/simple/` ask one platform question: listed kit, another/custom/modified board, or not yet designed/selected/needs guidance. Only relevant optional kit/name detail is shown; unknown board name is valid. Existing vendor/family/term/access rules remain. Platform is saved inside existing owner configuration/cart/quotation snapshots, with old snapshots still readable. In the no-JavaScript cart, edit a saved other-board line to add its optional short name. Standalone support-line forms gain no board inputs. No technical upload or project-stage field was added.

The actual catalog has no supplied approved ready-kit entries or commercial policy yet, so affected actual purchase actions remain pending. Custom board selection itself does not cause a new review hold. The public catalog retains the historical product SHA and final amendment SHA; private customer platform names are never build inputs. Applicable approved standard offers, when supplied, need no individual engineering approval per sale.

## Reproducible synthetic purchase rehearsal

`nix --extra-experimental-features 'nix-command flakes' develop --max-jobs 1 --cores 4 ./ops/nixos#backend --command python3 scripts/demo_purchase_flow.py`

The wrapper creates a fresh owned PostgreSQL18.6 cluster/database and private temporary archive, then cleans them up. It seeds a clearly synthetic verified identity, uses the existing owner/CSRF-protected configuration-draft API and guarded bank/archive interfaces, and prints a fixed synthetic result without customer/host/key values. It uses no real email/bank/cloud service or credentials. Seeding is not evidence of actual email/access delivery.

The demo covers standard R&D/support purchases for not-designed and unnamed/custom boards, required minimum tamper refusal, a zero-support ready-kit fixture, initial materials with a later design still outstanding, later design closure with one simulated entitlement, independent support top-up and once-only recorded existing-credit reservation. Fixture amounts, kit variants, rights/start/delivery strings and the example two-package minimum are not actual approvals, compatibility guarantees or a universal support rule. The separate local checkout rehearsal uses these fixed fixture policies; customers cannot supply policy or price fields, and actual catalog approvals remain pending.

Small SyntheticPurchase/SyntheticCreditReservation records reference existing owner configuration drafts; they do not replace actual orders, acceptance, licence delivery or the support ledger. All financial/effect flags are constrained false; balances/entitlements are explicitly simulated. Lost response remains lookup-only through existing payment attempts. Snapshot bytes are published/recovered before the fake-bank call, and staged completion records are prepared/read back before simulated flags change. Prepared local evidence does not qualify actual retained delivery/custody.

## Complete-cart checkout rehearsal

The verified local customer path `/purchase/checkout-rehearsal/` and private `/api/v1/checkout-rehearsal/` share one backend service. Save a cart and business revision first. The preview includes every IP/support line, exact business details and the complete source document definition. A digest binds the displayed review to those bytes; a changed cart, business record, catalog or document definition rejects an uncommitted stale submission. Required support minima come from the seller fixture offer. Newly purchased packages are allocated once within this basket and priced once; existing support balances are not pooled. A single uncovered licence line or insufficient support holds the whole basket. Ready-kit cases require a listed catalog variant; real ready-kit entries remain pending.

The no-JavaScript page links from the saved cart. It asks only for deliberate recording of the reviewed synthetic checkout, with no project stage, technical upload or engineering approval ID. Receipts contain revision metadata without business values. Concurrent retries and different keys for the same snapshot yield one retained record; committed retries reconcile before current-cart checks. The demo now saves cart/business through supported CSRF-protected routes, records through the API, repeats through the no-JavaScript route and publishes/recovers the exact private checkout snapshot in its temporary archive.

`SyntheticCheckout` and its retry keys are prepared local facts. No bank dispatch, legal acceptance, actual order or entitlement follows from recording them. Country/tax, document bodies/approvals and applicable host bindings remain pending in the retained snapshot. The existing single-draft synthetic payment/staged-delivery rehearsal remains separately labelled; the complete-cart synthetic acceptance/payment connection is described below; actual order and fulfilment remain pending.

## Synthetic acceptance and payment

After recording a checkout, follow **Continue synthetic acceptance and payment**. Review the frozen cart/business revisions and clearly labelled document fixtures, select the unchecked rehearsal declaration and choose **Record synthetic acceptance**. Then choose **Simulate payment once**. A successful result says **Simulated payment captured** and preserves the same rehearsal order reference on retries. A lost response shows an uncertain state with a **Look up simulated payment** action; no new start is authorized. Real terms/acceptance, charges and licence/support rights remain disabled.

The local demo provisions its own private temporary checkout archive. Checkout, explicit fixture confirmation and payment-attempt bytes are published and recovered before fake bank dispatch. The fixture uses separate30-minute offer,45-minute order-payment and10-minute bank-session windows, with the bank window bounded by the order deadline. These are illustrative test values, not actual commercial rules. API and no-JavaScript routes share the same owner/CSRF/archive/once-only guards.

Customer access, business, cart and review/payment pages now share the public shop's cream/green layout, step navigation, grouped business fields and readable EUR totals. The persistent demo label distinguishes simulated actions. Country/tax fields remain pending; incomplete business drafts still save, and checkout names any missing required fields. No new project-stage or technical upload fields are introduced.

## Complete-cart fulfilment rehearsal

After simulated capture, choose **Simulate licence and support grants**. Expect one synthetic licence record per IP line and36000 integer support seconds per purchased package, with no expiry. Repeating the action preserves the same counts. Support-only carts create no IP licence. For each development IP line choose **Simulate initial delivery**: initial materials complete while the later reference design remains outstanding. **Simulate later reference design** closes that obligation without another licence/support grant. Ready-kit fixtures need no later event when their initial design is already covered.

These actions publish/recover their grant/completion snapshots before changing simulated records. No real file/key, entitlement or spendable support is issued. Work reservations, charges, corrections and statements are the next ledger implementation; actual fulfilment and private custody qualifications remain pending.

## Pending actual work

- P-02/03/05/06/08: initial real kit variants, standard development offers/price/required support minimum, annual rights/start trigger, exact legal/entity/tax and honest initial/later design/work scope; approved existing-credit ownership/scope.
- Actual immutable order/acceptance integration, approved commercial application across complete baskets and real licence/support ledger/fulfilment. Synthetic flags are not acceptance or money evidence.
- Authorized confidential engineering follow-up and resource-scoped technical document custody/versioning before receiving technical files. No new portal is mandatory; no public bucket/form or EDA execution is permitted.
- Existing live staff MFA, actual bank/mail, retained evidence, host/ingress/deployment and independent off-host recovery qualifications. No protected service authority is added by this amendment.


## Integrated staff finance rehearsal

The supported `python3 scripts/demo_purchase_flow.py` rehearsal now includes a separate support-only accepted checkout and uses the same real local two-factor staff session as the complete-cart scenario. The local operator explicitly grants each acceptance/kind. Staff forms and JSON actions prepare/retry capture, lose its response after fake-provider commit, reject a blind second mutation, and recover through lookup. Authorization alone cannot provision credit. A later full synthetic refund keeps the original36000 support seconds and60-second reservation, creates no extra grant/work event, and changes no accepted snapshot. Revoking the exact refund assignment denies further access.

The result includes `staff_finance_lifecycle`; no identifiers or private business details are printed. Provider timeouts return409 `payment_operation_uncertain_use_lookup`; archive failures retain their separate503 response. This is local simulator evidence, with null actual refund policy and false financial/effect flags. It does not establish real staff delivery/MFA, actual bank guarantees, refund eligibility or rights/credit reversal.


## Source acceptance report

The supported demo emits `source_acceptance_checks` numbered1–8 in final amendment §8 order. Seven scenarios report `synthetic_pass`; check8 remains `partial` with explicit pending confidential customer technical-data intake/custody. Private synthetic seller materials do not establish that intake qualification. The runner rejects omitted, duplicated or reordered cases and actual-authority promotion. Required support removal is now attempted through the actual cart API, then rejected by both API/no-JavaScript review and capture before support restoration. Separate fixture checks refuse missing price/rights/delivery and an unsupported ready-design promise; a distinct reservation cannot reallocate exhausted top-up credit.

Run `python3 -m unittest discover -s tests -p test_purchase_demo_report.py` for negative report controls. Prepared ordinary CI also runs the supported database-backed demo; hosted execution and actual qualification remain separate.


## Optional private synthetic follow-up

The existing customer support page now offers fixed synthetic follow-up examples after a captured purchase has its retained grant. Each optional submission appends an archived/read-back immutable context revision; a stale base conflicts and an exact historical request retry returns its original revision. The same purchase's assigned recent-MFA staff can read the version history. No separate engineering portal, checkout questionnaire or support debit is introduced. Accepted order scope, grants, reservations, work and statements remain unchanged.

Only named fixed fixture examples are accepted. Arbitrary technical text, files, raw hosts, keys and unknown fields are rejected. The page does not accept actual technical data; actual confidential intake/transport/custody remains pending. PostgreSQL forbids updates/deletes of retained context revisions. Owner isolation and current staff resource assignment remain mandatory on every read; ordinary command receipts omit owner/acceptance/archive hashes.
