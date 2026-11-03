# Protected scoped discount issuance

Authority: [SHB revision1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md), including Appendix A. Existing06-01/07-02 continue inline after pushed invitation issuance4db2586 and scoped discount revocation34c0019. Real company inputs/adoption remain pending in the single [decision register](../decisions.md).

The existing staff application now registers synthetic discount issuance scopes with explicit customer, variant allowance, percentage, use limit and claim-period authority. A separate explicit issuance grant permits one staff member to issue codes under one scope; invitation eligibility, revocation grants and form-entered contact never establish commercial authority. GET reveals no raw code, verifier or private contact and creates no code, grant or notification.

The issuance service archives an attributed immutable digest-only intent before publication, publishes exactly one DiscountCode atomically with the matching scope and clocks, and returns the raw code once in the issuing response. Retries of the same request return the same reference without regenerating or revealing a code. Archive failure holds the intent and refuses to reveal a code on retry. Published archive bytes followed by rollback remain503-held; no fresh timestamp substitution. SQL requires current exact issuance grant and timestamps, append-only publication binding and matching DiscountCode fields in one commit.

Operator and selected restore clear mutable issuance grants while retaining the audit; recovery validates original clocks and holds release on missing published bytes. Legacy fixture issuance helpers remain unchanged for other tests; they are not commercial adoption. No new time-accounting, customer panel or mail path is added.

## Verification

RED705c2de is ordinarily pushed before any implementation edit: the discount issuance test module imports models and a service that do not yet exist, surfacing the gap. Private diagnostic .scratch/shb-discount-issuance-red-2026-11-02.log is not retained; the actual RED record lives in the retained-tests chain.

Shared regression passes **607 tests** (previously605;+2 for the issuance→revocation lifecycle test and the mirror admin-nav assertion closing the authority-separation invariant from both admin surfaces,24 total discount-related assertions above the 583 pre-issuance baseline): 264 SHB,95 access/recovery,104 payment,30 staff,24 worker/statement-mail,75 shared transaction/archive, nine source/catalog and six actual network-isolated adapter cases. Django check,0029/0030 and migration drift pass with no new drift. [Current regression/source record](../evidence/shb/retained-tests/6272c2fa05205d30bbe9d9bcedb520005791ce43c136300b532424ae16c76c21.json); the prior shared record [48448c3c…json](../evidence/shb/retained-tests/48448c3c95332511c5734a3ff375b48f9d8d6873c96691d2f1db8d816ccba490.json) and the focused40-test audit record [fe29b38a…json](../evidence/shb/retained-tests/fe29b38a93d85070dc0c795a2b0260c7fb4d07656ea44ca237f7463bb5fbb26b.json) are retained as the audit trail of the lifecycle/mirror addition. Implementation commit b7cd2e9.

Actual Chromium151.0.7922.173/Node24.15.0 passes **161 checks**:71 customer/90 staff in JS/no-JS at320px (unchanged; the lifecycle/mirror additions are backend-only). The native staff discount issuance flow exercises the scope list, GET detail (no raw code visible), native CSRF reject, native POST issuing one raw code, GET after issuance (no raw code), and prepared-intent retry (no raw code) in both modes. No existing customer-session, FPGA/ASIC, refund, invitation issuance/revocation or discount revocation behaviour changes. [Current browser/source record](../evidence/shb/retained-tests/9a729dd1bbee341bd48a366d64a901beefedac6ccf2c8063da1561a6bca3276e.json); prior browser record [45bcdeab…json](../evidence/shb/retained-tests/45bcdeab8f642c4ecdf724bf81a60ef215b208588db7fc23b2d8b26f946045aa.json) retained. Private evidence .scratch/shb-checkout-browser-k67relwn. Planning activity3 tests pass and both planning checks run before commit. All owned contexts completed; no async job.

## Reproduce

```sh
python3 scripts/check_shb_retained.py --test-label shop.shb.discount_issuance_tests
python3 scripts/check_shb_retained.py --shared
python3 scripts/check_shb_retained.py --browser --release .scratch/shb-private-resume-t2p3r5cc/release --browser-binary /nix/store/53p8msmqxpi829zdrw6qkvaamidxy9cj-chromium-151.0.7922.173/bin/chromium --browser-node /nix/store/5a8ysg1jnj8jmzzyfcfw7rvpvnp5rfpa-nodejs-24.15.0/bin/node
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
python3 scripts/check_purchase_plan.py --refresh-inventory
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

Normal pinned Nix/source/runtime/native/licence/OCI/CI and actual commercial/provider/refund/tax/mail/host/ingress/database/human/independent custody/post-backup/transport/restore/complete-loss qualification remain open. The authorized independent off-host runner is unassigned. Actual company inputs arrive later through docs/decisions.md; no repeated request. No real credentials/.env, production/bank-sandbox connection, host/DNS/TLS/bank/mail/storage operation or paid provision. The private Astro release and unrelated http_cache.sqlite remain unchanged. Parent counts stay11/42 retained summaries and1/14 documentary phases; no new SUMMARY/FULL_PASS. Current revocation43 and matched reservation holds remain intact.
