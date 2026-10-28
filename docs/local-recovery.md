# Local restore startup fence

This boundary supports disposable local/synthetic PostgreSQL fixtures with fake bank, mail and storage adapters. Actual restoration, traffic/egress isolation, post-point revocation/MFA reconciliation and safe reopening remain unqualified.

For each selected local restore, supply a fresh canonical UUID4 as `SHOP_LOCAL_RESTORE_ID` outside the restored database, before starting any customer, staff or worker process. All cooperating processes must use the same value. Settings import validates the value without connecting to the database. Blank, malformed and production/bank-sandbox selections reject startup with a fixed error. The identifier grants no authority and is never accepted from a customer request.

The selected identity closes private access, customer code capture/verification, both staff factors and new worker/provider effect admissions even when the restored database has an unheld or missing `AccessEpoch`. It creates no recovery history during import, ordinary reads or denied admission. Public catalog and database-connectivity health responses retain their existing contracts; they do not establish recovery readiness.

The existing internal fixture function `shop.access.recovery.local_recovery_operation` requires an exact newly owned test database identity and `shop_test` role, checked against the actual PostgreSQL connection. There is no HTTP or production recovery command. Its local sequence is:

1. Record `quarantine` with `request_id` equal to the selected startup identity. This rotates the access epoch and staff generations, consumes pending customer/staff challenges and deletes restored sessions while preserving business history and resource grants.
2. Inspect/reconcile synthetic facts while held. Typed bank `lookup` and `lookup_mutation` remain available without new effect admissions. An uncertain result or lookup miss never authorizes resending a financial operation. An unfinished admitted call does not expire; synthetic release refuses until every admitted scope has recorded its exit.
3. Record `release` with `basis_reset` equal to the selected identity and a new request identity. It still requires the current persisted hold and an empty unfinished-admission set, then invalidates access again. This transition represents completed fixture cleanup only.
4. Keep the selected startup identity on subsequent cooperating process restarts. Matching immutable quarantine/release history clears that startup fence, while current database holds continue to close access. Customers and staff must authenticate afresh. A later ordinary quarantine/release does not discard the completed startup sequence.

Older or unrelated recovery records cannot satisfy a fresh identity. A missing epoch remains closed even with matching old history. Inspection distinguishes `startup_recovery_pending` from the persisted `currently_quarantined` flag; an unheld startup fence does not claim that existing effects have drained.

Omitting the setting selects ordinary local development behavior. Reusing an identity after another restore can match restored history, so it is unsuitable for a new restore. Stopping old processes, supplying fresh shared configuration and blocking actual traffic/outbound effects belong to the separately authorized recovery procedure. The fixture gate cannot prove those operations, recover lost business facts or reconcile actual MFA recovery codes.

Tests and exact evidence: [startup component](../.planning/phases/13-purchase-flow-fulfilment-and-release-acceptance/13-STARTUP-RECOVERY-PARTIAL.md). Payment uncertainty: [synthetic bank](synthetic-bank.md).
